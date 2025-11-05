"""
Tests for FinishingBuilder - Fillet and Chamfer operations

Tests finishing operations (fillet, chamfer) with various edge selectors.

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import pytest
import cadquery as cq
from tiacad_core.parser.finishing_builder import FinishingBuilder, FinishingBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part, PartRegistry


@pytest.fixture
def part_registry():
    """Fixture providing a fresh part registry"""
    return PartRegistry()


@pytest.fixture
def parameter_resolver():
    """Fixture providing a parameter resolver with test parameters"""
    params = {
        'fillet_radius': 2.0,
        'chamfer_length': 1.5,
        'edge_radius': 0.5
    }
    return ParameterResolver(params)


@pytest.fixture
def finishing_builder(part_registry, parameter_resolver):
    """Fixture providing a FinishingBuilder instance"""
    return FinishingBuilder(part_registry, parameter_resolver)


@pytest.fixture
def sample_box(part_registry):
    """Fixture providing a sample box part"""
    geometry = cq.Workplane("XY").box(10, 10, 10)
    part = Part(name="test_box", geometry=geometry, metadata={})
    part_registry.add(part)
    return part


@pytest.fixture
def sample_cylinder(part_registry):
    """Fixture providing a sample cylinder part"""
    geometry = cq.Workplane("XY").cylinder(10, 5)
    part = Part(name="test_cylinder", geometry=geometry, metadata={})
    part_registry.add(part)
    return part


# ============================================================================
# FILLET TESTS (15 tests)
# ============================================================================

def test_fillet_all_edges(finishing_builder, sample_box):
    """Test fillet operation on all edges"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    # Verify part was modified
    part = finishing_builder.registry.get('test_box')
    assert part is not None

    # Verify metadata was updated
    assert 'finishing_ops' in part.metadata
    assert len(part.metadata['finishing_ops']) == 1
    assert part.metadata['finishing_ops'][0]['type'] == 'fillet'
    assert part.metadata['finishing_ops'][0]['radius'] == 1.0


def test_fillet_with_parameter_expression(finishing_builder, sample_box):
    """Test fillet with parameter expression for radius"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': '${fillet_radius}',
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['radius'] == 2.0


def test_fillet_direction_selector_z(finishing_builder, sample_box):
    """Test fillet with direction selector (Z axis)"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'direction': 'Z'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert 'finishing_ops' in part.metadata


def test_fillet_direction_selector_x(finishing_builder, sample_box):
    """Test fillet with direction selector (X axis)"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'direction': 'X'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['direction'] == 'X'


def test_fillet_direction_selector_vector(finishing_builder, sample_box):
    """Test fillet with direction selector using vector"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'direction': [0, 0, 1]}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert 'finishing_ops' in part.metadata


def test_fillet_parallel_to_z(finishing_builder, sample_box):
    """Test fillet with parallel_to selector"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'parallel_to': 'Z'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['parallel_to'] == 'Z'


def test_fillet_perpendicular_to_z(finishing_builder, sample_box):
    """Test fillet with perpendicular_to selector"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'perpendicular_to': 'Z'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['perpendicular_to'] == 'Z'


def test_fillet_string_selector(finishing_builder, sample_box):
    """Test fillet with direct string selector"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'selector': '>Z'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['selector'] == '>Z'


def test_fillet_updates_part_in_place(finishing_builder, sample_box):
    """Test that fillet modifies the part in-place"""
    original_part = finishing_builder.registry.get('test_box')
    original_id = id(original_part)

    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    # Same part object (modified in-place)
    modified_part = finishing_builder.registry.get('test_box')
    assert id(modified_part) == original_id


def test_fillet_multiple_operations_same_part(finishing_builder, sample_box):
    """Test multiple fillet operations on the same part"""
    spec1 = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.5,
        'edges': {'direction': 'Z'}
    }

    spec2 = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 0.3,
        'edges': {'parallel_to': 'X'}
    }

    finishing_builder.execute_finishing_operation('fillet_op1', spec1)
    finishing_builder.execute_finishing_operation('fillet_op2', spec2)

    part = finishing_builder.registry.get('test_box')
    assert len(part.metadata['finishing_ops']) == 2
    assert part.metadata['finishing_ops'][0]['radius'] == 0.5
    assert part.metadata['finishing_ops'][1]['radius'] == 0.3


def test_fillet_missing_input_error(finishing_builder, sample_box):
    """Test error when input field is missing"""
    spec = {
        'finish': 'fillet',
        'radius': 1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "missing 'input' field" in str(exc_info.value)


def test_fillet_missing_radius_error(finishing_builder, sample_box):
    """Test error when radius field is missing"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "missing 'radius' field" in str(exc_info.value)


def test_fillet_nonexistent_part_error(finishing_builder):
    """Test error when input part doesn't exist"""
    spec = {
        'finish': 'fillet',
        'input': 'nonexistent_part',
        'radius': 1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "not found" in str(exc_info.value)


def test_fillet_invalid_edge_selector_error(finishing_builder, sample_box):
    """Test error when edge selector is invalid"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': {'unknown_selector': 'Z'}
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "Invalid edge selector" in str(exc_info.value)


def test_fillet_negative_radius_error(finishing_builder, sample_box):
    """Test error when radius is negative"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': -1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "must be positive" in str(exc_info.value)


# ============================================================================
# CHAMFER TESTS (15 tests)
# ============================================================================

def test_chamfer_all_edges(finishing_builder, sample_box):
    """Test chamfer operation on all edges"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 1.0,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    # Verify part was modified
    part = finishing_builder.registry.get('test_box')
    assert part is not None

    # Verify metadata was updated
    assert 'finishing_ops' in part.metadata
    assert len(part.metadata['finishing_ops']) == 1
    assert part.metadata['finishing_ops'][0]['type'] == 'chamfer'
    assert part.metadata['finishing_ops'][0]['length'] == 1.0


def test_chamfer_uniform_length(finishing_builder, sample_box):
    """Test chamfer with uniform length"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 1.5,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['length'] == 1.5
    assert 'length2' not in part.metadata['finishing_ops'][0]


def test_chamfer_asymmetric_two_lengths(finishing_builder, sample_box):
    """Test chamfer with asymmetric lengths"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 2.0,
        'length2': 1.0,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['length'] == 2.0
    assert part.metadata['finishing_ops'][0]['length2'] == 1.0


def test_chamfer_with_parameter_expression(finishing_builder, sample_box):
    """Test chamfer with parameter expression for length"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': '${chamfer_length}',
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['length'] == 1.5


def test_chamfer_direction_selector(finishing_builder, sample_box):
    """Test chamfer with direction selector"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.5,
        'edges': {'direction': 'Z'}
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['direction'] == 'Z'


def test_chamfer_parallel_to_selector(finishing_builder, sample_box):
    """Test chamfer with parallel_to selector"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.5,
        'edges': {'parallel_to': 'X'}
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['parallel_to'] == 'X'


def test_chamfer_perpendicular_to_selector(finishing_builder, sample_box):
    """Test chamfer with perpendicular_to selector"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.5,
        'edges': {'perpendicular_to': 'Y'}
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_box')
    assert part.metadata['finishing_ops'][0]['edges']['perpendicular_to'] == 'Y'


def test_chamfer_updates_part_in_place(finishing_builder, sample_box):
    """Test that chamfer modifies the part in-place"""
    original_part = finishing_builder.registry.get('test_box')
    original_id = id(original_part)

    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 1.0,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    # Same part object (modified in-place)
    modified_part = finishing_builder.registry.get('test_box')
    assert id(modified_part) == original_id


def test_chamfer_multiple_operations_same_part(finishing_builder, sample_box):
    """Test multiple chamfer operations on the same part"""
    spec1 = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.5,
        'edges': {'direction': 'Z'}
    }

    spec2 = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.3,
        'edges': {'parallel_to': 'X'}
    }

    finishing_builder.execute_finishing_operation('chamfer_op1', spec1)
    finishing_builder.execute_finishing_operation('chamfer_op2', spec2)

    part = finishing_builder.registry.get('test_box')
    assert len(part.metadata['finishing_ops']) == 2
    assert part.metadata['finishing_ops'][0]['length'] == 0.5
    assert part.metadata['finishing_ops'][1]['length'] == 0.3


def test_chamfer_missing_input_error(finishing_builder, sample_box):
    """Test error when input field is missing"""
    spec = {
        'finish': 'chamfer',
        'length': 1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('chamfer_op', spec)

    assert "missing 'input' field" in str(exc_info.value)


def test_chamfer_missing_length_error(finishing_builder, sample_box):
    """Test error when length field is missing"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('chamfer_op', spec)

    assert "missing 'length' field" in str(exc_info.value)


def test_chamfer_nonexistent_part_error(finishing_builder):
    """Test error when input part doesn't exist"""
    spec = {
        'finish': 'chamfer',
        'input': 'nonexistent_part',
        'length': 1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('chamfer_op', spec)

    assert "not found" in str(exc_info.value)


def test_chamfer_negative_length_error(finishing_builder, sample_box):
    """Test error when length is negative"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': -1.0,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('chamfer_op', spec)

    assert "must be positive" in str(exc_info.value)


def test_chamfer_negative_length2_error(finishing_builder, sample_box):
    """Test error when length2 is negative"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 1.0,
        'length2': -0.5,
        'edges': 'all'
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('chamfer_op', spec)

    assert "must be positive" in str(exc_info.value)


# ============================================================================
# MIXED OPERATIONS TESTS (5 tests)
# ============================================================================

def test_fillet_and_chamfer_same_part(finishing_builder, sample_box):
    """Test both fillet and chamfer on the same part"""
    spec1 = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': {'direction': 'Z'}
    }

    spec2 = {
        'finish': 'chamfer',
        'input': 'test_box',
        'length': 0.5,
        'edges': {'parallel_to': 'X'}
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec1)
    finishing_builder.execute_finishing_operation('chamfer_op', spec2)

    part = finishing_builder.registry.get('test_box')
    assert len(part.metadata['finishing_ops']) == 2
    assert part.metadata['finishing_ops'][0]['type'] == 'fillet'
    assert part.metadata['finishing_ops'][1]['type'] == 'chamfer'


def test_unknown_finish_type_error(finishing_builder, sample_box):
    """Test error when finish type is unknown"""
    spec = {
        'finish': 'unknown_finish',
        'input': 'test_box',
        'radius': 1.0
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('unknown_op', spec)

    assert "Unknown finishing operation" in str(exc_info.value)


def test_missing_finish_field_error(finishing_builder, sample_box):
    """Test error when finish field is missing"""
    spec = {
        'input': 'test_box',
        'radius': 1.0
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('bad_op', spec)

    assert "missing 'finish' field" in str(exc_info.value)


def test_invalid_axis_string_error(finishing_builder, sample_box):
    """Test error when axis string is invalid"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': {'direction': 'INVALID'}
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "Invalid axis" in str(exc_info.value)


def test_invalid_axis_vector_error(finishing_builder, sample_box):
    """Test error when axis vector is invalid"""
    spec = {
        'finish': 'fillet',
        'input': 'test_box',
        'radius': 1.0,
        'edges': {'direction': [1, 1, 1]}  # Not a unit vector
    }

    with pytest.raises(FinishingBuilderError) as exc_info:
        finishing_builder.execute_finishing_operation('fillet_op', spec)

    assert "Unsupported axis vector" in str(exc_info.value)


# ============================================================================
# INTEGRATION TESTS (4 tests)
# ============================================================================

def test_fillet_on_cylinder(finishing_builder, sample_cylinder):
    """Test fillet operation on cylinder geometry"""
    spec = {
        'finish': 'fillet',
        'input': 'test_cylinder',
        'radius': 0.5,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('fillet_op', spec)

    part = finishing_builder.registry.get('test_cylinder')
    assert 'finishing_ops' in part.metadata


def test_chamfer_on_cylinder(finishing_builder, sample_cylinder):
    """Test chamfer operation on cylinder geometry"""
    spec = {
        'finish': 'chamfer',
        'input': 'test_cylinder',
        'length': 0.5,
        'edges': 'all'
    }

    finishing_builder.execute_finishing_operation('chamfer_op', spec)

    part = finishing_builder.registry.get('test_cylinder')
    assert 'finishing_ops' in part.metadata


def test_edge_selector_all_axes(finishing_builder, part_registry):
    """Test edge selectors with all three axes on separate boxes"""
    # Create separate boxes for each axis test (can't chain selectors on same part)
    for axis in ['X', 'Y', 'Z']:
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name=f'box_{axis}', geometry=geometry, metadata={})
        part_registry.add(part)

        spec = {
            'finish': 'fillet',
            'input': f'box_{axis}',
            'radius': 0.2,
            'edges': {'direction': axis}
        }

        finishing_builder.execute_finishing_operation(f'fillet_{axis}', spec)

        part = finishing_builder.registry.get(f'box_{axis}')
        assert 'finishing_ops' in part.metadata
        assert part.metadata['finishing_ops'][0]['edges']['direction'] == axis


def test_repr(finishing_builder):
    """Test string representation"""
    repr_str = repr(finishing_builder)
    assert 'FinishingBuilder' in repr_str
    assert 'parts=' in repr_str
