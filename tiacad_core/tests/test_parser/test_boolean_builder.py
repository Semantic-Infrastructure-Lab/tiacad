"""
Tests for BooleanBuilder - Boolean operations on Part objects

Test Coverage:
- Union operations (8 tests)
- Difference operations (10 tests)
- Intersection operations (8 tests)
- Integration tests (4 tests)

Total: 30 tests

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import pytest
import cadquery as cq

from tiacad_core.parser.boolean_builder import BooleanBuilder, BooleanBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part, PartRegistry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Create a PartRegistry with some test parts."""
    reg = PartRegistry()

    # Box 1: 10x10x10 at origin
    box1 = cq.Workplane("XY").box(10, 10, 10)
    reg.add(Part("box1", box1))

    # Box 2: 10x10x10 offset by 5mm in X (overlapping with box1)
    box2 = cq.Workplane("XY").box(10, 10, 10).translate((5, 0, 0))
    reg.add(Part("box2", box2))

    # Box 3: 10x10x10 offset by 5mm in Y
    box3 = cq.Workplane("XY").box(10, 10, 10).translate((0, 5, 0))
    reg.add(Part("box3", box3))

    # Small cylinder for holes: radius 2, height 15 (taller than boxes)
    hole = cq.Workplane("XY").circle(2).extrude(15).translate((0, 0, -7.5))
    reg.add(Part("hole", hole))

    # Hole offset to the left
    hole_left = cq.Workplane("XY").circle(2).extrude(15).translate((-3, 0, -7.5))
    reg.add(Part("hole_left", hole_left))

    # Hole offset to the right
    hole_right = cq.Workplane("XY").circle(2).extrude(15).translate((3, 0, -7.5))
    reg.add(Part("hole_right", hole_right))

    return reg


@pytest.fixture
def resolver():
    """Create a basic ParameterResolver."""
    params = {
        'spacing': 6,
        'diameter': 4
    }
    return ParameterResolver(params)


@pytest.fixture
def builder(registry, resolver):
    """Create a BooleanBuilder instance."""
    return BooleanBuilder(registry, resolver)


# ============================================================================
# Union Tests (8 tests)
# ============================================================================

def test_union_two_boxes(builder, registry):
    """Test union of two boxes."""
    spec = {
        'operation': 'union',
        'inputs': ['box1', 'box2']
    }

    builder.execute_boolean_operation('union_result', spec)

    # Verify result exists
    assert registry.exists('union_result')
    result = registry.get('union_result')

    # Result should have geometry
    assert result.geometry is not None

    # Volume should be more than one box (1000) but less than two (2000)
    # because they overlap
    volume = result.geometry.val().Volume()
    assert 1000 < volume < 2000, f"Expected volume between 1000 and 2000, got {volume}"


def test_union_three_parts(builder, registry):
    """Test union of three parts."""
    spec = {
        'operation': 'union',
        'inputs': ['box1', 'box2', 'box3']
    }

    builder.execute_boolean_operation('triple_union', spec)

    # Verify result exists
    assert registry.exists('triple_union')
    result = registry.get('triple_union')
    assert result.geometry is not None


def test_union_with_parameters(registry):
    """Test union with parameter expressions."""
    params = {
        'part_a': 'box1',
        'part_b': 'box2'
    }
    resolver = ParameterResolver(params)
    builder = BooleanBuilder(registry, resolver)

    spec = {
        'operation': 'union',
        'inputs': ['${part_a}', '${part_b}']
    }

    builder.execute_boolean_operation('param_union', spec)

    assert registry.exists('param_union')


def test_union_missing_inputs(builder):
    """Test union fails without inputs field."""
    spec = {
        'operation': 'union'
        # Missing 'inputs'
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_union', spec)

    assert "missing 'inputs' field" in str(exc_info.value)


def test_union_too_few_inputs(builder):
    """Test union fails with less than 2 inputs."""
    spec = {
        'operation': 'union',
        'inputs': ['box1']  # Only one input
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_union', spec)

    assert "at least 2 inputs" in str(exc_info.value)


def test_union_nonexistent_part(builder):
    """Test union fails with non-existent part reference."""
    spec = {
        'operation': 'union',
        'inputs': ['box1', 'nonexistent_part']
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_union', spec)

    assert "not found" in str(exc_info.value)
    assert "nonexistent_part" in str(exc_info.value)


def test_union_invalid_inputs_type(builder):
    """Test union fails when inputs is not a list."""
    spec = {
        'operation': 'union',
        'inputs': 'box1'  # String instead of list
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_union', spec)

    assert "must be a list" in str(exc_info.value)


def test_union_preserves_geometry(builder, registry):
    """Test union geometry is valid (volume check)."""
    spec = {
        'operation': 'union',
        'inputs': ['box1', 'box2']
    }

    builder.execute_boolean_operation('union_check', spec)

    result = registry.get('union_check')

    # Volume should be positive
    volume = result.geometry.val().Volume()
    assert volume > 0

    # Bounding box should encompass both boxes
    bbox = result.geometry.val().BoundingBox()
    # box1 is -5 to 5 in X, box2 extends from 0 to 10
    # So union should go from -5 to 10 in X
    assert bbox.xmin < -4
    assert bbox.xmax > 9


# ============================================================================
# Difference Tests (10 tests)
# ============================================================================

def test_difference_box_with_hole(builder, registry):
    """Test difference: box with single hole."""
    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': ['hole']
    }

    builder.execute_boolean_operation('box_with_hole', spec)

    # Verify result exists
    assert registry.exists('box_with_hole')
    result = registry.get('box_with_hole')
    assert result.geometry is not None

    # Volume should be less than original box (1000)
    volume = result.geometry.val().Volume()
    assert volume < 1000, f"Expected volume < 1000, got {volume}"


def test_difference_multiple_subtractions(builder, registry):
    """Test difference: subtract multiple parts."""
    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': ['hole_left', 'hole_right']
    }

    builder.execute_boolean_operation('box_two_holes', spec)

    assert registry.exists('box_two_holes')
    result = registry.get('box_two_holes')

    # Volume should be less than original
    volume = result.geometry.val().Volume()
    assert volume < 1000


def test_difference_with_parameters(registry):
    """Test difference with parameter expressions."""
    params = {
        'base_part': 'box1',
        'hole_part': 'hole'
    }
    resolver = ParameterResolver(params)
    builder = BooleanBuilder(registry, resolver)

    spec = {
        'operation': 'difference',
        'base': '${base_part}',
        'subtract': ['${hole_part}']
    }

    builder.execute_boolean_operation('param_diff', spec)

    assert registry.exists('param_diff')


def test_difference_missing_base(builder):
    """Test difference fails without base field."""
    spec = {
        'operation': 'difference',
        'subtract': ['hole']
        # Missing 'base'
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "missing 'base' field" in str(exc_info.value)


def test_difference_missing_subtract(builder):
    """Test difference fails without subtract field."""
    spec = {
        'operation': 'difference',
        'base': 'box1'
        # Missing 'subtract'
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "missing 'subtract' field" in str(exc_info.value)


def test_difference_empty_subtract_list(builder):
    """Test difference fails with empty subtract list."""
    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': []  # Empty list
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "cannot be empty" in str(exc_info.value)


def test_difference_nonexistent_base(builder):
    """Test difference fails with non-existent base part."""
    spec = {
        'operation': 'difference',
        'base': 'nonexistent_base',
        'subtract': ['hole']
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "not found" in str(exc_info.value)
    assert "nonexistent_base" in str(exc_info.value)


def test_difference_nonexistent_subtract_part(builder):
    """Test difference fails with non-existent subtract part."""
    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': ['nonexistent_hole']
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "not found" in str(exc_info.value)
    assert "nonexistent_hole" in str(exc_info.value)


def test_difference_invalid_subtract_type(builder):
    """Test difference fails when subtract is not a list."""
    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': 'hole'  # String instead of list
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_diff', spec)

    assert "must be a list" in str(exc_info.value)


def test_difference_reduces_volume(builder, registry):
    """Test difference reduces volume as expected."""
    # Get original volume
    original_volume = registry.get('box1').geometry.val().Volume()

    spec = {
        'operation': 'difference',
        'base': 'box1',
        'subtract': ['hole']
    }

    builder.execute_boolean_operation('reduced_box', spec)

    result_volume = registry.get('reduced_box').geometry.val().Volume()

    # Result should have less volume
    assert result_volume < original_volume

    # Difference should be approximately the volume of the intersecting part
    # Hole is radius 2, height ~10 (intersecting with box), so ~125 mm³
    volume_diff = original_volume - result_volume
    assert 100 < volume_diff < 200, f"Expected volume diff 100-200, got {volume_diff}"


# ============================================================================
# Intersection Tests (8 tests)
# ============================================================================

def test_intersection_two_overlapping_boxes(builder, registry):
    """Test intersection of two overlapping boxes."""
    spec = {
        'operation': 'intersection',
        'inputs': ['box1', 'box2']
    }

    builder.execute_boolean_operation('overlap_result', spec)

    # Verify result exists
    assert registry.exists('overlap_result')
    result = registry.get('overlap_result')
    assert result.geometry is not None

    # Volume should be less than either box
    volume = result.geometry.val().Volume()
    assert 0 < volume < 1000, f"Expected volume 0-1000, got {volume}"


def test_intersection_three_parts(builder, registry):
    """Test intersection of three parts."""
    spec = {
        'operation': 'intersection',
        'inputs': ['box1', 'box2', 'box3']
    }

    builder.execute_boolean_operation('triple_intersection', spec)

    # Verify result exists
    assert registry.exists('triple_intersection')
    result = registry.get('triple_intersection')
    assert result.geometry is not None


def test_intersection_with_parameters(registry):
    """Test intersection with parameter expressions."""
    params = {
        'part1': 'box1',
        'part2': 'box2'
    }
    resolver = ParameterResolver(params)
    builder = BooleanBuilder(registry, resolver)

    spec = {
        'operation': 'intersection',
        'inputs': ['${part1}', '${part2}']
    }

    builder.execute_boolean_operation('param_intersect', spec)

    assert registry.exists('param_intersect')


def test_intersection_missing_inputs(builder):
    """Test intersection fails without inputs field."""
    spec = {
        'operation': 'intersection'
        # Missing 'inputs'
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_intersect', spec)

    assert "missing 'inputs' field" in str(exc_info.value)


def test_intersection_too_few_inputs(builder):
    """Test intersection fails with less than 2 inputs."""
    spec = {
        'operation': 'intersection',
        'inputs': ['box1']  # Only one input
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_intersect', spec)

    assert "at least 2 inputs" in str(exc_info.value)


def test_intersection_nonexistent_part(builder):
    """Test intersection fails with non-existent part reference."""
    spec = {
        'operation': 'intersection',
        'inputs': ['box1', 'nonexistent_part']
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_intersect', spec)

    assert "not found" in str(exc_info.value)
    assert "nonexistent_part" in str(exc_info.value)


def test_intersection_invalid_inputs_type(builder):
    """Test intersection fails when inputs is not a list."""
    spec = {
        'operation': 'intersection',
        'inputs': 'box1'  # String instead of list
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_intersect', spec)

    assert "must be a list" in str(exc_info.value)


def test_intersection_produces_expected_volume(builder, registry):
    """Test intersection produces correct volume."""
    spec = {
        'operation': 'intersection',
        'inputs': ['box1', 'box2']
    }

    builder.execute_boolean_operation('intersect_check', spec)

    result = registry.get('intersect_check')
    volume = result.geometry.val().Volume()

    # box1 is -5 to 5 in X, box2 is 0 to 10 in X
    # Intersection is 0 to 5 in X, so 5x10x10 = 500 mm³
    assert 400 < volume < 600, f"Expected volume ~500, got {volume}"


# ============================================================================
# Integration Tests (4 tests)
# ============================================================================

def test_integration_parse_yaml_with_union():
    """Test end-to-end: Parse YAML with union operation."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Union Test

parameters:
  size: 10

parts:
  box_a:
    primitive: box
    size: ['${size}', '${size}', '${size}']

  box_b:
    primitive: box
    size: ['${size}', '${size}', '${size}']

operations:
  combined:
    type: boolean
    operation: union
    inputs:
      - box_a
      - box_b
"""

    # Write temporary YAML file
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        # Parse
        doc = parse(temp_path)

        # Verify combined part exists
        assert doc.parts.exists('combined')

        # Verify it has geometry
        combined = doc.parts.get('combined')
        assert combined.geometry is not None

    finally:
        os.unlink(temp_path)


def test_integration_parse_yaml_with_difference():
    """Test end-to-end: Parse YAML with difference operation."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Difference Test

parts:
  plate:
    primitive: box
    size: [20, 20, 5]

  hole:
    primitive: cylinder
    radius: 3
    height: 10
    origin: base

operations:
  plate_with_hole:
    type: boolean
    operation: difference
    base: plate
    subtract:
      - hole
"""

    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        doc = parse(temp_path)

        # Verify result exists
        assert doc.parts.exists('plate_with_hole')

        # Volume should be less than original plate
        result = doc.parts.get('plate_with_hole')
        volume = result.geometry.val().Volume()
        assert volume < 2000  # 20*20*5 = 2000

    finally:
        os.unlink(temp_path)


def test_integration_chain_transform_then_boolean(registry, resolver):
    """Test chaining: transform then boolean."""
    from tiacad_core.parser.operations_builder import OperationsBuilder

    # Create operations builder
    ops_builder = OperationsBuilder(registry, resolver)

    # First: transform box2 to move it
    transform_spec = {
        'type': 'transform',
        'input': 'box2',
        'transforms': [
            {'translate': [10, 0, 0]}
        ]
    }
    ops_builder.execute_operation('box2_moved', transform_spec)

    # Now: union original box1 with moved box2
    boolean_builder = BooleanBuilder(registry, resolver)
    union_spec = {
        'operation': 'union',
        'inputs': ['box1', 'box2_moved']
    }
    boolean_builder.execute_boolean_operation('final_union', union_spec)

    # Verify result exists
    assert registry.exists('final_union')


def test_integration_boolean_then_transform(registry, resolver):
    """Test chaining: boolean then transform."""
    from tiacad_core.parser.operations_builder import OperationsBuilder

    # First: union two boxes
    boolean_builder = BooleanBuilder(registry, resolver)
    union_spec = {
        'operation': 'union',
        'inputs': ['box1', 'box2']
    }
    boolean_builder.execute_boolean_operation('unioned', union_spec)

    # Now: transform the result
    ops_builder = OperationsBuilder(registry, resolver)
    transform_spec = {
        'type': 'transform',
        'input': 'unioned',
        'transforms': [
            {'translate': [0, 0, 10]}
        ]
    }
    ops_builder.execute_operation('unioned_moved', transform_spec)

    # Verify result exists
    assert registry.exists('unioned_moved')
    result = registry.get('unioned_moved')

    # Check position was updated
    assert result.current_position[2] == 10  # Z position should be 10


# ============================================================================
# Additional Edge Cases
# ============================================================================

def test_unknown_boolean_operation(builder):
    """Test error on unknown boolean operation."""
    spec = {
        'operation': 'invalid_op',
        'inputs': ['box1', 'box2']
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('bad_op', spec)

    assert "Unknown boolean operation" in str(exc_info.value)
    assert "invalid_op" in str(exc_info.value)


def test_missing_operation_field(builder):
    """Test error when operation field is missing."""
    spec = {
        'inputs': ['box1', 'box2']
        # Missing 'operation'
    }

    with pytest.raises(BooleanBuilderError) as exc_info:
        builder.execute_boolean_operation('no_op', spec)

    assert "missing 'operation' field" in str(exc_info.value)
