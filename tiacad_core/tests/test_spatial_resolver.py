"""
Tests for spatial_resolver.py - SpatialResolver class

Tests cover:
- Basic resolution (lists, strings, dicts)
- Named reference resolution
- Part-local auto-generated references
- Face and edge extraction from geometry
- Derived references with offsets (world and local frame)
- Error handling and validation
- Caching behavior
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
from unittest.mock import Mock, MagicMock, patch

from tiacad_core.spatial_resolver import SpatialResolver, SpatialResolverError
from tiacad_core.geometry.spatial_references import SpatialRef
from tiacad_core.part import PartRegistry


class TestBasicResolution:
    """Test basic resolution of different spec types"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.resolver = SpatialResolver(self.registry, references={})

    def test_resolve_absolute_list(self):
        """Test resolving absolute coordinates as list"""
        ref = self.resolver.resolve([10, 20, 30])

        assert isinstance(ref, SpatialRef)
        assert_array_almost_equal(ref.position, [10, 20, 30])
        assert ref.orientation is None
        assert ref.ref_type == 'point'

    def test_resolve_absolute_list_with_floats(self):
        """Test resolving list with float values"""
        ref = self.resolver.resolve([10.5, 20.7, 30.9])

        assert_array_almost_equal(ref.position, [10.5, 20.7, 30.9])

    def test_resolve_list_invalid_length(self):
        """Test that list with wrong number of elements raises error"""
        with pytest.raises(SpatialResolverError, match="exactly 3 values"):
            self.resolver.resolve([10, 20])  # Only 2 values

        with pytest.raises(SpatialResolverError, match="exactly 3 values"):
            self.resolver.resolve([10, 20, 30, 40])  # 4 values

    def test_resolve_list_invalid_values(self):
        """Test that non-numeric list values raise error"""
        with pytest.raises(SpatialResolverError, match="Invalid coordinate values"):
            self.resolver.resolve(["x", "y", "z"])

    def test_resolve_invalid_type(self):
        """Test that invalid spec type raises error"""
        with pytest.raises(SpatialResolverError, match="Invalid reference spec type"):
            self.resolver.resolve(42)  # Not list, string, or dict


class TestNamedReferences:
    """Test resolution of named references"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.references = {
            'origin': [0, 0, 0],
            'corner': [100, 100, 0],
            'top_center': [50, 50, 100]
        }
        self.resolver = SpatialResolver(self.registry, self.references)

    def test_resolve_simple_named_reference(self):
        """Test resolving a simple named reference"""
        ref = self.resolver.resolve('origin')

        assert_array_almost_equal(ref.position, [0, 0, 0])
        assert ref.ref_type == 'point'

    def test_resolve_multiple_named_references(self):
        """Test resolving different named references"""
        ref1 = self.resolver.resolve('origin')
        ref2 = self.resolver.resolve('corner')
        ref3 = self.resolver.resolve('top_center')

        assert_array_almost_equal(ref1.position, [0, 0, 0])
        assert_array_almost_equal(ref2.position, [100, 100, 0])
        assert_array_almost_equal(ref3.position, [50, 50, 100])

    def test_resolve_nonexistent_reference(self):
        """Test that nonexistent reference raises error"""
        with pytest.raises(SpatialResolverError, match="not found"):
            self.resolver.resolve('nonexistent')

    def test_named_reference_caching(self):
        """Test that named references are cached"""
        # First resolution
        ref1 = self.resolver.resolve('origin')
        # Second resolution should use cache
        ref2 = self.resolver.resolve('origin')

        # Should be same object from cache
        assert ref1 is ref2

    def test_clear_cache(self):
        """Test clearing the resolution cache"""
        # Resolve and cache
        ref1 = self.resolver.resolve('origin')
        assert 'origin' in self.resolver._cache

        # Clear cache
        self.resolver.clear_cache()
        assert 'origin' not in self.resolver._cache


class TestInlinePointDefinitions:
    """Test inline point definitions via dict specs"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.resolver = SpatialResolver(self.registry, references={})

    def test_point_with_value(self):
        """Test inline point with absolute value"""
        spec = {'type': 'point', 'value': [10, 20, 30]}
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [10, 20, 30])
        assert ref.ref_type == 'point'

    def test_point_value_invalid(self):
        """Test that invalid point value raises error"""
        with pytest.raises(SpatialResolverError, match="must be list of 3 coordinates"):
            self.resolver.resolve({'type': 'point', 'value': [10, 20]})

    def test_point_missing_required_key(self):
        """Test that point without value or from raises error"""
        with pytest.raises(SpatialResolverError, match="must have either"):
            self.resolver.resolve({'type': 'point'})


class TestDerivedReferencesWithOffset:
    """Test derived references with offsets"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.references = {
            'base': [10, 20, 30]
        }
        self.resolver = SpatialResolver(self.registry, self.references)

    def test_offset_from_point_world_frame(self):
        """Test offset from point (no orientation = world frame)"""
        spec = {
            'type': 'point',
            'from': 'base',
            'offset': [5, 0, 10]
        }
        ref = self.resolver.resolve(spec)

        # Should add offset in world coordinates
        assert_array_almost_equal(ref.position, [15, 20, 40])
        assert ref.ref_type == 'point'

    def test_offset_from_absolute_point(self):
        """Test offset from absolute point list"""
        spec = {
            'type': 'point',
            'from': [0, 0, 0],
            'offset': [10, 20, 30]
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [10, 20, 30])

    def test_offset_from_face_local_frame(self):
        """Test offset from face (has orientation = local frame)"""
        # Create a face reference directly (no part needed)
        face_ref = SpatialRef(
            position=np.array([0, 0, 50]),
            orientation=np.array([0, 0, 1]),  # Normal pointing up
            ref_type='face'
        )
        self.references['top_face'] = face_ref
        # Update resolver to use this reference
        self.resolver = SpatialResolver(self.registry, self.references)

        # Check what the actual frame is
        frame = face_ref.frame
        # For Z-up normal: frame uses cross(Z, X_world) for first axis
        # cross([0,0,1], [1,0,0]) = [0,1,0] (Y-direction)
        # So frame has: X=[0,1,0], Y=[-1,0,0] or [1,0,0], Z=[0,0,1]

        # Offset in local frame: [10, 0, 5]
        # 10*frame.x + 0*frame.y + 5*frame.z
        spec = {
            'type': 'point',
            'from': 'top_face',
            'offset': [10, 0, 5]
        }
        ref = self.resolver.resolve(spec)

        # Calculate expected based on actual frame
        expected = face_ref.position + 10*frame.x_axis + 0*frame.y_axis + 5*frame.z_axis
        assert_array_almost_equal(ref.position, expected)

    def test_offset_from_tilted_face_local_frame(self):
        """Test offset from tilted face (local frame different from world)"""
        # Create a face with normal pointing at 45° in XZ plane
        normal = np.array([1, 0, 1]) / np.sqrt(2)

        self.references['tilted_face'] = SpatialRef(
            position=np.array([0, 0, 0]),
            orientation=normal,
            ref_type='face'
        )
        # Update resolver
        self.resolver = SpatialResolver(self.registry, self.references)

        # Offset [0, 0, 10] in local frame = 10 along normal
        spec = {
            'type': 'point',
            'from': 'tilted_face',
            'offset': [0, 0, 10]
        }
        ref = self.resolver.resolve(spec)

        # Should move 10 units along the normal direction
        expected = 10 * normal
        assert_array_almost_equal(ref.position, expected, decimal=5)

    def test_offset_invalid_format(self):
        """Test that invalid offset format raises error"""
        with pytest.raises(SpatialResolverError, match="Offset must be list of 3 values"):
            self.resolver.resolve({
                'type': 'point',
                'from': 'base',
                'offset': [10, 20]  # Only 2 values
            })

    def test_offset_missing_from(self):
        """Test that offset without 'from' raises error"""
        with pytest.raises(SpatialResolverError, match="must have either"):
            self.resolver.resolve({
                'type': 'point',
                'offset': [10, 20, 30]
            })


class TestPartLocalReferences:
    """Test auto-generated part-local references"""

    def setup_method(self):
        """Setup test fixtures with mock part"""
        self.registry = PartRegistry()

        # Create mock part with geometry
        self.mock_part = Mock()
        self.mock_part.name = 'test_box'

        # Mock geometry with bounding box
        mock_bbox = Mock()
        mock_bbox.xmin, mock_bbox.xmax = 0, 100
        mock_bbox.ymin, mock_bbox.ymax = 0, 60
        mock_bbox.zmin, mock_bbox.zmax = 0, 10

        mock_val = Mock()
        mock_val.BoundingBox.return_value = mock_bbox

        mock_geometry = Mock()
        mock_geometry.val.return_value = mock_val

        self.mock_part.geometry = mock_geometry

        # Register the mock part
        self.registry.add(self.mock_part)
        self.resolver = SpatialResolver(self.registry, references={})

    def test_part_center_reference(self):
        """Test resolving part.center reference"""
        ref = self.resolver.resolve('test_box.center')

        # Center should be at (50, 30, 5)
        assert_array_almost_equal(ref.position, [50, 30, 5])
        assert ref.ref_type == 'point'

    def test_part_origin_reference(self):
        """Test resolving part.origin reference"""
        ref = self.resolver.resolve('test_box.origin')

        # Origin is currently hardcoded to [0, 0, 0]
        assert_array_almost_equal(ref.position, [0, 0, 0])
        assert ref.ref_type == 'point'

    def test_part_axis_references(self):
        """Test resolving part.axis_x, axis_y, axis_z"""
        ref_x = self.resolver.resolve('test_box.axis_x')
        ref_y = self.resolver.resolve('test_box.axis_y')
        ref_z = self.resolver.resolve('test_box.axis_z')

        # All axes should go through part center
        assert_array_almost_equal(ref_x.position, [50, 30, 5])
        assert_array_almost_equal(ref_y.position, [50, 30, 5])
        assert_array_almost_equal(ref_z.position, [50, 30, 5])

        # Check orientations
        assert_array_almost_equal(ref_x.orientation, [1, 0, 0])
        assert_array_almost_equal(ref_y.orientation, [0, 1, 0])
        assert_array_almost_equal(ref_z.orientation, [0, 0, 1])

        # Type should be axis
        assert ref_x.ref_type == 'axis'
        assert ref_y.ref_type == 'axis'
        assert ref_z.ref_type == 'axis'

    def test_nonexistent_part(self):
        """Test that referencing nonexistent part raises error"""
        with pytest.raises(SpatialResolverError, match="not found in registry"):
            self.resolver.resolve('nonexistent_part.center')

    def test_invalid_part_local_reference(self):
        """Test that invalid part-local reference raises error"""
        with pytest.raises(SpatialResolverError, match="Unknown part-local reference"):
            self.resolver.resolve('test_box.invalid_ref')


class TestFaceExtraction:
    """Test face reference extraction from geometry"""

    def setup_method(self):
        """Setup test fixtures with mock part"""
        self.registry = PartRegistry()

        # Create mock part
        self.mock_part = Mock()
        self.mock_part.name = 'test_box'

        # Create mock face with proper attributes
        self.mock_face = Mock()
        self.mock_face.center = (50, 30, 10)
        self.mock_face.normal = (0, 0, 1)

        # Create mock backend that returns our mock face
        self.mock_backend = Mock()
        self.mock_backend.select_faces.return_value = [self.mock_face]
        self.mock_backend.get_face_center.return_value = (50, 30, 10)
        self.mock_backend.get_face_normal.return_value = (0, 0, 1)
        self.mock_backend.get_bounding_box.return_value = {
            'min': (0, 0, 0),
            'max': (100, 60, 20),
            'center': (50, 30, 10)
        }

        # Mock geometry (not directly used anymore, but needed for Part)
        mock_geometry = Mock()

        self.mock_part.geometry = mock_geometry
        self.mock_part.backend = self.mock_backend

        # Register part
        self.registry.add(self.mock_part)
        self.resolver = SpatialResolver(self.registry, references={})

    def test_face_reference_extraction(self):
        """Test extracting face reference from geometry"""
        spec = {
            'type': 'face',
            'part': 'test_box',
            'selector': '>Z',
            'at': 'center'
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [50, 30, 10])
        assert_array_almost_equal(ref.orientation, [0, 0, 1])
        assert ref.ref_type == 'face'

    def test_face_auto_generated(self):
        """Test auto-generated face references like part.face_top"""
        # Mock will be called with '>Z' selector for face_top
        ref = self.resolver.resolve('test_box.face_top')

        assert ref.ref_type == 'face'
        assert ref.orientation is not None

    def test_face_selector_no_match(self):
        """Test that selector matching no faces raises error"""
        # Make backend return empty list to simulate no match
        self.mock_backend.select_faces.return_value = []

        with pytest.raises(SpatialResolverError, match="matched no faces"):
            self.resolver.resolve({
                'type': 'face',
                'part': 'test_box',
                'selector': '>X+Y+Z'  # Invalid selector
            })

    def test_face_missing_part(self):
        """Test that face reference without part raises error"""
        with pytest.raises(SpatialResolverError, match="must have 'part' and 'selector'"):
            self.resolver.resolve({
                'type': 'face',
                'selector': '>Z'
            })


class TestEdgeExtraction:
    """Test edge reference extraction from geometry"""

    def setup_method(self):
        """Setup test fixtures with mock part"""
        self.registry = PartRegistry()

        # Create mock part
        self.mock_part = Mock()
        self.mock_part.name = 'test_box'

        # Create mock edge
        self.mock_edge = Mock()
        self.mock_edge.start = (0, 0, 0)
        self.mock_edge.end = (100, 0, 0)

        # Create mock backend that returns our mock edge
        self.mock_backend = Mock()
        self.mock_backend.select_edges.return_value = [self.mock_edge]
        self.mock_backend.get_edge_point.side_effect = lambda edge, location: {
            'start': (0, 0, 0),
            'end': (100, 0, 0),
            'midpoint': (50, 0, 0)
        }[location]
        self.mock_backend.get_edge_tangent.return_value = (1, 0, 0)  # Along X axis
        self.mock_backend.get_bounding_box.return_value = {
            'min': (0, 0, 0),
            'max': (100, 60, 20),
            'center': (50, 30, 10)
        }

        # Mock geometry (not directly used anymore, but needed for Part)
        mock_geometry = Mock()

        self.mock_part.geometry = mock_geometry
        self.mock_part.backend = self.mock_backend

        # Register part
        self.registry.add(self.mock_part)
        self.resolver = SpatialResolver(self.registry, references={})

    def test_edge_reference_midpoint(self):
        """Test extracting edge reference at midpoint"""
        spec = {
            'type': 'edge',
            'part': 'test_box',
            'selector': '|Z',
            'at': 'midpoint'
        }
        ref = self.resolver.resolve(spec)

        # Midpoint should be (50, 0, 0)
        assert_array_almost_equal(ref.position, [50, 0, 0])
        # Tangent should be along X
        assert_array_almost_equal(ref.orientation, [1, 0, 0])
        assert ref.ref_type == 'edge'

    def test_edge_reference_start(self):
        """Test extracting edge reference at start"""
        spec = {
            'type': 'edge',
            'part': 'test_box',
            'selector': '|Z',
            'at': 'start'
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [0, 0, 0])
        assert ref.ref_type == 'edge'

    def test_edge_reference_end(self):
        """Test extracting edge reference at end"""
        spec = {
            'type': 'edge',
            'part': 'test_box',
            'selector': '|Z',
            'at': 'end'
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [100, 0, 0])
        assert ref.ref_type == 'edge'

    def test_edge_selector_no_match(self):
        """Test that selector matching no edges raises error"""
        # Make backend return empty list to simulate no match
        self.mock_backend.select_edges.return_value = []

        with pytest.raises(SpatialResolverError, match="matched no edges"):
            self.resolver.resolve({
                'type': 'edge',
                'part': 'test_box',
                'selector': 'invalid'
            })

    def test_edge_invalid_location(self):
        """Test that invalid edge location raises error"""
        # Make backend raise ValueError for invalid location
        self.mock_backend.get_edge_point.side_effect = ValueError("Invalid location 'invalid'")

        with pytest.raises(SpatialResolverError, match="Invalid location"):
            self.resolver.resolve({
                'type': 'edge',
                'part': 'test_box',
                'selector': '|Z',
                'at': 'invalid'
            })


class TestAxisReferences:
    """Test axis reference definitions"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.resolver = SpatialResolver(self.registry, references={})

    def test_axis_from_two_points(self):
        """Test creating axis from two points"""
        spec = {
            'type': 'axis',
            'from': [0, 0, 0],
            'to': [0, 0, 100]
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [0, 0, 0])
        assert_array_almost_equal(ref.orientation, [0, 0, 1])  # Normalized direction
        assert ref.ref_type == 'axis'

    def test_axis_from_references(self):
        """Test creating axis from named references"""
        self.references = {
            'point1': [10, 20, 30],
            'point2': [40, 20, 30]
        }
        self.resolver = SpatialResolver(self.registry, self.references)

        spec = {
            'type': 'axis',
            'from': 'point1',
            'to': 'point2'
        }
        ref = self.resolver.resolve(spec)

        assert_array_almost_equal(ref.position, [10, 20, 30])
        # Direction should be along X
        assert_array_almost_equal(ref.orientation, [1, 0, 0])

    def test_axis_direction_normalized(self):
        """Test that axis direction is normalized"""
        spec = {
            'type': 'axis',
            'from': [0, 0, 0],
            'to': [3, 0, 4]  # Length = 5
        }
        ref = self.resolver.resolve(spec)

        # Direction should be normalized
        assert_array_almost_equal(ref.orientation, [0.6, 0, 0.8])
        assert_array_almost_equal(np.linalg.norm(ref.orientation), 1.0)

    def test_axis_identical_points_error(self):
        """Test that axis with identical points raises error"""
        with pytest.raises(SpatialResolverError, match="identical"):
            self.resolver.resolve({
                'type': 'axis',
                'from': [10, 20, 30],
                'to': [10, 20, 30]
            })


class TestErrorHandling:
    """Test error handling and validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.resolver = SpatialResolver(self.registry, references={})

    def test_unknown_reference_type(self):
        """Test that unknown reference type raises error"""
        with pytest.raises(SpatialResolverError, match="Unknown reference type"):
            self.resolver.resolve({
                'type': 'invalid_type',
                'part': 'test'
            })

    def test_part_not_found(self):
        """Test that referencing nonexistent part raises error"""
        with pytest.raises(SpatialResolverError, match="not found in registry"):
            self.resolver.resolve({
                'type': 'face',
                'part': 'nonexistent',
                'selector': '>Z'
            })

    def test_face_missing_required_keys(self):
        """Test that face without required keys raises error"""
        with pytest.raises(SpatialResolverError, match="must have 'part' and 'selector'"):
            self.resolver.resolve({'type': 'face', 'part': 'test'})

    def test_edge_missing_required_keys(self):
        """Test that edge without required keys raises error"""
        with pytest.raises(SpatialResolverError, match="must have 'part' and 'selector'"):
            self.resolver.resolve({'type': 'edge', 'selector': '|Z'})


class TestIntegration:
    """Integration tests with multiple references and chaining"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = PartRegistry()
        self.references = {
            'origin': [0, 0, 0],
            'offset1': {
                'type': 'point',
                'from': 'origin',
                'offset': [10, 0, 0]
            },
            'offset2': {
                'type': 'point',
                'from': 'offset1',
                'offset': [0, 10, 0]
            }
        }
        self.resolver = SpatialResolver(self.registry, self.references)

    def test_chained_offsets(self):
        """Test resolving chained offset references"""
        ref = self.resolver.resolve('offset2')

        # Should be [0,0,0] + [10,0,0] + [0,10,0] = [10,10,0]
        assert_array_almost_equal(ref.position, [10, 10, 0])

    def test_recursive_named_resolution(self):
        """Test that named references resolve recursively"""
        ref1 = self.resolver.resolve('offset1')
        assert_array_almost_equal(ref1.position, [10, 0, 0])

        ref2 = self.resolver.resolve('offset2')
        assert_array_almost_equal(ref2.position, [10, 10, 0])
