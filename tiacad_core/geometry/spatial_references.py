"""
Spatial References - Unified geometry reference system for TiaCAD v3.0

This module provides the core spatial reference types that unify position and
orientation information for all geometric references (points, faces, edges, axes).

Key types:
- SpatialRef: Universal reference with position + optional orientation
- Frame: Local coordinate system derived from spatial references

Philosophy: Everything is a SpatialRef. Positions, faces, edges, axes - all
represented uniformly with position and optional orientation data.
"""

from dataclasses import dataclass
from typing import Optional, Literal
import numpy as np
from numpy.typing import NDArray


@dataclass
class SpatialRef:
    """
    Universal spatial reference - the core type for all geometric references.

    Represents a location in 3D space with optional orientation information.
    Can represent points, faces, edges, or axes depending on what orientation
    data is present.

    Attributes:
        position: 3D coordinates (always present)
        orientation: Primary direction vector (normal for faces, direction for axes/edges)
        tangent: Secondary direction vector (for edges, defines local coordinate system)
        ref_type: Type hint for debugging/validation

    Examples:
        # Simple point (no orientation)
        point = SpatialRef(position=np.array([10, 20, 30]), ref_type='point')

        # Face (position + normal)
        face = SpatialRef(
            position=np.array([0, 0, 50]),
            orientation=np.array([0, 0, 1]),  # Normal pointing up
            ref_type='face'
        )

        # Edge (position + tangent + normal)
        edge = SpatialRef(
            position=np.array([10, 0, 0]),
            orientation=np.array([0, 1, 0]),  # Tangent along Y
            tangent=np.array([1, 0, 0]),      # Secondary direction
            ref_type='edge'
        )

        # Axis (origin + direction)
        axis = SpatialRef(
            position=np.array([0, 0, 0]),
            orientation=np.array([0, 0, 1]),  # Z-axis
            ref_type='axis'
        )
    """

    position: NDArray[np.float64]  # (3,) array
    orientation: Optional[NDArray[np.float64]] = None  # (3,) normal/direction vector
    tangent: Optional[NDArray[np.float64]] = None  # (3,) tangent vector (for edges)
    ref_type: Literal['point', 'face', 'edge', 'axis'] = 'point'

    def __post_init__(self):
        """Validate and normalize vector data."""
        # Ensure position is numpy array
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position, dtype=np.float64)

        # Ensure orientation is numpy array and normalized
        if self.orientation is not None:
            if not isinstance(self.orientation, np.ndarray):
                self.orientation = np.array(self.orientation, dtype=np.float64)

            # Normalize orientation vector
            norm = np.linalg.norm(self.orientation)
            if norm > 1e-10:  # Avoid division by zero
                self.orientation = self.orientation / norm

        # Ensure tangent is numpy array and normalized
        if self.tangent is not None:
            if not isinstance(self.tangent, np.ndarray):
                self.tangent = np.array(self.tangent, dtype=np.float64)

            # Normalize tangent vector
            norm = np.linalg.norm(self.tangent)
            if norm > 1e-10:
                self.tangent = self.tangent / norm

        # Validate dimensions
        if self.position.shape != (3,):
            raise ValueError(f"Position must be 3D, got shape {self.position.shape}")
        if self.orientation is not None and self.orientation.shape != (3,):
            raise ValueError(f"Orientation must be 3D, got shape {self.orientation.shape}")
        if self.tangent is not None and self.tangent.shape != (3,):
            raise ValueError(f"Tangent must be 3D, got shape {self.tangent.shape}")

    @property
    def frame(self) -> 'Frame':
        """
        Generate a Frame (local coordinate system) from this reference.

        Returns:
            Frame with origin at this reference's position and axes determined
            by orientation/tangent if present, or world-aligned if not.

        Examples:
            # Point with no orientation → world-aligned frame
            point = SpatialRef(position=[0, 0, 0])
            frame = point.frame  # X=[1,0,0], Y=[0,1,0], Z=[0,0,1]

            # Face with normal → frame aligned to normal
            face = SpatialRef(position=[0,0,10], orientation=[0,0,1], ref_type='face')
            frame = face.frame  # Z-axis aligned to normal
        """
        if self.orientation is None:
            # No orientation - return world-aligned frame at this position
            return Frame(
                origin=self.position,
                x_axis=np.array([1.0, 0.0, 0.0]),
                y_axis=np.array([0.0, 1.0, 0.0]),
                z_axis=np.array([0.0, 0.0, 1.0])
            )

        if self.tangent is None:
            # Have normal, construct arbitrary tangent
            return Frame.from_normal(self.position, self.orientation)

        # Have both orientation and tangent - full frame definition
        return Frame.from_normal_tangent(self.position, self.orientation, self.tangent)

    def offset(self, delta: NDArray[np.float64], in_local_frame: bool = True) -> 'SpatialRef':
        """
        Create a new SpatialRef offset from this one.

        Args:
            delta: Offset vector [dx, dy, dz]
            in_local_frame: If True, interpret delta in this reference's local frame.
                           If False, interpret in world coordinates.

        Returns:
            New SpatialRef at offset position, inheriting orientation if present.

        Examples:
            # World-space offset
            ref = SpatialRef(position=[0,0,0])
            offset_ref = ref.offset([10, 0, 0], in_local_frame=False)
            # offset_ref.position = [10, 0, 0]

            # Local-frame offset (follows reference's orientation)
            face = SpatialRef(position=[0,0,10], orientation=[0,0,1], ref_type='face')
            offset_ref = face.offset([5, 0, 2], in_local_frame=True)
            # 5 units in face's X, 0 in Y, 2 along normal (Z)
        """
        if not isinstance(delta, np.ndarray):
            delta = np.array(delta, dtype=np.float64)

        if in_local_frame and self.orientation is not None:
            # Transform delta from local frame to world coordinates
            frame = self.frame
            world_offset = (
                delta[0] * frame.x_axis +
                delta[1] * frame.y_axis +
                delta[2] * frame.z_axis
            )
        else:
            # Use delta directly as world offset
            world_offset = delta

        return SpatialRef(
            position=self.position + world_offset,
            orientation=self.orientation,  # Inherit orientation
            tangent=self.tangent,          # Inherit tangent
            ref_type=self.ref_type
        )

    def to_tuple(self) -> tuple[float, float, float]:
        """
        Convert position to a simple (x, y, z) tuple.

        Useful for backward compatibility with code expecting position tuples.

        Returns:
            Tuple of (x, y, z) coordinates
        """
        return tuple(self.position.tolist())


@dataclass
class Frame:
    """
    Local coordinate system with origin and three orthonormal axes.

    Frames are typically generated FROM SpatialRef objects, not created directly.
    They provide a complete 3D coordinate system for transformations.

    Attributes:
        origin: Origin point of the frame
        x_axis: X-axis direction (normalized)
        y_axis: Y-axis direction (normalized)
        z_axis: Z-axis direction (normalized)

    Invariants:
        - All axes are unit vectors (normalized)
        - Axes are orthogonal to each other
        - Axes form a right-handed coordinate system
    """

    origin: NDArray[np.float64]    # (3,)
    x_axis: NDArray[np.float64]    # (3,) normalized
    y_axis: NDArray[np.float64]    # (3,) normalized
    z_axis: NDArray[np.float64]    # (3,) normalized

    def __post_init__(self):
        """Validate and normalize axes."""
        # Ensure all are numpy arrays
        if not isinstance(self.origin, np.ndarray):
            self.origin = np.array(self.origin, dtype=np.float64)
        if not isinstance(self.x_axis, np.ndarray):
            self.x_axis = np.array(self.x_axis, dtype=np.float64)
        if not isinstance(self.y_axis, np.ndarray):
            self.y_axis = np.array(self.y_axis, dtype=np.float64)
        if not isinstance(self.z_axis, np.ndarray):
            self.z_axis = np.array(self.z_axis, dtype=np.float64)

        # Normalize all axes
        self.x_axis = self._normalize(self.x_axis)
        self.y_axis = self._normalize(self.y_axis)
        self.z_axis = self._normalize(self.z_axis)

        # Validate dimensions
        if self.origin.shape != (3,):
            raise ValueError(f"Origin must be 3D, got shape {self.origin.shape}")
        if self.x_axis.shape != (3,):
            raise ValueError(f"X-axis must be 3D, got shape {self.x_axis.shape}")
        if self.y_axis.shape != (3,):
            raise ValueError(f"Y-axis must be 3D, got shape {self.y_axis.shape}")
        if self.z_axis.shape != (3,):
            raise ValueError(f"Z-axis must be 3D, got shape {self.z_axis.shape}")

    @staticmethod
    def _normalize(vec: NDArray[np.float64]) -> NDArray[np.float64]:
        """Normalize a vector to unit length."""
        norm = np.linalg.norm(vec)
        if norm < 1e-10:
            raise ValueError(f"Cannot normalize zero vector: {vec}")
        return vec / norm

    @classmethod
    def from_normal(cls, origin: NDArray[np.float64], normal: NDArray[np.float64]) -> 'Frame':
        """
        Construct frame from origin + normal (auto-generate perpendicular axes).

        The normal becomes the Z-axis of the frame. X and Y axes are chosen
        to be perpendicular to the normal and to each other, forming a right-handed
        coordinate system.

        Args:
            origin: Origin point of the frame
            normal: Normal vector (will become Z-axis)

        Returns:
            Frame with Z-axis aligned to normal

        Examples:
            # Face pointing up
            frame = Frame.from_normal([0, 0, 10], [0, 0, 1])
            # frame.z_axis = [0, 0, 1]
            # frame.x_axis and y_axis are perpendicular to Z
        """
        if not isinstance(origin, np.ndarray):
            origin = np.array(origin, dtype=np.float64)
        if not isinstance(normal, np.ndarray):
            normal = np.array(normal, dtype=np.float64)

        # Normalize the normal
        z = cls._normalize(normal)

        # Choose arbitrary perpendicular vector
        # If normal is close to Z-axis, use X-axis as reference
        # Otherwise use Z-axis as reference
        if abs(z[2]) < 0.9:
            # Normal is not close to world Z - cross with world Z
            x = np.cross(z, np.array([0.0, 0.0, 1.0]))
        else:
            # Normal is close to world Z - cross with world X
            x = np.cross(z, np.array([1.0, 0.0, 0.0]))

        x = cls._normalize(x)

        # Y-axis is cross product of Z and X (right-handed system)
        y = np.cross(z, x)
        y = cls._normalize(y)

        return cls(origin=origin, x_axis=x, y_axis=y, z_axis=z)

    @classmethod
    def from_normal_tangent(
        cls,
        origin: NDArray[np.float64],
        normal: NDArray[np.float64],
        tangent: NDArray[np.float64]
    ) -> 'Frame':
        """
        Construct frame from origin + normal + tangent.

        Normal becomes Z-axis, tangent becomes X-axis (after orthogonalization),
        and Y-axis is computed to form a right-handed system.

        Args:
            origin: Origin point of the frame
            normal: Normal vector (will become Z-axis)
            tangent: Tangent vector (will influence X-axis direction)

        Returns:
            Frame with Z aligned to normal and X aligned to tangent

        Examples:
            # Edge with known tangent direction
            frame = Frame.from_normal_tangent(
                origin=[0, 0, 0],
                normal=[0, 0, 1],
                tangent=[1, 0, 0]
            )
        """
        if not isinstance(origin, np.ndarray):
            origin = np.array(origin, dtype=np.float64)
        if not isinstance(normal, np.ndarray):
            normal = np.array(normal, dtype=np.float64)
        if not isinstance(tangent, np.ndarray):
            tangent = np.array(tangent, dtype=np.float64)

        # Normalize inputs
        z = cls._normalize(normal)
        x = cls._normalize(tangent)

        # Ensure X is perpendicular to Z (Gram-Schmidt orthogonalization)
        x = x - np.dot(x, z) * z
        x = cls._normalize(x)

        # Y-axis is cross product (right-handed system)
        y = np.cross(z, x)
        y = cls._normalize(y)

        return cls(origin=origin, x_axis=x, y_axis=y, z_axis=z)

    def to_transform_matrix(self) -> NDArray[np.float64]:
        """
        Convert frame to 4x4 homogeneous transformation matrix.

        The matrix can be used to transform points from world coordinates to
        this frame's local coordinates (or vice versa with inverse).

        Returns:
            4x4 transformation matrix where:
            - First 3 columns are the frame axes
            - Fourth column is the origin
            - Last row is [0, 0, 0, 1]

        Examples:
            frame = Frame.from_normal([10, 20, 30], [0, 0, 1])
            mat = frame.to_transform_matrix()
            # Apply to a point: mat @ [x, y, z, 1]
        """
        mat = np.eye(4, dtype=np.float64)
        mat[:3, 0] = self.x_axis
        mat[:3, 1] = self.y_axis
        mat[:3, 2] = self.z_axis
        mat[:3, 3] = self.origin
        return mat

    def transform_point(self, point: NDArray[np.float64], from_local: bool = True) -> NDArray[np.float64]:
        """
        Transform a point between local and world coordinates.

        Args:
            point: 3D point to transform
            from_local: If True, transform from local to world.
                       If False, transform from world to local.

        Returns:
            Transformed 3D point

        Examples:
            frame = Frame.from_normal([10, 0, 0], [0, 0, 1])

            # Local point [1, 0, 0] in frame coordinates
            world_point = frame.transform_point([1, 0, 0], from_local=True)
            # Result: [11, 0, 0] (1 unit along frame's X-axis from origin)

            # World point to local
            local_point = frame.transform_point([11, 0, 0], from_local=False)
            # Result: [1, 0, 0]
        """
        if not isinstance(point, np.ndarray):
            point = np.array(point, dtype=np.float64)

        if from_local:
            # Transform from local to world
            world_point = (
                self.origin +
                point[0] * self.x_axis +
                point[1] * self.y_axis +
                point[2] * self.z_axis
            )
            return world_point
        else:
            # Transform from world to local
            relative = point - self.origin
            local_point = np.array([
                np.dot(relative, self.x_axis),
                np.dot(relative, self.y_axis),
                np.dot(relative, self.z_axis)
            ])
            return local_point

    def is_orthonormal(self, tolerance: float = 1e-6) -> bool:
        """
        Check if frame axes are orthonormal (perpendicular and unit length).

        Args:
            tolerance: Numerical tolerance for floating point comparison

        Returns:
            True if axes are orthonormal within tolerance

        Examples:
            frame = Frame.from_normal([0, 0, 0], [0, 0, 1])
            assert frame.is_orthonormal()  # Should be True
        """
        # Check unit length
        if abs(np.linalg.norm(self.x_axis) - 1.0) > tolerance:
            return False
        if abs(np.linalg.norm(self.y_axis) - 1.0) > tolerance:
            return False
        if abs(np.linalg.norm(self.z_axis) - 1.0) > tolerance:
            return False

        # Check orthogonality (dot products should be zero)
        if abs(np.dot(self.x_axis, self.y_axis)) > tolerance:
            return False
        if abs(np.dot(self.y_axis, self.z_axis)) > tolerance:
            return False
        if abs(np.dot(self.z_axis, self.x_axis)) > tolerance:
            return False

        return True
