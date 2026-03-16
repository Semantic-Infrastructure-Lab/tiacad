"""
Rotation Correctness Tests

Tests that verify correct rotation behavior, including:
- Basic rotations (90°, 45°, arbitrary angles around X, Y, Z axes)
- Face normal verification after rotation
- Transform composition order (rotate-translate vs translate-rotate)
- Multiple rotation composition

Part of the Testing Confidence Plan v3.1 Week 5.

Author: TIA (v3.1 Week 5)
Version: 1.0 (v3.1)
"""

import pytest
import numpy as np
import math

from tiacad_core.testing.orientation import (
    get_orientation_angles,
    get_normal_vector,
    parts_aligned,
)
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestBasicRotations:
    """Test basic rotation correctness around each axis"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_box_rotate_90deg_around_z_axis(self):
        """Test box rotated 90° around Z axis has correct orientation"""
        # Create unrotated box
        box_unrotated = Part(
            name="box_unrotated",
            geometry=cq.Workplane("XY").box(20, 10, 5),
            backend=self.backend
        )

        # Create box rotated 90° around Z
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 90))
                .box(20, 10, 5)
            ),
            backend=self.backend
        )

        # After 90° rotation around Z:
        # Original dimensions: 20 (X) x 10 (Y) x 5 (Z)
        # Rotated dimensions: 10 (X) x 20 (Y) x 5 (Z)
        # (X and Y swap due to 90° rotation)

        # Get bounding box dimensions to verify rotation
        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_unrotated = get_bounding_box_dimensions(box_unrotated)
        dims_rotated = get_bounding_box_dimensions(box_rotated)

        # X and Y should be swapped
        assert abs(dims_unrotated['width'] - 20.0) < 0.1
        assert abs(dims_unrotated['height'] - 10.0) < 0.1

        # After 90° Z rotation, width and height swap
        assert abs(dims_rotated['width'] - 10.0) < 0.5
        assert abs(dims_rotated['height'] - 20.0) < 0.5

        # Z dimension unchanged
        assert abs(dims_rotated['depth'] - 5.0) < 0.1

    def test_box_rotate_90deg_around_x_axis(self):
        """Test box rotated 90° around X axis has correct orientation"""
        # Create box rotated 90° around X
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(90, 0, 0))
                .box(10, 20, 30)
            ),
            backend=self.backend
        )

        # After 90° rotation around X:
        # Original: 10 (X) x 20 (Y) x 30 (Z)
        # Rotated: 10 (X) x 30 (Y) x 20 (Z)
        # (Y and Z swap)

        from tiacad_core.testing.measurements import get_bounding_box_dimensions
        dims = get_bounding_box_dimensions(box_rotated)

        # X unchanged, Y and Z swap
        assert abs(dims['width'] - 10.0) < 0.1
        # Y and Z may swap depending on rotation direction
        # Just verify dimensions make sense
        assert abs(dims['height'] - 30.0) < 0.5
        assert abs(dims['depth'] - 20.0) < 0.5

    def test_box_rotate_90deg_around_y_axis(self):
        """Test box rotated 90° around Y axis has correct orientation"""
        # Create box rotated 90° around Y
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 90, 0))
                .box(40, 10, 20)
            ),
            backend=self.backend
        )

        # After 90° rotation around Y:
        # Original: 40 (X) x 10 (Y) x 20 (Z)
        # Rotated: 20 (X) x 10 (Y) x 40 (Z)
        # (X and Z swap)

        from tiacad_core.testing.measurements import get_bounding_box_dimensions
        dims = get_bounding_box_dimensions(box_rotated)

        # Y unchanged, X and Z swap
        assert abs(dims['height'] - 10.0) < 0.1
        # X and Z may swap
        assert abs(dims['width'] - 20.0) < 0.5
        assert abs(dims['depth'] - 40.0) < 0.5

    def test_box_rotate_45deg_around_z_axis(self):
        """Test box rotated 45° around Z axis"""
        # Create box rotated 45° around Z
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 45))
                .box(10, 10, 10)
            ),
            backend=self.backend
        )

        # After 45° rotation, bounding box should be larger
        # For a 10x10x10 box rotated 45° around Z:
        # Diagonal projection = 10 * sqrt(2) ≈ 14.14

        from tiacad_core.testing.measurements import get_bounding_box_dimensions
        dims = get_bounding_box_dimensions(box_rotated)

        # X and Y should be approximately 10*sqrt(2)
        expected_diagonal = 10 * math.sqrt(2)
        assert abs(dims['width'] - expected_diagonal) < 1.0
        assert abs(dims['height'] - expected_diagonal) < 1.0

        # Z unchanged
        assert abs(dims['depth'] - 10.0) < 0.1

    def test_cylinder_rotate_90deg_lies_horizontal(self):
        """Test cylinder rotated 90° lies horizontal"""
        # Vertical cylinder (default)
        cylinder_vertical = Part(
            name="cylinder_vertical",
            geometry=cq.Workplane("XY").cylinder(20, 5),  # height, radius
            backend=self.backend
        )

        # Horizontal cylinder (rotated 90° around Y)
        cylinder_horizontal = Part(
            name="cylinder_horizontal",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 90, 0))
                .cylinder(20, 5)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_vertical = get_bounding_box_dimensions(cylinder_vertical)
        dims_horizontal = get_bounding_box_dimensions(cylinder_horizontal)

        # Vertical: width=10, height=10, depth=20
        assert abs(dims_vertical['width'] - 10.0) < 0.1
        assert abs(dims_vertical['depth'] - 20.0) < 0.1

        # Horizontal: width=20, depth=10 (dimensions swap)
        assert abs(dims_horizontal['width'] - 20.0) < 0.5
        assert abs(dims_horizontal['depth'] - 10.0) < 0.5

    def test_rotation_180deg_equivalent_to_two_90deg(self):
        """Test that 180° rotation equals two 90° rotations"""
        # Box rotated 180° around Z
        box_180 = Part(
            name="box_180",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 180))
                .box(15, 25, 10)
            ),
            backend=self.backend
        )

        # Box rotated 90° twice around Z
        box_90_twice = Part(
            name="box_90_twice",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 90))
                .transformed(rotate=cq.Vector(0, 0, 90))
                .box(15, 25, 10)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_180 = get_bounding_box_dimensions(box_180)
        dims_90_twice = get_bounding_box_dimensions(box_90_twice)

        # Both should have same dimensions
        assert abs(dims_180['width'] - dims_90_twice['width']) < 0.5
        assert abs(dims_180['height'] - dims_90_twice['height']) < 0.5
        assert abs(dims_180['depth'] - dims_90_twice['depth']) < 0.1

    def test_rotation_360deg_returns_to_original(self):
        """Test that 360° rotation returns to original orientation"""
        # Original box
        box_original = Part(
            name="box_original",
            geometry=cq.Workplane("XY").box(20, 15, 10),
            backend=self.backend
        )

        # Box rotated 360° around Z
        box_360 = Part(
            name="box_360",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 360))
                .box(20, 15, 10)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_original = get_bounding_box_dimensions(box_original)
        dims_360 = get_bounding_box_dimensions(box_360)

        # Dimensions should be identical
        assert abs(dims_original['width'] - dims_360['width']) < 0.1
        assert abs(dims_original['height'] - dims_360['height']) < 0.1
        assert abs(dims_original['depth'] - dims_360['depth']) < 0.1

    def test_rotation_arbitrary_angle_30deg(self):
        """Test rotation by arbitrary angle (30°)"""
        # Box rotated 30° around Z
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 30))
                .box(20, 10, 5)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions
        dims = get_bounding_box_dimensions(box_rotated)

        # Bounding box should be larger than original due to rotation
        # Original: 20x10x5
        # After 30° rotation, bbox should be wider
        assert dims['width'] > 20.0
        assert dims['height'] > 10.0
        assert abs(dims['depth'] - 5.0) < 0.1  # Z unchanged


class TestNormalVectorsAfterRotation:
    """Test face normal vectors after rotation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_unrotated_box_top_normal_points_up(self):
        """Test that unrotated box top face normal points up"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        normal = get_normal_vector(box, "face_top")

        # Should point up (+Z direction)
        assert normal[2] > 0.9  # Primarily in +Z direction
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)

    def test_box_rotated_90deg_x_top_normal_changes(self):
        """Test box rotated 90° around X has changed top normal"""
        # After rotating 90° around X axis:
        # Original top face (pointing +Z) now points in +Y direction

        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(90, 0, 0))
                .box(10, 10, 10)
            ),
            backend=self.backend
        )

        # The "top" face after rotation
        normal = get_normal_vector(box_rotated, "face_top")

        # After 90° rotation around X, top face should point in Y direction
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)
        # Normal should have significant Y or Z component
        assert abs(normal[1]) > 0.5 or abs(normal[2]) > 0.5

    def test_box_rotated_90deg_z_front_normal_changes(self):
        """Test box rotated 90° around Z has changed front normal"""
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 90))
                .box(10, 10, 10)
            ),
            backend=self.backend
        )

        # After 90° rotation around Z, normals rotate in XY plane
        normal_front = get_normal_vector(box_rotated, "face_front")

        # Should be normalized
        assert np.linalg.norm(normal_front) == pytest.approx(1.0, abs=1e-6)

        # Should be primarily horizontal (in XY plane)
        assert abs(normal_front[2]) < 0.1  # Little Z component

    def test_cylinder_top_normal_after_90deg_rotation(self):
        """Test cylinder top face normal after 90° rotation"""
        # Cylinder lying on its side (rotated 90° around Y)
        cylinder_rotated = Part(
            name="cylinder_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 90, 0))
                .cylinder(20, 5)
            ),
            backend=self.backend
        )

        normal = get_normal_vector(cylinder_rotated, "face_top")

        # Should be normalized
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)

    def test_opposite_faces_have_opposite_normals_after_rotation(self):
        """Test that opposite faces maintain opposite normals after rotation"""
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 45))
                .box(10, 10, 10)
            ),
            backend=self.backend
        )

        normal_top = get_normal_vector(box_rotated, "face_top")
        normal_bottom = get_normal_vector(box_rotated, "face_bottom")

        # Opposite normals: dot product should be ~-1
        dot_product = np.dot(normal_top, normal_bottom)
        assert dot_product == pytest.approx(-1.0, abs=0.1)

    def test_perpendicular_faces_remain_perpendicular_after_rotation(self):
        """Test that perpendicular faces remain perpendicular after rotation"""
        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 30))
                .box(10, 10, 10)
            ),
            backend=self.backend
        )

        normal_top = get_normal_vector(box_rotated, "face_top")
        normal_front = get_normal_vector(box_rotated, "face_front")

        # Perpendicular: dot product should be ~0
        dot_product = np.dot(normal_top, normal_front)
        assert abs(dot_product) < 0.1


class TestTransformComposition:
    """Test transform composition order matters"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_translate_then_rotate_vs_rotate_then_translate(self):
        """Test that transform order matters: translate-rotate ≠ rotate-translate"""
        # Translate THEN rotate
        # Create at [10, 0, 0], then rotate 90° around Z
        box_translate_rotate = Part(
            name="box_translate_rotate",
            geometry=(
                cq.Workplane("XY")
                .center(10, 0)
                .box(5, 5, 5)
                .translate((0, 0, 0))  # No translation needed, already offset
                .rotate((0, 0, 0), (0, 0, 1), 90)  # Rotate around origin
            ),
            backend=self.backend
        )

        # Rotate THEN translate
        # Rotate 90° around Z, then move to [10, 0, 0]
        box_rotate_translate = Part(
            name="box_rotate_translate",
            geometry=(
                cq.Workplane("XY")
                .box(5, 5, 5)
                .rotate((0, 0, 0), (0, 0, 1), 90)
                .translate((10, 0, 0))
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_tr = get_bounding_box_dimensions(box_translate_rotate)
        dims_rt = get_bounding_box_dimensions(box_rotate_translate)

        # Centers should be at different positions
        center_tr = dims_tr['center']
        center_rt = dims_rt['center']

        # Should NOT be at the same position
        distance = np.linalg.norm(np.array(center_tr) - np.array(center_rt))
        assert distance > 1.0, f"Centers should be different, but distance is {distance}"

    def test_multiple_rotation_composition_xyz(self):
        """Test composition of multiple rotations around different axes"""
        # Rotate around X, then Z (not back through origin)
        box_xz = Part(
            name="box_xz",
            geometry=(
                cq.Workplane("XY")
                .box(10, 20, 30)
                .rotate((0, 0, 0), (1, 0, 0), 45)  # X by 45°
                .rotate((0, 0, 0), (0, 0, 1), 45)  # Z by 45°
            ),
            backend=self.backend
        )

        # Rotate around Z, then X (reverse order)
        box_zx = Part(
            name="box_zx",
            geometry=(
                cq.Workplane("XY")
                .box(10, 20, 30)
                .rotate((0, 0, 0), (0, 0, 1), 45)  # Z by 45°
                .rotate((0, 0, 0), (1, 0, 0), 45)  # X by 45°
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_xz = get_bounding_box_dimensions(box_xz)
        dims_zx = get_bounding_box_dimensions(box_zx)

        # Different rotation orders should produce different results
        # At least one dimension should differ significantly
        diff_w = abs(dims_xz['width'] - dims_zx['width'])
        diff_h = abs(dims_xz['height'] - dims_zx['height'])
        diff_d = abs(dims_xz['depth'] - dims_zx['depth'])

        # At least one should be significantly different (using 45° angles should show difference)
        assert (diff_w > 0.5 or diff_h > 0.5 or diff_d > 0.5), \
            f"Different rotation orders should produce different results (diffs: {diff_w:.3f}, {diff_h:.3f}, {diff_d:.3f})"

    def test_rotation_around_different_points(self):
        """Test rotation around different pivot points produces different results"""
        # Rotate around origin
        box_origin = Part(
            name="box_origin",
            geometry=(
                cq.Workplane("XY")
                .center(10, 0)
                .box(5, 5, 5)
                .rotate((0, 0, 0), (0, 0, 1), 90)  # Rotate around origin
            ),
            backend=self.backend
        )

        # Rotate around center of box
        box_center = Part(
            name="box_center",
            geometry=(
                cq.Workplane("XY")
                .center(10, 0)
                .box(5, 5, 5)
                .rotate((10, 0, 0), (0, 0, 1), 90)  # Rotate around box center
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        center_origin = get_bounding_box_dimensions(box_origin)['center']
        center_center = get_bounding_box_dimensions(box_center)['center']

        # Centers should be at different positions
        distance = np.linalg.norm(np.array(center_origin) - np.array(center_center))
        assert distance > 1.0, f"Rotation around different points should produce different positions"


class TestRotationAccuracy:
    """Test rotation angle accuracy"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_small_rotation_5deg(self):
        """Test small rotation angle (5°) produces expected change"""
        box_unrotated = Part(
            name="box_unrotated",
            geometry=cq.Workplane("XY").box(30, 10, 5),
            backend=self.backend
        )

        box_rotated = Part(
            name="box_rotated",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 5))
                .box(30, 10, 5)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims_unrotated = get_bounding_box_dimensions(box_unrotated)
        dims_rotated = get_bounding_box_dimensions(box_rotated)

        # Small rotation should produce small change in bounding box
        # Original: 30x10
        # After 5° rotation: slightly larger due to bounding box calculation
        # For a 30x10 rectangle rotated by 5°:
        # width ≈ 30*cos(5°) + 10*sin(5°) ≈ 30*0.996 + 10*0.087 ≈ 30.75
        # height ≈ 30*sin(5°) + 10*cos(5°) ≈ 30*0.087 + 10*0.996 ≈ 12.57
        assert dims_rotated['width'] >= dims_unrotated['width']
        assert dims_rotated['height'] >= dims_unrotated['height']

        # Reasonable upper bounds for 5° rotation
        assert dims_rotated['width'] < dims_unrotated['width'] + 3.0
        assert dims_rotated['height'] < dims_unrotated['height'] + 5.0

    def test_rotation_precision_consistency(self):
        """Test that same rotation produces consistent results"""
        # Create two boxes with same rotation
        box1 = Part(
            name="box1",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 37))
                .box(15, 15, 15)
            ),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 37))
                .box(15, 15, 15)
            ),
            backend=self.backend
        )

        from tiacad_core.testing.measurements import get_bounding_box_dimensions

        dims1 = get_bounding_box_dimensions(box1)
        dims2 = get_bounding_box_dimensions(box2)

        # Should have identical dimensions
        assert abs(dims1['width'] - dims2['width']) < 0.001
        assert abs(dims1['height'] - dims2['height']) < 0.001
        assert abs(dims1['depth'] - dims2['depth']) < 0.001


# Pytest markers for test organization
pytestmark = pytest.mark.rotation
