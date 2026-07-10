"""Structured geometry summaries for testing and AI/debug workflows."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..backend_support import tessellate_part
from ..part import Part, PartRegistry
from .dimensions import get_surface_area, get_volume

try:
    import trimesh
except ImportError:  # pragma: no cover - optional dependency
    trimesh = None


class GeometrySummaryError(Exception):
    """Raised when summary generation fails for invalid input."""


def summarize_part_geometry(
    part: Part,
    *,
    include_mesh: bool = True,
    tessellation_tolerance: float = 0.1,
) -> Dict[str, Any]:
    """Return a structured, JSON-safe summary of a part's geometry state."""
    if not isinstance(part, Part):
        raise GeometrySummaryError(f"part must be a Part instance, got {type(part)}")

    bounds = part.get_bounds()
    min_corner = tuple(float(v) for v in bounds['min'])
    max_corner = tuple(float(v) for v in bounds['max'])
    center = tuple(float(v) for v in bounds['center'])

    summary: Dict[str, Any] = {
        'name': part.name,
        'backend': _backend_name(part),
        'bounds': {
            'min': min_corner,
            'max': max_corner,
            'center': center,
        },
        'extents': {
            'x': max_corner[0] - min_corner[0],
            'y': max_corner[1] - min_corner[1],
            'z': max_corner[2] - min_corner[2],
        },
        'current_position': _maybe_tuple(part.current_position),
        'transform_count': len(part.transform_history),
        'transform_types': [step.get('type') for step in part.transform_history],
        'metadata_keys': sorted(part.metadata.keys()),
        'metrics': {
            'volume': _safe_metric(get_volume, part),
            'surface_area': _safe_metric(get_surface_area, part),
        },
    }

    if include_mesh:
        summary['mesh'] = _summarize_mesh(part, tessellation_tolerance)

    return summary


def summarize_part_registry(
    registry: PartRegistry,
    *,
    include_mesh: bool = True,
    tessellation_tolerance: float = 0.1,
) -> Dict[str, Dict[str, Any]]:
    """Return summaries for every part in a registry keyed by part name."""
    if not isinstance(registry, PartRegistry):
        raise GeometrySummaryError(
            f"registry must be a PartRegistry instance, got {type(registry)}"
        )

    return {
        part_name: summarize_part_geometry(
            registry.get(part_name),
            include_mesh=include_mesh,
            tessellation_tolerance=tessellation_tolerance,
        )
        for part_name in registry.list_parts()
    }


def _backend_name(part: Part) -> Optional[str]:
    """Return a stable backend label when available."""
    if part.backend is None:
        return None
    return type(part.backend).__name__


def _maybe_tuple(value) -> Optional[tuple[float, float, float]]:
    """Normalize optional xyz-like values to float tuples."""
    if value is None:
        return None
    return tuple(float(v) for v in value)


def _safe_metric(metric_fn, part: Part) -> Optional[float]:
    """Return a metric value when available, otherwise None."""
    try:
        return float(metric_fn(part))
    except Exception:
        return None


def _summarize_mesh(part: Part, tessellation_tolerance: float) -> Dict[str, Any]:
    """Summarize mesh/tessellation facts for a part."""
    try:
        vertices, triangles = tessellate_part(part, tessellation_tolerance)
    except Exception as exc:
        return {
            'available': False,
            'error': str(exc),
        }

    summary: Dict[str, Any] = {
        'available': True,
        'vertex_count': len(vertices),
        'triangle_count': len(triangles),
        'component_count': None,
        'watertight': None,
    }

    if trimesh is not None and vertices and triangles:
        mesh = trimesh.Trimesh(vertices=vertices, faces=triangles, process=False)
        summary['component_count'] = len(mesh.split(only_watertight=False))
        summary['watertight'] = bool(mesh.is_watertight)

    return summary
