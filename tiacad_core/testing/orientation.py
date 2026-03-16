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


class OrientationError(Exception):
    """Raised when orientation operations fail"""
    pass


# Perpendicular axis indices for alignment checks: axis → (i, j) of the two
# axes that must match (e.g. 'z' → compare X=0 and Y=1 coordinates).
_PERP_AXES: Dict[str, Tuple[int, int]] = {'x': (1, 2), 'y': (0, 2), 'z': (0, 1)}


def _make_resolver(registry: Optional[PartRegistry], *parts: Part) -> SpatialResolver:
    """Create a SpatialResolver, building a temporary PartRegistry if needed."""
    if registry is None:
        registry = PartRegistry()
        for part in parts:
            if not registry.exists(part.name):
                registry.add(part)
    return SpatialResolver(registry, references={})


def _resolve_part_ref(resolver: SpatialResolver, part_name: str, ref: str, context: str):
    """Resolve a part reference, converting SpatialResolverError → OrientationError."""
    ref_spec = f"{part_name}.{ref}" if "." not in ref else ref
    try:
        return resolver.resolve(ref_spec)
    except SpatialResolverError as e:
        raise OrientationError(f"Failed to resolve reference: {e}\n{context}") from e


def get_orientation_angles(
    part: Part,
    reference: str = "center",
    registry: Optional[PartRegistry] = None
) -> Dict[str, float]:
    """
    Extract orientation angles (roll, pitch, yaw) from a part at a reference.

    Returns Euler angles in degrees using ZYX convention (intrinsic rotations).
    If the reference has no orientation data, returns zeros with has_orientation=False.

    Args:
        part: Part to analyze
        reference: Reference point on part (default: "center")
        registry: Optional PartRegistry; if None, a temporary one is created.

    Returns:
        Dict with 'roll', 'pitch', 'yaw' (degrees) and 'has_orientation' (bool).

    Raises:
        OrientationError: If part is invalid or reference resolution fails
    """
    if not isinstance(part, Part):
        raise OrientationError(f"part must be a Part instance, got {type(part)}")

    resolver = _make_resolver(registry, part)
    spatial_ref = _resolve_part_ref(
        resolver, part.name, reference,
        f"part='{part.name}', reference='{reference}'"
    )

    if spatial_ref.orientation is None:
        return {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'has_orientation': False}

    rotation_matrix = spatial_ref.frame.to_transform_matrix()[:3, :3]
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
    Get the outward-pointing normal vector from a face reference on a part.

    Args:
        part: Part to analyze
        face_ref: Face reference (e.g., "face_top", "face_bottom")
        registry: Optional PartRegistry; if None, a temporary one is created.

    Returns:
        Normalized normal vector as [x, y, z] numpy array

    Raises:
        OrientationError: If reference is invalid or has no orientation
    """
    if not isinstance(part, Part):
        raise OrientationError(f"part must be a Part instance, got {type(part)}")

    resolver = _make_resolver(registry, part)
    spatial_ref = _resolve_part_ref(
        resolver, part.name, face_ref,
        f"part='{part.name}', face_ref='{face_ref}'"
    )

    if spatial_ref.orientation is None:
        raise OrientationError(
            f"Reference '{face_ref}' has no orientation/normal vector.\n"
            f"Use a face reference (e.g., 'face_top') instead of point reference."
        )

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

    "Aligned" means both parts share the same coordinates on the two axes
    perpendicular to the given axis (e.g. axis='z' → same X and Y).

    Args:
        part1: First part
        part2: Second part
        axis: Axis to check alignment perpendicular to ('x', 'y', or 'z')
        ref1: Reference point on part1 (default: "center")
        ref2: Reference point on part2 (default: "center")
        tolerance: Maximum Euclidean distance in alignment plane (default: 0.01)
        registry: Optional PartRegistry; if None, a temporary one is created.

    Returns:
        True if parts are aligned within tolerance

    Raises:
        OrientationError: If parts are invalid or axis is unrecognized
    """
    if not isinstance(part1, Part):
        raise OrientationError(f"part1 must be a Part instance, got {type(part1)}")
    if not isinstance(part2, Part):
        raise OrientationError(f"part2 must be a Part instance, got {type(part2)}")
    if axis not in _PERP_AXES:
        raise OrientationError(f"axis must be 'x', 'y', or 'z', got '{axis}'")

    resolver = _make_resolver(registry, part1, part2)
    spatial_ref1 = _resolve_part_ref(
        resolver, part1.name, ref1,
        f"part1='{part1.name}', ref1='{ref1}'\npart2='{part2.name}', ref2='{ref2}'"
    )
    spatial_ref2 = _resolve_part_ref(
        resolver, part2.name, ref2,
        f"part1='{part1.name}', ref1='{ref1}'\npart2='{part2.name}', ref2='{ref2}'"
    )

    pos1, pos2 = spatial_ref1.position, spatial_ref2.position
    i, j = _PERP_AXES[axis]
    diff = np.array([pos1[i] - pos2[i], pos1[j] - pos2[j]])

    return float(np.linalg.norm(diff)) <= tolerance


# Internal helper functions

def _rotation_matrix_to_euler_angles(R: NDArray[np.float64]) -> Tuple[float, float, float]:
    """
    Convert a 3x3 rotation matrix to Euler angles (ZYX convention).

    Args:
        R: 3x3 rotation matrix

    Returns:
        Tuple of (roll, pitch, yaw) in radians
    """
    sy = np.sqrt(R[0, 0]**2 + R[1, 0]**2)
    singular = sy < 1e-6  # Gimbal lock threshold

    if not singular:
        roll = np.arctan2(R[2, 1], R[2, 2])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        # Gimbal lock case (pitch ≈ ±90°)
        roll = np.arctan2(-R[1, 2], R[1, 1])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = 0.0

    return (roll, pitch, yaw)
