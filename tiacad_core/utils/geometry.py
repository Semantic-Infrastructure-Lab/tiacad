"""
Geometry Utility Functions

Shared functions for working with CadQuery geometry.
Eliminates code duplication across Part, TransformTracker, and PointResolver.
"""

from typing import Tuple, Dict, Optional
import logging

from .exceptions import InvalidGeometryError

logger = logging.getLogger(__name__)


def get_center(geometry) -> Tuple[float, float, float]:
    """
    Extract center point from CadQuery geometry.

    Handles both real CadQuery Workplanes and mocks for testing.

    Args:
        geometry: CadQuery Workplane or mock object

    Returns:
        Center point as (x, y, z) tuple

    Raises:
        InvalidGeometryError: If geometry is invalid and has no fallback

    Examples:
        >>> center = get_center(box_geometry)
        >>> x, y, z = center
    """
    # Check for mock geometry (used in testing)
    if hasattr(geometry, 'center_point'):
        return geometry.center_point

    # Real CadQuery geometry
    try:
        bbox = geometry.val().BoundingBox()

        # Try to use bbox.center if available
        if hasattr(bbox, 'center'):
            return (bbox.center.x, bbox.center.y, bbox.center.z)
        else:
            # Calculate center from min/max bounds
            return calculate_center_from_bounds(
                (bbox.xmin, bbox.ymin, bbox.zmin),
                (bbox.xmax, bbox.ymax, bbox.zmax)
            )

    except (AttributeError, RuntimeError, TypeError) as e:
        logger.warning(f"Could not extract center from geometry: {e}, using origin")
        return (0.0, 0.0, 0.0)


def get_bounding_box(geometry) -> Dict[str, Tuple[float, float, float]]:
    """
    Get bounding box of geometry as dictionary.

    Args:
        geometry: CadQuery Workplane

    Returns:
        Dictionary with keys:
        - 'min': (xmin, ymin, zmin)
        - 'max': (xmax, ymax, zmax)
        - 'center': (x, y, z)

    Raises:
        InvalidGeometryError: If geometry has no bounding box

    Examples:
        >>> bbox = get_bounding_box(box_geometry)
        >>> print(bbox['min'])
        (0.0, 0.0, 0.0)
    """
    try:
        bbox = geometry.val().BoundingBox()
        return {
            'min': (bbox.xmin, bbox.ymin, bbox.zmin),
            'max': (bbox.xmax, bbox.ymax, bbox.zmax),
            'center': get_center(geometry),
        }
    except (AttributeError, RuntimeError, TypeError) as e:
        raise InvalidGeometryError(
            f"Cannot extract bounding box from geometry: {e}"
        )


def calculate_center_from_bounds(
    min_point: Tuple[float, float, float],
    max_point: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    """
    Calculate center point from min/max bounds.

    Args:
        min_point: Minimum corner (xmin, ymin, zmin)
        max_point: Maximum corner (xmax, ymax, zmax)

    Returns:
        Center point (x, y, z)

    Examples:
        >>> center = calculate_center_from_bounds((0, 0, 0), (10, 10, 10))
        >>> print(center)
        (5.0, 5.0, 5.0)
    """
    return (
        (min_point[0] + max_point[0]) / 2.0,
        (min_point[1] + max_point[1]) / 2.0,
        (min_point[2] + max_point[2]) / 2.0,
    )
