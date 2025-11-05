"""
Test Auto-Generated Part-Local References (Phase 3 - Week 5)

Tests the automatic generation of part-local references for all primitive types:
- {part}.center - bounding box center
- {part}.origin - part origin
- {part}.face_top, face_bottom, face_left, face_right, face_front, face_back
- {part}.axis_x, axis_y, axis_z

These auto-references make it easy to position and attach parts without manually
calculating positions.

Author: TIA
Phase: v3.0 Week 5
"""

import pytest
import numpy as np
from tiacad_core.part import Part, PartRegistry
from tiacad_core.spatial_resolver import SpatialResolver, SpatialResolverError
from tiacad_core.geometry.mock_backend import MockBackend


@pytest.fixture
def registry():
    """Create a registry with mock parts for testing."""
    reg = PartRegistry()
    backend = MockBackend()

    # Create a box at origin with size 20x20x20
    # MockBackend automatically centers boxes at (0,0,0)
    box_geom = backend.create_box(20, 20, 20)
    box = Part(name='box', geometry=box_geom, current_position=(0, 0, 0), backend=backend)
    reg.add(box)

    # Create a cylinder with radius=10, height=40
    # MockBackend centers cylinders in X/Y, puts base at Z=0
    # So bounds are: x:[-10,10], y:[-10,10], z:[-20,20] (centered)
    cyl_geom = backend.create_cylinder(radius=10, height=40)
    cylinder = Part(name='cylinder', geometry=cyl_geom, current_position=(30, 0, 0), backend=backend)
    reg.add(cylinder)

    # Create a sphere with radius=15
    # MockBackend centers spheres at (0,0,0)
    sphere_geom = backend.create_sphere(radius=15)
    sphere = Part(name='sphere', geometry=sphere_geom, current_position=(0, 30, 0), backend=backend)
    reg.add(sphere)

    # Note: MockBackend doesn't have create_cone() yet,
    # so we only test box, cylinder, and sphere

    return reg


@pytest.fixture
def resolver(registry):
    """Create SpatialResolver with the test registry."""
    return SpatialResolver(registry, {})


# ============================================================================
# Box Auto-References (8 tests)
# ============================================================================

def test_box_center(resolver):
    """Test box.center returns bounding box center."""
    ref = resolver.resolve('box.center')

    assert ref.ref_type == 'point'
    # Box is 20x20x20 centered at origin, so center should be (0,0,0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])


def test_box_origin(resolver):
    """Test box.origin returns part origin."""
    ref = resolver.resolve('box.origin')

    assert ref.ref_type == 'point'
    # Origin is always (0,0,0) for now
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])


def test_box_face_top(resolver):
    """Test box.face_top returns top face reference."""
    ref = resolver.resolve('box.face_top')

    assert ref.ref_type == 'face'
    # Top face should be at z=10 (center + half height)
    assert ref.position[2] == pytest.approx(10.0)
    # Normal should point up (+Z)
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, 1.0])


def test_box_face_bottom(resolver):
    """Test box.face_bottom returns bottom face reference."""
    ref = resolver.resolve('box.face_bottom')

    assert ref.ref_type == 'face'
    # Bottom face should be at z=-10
    assert ref.position[2] == pytest.approx(-10.0)
    # Normal should point down (-Z)
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, -1.0])


def test_box_face_left(resolver):
    """Test box.face_left returns left face reference."""
    ref = resolver.resolve('box.face_left')

    assert ref.ref_type == 'face'
    # Left face should be at x=-10
    assert ref.position[0] == pytest.approx(-10.0)
    # Normal should point left (-X)
    np.testing.assert_array_almost_equal(ref.orientation, [-1.0, 0.0, 0.0])


def test_box_face_right(resolver):
    """Test box.face_right returns right face reference."""
    ref = resolver.resolve('box.face_right')

    assert ref.ref_type == 'face'
    # Right face should be at x=10
    assert ref.position[0] == pytest.approx(10.0)
    # Normal should point right (+X)
    np.testing.assert_array_almost_equal(ref.orientation, [1.0, 0.0, 0.0])


def test_box_face_front(resolver):
    """Test box.face_front returns front face reference."""
    ref = resolver.resolve('box.face_front')

    assert ref.ref_type == 'face'
    # Front face should be at y=10
    assert ref.position[1] == pytest.approx(10.0)
    # Normal should point forward (+Y)
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 1.0, 0.0])


def test_box_face_back(resolver):
    """Test box.face_back returns back face reference."""
    ref = resolver.resolve('box.face_back')

    assert ref.ref_type == 'face'
    # Back face should be at y=-10
    assert ref.position[1] == pytest.approx(-10.0)
    # Normal should point back (-Y)
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, -1.0, 0.0])


# ============================================================================
# Cylinder Auto-References (6 tests)
# ============================================================================

def test_cylinder_center(resolver):
    """Test cylinder.center returns bounding box center."""
    ref = resolver.resolve('cylinder.center')

    assert ref.ref_type == 'point'
    # Cylinder: radius=10, height=40, centered in MockBackend
    # Bounding box: x: -10 to 10, y: -10 to 10, z: -20 to 20
    # Center: (0, 0, 0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])


def test_cylinder_face_top(resolver):
    """Test cylinder.face_top returns top circular face."""
    ref = resolver.resolve('cylinder.face_top')

    assert ref.ref_type == 'face'
    # Top face at z=20 (centered cylinder)
    assert ref.position[2] == pytest.approx(20.0)
    # Normal points up
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, 1.0])


def test_cylinder_face_bottom(resolver):
    """Test cylinder.face_bottom returns bottom circular face."""
    ref = resolver.resolve('cylinder.face_bottom')

    assert ref.ref_type == 'face'
    # Bottom face at z=-20 (centered cylinder)
    assert ref.position[2] == pytest.approx(-20.0)
    # Normal points down
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, -1.0])


def test_cylinder_axis_z(resolver):
    """Test cylinder.axis_z returns central axis."""
    ref = resolver.resolve('cylinder.axis_z')

    assert ref.ref_type == 'axis'
    # Axis goes through center at (0,0,0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])
    # Direction is +Z
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, 1.0])


def test_cylinder_axis_x(resolver):
    """Test cylinder.axis_x returns X axis through center."""
    ref = resolver.resolve('cylinder.axis_x')

    assert ref.ref_type == 'axis'
    # Axis goes through center at (0,0,0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])
    # Direction is +X
    np.testing.assert_array_almost_equal(ref.orientation, [1.0, 0.0, 0.0])


def test_cylinder_axis_y(resolver):
    """Test cylinder.axis_y returns Y axis through center."""
    ref = resolver.resolve('cylinder.axis_y')

    assert ref.ref_type == 'axis'
    # Axis goes through center at (0,0,0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])
    # Direction is +Y
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 1.0, 0.0])


# ============================================================================
# Sphere Auto-References (4 tests)
# ============================================================================

def test_sphere_center(resolver):
    """Test sphere.center returns sphere center."""
    ref = resolver.resolve('sphere.center')

    assert ref.ref_type == 'point'
    # Sphere: radius=15, centered
    # Bounding box: -15 to 15 on all axes
    # Center: (0, 0, 0)
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])


def test_sphere_face_top(resolver):
    """Test sphere.face_top returns top point."""
    ref = resolver.resolve('sphere.face_top')

    assert ref.ref_type == 'face'
    # Top of sphere at z=15
    assert ref.position[2] == pytest.approx(15.0)
    # Normal points up
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, 1.0])


def test_sphere_face_bottom(resolver):
    """Test sphere.face_bottom returns bottom point."""
    ref = resolver.resolve('sphere.face_bottom')

    assert ref.ref_type == 'face'
    # Bottom of sphere at z=-15
    assert ref.position[2] == pytest.approx(-15.0)
    # Normal points down
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, -1.0])


def test_sphere_axis_z(resolver):
    """Test sphere.axis_z returns Z axis through center."""
    ref = resolver.resolve('sphere.axis_z')

    assert ref.ref_type == 'axis'
    # Axis goes through center
    np.testing.assert_array_almost_equal(ref.position, [0.0, 0.0, 0.0])
    # Direction is +Z
    np.testing.assert_array_almost_equal(ref.orientation, [0.0, 0.0, 1.0])


# ============================================================================
# Cone Auto-References (6 tests) - SKIPPED: MockBackend doesn't have create_cone yet
# ============================================================================

# TODO: Add cone tests when MockBackend supports create_cone()


# ============================================================================
# Usage in Transforms (6 tests)
# ============================================================================

def test_auto_reference_in_translate(resolver):
    """Test using auto-reference for translation."""
    # This would be used like: translate: {to: "box.face_top"}
    ref = resolver.resolve('box.face_top')

    # Should get a valid position we can translate to
    assert ref.ref_type == 'face'
    assert len(ref.position) == 3
    assert all(isinstance(x, (int, float, np.number)) for x in ref.position)


def test_auto_reference_with_offset(resolver):
    """Test using auto-reference with offset."""
    # This would be used like:
    # translate:
    #   to: {from: "cylinder.face_top", offset: [0, 0, 5]}

    spec = {
        'type': 'point',
        'from': 'cylinder.face_top',
        'offset': [0, 0, 5]
    }
    ref = resolver.resolve(spec)

    # Should be 5 units above cylinder top (20 + 5 = 25 for centered cylinder)
    assert ref.position[2] == pytest.approx(25.0)


def test_auto_reference_dot_notation_caching(resolver):
    """Test that auto-references are cached properly."""
    # First resolution
    ref1 = resolver.resolve('box.center')

    # Second resolution (should hit cache)
    ref2 = resolver.resolve('box.center')

    # Should be the same object from cache
    assert ref1 is ref2
    np.testing.assert_array_equal(ref1.position, ref2.position)


def test_auto_reference_invalid_part(resolver):
    """Test error when referencing non-existent part."""
    with pytest.raises(SpatialResolverError) as exc_info:
        resolver.resolve('nonexistent.center')

    assert 'not found' in str(exc_info.value).lower()
    assert 'nonexistent' in str(exc_info.value)


def test_auto_reference_invalid_reference_name(resolver):
    """Test error when using invalid reference name."""
    with pytest.raises(SpatialResolverError) as exc_info:
        resolver.resolve('box.invalid_ref')

    assert 'unknown' in str(exc_info.value).lower()
    assert 'invalid_ref' in str(exc_info.value)


def test_auto_reference_all_axes(resolver):
    """Test that all three axes work correctly."""
    # Get all three axes
    axis_x = resolver.resolve('box.axis_x')
    axis_y = resolver.resolve('box.axis_y')
    axis_z = resolver.resolve('box.axis_z')

    # All should be axes
    assert axis_x.ref_type == 'axis'
    assert axis_y.ref_type == 'axis'
    assert axis_z.ref_type == 'axis'

    # All should go through the same center point
    np.testing.assert_array_almost_equal(axis_x.position, axis_y.position)
    np.testing.assert_array_almost_equal(axis_y.position, axis_z.position)

    # Directions should be orthogonal unit vectors
    np.testing.assert_array_almost_equal(axis_x.orientation, [1, 0, 0])
    np.testing.assert_array_almost_equal(axis_y.orientation, [0, 1, 0])
    np.testing.assert_array_almost_equal(axis_z.orientation, [0, 0, 1])


# ============================================================================
# Summary Test
# ============================================================================

def test_auto_references_summary(resolver):
    """Summary test: verify all primitive types have working auto-references."""
    # Only test primitives supported by MockBackend
    primitives = ['box', 'cylinder', 'sphere']

    for prim in primitives:
        # Every primitive should have center
        center = resolver.resolve(f'{prim}.center')
        assert center.ref_type == 'point'

        # Every primitive should have origin
        origin = resolver.resolve(f'{prim}.origin')
        assert origin.ref_type == 'point'

        # Every primitive should have face_top
        face_top = resolver.resolve(f'{prim}.face_top')
        assert face_top.ref_type == 'face'
        assert face_top.orientation[2] > 0  # Normal points up

        # Every primitive should have axis_z
        axis_z = resolver.resolve(f'{prim}.axis_z')
        assert axis_z.ref_type == 'axis'
        np.testing.assert_array_almost_equal(axis_z.orientation, [0, 0, 1])
