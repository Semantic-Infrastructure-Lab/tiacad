"""
Backend helpers for parser/build pipeline.

This module centralizes the explicit boundary between backend-agnostic and
CadQuery-only builder paths.
"""

from __future__ import annotations

from ..geometry import CadQueryBackend, get_default_backend
from ..part import Part

_cadquery_backend: CadQueryBackend | None = None


def get_cadquery_backend() -> CadQueryBackend:
    """Return a shared CadQuery backend instance for CadQuery-native builders."""
    global _cadquery_backend
    default_backend = get_default_backend()
    if isinstance(default_backend, CadQueryBackend):
        _cadquery_backend = default_backend
        return default_backend
    if _cadquery_backend is None:
        _cadquery_backend = CadQueryBackend()
    return _cadquery_backend


def require_cadquery_input_part(part: Part, operation_label: str, context: str) -> CadQueryBackend:
    """
    Ensure an input part is compatible with CadQuery-native builder logic.

    Parts without an attached backend are treated as legacy CadQuery parts.
    """
    if part.backend is None:
        return get_cadquery_backend()
    if isinstance(part.backend, CadQueryBackend):
        return part.backend
    raise TypeError(
        f"{operation_label} '{context}' requires a CadQuery-compatible input part; "
        f"part '{part.name}' uses a different backend."
    )
