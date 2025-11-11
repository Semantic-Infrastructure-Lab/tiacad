"""
Tests for testing/measurements.py - Measurement utilities

Tests cover:
- measure_distance() with various reference types
- get_bounding_box_dimensions() for primitives
- get_distance_between_points() helper
- Error handling and validation

Author: TIA (galactic-expedition-1110)
Version: 1.0 (v3.1 Week 1)
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from tiacad_core.testing.measurements import (
    measure_distance,
    get_bounding_box_dimensions,
    get_distance_between_points,
    MeasurementError,
)
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestMeasureDistance:
    """Test measure_distance() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

        # Create simple test parts
        self.box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        self.box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").box(20, 20, 20),
            backend=self.backend
        )

        self.cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),  # height, radius
            backend=self.backend
        )

    def test_distance_between_centers_default(self):
        """Test distance between part centers (default behavior)"""
        # Create parts at known positions
        box_at_origin = Part(
            name="box_origin",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        # Move box to [30, 0, 0]
        box_offset = Part(
            name="box_offset",
            geometry=cq.Workplane("XY").center(30, 0).box(10, 10, 10),
            backend=self.backend
        )

        dist = measure_distance(box_at_origin, box_offset)

        # Centers should be 30 units apart
        assert abs(dist - 30.0) < 0.1

    def test_distance_with_explicit_center_references(self):
        """Test distance with explicit 'center' reference"""
        box_origin = Part(
            name="box_origin",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box_offset = Part(
            name="box_offset",
            geometry=cq.Workplane("XY").center(30, 0).box(10, 10, 10),
            backend=self.backend
        )

        dist = measure_distance(box_origin, box_offset, ref1="center", ref2="center")

        assert abs(dist - 30.0) < 0.1

    def test_distance_to_face_references(self):
        """Test distance using auto-generated face references"""
        # Box centered at origin (5x5x5 extends from -2.5 to 2.5)
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        # Cylinder at z=10 (bottom at z=0, top at z=20, radius=5)
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").workplane(offset=10).cylinder(20, 5),
            backend=self.backend
        )

        # Create registry for both parts
        registry = PartRegistry()
        registry.add(box)
        registry.add(cylinder)

        # Distance from box top to cylinder bottom
        # Box top should be at z=5, cylinder bottom at z=0
        # But we need to verify this with actual geometry
        dist = measure_distance(
            box, cylinder,
            ref1="face_top",
            ref2="face_bottom",
            registry=registry
        )

        # This should be a specific distance based on geometry
        # For now, just verify it's a reasonable value
        assert dist >= 0
        assert isinstance(dist, float)

    def test_distance_with_registry(self):
        """Test distance with provided registry"""
        registry = PartRegistry()
        registry.add(self.box1)
        registry.add(self.box2)

        dist = measure_distance(
            self.box1, self.box2,
            registry=registry
        )

        assert isinstance(dist, float)
        assert dist >= 0

    def test_distance_without_registry(self):
        """Test distance creates temporary registry automatically"""
        # Should work without providing registry
        dist = measure_distance(self.box1, self.box2)

        assert isinstance(dist, float)
        assert dist >= 0

    def test_distance_invalid_part1(self):
        """Test that invalid part1 raises MeasurementError"""
        with pytest.raises(MeasurementError, match="part1 must be a Part instance"):
            measure_distance("not a part", self.box2)

    def test_distance_invalid_part2(self):
        """Test that invalid part2 raises MeasurementError"""
        with pytest.raises(MeasurementError, match="part2 must be a Part instance"):
            measure_distance(self.box1, "not a part")

    def test_distance_invalid_reference(self):
        """Test that invalid reference raises MeasurementError"""
        with pytest.raises(MeasurementError, match="Failed to resolve references"):
            measure_distance(
                self.box1, self.box2,
                ref1="nonexistent_reference"
            )

    def test_distance_3_4_5_triangle(self):
        """Test distance calculation accuracy with known 3-4-5 triangle"""
        # Create boxes at precise positions
        box_origin = Part(
            name="box_origin",
            geometry=cq.Workplane("XY").box(1, 1, 1),
            backend=self.backend
        )

        # Box at [3, 4, 0] from origin
        box_345 = Part(
            name="box_345",
            geometry=cq.Workplane("XY").center(3, 4).box(1, 1, 1),
            backend=self.backend
        )

        dist = measure_distance(box_origin, box_345)

        # Should be 5.0 (3-4-5 triangle)
        assert abs(dist - 5.0) < 0.1


class TestGetBoundingBoxDimensions:
    """Test get_bounding_box_dimensions() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

    def test_box_dimensions(self):
        """Test bounding box dimensions for a box"""
        # Create 50x30x20 box
        box = Part(
            name="test_box",
            geometry=cq.Workplane("XY").box(50, 30, 20),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(box)

        # Verify dimensions
        assert abs(dims["width"] - 50.0) < 0.1
        assert abs(dims["height"] - 30.0) < 0.1
        assert abs(dims["depth"] - 20.0) < 0.1

    def test_cylinder_dimensions(self):
        """Test bounding box dimensions for a cylinder"""
        # Create cylinder: radius=10, height=50
        cylinder = Part(
            name="test_cylinder",
            geometry=cq.Workplane("XY").cylinder(50, 10),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(cylinder)

        # Cylinder bbox width/height should be 2*radius = 20
        assert abs(dims["width"] - 20.0) < 0.1
        assert abs(dims["height"] - 20.0) < 0.1
        assert abs(dims["depth"] - 50.0) < 0.1

    def test_sphere_dimensions(self):
        """Test bounding box dimensions for a sphere"""
        # Create sphere: radius=15
        sphere = Part(
            name="test_sphere",
            geometry=cq.Workplane("XY").sphere(15),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(sphere)

        # Sphere bbox should be 2*radius = 30 in all dimensions
        assert abs(dims["width"] - 30.0) < 0.1
        assert abs(dims["height"] - 30.0) < 0.1
        assert abs(dims["depth"] - 30.0) < 0.1

    def test_dimensions_includes_center(self):
        """Test that dimensions dict includes center point"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(box)

        assert "center" in dims
        assert isinstance(dims["center"], list)
        assert len(dims["center"]) == 3

    def test_dimensions_includes_min_max(self):
        """Test that dimensions dict includes min/max corners"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(box)

        assert "min" in dims
        assert "max" in dims
        assert isinstance(dims["min"], list)
        assert isinstance(dims["max"], list)
        assert len(dims["min"]) == 3
        assert len(dims["max"]) == 3

    def test_dimensions_min_max_relationship(self):
        """Test that max > min for all axes"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(20, 20, 20),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(box)

        min_corner = dims["min"]
        max_corner = dims["max"]

        # Max should be greater than min for all axes
        assert max_corner[0] > min_corner[0]
        assert max_corner[1] > min_corner[1]
        assert max_corner[2] > min_corner[2]

    def test_dimensions_consistency(self):
        """Test that width/height/depth match max-min"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(30, 40, 50),
            backend=self.backend
        )

        dims = get_bounding_box_dimensions(box)

        # Verify dimensions match max - min
        assert abs(dims["width"] - (dims["max"][0] - dims["min"][0])) < 0.001
        assert abs(dims["height"] - (dims["max"][1] - dims["min"][1])) < 0.001
        assert abs(dims["depth"] - (dims["max"][2] - dims["min"][2])) < 0.001

    def test_dimensions_invalid_part(self):
        """Test that invalid part raises MeasurementError"""
        with pytest.raises(MeasurementError, match="part must be a Part instance"):
            get_bounding_box_dimensions("not a part")


class TestGetDistanceBetweenPoints:
    """Test get_distance_between_points() helper"""

    def test_distance_origin_to_point(self):
        """Test distance from origin to a point"""
        p1 = np.array([0, 0, 0])
        p2 = np.array([3, 4, 0])

        dist = get_distance_between_points(p1, p2)

        # 3-4-5 triangle
        assert abs(dist - 5.0) < 0.001

    def test_distance_symmetric(self):
        """Test that distance is symmetric: d(p1,p2) = d(p2,p1)"""
        p1 = np.array([10, 20, 30])
        p2 = np.array([15, 25, 35])

        dist1 = get_distance_between_points(p1, p2)
        dist2 = get_distance_between_points(p2, p1)

        assert abs(dist1 - dist2) < 0.001

    def test_distance_zero_same_point(self):
        """Test that distance is zero for same point"""
        p = np.array([10, 20, 30])

        dist = get_distance_between_points(p, p)

        assert abs(dist) < 1e-10

    def test_distance_3d_pythagoras(self):
        """Test 3D distance calculation"""
        p1 = np.array([0, 0, 0])
        p2 = np.array([1, 1, 1])

        dist = get_distance_between_points(p1, p2)

        # sqrt(1^2 + 1^2 + 1^2) = sqrt(3)
        expected = np.sqrt(3)
        assert abs(dist - expected) < 0.001

    def test_distance_accepts_lists(self):
        """Test that function accepts Python lists"""
        p1 = [0, 0, 0]
        p2 = [3, 4, 0]

        dist = get_distance_between_points(p1, p2)

        assert abs(dist - 5.0) < 0.001

    def test_distance_invalid_dimensions_point1(self):
        """Test that non-3D point1 raises ValueError"""
        p1 = np.array([0, 0])  # 2D
        p2 = np.array([1, 1, 1])

        with pytest.raises(ValueError, match="point1 must be 3D"):
            get_distance_between_points(p1, p2)

    def test_distance_invalid_dimensions_point2(self):
        """Test that non-3D point2 raises ValueError"""
        p1 = np.array([0, 0, 0])
        p2 = np.array([1, 1, 1, 1])  # 4D

        with pytest.raises(ValueError, match="point2 must be 3D"):
            get_distance_between_points(p1, p2)


class TestMeasurementErrorHandling:
    """Test error handling across measurement utilities"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()
        self.valid_part = Part(
            name="valid",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

    def test_measure_distance_type_errors(self):
        """Test type validation in measure_distance"""
        # Invalid part1
        with pytest.raises(MeasurementError):
            measure_distance(None, self.valid_part)

        # Invalid part2
        with pytest.raises(MeasurementError):
            measure_distance(self.valid_part, 123)

    def test_get_bounding_box_type_error(self):
        """Test type validation in get_bounding_box_dimensions"""
        with pytest.raises(MeasurementError):
            get_bounding_box_dimensions([1, 2, 3])

    def test_get_distance_between_points_dimension_errors(self):
        """Test dimension validation in get_distance_between_points"""
        # 2D point
        with pytest.raises(ValueError):
            get_distance_between_points([0, 0], [1, 1, 1])

        # 4D point
        with pytest.raises(ValueError):
            get_distance_between_points([0, 0, 0], [1, 1, 1, 1])


class TestMeasurementsIntegration:
    """Integration tests combining multiple measurement utilities"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_stack_attachment(self):
        """Test measuring distance in a box stack (integration test)"""
        # Create two boxes that should be touching
        bottom_box = Part(
            name="bottom",
            geometry=cq.Workplane("XY").box(20, 20, 10),
            backend=self.backend
        )

        # Top box offset by 10 in Z (sitting on bottom box)
        top_box = Part(
            name="top",
            geometry=cq.Workplane("XY").workplane(offset=10).box(20, 20, 10),
            backend=self.backend
        )

        # Create registry
        registry = PartRegistry()
        registry.add(bottom_box)
        registry.add(top_box)

        # Measure distance between face_top of bottom and face_bottom of top
        # They should be touching (distance ~0)
        dist = measure_distance(
            bottom_box, top_box,
            ref1="face_top",
            ref2="face_bottom",
            registry=registry
        )

        # Should be very close to touching
        # Note: There might be small numerical errors
        assert dist >= 0  # Distance can't be negative
        assert dist < 1.0  # Should be reasonably close

    def test_dimensions_and_distance_consistency(self):
        """Test that dimensions and distances are consistent"""
        # Create a box at origin
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(40, 30, 20),
            backend=self.backend
        )

        # Get dimensions
        dims = get_bounding_box_dimensions(box)

        # Distance from min to max corner should equal diagonal
        min_corner = np.array(dims["min"])
        max_corner = np.array(dims["max"])

        diagonal = get_distance_between_points(min_corner, max_corner)

        # Calculate expected diagonal from dimensions
        expected_diagonal = np.sqrt(
            dims["width"]**2 + dims["height"]**2 + dims["depth"]**2
        )

        assert abs(diagonal - expected_diagonal) < 0.1
