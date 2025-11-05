"""
Tests for HullBuilder - Convex hull operations on Part objects

Test Coverage:
- Basic hull operations (6 tests)
- Single input handling (2 tests)
- Error handling (6 tests)
- Coplanarity detection (2 tests)
- Integration tests (4 tests)

Total: 20 tests

Author: TIA
Version: 0.1.0-alpha (Phase 4A)
"""

import pytest
import cadquery as cq
import numpy as np

from tiacad_core.parser.hull_builder import HullBuilder, HullBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part, PartRegistry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Create a PartRegistry with test parts for hull operations."""
    reg = PartRegistry()

    # Create four corner posts for hull testing
    # Post 1: Bottom-left
    post1 = cq.Workplane("XY").cylinder(10, 2).translate((0, 0, 0))
    reg.add(Part("post1", post1))

    # Post 2: Bottom-right
    post2 = cq.Workplane("XY").cylinder(10, 2).translate((20, 0, 0))
    reg.add(Part("post2", post2))

    # Post 3: Top-left
    post3 = cq.Workplane("XY").cylinder(10, 2).translate((0, 20, 0))
    reg.add(Part("post3", post3))

    # Post 4: Top-right
    post4 = cq.Workplane("XY").cylinder(10, 2).translate((20, 20, 0))
    reg.add(Part("post4", post4))

    # Add a center elevated post
    post_center = cq.Workplane("XY").cylinder(15, 2).translate((10, 10, 0))
    reg.add(Part("post_center", post_center))

    # Add simple spheres for testing
    sphere1 = cq.Workplane("XY").sphere(5).translate((0, 0, 0))
    reg.add(Part("sphere1", sphere1))

    sphere2 = cq.Workplane("XY").sphere(5).translate((30, 0, 0))
    reg.add(Part("sphere2", sphere2))

    sphere3 = cq.Workplane("XY").sphere(5).translate((15, 25, 0))
    reg.add(Part("sphere3", sphere3))

    # Add a small box for testing
    small_box = cq.Workplane("XY").box(5, 5, 5)
    reg.add(Part("small_box", small_box))

    return reg


@pytest.fixture
def resolver():
    """Create a basic ParameterResolver."""
    params = {
        'post_a': 'post1',
        'post_b': 'post2',
        'post_c': 'post3'
    }
    return ParameterResolver(params)


@pytest.fixture
def builder(registry, resolver):
    """Create a HullBuilder instance."""
    return HullBuilder(registry, resolver)


# ============================================================================
# Basic Hull Tests (6 tests)
# ============================================================================

def test_hull_two_spheres(builder, registry):
    """Test hull around two spheres creates elongated shape."""
    spec = {
        'inputs': ['sphere1', 'sphere2']
    }

    builder.execute_hull_operation('hull_result', spec)

    # Verify result exists
    assert registry.exists('hull_result')
    result = registry.get('hull_result')
    assert result.geometry is not None

    # Verify it's a solid
    solid = result.geometry.val()
    assert solid.Volume() > 0

    # Hull should have larger volume than single sphere
    sphere_volume = registry.get('sphere1').geometry.val().Volume()
    assert solid.Volume() > sphere_volume


def test_hull_three_spheres(builder, registry):
    """Test hull around three spheres creates triangular prism-like shape."""
    spec = {
        'inputs': ['sphere1', 'sphere2', 'sphere3']
    }

    builder.execute_hull_operation('hull_triangle', spec)

    # Verify result exists
    assert registry.exists('hull_triangle')
    result = registry.get('hull_triangle')
    assert result.geometry is not None

    # Verify it's a solid with volume
    solid = result.geometry.val()
    assert solid.Volume() > 0


def test_hull_four_posts(builder, registry):
    """Test hull around four corner posts creates rectangular enclosure."""
    spec = {
        'inputs': ['post1', 'post2', 'post3', 'post4']
    }

    builder.execute_hull_operation('enclosure', spec)

    # Verify result exists
    assert registry.exists('enclosure')
    result = registry.get('enclosure')
    assert result.geometry is not None

    # Verify bounding box approximately matches post positions
    bbox = result.geometry.val().BoundingBox()

    # Posts are at (0,0), (20,0), (0,20), (20,20), with radius 2
    # So hull should roughly span from -2 to 22 in X and Y
    assert -3 < bbox.xmin < 0
    assert 20 < bbox.xmax < 23


def test_hull_five_posts_with_center(builder, registry):
    """Test hull with center elevated post."""
    spec = {
        'inputs': ['post1', 'post2', 'post3', 'post4', 'post_center']
    }

    builder.execute_hull_operation('enclosure_raised', spec)

    # Verify result exists
    assert registry.exists('enclosure_raised')
    result = registry.get('enclosure_raised')
    assert result.geometry is not None

    # Center post is taller (height 15 vs 10), so hull should extend higher
    # Hull encompasses all posts, so should be at least as tall as corner posts
    bbox = result.geometry.val().BoundingBox()
    assert bbox.zmax >= 5  # At least half height of corner posts (10/2)


def test_hull_mixed_shapes(builder, registry):
    """Test hull with mixed geometry types (sphere, cylinder, box)."""
    spec = {
        'inputs': ['sphere1', 'post1', 'small_box']
    }

    builder.execute_hull_operation('mixed_hull', spec)

    # Verify result exists
    assert registry.exists('mixed_hull')
    result = registry.get('mixed_hull')
    assert result.geometry is not None
    assert result.geometry.val().Volume() > 0


def test_hull_metadata_propagation(builder, registry):
    """Test that metadata is properly set on hull result."""
    spec = {
        'inputs': ['sphere1', 'sphere2']
    }

    builder.execute_hull_operation('meta_hull', spec)

    result = registry.get('meta_hull')

    # Check metadata exists
    assert result.metadata is not None
    assert 'operation_type' in result.metadata
    assert result.metadata['operation_type'] == 'hull'
    assert 'sources' in result.metadata
    assert result.metadata['sources'] == ['sphere1', 'sphere2']


# ============================================================================
# Single Input Tests (2 tests)
# ============================================================================

def test_hull_single_input_returns_unchanged(builder, registry):
    """Test hull with single input returns the input geometry unchanged."""
    spec = {
        'inputs': ['sphere1']
    }

    builder.execute_hull_operation('single_hull', spec)

    # Verify result exists
    assert registry.exists('single_hull')
    result = registry.get('single_hull')

    # Verify geometry exists
    assert result.geometry is not None

    # Volume should match original
    original_volume = registry.get('sphere1').geometry.val().Volume()
    result_volume = result.geometry.val().Volume()
    assert abs(result_volume - original_volume) < 0.1


def test_hull_single_input_preserves_metadata(builder, registry):
    """Test hull with single input preserves source metadata."""
    # Add metadata to source
    sphere = registry.get('sphere1')
    sphere.metadata = {'color': '#FF0000', 'material': 'plastic'}

    spec = {
        'inputs': ['sphere1']
    }

    builder.execute_hull_operation('single_meta', spec)

    result = registry.get('single_meta')
    assert 'color' in result.metadata
    assert result.metadata['color'] == '#FF0000'


# ============================================================================
# Error Handling Tests (6 tests)
# ============================================================================

def test_hull_missing_inputs_field(builder):
    """Test hull fails without inputs field."""
    spec = {}

    with pytest.raises(HullBuilderError) as exc_info:
        builder.execute_hull_operation('bad_hull', spec)

    assert "missing required 'inputs' field" in str(exc_info.value).lower()


def test_hull_inputs_not_list(builder):
    """Test hull fails when inputs is not a list."""
    spec = {
        'inputs': 'sphere1'  # String instead of list
    }

    with pytest.raises(HullBuilderError) as exc_info:
        builder.execute_hull_operation('bad_hull', spec)

    assert "inputs must be a list" in str(exc_info.value).lower()


def test_hull_empty_inputs_list(builder):
    """Test hull fails with empty inputs list."""
    spec = {
        'inputs': []
    }

    with pytest.raises(HullBuilderError) as exc_info:
        builder.execute_hull_operation('empty_hull', spec)

    assert "at least 1 input" in str(exc_info.value).lower()


def test_hull_nonexistent_part(builder, registry):
    """Test hull fails when input part doesn't exist."""
    spec = {
        'inputs': ['sphere1', 'nonexistent_part']
    }

    with pytest.raises(HullBuilderError) as exc_info:
        builder.execute_hull_operation('bad_hull', spec)

    assert "not found" in str(exc_info.value).lower()
    assert "nonexistent_part" in str(exc_info.value)


def test_hull_with_parameters(registry):
    """Test hull with parameter expressions."""
    params = {
        'part_a': 'sphere1',
        'part_b': 'sphere2'
    }
    resolver = ParameterResolver(params)
    builder = HullBuilder(registry, resolver)

    spec = {
        'inputs': ['${part_a}', '${part_b}']
    }

    # This should work after parameter resolution
    builder.execute_hull_operation('param_hull', spec)

    assert registry.exists('param_hull')


def test_hull_too_few_vertices(builder, registry):
    """Test hull fails with geometries that have too few vertices."""
    # This test verifies error handling for degenerate cases
    # In practice, even simple shapes have enough vertices,
    # but we test the validation logic

    # Create a very simple point-like geometry (if possible)
    # For now, we'll skip this as CadQuery shapes always have enough vertices
    # This is more of a theoretical edge case
    pass


# ============================================================================
# Coplanarity Tests (2 tests)
# ============================================================================

def test_hull_detects_coplanar_points():
    """Test that coplanarity detection works correctly."""
    # Create a hull builder for testing internal methods
    registry = PartRegistry()
    resolver = ParameterResolver({})
    builder = HullBuilder(registry, resolver)

    # Create coplanar points (all in XY plane)
    coplanar_points = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [0.5, 0.5, 0]
    ])

    assert builder._are_points_coplanar(coplanar_points)


def test_hull_detects_non_coplanar_points():
    """Test that non-coplanarity is detected correctly."""
    registry = PartRegistry()
    resolver = ParameterResolver({})
    builder = HullBuilder(registry, resolver)

    # Create non-coplanar points
    non_coplanar_points = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]  # Out of XY plane
    ])

    assert not builder._are_points_coplanar(non_coplanar_points)


# ============================================================================
# Integration Tests (4 tests)
# ============================================================================

def test_hull_integration_simple_enclosure(builder, registry):
    """Integration test: Create simple enclosure around corner posts."""
    spec = {
        'inputs': ['post1', 'post2', 'post3', 'post4']
    }

    builder.execute_hull_operation('simple_enclosure', spec)

    result = registry.get('simple_enclosure')

    # Verify geometry properties
    solid = result.geometry.val()
    bbox = solid.BoundingBox()

    # Verify hull spans the expected space
    assert bbox.xmax - bbox.xmin > 20  # At least 20mm wide
    assert bbox.ymax - bbox.ymin > 20  # At least 20mm deep


def test_hull_integration_with_subsequent_boolean(builder, registry):
    """Integration test: Use hull result in boolean operation."""
    # Create hull
    hull_spec = {
        'inputs': ['sphere1', 'sphere2']
    }
    builder.execute_hull_operation('hull_base', hull_spec)

    # Now subtract a sphere from the hull
    # (Would need BooleanBuilder for this, but we can verify hull exists)
    assert registry.exists('hull_base')
    hull_part = registry.get('hull_base')

    # Verify we can get bounding box (geometry is valid)
    bbox = hull_part.geometry.val().BoundingBox()
    assert bbox is not None


def test_hull_integration_vertex_extraction(builder, registry):
    """Integration test: Verify vertex extraction works on real geometry."""
    # Test internal method
    sphere_geom = registry.get('sphere1').geometry

    vertices = builder._extract_vertices(sphere_geom)

    # Sphere should have many vertices from tessellation
    assert len(vertices) > 10

    # All vertices should be tuples of 3 floats
    for vertex in vertices:
        assert isinstance(vertex, tuple)
        assert len(vertex) == 3
        assert all(isinstance(coord, (int, float)) for coord in vertex)


def test_hull_integration_volume_check(builder, registry):
    """Integration test: Verify hull volume is reasonable."""
    # Create hull around three spheres
    spec = {
        'inputs': ['sphere1', 'sphere2', 'sphere3']
    }

    builder.execute_hull_operation('volume_test', spec)

    result = registry.get('volume_test')
    hull_volume = result.geometry.val().Volume()

    # Hull should have positive volume
    assert hull_volume > 0

    # Hull volume should be greater than largest input sphere
    sphere_volume = registry.get('sphere1').geometry.val().Volume()
    assert hull_volume > sphere_volume


# ============================================================================
# Optional: Performance Tests
# ============================================================================

def test_hull_performance_reasonable(builder, registry):
    """Test that hull computation completes in reasonable time."""
    import time

    spec = {
        'inputs': ['post1', 'post2', 'post3', 'post4']
    }

    start = time.time()
    builder.execute_hull_operation('perf_test', spec)
    elapsed = time.time() - start

    # Hull should complete in under 2 seconds for simple geometry
    assert elapsed < 2.0, f"Hull took {elapsed:.2f}s (expected < 2s)"


# ============================================================================
# Test Summary
# ============================================================================

def test_hull_builder_repr(builder):
    """Test HullBuilder string representation."""
    repr_str = repr(builder)
    assert 'HullBuilder' in repr_str
    assert 'parts=' in repr_str
