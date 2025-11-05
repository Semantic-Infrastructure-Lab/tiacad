"""
Tests for GeometryBackend Spatial Query Methods

Tests the spatial reference extraction methods added to GeometryBackend:
- select_faces() / select_edges() (already existed, but tested here)
- get_face_center()
- get_face_normal()
- get_edge_point()
- get_edge_tangent()

These tests use MockBackend for speed and isolation.
Integration with real CadQuery is tested separately.
"""

import pytest
import math
from typing import Tuple

from tiacad_core.geometry.mock_backend import MockBackend, MockGeometry, MockFace, MockEdge


class TestFaceSelection:
    """Test face selection from geometry"""

    def test_select_top_face(self):
        """Select top face of a box (>Z)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, ">Z")

        assert len(faces) == 1
        assert isinstance(faces[0], MockFace)
        assert faces[0].center == (0, 0, 10)  # Top at z=10 (height/2)
        assert faces[0].normal == (0, 0, 1)

    def test_select_bottom_face(self):
        """Select bottom face of a box (<Z)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, "<Z")

        assert len(faces) == 1
        assert faces[0].center == (0, 0, -10)  # Bottom at z=-10
        assert faces[0].normal == (0, 0, -1)

    def test_select_right_face(self):
        """Select right face of a box (>X)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, ">X")

        assert len(faces) == 1
        assert faces[0].center == (5, 0, 0)  # Right at x=5 (width/2)
        assert faces[0].normal == (1, 0, 0)

    def test_select_left_face(self):
        """Select left face of a box (<X)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, "<X")

        assert len(faces) == 1
        assert faces[0].center == (-5, 0, 0)  # Left at x=-5
        assert faces[0].normal == (-1, 0, 0)

    def test_select_front_face(self):
        """Select front face of a box (>Y)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, ">Y")

        assert len(faces) == 1
        assert faces[0].center == (0, 2.5, 0)  # Front at y=2.5 (depth/2)
        assert faces[0].normal == (0, 1, 0)

    def test_select_back_face(self):
        """Select back face of a box (<Y)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, "<Y")

        assert len(faces) == 1
        assert faces[0].center == (0, -2.5, 0)  # Back at y=-2.5
        assert faces[0].normal == (0, -1, 0)

    def test_select_faces_translated_box(self):
        """Face selection works on translated geometry"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        translated = backend.translate(box, (100, 200, 300))

        faces = backend.select_faces(translated, ">Z")

        # Face should be at translated position
        assert faces[0].center == (100, 200, 310)  # center + height/2
        assert faces[0].normal == (0, 0, 1)

    def test_select_faces_returns_list(self):
        """select_faces always returns a list"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        faces = backend.select_faces(box, ">Z")

        assert isinstance(faces, list)
        assert len(faces) > 0


class TestEdgeSelection:
    """Test edge selection from geometry"""

    def test_select_vertical_edges(self):
        """Select vertical edges (|Z) from a box"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        edges = backend.select_edges(box, "|Z")

        # Box has 4 vertical edges
        assert len(edges) == 4
        assert all(isinstance(e, MockEdge) for e in edges)

        # All edges should be parallel to Z (same x,y at start/end)
        for edge in edges:
            assert edge.start[0] == edge.end[0]  # Same x
            assert edge.start[1] == edge.end[1]  # Same y
            assert edge.start[2] != edge.end[2]  # Different z

    def test_select_horizontal_edges(self):
        """Select horizontal edges (|X) from a box"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        edges = backend.select_edges(box, "|X")

        # Should return edges parallel to X
        assert len(edges) >= 1
        assert all(isinstance(e, MockEdge) for e in edges)

    def test_edge_start_end_different(self):
        """Edges have distinct start and end points"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        edges = backend.select_edges(box, "|Z")

        for edge in edges:
            assert edge.start != edge.end

    def test_edge_selection_on_translated_box(self):
        """Edge selection works on translated geometry"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        translated = backend.translate(box, (100, 200, 300))

        edges = backend.select_edges(translated, "|Z")

        # Edges should be at translated positions
        assert len(edges) == 4
        # Check first edge is translated
        assert edges[0].start != (-5, -2.5, -10)  # Not original position

    def test_select_edges_returns_list(self):
        """select_edges always returns a list"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        edges = backend.select_edges(box, "|Z")

        assert isinstance(edges, list)
        assert len(edges) > 0


class TestFaceCenterQuery:
    """Test get_face_center() method"""

    def test_get_face_center_basic(self):
        """Get center of a face"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        faces = backend.select_faces(box, ">Z")

        center = backend.get_face_center(faces[0])

        assert isinstance(center, tuple)
        assert len(center) == 3
        assert center == (0, 0, 10)

    def test_get_face_center_all_faces(self):
        """Get centers for all 6 box faces"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        selectors = [">Z", "<Z", ">X", "<X", ">Y", "<Y"]
        expected_centers = [
            (0, 0, 10),   # Top
            (0, 0, -10),  # Bottom
            (5, 0, 0),    # Right
            (-5, 0, 0),   # Left
            (0, 2.5, 0),  # Front
            (0, -2.5, 0), # Back
        ]

        for selector, expected in zip(selectors, expected_centers):
            faces = backend.select_faces(box, selector)
            center = backend.get_face_center(faces[0])
            assert center == expected, f"Failed for selector {selector}"

    def test_get_face_center_returns_tuple(self):
        """get_face_center returns tuple of 3 floats"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        faces = backend.select_faces(box, ">Z")

        center = backend.get_face_center(faces[0])

        assert isinstance(center, tuple)
        assert len(center) == 3
        assert all(isinstance(c, (int, float)) for c in center)

    def test_get_face_center_translated(self):
        """Face center accounts for translation"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        translated = backend.translate(box, (50, 60, 70))
        faces = backend.select_faces(translated, ">Z")

        center = backend.get_face_center(faces[0])

        assert center == (50, 60, 80)  # Translated + height/2


class TestFaceNormalQuery:
    """Test get_face_normal() method"""

    def test_get_face_normal_top(self):
        """Top face normal points up"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        faces = backend.select_faces(box, ">Z")

        normal = backend.get_face_normal(faces[0])

        assert normal == (0, 0, 1)

    def test_get_face_normal_all_faces(self):
        """All face normals are unit vectors pointing outward"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        test_cases = [
            (">Z", (0, 0, 1)),   # Top
            ("<Z", (0, 0, -1)),  # Bottom
            (">X", (1, 0, 0)),   # Right
            ("<X", (-1, 0, 0)),  # Left
            (">Y", (0, 1, 0)),   # Front
            ("<Y", (0, -1, 0)),  # Back
        ]

        for selector, expected_normal in test_cases:
            faces = backend.select_faces(box, selector)
            normal = backend.get_face_normal(faces[0])
            assert normal == expected_normal, f"Failed for selector {selector}"

    def test_face_normal_is_normalized(self):
        """Face normals are unit vectors (length 1)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        faces = backend.select_faces(box, ">Z")

        normal = backend.get_face_normal(faces[0])

        # Calculate length
        length = math.sqrt(sum(n**2 for n in normal))
        assert abs(length - 1.0) < 1e-10

    def test_face_normal_unchanged_by_translation(self):
        """Face normal direction is unaffected by translation"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        translated = backend.translate(box, (100, 200, 300))

        faces_original = backend.select_faces(box, ">Z")
        faces_translated = backend.select_faces(translated, ">Z")

        normal_original = backend.get_face_normal(faces_original[0])
        normal_translated = backend.get_face_normal(faces_translated[0])

        assert normal_original == normal_translated

    def test_get_face_normal_returns_tuple(self):
        """get_face_normal returns tuple of 3 floats"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        faces = backend.select_faces(box, ">Z")

        normal = backend.get_face_normal(faces[0])

        assert isinstance(normal, tuple)
        assert len(normal) == 3
        assert all(isinstance(n, (int, float)) for n in normal)


class TestEdgePointQuery:
    """Test get_edge_point() method"""

    def test_get_edge_point_start(self):
        """Get start point of an edge"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        point = backend.get_edge_point(edges[0], "start")

        assert isinstance(point, tuple)
        assert len(point) == 3
        # Vertical edge starts at bottom
        assert point[2] == -10  # z = -height/2

    def test_get_edge_point_end(self):
        """Get end point of an edge"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        point = backend.get_edge_point(edges[0], "end")

        assert isinstance(point, tuple)
        assert len(point) == 3
        # Vertical edge ends at top
        assert point[2] == 10  # z = height/2

    def test_get_edge_point_midpoint(self):
        """Get midpoint of an edge"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        start = backend.get_edge_point(edges[0], "start")
        end = backend.get_edge_point(edges[0], "end")
        midpoint = backend.get_edge_point(edges[0], "midpoint")

        # Midpoint should be average of start and end
        expected = tuple((s + e) / 2 for s, e in zip(start, end))
        assert midpoint == expected

    def test_get_edge_point_invalid_location(self):
        """Invalid location raises ValueError"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        with pytest.raises(ValueError, match="Invalid location"):
            backend.get_edge_point(edges[0], "invalid")

    def test_get_edge_point_all_locations(self):
        """Test all valid location options"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        locations = ["start", "end", "midpoint"]

        for location in locations:
            point = backend.get_edge_point(edges[0], location)
            assert isinstance(point, tuple)
            assert len(point) == 3

    def test_edge_point_returns_tuple(self):
        """get_edge_point returns tuple of 3 floats"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        point = backend.get_edge_point(edges[0], "midpoint")

        assert isinstance(point, tuple)
        assert len(point) == 3
        assert all(isinstance(p, (int, float)) for p in point)


class TestEdgeTangentQuery:
    """Test get_edge_tangent() method"""

    def test_get_edge_tangent_vertical(self):
        """Tangent of vertical edge points up"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        tangent = backend.get_edge_tangent(edges[0])

        # Vertical edge tangent should be (0, 0, ±1)
        assert tangent[0] == 0
        assert tangent[1] == 0
        assert abs(abs(tangent[2]) - 1.0) < 1e-10

    def test_get_edge_tangent_horizontal(self):
        """Tangent of horizontal edge is horizontal"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|X")

        tangent = backend.get_edge_tangent(edges[0])

        # Horizontal edge tangent should have z=0
        assert tangent[2] == 0

    def test_edge_tangent_is_normalized(self):
        """Edge tangent is a unit vector (length 1)"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        tangent = backend.get_edge_tangent(edges[0])

        # Calculate length
        length = math.sqrt(sum(t**2 for t in tangent))
        assert abs(length - 1.0) < 1e-10

    def test_edge_tangent_direction(self):
        """Edge tangent points from start to end"""
        backend = MockBackend()
        # Create custom edge with known direction
        edge = MockEdge(start=(0, 0, 0), end=(10, 0, 0))

        tangent = backend.get_edge_tangent(edge)

        # Should point in +X direction
        assert tangent == (1, 0, 0)

    def test_edge_tangent_zero_length_error(self):
        """Zero-length edge raises ValueError"""
        backend = MockBackend()
        # Create edge with same start and end
        edge = MockEdge(start=(5, 5, 5), end=(5, 5, 5))

        with pytest.raises(ValueError, match="zero length"):
            backend.get_edge_tangent(edge)

    def test_edge_tangent_returns_tuple(self):
        """get_edge_tangent returns tuple of 3 floats"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)
        edges = backend.select_edges(box, "|Z")

        tangent = backend.get_edge_tangent(edges[0])

        assert isinstance(tangent, tuple)
        assert len(tangent) == 3
        assert all(isinstance(t, (int, float)) for t in tangent)


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_face_extraction_complete_workflow(self):
        """Complete workflow: select face, get center and normal"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        # Select top face
        faces = backend.select_faces(box, ">Z")
        face = faces[0]

        # Get properties
        center = backend.get_face_center(face)
        normal = backend.get_face_normal(face)

        # Verify
        assert center == (0, 0, 10)
        assert normal == (0, 0, 1)

    def test_edge_extraction_complete_workflow(self):
        """Complete workflow: select edge, get point and tangent"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        # Select vertical edge
        edges = backend.select_edges(box, "|Z")
        edge = edges[0]

        # Get properties
        start = backend.get_edge_point(edge, "start")
        midpoint = backend.get_edge_point(edge, "midpoint")
        end = backend.get_edge_point(edge, "end")
        tangent = backend.get_edge_tangent(edge)

        # Verify relationships
        assert start[2] < end[2]  # Edge goes upward
        assert midpoint[2] == (start[2] + end[2]) / 2  # Midpoint is middle
        assert tangent[2] > 0  # Tangent points upward

    def test_all_faces_workflow(self):
        """Extract properties from all 6 box faces"""
        backend = MockBackend()
        box = backend.create_box(width=10, height=20, depth=5)

        selectors = [">Z", "<Z", ">X", "<X", ">Y", "<Y"]

        for selector in selectors:
            faces = backend.select_faces(box, selector)
            face = faces[0]

            center = backend.get_face_center(face)
            normal = backend.get_face_normal(face)

            # Basic validity checks
            assert isinstance(center, tuple)
            assert isinstance(normal, tuple)
            assert len(center) == 3
            assert len(normal) == 3

            # Normal is unit vector
            length = math.sqrt(sum(n**2 for n in normal))
            assert abs(length - 1.0) < 1e-10
