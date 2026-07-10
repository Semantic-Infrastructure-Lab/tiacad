"""
Backend support helpers for runtime export and visualization paths.

These helpers make the kernel boundary explicit in user-facing surfaces:
- STL/STEP export is currently CadQuery-only
- Mesh/tessellation consumers can use any backend that implements tessellation
"""

from __future__ import annotations

from typing import List, Tuple

from .geometry import CadQueryBackend
from .part import Part


def require_cadquery_part(part: Part, operation_label: str) -> None:
    """Raise a clear error when an operation requires CadQuery geometry."""
    if part.backend is None or isinstance(part.backend, CadQueryBackend):
        return
    raise TypeError(
        f"{operation_label} requires a CadQuery-compatible part; "
        f"part '{part.name}' uses a different backend."
    )


def tessellate_part(
    part: Part,
    tolerance: float = 0.1,
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, int, int]]]:
    """Tessellate a part using its backend when available, otherwise fall back to CadQuery."""
    if part.backend is not None:
        raw_vertices, raw_triangles = part.backend.tessellate(part.geometry, tolerance)
    else:
        raw_vertices, raw_triangles = part.geometry.val().tessellate(tolerance)

    vertices = [_vertex_to_tuple(v) for v in raw_vertices]
    triangles = [tuple(int(i) for i in tri) for tri in raw_triangles]
    return vertices, triangles


def _vertex_to_tuple(vertex) -> Tuple[float, float, float]:
    """Normalize backend-specific vertex objects to plain xyz tuples."""
    if hasattr(vertex, 'x') and hasattr(vertex, 'y') and hasattr(vertex, 'z'):
        return (float(vertex.x), float(vertex.y), float(vertex.z))
    if isinstance(vertex, (list, tuple)) and len(vertex) == 3:
        return (float(vertex[0]), float(vertex[1]), float(vertex[2]))
    raise TypeError(f"Unsupported tessellation vertex type: {type(vertex).__name__}")
