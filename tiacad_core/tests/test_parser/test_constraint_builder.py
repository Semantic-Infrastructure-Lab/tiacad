"""
Tests for ConstraintBuilder (TCAD-CON-1/TCAD-CON-3/TCAD-1).

Covers 'flush'/'offset' (CadQuery 'Plane' kind) and 'coaxial' (CadQuery
'Axis'+'Point' kinds), all implemented by wrapping CadQuery's own
Assembly.constrain()/.solve(). 'tangent' (TCAD-1) is implemented WITHOUT
CadQuery's solver — see constraint_builder.py module docstring for why a
real PointInPlane solve leaves rotation freedom open — via a direct
distance-to-plane computation instead.
"""

import numpy as np
import pytest
import cadquery as cq

from tiacad_core.part import Part, PartRegistry
from tiacad_core.spatial_resolver import SpatialResolver
from tiacad_core.geometry.cadquery_backend import CadQueryBackend
from tiacad_core.parser.constraint_builder import ConstraintBuilder, ConstraintBuilderError
from tiacad_core.parser.tiacad_parser import TiaCADParser


def _approx(actual, expected, abs_tol=1e-6):
    assert actual == pytest.approx(expected, abs=abs_tol)


@pytest.fixture
def two_box_registry():
    backend = CadQueryBackend()
    registry = PartRegistry()
    registry.add(Part(name='base', geometry=cq.Workplane('XY').box(10, 10, 10), backend=backend))
    registry.add(Part(name='top', geometry=cq.Workplane('XY').box(5, 5, 5), backend=backend))
    return registry


class TestFlushConstraint:
    def test_flush_mates_faces_reproduces_roadmap_example(self, two_box_registry):
        """The exact ROADMAP.md worked example: 5mm cube flush on 10mm cube."""
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([
            {'type': 'flush', 'faces': ['base.face_top', 'top.face_bottom']}
        ])

        _approx(registry.get('base').get_center(), (0.0, 0.0, 0.0))
        _approx(registry.get('top').get_center(), (0.0, 0.0, 7.5))

    def test_reference_part_stays_fixed(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([
            {'type': 'flush', 'faces': ['base.face_top', 'top.face_bottom']}
        ])
        _approx(registry.get('base').get_center(), (0.0, 0.0, 0.0))
        assert np.allclose(registry.get('base').current_orientation, np.eye(3))

    def test_flush_requiring_rotation_updates_orientation(self):
        """Mating a side face to a top face forces the moving part to rotate 90°;
        verify both position and current_orientation (TCAD-CON-2) come out right."""
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='base', geometry=cq.Workplane('XY').box(10, 10, 10), backend=backend))
        registry.add(Part(name='bracket', geometry=cq.Workplane('XY').box(2, 6, 6), backend=backend))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([
            {'type': 'flush', 'faces': ['base.face_top', 'bracket.face_right']}
        ])

        _approx(registry.get('bracket').get_center(), (0.0, 0.0, 6.0))
        # bracket's local +X (its mated face's normal) must now point along -Z
        axis_x = resolver.resolve('bracket.axis_x')
        _approx(axis_x.orientation.tolist(), [0.0, 0.0, -1.0])

    def test_inline_face_spec_is_accepted(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'flush',
            'faces': [
                {'type': 'face', 'part': 'base', 'selector': '>Z'},
                {'type': 'face', 'part': 'top', 'selector': '<Z'},
            ],
        }])
        _approx(registry.get('top').get_center(), (0.0, 0.0, 7.5))


class TestOffsetConstraint:
    def test_offset_adds_gap_along_normal(self):
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='surface', geometry=cq.Workplane('XY').box(20, 20, 2), backend=backend))
        registry.add(Part(name='mount', geometry=cq.Workplane('XY').box(4, 4, 4), backend=backend))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'offset',
            'faces': ['surface.face_top', 'mount.face_bottom'],
            'distance': 5,
        }])

        # surface top at z=1; flush would put mount center at z=3; +5 offset -> z=8
        _approx(registry.get('mount').get_center(), (0.0, 0.0, 8.0), abs_tol=1e-4)

    def test_offset_does_not_introduce_arbitrary_rotation(self):
        """TCAD-CON-10 regression: a 20x20x2 surface / 4x4x4 mount is the
        exact size ratio that previously converged to an arbitrary ~50deg
        in-plane rotation (flush/offset's 'Plane' constraint leaves rotation
        about the aligned normal unconstrained, and IPOPT's fixed nonzero
        seed decided that free angle from numerical noise rather than
        geometry). Both parts are square, so the rotation was invisible to
        test_offset_adds_gap_along_normal's center-position-only assertion;
        assert current_orientation stays identity instead."""
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='surface', geometry=cq.Workplane('XY').box(20, 20, 2), backend=backend))
        registry.add(Part(name='mount', geometry=cq.Workplane('XY').box(4, 4, 4), backend=backend))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'offset',
            'faces': ['surface.face_top', 'mount.face_bottom'],
            'distance': 5,
        }])

        assert np.allclose(registry.get('mount').current_orientation, np.eye(3), atol=1e-6)

    def test_offset_distance_accepts_mm_suffix(self):
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='surface', geometry=cq.Workplane('XY').box(20, 20, 2), backend=backend))
        registry.add(Part(name='mount', geometry=cq.Workplane('XY').box(4, 4, 4), backend=backend))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'offset',
            'faces': ['surface.face_top', 'mount.face_bottom'],
            'distance': '5mm',
        }])
        _approx(registry.get('mount').get_center(), (0.0, 0.0, 8.0), abs_tol=1e-4)

    def test_offset_missing_distance_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="requires a 'distance'"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'offset', 'faces': ['base.face_top', 'top.face_bottom']}
            ])


class TestCoaxialConstraint:
    def test_coaxial_pin_lands_on_hole_axis(self):
        """A pin cylinder off to the side must land centered on a plate's hole axis."""
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(
            name='plate',
            geometry=cq.Workplane('XY').box(20, 20, 5).faces('>Z').workplane().hole(6),
            backend=backend,
        ))
        registry.add(Part(
            name='pin',
            geometry=cq.Workplane('XY').center(30, 30).cylinder(10, 3),
            backend=backend,
        ))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'coaxial',
            'edges': [
                {'type': 'edge', 'part': 'plate', 'selector': '%CIRCLE and >Z'},
                {'type': 'edge', 'part': 'pin', 'selector': '%CIRCLE and >Z'},
            ],
        }])

        pin_center = registry.get('pin').get_center()
        assert pin_center[0] == pytest.approx(0.0, abs=1e-4)
        assert pin_center[1] == pytest.approx(0.0, abs=1e-4)

    def test_coaxial_reference_part_stays_fixed(self):
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(
            name='plate',
            geometry=cq.Workplane('XY').box(20, 20, 5).faces('>Z').workplane().hole(6),
            backend=backend,
        ))
        registry.add(Part(
            name='pin',
            geometry=cq.Workplane('XY').center(30, 30).cylinder(10, 3),
            backend=backend,
        ))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'coaxial',
            'edges': [
                {'type': 'edge', 'part': 'plate', 'selector': '%CIRCLE and >Z'},
                {'type': 'edge', 'part': 'pin', 'selector': '%CIRCLE and >Z'},
            ],
        }])

        _approx(registry.get('plate').get_center(), (0.0, 0.0, 0.0))
        assert np.allclose(registry.get('plate').current_orientation, np.eye(3))

    def test_coaxial_string_face_ref_rejected(self, two_box_registry):
        """No FACE_SELECTOR_MAP equivalent exists for edges — dotted shorthand isn't valid."""
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="inline"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'coaxial', 'edges': ['base.face_top', 'top.face_bottom']}
            ])

    def test_coaxial_requires_edges_field(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="'edges' list"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'coaxial', 'faces': ['base.face_top', 'top.face_bottom']}
            ])


class TestTangentConstraint:
    """A roller (cylinder lying on its side) resting tangent on a rail (flat
    top face). Unlike flush/offset/coaxial, 'tangent' never calls CadQuery's
    solve() — see the module docstring for why — so these tests check the
    resulting geometry directly rather than just SpatialRef math."""

    @staticmethod
    def _rail_and_sideways_roller(radius=3.0, height=10.0, roller_pos=(5.0, 7.0, 50.0)):
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='rail', geometry=cq.Workplane('XY').box(40, 40, 4), backend=backend))
        # Cylinder built with its axis along Z, then rotated 90° about Y so
        # its axis lies along X — "already axis-aligned" is on the caller,
        # same limitation as 'offset'.
        roller_geom = (
            cq.Workplane('XY')
            .cylinder(height, radius)
            .rotate((0, 0, 0), (0, 1, 0), 90)
            .translate(roller_pos)
        )
        registry.add(Part(name='roller', geometry=roller_geom, backend=backend))
        return registry

    def test_tangent_lifts_roller_by_exactly_one_radius(self):
        """rail's top face is at z=2 (20x20x2 half-height box); the roller's
        axis must land at z=2+radius=5, with X/Y untouched (translate-only)."""
        registry = self._rail_and_sideways_roller(radius=3.0, roller_pos=(5.0, 7.0, 50.0))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'tangent',
            'face': 'rail.face_top',
            'edge': {'type': 'edge', 'part': 'roller', 'selector': '%CIRCLE and <X'},
        }])

        _approx(registry.get('roller').get_center(), (5.0, 7.0, 5.0), abs_tol=1e-4)
        bbox = registry.get('roller').geometry.val().BoundingBox()
        _approx(bbox.zmin, 2.0, abs_tol=1e-4)  # touches the plane, doesn't cross it
        _approx(bbox.zmax, 8.0, abs_tol=1e-4)  # 2 * radius above the touch point

    def test_reference_part_stays_fixed(self):
        registry = self._rail_and_sideways_roller()
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'tangent',
            'face': 'rail.face_top',
            'edge': {'type': 'edge', 'part': 'roller', 'selector': '%CIRCLE and <X'},
        }])
        _approx(registry.get('rail').get_center(), (0.0, 0.0, 0.0))

    def test_radius_measured_from_geometry_not_yaml(self):
        """A bigger cylinder must land higher, with no 'distance' field supplied."""
        registry = self._rail_and_sideways_roller(radius=6.0, roller_pos=(0.0, 0.0, 50.0))
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([{
            'type': 'tangent',
            'face': 'rail.face_top',
            'edge': {'type': 'edge', 'part': 'roller', 'selector': '%CIRCLE and <X'},
        }])
        _approx(registry.get('roller').get_center(), (0.0, 0.0, 8.0), abs_tol=1e-4)

    def test_missing_face_field_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="requires a 'face'"):
            ConstraintBuilder(registry, resolver).apply_constraints([{
                'type': 'tangent',
                'edge': {'type': 'edge', 'part': 'top', 'selector': '%CIRCLE and <X'},
            }])

    def test_missing_edge_field_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="requires a 'face'"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'tangent', 'face': 'base.face_top'}
            ])

    def test_non_circular_edge_selector_raises(self):
        """A straight edge has no radius — must fail loudly, not silently use 0."""
        registry = self._rail_and_sideways_roller()
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="single circular edge"):
            ConstraintBuilder(registry, resolver).apply_constraints([{
                'type': 'tangent',
                'face': 'rail.face_top',
                'edge': {'type': 'edge', 'part': 'roller', 'selector': '%LINE'},
            }])

    def test_same_part_on_both_sides_raises(self):
        registry = self._rail_and_sideways_roller()
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="two distinct parts"):
            ConstraintBuilder(registry, resolver).apply_constraints([{
                'type': 'tangent',
                'face': 'roller.face_top',
                'edge': {'type': 'edge', 'part': 'roller', 'selector': '%CIRCLE and <X'},
            }])


class TestConstraintValidation:
    def test_unknown_type_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="unknown type"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'glue', 'faces': ['base.face_top', 'top.face_bottom']}
            ])

    def test_reserved_type_raises_distinct_error(self, two_box_registry):
        """'parallel'/'perpendicular'/'angle'/'symmetric' are named and reserved
        (TCAD-CON-9) so this errors as 'reserved for a future revision', not the
        generic 'unknown type' a made-up type name gets."""
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="reserved for a future revision"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'parallel', 'faces': ['base.face_top', 'top.face_bottom']}
            ])

    def test_unknown_part_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="unknown part 'missing'"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'flush', 'faces': ['base.face_top', 'missing.face_bottom']}
            ])

    def test_same_part_on_both_sides_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="two distinct parts"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'flush', 'faces': ['base.face_top', 'base.face_bottom']}
            ])

    def test_faces_must_have_exactly_two_entries(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="exactly"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'flush', 'faces': ['base.face_top']}
            ])

    def test_empty_constraints_is_noop(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        ConstraintBuilder(registry, resolver).apply_constraints([])
        _approx(registry.get('top').get_center(), (0.0, 0.0, 0.0))

    def test_conflicting_plane_constraints_raise_before_solve(self):
        """TCAD-CON-4: mating the same moving face flush against two
        non-coincident reference planes must be caught up front, not left
        to fail opaquely inside CadQuery's .solve()."""
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='base', geometry=cq.Workplane('XY').box(10, 10, 10), backend=backend))
        registry.add(Part(name='wall', geometry=cq.Workplane('XY').box(10, 10, 10), backend=backend))
        registry.add(Part(name='top', geometry=cq.Workplane('XY').box(5, 5, 5), backend=backend))
        resolver = SpatialResolver(registry)

        with pytest.raises(ConstraintBuilderError, match="can't satisfy both simultaneously"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'flush', 'faces': ['base.face_top', 'top.face_bottom']},
                {'type': 'flush', 'faces': ['wall.face_right', 'top.face_bottom']},
            ])

    def test_same_reference_plane_from_different_parts_does_not_conflict(self):
        """Two reference parts whose selected faces happen to share the same
        plane (e.g. two equal-height boxes side by side) are a legitimate
        double mate, not a contradiction, and must solve normally."""
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part(name='base_a', geometry=cq.Workplane('XY').box(10, 10, 10), backend=backend))
        registry.add(Part(
            name='base_b',
            geometry=cq.Workplane('XY').box(10, 10, 10).translate((20, 0, 0)),
            backend=backend,
        ))
        registry.add(Part(name='top', geometry=cq.Workplane('XY').box(5, 5, 5), backend=backend))
        resolver = SpatialResolver(registry)

        ConstraintBuilder(registry, resolver).apply_constraints([
            {'type': 'flush', 'faces': ['base_a.face_top', 'top.face_bottom']},
            {'type': 'flush', 'faces': ['base_b.face_top', 'top.face_bottom']},
        ])
        _approx(registry.get('top').get_center()[2], 7.5)


class TestConstraintPipelineIntegration:
    """End-to-end: constraints solved through the real YAML parse pipeline."""

    def test_flush_via_yaml(self):
        doc = TiaCADParser.parse_string("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  top:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center

constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]
""")
        _approx(doc.parts.get('base').get_center(), (0.0, 0.0, 0.0))
        _approx(doc.parts.get('top').get_center(), (0.0, 0.0, 7.5))

    def test_constraints_can_reference_operation_output_parts(self):
        """Constraints run after operations, so they may reference a part an
        operation created (not just parts: entries)."""
        doc = TiaCADParser.parse_string("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  raw_top:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center

operations:
  top:
    type: transform
    input: raw_top
    transforms:
      - translate: [100, 0, 0]

constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]
""")
        _approx(doc.parts.get('top').get_center(), (0.0, 0.0, 7.5))

    def test_coaxial_via_yaml(self):
        """Two cylinders (a bushing and a pin), offset in XY, made coaxial."""
        doc = TiaCADParser.parse_string("""
parts:
  bushing:
    primitive: cylinder
    parameters: {radius: 6, height: 5}
    origin: center
  pin:
    primitive: cylinder
    parameters: {radius: 3, height: 10}
    origin: [30, 30, 0]

constraints:
  - type: coaxial
    edges:
      - {type: edge, part: bushing, selector: "%CIRCLE and >Z"}
      - {type: edge, part: pin, selector: "%CIRCLE and >Z"}
""")
        pin_center = doc.parts.get('pin').get_center()
        assert pin_center[0] == pytest.approx(0.0, abs=1e-4)
        assert pin_center[1] == pytest.approx(0.0, abs=1e-4)

    def test_tangent_via_yaml(self):
        """A roller cylinder, laid on its side via an explicit rotate+translate
        operation, tangent to a rail's top face."""
        doc = TiaCADParser.parse_string("""
parts:
  rail:
    primitive: box
    parameters: {width: 40, depth: 40, height: 4}
    origin: center
  raw_roller:
    primitive: cylinder
    parameters: {radius: 3, height: 10}
    origin: center

operations:
  roller:
    type: transform
    input: raw_roller
    transforms:
      - rotate: {angle: 90, axis: Y, origin: [0, 0, 0]}
      - translate: [5, 7, 50]

constraints:
  - type: tangent
    face: rail.face_top
    edge: {type: edge, part: roller, selector: "%CIRCLE and <X"}
""")
        _approx(doc.parts.get('roller').get_center(), (5.0, 7.0, 5.0), abs_tol=1e-4)

    def test_missing_constraints_section_is_fine(self):
        doc = TiaCADParser.parse_string("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
""")
        _approx(doc.parts.get('base').get_center(), (0.0, 0.0, 0.0))
