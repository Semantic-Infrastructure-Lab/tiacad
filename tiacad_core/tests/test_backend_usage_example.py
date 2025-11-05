"""
Example tests demonstrating MockBackend usage.

This file shows how to write fast unit tests using MockBackend
instead of slow integration tests with CadQueryBackend.

Key Benefits:
- Unit tests run 10-100x faster
- No heavy CadQuery dependency needed
- Test TiaCAD logic, not CAD kernel
- Same Part API works with both backends
"""

import pytest
import time
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import MockBackend, CadQueryBackend


# ============================================================================
# Unit Tests (Fast - Use MockBackend)
# ============================================================================

@pytest.mark.unit
def test_part_creation_with_mock_backend(mock_backend):
    """
    Unit test: Uses MockBackend for fast execution.

    This tests Part logic without slow CAD operations.
    """
    # Create geometry with mock backend (instant!)
    geometry = mock_backend.create_box(10, 10, 10)

    # Create part with backend injection
    part = Part("test_box", geometry, backend=mock_backend)

    # Test Part logic
    assert part.name == "test_box"
    assert part.current_position == (0.0, 0.0, 0.0)
    assert part.backend is mock_backend


@pytest.mark.unit
def test_part_transform_with_mock_backend(mock_backend):
    """
    Unit test: Test transform logic without slow CAD.
    """
    geometry = mock_backend.create_box(10, 10, 10)
    part = Part("box", geometry, backend=mock_backend)

    # Transform using backend
    translated = mock_backend.translate(geometry, (5, 10, 15))
    part.geometry = translated
    part.update_position((5, 10, 15))

    # Verify logic
    assert part.current_position == (5, 10, 15)
    center = mock_backend.get_center(part.geometry)
    assert center == (5, 10, 15)


@pytest.mark.unit
def test_part_registry_with_mock_backend(mock_backend):
    """
    Unit test: Test registry logic with fast mock geometry.
    """
    registry = PartRegistry()

    # Create multiple parts quickly
    box_geom = mock_backend.create_box(10, 10, 10)
    cylinder_geom = mock_backend.create_cylinder(5, 20)
    sphere_geom = mock_backend.create_sphere(10)

    box = Part("box", box_geom, backend=mock_backend)
    cylinder = Part("cylinder", cylinder_geom, backend=mock_backend)
    sphere = Part("sphere", sphere_geom, backend=mock_backend)

    registry.add(box)
    registry.add(cylinder)
    registry.add(sphere)

    # Test registry logic
    assert len(registry) == 3
    assert registry.exists("box")
    assert registry.get("cylinder").name == "cylinder"


@pytest.mark.unit
def test_boolean_operations_with_mock_backend(mock_backend):
    """
    Unit test: Test boolean logic without CAD kernel.
    """
    box = mock_backend.create_box(20, 20, 20)
    cylinder = mock_backend.create_cylinder(5, 30)

    # Boolean operations are instant with mock
    union = mock_backend.boolean_union(box, cylinder)
    difference = mock_backend.boolean_difference(box, cylinder)

    # Verify operation was recorded
    assert 'union' in union.operation_history
    assert 'difference' in difference.operation_history


# ============================================================================
# Integration Tests (Slow - Use Real CadQuery)
# ============================================================================

@pytest.mark.integration
def test_part_creation_with_cadquery_backend(cadquery_backend):
    """
    Integration test: Uses real CadQuery for end-to-end validation.

    Use this sparingly - only when you need to verify actual CAD operations.
    """
    # Create real geometry (slower)
    geometry = cadquery_backend.create_box(10, 10, 10)

    # Create part
    part = Part("test_box", geometry, backend=cadquery_backend)

    # Verify real CAD geometry
    assert part.name == "test_box"
    assert part.backend is cadquery_backend

    # Real bounding box
    bounds = part.get_bounds()
    assert 'min' in bounds
    assert 'max' in bounds


@pytest.mark.integration
def test_tessellation_with_cadquery_backend(cadquery_backend):
    """
    Integration test: Verify real tessellation works.

    This needs real CadQuery - mock can't produce real mesh.
    """
    geometry = cadquery_backend.create_box(10, 10, 10)
    part = Part("box", geometry, backend=cadquery_backend)

    # Real tessellation
    vertices, triangles = cadquery_backend.tessellate(part.geometry)

    # Verify mesh is valid
    assert len(vertices) >= 8  # At least 8 vertices for a box
    assert len(triangles) >= 12  # At least 12 triangles


# ============================================================================
# Performance Demonstration
# ============================================================================

@pytest.mark.slow
def test_performance_comparison():
    """
    Demonstrate speed difference between Mock and CadQuery backends.

    This test shows why MockBackend is valuable for unit tests.
    """
    mock_backend = MockBackend()
    cq_backend = CadQueryBackend()

    # Time MockBackend
    start = time.time()
    for _ in range(100):
        box = mock_backend.create_box(10, 10, 10)
        cylinder = mock_backend.create_cylinder(5, 20)
        union = mock_backend.boolean_union(box, cylinder)
    mock_time = time.time() - start

    # Time CadQueryBackend
    start = time.time()
    for _ in range(100):
        box = cq_backend.create_box(10, 10, 10)
        cylinder = cq_backend.create_cylinder(5, 20)
        union = cq_backend.boolean_union(box, cylinder)
    cq_time = time.time() - start

    # MockBackend should be significantly faster
    speedup = cq_time / mock_time
    print(f"\nPerformance Results:")
    print(f"  MockBackend: {mock_time:.4f}s (100 iterations)")
    print(f"  CadQueryBackend: {cq_time:.4f}s (100 iterations)")
    print(f"  Speedup: {speedup:.1f}x faster")

    # Assert mock is at least 5x faster (usually 10-100x)
    assert speedup > 5.0, f"MockBackend should be much faster, got {speedup:.1f}x"


# ============================================================================
# Migration Example (Old → New Pattern)
# ============================================================================

# OLD PATTERN: Integration-heavy test (slow)
def test_part_old_pattern():
    """
    Old pattern: Always uses real CadQuery.

    Problems:
    - Slow (creates real geometry)
    - Tests CAD kernel, not TiaCAD logic
    - Hard to run without CadQuery installed
    """
    import cadquery as cq
    geometry = cq.Workplane("XY").box(10, 10, 10)  # Slow!
    part = Part("box", geometry)

    assert part.name == "box"


# NEW PATTERN: Unit test (fast)
@pytest.mark.unit
def test_part_new_pattern(mock_backend):
    """
    New pattern: Uses MockBackend for unit tests.

    Benefits:
    - Fast (no CAD operations)
    - Tests TiaCAD logic
    - Runs anywhere (no CadQuery needed)
    """
    geometry = mock_backend.create_box(10, 10, 10)  # Instant!
    part = Part("box", geometry, backend=mock_backend)

    assert part.name == "box"
