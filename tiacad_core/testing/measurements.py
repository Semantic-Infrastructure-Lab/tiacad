"""
Measurement Utilities for TiaCAD Testing

Provides utilities for measuring distances, dimensions, and spatial relationships
between parts. Part of the Testing Confidence Plan v3.1.

Key functions:
    - measure_distance: Measure distance between two parts at reference points
    - get_bounding_box_dimensions: Extract width/height/depth from bounding box

Philosophy: Enable precise verification of attachment correctness and spatial
relationships in tests without manual coordinate calculation.

Author: TIA (galactic-expedition-1110)
Version: 1.0 (v3.1)
"""

from typing import Dict, Tuple, Optional
import numpy as np
from numpy.typing import NDArray

from tiacad_core.part import Part, PartRegistry
from tiacad_core.spatial_resolver import SpatialResolver, SpatialResolverError
from tiacad_core.geometry.spatial_references import SpatialRef


class MeasurementError(Exception):
    """Raised when measurement operations fail"""
    pass


def measure_distance(
    part1: Part,
    part2: Part,
    ref1: str = "center",
    ref2: str = "center",
    registry: Optional[PartRegistry] = None
) -> float:
    """
    Measure Euclidean distance between two parts at specified reference points.

    This is the primary utility for verifying attachment correctness in tests.
    Supports all TiaCAD reference types including auto-generated references.

    Args:
        part1: First part
        part2: Second part
        ref1: Reference point on part1 (default: "center")
              Can be any valid reference: "center", "face_top", "face_bottom",
              "axis_x", etc.
        ref2: Reference point on part2 (default: "center")
        registry: Optional PartRegistry for resolving references.
                 If None, creates temporary registry with both parts.

    Returns:
        Distance in model units (float)

    Raises:
        MeasurementError: If reference resolution fails or parts invalid

    Examples:
        # Distance between part centers
        >>> dist = measure_distance(box, cylinder)
        >>> print(f"Distance: {dist:.2f}")
        Distance: 25.00

        # Distance from box top to cylinder bottom (should be 0 if touching)
        >>> dist = measure_distance(
        ...     box, cylinder,
        ...     ref1="face_top",
        ...     ref2="face_bottom"
        ... )
        >>> assert dist < 0.001  # Parts are touching

        # Distance from box edge to sphere center
        >>> dist = measure_distance(
        ...     box, sphere,
        ...     ref1="edge_top_front",
        ...     ref2="center"
        ... )

        # Verify grid spacing in pattern
        >>> dist = measure_distance(hole1, hole2, ref1="center", ref2="center")
        >>> assert abs(dist - 50.0) < 0.1  # 50mm spacing

    Technical Notes:
        - Uses SpatialResolver for reference resolution
        - Supports part-local auto-generated references (v3.0 feature)
        - Returns straight-line distance (not surface distance)
        - Precision limited by floating-point accuracy (~1e-10)

    See Also:
        get_bounding_box_dimensions: For part dimensions
        docs/TESTING_CONFIDENCE_PLAN.md: Attachment correctness testing
    """
    # Validate inputs
    if not isinstance(part1, Part):
        raise MeasurementError(f"part1 must be a Part instance, got {type(part1)}")
    if not isinstance(part2, Part):
        raise MeasurementError(f"part2 must be a Part instance, got {type(part2)}")

    # Create or use provided registry
    if registry is None:
        registry = PartRegistry()
        # Add parts if not already present
        if not registry.exists(part1.name):
            registry.add(part1)
        if not registry.exists(part2.name):
            registry.add(part2)

    # Create spatial resolver
    resolver = SpatialResolver(registry, references={})

    # Resolve references with dot notation (part.reference)
    try:
        # Build full reference specs
        ref1_spec = f"{part1.name}.{ref1}" if "." not in ref1 else ref1
        ref2_spec = f"{part2.name}.{ref2}" if "." not in ref2 else ref2

        spatial_ref1 = resolver.resolve(ref1_spec)
        spatial_ref2 = resolver.resolve(ref2_spec)
    except SpatialResolverError as e:
        raise MeasurementError(
            f"Failed to resolve references: {e}\n"
            f"part1='{part1.name}', ref1='{ref1}'\n"
            f"part2='{part2.name}', ref2='{ref2}'"
        ) from e

    # Calculate Euclidean distance
    distance = np.linalg.norm(spatial_ref1.position - spatial_ref2.position)

    return float(distance)


def get_bounding_box_dimensions(part: Part) -> Dict[str, float]:
    """
    Extract dimensional measurements from part's bounding box.

    Returns width, height, and depth of the part's axis-aligned bounding box.
    Useful for verifying primitive dimensions in tests.

    Args:
        part: Part to measure

    Returns:
        Dictionary with keys:
            - 'width': X-axis extent (max_x - min_x)
            - 'height': Y-axis extent (max_y - min_y)
            - 'depth': Z-axis extent (max_z - min_z)
            - 'center': [x, y, z] center point of bounding box
            - 'min': [x, y, z] minimum corner
            - 'max': [x, y, z] maximum corner

    Raises:
        MeasurementError: If bounding box cannot be computed

    Examples:
        # Verify box dimensions
        >>> yaml = '''
        ... parts:
        ...   - name: test_box
        ...     type: box
        ...     size: [50, 30, 20]
        ... '''
        >>> model = build_model(yaml)
        >>> dims = get_bounding_box_dimensions(model.get("test_box"))
        >>> assert abs(dims["width"] - 50.0) < 0.01
        >>> assert abs(dims["height"] - 30.0) < 0.01
        >>> assert abs(dims["depth"] - 20.0) < 0.01

        # Verify cylinder bounding box
        >>> dims = get_bounding_box_dimensions(cylinder_part)
        >>> # Cylinder with radius=10 has bbox width/height of 20
        >>> assert abs(dims["width"] - 20.0) < 0.01

        # Get center point
        >>> dims = get_bounding_box_dimensions(part)
        >>> center = dims["center"]
        >>> print(f"Part center at: {center}")

    Technical Notes:
        - Uses Part.get_bounds() which delegates to geometry backend
        - Bounding box is axis-aligned (not oriented bounding box)
        - For rotated parts, bbox may be larger than actual part extent
        - Precision depends on geometry backend implementation

    See Also:
        measure_distance: For measuring between parts
        tiacad_core.testing.dimensions.get_volume: For volume measurement (v3.1+)
    """
    # Validate input
    if not isinstance(part, Part):
        raise MeasurementError(f"part must be a Part instance, got {type(part)}")

    try:
        # Get bounding box from part
        # Part.get_bounds() returns dict with 'min', 'max', 'center'
        bounds = part.get_bounds()
    except Exception as e:
        raise MeasurementError(
            f"Failed to get bounding box for part '{part.name}': {e}"
        ) from e

    # Extract min/max corners
    min_corner = np.array(bounds['min'])
    max_corner = np.array(bounds['max'])
    center = np.array(bounds['center'])

    # Calculate dimensions
    dimensions = {
        'width': float(max_corner[0] - min_corner[0]),   # X extent
        'height': float(max_corner[1] - min_corner[1]),  # Y extent
        'depth': float(max_corner[2] - min_corner[2]),   # Z extent
        'center': center.tolist(),
        'min': min_corner.tolist(),
        'max': max_corner.tolist(),
    }

    return dimensions


def get_distance_between_points(
    point1: NDArray[np.float64],
    point2: NDArray[np.float64]
) -> float:
    """
    Calculate Euclidean distance between two 3D points.

    Helper function for distance calculations. Useful when you already have
    resolved positions and don't need full part reference resolution.

    Args:
        point1: First point as [x, y, z] numpy array
        point2: Second point as [x, y, z] numpy array

    Returns:
        Distance in model units

    Raises:
        ValueError: If points are not 3D

    Examples:
        >>> p1 = np.array([0, 0, 0])
        >>> p2 = np.array([3, 4, 0])
        >>> dist = get_distance_between_points(p1, p2)
        >>> assert abs(dist - 5.0) < 0.001  # 3-4-5 triangle

        >>> # Using with SpatialRef positions
        >>> ref1 = resolver.resolve("box.face_top")
        >>> ref2 = resolver.resolve("cylinder.face_bottom")
        >>> dist = get_distance_between_points(ref1.position, ref2.position)

    Technical Notes:
        - Uses numpy.linalg.norm for calculation
        - Equivalent to: sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
    """
    # Ensure numpy arrays
    p1 = np.asarray(point1, dtype=np.float64)
    p2 = np.asarray(point2, dtype=np.float64)

    # Validate dimensions
    if p1.shape != (3,):
        raise ValueError(f"point1 must be 3D, got shape {p1.shape}")
    if p2.shape != (3,):
        raise ValueError(f"point2 must be 3D, got shape {p2.shape}")

    # Calculate distance
    return float(np.linalg.norm(p2 - p1))


# Future utilities (planned for v3.1-v3.2)
# These are stubs for future implementation

def parts_in_contact(
    part1: Part,
    part2: Part,
    tolerance: float = 0.01
) -> bool:
    """
    Check if two parts are in physical contact (within tolerance).

    [STUB - To be implemented in v3.2]

    Args:
        part1: First part
        part2: Second part
        tolerance: Maximum distance to consider "in contact" (default 0.01)

    Returns:
        True if parts are within tolerance distance

    Implementation Plan (v3.2):
        1. Quick reject: Check bounding box proximity
        2. Accurate check: Compute minimum surface-to-surface distance
        3. Return True if min_distance <= tolerance
    """
    raise NotImplementedError(
        "parts_in_contact will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 7"
    )


def build_contact_graph(parts: list, tolerance: float = 0.1):
    """
    Build adjacency graph of parts based on contact detection.

    [STUB - To be implemented in v3.2]

    Args:
        parts: List of Part instances
        tolerance: Contact tolerance

    Returns:
        Graph structure (adjacency dict or NetworkX graph)

    Implementation Plan (v3.2):
        1. For each pair of parts, check parts_in_contact()
        2. Build adjacency graph
        3. Return graph for connectivity analysis
    """
    raise NotImplementedError(
        "build_contact_graph will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 7"
    )


def is_fully_connected(graph) -> bool:
    """
    Check if contact graph represents a fully connected assembly.

    [STUB - To be implemented in v3.2]

    Args:
        graph: Contact graph from build_contact_graph()

    Returns:
        True if all parts are transitively connected

    Implementation Plan (v3.2):
        1. Perform depth-first search from first node
        2. Check if all nodes are reachable
        3. Return True if fully connected
    """
    raise NotImplementedError(
        "is_fully_connected will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 7"
    )
