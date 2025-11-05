"""
Tests for GussetBuilder - structural gusset creation

Tests Phase 1 MVP (manual points mode) with comprehensive coverage:
- Basic triangular gussets
- Parameter resolution
- Error handling
- Metadata propagation
- Integration scenarios

Phase 2 (auto-connect mode) will be tested when implemented.

Author: TIA (sunny-rainbow-1102)
"""

import pytest
import cadquery as cq
import numpy as np

from tiacad_core.part import Part, PartRegistry
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.parser.gusset_builder import GussetBuilder, GussetBuilderError


@pytest.fixture
def registry():
    """Create a PartRegistry with test parts for gusset operations."""
    reg = PartRegistry()

    # Create some simple parts for testing
    # Box at origin
    box_geom = cq.Workplane("XY").box(20, 20, 20)
    reg.add(Part("box", box_geom, {}, (0, 0, 0)))

    # Vertical wall
    wall_geom = cq.Workplane("XY").box(100, 10, 80).translate((0, 0, 40))
    reg.add(Part("wall", wall_geom, {}, (0, 0, 40)))

    # Horizontal beam
    beam_geom = cq.Workplane("XY").box(75, 10, 10).translate((0, 40, 0))
    reg.add(Part("beam", beam_geom, {}, (0, 40, 0)))

    return reg


@pytest.fixture
def resolver():
    """Create a basic ParameterResolver."""
    params = {
        'gusset_thickness': 8,
        'support_height': 30
    }
    return ParameterResolver(params)


@pytest.fixture
def builder(registry, resolver):
    """Create a GussetBuilder instance."""
    return GussetBuilder(registry, resolver)


# ============================================================================
# Basic Functionality Tests
# ============================================================================

def test_simple_triangular_gusset(builder, registry):
    """Test creating a simple triangular gusset from 3 points."""
    builder.execute_gusset_operation('corner_support', {
        'points': [[0, 0, 0], [50, 0, 0], [25, 40, 0]],
        'thickness': 8
    })

    assert registry.exists('corner_support')
    result = registry.get('corner_support')
    assert result.geometry is not None

    # Verify it's a solid
    solid = result.geometry.val()
    assert solid.isValid()


def test_gusset_with_elevated_points(builder, registry):
    """Test gusset with points not on XY plane."""
    builder.execute_gusset_operation('elevated_gusset', {
        'points': [[0, 0, 10], [50, 0, 10], [25, 40, 30]],
        'thickness': 6
    })

    assert registry.exists('elevated_gusset')
    result = registry.get('elevated_gusset')
    solid = result.geometry.val()
    assert solid.isValid()


def test_gusset_thickness_variations(builder, registry):
    """Test gussets with different thickness values."""
    thicknesses = [2, 5, 10, 20]

    for i, thickness in enumerate(thicknesses):
        name = f'gusset_{thickness}mm'
        builder.execute_gusset_operation(name, {
            'points': [[0, 0, 0], [30, 0, 0], [15, 25, 0]],
            'thickness': thickness
        })

        assert registry.exists(name)
        result = registry.get(name)
        assert result.metadata['thickness'] == thickness


# ============================================================================
# Parameter Resolution Tests
# ============================================================================

def test_gusset_parameter_resolution(registry):
    """Test that parameter expressions are resolved."""
    params = {'thickness': 10, 'point_x': 50, 'point_y': 40}
    resolver = ParameterResolver(params)
    builder = GussetBuilder(registry, resolver)

    builder.execute_gusset_operation('param_gusset', {
        'points': [[0, 0, 0], ['${point_x}', 0, 0], [25, '${point_y}', 0]],
        'thickness': '${thickness}'
    })

    result = registry.get('param_gusset')
    assert result.metadata['thickness'] == 10


# ============================================================================
# Metadata Tests
# ============================================================================

def test_gusset_metadata_structure(builder, registry):
    """Test that gusset creates proper metadata."""
    builder.execute_gusset_operation('meta_test', {
        'points': [[0, 0, 0], [30, 0, 0], [15, 20, 0]],
        'thickness': 8
    })

    result = registry.get('meta_test')
    metadata = result.metadata

    assert metadata['operation_type'] == 'gusset'
    assert metadata['mode'] == 'manual_points'
    assert metadata['thickness'] == 8
    assert 'points' in metadata
    assert len(metadata['points']) == 3


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_gusset_missing_thickness(builder):
    """Test that missing thickness field raises error."""
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('no_thickness', {
            'points': [[0, 0, 0], [30, 0, 0], [15, 20, 0]]
        })

    assert "missing required 'thickness'" in str(exc_info.value).lower()


def test_gusset_invalid_thickness(builder):
    """Test that invalid thickness values raise errors."""
    invalid_thicknesses = [0, -5, 'not_a_number', None]

    for thickness in invalid_thicknesses:
        with pytest.raises(GussetBuilderError):
            builder.execute_gusset_operation(f'bad_thickness_{thickness}', {
                'points': [[0, 0, 0], [30, 0, 0], [15, 20, 0]],
                'thickness': thickness
            })


def test_gusset_missing_mode_specification(builder):
    """Test error when neither points nor connect specified."""
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('no_mode', {
            'thickness': 8
        })

    assert "must specify either 'points' or 'connect'" in str(exc_info.value).lower()


def test_gusset_wrong_number_of_points(builder):
    """Test error when not exactly 3 points provided."""
    # Too few points
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('too_few', {
            'points': [[0, 0, 0], [30, 0, 0]],  # Only 2 points
            'thickness': 8
        })
    assert "requires exactly 3 points" in str(exc_info.value).lower()

    # Too many points
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('too_many', {
            'points': [[0, 0, 0], [30, 0, 0], [15, 20, 0], [10, 10, 10]],  # 4 points
            'thickness': 8
        })
    assert "requires exactly 3 points" in str(exc_info.value).lower()


def test_gusset_invalid_point_format(builder):
    """Test error when points have invalid format."""
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('bad_point', {
            'points': [[0, 0, 0], [30, 0], [15, 20, 0]],  # Middle point missing Z
            'thickness': 8
        })
    assert "must be [x,y,z]" in str(exc_info.value).lower()


def test_gusset_collinear_points(builder):
    """Test error when points are collinear (form line, not triangle)."""
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('collinear', {
            'points': [[0, 0, 0], [25, 0, 0], [50, 0, 0]],  # All on X axis
            'thickness': 8
        })
    assert "collinear" in str(exc_info.value).lower()


def test_gusset_auto_connect_not_implemented(builder):
    """Test that auto-connect mode raises not-implemented error (Phase 2)."""
    with pytest.raises(GussetBuilderError) as exc_info:
        builder.execute_gusset_operation('auto_gusset', {
            'connect': {
                'from': {'part': 'wall', 'face': '>Y'},
                'to': {'part': 'beam', 'face': '<Y'}
            },
            'thickness': 8
        })

    assert "not yet implemented" in str(exc_info.value).lower()
    assert "phase 2" in str(exc_info.value).lower()


# ============================================================================
# Geometry Validation Tests
# ============================================================================

def test_gusset_geometry_is_solid(builder, registry):
    """Test that gusset creates a valid solid."""
    builder.execute_gusset_operation('solid_test', {
        'points': [[0, 0, 0], [40, 0, 0], [20, 30, 0]],
        'thickness': 10
    })

    result = registry.get('solid_test')
    solid = result.geometry.val()

    # Should be valid solid
    assert solid.isValid()

    # Should have volume
    volume = solid.Volume()
    assert volume > 0


def test_gusset_different_orientations(builder, registry):
    """Test gussets in different orientations (XY, XZ, YZ planes)."""
    # XY plane
    builder.execute_gusset_operation('gusset_xy', {
        'points': [[0, 0, 0], [30, 0, 0], [15, 25, 0]],
        'thickness': 8
    })

    # XZ plane
    builder.execute_gusset_operation('gusset_xz', {
        'points': [[0, 0, 0], [30, 0, 0], [15, 0, 25]],
        'thickness': 8
    })

    # YZ plane
    builder.execute_gusset_operation('gusset_yz', {
        'points': [[0, 0, 0], [0, 30, 0], [0, 15, 25]],
        'thickness': 8
    })

    # All should be valid
    for name in ['gusset_xy', 'gusset_xz', 'gusset_yz']:
        result = registry.get(name)
        assert result.geometry.val().isValid()


# ============================================================================
# Integration Tests
# ============================================================================

def test_gusset_integration_with_boolean(builder, registry):
    """Integration test: Use gusset with boolean operations."""
    from tiacad_core.parser.boolean_builder import BooleanBuilder

    # Create a box and a gusset
    builder.execute_gusset_operation('support_gusset', {
        'points': [[10, 10, 0], [30, 10, 0], [20, 10, 20]],
        'thickness': 5
    })

    # Union gusset with box
    bool_builder = BooleanBuilder(registry, ParameterResolver({}))
    bool_builder.execute_boolean_operation('box_with_support', {
        'operation': 'union',
        'inputs': ['box', 'support_gusset']
    })

    result = registry.get('box_with_support')
    assert result.geometry.val().isValid()


def test_gusset_multiple_in_assembly(builder, registry):
    """Integration test: Create multiple gussets for an assembly."""
    # Create 4 corner gussets for a table or structure
    corners = [
        ('gusset_nw', [[0, 0, 0], [20, 0, 0], [10, 0, 30]]),
        ('gusset_ne', [[80, 0, 0], [100, 0, 0], [90, 0, 30]]),
        ('gusset_sw', [[0, 60, 0], [20, 60, 0], [10, 60, 30]]),
        ('gusset_se', [[80, 60, 0], [100, 60, 0], [90, 60, 30]])
    ]

    for name, points in corners:
        builder.execute_gusset_operation(name, {
            'points': points,
            'thickness': 6
        })
        assert registry.exists(name)


# ============================================================================
# Real-World Use Case Tests
# ============================================================================

def test_gusset_guitar_hanger_scenario(builder, registry):
    """Real-world test: Guitar hanger gusset support."""
    # Gusset between beam and arm (simplified coordinates)
    builder.execute_gusset_operation('left_arm_gusset', {
        'points': [
            [-36, 20, 0],      # Base point on beam
            [-36, 40, 0],      # Extension along beam
            [-36, 30, 20]      # Apex point toward arm
        ],
        'thickness': 8
    })

    result = registry.get('left_arm_gusset')
    assert result.geometry.val().isValid()
    assert result.metadata['thickness'] == 8


def test_gusset_l_bracket_scenario(builder, registry):
    """Real-world test: L-bracket corner gusset."""
    # Gusset in corner of L-bracket
    builder.execute_gusset_operation('bracket_gusset', {
        'points': [
            [0, 0, 0],         # Corner origin
            [40, 0, 0],        # Along base
            [0, 0, 40]         # Up vertical
        ],
        'thickness': 6
    })

    result = registry.get('bracket_gusset')
    assert result.geometry.val().isValid()


# ============================================================================
# Performance and Stress Tests
# ============================================================================

def test_gusset_performance_reasonable(builder, registry):
    """Test that gusset creation completes in reasonable time."""
    import time

    start = time.time()
    builder.execute_gusset_operation('perf_test', {
        'points': [[0, 0, 0], [50, 0, 0], [25, 40, 0]],
        'thickness': 8
    })
    elapsed = time.time() - start

    # Should complete in under 1 second
    assert elapsed < 1.0


def test_gusset_various_sizes(builder, registry):
    """Test gussets of various sizes work correctly."""
    sizes = [
        ('tiny', 1, [[0, 0, 0], [5, 0, 0], [2.5, 4, 0]]),
        ('small', 3, [[0, 0, 0], [20, 0, 0], [10, 15, 0]]),
        ('medium', 8, [[0, 0, 0], [50, 0, 0], [25, 40, 0]]),
        ('large', 15, [[0, 0, 0], [100, 0, 0], [50, 80, 0]])
    ]

    for name, thickness, points in sizes:
        builder.execute_gusset_operation(f'size_{name}', {
            'points': points,
            'thickness': thickness
        })

        result = registry.get(f'size_{name}')
        assert result.geometry.val().isValid()


# ============================================================================
# Utility Tests
# ============================================================================

def test_gusset_builder_repr(builder):
    """Test GussetBuilder string representation."""
    repr_str = repr(builder)
    assert 'GussetBuilder' in repr_str
    assert 'parts=' in repr_str
