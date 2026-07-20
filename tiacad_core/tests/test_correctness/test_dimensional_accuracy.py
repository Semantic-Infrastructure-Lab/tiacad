"""
Dimensional Accuracy Tests

Tests that verify correct dimensional accuracy, including:
- Primitive dimensions (box, cylinder, sphere, cone)
- Volume calculations for all primitives
- Surface area calculations
- Boolean operation volumes (union, difference, intersection)

Part of the Testing Confidence Plan v3.1 Week 6.

Author: TIA (v3.1 Week 6)
Version: 1.0 (v3.1)
"""

import pytest
import math

from tiacad_core.testing.dimensions import (
    get_dimensions,
    get_volume,
    get_surface_area,
)
from tiacad_core.part import Part
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestPrimitiveDimensions:
    """Test dimensional accuracy for all primitive types"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_dimensions_accuracy(self):
        """Test box has accurate dimensions"""
        # Create 50x30x20 box
        box = Part(
            name="test_box",
            geometry=cq.Workplane("XY").box(50, 30, 20),
            backend=self.backend
        )

        dims = get_dimensions(box)

        # Verify dimensions to 0.01 unit accuracy
        assert abs(dims['width'] - 50.0) < 0.01
        assert abs(dims['depth'] - 30.0) < 0.01
        assert abs(dims['height'] - 20.0) < 0.01

    def test_cylinder_radius_accuracy(self):
        """Test cylinder has accurate radius"""
        # Create cylinder: radius=10, height=50
        cylinder = Part(
            name="test_cylinder",
            geometry=cq.Workplane("XY").cylinder(50, 10),
            backend=self.backend
        )

        dims = get_dimensions(cylinder)

        # Cylinder bounding box width/depth should be 2*radius = 20
        assert abs(dims['width'] - 20.0) < 0.1
        assert abs(dims['depth'] - 20.0) < 0.1
        assert abs(dims['height'] - 50.0) < 0.1

    def test_cylinder_height_accuracy(self):
        """Test cylinder has accurate height"""
        # Create tall cylinder: radius=5, height=100
        cylinder = Part(
            name="tall_cylinder",
            geometry=cq.Workplane("XY").cylinder(100, 5),
            backend=self.backend
        )

        dims = get_dimensions(cylinder)

        # Height should be accurate
        assert abs(dims['height'] - 100.0) < 0.1

    def test_sphere_radius_accuracy(self):
        """Test sphere has accurate radius"""
        # Create sphere: radius=15
        sphere = Part(
            name="test_sphere",
            geometry=cq.Workplane("XY").sphere(15),
            backend=self.backend
        )

        dims = get_dimensions(sphere)

        # Sphere bounding box should be 2*radius = 30 in all dimensions
        assert abs(dims['width'] - 30.0) < 0.1
        assert abs(dims['height'] - 30.0) < 0.1
        assert abs(dims['depth'] - 30.0) < 0.1

    def test_cone_dimensions_accuracy(self):
        """Test cone has accurate dimensions"""
        # Create cone: bottom radius=10, top radius=0, height=20
        cone = Part(
            name="test_cone",
            geometry=cq.Workplane("XY").union(
                cq.Solid.makeCone(10, 0, 20)
            ),
            backend=self.backend
        )

        dims = get_dimensions(cone)

        # Cone base should be 2*radius = 20
        assert abs(dims['width'] - 20.0) < 0.1
        assert abs(dims['height'] - 20.0) < 0.1
        # Height should be 20
        assert abs(dims['depth'] - 20.0) < 0.1

    def test_small_box_precision(self):
        """Test dimensional accuracy for very small box"""
        # Create 1x1x1 mm box
        small_box = Part(
            name="small_box",
            geometry=cq.Workplane("XY").box(1, 1, 1),
            backend=self.backend
        )

        dims = get_dimensions(small_box)

        # Even small dimensions should be accurate
        assert abs(dims['width'] - 1.0) < 0.01
        assert abs(dims['height'] - 1.0) < 0.01
        assert abs(dims['depth'] - 1.0) < 0.01

    def test_large_box_precision(self):
        """Test dimensional accuracy for very large box"""
        # Create 1000x1000x1000 unit box
        large_box = Part(
            name="large_box",
            geometry=cq.Workplane("XY").box(1000, 1000, 1000),
            backend=self.backend
        )

        dims = get_dimensions(large_box)

        # Large dimensions should also be accurate
        assert abs(dims['width'] - 1000.0) < 0.1
        assert abs(dims['height'] - 1000.0) < 0.1
        assert abs(dims['depth'] - 1000.0) < 0.1

    def test_non_uniform_box_dimensions(self):
        """Test box with very different dimensions"""
        # Create thin plate: 100x100x2
        plate = Part(
            name="plate",
            geometry=cq.Workplane("XY").box(100, 100, 2),
            backend=self.backend
        )

        dims = get_dimensions(plate)

        assert abs(dims['width'] - 100.0) < 0.1
        assert abs(dims['depth'] - 100.0) < 0.1
        assert abs(dims['height'] - 2.0) < 0.01


class TestVolumeCalculations:
    """Test volume calculation accuracy"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_volume_accuracy(self):
        """Test box volume calculation"""
        # Create 10x20x30 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 20, 30),
            backend=self.backend
        )

        volume = get_volume(box)
        expected = 10 * 20 * 30  # 6000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_cylinder_volume_accuracy(self):
        """Test cylinder volume calculation"""
        # Create cylinder: radius=10, height=25
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(25, 10),
            backend=self.backend
        )

        volume = get_volume(cylinder)
        expected = math.pi * 10**2 * 25  # π*r²*h ≈ 7853.98

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_sphere_volume_accuracy(self):
        """Test sphere volume calculation"""
        # Create sphere: radius=15
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").sphere(15),
            backend=self.backend
        )

        volume = get_volume(sphere)
        expected = (4/3) * math.pi * 15**3  # (4/3)*π*r³ ≈ 14137.17

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_cone_volume_accuracy(self):
        """Test cone volume calculation"""
        # Create cone: bottom radius=8, top radius=0, height=15
        cone = Part(
            name="cone",
            geometry=cq.Workplane("XY").union(
                cq.Solid.makeCone(8, 0, 15)
            ),
            backend=self.backend
        )

        volume = get_volume(cone)
        expected = (1/3) * math.pi * 8**2 * 15  # (1/3)*π*r²*h ≈ 1005.31

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_cube_volume(self):
        """Test volume of a perfect cube"""
        # Create 20x20x20 cube
        cube = Part(
            name="cube",
            geometry=cq.Workplane("XY").box(20, 20, 20),
            backend=self.backend
        )

        volume = get_volume(cube)
        expected = 20**3  # 8000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01


class TestBooleanOperationVolumes:
    """Test volume calculations for boolean operations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_union_volume_non_overlapping(self):
        """Test union of non-overlapping boxes"""
        # Create two boxes side by side
        box1 = cq.Workplane("XY").box(10, 10, 10)
        box2 = cq.Workplane("XY").center(15, 0).box(10, 10, 10)

        union = Part(
            name="union",
            geometry=box1.union(box2),
            backend=self.backend
        )

        volume = get_volume(union)
        expected = 1000 + 1000  # Two 10x10x10 boxes = 2000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_union_volume_overlapping(self):
        """Test union of overlapping boxes"""
        # Create two overlapping boxes
        box1 = cq.Workplane("XY").box(20, 10, 10)
        box2 = cq.Workplane("XY").center(10, 0).box(20, 10, 10)

        union = Part(
            name="union",
            geometry=box1.union(box2),
            backend=self.backend
        )

        volume = get_volume(union)

        # Box1: 20*10*10 = 2000
        # Box2: 20*10*10 = 2000
        # Overlap: 10*10*10 = 1000
        # Union: 2000 + 2000 - 1000 = 3000
        expected = 3000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_difference_volume_centered_hole(self):
        """Test difference operation (box with centered hole)"""
        # Create box with centered hole
        box = cq.Workplane("XY").box(30, 30, 30)
        hole = cq.Workplane("XY").box(10, 10, 40)  # Taller to ensure full cut

        difference = Part(
            name="difference",
            geometry=box.cut(hole),
            backend=self.backend
        )

        volume = get_volume(difference)

        # Box: 30*30*30 = 27000
        # Hole: 10*10*30 = 3000 (only the overlapping part)
        # Result: 27000 - 3000 = 24000
        expected = 24000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_difference_volume_cylinder_from_box(self):
        """Test cutting a cylinder from a box"""
        # Create box with cylindrical hole
        box = cq.Workplane("XY").box(40, 40, 20)
        cylinder = cq.Workplane("XY").cylinder(20, 8)

        difference = Part(
            name="difference",
            geometry=box.cut(cylinder),
            backend=self.backend
        )

        volume = get_volume(difference)

        # Box volume: 40*40*20 = 32000
        # Cylinder volume: π*8²*20 ≈ 4021.24
        # Result: 32000 - 4021.24 ≈ 27978.76
        box_vol = 40 * 40 * 20
        cyl_vol = math.pi * 8**2 * 20
        expected = box_vol - cyl_vol

        # Verify within 1% accuracy
        assert abs(volume - expected) < abs(expected) * 0.01

    def test_intersection_volume(self):
        """Test intersection of two boxes"""
        # Create two intersecting boxes
        box1 = cq.Workplane("XY").box(20, 20, 20)
        box2 = cq.Workplane("XY").center(10, 0).box(20, 20, 20)

        intersection = Part(
            name="intersection",
            geometry=box1.intersect(box2),
            backend=self.backend
        )

        volume = get_volume(intersection)

        # Intersection should be 10x20x20 = 4000
        expected = 10 * 20 * 20  # 4000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01


class TestSurfaceAreaCalculations:
    """Test surface area calculation accuracy"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_surface_area_accuracy(self):
        """Test box surface area calculation"""
        # Create 10x20x30 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 20, 30),
            backend=self.backend
        )

        area = get_surface_area(box)
        # Surface area = 2*(lw + lh + wh) = 2*(10*20 + 10*30 + 20*30) = 2*(200+300+600) = 2200
        expected = 2 * (10*20 + 10*30 + 20*30)

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_cylinder_surface_area_accuracy(self):
        """Test cylinder surface area calculation"""
        # Create cylinder: radius=10, height=25
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(25, 10),
            backend=self.backend
        )

        area = get_surface_area(cylinder)
        # Surface area = 2*π*r*h + 2*π*r² = 2*π*10*25 + 2*π*10² = 500π + 200π = 700π
        lateral = 2 * math.pi * 10 * 25
        caps = 2 * math.pi * 10**2
        expected = lateral + caps

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_sphere_surface_area_accuracy(self):
        """Test sphere surface area calculation"""
        # Create sphere: radius=15
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").sphere(15),
            backend=self.backend
        )

        area = get_surface_area(sphere)
        # Surface area = 4*π*r² = 4*π*15² = 900π ≈ 2827.43
        expected = 4 * math.pi * 15**2

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_cube_surface_area(self):
        """Test surface area of a perfect cube"""
        # Create 20x20x20 cube
        cube = Part(
            name="cube",
            geometry=cq.Workplane("XY").box(20, 20, 20),
            backend=self.backend
        )

        area = get_surface_area(cube)
        # Surface area = 6*s² = 6*20² = 2400
        expected = 6 * 20**2

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01


class TestDimensionalConsistency:
    """Test consistency across dimensional measurements"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_volume_and_dimensions_consistency(self):
        """Test that volume matches dimensions"""
        # Create 15x25x35 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(15, 25, 35),
            backend=self.backend
        )

        dims = get_dimensions(box)
        volume = get_volume(box)

        # Calculate expected volume from dimensions
        expected_volume = dims['width'] * dims['height'] * dims['depth']

        # Should match within 1%
        assert abs(volume - expected_volume) < expected_volume * 0.01

    def test_surface_area_and_dimensions_consistency(self):
        """Test that surface area matches dimensions"""
        # Create 12x18x24 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(12, 18, 24),
            backend=self.backend
        )

        dims = get_dimensions(box)
        area = get_surface_area(box)

        # Calculate expected surface area from dimensions
        w, h, d = dims['width'], dims['height'], dims['depth']
        expected_area = 2 * (w*h + w*d + h*d)

        # Should match within 1%
        assert abs(area - expected_area) < expected_area * 0.01

    def test_get_dimensions_includes_volume_and_area(self):
        """Test that get_dimensions includes volume and surface area"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(20, 20, 20),
            backend=self.backend
        )

        dims = get_dimensions(box)

        # Should include volume
        assert 'volume' in dims
        assert dims['volume'] > 0

        # Should include surface_area
        assert 'surface_area' in dims
        assert dims['surface_area'] > 0

        # Values should match standalone functions
        assert abs(dims['volume'] - get_volume(box)) < 0.01
        assert abs(dims['surface_area'] - get_surface_area(box)) < 0.01


# Pytest markers for test organization
pytestmark = pytest.mark.dimensions
