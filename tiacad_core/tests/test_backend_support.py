"""Tests for backend support helpers used by export/render paths."""

import pytest

from tiacad_core.backend_support import require_cadquery_part, tessellate_part
from tiacad_core.geometry import MockBackend
from tiacad_core.part import Part


def test_tessellate_part_uses_backend_tessellation():
    """tessellate_part should use backend tessellation and normalize vertex tuples."""
    backend = MockBackend()
    part = Part(name="mock_box", geometry=backend.create_box(10, 10, 10), backend=backend)

    vertices, triangles = tessellate_part(part)

    assert len(vertices) > 0
    assert len(triangles) > 0
    assert vertices[0] == (-1.0, -1.0, -1.0)
    assert triangles[0] == (0, 1, 2)


def test_require_cadquery_part_rejects_other_backends():
    """CadQuery-only operations should fail clearly on other backends."""
    backend = MockBackend()
    part = Part(name="mock_box", geometry=backend.create_box(10, 10, 10), backend=backend)

    with pytest.raises(TypeError) as exc_info:
        require_cadquery_part(part, "STL export")

    assert "cadquery-compatible part" in str(exc_info.value).lower()
