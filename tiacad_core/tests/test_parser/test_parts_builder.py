"""
Tests for PartsBuilder

Tests building Part objects from YAML primitive specifications.
"""

import pytest
import cadquery as cq

from tiacad_core.parser.parts_builder import PartsBuilder, PartsBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part
from tiacad_core.geometry import MockBackend, set_default_backend, reset_default_backend


class TestBox:
    """Test box primitive building"""

    def test_simple_box(self):
        """Test building a simple box"""
        params = {}
        spec = {
            'plate': {
                'primitive': 'box',
                'size': [100, 25, 50]
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('plate')
        assert part is not None
        assert part.name == 'plate'
        assert isinstance(part.geometry, cq.Workplane)

    def test_box_with_parameters(self):
        """Test box with ${...} parameters"""
        params = {
            'width': 100,
            'depth': 50,
            'height': 25,
        }
        spec = {
            'box': {
                'primitive': 'box',
                'size': ['${width}', '${height}', '${depth}']
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('box')
        assert part is not None

    def test_box_with_expressions(self):
        """Test box with expression parameters"""
        params = {
            'base_size': 100,
        }
        spec = {
            'box': {
                'primitive': 'box',
                'size': ['${base_size}', '${base_size / 4}', '${base_size / 2}']
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('box')
        assert part is not None

    def test_box_centered_origin(self):
        """Test box with centered origin (default)"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 10, 10],
                'origin': 'center'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('box')
        assert part is not None

    def test_box_corner_origin(self):
        """Test box with corner origin"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 10, 10],
                'origin': 'corner'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('box')
        assert part is not None

    def test_box_list_origin_places_corner_not_centered(self):
        """`origin: [x, y, z]` (schema v3.0's third, documented origin mode)
        was previously silently ignored by every primitive builder -- a box
        built this way just sat at its default centered position regardless
        of the coordinate given. This generalizes 'corner' mode: the box's
        min corner lands at the given point, not its center. See
        KNOWN_LIMITATIONS.md #17 (found rebuilding a Thingiverse model whose
        `wedge` part relies on this exact behavior for a clean 0..height
        slice)."""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 6, 4],
                'origin': [100, -50, 30],
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        bounds = registry.get('box').get_bounds()
        assert bounds['min'] == pytest.approx((100, -50, 30))
        assert bounds['max'] == pytest.approx((110, -44, 34))

    def test_box_missing_size(self):
        """Test box without a size"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'size: [x, y, z]' in str(exc_info.value)

    def test_box_invalid_size(self):
        """Test box with a two-value size"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 20]  # Missing z
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'exactly 3 values' in str(exc_info.value)

    def test_box_uses_default_geometry_backend(self):
        """PartsBuilder should honor the configured default backend."""
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 30, 20]
            }
        }

        set_default_backend(MockBackend())
        try:
            builder = PartsBuilder(ParameterResolver({}))
            registry = builder.build_parts(spec)
            part = registry.get('box')

            assert part.backend is builder.backend
            assert part.geometry.shape_type == 'box'
        finally:
            reset_default_backend()


class TestCylinder:
    """Test cylinder primitive building"""

    def test_simple_cylinder(self):
        """Test building a simple cylinder"""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'radius': 10,
                'length': 50
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('cyl')
        assert part is not None
        assert part.name == 'cyl'

    def test_cylinder_with_origin(self):
        """Test cylinder with different origins"""
        params = {}
        spec = {
            'cyl_center': {
                'primitive': 'cylinder',
                'radius': 10,
                'length': 50,
                'origin': 'center'
            },
            'cyl_base': {
                'primitive': 'cylinder',
                'radius': 10,
                'length': 50,
                'origin': 'base'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        assert registry.get('cyl_center') is not None
        assert registry.get('cyl_base') is not None

    def test_cylinder_list_origin_places_base_not_center(self):
        """`origin: [x, y, z]` generalizes 'base' mode (bottom-center at the
        given point), not a plain translate of the centered cylinder --
        confirmed against `examples/thingiverse_rebuilds/thing38359_outside.yaml`'s
        `bore`, whose `origin: [0, 0, -margin]` is meant to extend the bore's
        bottom past the solid for a clean cut. Before this fix, list-form
        origin was silently ignored entirely: `bore` built centered on Z
        (spanning roughly [-h/2, h/2]) instead of starting at -margin, so it
        fell short of the model's top and left a chunk of the boolean
        subtraction un-cut -- a ~15% volume error that looked like an OCCT
        boolean robustness bug until traced back here. See
        KNOWN_LIMITATIONS.md #17."""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'radius': 5,
                'length': 20,
                'origin': [3, -2, -10],
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        bounds = registry.get('cyl').get_bounds()
        assert bounds['center'] == pytest.approx((3, -2, 0))
        assert bounds['min'][2] == pytest.approx(-10)
        assert bounds['max'][2] == pytest.approx(10)

    def test_cylinder_missing_radius(self):
        """Test cylinder without radius"""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'length': 50
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'radius' in str(exc_info.value).lower()

    def test_cylinder_missing_length(self):
        """Test cylinder without length"""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'radius': 10
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'length' in str(exc_info.value).lower()


class TestSphere:
    """Test sphere primitive building"""

    def test_simple_sphere(self):
        """Test building a simple sphere"""
        params = {}
        spec = {
            'ball': {
                'primitive': 'sphere',
                'radius': 10
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('ball')
        assert part is not None
        assert part.name == 'ball'


class TestBackendBoundaries:
    """Test explicit backend limitations in PartsBuilder."""

    def test_cadquery_only_primitive_fails_with_mock_backend(self):
        spec = {
            'ring': {
                'primitive': 'torus',
                'parameters': {'major_radius': 20, 'minor_radius': 5}
            }
        }

        builder = PartsBuilder(ParameterResolver({}), backend=MockBackend())

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'requires cadquerybackend' in str(exc_info.value).lower()

    def test_sphere_with_parameters(self):
        """Test sphere with parameter"""
        params = {'ball_radius': 25}
        spec = {
            'ball': {
                'primitive': 'sphere',
                'radius': '${ball_radius}'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('ball')
        assert part is not None

    def test_sphere_missing_radius(self):
        """Test sphere without radius"""
        params = {}
        spec = {
            'ball': {
                'primitive': 'sphere'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'radius' in str(exc_info.value).lower()


class TestCone:
    """Test cone primitive building"""

    def test_simple_cone(self):
        """Test building a cone"""
        params = {}
        spec = {
            'cone': {
                'primitive': 'cone',
                'radius1': 20,  # Base
                'radius2': 10,  # Top
                'length': 50
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('cone')
        assert part is not None

    def test_pointed_cone(self):
        """Test cone with pointed top (radius2 = 0)"""
        params = {}
        spec = {
            'cone': {
                'primitive': 'cone',
                'radius1': 20,
                'radius2': 0,  # Pointed top
                'length': 50
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('cone')
        assert part is not None


class TestTorus:
    """Test torus primitive building"""

    def test_simple_torus(self):
        """Test building a torus.

        Asserts the geometry is a real, non-degenerate solid — not just that the
        Part exists. The previous `assert part is not None` let a zero-volume
        degenerate torus (broken revolve on the OCP 7.9 kernel) pass unnoticed.
        """
        import math

        params = {}
        major, minor = 20, 5
        spec = {
            'ring': {
                'primitive': 'torus',
                'major_radius': major,
                'minor_radius': minor
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('ring')
        assert part is not None

        # Pappus volume of a torus: 2 * pi^2 * R * r^2
        volume = part.geometry.val().Volume()
        expected = 2 * math.pi**2 * major * minor**2
        assert abs(volume - expected) < expected * 0.01, (
            f"torus volume {volume:.2f} != expected {expected:.2f} — a broken "
            f"torus primitive (degenerate/zero-volume solid) would trip here"
        )

        # Donut lies flat on XY, hole along Z: extents 2(R+r), 2(R+r), 2r
        bb = part.geometry.val().BoundingBox()
        assert abs(bb.xlen - 2 * (major + minor)) < 0.1
        assert abs(bb.ylen - 2 * (major + minor)) < 0.1
        assert abs(bb.zlen - 2 * minor) < 0.1


class TestMultipleParts:
    """Test building multiple parts at once"""

    def test_build_multiple_parts(self):
        """Test building multiple parts together"""
        params = {
            'plate_w': 100,
            'plate_h': 80,
            'plate_t': 12,
            'beam_w': 32,
            'beam_h': 24,
            'beam_len': 75,
        }
        spec = {
            'plate': {
                'primitive': 'box',
                'size': ['${plate_w}', '${plate_h}', '${plate_t}']
            },
            'beam': {
                'primitive': 'box',
                'size': ['${beam_w}', '${beam_h}', '${beam_len}']
            },
            'screw_hole': {
                'primitive': 'cylinder',
                'radius': 2.5,
                'length': '${plate_t + 2}'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        assert registry.get('plate') is not None
        assert registry.get('beam') is not None
        assert registry.get('screw_hole') is not None
        assert len(registry) == 3


class TestErrorHandling:
    """Test error handling and validation"""

    def test_missing_primitive_field(self):
        """Test part without primitive field"""
        params = {}
        spec = {
            'bad_part': {
                'parameters': {'width': 10, 'height': 10, 'depth': 10}
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'primitive' in str(exc_info.value).lower()

    def test_position_key_error(self):
        """'position' is not valid — must raise a clear error directing to 'origin' or 'transform'"""
        spec = {
            'my_part': {
                'primitive': 'box',
                'size': [10, 10, 10],
                'position': [0, 0, 5],
            }
        }

        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        msg = str(exc_info.value)
        assert 'position' in msg.lower()
        assert 'origin' in msg.lower()

    def test_unknown_primitive_type(self):
        """Test unknown primitive type"""
        params = {}
        spec = {
            'bad_part': {
                'primitive': 'unknown_shape',
                'parameters': {'width': 10, 'height': 10, 'depth': 10}
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'unknown' in str(exc_info.value).lower()


class TestMetadata:
    """Test part metadata"""

    def test_primitive_type_in_metadata(self):
        """Test that primitive type is stored in metadata"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 10, 10]
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('box')
        assert 'primitive_type' in part.metadata
        assert part.metadata['primitive_type'] == 'box'


class TestGuitarHangerExample:
    """Test parts from guitar hanger example"""

    def test_guitar_hanger_parts(self):
        """Test building all parts from guitar hanger"""
        params = {
            'plate_w': 100,
            'plate_h': 80,
            'plate_t': 12,
            'screw_d': 5.0,
            'beam_w': 32,
            'beam_h': 24,
            'beam_len': 75,
            'arm_w': 22,
            'arm_h': 16,
            'arm_len': 70,
        }
        spec = {
            'plate': {
                'primitive': 'box',
                'size': ['${plate_w}', '${plate_h}', '${plate_t}'],
                'origin': 'center'
            },
            'screw_hole': {
                'primitive': 'cylinder',
                'radius': '${screw_d / 2}',
                'length': '${plate_t + 2}',
                'origin': 'center'
            },
            'beam': {
                'primitive': 'box',
                'size': ['${beam_w}', '${beam_h}', '${beam_len}'],
                'origin': 'center'
            },
            'arm': {
                'primitive': 'box',
                'size': ['${arm_w}', '${arm_h}', '${arm_len}'],
                'origin': 'center'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        # Verify all parts built
        assert registry.get('plate') is not None
        assert registry.get('screw_hole') is not None
        assert registry.get('beam') is not None
        assert registry.get('arm') is not None
        assert len(registry) == 4

        # Verify they're Part objects
        for part_name in registry.list_parts():
            part = registry.get(part_name)
            assert isinstance(part, Part)
            assert isinstance(part.geometry, cq.Workplane)


# ---------------------------------------------------------------------------
# Polygon primitive tests
# ---------------------------------------------------------------------------

class TestPolygon:
    """Test polygon (extruded regular polygon) primitive building."""

    def _build(self, name, **params):
        spec = {name: {'primitive': 'polygon', **params}}
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        return builder.build_parts(spec).get(name)

    def test_hexagon_builds(self):
        part = self._build('hex', sides=6, diameter=10.0, length=5.0)
        assert part is not None
        assert isinstance(part.geometry, cq.Workplane)

    def test_square_prism_builds(self):
        part = self._build('sq', sides=4, diameter=20.0, length=10.0)
        assert part is not None

    def test_triangle_prism_builds(self):
        part = self._build('tri', sides=3, diameter=15.0, length=8.0)
        assert part is not None

    def test_polygon_metadata_primitive_type(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'hex': {'primitive': 'polygon', 'sides': 6, 'diameter': 10.0, 'length': 5.0}}
        registry = builder.build_parts(spec)
        part = registry.get('hex')
        assert part.metadata['primitive_type'] == 'polygon'

    def test_hexagon_positive_volume(self):
        part = self._build('hex', sides=6, diameter=10.0, length=5.0)
        bb = part.geometry.val().BoundingBox()
        # Should have non-trivial extent in all axes
        assert (bb.xmax - bb.xmin) > 0
        assert (bb.ymax - bb.ymin) > 0
        assert (bb.zmax - bb.zmin) > 0

    def test_length_controls_z_extent(self):
        p5 = self._build('h5', sides=6, diameter=10.0, length=5.0)
        p10 = self._build('h10', sides=6, diameter=10.0, length=10.0)
        bb5 = p5.geometry.val().BoundingBox()
        bb10 = p10.geometry.val().BoundingBox()
        z5 = bb5.zmax - bb5.zmin
        z10 = bb10.zmax - bb10.zmin
        assert abs(z10 - 2 * z5) < 0.1, f"length=10 should be 2× length=5: {z5:.2f} vs {z10:.2f}"

    def test_diameter_controls_xy_extent(self):
        p10 = self._build('d10', sides=6, diameter=10.0, length=5.0)
        p20 = self._build('d20', sides=6, diameter=20.0, length=5.0)
        bb10 = p10.geometry.val().BoundingBox()
        bb20 = p20.geometry.val().BoundingBox()
        xy10 = bb10.xmax - bb10.xmin
        xy20 = bb20.xmax - bb20.xmin
        assert xy20 > xy10, "larger diameter should produce larger XY footprint"

    def test_missing_sides_raises(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'hex': {'primitive': 'polygon', 'diameter': 10.0, 'length': 5.0}}
        with pytest.raises(PartsBuilderError, match="sides"):
            builder.build_parts(spec)

    def test_missing_diameter_raises(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'hex': {'primitive': 'polygon', 'sides': 6, 'length': 5.0}}
        with pytest.raises(PartsBuilderError, match="diameter"):
            builder.build_parts(spec)

    def test_missing_length_raises(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'hex': {'primitive': 'polygon', 'sides': 6, 'diameter': 10.0}}
        with pytest.raises(PartsBuilderError, match="length"):
            builder.build_parts(spec)

    def test_sides_less_than_3_raises(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'bad': {'primitive': 'polygon', 'sides': 2, 'diameter': 10.0, 'length': 5.0}}
        with pytest.raises(PartsBuilderError, match="3 sides"):
            builder.build_parts(spec)

    def test_negative_diameter_raises(self):
        resolver = ParameterResolver({})
        builder = PartsBuilder(resolver)
        spec = {'bad': {'primitive': 'polygon', 'sides': 6, 'diameter': -5.0, 'length': 5.0}}
        with pytest.raises(PartsBuilderError, match="positive"):
            builder.build_parts(spec)

    def test_circumscribed_false_smaller_footprint(self):
        """circumscribed=false (inscribed diameter) should produce same or smaller XY than circumscribed=true."""
        p_circ = self._build('pc', sides=6, diameter=10.0, length=5.0, circumscribed=True)
        p_insc = self._build('pi', sides=6, diameter=10.0, length=5.0, circumscribed=False)
        bb_c = p_circ.geometry.val().BoundingBox()
        bb_i = p_insc.geometry.val().BoundingBox()
        xy_c = bb_c.xmax - bb_c.xmin
        xy_i = bb_i.xmax - bb_i.xmin
        # inscribed diameter = circumscribed inscribed circle → smaller footprint
        assert xy_i <= xy_c + 0.01
