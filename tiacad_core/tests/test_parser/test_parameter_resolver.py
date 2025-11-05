"""
Tests for ParameterResolver

Tests parameter resolution, expression evaluation, and error handling.
"""

import pytest
import math
from tiacad_core.parser.parameter_resolver import (
    ParameterResolver,
    ParameterResolutionError
)


class TestBasicResolution:
    """Test basic parameter resolution"""

    def test_simple_values(self):
        """Test resolving simple scalar values"""
        params = {
            'width': 100,
            'height': 50,
            'name': 'test',
            'enabled': True,
            'disabled': False,
            'nothing': None,
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('width') == 100
        assert resolver.get_parameter('height') == 50
        assert resolver.get_parameter('name') == 'test'
        assert resolver.get_parameter('enabled') is True
        assert resolver.get_parameter('disabled') is False
        assert resolver.get_parameter('nothing') is None

    def test_simple_expression(self):
        """Test simple ${...} expression"""
        params = {
            'width': 100,
            'double_width': '${width * 2}'
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('double_width') == 200

    def test_arithmetic_operations(self):
        """Test arithmetic operations in expressions"""
        params = {
            'a': 10,
            'b': 3,
            'add': '${a + b}',
            'subtract': '${a - b}',
            'multiply': '${a * b}',
            'divide': '${a / b}',
            'modulo': '${a % b}',
            'power': '${a ** 2}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('add') == 13
        assert resolver.get_parameter('subtract') == 7
        assert resolver.get_parameter('multiply') == 30
        assert resolver.get_parameter('divide') == pytest.approx(3.333, abs=0.01)
        assert resolver.get_parameter('modulo') == 1
        assert resolver.get_parameter('power') == 100

    def test_parentheses_and_precedence(self):
        """Test expression precedence and parentheses"""
        params = {
            'a': 10,
            'b': 3,
            'c': 2,
            'expr1': '${a + b * c}',  # Should be 10 + 6 = 16
            'expr2': '${(a + b) * c}',  # Should be 13 * 2 = 26
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('expr1') == 16
        assert resolver.get_parameter('expr2') == 26


class TestFunctions:
    """Test function calls in expressions"""

    def test_min_max(self):
        """Test min() and max() functions"""
        params = {
            'a': 10,
            'b': 20,
            'minimum': '${min(a, b)}',
            'maximum': '${max(a, b)}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('minimum') == 10
        assert resolver.get_parameter('maximum') == 20

    def test_abs(self):
        """Test abs() function"""
        params = {
            'negative': -42,
            'absolute': '${abs(negative)}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('absolute') == 42

    def test_sqrt(self):
        """Test sqrt() function"""
        params = {
            'value': 16,
            'root': '${sqrt(value)}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('root') == 4.0

    def test_round_floor_ceil(self):
        """Test rounding functions"""
        params = {
            'value': 3.7,
            'rounded': '${round(value)}',
            'floored': '${floor(value)}',
            'ceiled': '${ceil(value)}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('rounded') == 4
        assert resolver.get_parameter('floored') == 3
        assert resolver.get_parameter('ceiled') == 4

    def test_trig_functions(self):
        """Test trigonometric functions"""
        params = {
            'angle': 0,
            'sine': '${sin(angle)}',
            'cosine': '${cos(angle)}',
            'pi_val': '${pi}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('sine') == pytest.approx(0.0)
        assert resolver.get_parameter('cosine') == pytest.approx(1.0)
        assert resolver.get_parameter('pi_val') == pytest.approx(math.pi)


class TestNestedReferences:
    """Test nested parameter references"""

    def test_simple_reference_chain(self):
        """Test parameters referencing other parameters"""
        params = {
            'base': 10,
            'level1': '${base * 2}',
            'level2': '${level1 + 5}',
            'level3': '${level2 * level1}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('base') == 10
        assert resolver.get_parameter('level1') == 20
        assert resolver.get_parameter('level2') == 25
        assert resolver.get_parameter('level3') == 500  # 25 * 20

    def test_complex_expressions(self):
        """Test complex expressions with multiple parameters"""
        params = {
            'width': 100,
            'height': 50,
            'depth': 25,
            'area': '${width * height}',
            'volume': '${width * height * depth}',
            'avg_dim': '${(width + height + depth) / 3}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('area') == 5000
        assert resolver.get_parameter('volume') == 125000
        assert resolver.get_parameter('avg_dim') == pytest.approx(58.333, abs=0.01)

    def test_caching(self):
        """Test that parameters are cached after first resolution"""
        params = {
            'expensive': '${10 * 20}',
            'uses_expensive': '${expensive + 5}',
        }
        resolver = ParameterResolver(params)

        # First resolution
        result1 = resolver.get_parameter('expensive')
        # Second resolution should use cache
        result2 = resolver.get_parameter('expensive')

        assert result1 == result2 == 200
        assert 'expensive' in resolver.resolved_cache


class TestStringSubstitution:
    """Test string substitution and mixed content"""

    def test_string_with_single_expression(self):
        """Test pure expression strings"""
        params = {
            'value': 42,
            'result': '${value}',
        }
        resolver = ParameterResolver(params)

        # Should return number, not string
        assert resolver.get_parameter('result') == 42
        assert isinstance(resolver.get_parameter('result'), int)

    def test_string_with_text_and_expression(self):
        """Test mixed text and expressions"""
        params = {
            'width': 100,
            'label': 'Width is ${width}mm',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('label') == 'Width is 100mm'

    def test_string_with_multiple_expressions(self):
        """Test multiple expressions in one string"""
        params = {
            'width': 100,
            'height': 50,
            'description': 'Size: ${width}x${height}mm',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('description') == 'Size: 100x50mm'

    def test_plain_string(self):
        """Test string without expressions"""
        params = {
            'name': 'My Part',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('name') == 'My Part'


class TestCollections:
    """Test resolution in lists and dicts"""

    def test_list_resolution(self):
        """Test resolving lists with expressions"""
        params = {
            'width': 100,
            'height': 50,
            'depth': 25,
            'size': ['${width}', '${height}', '${depth}'],
        }
        resolver = ParameterResolver(params)

        result = resolver.get_parameter('size')
        assert result == [100, 50, 25]

    def test_nested_list(self):
        """Test nested lists"""
        params = {
            'a': 1,
            'b': 2,
            'matrix': [
                ['${a}', '${b}'],
                ['${a * 2}', '${b * 2}']
            ]
        }
        resolver = ParameterResolver(params)

        result = resolver.get_parameter('matrix')
        assert result == [[1, 2], [2, 4]]

    def test_dict_resolution(self):
        """Test resolving dicts with expressions"""
        params = {
            'width': 100,
            'config': {
                'size': '${width}',
                'double': '${width * 2}',
                'label': 'Width ${width}'
            }
        }
        resolver = ParameterResolver(params)

        result = resolver.get_parameter('config')
        assert result['size'] == 100
        assert result['double'] == 200
        assert result['label'] == 'Width 100'


class TestResolveMethod:
    """Test the resolve() method for arbitrary values"""

    def test_resolve_scalar(self):
        """Test resolving scalar values"""
        resolver = ParameterResolver({'a': 10})

        assert resolver.resolve(42) == 42
        assert resolver.resolve(3.14) == 3.14
        assert resolver.resolve(True) is True
        assert resolver.resolve(None) is None

    def test_resolve_expression_string(self):
        """Test resolving string with expression"""
        resolver = ParameterResolver({'width': 100})

        result = resolver.resolve('${width * 2}')
        assert result == 200

    def test_resolve_list(self):
        """Test resolving list"""
        resolver = ParameterResolver({'a': 10})

        result = resolver.resolve(['${a}', '${a * 2}', 30])
        assert result == [10, 20, 30]

    def test_resolve_dict(self):
        """Test resolving dict"""
        resolver = ParameterResolver({'width': 100})

        result = resolver.resolve({
            'size': '${width}',
            'half': '${width / 2}',
            'fixed': 42
        })
        assert result == {'size': 100, 'half': 50, 'fixed': 42}


class TestResolveAll:
    """Test resolve_all() method"""

    def test_resolve_all_parameters(self):
        """Test resolving all parameters at once"""
        params = {
            'width': 100,
            'height': 50,
            'area': '${width * height}',
            'double_area': '${area * 2}',
        }
        resolver = ParameterResolver(params)

        result = resolver.resolve_all()

        assert result['width'] == 100
        assert result['height'] == 50
        assert result['area'] == 5000
        assert result['double_area'] == 10000


class TestErrorHandling:
    """Test error handling and validation"""

    def test_undefined_parameter(self):
        """Test referencing undefined parameter"""
        params = {
            'value': '${undefined_param}'
        }
        resolver = ParameterResolver(params)

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('value')

        assert 'undefined_param' in str(exc_info.value)

    def test_missing_parameter(self):
        """Test getting non-existent parameter"""
        resolver = ParameterResolver({'a': 10})

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('missing')

        assert 'missing' in str(exc_info.value)

    def test_circular_reference(self):
        """Test circular reference detection"""
        params = {
            'a': '${b}',
            'b': '${c}',
            'c': '${a}',  # Circular!
        }
        resolver = ParameterResolver(params)

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('a')

        # Circular references manifest as "not found" errors
        # because parameters in the resolution stack are excluded
        error_msg = str(exc_info.value).lower()
        assert 'not found' in error_msg or 'circular' in error_msg

    def test_self_reference(self):
        """Test self-referencing parameter"""
        params = {
            'a': '${a}',  # Self reference
        }
        resolver = ParameterResolver(params)

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('a')

        # Self-references manifest as "not found" errors
        error_msg = str(exc_info.value).lower()
        assert 'not found' in error_msg or 'circular' in error_msg

    def test_invalid_expression(self):
        """Test invalid expression syntax"""
        params = {
            'bad': '${1 / 0 * }',  # Actually invalid syntax
        }
        resolver = ParameterResolver(params)

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('bad')

        assert 'error' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    def test_division_by_zero(self):
        """Test division by zero"""
        params = {
            'zero': 0,
            'bad': '${10 / zero}',
        }
        resolver = ParameterResolver(params)

        with pytest.raises(ParameterResolutionError) as exc_info:
            resolver.get_parameter('bad')

        assert 'division by zero' in str(exc_info.value).lower()


class TestRealWorldExamples:
    """Test real-world parameter patterns from guitar hanger example"""

    def test_guitar_hanger_parameters(self):
        """Test parameters from guitar_hanger.yaml"""
        params = {
            # Basic dimensions
            'plate_w': 100,
            'plate_h': 80,
            'plate_t': 12,

            # Derived dimensions
            'screw_d': 5.0,
            'screw_spacing': 50,

            # Arms
            'arm_spacing': 72,
            'arm_len': 70,

            # Calculated positions
            'screw_upper': '${screw_spacing / 2}',
            'screw_lower': '${-screw_spacing / 2}',
            'arm_offset': '${arm_spacing / 2}',
            'arm_forward': '${arm_len / 2}',
        }
        resolver = ParameterResolver(params)

        assert resolver.get_parameter('screw_upper') == 25.0
        assert resolver.get_parameter('screw_lower') == -25.0
        assert resolver.get_parameter('arm_offset') == 36.0
        assert resolver.get_parameter('arm_forward') == 35.0

    def test_size_array_with_expressions(self):
        """Test size arrays with parameter expressions"""
        params = {
            'width': 100,
            'thickness': 12,
            'height': 80,
            'box_size': ['${width}', '${thickness}', '${height}'],
        }
        resolver = ParameterResolver(params)

        size = resolver.get_parameter('box_size')
        assert size == [100, 12, 80]

    def test_offset_calculation(self):
        """Test offset calculations for positioning"""
        params = {
            'arm_spacing': 72,
            'arm_len': 70,
            'left_offset': ['${-arm_spacing / 2}', '${arm_len / 2}', 0],
            'right_offset': ['${arm_spacing / 2}', '${arm_len / 2}', 0],
        }
        resolver = ParameterResolver(params)

        left = resolver.get_parameter('left_offset')
        right = resolver.get_parameter('right_offset')

        assert left == [-36.0, 35.0, 0]
        assert right == [36.0, 35.0, 0]
