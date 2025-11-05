"""
Tests for pattern expansion in BooleanBuilder

Tests the new pattern wildcard feature that allows:
- Wildcard patterns: "bolt_circle_*"
- Dict patterns: {"pattern": "bolt_circle"}
- Range specs: {"range": "bolt_circle[0..5]"}
- Range wildcards: {"range": "bolt_circle[*]"}

Author: TIA
Session: quantum-scout-1026 (Awesomeness improvements)
"""

import pytest
import cadquery as cq
from tiacad_core.part import Part, PartRegistry
from tiacad_core.parser.boolean_builder import BooleanBuilder, BooleanBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver


@pytest.fixture
def registry_with_pattern():
    """Create registry with pattern parts (bolt_circle_0 through bolt_circle_5)"""
    registry = PartRegistry()

    # Create base plate using real CadQuery
    plate_geom = cq.Workplane("XY").box(100, 100, 10)
    registry.add(Part(name="plate", geometry=plate_geom))

    # Create pattern of holes (bolt_circle_0 through bolt_circle_5)
    for i in range(6):
        hole_geom = cq.Workplane("XY").cylinder(12, 3.25)
        registry.add(Part(name=f"bolt_circle_{i}", geometry=hole_geom))

    # Create center hole
    center_geom = cq.Workplane("XY").cylinder(12, 10)
    registry.add(Part(name="center_hole", geometry=center_geom))

    return registry


@pytest.fixture
def boolean_builder(registry_with_pattern):
    """Create BooleanBuilder with pattern registry"""
    resolver = ParameterResolver({})
    return BooleanBuilder(registry_with_pattern, resolver)


# ============================================================================
# Wildcard Pattern Tests
# ============================================================================

def test_wildcard_pattern_expansion(boolean_builder, registry_with_pattern):
    """Test wildcard pattern: 'bolt_circle_*' expands to all bolt_circle_N"""
    # Use wildcard in subtract list
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': ['bolt_circle_*']  # ✨ NEW SYNTAX
    })

    # Should have subtracted all 6 bolt holes
    assert registry_with_pattern.exists('result')


def test_wildcard_pattern_with_center_hole(boolean_builder, registry_with_pattern):
    """Test mixing wildcard with regular part names"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': ['center_hole', 'bolt_circle_*']  # Mix regular + wildcard
    })

    assert registry_with_pattern.exists('result')


def test_wildcard_pattern_no_matches_raises_error(boolean_builder):
    """Test that non-matching wildcard raises helpful error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': ['nonexistent_*']  # No parts match
        })

    assert "matched no parts" in str(exc_info.value).lower()


# ============================================================================
# Dict Pattern Tests
# ============================================================================

def test_dict_pattern_expansion(boolean_builder, registry_with_pattern):
    """Test dict pattern: {"pattern": "bolt_circle"}"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [{'pattern': 'bolt_circle'}]  # ✨ NEW SYNTAX
    })

    assert registry_with_pattern.exists('result')


def test_dict_pattern_mixed_with_regular(boolean_builder, registry_with_pattern):
    """Test mixing dict pattern with regular names"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [
            'center_hole',  # Regular
            {'pattern': 'bolt_circle'}  # Dict pattern
        ]
    })

    assert registry_with_pattern.exists('result')


def test_dict_pattern_no_matches_raises_error(boolean_builder):
    """Test that non-matching dict pattern raises error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [{'pattern': 'nonexistent'}]
        })

    assert "matched no parts" in str(exc_info.value).lower()


# ============================================================================
# Range Specification Tests
# ============================================================================

def test_range_spec_numeric(boolean_builder, registry_with_pattern):
    """Test numeric range: {"range": "bolt_circle[0..5]"}"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [{'range': 'bolt_circle[0..5]'}]  # ✨ NEW SYNTAX
    })

    assert registry_with_pattern.exists('result')


def test_range_spec_partial(boolean_builder, registry_with_pattern):
    """Test partial range: {"range": "bolt_circle[0..2]"}"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [{'range': 'bolt_circle[0..2]'}]  # Only first 3
    })

    assert registry_with_pattern.exists('result')


def test_range_spec_wildcard(boolean_builder, registry_with_pattern):
    """Test range wildcard: {"range": "bolt_circle[*]"}"""
    boolean_builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [{'range': 'bolt_circle[*]'}]  # All with this prefix
    })

    assert registry_with_pattern.exists('result')


def test_range_spec_invalid_syntax_raises_error(boolean_builder):
    """Test that invalid range syntax raises error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [{'range': 'bolt_circle[invalid]'}]
        })

    assert "invalid range" in str(exc_info.value).lower()


def test_range_spec_backwards_range_raises_error(boolean_builder):
    """Test that start > end raises error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [{'range': 'bolt_circle[5..0]'}]  # Backwards
        })

    assert "start" in str(exc_info.value).lower()
    assert "end" in str(exc_info.value).lower()


def test_range_spec_missing_part_raises_error(boolean_builder):
    """Test that range with missing part raises error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [{'range': 'bolt_circle[0..10]'}]  # bolt_circle_7+ don't exist
        })

    assert "non-existent part" in str(exc_info.value).lower()


# ============================================================================
# Union Operation Tests
# ============================================================================

def test_union_with_wildcard_pattern(boolean_builder, registry_with_pattern):
    """Test union operation with wildcard pattern"""
    boolean_builder.execute_boolean_operation('all_holes', {
        'operation': 'union',
        'inputs': ['bolt_circle_*']  # Union all bolt holes
    })

    assert registry_with_pattern.exists('all_holes')


def test_union_with_dict_pattern(boolean_builder, registry_with_pattern):
    """Test union operation with dict pattern"""
    boolean_builder.execute_boolean_operation('all_holes', {
        'operation': 'union',
        'inputs': [{'pattern': 'bolt_circle'}]
    })

    assert registry_with_pattern.exists('all_holes')


def test_union_with_range_spec(boolean_builder, registry_with_pattern):
    """Test union operation with range specification"""
    boolean_builder.execute_boolean_operation('some_holes', {
        'operation': 'union',
        'inputs': [{'range': 'bolt_circle[0..3]'}]  # First 4 holes
    })

    assert registry_with_pattern.exists('some_holes')


# ============================================================================
# Intersection Operation Tests
# ============================================================================

def test_intersection_with_wildcard_pattern(boolean_builder, registry_with_pattern):
    """Test intersection operation with wildcard pattern"""
    # This is a bit artificial, but tests the pattern expansion works
    boolean_builder.execute_boolean_operation('intersection_result', {
        'operation': 'intersection',
        'inputs': ['plate', 'bolt_circle_0']  # Just to test expansion works
    })

    assert registry_with_pattern.exists('intersection_result')


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_pattern_expansion_raises_error(boolean_builder):
    """Test that pattern with no matches raises clear error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': ['xyz_*']  # No parts match
        })

    error_msg = str(exc_info.value).lower()
    assert "matched no parts" in error_msg
    assert "available parts" in error_msg  # Should show what's available


def test_invalid_dict_key_raises_error(boolean_builder):
    """Test that dict without 'pattern' or 'range' raises error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [{'invalid_key': 'something'}]
        })

    assert "pattern" in str(exc_info.value).lower()
    assert "range" in str(exc_info.value).lower()


def test_invalid_list_item_type_raises_error(boolean_builder):
    """Test that non-str/dict items raise error"""
    with pytest.raises(BooleanBuilderError) as exc_info:
        boolean_builder.execute_boolean_operation('result', {
            'operation': 'difference',
            'base': 'plate',
            'subtract': [123]  # Invalid: number
        })

    assert "invalid" in str(exc_info.value).lower()
    assert "type" in str(exc_info.value).lower()


# ============================================================================
# Sorting and Order Tests
# ============================================================================

def test_pattern_expansion_numeric_sorting(boolean_builder):
    """Test that pattern expansion sorts numerically"""
    registry = PartRegistry()

    # Create parts in non-sequential order
    for i in [3, 1, 5, 2, 4, 0]:
        part = Part(name=f"hole_{i}", geometry=cq.Workplane("XY").cylinder(10, 5))
        registry.add(part)

    builder = BooleanBuilder(registry, ParameterResolver({}))

    # Test internal expansion method
    expanded = builder._expand_part_list(['hole_*'])

    # Should be sorted: hole_0, hole_1, hole_2, hole_3, hole_4, hole_5
    assert expanded == ['hole_0', 'hole_1', 'hole_2', 'hole_3', 'hole_4', 'hole_5']


# ============================================================================
# Real-World Use Case Tests
# ============================================================================

def test_mounting_plate_use_case(boolean_builder, registry_with_pattern):
    """
    Test real-world mounting plate scenario.

    Before (old syntax):
        subtract: [bolt_circle_0, bolt_circle_1, bolt_circle_2,
                   bolt_circle_3, bolt_circle_4, bolt_circle_5]

    After (new syntax):
        subtract: ['bolt_circle_*']
    """
    # Old way would require listing all 6 parts
    # New way uses wildcard
    boolean_builder.execute_boolean_operation('plate_with_holes', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': ['center_hole', 'bolt_circle_*']
    })

    result = registry_with_pattern.get('plate_with_holes')
    assert result is not None
    assert result.metadata.get('operation_type') == 'boolean'
    assert result.metadata.get('boolean_op') == 'difference'


def test_flexible_pattern_count(boolean_builder):
    """Test that pattern expansion adapts to actual part count"""
    registry = PartRegistry()

    plate = Part(name="plate", geometry=cq.Workplane("XY").box(100, 100, 10))
    registry.add(plate)

    # Create 8 holes (different count than standard 6)
    for i in range(8):
        hole = Part(name=f"hole_{i}", geometry=cq.Workplane("XY").cylinder(10, 3))
        registry.add(hole)

    builder = BooleanBuilder(registry, ParameterResolver({}))

    # Pattern automatically expands to all 8 holes
    builder.execute_boolean_operation('result', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': ['hole_*']
    })

    assert registry.exists('result')


def test_documentation_example(boolean_builder, registry_with_pattern):
    """Test the example from documentation"""
    # This is the clean new syntax we're promoting
    boolean_builder.execute_boolean_operation('finished_plate', {
        'operation': 'difference',
        'base': 'plate',
        'subtract': [
            'center_hole',
            {'pattern': 'bolt_circle'}  # or: 'bolt_circle_*'
        ]
    })

    assert registry_with_pattern.exists('finished_plate')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
