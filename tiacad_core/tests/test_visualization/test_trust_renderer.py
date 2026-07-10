"""Unit tests for trust renderer helper behavior."""

from tiacad_core.geometry import MockBackend
from tiacad_core.part import Part
from tiacad_core.visual.trust_renderer import (
    _collect_visible_part_names,
    _maybe_start_xvfb,
    _part_to_pyvista,
)


def test_collect_visible_part_names_skips_consumed_inputs():
    class FakeParts:
        def list_parts(self):
            return ["base", "hole", "final"]

    class FakeDoc:
        parts = FakeParts()
        operations = {
            "final": {
                "type": "boolean",
                "operation": "difference",
                "base": "base",
                "subtract": ["hole"],
            }
        }

    assert _collect_visible_part_names(FakeDoc()) == ["final"]


def test_maybe_start_xvfb_ignores_startup_errors(monkeypatch):
    def boom():
        raise RuntimeError("xvfb unavailable")

    monkeypatch.setattr("tiacad_core.visual.trust_renderer.pv.start_xvfb", boom)
    _maybe_start_xvfb()


def test_part_to_pyvista_uses_backend_tessellation():
    backend = MockBackend()
    part = Part("mock_box", backend.create_box(10, 10, 10), backend=backend)

    mesh = _part_to_pyvista(part)

    assert mesh is not None
    assert mesh.n_points > 0
