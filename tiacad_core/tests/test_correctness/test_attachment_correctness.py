"""
Attachment Correctness Tests

Tests that verify correct attachment behavior between parts, including:
- Zero-distance attachments (parts touching)
- Face-to-face attachments
- Pattern attachment spacing (linear, circular, grid)
- Rotated attachments

Part of the Testing Confidence Plan v3.1 Week 4.

Author: TIA (v3.1 Week 4)
Version: 1.0 (v3.1)
"""

import pytest
import math

from tiacad_core.testing.measurements import (
    measure_distance,
    get_bounding_box_dimensions,
)
from tiacad_core.testing.orientation import (
    get_normal_vector,
    parts_aligned,
)
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import CadQueryBackend
import cadquery as cq


class TestBasicAttachments:
    """Test basic part-to-part attachments"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_cylinder_on_box_top_zero_distance(self):
        """Test cylinder attached to box top face (distance = 0)"""
        # Create a box centered at origin
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(20, 20, 10),
            backend=self.backend
        )

        # Create cylinder on top of box
        # Box is 10 units tall, so top face is at z=5
        # Cylinder with height 10 centered at z=10 (base at z=5)
        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").workplane(offset=10).cylinder(10, 5),
            backend=self.backend
        )

        # Distance between box top face and cylinder bottom face should be ~0
        dist = measure_distance(box, cylinder, ref1="face_top", ref2="face_bottom")

        assert dist < 0.01, f"Expected ~0 distance, got {dist}"

    def test_cylinder_on_box_top_centers_aligned(self):
        """Test cylinder on box top has aligned centers in XY plane"""
        box = Part(
            name="box",
            geometry=cq.Workplane("XY").box(20, 20, 10),
            backend=self.backend
        )

        cylinder = Part(
            name="cylinder",
            geometry=cq.Workplane("XY").workplane(offset=10).cylinder(10, 5),
            backend=self.backend
        )

        # Centers should be aligned in XY plane (along Z axis)
        aligned = parts_aligned(box, cylinder, axis='z', tolerance=0.01)
        assert aligned, "Cylinder and box should be aligned along Z axis"

    def test_box_beside_box_face_to_face(self):
        """Test box attached face-to-face beside another box"""
        # First box at origin
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        # Second box 10 units to the right (touching right face of box1)
        # Box1 right face is at x=5, Box2 left face should be at x=5
        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").center(10, 0).box(10, 10, 10),
            backend=self.backend
        )

        # Distance between right face of box1 and left face of box2 should be ~0
        dist = measure_distance(box1, box2, ref1="face_right", ref2="face_left")

        assert dist < 0.01, f"Expected ~0 distance, got {dist}"

    def test_box_beside_box_aligned_in_yz(self):
        """Test boxes beside each other are aligned in YZ plane"""
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(10, 10, 10),
            backend=self.backend
        )

        box2 = Part(
            name="box2",
            geometry=cq.Workplane("XY").center(10, 0).box(10, 10, 10),
            backend=self.backend
        )

        # Should be aligned perpendicular to X axis (same Y and Z)
        aligned = parts_aligned(box1, box2, axis='x', tolerance=0.01)
        assert aligned, "Boxes should be aligned in YZ plane"

    def test_sphere_on_plane_tangent(self):
        """Test sphere resting on a plane (tangent contact)"""
        # Create a thin box to represent a plane at z=0
        plane = Part(
            name="plane",
            geometry=cq.Workplane("XY").box(100, 100, 2),
            backend=self.backend
        )

        # Create sphere with radius 10, center at z=11 (touching top of plane at z=1)
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").workplane(offset=11).sphere(10),
            backend=self.backend
        )

        # Distance between plane top and sphere center should equal sphere radius
        dist = measure_distance(plane, sphere, ref1="face_top", ref2="center")

        # Plane top is at z=1, sphere center at z=11, so distance should be 10
        assert abs(dist - 10.0) < 0.1, f"Expected distance of 10, got {dist}"

    def test_sphere_on_plane_zero_gap(self):
        """Test sphere on plane has zero gap at contact point"""
        plane = Part(
            name="plane",
            geometry=cq.Workplane("XY").box(100, 100, 2),
            backend=self.backend
        )

        # Sphere with radius 10, bottom should touch plane top
        # Plane top at z=1, sphere bottom at z=1, center at z=11
        sphere = Part(
            name="sphere",
            geometry=cq.Workplane("XY").workplane(offset=11).sphere(10),
            backend=self.backend
        )

        # Get the distance between centers
        dist_centers = measure_distance(plane, sphere, ref1="center", ref2="center")

        # Plane center at z=0, sphere center at z=11
        # Distance should be 11
        assert abs(dist_centers - 11.0) < 0.1, f"Expected distance of 11, got {dist_centers}"

    def test_rotated_box_attachment_90deg_z(self):
        """Test box rotated 90° around Z axis attached to another box"""
        # First box at origin
        box1 = Part(
            name="box1",
            geometry=cq.Workplane("XY").box(20, 10, 10),
            backend=self.backend
        )

        # Second box rotated 90° around Z, placed to the right
        # Create at origin, rotate, then move
        box2 = Part(
            name="box2",
            geometry=(
                cq.Workplane("XY")
                .transformed(rotate=cq.Vector(0, 0, 90))
                .center(15, 0)
                .box(20, 10, 10)
            ),
            backend=self.backend
        )

        # Measure distance between centers
        dist = measure_distance(box1, box2)

        # Centers should be 15 units apart
        assert abs(dist - 15.0) < 0.5, f"Expected distance of ~15, got {dist}"

    def test_stacked_boxes_vertical_alignment(self):
        """Test vertically stacked boxes maintain alignment"""
        # Bottom box
        box_bottom = Part(
            name="box_bottom",
            geometry=cq.Workplane("XY").box(20, 20, 10),
            backend=self.backend
        )

        # Top box stacked on bottom
        # Bottom box top face at z=5, top box 10 units tall, center at z=10
        box_top = Part(
            name="box_top",
            geometry=cq.Workplane("XY").workplane(offset=10).box(20, 20, 10),
            backend=self.backend
        )

        # Should be aligned along Z axis
        aligned = parts_aligned(box_bottom, box_top, axis='z', tolerance=0.01)
        assert aligned, "Stacked boxes should be aligned along Z axis"

        # Distance between top face of bottom and bottom face of top should be ~0
        dist = measure_distance(box_bottom, box_top, ref1="face_top", ref2="face_bottom")
        assert dist < 0.01, f"Expected ~0 distance, got {dist}"


class TestPatternAttachments:
    """Test pattern-based attachments"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_linear_pattern_spacing_x_axis(self):
        """Test linear pattern spacing along X axis"""
        # Create 3 boxes in a line along X axis with 30 unit spacing
        boxes = []
        for i in range(3):
            box = Part(
                name=f"box_{i}",
                geometry=cq.Workplane("XY").center(i * 30, 0).box(10, 10, 10),
                backend=self.backend
            )
            boxes.append(box)

        # Check spacing between adjacent boxes
        dist_0_1 = measure_distance(boxes[0], boxes[1])
        dist_1_2 = measure_distance(boxes[1], boxes[2])

        assert abs(dist_0_1 - 30.0) < 0.1, f"Expected spacing of 30, got {dist_0_1}"
        assert abs(dist_1_2 - 30.0) < 0.1, f"Expected spacing of 30, got {dist_1_2}"

        # All should be aligned perpendicular to X
        assert parts_aligned(boxes[0], boxes[1], axis='x', tolerance=0.01)
        assert parts_aligned(boxes[1], boxes[2], axis='x', tolerance=0.01)

    def test_linear_pattern_spacing_y_axis(self):
        """Test linear pattern spacing along Y axis"""
        # Create 4 cylinders in a line along Y axis with 25 unit spacing
        cylinders = []
        for i in range(4):
            cyl = Part(
                name=f"cyl_{i}",
                geometry=cq.Workplane("XY").center(0, i * 25).cylinder(10, 5),
                backend=self.backend
            )
            cylinders.append(cyl)

        # Check spacing between first and last
        dist_0_3 = measure_distance(cylinders[0], cylinders[3])

        # Should be 3 * 25 = 75 units apart
        assert abs(dist_0_3 - 75.0) < 0.1, f"Expected distance of 75, got {dist_0_3}"

        # All should be aligned along Y axis (perpendicular to Y)
        for i in range(len(cylinders) - 1):
            assert parts_aligned(cylinders[i], cylinders[i+1], axis='y', tolerance=0.01)

    def test_circular_pattern_spacing(self):
        """Test circular pattern spacing around a center point"""
        # Create 4 boxes in a circle (90° apart) at radius 20
        boxes = []
        radius = 20.0
        num_parts = 4

        for i in range(num_parts):
            angle = i * (360.0 / num_parts)  # 0, 90, 180, 270
            angle_rad = math.radians(angle)
            x = radius * math.cos(angle_rad)
            y = radius * math.sin(angle_rad)

            box = Part(
                name=f"box_{i}",
                geometry=cq.Workplane("XY").center(x, y).box(5, 5, 5),
                backend=self.backend
            )
            boxes.append(box)

        # Check that all boxes are equidistant from origin
        for i, box in enumerate(boxes):
            dist = measure_distance(
                Part(name="origin", geometry=cq.Workplane("XY").box(1, 1, 1), backend=self.backend),
                box
            )
            assert abs(dist - radius) < 0.5, f"Box {i} distance from origin: expected {radius}, got {dist}"

    def test_circular_pattern_angular_spacing(self):
        """Test circular pattern maintains correct angular spacing"""
        # Create 6 parts in a circle (60° apart) at radius 15
        parts = []
        radius = 15.0
        num_parts = 6

        for i in range(num_parts):
            angle = i * (360.0 / num_parts)  # 0, 60, 120, 180, 240, 300
            angle_rad = math.radians(angle)
            x = radius * math.cos(angle_rad)
            y = radius * math.sin(angle_rad)

            part = Part(
                name=f"part_{i}",
                geometry=cq.Workplane("XY").center(x, y).cylinder(5, 3),
                backend=self.backend
            )
            parts.append(part)

        # Check arc distance between adjacent parts
        # Arc length = radius * angle_rad
        expected_arc = radius * math.radians(60)  # ~15.7

        for i in range(num_parts):
            next_i = (i + 1) % num_parts
            dist = measure_distance(parts[i], parts[next_i])

            # Arc distance should be close to chord distance for small angles
            # Chord length = 2 * radius * sin(angle/2)
            expected_chord = 2 * radius * math.sin(math.radians(30))  # sin(60/2)

            assert abs(dist - expected_chord) < 0.5, \
                f"Distance between parts {i} and {next_i}: expected ~{expected_chord}, got {dist}"

    def test_grid_pattern_spacing_2x3(self):
        """Test grid pattern with 2 rows and 3 columns"""
        # Create 2x3 grid with 20 unit spacing in X and 15 unit spacing in Y
        boxes = []
        spacing_x = 20.0
        spacing_y = 15.0

        for row in range(2):
            for col in range(3):
                x = col * spacing_x
                y = row * spacing_y

                box = Part(
                    name=f"box_{row}_{col}",
                    geometry=cq.Workplane("XY").center(x, y).box(8, 8, 8),
                    backend=self.backend
                )
                boxes.append(box)

        # Check horizontal spacing (same row)
        # Row 0: boxes 0, 1, 2
        dist_col_0_1 = measure_distance(boxes[0], boxes[1])  # (0,0) to (1,0)
        dist_col_1_2 = measure_distance(boxes[1], boxes[2])  # (1,0) to (2,0)

        assert abs(dist_col_0_1 - spacing_x) < 0.1, f"Expected X spacing of {spacing_x}, got {dist_col_0_1}"
        assert abs(dist_col_1_2 - spacing_x) < 0.1, f"Expected X spacing of {spacing_x}, got {dist_col_1_2}"

    def test_grid_pattern_alignment(self):
        """Test grid pattern maintains alignment in both axes"""
        # Create 3x3 grid with 10 unit spacing
        boxes = []
        spacing = 10.0

        for row in range(3):
            for col in range(3):
                x = col * spacing
                y = row * spacing

                box = Part(
                    name=f"box_{row}_{col}",
                    geometry=cq.Workplane("XY").center(x, y).box(5, 5, 5),
                    backend=self.backend
                )
                boxes.append(box)

        # Check vertical alignment (same column, different rows)
        # Column 0: boxes at indices 0, 3, 6
        # Column 1: boxes at indices 1, 4, 7
        for col in range(3):
            for row1 in range(3):
                for row2 in range(row1 + 1, 3):
                    idx1 = row1 * 3 + col
                    idx2 = row2 * 3 + col

                    # Should be aligned perpendicular to Y (same X, Z)
                    aligned = parts_aligned(boxes[idx1], boxes[idx2], axis='y', tolerance=0.01)
                    assert aligned, f"Boxes at ({row1},{col}) and ({row2},{col}) should be aligned in X"

    def test_grid_pattern_vertical_spacing(self):
        """Test grid pattern vertical spacing"""
        # Create 2x2 grid
        boxes = []
        spacing = 25.0

        for row in range(2):
            for col in range(2):
                x = col * spacing
                y = row * spacing

                box = Part(
                    name=f"box_{row}_{col}",
                    geometry=cq.Workplane("XY").center(x, y).box(10, 10, 10),
                    backend=self.backend
                )
                boxes.append(box)

        # Check vertical spacing (same column)
        # Column 0: boxes 0 and 2 (at (0,0) and (0,1))
        dist_row = measure_distance(boxes[0], boxes[2])

        assert abs(dist_row - spacing) < 0.1, f"Expected Y spacing of {spacing}, got {dist_row}"

    def test_3d_grid_pattern(self):
        """Test 3D grid pattern with spacing in X, Y, and Z"""
        # Create 2x2x2 3D grid
        boxes = []
        spacing = 15.0

        for x_i in range(2):
            for y_i in range(2):
                for z_i in range(2):
                    x = x_i * spacing
                    y = y_i * spacing
                    z = z_i * spacing

                    box = Part(
                        name=f"box_{x_i}_{y_i}_{z_i}",
                        geometry=(
                            cq.Workplane("XY")
                            .workplane(offset=z)
                            .center(x, y)
                            .box(5, 5, 5)
                        ),
                        backend=self.backend
                    )
                    boxes.append(box)

        # Check diagonal distance from (0,0,0) to (1,1,1)
        # Should be sqrt(3) * spacing
        dist_diagonal = measure_distance(boxes[0], boxes[-1])
        expected_diagonal = math.sqrt(3) * spacing

        assert abs(dist_diagonal - expected_diagonal) < 0.5, \
            f"Expected diagonal distance of {expected_diagonal}, got {dist_diagonal}"


# Pytest markers for test organization
pytestmark = pytest.mark.attachment
