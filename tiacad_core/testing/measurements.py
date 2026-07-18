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

from typing import Dict, List, Optional, Set
import numpy as np
from numpy.typing import NDArray

from tiacad_core.part import Part, PartRegistry
from tiacad_core.backend_support import require_cadquery_part
from tiacad_core.geometry.spatial_references import SpatialRef
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


def distance_between_refs(ref1: SpatialRef, ref2: SpatialRef) -> float:
    """
    Euclidean distance in model units between two already-resolved
    spatial references.
    """
    return float(np.linalg.norm(ref1.position - ref2.position))


def angle_between_refs(ref1: SpatialRef, ref2: SpatialRef) -> float:
    """
    Measure the angle in degrees between two spatial references' orientation
    vectors (face normals, axis directions, or edge tangents).

    Args:
        ref1: First resolved SpatialRef
        ref2: Second resolved SpatialRef

    Returns:
        Angle in degrees, in [0, 180]

    Raises:
        MeasurementError: If either reference has no orientation (e.g. a bare point)
    """
    if ref1.orientation is None or ref2.orientation is None:
        raise MeasurementError(
            "angle requires both references to carry an orientation vector "
            "(face, axis, or edge) — a bare point has none"
        )
    cos_theta = np.clip(np.dot(ref1.orientation, ref2.orientation), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))


def measure_angle(
    part1: Part,
    part2: Part,
    ref1: str = "center",
    ref2: str = "center",
    registry: Optional[PartRegistry] = None
) -> float:
    """
    Measure the angle in degrees between two parts' reference orientation
    vectors (face normals, axis directions, or edge tangents).

    Args:
        part1: First part
        part2: Second part
        ref1: Reference point on part1 (must resolve to an oriented reference)
        ref2: Reference point on part2 (must resolve to an oriented reference)
        registry: Optional PartRegistry; if None, a temporary one is created.

    Returns:
        Angle in degrees, in [0, 180]

    Raises:
        MeasurementError: If reference resolution fails or either reference
            has no orientation
    """
    if not isinstance(part1, Part):
        raise MeasurementError(f"part1 must be a Part instance, got {type(part1)}")
    if not isinstance(part2, Part):
        raise MeasurementError(f"part2 must be a Part instance, got {type(part2)}")

    resolver = _make_resolver(registry, part1, part2)
    context = f"part1='{part1.name}', ref1='{ref1}'\npart2='{part2.name}', ref2='{ref2}'"
    spatial_ref1 = _resolve_part_ref(resolver, part1.name, ref1, context)
    spatial_ref2 = _resolve_part_ref(resolver, part2.name, ref2, context)

    return angle_between_refs(spatial_ref1, spatial_ref2)


def check_alignment(
    ref1: SpatialRef,
    ref2: SpatialRef,
    angle_tolerance_deg: float = 0.5,
    offset_tolerance: float = 0.01,
) -> Dict[str, float]:
    """
    Check whether two spatial references are coaxial: their orientation
    vectors are parallel or antiparallel (within angle_tolerance_deg) and
    ref2's position lies on the line through ref1 along its orientation
    (within offset_tolerance).

    Args:
        ref1: First resolved SpatialRef (defines the reference axis)
        ref2: Second resolved SpatialRef
        angle_tolerance_deg: Max deviation from 0deg/180deg to count as parallel
        offset_tolerance: Max perpendicular distance from ref2's position to
            ref1's axis to count as coaxial

    Returns:
        Dict with 'aligned' (bool), 'angle_deg', 'parallel' (bool),
        'lateral_offset' (perpendicular distance from ref2 to ref1's axis)

    Raises:
        MeasurementError: If either reference has no orientation
    """
    angle = angle_between_refs(ref1, ref2)
    parallel = angle <= angle_tolerance_deg or angle >= (180.0 - angle_tolerance_deg)

    delta = ref2.position - ref1.position
    proj_len = np.dot(delta, ref1.orientation)
    perp = delta - proj_len * ref1.orientation
    lateral_offset = float(np.linalg.norm(perp))

    return {
        "aligned": bool(parallel and lateral_offset <= offset_tolerance),
        "angle_deg": angle,
        "parallel": parallel,
        "lateral_offset": lateral_offset,
    }


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

def _shape_distance(part1: Part, part2: Part) -> float:
    """Exact BREP surface-to-surface distance between two parts' geometry.

    Uses OCCT's ``BRepExtrema_DistShapeShape`` on the CadQuery kernel shapes —
    the true minimum gap between the solids, not a bounding-box approximation.
    """
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    require_cadquery_part(part1, "parts_in_contact")
    require_cadquery_part(part2, "parts_in_contact")

    calc = BRepExtrema_DistShapeShape(
        part1.geometry.val().wrapped, part2.geometry.val().wrapped
    )
    calc.Perform()
    if not calc.IsDone():
        raise MeasurementError(
            f"could not compute distance between {part1.name!r} and {part2.name!r}"
        )
    return float(calc.Value())


def parts_in_contact(
    part1: Part,
    part2: Part,
    tolerance: float = 0.01
) -> bool:
    """
    Check if two parts are in physical contact (within tolerance).

    Computes the exact minimum BREP surface-to-surface distance between the two
    solids (via OCCT ``BRepExtrema_DistShapeShape``) and returns True when it is
    within ``tolerance``. Touching faces measure 0.0; overlapping solids also
    measure 0.0. This is a real geometric test, not a bounding-box heuristic.

    Args:
        part1: First part
        part2: Second part
        tolerance: Maximum distance to consider "in contact" (default 0.01mm)

    Returns:
        True if the parts are within ``tolerance`` distance of each other
    """
    return _shape_distance(part1, part2) <= tolerance


def build_contact_graph(parts: list, tolerance: float = 0.1) -> Dict[str, Set[str]]:
    """
    Build an adjacency graph of parts based on real contact detection.

    Every pair is tested with :func:`parts_in_contact`; parts within
    ``tolerance`` are recorded as adjacent. Nodes are part names.

    Args:
        parts: List of Part instances
        tolerance: Contact tolerance (default 0.1mm)

    Returns:
        Adjacency dict mapping each part name to the set of names it contacts.
    """
    adjacency: Dict[str, Set[str]] = {p.name: set() for p in parts}
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            if parts_in_contact(a, b, tolerance):
                adjacency[a.name].add(b.name)
                adjacency[b.name].add(a.name)
    return adjacency


def is_fully_connected(graph: Dict[str, Set[str]]) -> bool:
    """
    Check whether a contact graph is a single connected assembly.

    A graph with 0 or 1 nodes is trivially connected. Otherwise, a
    breadth-first traversal from an arbitrary node must reach every node.

    Args:
        graph: Adjacency dict from :func:`build_contact_graph`

    Returns:
        True if all parts are transitively connected through contact
    """
    if len(graph) <= 1:
        return True

    start = next(iter(graph))
    seen: Set[str] = {start}
    queue: List[str] = [start]
    while queue:
        node = queue.pop()
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(graph)
