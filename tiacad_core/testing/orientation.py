"""
Orientation Utilities for TiaCAD Testing

Provides utilities for verifying rotation, orientation, and alignment of parts.
Part of the Testing Confidence Plan v3.1 Week 2.

Key functions:
    - get_orientation_angles: Extract roll/pitch/yaw angles from part
    - get_normal_vector: Get normal vector from face reference
    - parts_aligned: Check if parts are aligned along an axis

Philosophy: Enable precise verification of rotation correctness and part
alignment in tests without manual angle calculation.

Author: TIA (v3.1 Week 2)
Version: 1.0 (v3.1)
"""

from typing import Dict, Optional, Literal, Tuple
import numpy as np
from numpy.typing import NDArray

from tiacad_core.part import Part, PartRegistry
from tiacad_core.spatial_resolver import SpatialResolver, SpatialResolverError
from tiacad_core.geometry.spatial_references import SpatialRef


class OrientationError(Exception):
    """Raised when orientation operations fail"""
    pass


def get_orientation_angles(
    part: Part,
    reference: str = "center",
    registry: Optional[PartRegistry] = None
) -> Dict[str, float]:
    """
    Extract orientation angles (roll, pitch, yaw) from a part at a reference.

    Returns Euler angles in degrees describing the part's orientation.
    Uses ZYX Euler angle convention (intrinsic rotations).

    Args:
        part: Part to analyze
        reference: Reference point on part (default: "center")
                  Should typically be a face or axis reference with orientation
        registry: Optional PartRegistry for resolving references.
                 If None, creates temporary registry with the part.

    Returns:
        Dictionary with keys:
            - 'roll': Rotation around X-axis (degrees, -180 to 180)
            - 'pitch': Rotation around Y-axis (degrees, -90 to 90)
            - 'yaw': Rotation around Z-axis (degrees, -180 to 180)
            - 'has_orientation': Boolean indicating if reference has orientation data

    Raises:
        OrientationError: If part is invalid or reference resolution fails

    Examples:
        # Get orientation of a rotated box
        >>> angles = get_orientation_angles(box)
        >>> print(f"Yaw: {angles['yaw']:.1f}°")
        Yaw: 45.0°

        # Check if box is rotated 90 degrees around Z
        >>> angles = get_orientation_angles(rotated_box)
        >>> assert abs(angles['yaw'] - 90.0) < 1.0

        # Get orientation from specific face
        >>> angles = get_orientation_angles(box, reference="face_top")
        >>> # face_top should point up (pitch ~= 90° or normal along +Z)

    Technical Notes:
        - If reference has no orientation (e.g., simple point), returns zeros
          with has_orientation=False
        - Uses reference's orientation vector (normal) to compute frame
        - Euler angles computed from rotation matrix using ZYX convention
        - Gimbal lock may occur at pitch = ±90°
        - Angles are normalized to standard ranges

    See Also:
        get_normal_vector: For raw normal vectors
        parts_aligned: For checking alignment between parts
    """
    # Validate input
    if not isinstance(part, Part):
        raise OrientationError(f"part must be a Part instance, got {type(part)}")

    # Create or use provided registry
    if registry is None:
        registry = PartRegistry()
        if not registry.exists(part.name):
            registry.add(part)

    # Create spatial resolver
    resolver = SpatialResolver(registry, references={})

    # Resolve reference with dot notation
    try:
        ref_spec = f"{part.name}.{reference}" if "." not in reference else reference
        spatial_ref = resolver.resolve(ref_spec)
    except SpatialResolverError as e:
        raise OrientationError(
            f"Failed to resolve reference: {e}\n"
            f"part='{part.name}', reference='{reference}'"
        ) from e

    # Check if reference has orientation
    if spatial_ref.orientation is None:
        return {
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0,
            'has_orientation': False
        }

    # Get frame from spatial reference (includes orientation)
    frame = spatial_ref.frame

    # Extract rotation matrix (3x3 upper-left of transform matrix)
    transform = frame.to_transform_matrix()
    rotation_matrix = transform[:3, :3]

    # Compute Euler angles from rotation matrix (ZYX convention)
    angles = _rotation_matrix_to_euler_angles(rotation_matrix)

    return {
        'roll': float(np.degrees(angles[0])),
        'pitch': float(np.degrees(angles[1])),
        'yaw': float(np.degrees(angles[2])),
        'has_orientation': True
    }


def get_normal_vector(
    part: Part,
    face_ref: str,
    registry: Optional[PartRegistry] = None
) -> NDArray[np.float64]:
    """
    Get the normal vector from a face reference on a part.

    Extracts the outward-pointing normal vector from a specified face.
    Useful for verifying face orientations in tests.

    Args:
        part: Part to analyze
        face_ref: Face reference (e.g., "face_top", "face_bottom")
        registry: Optional PartRegistry for resolving references

    Returns:
        Normalized normal vector as [x, y, z] numpy array

    Raises:
        OrientationError: If reference is invalid or has no orientation

    Examples:
        # Get normal from top face (should point up)
        >>> normal = get_normal_vector(box, "face_top")
        >>> assert np.allclose(normal, [0, 0, 1])

        # Verify face points in expected direction
        >>> normal = get_normal_vector(cylinder, "face_bottom")
        >>> assert normal[2] < 0  # Points down (negative Z)

        # Check perpendicularity between faces
        >>> top_normal = get_normal_vector(box, "face_top")
        >>> front_normal = get_normal_vector(box, "face_front")
        >>> dot_product = np.dot(top_normal, front_normal)
        >>> assert abs(dot_product) < 0.01  # Perpendicular

    Technical Notes:
        - Returned vector is always normalized (unit length)
        - Normal direction follows right-hand rule
        - For face references, orientation is the outward normal
        - Returns the normal from SpatialRef.orientation field

    See Also:
        get_orientation_angles: For full rotation angles
        parts_aligned: For checking alignment
    """
    # Validate input
    if not isinstance(part, Part):
        raise OrientationError(f"part must be a Part instance, got {type(part)}")

    # Create or use provided registry
    if registry is None:
        registry = PartRegistry()
        if not registry.exists(part.name):
            registry.add(part)

    # Create spatial resolver
    resolver = SpatialResolver(registry, references={})

    # Resolve reference
    try:
        ref_spec = f"{part.name}.{face_ref}" if "." not in face_ref else face_ref
        spatial_ref = resolver.resolve(ref_spec)
    except SpatialResolverError as e:
        raise OrientationError(
            f"Failed to resolve face reference: {e}\n"
            f"part='{part.name}', face_ref='{face_ref}'"
        ) from e

    # Check if reference has orientation (normal)
    if spatial_ref.orientation is None:
        raise OrientationError(
            f"Reference '{face_ref}' has no orientation/normal vector.\n"
            f"Use a face reference (e.g., 'face_top') instead of point reference."
        )

    # Return the normalized normal vector
    return spatial_ref.orientation.copy()


def parts_aligned(
    part1: Part,
    part2: Part,
    axis: Literal['x', 'y', 'z'] = 'z',
    ref1: str = "center",
    ref2: str = "center",
    tolerance: float = 0.01,
    registry: Optional[PartRegistry] = None
) -> bool:
    """
    Check if two parts are aligned along a specified axis.

    Verifies that two parts have the same position along two of the three axes
    (i.e., they are aligned when projected onto a plane perpendicular to the
    specified axis).

    Args:
        part1: First part
        part2: Second part
        axis: Axis to check alignment perpendicular to ('x', 'y', or 'z')
              - 'x': Parts aligned in YZ plane (same Y and Z coordinates)
              - 'y': Parts aligned in XZ plane (same X and Z coordinates)
              - 'z': Parts aligned in XY plane (same X and Y coordinates)
        ref1: Reference point on part1 (default: "center")
        ref2: Reference point on part2 (default: "center")
        tolerance: Maximum distance to consider "aligned" (default: 0.01)
        registry: Optional PartRegistry for resolving references

    Returns:
        True if parts are aligned within tolerance

    Raises:
        OrientationError: If parts are invalid or axis is unrecognized

    Examples:
        # Check if boxes are vertically aligned (same X, Y)
        >>> aligned = parts_aligned(box1, box2, axis='z')
        >>> assert aligned  # Both at same XY position

        # Check if parts are aligned along X axis (same Y, Z)
        >>> aligned = parts_aligned(part1, part2, axis='x', tolerance=0.1)

        # Verify stack alignment using face references
        >>> aligned = parts_aligned(
        ...     bottom_box, top_box,
        ...     axis='z',
        ...     ref1="face_top",
        ...     ref2="face_bottom",
        ...     tolerance=0.01
        ... )
        >>> assert aligned  # Stacked vertically with aligned centers

    Technical Notes:
        - Uses reference positions from SpatialResolver
        - Alignment is checked in 2D (two axes perpendicular to specified axis)
        - Tolerance is Euclidean distance in the alignment plane
        - Useful for verifying part placement in assemblies

    See Also:
        measure_distance: From measurements module, for distance checks
        get_orientation_angles: For rotation verification
    """
    # Validate inputs
    if not isinstance(part1, Part):
        raise OrientationError(f"part1 must be a Part instance, got {type(part1)}")
    if not isinstance(part2, Part):
        raise OrientationError(f"part2 must be a Part instance, got {type(part2)}")
    if axis not in ('x', 'y', 'z'):
        raise OrientationError(f"axis must be 'x', 'y', or 'z', got '{axis}'")

    # Create or use provided registry
    if registry is None:
        registry = PartRegistry()
        if not registry.exists(part1.name):
            registry.add(part1)
        if not registry.exists(part2.name):
            registry.add(part2)

    # Create spatial resolver
    resolver = SpatialResolver(registry, references={})

    # Resolve references
    try:
        ref1_spec = f"{part1.name}.{ref1}" if "." not in ref1 else ref1
        ref2_spec = f"{part2.name}.{ref2}" if "." not in ref2 else ref2

        spatial_ref1 = resolver.resolve(ref1_spec)
        spatial_ref2 = resolver.resolve(ref2_spec)
    except SpatialResolverError as e:
        raise OrientationError(
            f"Failed to resolve references: {e}\n"
            f"part1='{part1.name}', ref1='{ref1}'\n"
            f"part2='{part2.name}', ref2='{ref2}'"
        ) from e

    # Get positions
    pos1 = spatial_ref1.position
    pos2 = spatial_ref2.position

    # Check alignment based on axis
    # Alignment means same position in the two perpendicular axes
    if axis == 'x':
        # Aligned in YZ plane (perpendicular to X axis)
        diff = np.array([pos1[1] - pos2[1], pos1[2] - pos2[2]])
    elif axis == 'y':
        # Aligned in XZ plane (perpendicular to Y axis)
        diff = np.array([pos1[0] - pos2[0], pos1[2] - pos2[2]])
    else:  # axis == 'z'
        # Aligned in XY plane (perpendicular to Z axis)
        diff = np.array([pos1[0] - pos2[0], pos1[1] - pos2[1]])

    # Compute distance in alignment plane
    distance = np.linalg.norm(diff)

    return distance <= tolerance


# Internal helper functions

def _rotation_matrix_to_euler_angles(R: NDArray[np.float64]) -> Tuple[float, float, float]:
    """
    Convert a 3x3 rotation matrix to Euler angles (ZYX convention).

    Extracts roll, pitch, yaw from rotation matrix using intrinsic ZYX rotations.
    This is a common convention where:
    - Roll: Rotation around X-axis (applied first)
    - Pitch: Rotation around Y-axis (applied second)
    - Yaw: Rotation around Z-axis (applied third)

    Args:
        R: 3x3 rotation matrix

    Returns:
        Tuple of (roll, pitch, yaw) in radians
        - roll: -π to π
        - pitch: -π/2 to π/2
        - yaw: -π to π

    Technical Notes:
        - Handles gimbal lock at pitch = ±90°
        - Uses atan2 for proper quadrant handling
        - ZYX convention: R = Rz(yaw) * Ry(pitch) * Rx(roll)

    References:
        - https://www.geometrictools.com/Documentation/EulerAngles.pdf
        - Gregory G. Slabaugh, "Computing Euler angles from a rotation matrix"
    """
    # Check for gimbal lock
    sy = np.sqrt(R[0, 0]**2 + R[1, 0]**2)

    singular = sy < 1e-6  # Gimbal lock threshold

    if not singular:
        # Normal case
        roll = np.arctan2(R[2, 1], R[2, 2])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        # Gimbal lock case (pitch ≈ ±90°)
        roll = np.arctan2(-R[1, 2], R[1, 1])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = 0.0  # Arbitrary, set to zero

    return (roll, pitch, yaw)
