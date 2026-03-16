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

from typing import Dict, Optional
import numpy as np
from numpy.typing import NDArray

from tiacad_core.part import Part, PartRegistry
from tiacad_core.spatial_resolver import SpatialResolver, SpatialResolverError


class MeasurementError(Exception):
    """Raised when measurement operations fail"""
    pass


def _make_resolver(registry: Optional[PartRegistry], *parts: Part) -> SpatialResolver:
    """Create a SpatialResolver, building a temporary PartRegistry if needed."""
    if registry is None:
        registry = PartRegistry()
        for part in parts:
            if not registry.exists(part.name):
                registry.add(part)
    return SpatialResolver(registry, references={})


def _resolve_part_ref(resolver: SpatialResolver, part_name: str, ref: str, context: str):
    """Resolve a part reference, converting SpatialResolverError → MeasurementError."""
    ref_spec = f"{part_name}.{ref}" if "." not in ref else ref
    try:
        return resolver.resolve(ref_spec)
    except SpatialResolverError as e:
        raise MeasurementError(f"Failed to resolve references: {e}\n{context}") from e


def measure_distance(
    part1: Part,
    part2: Part,
    ref1: str = "center",
    ref2: str = "center",
    registry: Optional[PartRegistry] = None
) -> float:
    """
    Measure Euclidean distance between two parts at specified reference points.

    Args:
        part1: First part
        part2: Second part
        ref1: Reference point on part1 (default: "center")
        ref2: Reference point on part2 (default: "center")
        registry: Optional PartRegistry; if None, a temporary one is created.

    Returns:
        Distance in model units (float)

    Raises:
        MeasurementError: If reference resolution fails or parts invalid
    """
    if not isinstance(part1, Part):
        raise MeasurementError(f"part1 must be a Part instance, got {type(part1)}")
    if not isinstance(part2, Part):
        raise MeasurementError(f"part2 must be a Part instance, got {type(part2)}")

    resolver = _make_resolver(registry, part1, part2)
    context = f"part1='{part1.name}', ref1='{ref1}'\npart2='{part2.name}', ref2='{ref2}'"
    spatial_ref1 = _resolve_part_ref(resolver, part1.name, ref1, context)
    spatial_ref2 = _resolve_part_ref(resolver, part2.name, ref2, context)

    return float(np.linalg.norm(spatial_ref1.position - spatial_ref2.position))


def get_bounding_box_dimensions(part: Part) -> Dict[str, float]:
    """
    Extract dimensional measurements from part's axis-aligned bounding box.

    Args:
        part: Part to measure

    Returns:
        Dict with 'width' (X), 'height' (Y), 'depth' (Z), 'center', 'min', 'max'.

    Raises:
        MeasurementError: If bounding box cannot be computed
    """
    if not isinstance(part, Part):
        raise MeasurementError(f"part must be a Part instance, got {type(part)}")

    try:
        bounds = part.get_bounds()
    except Exception as e:
        raise MeasurementError(
            f"Failed to get bounding box for part '{part.name}': {e}"
        ) from e

    min_corner = np.array(bounds['min'])
    max_corner = np.array(bounds['max'])
    center = np.array(bounds['center'])

    return {
        'width': float(max_corner[0] - min_corner[0]),
        'height': float(max_corner[1] - min_corner[1]),
        'depth': float(max_corner[2] - min_corner[2]),
        'center': center.tolist(),
        'min': min_corner.tolist(),
        'max': max_corner.tolist(),
    }


def get_distance_between_points(
    point1: NDArray[np.float64],
    point2: NDArray[np.float64]
) -> float:
    """
    Calculate Euclidean distance between two 3D points.

    Args:
        point1: First point as [x, y, z] numpy array
        point2: Second point as [x, y, z] numpy array

    Returns:
        Distance in model units

    Raises:
        ValueError: If points are not 3D
    """
    p1 = np.asarray(point1, dtype=np.float64)
    p2 = np.asarray(point2, dtype=np.float64)

    if p1.shape != (3,):
        raise ValueError(f"point1 must be 3D, got shape {p1.shape}")
    if p2.shape != (3,):
        raise ValueError(f"point2 must be 3D, got shape {p2.shape}")

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
    """
    raise NotImplementedError(
        "is_fully_connected will be implemented in v3.2\n"
        "See docs/TESTING_ROADMAP.md Week 7"
    )
