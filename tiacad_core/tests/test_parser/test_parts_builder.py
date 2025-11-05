"""
Tests for PartsBuilder

Tests building Part objects from YAML primitive specifications.
"""

import pytest
import cadquery as cq

from tiacad_core.parser.parts_builder import PartsBuilder, PartsBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part, PartRegistry


class TestBox:
    """Test box primitive building"""

    def test_simple_box(self):
        """Test building a simple box"""
        params = {}
        spec = {
            'plate': {
                'primitive': 'box',
                'size': [100, 50, 25]
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
                'size': ['${width}', '${depth}', '${height}']
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
                'size': ['${base_size}', '${base_size / 2}', '${base_size / 4}']
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

    def test_box_missing_size(self):
        """Test box without size parameter"""
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

        assert 'size' in str(exc_info.value).lower()

    def test_box_invalid_size(self):
        """Test box with invalid size"""
        params = {}
        spec = {
            'box': {
                'primitive': 'box',
                'size': [10, 20]  # Only 2 dimensions
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'size' in str(exc_info.value).lower()


class TestCylinder:
    """Test cylinder primitive building"""

    def test_simple_cylinder(self):
        """Test building a simple cylinder"""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'radius': 10,
                'height': 50
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
                'height': 50,
                'origin': 'center'
            },
            'cyl_base': {
                'primitive': 'cylinder',
                'radius': 10,
                'height': 50,
                'origin': 'base'
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        assert registry.get('cyl_center') is not None
        assert registry.get('cyl_base') is not None

    def test_cylinder_missing_radius(self):
        """Test cylinder without radius"""
        params = {}
        spec = {
            'cyl': {
                'primitive': 'cylinder',
                'height': 50
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'radius' in str(exc_info.value).lower()

    def test_cylinder_missing_height(self):
        """Test cylinder without height"""
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

        assert 'height' in str(exc_info.value).lower()


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
                'height': 50
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
                'height': 50
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
        """Test building a torus"""
        params = {}
        spec = {
            'ring': {
                'primitive': 'torus',
                'major_radius': 20,
                'minor_radius': 5
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)
        registry = builder.build_parts(spec)

        part = registry.get('ring')
        assert part is not None


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
                'size': ['${plate_w}', '${plate_t}', '${plate_h}']
            },
            'beam': {
                'primitive': 'box',
                'size': ['${beam_w}', '${beam_len}', '${beam_h}']
            },
            'screw_hole': {
                'primitive': 'cylinder',
                'radius': 2.5,
                'height': '${plate_t + 2}'
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
                'size': [10, 10, 10]
            }
        }

        resolver = ParameterResolver(params)
        builder = PartsBuilder(resolver)

        with pytest.raises(PartsBuilderError) as exc_info:
            builder.build_parts(spec)

        assert 'primitive' in str(exc_info.value).lower()

    def test_unknown_primitive_type(self):
        """Test unknown primitive type"""
        params = {}
        spec = {
            'bad_part': {
                'primitive': 'unknown_shape',
                'size': [10, 10, 10]
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
                'size': ['${plate_w}', '${plate_t}', '${plate_h}'],
                'origin': 'center'
            },
            'screw_hole': {
                'primitive': 'cylinder',
                'radius': '${screw_d / 2}',
                'height': '${plate_t + 2}',
                'origin': 'center'
            },
            'beam': {
                'primitive': 'box',
                'size': ['${beam_w}', '${beam_len}', '${beam_h}'],
                'origin': 'center'
            },
            'arm': {
                'primitive': 'box',
                'size': ['${arm_w}', '${arm_len}', '${arm_h}'],
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
