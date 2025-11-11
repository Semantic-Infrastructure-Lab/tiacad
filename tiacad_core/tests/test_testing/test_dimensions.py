"""
Tests for testing/dimensions.py - Dimensional accuracy utilities

Tests cover:
- get_dimensions() for various primitive types
- get_volume() accuracy for all primitives
- get_surface_area() accuracy for all primitives
- Boolean operation volume/area verification
- Error handling and validation

Author: TIA (v3.1 Week 3)
Version: 1.0 (v3.1)
"""

import pytest
import math
from tiacad_core.testing.dimensions import (
    get_dimensions,
    get_volume,
    get_surface_area,
    DimensionError,
)
from tiacad_core.part import Part
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestGetDimensions:
    """Test get_dimensions() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

    def test_box_dimensions(self):
        """Test dimension extraction from a box"""
        # Create 50x30x20 box
        box = Part(
            name="test_box",
            geometry=cq.Workplane("XY").box(50, 30, 20),
            backend=self.backend
        )

        dims = get_dimensions(box)

        # Verify bounding box dimensions
        # Note: CadQuery box(w, d, h) creates box with those dimensions
        assert abs(dims['width'] - 50.0) < 0.01
        assert abs(dims['height'] - 30.0) < 0.01
        assert abs(dims['depth'] - 20.0) < 0.01

        # Verify volume is present
        assert 'volume' in dims
        assert dims['volume'] > 0

        # Verify surface area is present
        assert 'surface_area' in dims
        assert dims['surface_area'] > 0

    def test_cylinder_dimensions(self):
        """Test dimension extraction from a cylinder"""
        # Create cylinder with radius=5, height=20
        cylinder = Part(
            name="test_cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),
            backend=self.backend
        )

        dims = get_dimensions(cylinder)

        # Cylinder bounding box should be 2*radius in X and Y
        assert abs(dims['width'] - 10.0) < 0.1   # 2*5
        assert abs(dims['height'] - 10.0) < 0.1  # 2*5
        assert abs(dims['depth'] - 20.0) < 0.1   # height

        # Verify volume and surface area are present
        assert dims['volume'] > 0
        assert dims['surface_area'] > 0

    def test_sphere_dimensions(self):
        """Test dimension extraction from a sphere"""
        # Create sphere with radius=10
        sphere = Part(
            name="test_sphere",
            geometry=cq.Workplane("XY").sphere(10),
            backend=self.backend
        )

        dims = get_dimensions(sphere)

        # Sphere bounding box should be 2*radius in all directions
        assert abs(dims['width'] - 20.0) < 0.1
        assert abs(dims['height'] - 20.0) < 0.1
        assert abs(dims['depth'] - 20.0) < 0.1

        # Verify volume and surface area are present
        assert dims['volume'] > 0
        assert dims['surface_area'] > 0

    def test_dimensions_invalid_input(self):
        """Test that invalid input raises DimensionError"""
        with pytest.raises(DimensionError, match="part must be a Part instance"):
            get_dimensions("not a part")


class TestGetVolume:
    """Test get_volume() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

    def test_box_volume(self):
        """Test volume calculation for a box"""
        # Create 10x10x10 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        volume = get_volume(box)
        expected = 10 * 10 * 10  # 1000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01
        assert volume > 0

    def test_cylinder_volume(self):
        """Test volume calculation for a cylinder"""
        # Create cylinder with radius=5, height=20
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),
            backend=self.backend
        )

        volume = get_volume(cylinder)
        expected = math.pi * 5**2 * 20  # π*r²*h

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_sphere_volume(self):
        """Test volume calculation for a sphere"""
        # Create sphere with radius=10
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").sphere(10),
            backend=self.backend
        )

        volume = get_volume(sphere)
        expected = (4/3) * math.pi * 10**3  # (4/3)*π*r³

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_cone_volume(self):
        """Test volume calculation for a cone"""
        # Create cone with radius=6, height=12
        # Using CadQuery's cone (height, bottomRadius, topRadius=0)
        cone = Part(
            name="cone",
            geometry=cq.Workplane("XY").union(
                cq.Solid.makeCone(6, 0, 12)
            ),
            backend=self.backend
        )

        volume = get_volume(cone)
        expected = (1/3) * math.pi * 6**2 * 12  # (1/3)*π*r²*h

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_boolean_union_volume(self):
        """Test volume calculation for union of two boxes"""
        # Create two overlapping boxes
        box1 = cq.Workplane("XY").box(20, 10, 10)
        box2 = cq.Workplane("XY").center(10, 0).box(20, 10, 10)

        # Union them
        union = Part(
            name="union",
            geometry=box1.union(box2),
            backend=self.backend
        )

        volume = get_volume(union)

        # Volume should be less than sum due to overlap
        # Box1: 20*10*10 = 2000
        # Box2: 20*10*10 = 2000
        # Overlap: 10*10*10 = 1000
        # Union: 2000 + 2000 - 1000 = 3000
        expected = 3000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_boolean_difference_volume(self):
        """Test volume calculation for difference of two boxes"""
        # Create box with hole
        box = cq.Workplane("XY").box(20, 20, 20)
        hole = cq.Workplane("XY").box(10, 10, 30)  # Taller to ensure full cut

        difference = Part(
            name="difference",
            geometry=box.cut(hole),
            backend=self.backend
        )

        volume = get_volume(difference)

        # Volume should be box - hole
        # Box: 20*20*20 = 8000
        # Hole: 10*10*20 = 2000 (only the overlapping part)
        # Result: 8000 - 2000 = 6000
        expected = 6000

        # Verify within 1% accuracy
        assert abs(volume - expected) < expected * 0.01

    def test_volume_invalid_input(self):
        """Test that invalid input raises DimensionError"""
        with pytest.raises(DimensionError, match="part must be a Part instance"):
            get_volume("not a part")


class TestGetSurfaceArea:
    """Test get_surface_area() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

    def test_box_surface_area(self):
        """Test surface area calculation for a box"""
        # Create 10x10x10 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        area = get_surface_area(box)
        # Box surface area = 2*(lw + lh + wh)
        # For 10x10x10: 2*(100 + 100 + 100) = 600
        expected = 600

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_cylinder_surface_area(self):
        """Test surface area calculation for a cylinder"""
        # Create cylinder with radius=5, height=20
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),
            backend=self.backend
        )

        area = get_surface_area(cylinder)
        # Cylinder SA = 2*π*r*h + 2*π*r²
        # Lateral area + 2 caps
        lateral = 2 * math.pi * 5 * 20
        caps = 2 * math.pi * 5**2
        expected = lateral + caps

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_sphere_surface_area(self):
        """Test surface area calculation for a sphere"""
        # Create sphere with radius=10
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").sphere(10),
            backend=self.backend
        )

        area = get_surface_area(sphere)
        # Sphere SA = 4*π*r²
        expected = 4 * math.pi * 10**2

        # Verify within 1% accuracy
        assert abs(area - expected) < expected * 0.01

    def test_surface_area_invalid_input(self):
        """Test that invalid input raises DimensionError"""
        with pytest.raises(DimensionError, match="part must be a Part instance"):
            get_surface_area("not a part")


class TestDimensionsIntegration:
    """Integration tests for dimensional utilities"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_all_dimensions_consistent(self):
        """Test that all dimension functions return consistent values"""
        # Create a 10x20x30 box
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 20, 30),
            backend=self.backend
        )

        # Get dimensions
        dims = get_dimensions(box)
        volume = get_volume(box)
        area = get_surface_area(box)

        # Verify consistency
        assert dims['volume'] == volume
        assert dims['surface_area'] == area

        # Verify expected values
        expected_volume = 10 * 20 * 30
        expected_area = 2 * (10*20 + 10*30 + 20*30)

        assert abs(volume - expected_volume) < expected_volume * 0.01
        assert abs(area - expected_area) < expected_area * 0.01

    def test_small_part_precision(self):
        """Test dimensional accuracy for small parts"""
        # Create a very small box (1mm cube)
        small_box = Part(
            name="small_box",
            geometry=cq.Workplane("XY").box(1, 1, 1),
            backend=self.backend
        )

        volume = get_volume(small_box)
        area = get_surface_area(small_box)

        # Verify within 1%
        assert abs(volume - 1.0) < 0.01
        assert abs(area - 6.0) < 0.06

    def test_large_part_precision(self):
        """Test dimensional accuracy for large parts"""
        # Create a large box (1000 unit cube)
        large_box = Part(
            name="large_box",
            geometry=cq.Workplane("XY").box(1000, 1000, 1000),
            backend=self.backend
        )

        volume = get_volume(large_box)
        area = get_surface_area(large_box)

        expected_volume = 1e9  # 1000^3
        expected_area = 6e6    # 6 * 1000^2

        # Verify within 1%
        assert abs(volume - expected_volume) < expected_volume * 0.01
        assert abs(area - expected_area) < expected_area * 0.01
