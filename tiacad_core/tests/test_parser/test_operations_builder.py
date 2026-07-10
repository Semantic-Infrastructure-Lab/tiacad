"""
Tests for OperationsBuilder

Tests transform operations (translate, rotate) and integration with
TransformTracker and PointResolver.
"""

import pytest

from tiacad_core.parser.operations_builder import OperationsBuilder, OperationsBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.parser.parts_builder import PartsBuilder
from tiacad_core.geometry import MockBackend


class TestTranslateOperations:
    """Test translate transform operations"""

    def test_translate_to_point_with_offset(self):
        """Test translate to point with offset"""
        # Build initial parts
        params = {}
        parts_spec = {
            'box1': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}},
            'box2': {'primitive': 'box', 'parameters': {'width': 5, 'height': 5, 'depth': 5}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        # Execute translate operation
        ops_spec = {
            'box2_moved': {
                'type': 'transform',
                'input': 'box2',
                'transforms': [
                    {
                        'translate': {
                            'to': [20, 0, 0],  # Absolute point
                            'offset': [5, 0, 0]  # Additional offset
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        # Verify new part created
        moved_part = result_registry.get('box2_moved')
        assert moved_part is not None
        assert moved_part.name == 'box2_moved'

        # Position should be at [20+5, 0, 0] = [25, 0, 0]
        assert moved_part.current_position[0] == pytest.approx(25.0)

    def test_translate_absolute_position(self):
        """Test translate to absolute position"""
        params = {}
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {'translate': [30, 20, 10]}
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        moved_part = result_registry.get('box_moved')
        assert moved_part.current_position == pytest.approx((30.0, 20.0, 10.0))

    def test_translate_with_parameters(self):
        """Test translate with parameter expressions"""
        params = {
            'target_x': 50,
            'target_y': 25,
            'offset_x': 10
        }
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {
                        'translate': {
                            'to': ['${target_x}', '${target_y}', 0],
                            'offset': ['${offset_x}', 0, 0]
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        moved_part = result_registry.get('box_moved')
        # Should be at [50+10, 25, 0] = [60, 25, 0]
        assert moved_part.current_position[0] == pytest.approx(60.0)
        assert moved_part.current_position[1] == pytest.approx(25.0)


class TestRotateOperations:
    """Test rotate transform operations"""

    def test_rotate_around_origin(self):
        """Test rotate around origin"""
        params = {}
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_rotated': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {
                        'rotate': {
                            'angle': 90,
                            'axis': 'Z',
                            'origin': [0, 0, 0]
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        rotated_part = result_registry.get('box_rotated')
        assert rotated_part is not None

    def test_rotate_with_all_axes(self):
        """Test rotation around X, Y, Z axes"""
        params = {}
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        # Test each axis
        for axis in ['X', 'Y', 'Z']:
            ops_spec = {
                f'box_rotated_{axis}': {
                    'type': 'transform',
                    'input': 'box',
                    'transforms': [
                        {
                            'rotate': {
                                'angle': 45,
                                'axis': axis,
                                'origin': [0, 0, 0]
                            }
                        }
                    ]
                }
            }

            ops_builder = OperationsBuilder(registry, resolver)
            result_registry = ops_builder.execute_operations(ops_spec)

            rotated_part = result_registry.get(f'box_rotated_{axis}')
            assert rotated_part is not None

    def test_rotate_with_parameters(self):
        """Test rotate with parameter expressions"""
        params = {
            'angle': 10,
            'origin_x': 0,
            'origin_y': 50,
        }
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_rotated': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {
                        'rotate': {
                            'angle': '${angle}',
                            'axis': 'X',
                            'origin': ['${origin_x}', '${origin_y}', 0]
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        rotated_part = result_registry.get('box_rotated')
        assert rotated_part is not None


class TestSequentialTransforms:
    """Test multiple transforms in sequence"""

    def test_translate_then_rotate(self):
        """Test translating then rotating"""
        params = {}
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_transformed': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {'translate': [20, 0, 0]},  # Move away from origin
                    {
                        'rotate': {
                            'angle': 90,
                            'axis': 'Z',
                            'origin': [0, 0, 0]  # Rotate around origin
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        transformed_part = result_registry.get('box_transformed')
        assert transformed_part is not None

    def test_multiple_translates(self):
        """Test multiple translations"""
        params = {}
        parts_spec = {
            'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'box_moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {'translate': [10, 0, 0]},
                    {'translate': [10, 0, 0]},
                    {'translate': [10, 0, 0]}
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        moved_part = result_registry.get('box_moved')
        # Should be at [30, 0, 0] (3 x 10)
        assert moved_part.current_position[0] == pytest.approx(30.0)


class TestMultipleOperations:
    """Test executing multiple operations"""

    def test_multiple_operations(self):
        """Test multiple operations creating multiple parts"""
        params = {}
        parts_spec = {
            'base': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'part1': {
                'type': 'transform',
                'input': 'base',
                'transforms': [{'translate': [20, 0, 0]}]
            },
            'part2': {
                'type': 'transform',
                'input': 'base',
                'transforms': [{'translate': [-20, 0, 0]}]
            },
            'part3': {
                'type': 'transform',
                'input': 'base',
                'transforms': [{'translate': [0, 20, 0]}]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        # All parts should exist
        assert result_registry.get('part1') is not None
        assert result_registry.get('part2') is not None
        assert result_registry.get('part3') is not None
        assert len(result_registry) == 4  # base + 3 transformed

    def test_transform_preserves_input_backend(self):
        """Transform results should preserve the source part backend."""
        resolver = ParameterResolver({})
        registry = PartsBuilder(resolver, backend=MockBackend()).build_parts({
            'base': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}
        })

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations({
            'shifted': {
                'type': 'transform',
                'input': 'base',
                'transforms': [{'translate': [5, 0, 0]}]
            }
        })

        shifted = result_registry.get('shifted')
        assert shifted.backend is registry.get('base').backend


class TestErrorHandling:
    """Test error handling and validation"""

    def test_missing_type_field(self):
        """Test operation without type field"""
        params = {}
        parts_spec = {'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}}

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'bad_op': {
                'input': 'box'
                # Missing 'type' field
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        with pytest.raises(OperationsBuilderError) as exc_info:
            ops_builder.execute_operations(ops_spec)

        assert 'type' in str(exc_info.value).lower()

    def test_unknown_input_part(self):
        """Test transform with non-existent input part"""
        params = {}
        parts_spec = {'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}}

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'bad_op': {
                'type': 'transform',
                'input': 'nonexistent',
                'transforms': [{'translate': [10, 0, 0]}]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        with pytest.raises(OperationsBuilderError) as exc_info:
            ops_builder.execute_operations(ops_spec)

        assert 'not found' in str(exc_info.value).lower()

    def test_missing_transforms_field(self):
        """Test transform without transforms field"""
        params = {}
        parts_spec = {'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}}

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'bad_op': {
                'type': 'transform',
                'input': 'box'
                # Missing 'transforms' field
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        with pytest.raises(OperationsBuilderError) as exc_info:
            ops_builder.execute_operations(ops_spec)

        assert 'transforms' in str(exc_info.value).lower()

    def test_rotate_missing_angle(self):
        """Test rotate without angle"""
        params = {}
        parts_spec = {'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}}

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'bad_op': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {
                        'rotate': {
                            'axis': 'Z',
                            'origin': [0, 0, 0]
                            # Missing 'angle'
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        with pytest.raises(OperationsBuilderError) as exc_info:
            ops_builder.execute_operations(ops_spec)

        assert 'angle' in str(exc_info.value).lower()

    def test_rotate_missing_origin(self):
        """Test rotate without origin (required in TiaCAD!)"""
        params = {}
        parts_spec = {'box': {'primitive': 'box', 'parameters': {'width': 10, 'height': 10, 'depth': 10}}}

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        ops_spec = {
            'bad_op': {
                'type': 'transform',
                'input': 'box',
                'transforms': [
                    {
                        'rotate': {
                            'angle': 90,
                            'axis': 'Z'
                            # Missing 'origin' - REQUIRED in TiaCAD!
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        with pytest.raises(OperationsBuilderError) as exc_info:
            ops_builder.execute_operations(ops_spec)

        assert 'origin' in str(exc_info.value).lower()


class TestGuitarHangerPattern:
    """Test transform patterns from guitar hanger example"""

    def test_arm_positioning_pattern(self):
        """Test the arm positioning pattern from guitar hanger"""
        params = {
            'arm_spacing': 72,
            'arm_len': 70,
            'arm_tilt_deg': 10,
        }

        parts_spec = {
            'beam': {'primitive': 'box', 'parameters': {'width': 32, 'height': 75, 'depth': 24}},
            'arm': {'primitive': 'box', 'parameters': {'width': 22, 'height': '${arm_len}', 'depth': 16}}
        }

        resolver = ParameterResolver(params)
        parts_builder = PartsBuilder(resolver)
        registry = parts_builder.build_parts(parts_spec)

        # Left arm transform (from guitar hanger)
        ops_spec = {
            'left_arm_positioned': {
                'type': 'transform',
                'input': 'arm',
                'transforms': [
                    {
                        'translate': {
                            'to': [0, 37.5, 0],  # beam front center (beam_len/2)
                            'offset': ['${-arm_spacing / 2}', '${arm_len / 2}', 0]
                        }
                    },
                    {
                        'rotate': {
                            'angle': '${arm_tilt_deg}',
                            'axis': 'X',
                            'origin': [0, 37.5, 0]  # Pivot at beam front
                        }
                    }
                ]
            }
        }

        ops_builder = OperationsBuilder(registry, resolver)
        result_registry = ops_builder.execute_operations(ops_spec)

        left_arm = result_registry.get('left_arm_positioned')
        assert left_arm is not None
        # Left arm should be at negative X (left side)
        assert left_arm.current_position[0] < 0
