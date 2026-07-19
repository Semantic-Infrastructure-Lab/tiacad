"""
Tests for ConstraintBuilder (TCAD-CON-1 MVP).

Covers the 'flush' and 'offset' constraint types, both implemented by
wrapping CadQuery's own Assembly.constrain()/.solve(). 'coaxial'/'tangent'
are schema-recognized but intentionally not implemented yet (see
constraint_builder.py module docstring) — covered here only to confirm they
fail loudly rather than silently doing nothing.
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


class TestConstraintValidation:
    def test_unknown_type_raises(self, two_box_registry):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="unknown type"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': 'glue', 'faces': ['base.face_top', 'top.face_bottom']}
            ])

    @pytest.mark.parametrize("reserved_type", ["coaxial", "tangent"])
    def test_reserved_types_raise_not_implemented(self, two_box_registry, reserved_type):
        registry = two_box_registry
        resolver = SpatialResolver(registry)
        with pytest.raises(ConstraintBuilderError, match="reserved for a future revision"):
            ConstraintBuilder(registry, resolver).apply_constraints([
                {'type': reserved_type, 'faces': ['base.face_top', 'top.face_bottom']}
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

    def test_missing_constraints_section_is_fine(self):
        doc = TiaCADParser.parse_string("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
""")
        _approx(doc.parts.get('base').get_center(), (0.0, 0.0, 0.0))
