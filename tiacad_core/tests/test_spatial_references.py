"""
Tests for spatial_references.py - SpatialRef and Frame classes

Tests cover:
- SpatialRef creation and validation
- Frame creation and transformation
- Local/world coordinate transformations
- Auto-generated frames from spatial references
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from tiacad_core.geometry.spatial_references import SpatialRef, Frame


class TestSpatialRefCreation:
    """Test SpatialRef creation and validation"""

    def test_simple_point_creation(self):
        """Test creating a simple point with no orientation"""
        ref = SpatialRef(position=np.array([10.0, 20.0, 30.0]), ref_type='point')

        assert_array_almost_equal(ref.position, [10, 20, 30])
        assert ref.orientation is None
        assert ref.tangent is None
        assert ref.ref_type == 'point'

    def test_point_from_list(self):
        """Test that position can be created from Python list"""
        ref = SpatialRef(position=[10, 20, 30])

        assert isinstance(ref.position, np.ndarray)
        assert_array_almost_equal(ref.position, [10, 20, 30])

    def test_face_with_normal(self):
        """Test creating a face reference with normal"""
        ref = SpatialRef(
            position=[0, 0, 50],
            orientation=[0, 0, 1],
            ref_type='face'
        )

        assert_array_almost_equal(ref.position, [0, 0, 50])
        assert_array_almost_equal(ref.orientation, [0, 0, 1])
        assert ref.ref_type == 'face'

    def test_orientation_normalization(self):
        """Test that orientation vector is automatically normalized"""
        ref = SpatialRef(
            position=[0, 0, 0],
            orientation=[3, 0, 4],  # Length = 5
            ref_type='face'
        )

        # Should be normalized to unit length
        assert_array_almost_equal(ref.orientation, [0.6, 0, 0.8])
        assert_array_almost_equal(np.linalg.norm(ref.orientation), 1.0)

    def test_edge_with_tangent(self):
        """Test creating an edge reference with tangent"""
        ref = SpatialRef(
            position=[10, 0, 0],
            orientation=[0, 1, 0],  # Primary direction
            tangent=[1, 0, 0],      # Secondary direction
            ref_type='edge'
        )

        assert_array_almost_equal(ref.position, [10, 0, 0])
        assert_array_almost_equal(ref.orientation, [0, 1, 0])
        assert_array_almost_equal(ref.tangent, [1, 0, 0])

    def test_axis_reference(self):
        """Test creating an axis reference"""
        ref = SpatialRef(
            position=[0, 0, 0],
            orientation=[0, 0, 1],
            ref_type='axis'
        )

        assert ref.ref_type == 'axis'
        assert_array_almost_equal(ref.orientation, [0, 0, 1])

    def test_invalid_position_dimension(self):
        """Test that non-3D position raises error"""
        with pytest.raises(ValueError, match="Position must be 3D"):
            SpatialRef(position=np.array([1, 2]))  # Only 2D

    def test_invalid_orientation_dimension(self):
        """Test that non-3D orientation raises error"""
        with pytest.raises(ValueError, match="Orientation must be 3D"):
            SpatialRef(
                position=[0, 0, 0],
                orientation=np.array([1, 2])  # Only 2D
            )


class TestSpatialRefMethods:
    """Test SpatialRef instance methods"""

    def test_to_tuple(self):
        """Test converting position to tuple"""
        ref = SpatialRef(position=[10, 20, 30])
        result = ref.to_tuple()

        assert result == (10.0, 20.0, 30.0)
        assert isinstance(result, tuple)

    def test_offset_in_world_frame(self):
        """Test offsetting reference in world coordinates"""
        ref = SpatialRef(position=[10, 20, 30])
        offset_ref = ref.offset([5, 0, -10], in_local_frame=False)

        assert_array_almost_equal(offset_ref.position, [15, 20, 20])
        assert offset_ref.orientation is None  # Inherited

    def test_offset_in_local_frame_no_orientation(self):
        """Test that offset without orientation uses world coords"""
        ref = SpatialRef(position=[10, 20, 30])
        offset_ref = ref.offset([5, 0, 0], in_local_frame=True)

        # No orientation, so should still be world offset
        assert_array_almost_equal(offset_ref.position, [15, 20, 30])

    def test_offset_in_local_frame_with_orientation(self):
        """Test offsetting in reference's local frame"""
        # Face pointing in +Z direction
        ref = SpatialRef(
            position=[0, 0, 10],
            orientation=[0, 0, 1],
            ref_type='face'
        )

        # Offset 5 units in face's Z (normal) direction
        offset_ref = ref.offset([0, 0, 5], in_local_frame=True)

        # Should move along normal
        assert_array_almost_equal(offset_ref.position, [0, 0, 15])

    def test_offset_preserves_orientation(self):
        """Test that offset preserves orientation"""
        ref = SpatialRef(
            position=[0, 0, 0],
            orientation=[1, 0, 0],
            ref_type='face'
        )

        offset_ref = ref.offset([0, 10, 0], in_local_frame=False)

        assert_array_almost_equal(offset_ref.orientation, [1, 0, 0])
        assert offset_ref.ref_type == 'face'


class TestSpatialRefFrame:
    """Test frame generation from SpatialRef"""

    def test_point_generates_world_aligned_frame(self):
        """Test that point with no orientation gives world-aligned frame"""
        ref = SpatialRef(position=[10, 20, 30])
        frame = ref.frame

        assert_array_almost_equal(frame.origin, [10, 20, 30])
        assert_array_almost_equal(frame.x_axis, [1, 0, 0])
        assert_array_almost_equal(frame.y_axis, [0, 1, 0])
        assert_array_almost_equal(frame.z_axis, [0, 0, 1])

    def test_face_generates_aligned_frame(self):
        """Test that face normal becomes frame's Z-axis"""
        ref = SpatialRef(
            position=[0, 0, 10],
            orientation=[0, 0, 1],
            ref_type='face'
        )
        frame = ref.frame

        assert_array_almost_equal(frame.origin, [0, 0, 10])
        assert_array_almost_equal(frame.z_axis, [0, 0, 1])
        # X and Y should be perpendicular to Z
        assert abs(np.dot(frame.x_axis, frame.z_axis)) < 1e-10
        assert abs(np.dot(frame.y_axis, frame.z_axis)) < 1e-10


class TestFrameCreation:
    """Test Frame creation methods"""

    def test_direct_frame_creation(self):
        """Test creating frame directly"""
        frame = Frame(
            origin=[0, 0, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )

        assert_array_almost_equal(frame.origin, [0, 0, 0])
        assert_array_almost_equal(frame.x_axis, [1, 0, 0])
        assert frame.is_orthonormal()

    def test_frame_from_normal_z_up(self):
        """Test creating frame from normal pointing up"""
        frame = Frame.from_normal(
            origin=[10, 20, 30],
            normal=[0, 0, 1]
        )

        assert_array_almost_equal(frame.origin, [10, 20, 30])
        assert_array_almost_equal(frame.z_axis, [0, 0, 1])
        assert frame.is_orthonormal()

    def test_frame_from_normal_x_aligned(self):
        """Test creating frame from normal pointing in X"""
        frame = Frame.from_normal(
            origin=[0, 0, 0],
            normal=[1, 0, 0]
        )

        assert_array_almost_equal(frame.z_axis, [1, 0, 0])
        assert frame.is_orthonormal()

    def test_frame_from_normal_arbitrary(self):
        """Test creating frame from arbitrary normal"""
        frame = Frame.from_normal(
            origin=[0, 0, 0],
            normal=[1, 1, 1]
        )

        # Normal should be normalized
        expected_z = np.array([1, 1, 1]) / np.sqrt(3)
        assert_array_almost_equal(frame.z_axis, expected_z)
        assert frame.is_orthonormal()

    def test_frame_from_normal_tangent(self):
        """Test creating frame with both normal and tangent"""
        frame = Frame.from_normal_tangent(
            origin=[0, 0, 0],
            normal=[0, 0, 1],
            tangent=[1, 0, 0]
        )

        assert_array_almost_equal(frame.origin, [0, 0, 0])
        assert_array_almost_equal(frame.z_axis, [0, 0, 1])
        assert_array_almost_equal(frame.x_axis, [1, 0, 0])
        assert_array_almost_equal(frame.y_axis, [0, 1, 0])

    def test_frame_normalization(self):
        """Test that frame axes are automatically normalized"""
        frame = Frame(
            origin=[0, 0, 0],
            x_axis=[2, 0, 0],  # Not normalized
            y_axis=[0, 3, 0],
            z_axis=[0, 0, 4]
        )

        # All axes should be normalized
        assert_array_almost_equal(np.linalg.norm(frame.x_axis), 1.0)
        assert_array_almost_equal(np.linalg.norm(frame.y_axis), 1.0)
        assert_array_almost_equal(np.linalg.norm(frame.z_axis), 1.0)

    def test_frame_zero_vector_raises_error(self):
        """Test that zero vector raises error"""
        with pytest.raises(ValueError, match="Cannot normalize zero vector"):
            Frame(
                origin=[0, 0, 0],
                x_axis=[0, 0, 0],  # Zero vector
                y_axis=[0, 1, 0],
                z_axis=[0, 0, 1]
            )


class TestFrameTransformations:
    """Test Frame transformation methods"""

    def test_to_transform_matrix_identity(self):
        """Test transformation matrix for world-aligned frame"""
        frame = Frame(
            origin=[0, 0, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )

        mat = frame.to_transform_matrix()

        # Should be 4x4 identity matrix
        assert mat.shape == (4, 4)
        assert_array_almost_equal(mat, np.eye(4))

    def test_to_transform_matrix_translated(self):
        """Test transformation matrix for translated frame"""
        frame = Frame(
            origin=[10, 20, 30],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )

        mat = frame.to_transform_matrix()

        # Translation part should be [10, 20, 30]
        assert_array_almost_equal(mat[:3, 3], [10, 20, 30])

    def test_transform_point_local_to_world(self):
        """Test transforming point from local to world coordinates"""
        frame = Frame(
            origin=[10, 0, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )

        # Point at [1, 0, 0] in local frame
        local_point = [1, 0, 0]
        world_point = frame.transform_point(local_point, from_local=True)

        # Should be at [11, 0, 0] in world (origin + 1*x_axis)
        assert_array_almost_equal(world_point, [11, 0, 0])

    def test_transform_point_world_to_local(self):
        """Test transforming point from world to local coordinates"""
        frame = Frame(
            origin=[10, 0, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )

        # Point at [11, 0, 0] in world
        world_point = [11, 0, 0]
        local_point = frame.transform_point(world_point, from_local=False)

        # Should be at [1, 0, 0] in local frame
        assert_array_almost_equal(local_point, [1, 0, 0])

    def test_transform_point_roundtrip(self):
        """Test that local→world→local gives original point"""
        frame = Frame.from_normal([10, 20, 30], [0, 0, 1])

        original = np.array([5, 3, -2])
        world = frame.transform_point(original, from_local=True)
        back_to_local = frame.transform_point(world, from_local=False)

        assert_array_almost_equal(back_to_local, original)

    def test_transform_point_rotated_frame(self):
        """Test transformation with rotated frame"""
        # Frame rotated 90° around Z
        frame = Frame(
            origin=[0, 0, 0],
            x_axis=[0, 1, 0],  # X points in world Y
            y_axis=[-1, 0, 0], # Y points in world -X
            z_axis=[0, 0, 1]
        )

        # Point [1, 0, 0] in local frame
        local_point = [1, 0, 0]
        world_point = frame.transform_point(local_point, from_local=True)

        # Should be at [0, 1, 0] in world
        assert_array_almost_equal(world_point, [0, 1, 0])


class TestFrameValidation:
    """Test Frame validation methods"""

    def test_is_orthonormal_valid_frame(self):
        """Test that properly constructed frame is orthonormal"""
        frame = Frame.from_normal([0, 0, 0], [1, 1, 1])
        assert frame.is_orthonormal()

    def test_is_orthonormal_world_frame(self):
        """Test that world-aligned frame is orthonormal"""
        frame = Frame(
            origin=[0, 0, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
            z_axis=[0, 0, 1]
        )
        assert frame.is_orthonormal()

    def test_frame_right_handed(self):
        """Test that frame forms right-handed coordinate system"""
        frame = Frame.from_normal([0, 0, 0], [0, 0, 1])

        # Cross product of X and Y should give Z
        cross = np.cross(frame.x_axis, frame.y_axis)
        assert_array_almost_equal(cross, frame.z_axis)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_length_orientation_normalization(self):
        """Test that zero-length orientation doesn't crash"""
        # This should work - zero vector won't be normalized but post_init
        # will handle gracefully
        ref = SpatialRef(
            position=[0, 0, 0],
            orientation=[0, 0, 0],
            ref_type='point'
        )
        # Orientation should remain zero (not normalized)
        assert_array_almost_equal(ref.orientation, [0, 0, 0])

    def test_very_small_position_values(self):
        """Test handling of very small position values"""
        ref = SpatialRef(position=[1e-10, 1e-10, 1e-10])
        assert_array_almost_equal(ref.position, [1e-10, 1e-10, 1e-10])

    def test_large_position_values(self):
        """Test handling of large position values"""
        ref = SpatialRef(position=[1e6, 1e6, 1e6])
        assert_array_almost_equal(ref.position, [1e6, 1e6, 1e6])
