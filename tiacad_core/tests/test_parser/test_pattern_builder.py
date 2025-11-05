"""
Tests for PatternBuilder - Pattern operations on Part objects

Test Coverage:
- Linear pattern operations (10 tests)
- Circular pattern operations (12 tests)
- Grid pattern operations (10 tests)
- Integration tests (6 tests)

Total: 38 tests

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import pytest
import cadquery as cq
import math

from tiacad_core.parser.pattern_builder import PatternBuilder, PatternBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part, PartRegistry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Create a PartRegistry with test parts."""
    reg = PartRegistry()

    # Simple box
    box = cq.Workplane("XY").box(10, 10, 10)
    reg.add(Part("box", box))

    # Small hole for patterns
    hole = cq.Workplane("XY").circle(2).extrude(5).translate((0, 0, -2.5))
    reg.add(Part("hole", hole))

    # Marker (small sphere) for position verification
    marker = cq.Workplane("XY").sphere(1)
    reg.add(Part("marker", marker))

    return reg


@pytest.fixture
def resolver():
    """Create a basic ParameterResolver."""
    params = {
        'count': 4,
        'spacing': 25,
        'radius': 50
    }
    return ParameterResolver(params)


@pytest.fixture
def builder(registry, resolver):
    """Create a PatternBuilder instance."""
    return PatternBuilder(registry, resolver)


# ============================================================================
# Linear Pattern Tests (10 tests)
# ============================================================================

def test_linear_basic(builder, registry):
    """Test basic linear pattern with X spacing."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 4,
        'spacing': [20, 0, 0]
    }

    parts = builder.execute_pattern_operation('hole_row', spec)

    # Verify correct number of parts created
    assert len(parts) == 4

    # Verify parts exist in registry
    for i in range(4):
        assert registry.exists(f'hole_row_{i}')

    # Verify positions
    for i in range(4):
        part = registry.get(f'hole_row_{i}')
        expected_x = 20 * i
        assert part.current_position[0] == expected_x
        assert part.current_position[1] == 0
        assert part.current_position[2] == 0


def test_linear_with_y_z_spacing(builder, registry):
    """Test linear pattern with Y and Z spacing."""
    spec = {
        'pattern': 'linear',
        'input': 'marker',
        'count': 3,
        'spacing': [0, 15, 5]  # Y and Z movement
    }

    parts = builder.execute_pattern_operation('markers', spec)

    assert len(parts) == 3

    # Check positions
    part0 = registry.get('markers_0')
    part1 = registry.get('markers_1')
    part2 = registry.get('markers_2')

    assert part0.current_position == (0, 0, 0)
    assert part1.current_position == (0, 15, 5)
    assert part2.current_position == (0, 30, 10)


def test_linear_with_start_offset(builder, registry):
    """Test linear pattern with start offset."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 3,
        'spacing': [10, 0, 0],
        'start_offset': [-20, 5, 0]
    }

    parts = builder.execute_pattern_operation('offset_holes', spec)

    assert len(parts) == 3

    # Positions should be: start_offset + (spacing * i)
    part0 = registry.get('offset_holes_0')
    part1 = registry.get('offset_holes_1')
    part2 = registry.get('offset_holes_2')

    assert part0.current_position == (-20, 5, 0)
    assert part1.current_position == (-10, 5, 0)
    assert part2.current_position == (0, 5, 0)


def test_linear_with_parameters(registry):
    """Test linear pattern with parameter expressions."""
    params = {
        'hole_count': 5,
        'hole_spacing': 12.5
    }
    resolver = ParameterResolver(params)
    builder = PatternBuilder(registry, resolver)

    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': '${hole_count}',
        'spacing': ['${hole_spacing}', 0, 0]
    }

    parts = builder.execute_pattern_operation('param_holes', spec)

    assert len(parts) == 5

    # Check spacing is correct
    part1 = registry.get('param_holes_1')
    assert part1.current_position[0] == 12.5


def test_linear_single_copy(builder, registry):
    """Test linear pattern with count=1."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 1,
        'spacing': [10, 0, 0]
    }

    parts = builder.execute_pattern_operation('single', spec)

    assert len(parts) == 1
    assert registry.exists('single_0')


def test_linear_missing_input(builder):
    """Test linear pattern fails without input field."""
    spec = {
        'pattern': 'linear',
        'count': 3,
        'spacing': [10, 0, 0]
        # Missing 'input'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_linear', spec)

    assert "missing 'input' field" in str(exc_info.value)


def test_linear_missing_count(builder):
    """Test linear pattern fails without count field."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'spacing': [10, 0, 0]
        # Missing 'count'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_linear', spec)

    assert "missing 'count' field" in str(exc_info.value)


def test_linear_missing_spacing(builder):
    """Test linear pattern fails without spacing field."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 3
        # Missing 'spacing'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_linear', spec)

    assert "missing 'spacing' field" in str(exc_info.value)


def test_linear_nonexistent_part(builder):
    """Test linear pattern fails with non-existent input part."""
    spec = {
        'pattern': 'linear',
        'input': 'nonexistent',
        'count': 3,
        'spacing': [10, 0, 0]
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_linear', spec)

    assert "not found" in str(exc_info.value)
    assert "nonexistent" in str(exc_info.value)


def test_linear_naming(builder, registry):
    """Test linear pattern creates correctly named parts."""
    spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 3,
        'spacing': [10, 0, 0]
    }

    parts = builder.execute_pattern_operation('test_pattern', spec)

    # Verify names
    assert parts[0].name == 'test_pattern_0'
    assert parts[1].name == 'test_pattern_1'
    assert parts[2].name == 'test_pattern_2'

    # Verify metadata
    assert parts[0].metadata['pattern_type'] == 'linear'
    assert parts[0].metadata['pattern_index'] == 0
    assert parts[1].metadata['pattern_index'] == 1


# ============================================================================
# Circular Pattern Tests (12 tests)
# ============================================================================

def test_circular_basic(builder, registry):
    """Test basic circular pattern (full circle)."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 6,
        'axis': 'Z',
        'center': [0, 0, 0]
    }

    parts = builder.execute_pattern_operation('circle', spec)

    # Verify count
    assert len(parts) == 6

    # Verify all parts exist
    for i in range(6):
        assert registry.exists(f'circle_{i}')

    # Verify metadata includes angles
    assert parts[0].metadata['angle'] == 0
    assert parts[1].metadata['angle'] == 60
    assert parts[2].metadata['angle'] == 120


def test_circular_with_custom_angles(builder, registry):
    """Test circular pattern with custom start/end angles."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 4,
        'axis': 'Z',
        'center': [0, 0, 0],
        'start_angle': 45,
        'end_angle': 135
    }

    parts = builder.execute_pattern_operation('arc', spec)

    assert len(parts) == 4

    # Check angles (45° to 135° in 4 steps = 22.5° increments)
    assert parts[0].metadata['angle'] == 45
    assert parts[1].metadata['angle'] == pytest.approx(67.5)
    assert parts[2].metadata['angle'] == pytest.approx(90)
    assert parts[3].metadata['angle'] == pytest.approx(112.5)


def test_circular_with_radius(builder, registry):
    """Test circular pattern with radius offset."""
    spec = {
        'pattern': 'circular',
        'input': 'hole',
        'count': 4,
        'axis': 'Z',
        'center': [0, 0, 0],
        'radius': 30
    }

    parts = builder.execute_pattern_operation('bolt_circle', spec)

    assert len(parts) == 4

    # Verify parts were created
    for i in range(4):
        assert registry.exists(f'bolt_circle_{i}')


def test_circular_around_x_axis(builder, registry):
    """Test circular pattern around X axis."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 4,
        'axis': 'X',
        'center': [0, 0, 0]
    }

    parts = builder.execute_pattern_operation('x_circle', spec)

    assert len(parts) == 4


def test_circular_around_y_axis(builder, registry):
    """Test circular pattern around Y axis."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 4,
        'axis': 'Y',
        'center': [0, 0, 0]
    }

    parts = builder.execute_pattern_operation('y_circle', spec)

    assert len(parts) == 4


def test_circular_around_custom_axis(builder, registry):
    """Test circular pattern around custom axis vector."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 3,
        'axis': [1, 1, 0],  # 45° between X and Y
        'center': [0, 0, 0]
    }

    parts = builder.execute_pattern_operation('custom_circle', spec)

    assert len(parts) == 3


def test_circular_with_parameters(registry):
    """Test circular pattern with parameter expressions."""
    params = {
        'bolt_count': 8,
        'bolt_radius': 40
    }
    resolver = ParameterResolver(params)
    builder = PatternBuilder(registry, resolver)

    spec = {
        'pattern': 'circular',
        'input': 'hole',
        'count': '${bolt_count}',
        'axis': 'Z',
        'center': [0, 0, 0],
        'radius': '${bolt_radius}'
    }

    parts = builder.execute_pattern_operation('param_circle', spec)

    assert len(parts) == 8


def test_circular_missing_center(builder):
    """Test circular pattern fails without center field."""
    spec = {
        'pattern': 'circular',
        'input': 'hole',
        'count': 4,
        'axis': 'Z'
        # Missing 'center'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_circle', spec)

    assert "missing 'center' field" in str(exc_info.value)


def test_circular_missing_axis(builder):
    """Test circular pattern fails without axis field."""
    spec = {
        'pattern': 'circular',
        'input': 'hole',
        'count': 4,
        'center': [0, 0, 0]
        # Missing 'axis'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_circle', spec)

    assert "missing 'axis' field" in str(exc_info.value)


def test_circular_invalid_axis(builder):
    """Test circular pattern fails with invalid axis."""
    spec = {
        'pattern': 'circular',
        'input': 'hole',
        'count': 4,
        'axis': 'W',  # Invalid axis
        'center': [0, 0, 0]
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_circle', spec)

    assert "invalid axis" in str(exc_info.value).lower()


def test_circular_nonexistent_part(builder):
    """Test circular pattern fails with non-existent input part."""
    spec = {
        'pattern': 'circular',
        'input': 'nonexistent',
        'count': 4,
        'axis': 'Z',
        'center': [0, 0, 0]
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_circle', spec)

    assert "not found" in str(exc_info.value)


def test_circular_naming(builder, registry):
    """Test circular pattern creates correctly named parts."""
    spec = {
        'pattern': 'circular',
        'input': 'marker',
        'count': 3,
        'axis': 'Z',
        'center': [0, 0, 0]
    }

    parts = builder.execute_pattern_operation('test_circle', spec)

    # Verify names
    assert parts[0].name == 'test_circle_0'
    assert parts[1].name == 'test_circle_1'
    assert parts[2].name == 'test_circle_2'

    # Verify metadata
    assert parts[0].metadata['pattern_type'] == 'circular'
    assert parts[0].metadata['source'] == 'marker'


# ============================================================================
# Grid Pattern Tests (10 tests)
# ============================================================================

def test_grid_basic(builder, registry):
    """Test basic grid pattern (3x4)."""
    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'count': [3, 4],  # 3 rows, 4 columns
        'spacing': [25, 20, 0]
    }

    parts = builder.execute_pattern_operation('hole_grid', spec)

    # Verify count
    assert len(parts) == 12  # 3 * 4

    # Verify all parts exist
    for row in range(3):
        for col in range(4):
            assert registry.exists(f'hole_grid_{row}_{col}')

    # Verify positions
    part_0_0 = registry.get('hole_grid_0_0')
    part_1_2 = registry.get('hole_grid_1_2')

    assert part_0_0.current_position == (0, 0, 0)
    assert part_1_2.current_position == (25, 40, 0)  # 1*25, 2*20


def test_grid_with_centering(builder, registry):
    """Test grid pattern with centering enabled."""
    spec = {
        'pattern': 'grid',
        'input': 'marker',
        'count': [2, 2],
        'spacing': [10, 10, 0],
        'center_grid': True
    }

    parts = builder.execute_pattern_operation('centered', spec)

    assert len(parts) == 4

    # With 2x2 grid and spacing 10, centered grid should go from -5 to 5
    part_0_0 = registry.get('centered_0_0')
    part_1_1 = registry.get('centered_1_1')

    assert part_0_0.current_position == (-5, -5, 0)
    assert part_1_1.current_position == (5, 5, 0)


def test_grid_with_start_offset(builder, registry):
    """Test grid pattern with start offset."""
    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'count': [2, 2],
        'spacing': [10, 10, 0],
        'start_offset': [100, 200, 5]
    }

    parts = builder.execute_pattern_operation('offset_grid', spec)

    assert len(parts) == 4

    part_0_0 = registry.get('offset_grid_0_0')
    assert part_0_0.current_position == (100, 200, 5)

    part_1_1 = registry.get('offset_grid_1_1')
    assert part_1_1.current_position == (110, 210, 5)


def test_grid_with_parameters(registry):
    """Test grid pattern with parameter expressions."""
    params = {
        'rows': 3,
        'cols': 5,
        'x_spacing': 15,
        'y_spacing': 12
    }
    resolver = ParameterResolver(params)
    builder = PatternBuilder(registry, resolver)

    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'count': ['${rows}', '${cols}'],
        'spacing': ['${x_spacing}', '${y_spacing}', 0]
    }

    parts = builder.execute_pattern_operation('param_grid', spec)

    assert len(parts) == 15  # 3 * 5


def test_grid_with_z_offset(builder, registry):
    """Test grid pattern with Z offset in spacing."""
    spec = {
        'pattern': 'grid',
        'input': 'marker',
        'count': [2, 2],
        'spacing': [10, 10, 5]  # Z offset of 5
    }

    parts = builder.execute_pattern_operation('z_grid', spec)

    # All parts should be at Z=5
    for row in range(2):
        for col in range(2):
            part = registry.get(f'z_grid_{row}_{col}')
            assert part.current_position[2] == 5


def test_grid_missing_count(builder):
    """Test grid pattern fails without count field."""
    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'spacing': [10, 10, 0]
        # Missing 'count'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_grid', spec)

    assert "missing 'count' field" in str(exc_info.value)


def test_grid_missing_spacing(builder):
    """Test grid pattern fails without spacing field."""
    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'count': [2, 2]
        # Missing 'spacing'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_grid', spec)

    assert "missing 'spacing' field" in str(exc_info.value)


def test_grid_invalid_count(builder):
    """Test grid pattern fails with invalid count."""
    spec = {
        'pattern': 'grid',
        'input': 'hole',
        'count': [2],  # Should be [rows, cols]
        'spacing': [10, 10, 0]
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_grid', spec)

    assert "must be [rows, columns]" in str(exc_info.value)


def test_grid_nonexistent_part(builder):
    """Test grid pattern fails with non-existent input part."""
    spec = {
        'pattern': 'grid',
        'input': 'nonexistent',
        'count': [2, 2],
        'spacing': [10, 10, 0]
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_grid', spec)

    assert "not found" in str(exc_info.value)


def test_grid_naming(builder, registry):
    """Test grid pattern creates correctly named parts."""
    spec = {
        'pattern': 'grid',
        'input': 'marker',
        'count': [2, 3],
        'spacing': [10, 10, 0]
    }

    parts = builder.execute_pattern_operation('test_grid', spec)

    # Verify names (row_col format)
    assert registry.exists('test_grid_0_0')
    assert registry.exists('test_grid_0_1')
    assert registry.exists('test_grid_0_2')
    assert registry.exists('test_grid_1_0')
    assert registry.exists('test_grid_1_1')
    assert registry.exists('test_grid_1_2')

    # Verify metadata
    assert parts[0].metadata['pattern_type'] == 'grid'
    assert parts[0].metadata['grid_position'] == (0, 0)
    assert parts[3].metadata['grid_position'] == (1, 0)


# ============================================================================
# Integration Tests (6 tests)
# ============================================================================

def test_integration_parse_yaml_with_linear_pattern():
    """Test end-to-end: Parse YAML with linear pattern."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Linear Pattern Test

parts:
  hole:
    primitive: cylinder
    radius: 2
    height: 5
    origin: center

operations:
  hole_row:
    type: pattern
    pattern: linear
    input: hole
    count: 4
    spacing: [20, 0, 0]
"""

    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        doc = parse(temp_path)

        # Verify pattern parts exist
        assert doc.parts.exists('hole_row_0')
        assert doc.parts.exists('hole_row_1')
        assert doc.parts.exists('hole_row_2')
        assert doc.parts.exists('hole_row_3')

    finally:
        os.unlink(temp_path)


def test_integration_parse_yaml_with_circular_pattern():
    """Test end-to-end: Parse YAML with circular pattern."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Circular Pattern Test

parts:
  marker:
    primitive: sphere
    radius: 2

operations:
  circle:
    type: pattern
    pattern: circular
    input: marker
    count: 6
    axis: Z
    center: [0, 0, 0]
    radius: 30
"""

    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        doc = parse(temp_path)

        # Verify pattern parts exist
        for i in range(6):
            assert doc.parts.exists(f'circle_{i}')

    finally:
        os.unlink(temp_path)


def test_integration_parse_yaml_with_grid_pattern():
    """Test end-to-end: Parse YAML with grid pattern."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Grid Pattern Test

parts:
  hole:
    primitive: cylinder
    radius: 2
    height: 5
    origin: center

operations:
  grid:
    type: pattern
    pattern: grid
    input: hole
    count: [3, 4]
    spacing: [15, 12, 0]
"""

    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        doc = parse(temp_path)

        # Verify grid parts exist (3x4 = 12 parts)
        for row in range(3):
            for col in range(4):
                assert doc.parts.exists(f'grid_{row}_{col}')

    finally:
        os.unlink(temp_path)


def test_integration_pattern_then_boolean(registry, resolver):
    """Test chaining: pattern then boolean (create holes then subtract)."""
    from tiacad_core.parser.boolean_builder import BooleanBuilder

    # Create pattern
    pattern_builder = PatternBuilder(registry, resolver)
    pattern_spec = {
        'pattern': 'linear',
        'input': 'hole',
        'count': 3,
        'spacing': [20, 0, 0]
    }
    pattern_builder.execute_pattern_operation('holes', pattern_spec)

    # Now subtract all holes from box
    boolean_builder = BooleanBuilder(registry, resolver)
    boolean_spec = {
        'operation': 'difference',
        'base': 'box',
        'subtract': ['holes_0', 'holes_1', 'holes_2']
    }
    boolean_builder.execute_boolean_operation('box_with_holes', boolean_spec)

    # Verify result exists
    assert registry.exists('box_with_holes')

    # Volume should be less than original box
    result = registry.get('box_with_holes')
    volume = result.geometry.val().Volume()
    assert volume < 1000  # Original box is 10x10x10 = 1000


def test_integration_boolean_then_pattern(registry, resolver):
    """Test chaining: boolean then pattern (union then array)."""
    from tiacad_core.parser.boolean_builder import BooleanBuilder

    # First: create a combined part
    boolean_builder = BooleanBuilder(registry, resolver)
    boolean_spec = {
        'operation': 'union',
        'inputs': ['box', 'hole']
    }
    boolean_builder.execute_boolean_operation('combined', boolean_spec)

    # Now: pattern the combined part
    pattern_builder = PatternBuilder(registry, resolver)
    pattern_spec = {
        'pattern': 'linear',
        'input': 'combined',
        'count': 3,
        'spacing': [30, 0, 0]
    }
    parts = pattern_builder.execute_pattern_operation('array', pattern_spec)

    # Verify pattern was created
    assert len(parts) == 3
    assert registry.exists('array_0')
    assert registry.exists('array_1')
    assert registry.exists('array_2')


def test_integration_multiple_patterns():
    """Test complex: multiple patterns in one file."""
    from tiacad_core.parser import parse

    yaml_content = """
metadata:
  name: Multiple Patterns Test

parts:
  hole:
    primitive: cylinder
    radius: 2
    height: 5
    origin: center

  marker:
    primitive: sphere
    radius: 1

operations:
  # Linear pattern
  row:
    type: pattern
    pattern: linear
    input: hole
    count: 3
    spacing: [15, 0, 0]

  # Circular pattern
  circle:
    type: pattern
    pattern: circular
    input: marker
    count: 4
    axis: Z
    center: [0, 0, 0]

  # Grid pattern
  grid:
    type: pattern
    pattern: grid
    input: hole
    count: [2, 2]
    spacing: [10, 10, 0]
"""

    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        doc = parse(temp_path)

        # Verify all patterns created
        assert doc.parts.exists('row_0')
        assert doc.parts.exists('circle_0')
        assert doc.parts.exists('grid_0_0')

    finally:
        os.unlink(temp_path)


# ============================================================================
# Additional Edge Cases
# ============================================================================

def test_unknown_pattern_type(builder):
    """Test error on unknown pattern type."""
    spec = {
        'pattern': 'invalid_pattern',
        'input': 'hole',
        'count': 3
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('bad_pattern', spec)

    assert "Unknown pattern type" in str(exc_info.value)
    assert "invalid_pattern" in str(exc_info.value)


def test_missing_pattern_field(builder):
    """Test error when pattern field is missing."""
    spec = {
        'input': 'hole',
        'count': 3
        # Missing 'pattern'
    }

    with pytest.raises(PatternBuilderError) as exc_info:
        builder.execute_pattern_operation('no_pattern', spec)

    assert "missing 'pattern' field" in str(exc_info.value)
