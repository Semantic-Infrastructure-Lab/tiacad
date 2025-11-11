"""
Dimensional Accuracy Utilities for TiaCAD Testing

Provides utilities for verifying dimensions, volumes, and surface areas of parts.
Part of the Testing Confidence Plan v3.1 Week 3.

Key functions:
    - get_dimensions: Extract dimensional measurements from part
    - get_volume: Calculate part volume
    - get_surface_area: Calculate part surface area

Philosophy: Enable precise verification of dimensional accuracy in tests
without manual calculation.

Author: TIA (v3.1 Week 3)
Version: 1.0 (v3.1)
"""

from typing import Dict, Optional
import math

from tiacad_core.part import Part


class DimensionError(Exception):
    """Raised when dimension operations fail"""
    pass


def get_dimensions(part: Part) -> Dict[str, float]:
    """
    Extract dimensional measurements from a part.

    Returns bounding box dimensions plus additional measurements where applicable.
    For primitives, attempts to extract native dimensions (radius, height, etc.).

    Args:
        part: Part to measure

    Returns:
        Dictionary with keys (depending on part type):
            - 'width': X-axis extent (always present)
            - 'height': Y-axis extent (always present)
            - 'depth': Z-axis extent (always present)
            - 'volume': Part volume (always present)
            - 'surface_area': Part surface area (always present)

    Raises:
        DimensionError: If dimensions cannot be extracted

    Examples:
        # Get dimensions of a box
        >>> dims = get_dimensions(box_part)
        >>> assert abs(dims['width'] - 50.0) < 0.01
        >>> assert abs(dims['height'] - 30.0) < 0.01
        >>> assert abs(dims['depth'] - 20.0) < 0.01

        # Get cylinder dimensions
        >>> dims = get_dimensions(cylinder_part)
        >>> # Cylinder bounding box is 2*radius in X and Y
        >>> assert abs(dims['width'] - 20.0) < 0.01  # radius=10

        # Verify dimensions
        >>> dims = get_dimensions(part)
        >>> expected_volume = 50 * 30 * 20  # For box
        >>> assert abs(dims['volume'] - expected_volume) < 0.01

    Technical Notes:
        - Uses Part.get_bounds() for bounding box
        - Uses get_volume() and get_surface_area() for measurements
        - Bounding box is axis-aligned (not oriented bounding box)
        - For rotated parts, bbox may be larger than actual part extent

    See Also:
        get_volume: For volume calculation
        get_surface_area: For surface area calculation
    """
    # Validate input
    if not isinstance(part, Part):
        raise DimensionError(f"part must be a Part instance, got {type(part)}")

    try:
        # Get bounding box
        bounds = part.get_bounds()
        min_corner = bounds['min']
        max_corner = bounds['max']

        # Calculate dimensions
        dimensions = {
            'width': max_corner[0] - min_corner[0],   # X extent
            'height': max_corner[1] - min_corner[1],  # Y extent
            'depth': max_corner[2] - min_corner[2],   # Z extent
        }

        # Add volume and surface area
        dimensions['volume'] = get_volume(part)
        dimensions['surface_area'] = get_surface_area(part)

        return dimensions

    except Exception as e:
        raise DimensionError(
            f"Failed to extract dimensions for part '{part.name}': {e}"
        ) from e


def get_volume(part: Part) -> float:
    """
    Calculate the volume of a part.

    Uses the CAD kernel (CadQuery) to compute the exact volume.
    Accuracy depends on the kernel's implementation.

    Args:
        part: Part to measure

    Returns:
        Volume in cubic units

    Raises:
        DimensionError: If volume cannot be calculated

    Examples:
        # Get box volume
        >>> volume = get_volume(box_part)  # 10x10x10 box
        >>> assert abs(volume - 1000.0) < 10.0  # Within 1%

        # Get cylinder volume
        >>> volume = get_volume(cylinder_part)  # r=5, h=20
        >>> expected = math.pi * 5**2 * 20
        >>> assert abs(volume - expected) < expected * 0.01  # Within 1%

        # Get sphere volume
        >>> volume = get_volume(sphere_part)  # r=10
        >>> expected = (4/3) * math.pi * 10**3
        >>> assert abs(volume - expected) < expected * 0.01  # Within 1%

        # Verify boolean operation volume
        >>> union_vol = get_volume(union_part)
        >>> # Union volume should be less than sum (due to overlap)
        >>> assert union_vol < get_volume(part1) + get_volume(part2)

    Technical Notes:
        - Uses CadQuery's Volume() method on solid
        - Accuracy typically better than 0.1%
        - For complex boolean operations, may have small numerical errors
        - Works with all primitive types and boolean combinations

    See Also:
        get_surface_area: For surface area calculation
        get_dimensions: For all dimensional measurements
    """
    # Validate input
    if not isinstance(part, Part):
        raise DimensionError(f"part must be a Part instance, got {type(part)}")

    try:
        # Get the CadQuery Workplane geometry
        geometry = part.geometry

        # Extract the solid and get its volume
        # CadQuery Workplane has .val() which returns the current object
        # or .solids().val() to get the first solid
        try:
            # Try to get the solid directly
            solid = geometry.val()
            volume = solid.Volume()
        except AttributeError:
            # If that fails, try to get solids
            try:
                solid = geometry.solids().val()
                volume = solid.Volume()
            except Exception:
                raise DimensionError(
                    f"Could not extract solid from geometry for part '{part.name}'"
                )

        return float(volume)

    except DimensionError:
        raise
    except Exception as e:
        raise DimensionError(
            f"Failed to calculate volume for part '{part.name}': {e}"
        ) from e


def get_surface_area(part: Part) -> float:
    """
    Calculate the surface area of a part.

    Uses the CAD kernel (CadQuery) to compute the exact surface area.
    Sums the area of all faces in the part.

    Args:
        part: Part to measure

    Returns:
        Surface area in square units

    Raises:
        DimensionError: If surface area cannot be calculated

    Examples:
        # Get box surface area
        >>> area = get_surface_area(box_part)  # 10x10x10 box
        >>> expected = 6 * 10 * 10  # 6 faces
        >>> assert abs(area - expected) < expected * 0.01  # Within 1%

        # Get cylinder surface area
        >>> area = get_surface_area(cylinder_part)  # r=5, h=20
        >>> # SA = 2*pi*r*h + 2*pi*r^2 (lateral + 2 caps)
        >>> expected = 2*math.pi*5*20 + 2*math.pi*5**2
        >>> assert abs(area - expected) < expected * 0.01  # Within 1%

        # Get sphere surface area
        >>> area = get_surface_area(sphere_part)  # r=10
        >>> expected = 4 * math.pi * 10**2
        >>> assert abs(area - expected) < expected * 0.01  # Within 1%

        # Verify surface area after fillet
        >>> filleted_area = get_surface_area(filleted_box)
        >>> # Fillet should reduce surface area slightly
        >>> original_area = get_surface_area(box)
        >>> # (Actually fillet might increase it slightly due to curved surfaces)

    Technical Notes:
        - Uses CadQuery's Face.Area() method
        - Sums areas of all faces in the solid
        - Accuracy typically better than 0.1%
        - For curved surfaces, area is computed via tessellation

    See Also:
        get_volume: For volume calculation
        get_dimensions: For all dimensional measurements
    """
    # Validate input
    if not isinstance(part, Part):
        raise DimensionError(f"part must be a Part instance, got {type(part)}")

    try:
        # Get the CadQuery Workplane geometry
        geometry = part.geometry

        # Extract all faces and sum their areas
        try:
            faces = geometry.faces().vals()
            total_area = sum(face.Area() for face in faces)
        except AttributeError as e:
            raise DimensionError(
                f"Could not extract faces from geometry for part '{part.name}': {e}"
            )
        except Exception as e:
            raise DimensionError(
                f"Error calculating face areas for part '{part.name}': {e}"
            )

        return float(total_area)

    except DimensionError:
        raise
    except Exception as e:
        raise DimensionError(
            f"Failed to calculate surface area for part '{part.name}': {e}"
        ) from e


# Future utilities planned for v3.2

def find_cylindrical_holes(part: Part):
    """
    Find cylindrical holes in a part.

    [STUB - To be implemented in v3.2]

    Args:
        part: Part to analyze

    Returns:
        List of hole descriptors with radius, depth, position, normal

    Implementation Plan (v3.2):
        1. Identify negative cylindrical features
        2. Extract hole parameters
        3. Return structured hole data
    """
    raise NotImplementedError(
        "find_cylindrical_holes will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 8"
    )


def find_fillets(part: Part):
    """
    Find filleted edges in a part.

    [STUB - To be implemented in v3.2]

    Args:
        part: Part to analyze

    Returns:
        List of fillet descriptors with radius, location

    Implementation Plan (v3.2):
        1. Identify rounded edges
        2. Measure fillet radius
        3. Return structured fillet data
    """
    raise NotImplementedError(
        "find_fillets will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 8"
    )


def find_chamfers(part: Part):
    """
    Find chamfered edges in a part.

    [STUB - To be implemented in v3.2]

    Args:
        part: Part to analyze

    Returns:
        List of chamfer descriptors with distance, location

    Implementation Plan (v3.2):
        1. Identify beveled edges
        2. Measure chamfer distance
        3. Return structured chamfer data
    """
    raise NotImplementedError(
        "find_chamfers will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 8"
    )
