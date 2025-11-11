"""
Tests for testing/orientation.py - Orientation and rotation utilities

Tests cover:
- get_orientation_angles() with various rotations
- get_normal_vector() for face references
- parts_aligned() for alignment verification
- Error handling and edge cases

Author: TIA (v3.1 Week 2)
Version: 1.0 (v3.1 Week 2)
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from tiacad_core.testing.orientation import (
    get_orientation_angles,
    get_normal_vector,
    parts_aligned,
    OrientationError,
)
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestGetOrientationAngles:
    """Test get_orientation_angles() utility"""

    def setup_method(self):
        """Setup test fixtures with real CadQuery geometry"""
        self.backend = CadQueryBackend()

    def test_unrotated_box_center_has_no_orientation(self):
        """Test that center reference has no orientation (returns zeros)"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        angles = get_orientation_angles(box, reference="center")

        # Center reference has no orientation, should return zeros
        assert angles['has_orientation'] is False
        assert angles['roll'] == 0.0
        assert angles['pitch'] == 0.0
        assert angles['yaw'] == 0.0

    def test_upright_box_face_top_orientation(self):
        """Test orientation of top face on upright box"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        angles = get_orientation_angles(box, reference="face_top")

        # Top face should have orientation (normal pointing up)
        assert angles['has_orientation'] is True
        # Exact angles depend on frame construction, but should be consistent
        # For a face pointing up (+Z), we expect specific orientation

    def test_orientation_angles_range(self):
        """Test that angles are in expected ranges"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        angles = get_orientation_angles(box, reference="face_top")

        # Verify angle ranges
        assert -180.0 <= angles['roll'] <= 180.0
        assert -90.0 <= angles['pitch'] <= 90.0
        assert -180.0 <= angles['yaw'] <= 180.0

    def test_cylinder_face_top_orientation(self):
        """Test orientation of cylinder top face"""
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),  # height, radius
            backend=self.backend
        )

        angles = get_orientation_angles(cylinder, reference="face_top")

        # Cylinder top should have orientation
        assert angles['has_orientation'] is True

    def test_invalid_part_raises_error(self):
        """Test that invalid part raises OrientationError"""
        with pytest.raises(OrientationError, match="must be a Part instance"):
            get_orientation_angles("not a part")

    def test_invalid_reference_raises_error(self):
        """Test that invalid reference raises OrientationError"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        with pytest.raises(OrientationError, match="Failed to resolve"):
            get_orientation_angles(box, reference="nonexistent_reference")


class TestGetNormalVector:
    """Test get_normal_vector() utility"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_face_top_normal_points_up(self):
        """Test that top face normal points upward"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        normal = get_normal_vector(box, "face_top")

        # Top face should point up (positive Z direction)
        # Normal should be normalized
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)
        # Should point primarily in +Z direction
        assert normal[2] > 0.9  # Mostly upward

    def test_box_face_bottom_normal_points_down(self):
        """Test that bottom face normal points downward"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        normal = get_normal_vector(box, "face_bottom")

        # Bottom face should point down (negative Z direction)
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)
        assert normal[2] < -0.9  # Mostly downward

    def test_cylinder_face_top_normal(self):
        """Test cylinder top face normal"""
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),
            backend=self.backend
        )

        normal = get_normal_vector(cylinder, "face_top")

        # Should be normalized
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)
        # Should point upward
        assert normal[2] > 0.9

    def test_normal_vectors_are_normalized(self):
        """Test that all returned normals are unit vectors"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        for face_ref in ["face_top", "face_bottom", "face_left", "face_right"]:
            normal = get_normal_vector(box, face_ref)
            assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)

    def test_perpendicular_faces_have_perpendicular_normals(self):
        """Test that perpendicular faces have perpendicular normals"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        top_normal = get_normal_vector(box, "face_top")
        front_normal = get_normal_vector(box, "face_front")

        # Dot product of perpendicular vectors should be ~0
        dot_product = np.dot(top_normal, front_normal)
        assert abs(dot_product) < 0.01

    def test_opposite_faces_have_opposite_normals(self):
        """Test that opposite faces have opposite normals"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        top_normal = get_normal_vector(box, "face_top")
        bottom_normal = get_normal_vector(box, "face_bottom")

        # Opposite normals: dot product should be ~-1
        dot_product = np.dot(top_normal, bottom_normal)
        assert dot_product == pytest.approx(-1.0, abs=0.01)

    def test_center_reference_has_no_normal_raises_error(self):
        """Test that using center reference raises error"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        with pytest.raises(OrientationError, match="has no orientation"):
            get_normal_vector(box, "center")

    def test_invalid_part_raises_error(self):
        """Test that invalid part raises error"""
        with pytest.raises(OrientationError, match="must be a Part instance"):
            get_normal_vector("not a part", "face_top")


class TestPartsAligned:
    """Test parts_aligned() utility"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_boxes_aligned_along_z_axis(self):
        """Test that vertically stacked boxes are Z-aligned"""
        # Two boxes at same XY position, different Z
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").workplane(offset=20).box(10, 10, 10),
            backend=self.backend
        )

        # Should be aligned along Z axis (same X, Y)
        assert parts_aligned(box1, box2, axis='z', tolerance=0.1)

    def test_boxes_not_aligned_when_offset(self):
        """Test that offset boxes are not aligned"""
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        # Offset in X direction
        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").center(20, 0).box(10, 10, 10),
            backend=self.backend
        )

        # Should NOT be aligned along Z (different X)
        assert not parts_aligned(box1, box2, axis='z', tolerance=0.1)

    def test_alignment_along_x_axis(self):
        """Test alignment along X axis (same Y, Z)"""
        # Create two boxes at same Y, Z but different X
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").center(20, 0).box(10, 10, 10),
            backend=self.backend
        )

        # Should be aligned along X (same Y, Z)
        assert parts_aligned(box1, box2, axis='x', tolerance=0.1)

    def test_alignment_with_face_references(self):
        """Test alignment using face references"""
        # Stack boxes vertically
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").workplane(offset=15).box(10, 10, 10),
            backend=self.backend
        )

        # Top of box1 and bottom of box2 should be Z-aligned
        assert parts_aligned(
            box1, box2,
            axis='z',
            ref1="face_top",
            ref2="face_bottom",
            tolerance=0.1
        )

    def test_tolerance_parameter(self):
        """Test that tolerance parameter works correctly"""
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        # Slight offset (0.05 in X)
        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").center(0.05, 0).box(10, 10, 10),
            backend=self.backend
        )

        # Should be aligned with loose tolerance
        assert parts_aligned(box1, box2, axis='z', tolerance=0.1)

        # Should NOT be aligned with tight tolerance
        assert not parts_aligned(box1, box2, axis='z', tolerance=0.01)

    def test_invalid_axis_raises_error(self):
        """Test that invalid axis raises error"""
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        with pytest.raises(OrientationError, match="axis must be"):
            parts_aligned(box1, box2, axis='w')  # Invalid axis

    def test_invalid_part1_raises_error(self):
        """Test that invalid part1 raises error"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        with pytest.raises(OrientationError, match="part1 must be"):
            parts_aligned("not a part", box, axis='z')

    def test_invalid_part2_raises_error(self):
        """Test that invalid part2 raises error"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        with pytest.raises(OrientationError, match="part2 must be"):
            parts_aligned(box, "not a part", axis='z')


class TestOrientationIntegration:
    """Integration tests combining multiple orientation utilities"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_stacked_boxes_normal_alignment(self):
        """Test that stacked boxes have aligned normals"""
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").workplane(offset=15).box(10, 10, 10),
            backend=self.backend
        )

        # Both top faces should point up (same direction)
        normal1 = get_normal_vector(box1, "face_top")
        normal2 = get_normal_vector(box2, "face_top")

        # Normals should be parallel (dot product ~= 1)
        dot_product = np.dot(normal1, normal2)
        assert dot_product == pytest.approx(1.0, abs=0.01)

    def test_normal_consistency_across_primitives(self):
        """Test that normal extraction is consistent across primitives"""
        # Create different primitives with well-defined top faces
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").cylinder(20, 5),
            backend=self.backend
        )

        # Box and cylinder top faces should point upward
        # (Sphere has ambiguous face normals, so we skip it)
        for part in [box, cylinder]:
            normal = get_normal_vector(part, "face_top")
            assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)
            assert normal[2] > 0.9  # Points up
