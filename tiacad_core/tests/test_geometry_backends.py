"""
Tests for geometry backend system.

Tests both CadQueryBackend and MockBackend to ensure they implement
the GeometryBackend interface correctly and produce expected results.
"""

import pytest
import math
from typing import Tuple

from tiacad_core.geometry import (
    GeometryBackend,
    CadQueryBackend,
    MockBackend,
    MockGeometry,
    get_default_backend,
    set_default_backend,
    reset_default_backend,
)


# ============================================================================
# Helper Functions
# ============================================================================

def assert_point_close(
    actual: Tuple[float, float, float],
    expected: Tuple[float, float, float],
    tolerance: float = 0.01
):
    """Assert two 3D points are within tolerance"""
    distance = math.sqrt(sum((a - e)**2 for a, e in zip(actual, expected)))
    assert distance < tolerance, \
        f"Points not close: {actual} vs {expected} (distance: {distance})"


# ============================================================================
# Test Backend Interface Compliance
# ============================================================================

@pytest.mark.parametrize("backend_class", [CadQueryBackend, MockBackend])
class TestBackendInterface:
    """Test that both backends implement the full interface"""

    def test_backend_has_all_required_methods(self, backend_class):
        """Backend should have all abstract methods implemented"""
        backend = backend_class()

        # Check all abstract methods are present
        required_methods = [
            'create_box', 'create_cylinder', 'create_sphere',
            'boolean_union', 'boolean_difference', 'boolean_intersection',
            'translate', 'rotate', 'scale',
            'fillet', 'chamfer',
            'get_center', 'get_bounding_box',
            'select_faces', 'select_edges',
        ]

        for method_name in required_methods:
            assert hasattr(backend, method_name), \
                f"{backend_class.__name__} missing method: {method_name}"

    def test_primitive_creation(self, backend_class):
        """All primitives should be creatable"""
        backend = backend_class()

        box = backend.create_box(10, 20, 30)
        assert box is not None

        cylinder = backend.create_cylinder(5, 20)
        assert cylinder is not None

        sphere = backend.create_sphere(10)
        assert sphere is not None


# ============================================================================
# MockBackend Specific Tests
# ============================================================================

class TestMockBackend:
    """Test MockBackend functionality"""

    @pytest.fixture
    def backend(self):
        return MockBackend()

    def test_create_box(self, backend):
        """MockBackend creates MockGeometry for box"""
        box = backend.create_box(10, 20, 30)

        assert isinstance(box, MockGeometry)
        assert box.shape_type == 'box'
        assert box.parameters['width'] == 10
        assert box.parameters['height'] == 20
        assert box.parameters['depth'] == 30

    def test_create_cylinder(self, backend):
        """MockBackend creates MockGeometry for cylinder"""
        cylinder = backend.create_cylinder(5, 20)

        assert isinstance(cylinder, MockGeometry)
        assert cylinder.shape_type == 'cylinder'
        assert cylinder.parameters['radius'] == 5
        assert cylinder.parameters['height'] == 20

    def test_create_sphere(self, backend):
        """MockBackend creates MockGeometry for sphere"""
        sphere = backend.create_sphere(10)

        assert isinstance(sphere, MockGeometry)
        assert sphere.shape_type == 'sphere'
        assert sphere.parameters['radius'] == 10

    def test_boolean_union(self, backend):
        """Union creates composite geometry"""
        box = backend.create_box(10, 10, 10)
        cylinder = backend.create_cylinder(5, 20)

        result = backend.boolean_union(box, cylinder)

        assert isinstance(result, MockGeometry)
        assert result.shape_type == 'union'
        assert 'union' in result.operation_history

    def test_translate(self, backend):
        """Translate updates center position"""
        box = backend.create_box(10, 10, 10)
        original_center = box.center

        moved = backend.translate(box, (5, 10, 15))

        assert moved.center == (5, 10, 15)
        assert 'translate' in moved.operation_history[0]

    def test_rotate(self, backend):
        """Rotate records operation"""
        box = backend.create_box(10, 10, 10)

        rotated = backend.rotate(
            box,
            axis_start=(0, 0, 0),
            axis_end=(0, 0, 1),
            angle=45
        )

        assert isinstance(rotated, MockGeometry)
        assert any('rotate' in op for op in rotated.operation_history)

    def test_get_center(self, backend):
        """get_center returns geometry center"""
        box = backend.create_box(10, 10, 10)

        center = backend.get_center(box)

        assert center == (0.0, 0.0, 0.0)

    def test_get_bounding_box(self, backend):
        """get_bounding_box returns bounds dict"""
        box = backend.create_box(10, 10, 10)

        bbox = backend.get_bounding_box(box)

        assert 'min' in bbox
        assert 'max' in bbox
        assert 'center' in bbox

    def test_operations_count_tracking(self, backend):
        """Backend tracks operation count"""
        initial_count = backend.operations_count

        box = backend.create_box(10, 10, 10)
        cylinder = backend.create_cylinder(5, 20)
        union = backend.boolean_union(box, cylinder)

        assert backend.operations_count == initial_count + 3

    def test_tessellate(self, backend):
        """Tessellation returns vertices and triangles"""
        box = backend.create_box(10, 10, 10)

        vertices, triangles = backend.tessellate(box)

        assert len(vertices) > 0
        assert len(triangles) > 0


# ============================================================================
# CadQueryBackend Specific Tests
# ============================================================================

class TestCadQueryBackend:
    """Test CadQueryBackend functionality"""

    @pytest.fixture
    def backend(self):
        return CadQueryBackend()

    def test_create_box(self, backend):
        """CadQueryBackend creates real Workplane"""
        box = backend.create_box(10, 20, 30)

        # Should be a CadQuery Workplane
        assert hasattr(box, 'val')
        assert hasattr(box, 'faces')

        # Check size approximately
        center = backend.get_center(box)
        assert_point_close(center, (0, 0, 0))

    def test_create_cylinder(self, backend):
        """CadQueryBackend creates cylinder"""
        cylinder = backend.create_cylinder(5, 20)

        assert hasattr(cylinder, 'val')

        center = backend.get_center(cylinder)
        assert_point_close(center, (0, 0, 0))

    def test_create_sphere(self, backend):
        """CadQueryBackend creates sphere"""
        sphere = backend.create_sphere(10)

        assert hasattr(sphere, 'val')

        center = backend.get_center(sphere)
        assert_point_close(center, (0, 0, 0))

    def test_boolean_union(self, backend):
        """Union combines geometries"""
        box = backend.create_box(10, 10, 10)
        cylinder = backend.create_cylinder(5, 20)

        result = backend.boolean_union(box, cylinder)

        assert hasattr(result, 'val')

    def test_translate(self, backend):
        """Translate moves geometry"""
        box = backend.create_box(10, 10, 10)

        moved = backend.translate(box, (5, 10, 15))

        center = backend.get_center(moved)
        assert_point_close(center, (5, 10, 15))

    def test_tessellate(self, backend):
        """Tessellation returns vertices and triangles"""
        box = backend.create_box(10, 10, 10)

        vertices, triangles = backend.tessellate(box, tolerance=0.1)

        assert len(vertices) > 0
        assert len(triangles) > 0

        # Box should have 8 vertices (corners)
        # Tessellation may have more for curved approximations
        assert len(vertices) >= 8


# ============================================================================
# Backend Comparison Tests
# ============================================================================

class TestBackendEquivalence:
    """Test that Mock and CadQuery backends produce equivalent results"""

    def test_box_center_equivalent(self):
        """Both backends should return same center for box"""
        cq_backend = CadQueryBackend()
        mock_backend = MockBackend()

        cq_box = cq_backend.create_box(10, 10, 10)
        mock_box = mock_backend.create_box(10, 10, 10)

        cq_center = cq_backend.get_center(cq_box)
        mock_center = mock_backend.get_center(mock_box)

        assert_point_close(cq_center, mock_center)

    def test_translate_center_equivalent(self):
        """Both backends should translate to same position"""
        cq_backend = CadQueryBackend()
        mock_backend = MockBackend()

        cq_box = cq_backend.create_box(10, 10, 10)
        mock_box = mock_backend.create_box(10, 10, 10)

        cq_moved = cq_backend.translate(cq_box, (5, 10, 15))
        mock_moved = mock_backend.translate(mock_box, (5, 10, 15))

        cq_center = cq_backend.get_center(cq_moved)
        mock_center = mock_backend.get_center(mock_moved)

        assert_point_close(cq_center, mock_center)


# ============================================================================
# Default Backend Management
# ============================================================================

class TestDefaultBackend:
    """Test default backend getter/setter"""

    def test_get_default_backend_returns_cadquery(self):
        """Default backend should be CadQueryBackend"""
        reset_default_backend()
        backend = get_default_backend()
        assert isinstance(backend, CadQueryBackend)

    def test_set_default_backend(self):
        """Can set custom default backend"""
        mock = MockBackend()
        set_default_backend(mock)

        backend = get_default_backend()
        assert backend is mock

        # Cleanup
        reset_default_backend()

    def test_reset_default_backend(self):
        """Reset returns to CadQueryBackend"""
        set_default_backend(MockBackend())
        reset_default_backend()

        backend = get_default_backend()
        assert isinstance(backend, CadQueryBackend)


# ============================================================================
# MockGeometry Tests
# ============================================================================

class TestMockGeometry:
    """Test MockGeometry data structure"""

    def test_create_mock_geometry(self):
        """Can create MockGeometry directly"""
        geom = MockGeometry(
            shape_type='box',
            parameters={'width': 10, 'height': 20, 'depth': 30}
        )

        assert geom.shape_type == 'box'
        assert geom.center == (0, 0, 0)

    def test_with_center(self):
        """with_center creates new instance with updated center"""
        geom = MockGeometry(shape_type='box', parameters={})
        moved = geom.with_center((5, 10, 15))

        # Original unchanged
        assert geom.center == (0, 0, 0)

        # New instance updated
        assert moved.center == (5, 10, 15)

    def test_add_operation(self):
        """add_operation records operation in history"""
        geom = MockGeometry(shape_type='box', parameters={})
        modified = geom.add_operation('test_op')

        assert 'test_op' in modified.operation_history
        assert len(geom.operation_history) == 0  # Original unchanged
