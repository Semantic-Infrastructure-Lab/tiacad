"""Unit tests for trust renderer helper behavior."""

import pyvista as pv

from tiacad_core.geometry import MockBackend
from tiacad_core.part import Part
from tiacad_core.validation.validation_types import Severity, ValidationIssue
from tiacad_core.visual.trust_renderer import (
    _annotate_issues,
    _collect_visible_part_names,
    _maybe_start_xvfb,
    _part_to_pyvista,
    _project_world_to_pixel,
    _subplot_pixel_rect,
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


def test_collect_visible_part_names_expands_pattern_dict_refs():
    """Regression: subtract:[{pattern: X}] must not crash on unhashable dict.

    Pattern-expanded subtract entries reference the pattern's instances
    (`X_0`, `X_1`, ...) by prefix, not the literal dict — see
    boolean_builder.py's _expand_dict_item for the matching expansion used
    when the operation actually runs.
    """

    class FakeParts:
        def list_parts(self):
            return ["base", "groove_ring_0", "groove_ring_1", "final"]

    class FakeDoc:
        parts = FakeParts()
        operations = {
            "final": {
                "type": "boolean",
                "operation": "difference",
                "base": "base",
                "subtract": [{"pattern": "groove_ring"}],
            }
        }

    assert _collect_visible_part_names(FakeDoc()) == ["final"]


def test_maybe_start_xvfb_ignores_startup_errors(monkeypatch):
    def boom():
        raise RuntimeError("xvfb unavailable")

    monkeypatch.setattr(
        "tiacad_core.visual.trust_renderer.pv.start_xvfb", boom, raising=False
    )
    _maybe_start_xvfb()


def test_part_to_pyvista_uses_backend_tessellation():
    backend = MockBackend()
    part = Part("mock_box", backend.create_box(10, 10, 10), backend=backend)

    mesh = _part_to_pyvista(part)

    assert mesh is not None
    assert mesh.n_points > 0


def _top_down_plotter(width=200, height=100):
    """A 1x2 off-screen plotter with a parallel top-down camera on each subplot."""
    plotter = pv.Plotter(shape=(1, 2), off_screen=True, window_size=[width, height])
    for col in range(2):
        plotter.subplot(0, col)
        plotter.camera_position = [(0, 0, 10), (0, 0, 0), (0, 1, 0)]
        plotter.camera.parallel_projection = True
        plotter.camera.parallel_scale = 5
        plotter.render()
    return plotter


def test_subplot_pixel_rect_splits_window_by_viewport():
    plotter = _top_down_plotter(width=200, height=100)

    left = _subplot_pixel_rect(plotter.renderers[0], 200, 100)
    right = _subplot_pixel_rect(plotter.renderers[1], 200, 100)

    assert left == (0, 0, 100, 100)
    assert right == (100, 0, 200, 100)
    plotter.close()


def test_project_world_to_pixel_maps_origin_to_subplot_center():
    plotter = _top_down_plotter(width=200, height=100)

    px, py = _project_world_to_pixel(plotter.renderers[0], (0, 0, 0), 100)

    # Origin is dead-center of the left subplot (0-100 x, 0-100 y).
    assert abs(px - 50) < 1e-6
    assert abs(py - 50) < 1e-6
    plotter.close()


def test_annotate_issues_noop_without_located_issues():
    render_img = pv.Plotter  # any object works: function must return before touching it
    _annotate_issues(render_img, plotter=None, issues=None, width=200, height=100)
    _annotate_issues(
        render_img, plotter=None,
        issues=[ValidationIssue(severity=Severity.WARNING, category="geometry", message="no location")],
        width=200, height=100,
    )


def test_annotate_issues_draws_marker_in_correct_subplot():
    from PIL import Image

    plotter = _top_down_plotter(width=200, height=100)
    render_img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    issue = ValidationIssue(
        severity=Severity.ERROR, category="geometry", message="at origin",
        world_position=(0, 0, 0),
    )

    _annotate_issues(render_img, plotter, [issue], width=200, height=100)

    pixels = render_img.load()
    # Marker ring (vivid red) should appear on the left subplot's crosshair rim,
    # not anywhere in the right subplot.
    assert pixels[60, 50] != (255, 255, 255)
    assert all(pixels[x, y] == (255, 255, 255) for x in (150, 199) for y in (0, 99))
    plotter.close()
