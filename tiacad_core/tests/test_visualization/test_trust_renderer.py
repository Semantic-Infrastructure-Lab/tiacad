"""Unit tests for trust renderer helper behavior."""

import pyvista as pv

from tiacad_core.geometry import MockBackend
from tiacad_core.part import Part
from tiacad_core.validation.validation_types import Severity, ValidationIssue
import numpy as np
import pytest

from tiacad_core.visual.trust_renderer import (
    _DEPTH_SHADE_MIN,
    _annotate_issues,
    _cap_at_plane,
    _depth_shaded,
    parse_section_spec,
    _collect_component_parts,
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

        def get(self, name):
            return Part(name=name, geometry=MockBackend().create_box(1, 1, 1))

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

        def get(self, name):
            return Part(name=name, geometry=MockBackend().create_box(1, 1, 1))

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


def test_collect_component_parts_expands_pattern_and_range_refs():
    """Regression: `render --section` crashed (unhashable dict) on subtract:[{pattern: X}]."""

    class FakeParts:
        def list_parts(self):
            return ["base", "slots_0", "slots_1", "slots_10", "hole_0", "hole_1", "final"]

    class FakeDoc:
        parts = FakeParts()
        export_config = {}
        operations = {
            "final": {
                "type": "boolean",
                "operation": "difference",
                "base": "base",
                "subtract": [{"pattern": "slots"}, {"range": "hole[0..0]"}],
            }
        }

    additive, subtractive = _collect_component_parts(FakeDoc())
    assert additive == ["base"]
    assert subtractive == ["slots_0", "slots_1", "slots_10", "hole_0"]  # numeric order, range honored


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


def test_parse_section_spec_accepts_axis_and_value():
    assert parse_section_spec("y=79.5") == ("y", 79.5)
    assert parse_section_spec("Z=-3") == ("z", -3.0)


@pytest.mark.parametrize("spec", ["", "y", "w=1", "y=abc", "=5"])
def test_parse_section_spec_rejects_malformed_specs(spec):
    with pytest.raises(ValueError, match="Invalid section"):
        parse_section_spec(spec)


def _u_prism(depth=10.0):
    """U-shaped (concave) solid extruded along +Y; its XZ outline area is 226.0."""
    outline = [(0, 0), (74, 0), (74, 50), (73.2, 50), (73.2, 2), (0.8, 2), (0.8, 50), (0, 50)]
    pts = np.array([(x, 0.0, z) for x, z in outline])
    face = [len(pts), *range(len(pts))]
    solid = pv.PolyData(pts, np.array(face)).extrude((0, depth, 0), capping=True)
    return solid.triangulate().clean()


def test_cap_at_plane_fills_concave_profile_exactly():
    cap = _cap_at_plane(_u_prism(), axis_idx=1, value=5.0)

    area = cap.compute_cell_sizes(length=False, volume=False).cell_data["Area"].sum()
    # 74*2 floor + 2 * (0.8 * 48) walls; a convex fill would also cover the notch.
    assert area == pytest.approx(74 * 2 + 2 * 0.8 * 48)


def test_cap_at_plane_returns_none_when_plane_misses_the_solid():
    assert _cap_at_plane(_u_prism(), axis_idx=1, value=999.0) is None


def test_depth_shaded_darkens_far_points_and_keeps_near_points_full_colour():
    box = pv.Box(bounds=(0, 1, 0, 1, 0, 10)).triangulate()

    shaded = _depth_shaded(box, (1.0, 0.5, 0.0), view_dir=(0, 0, 1))

    rgb = shaded.point_data["depth_rgb"].astype(float)
    near = rgb[box.points[:, 2] == 10][0]
    far = rgb[box.points[:, 2] == 0][0]
    assert tuple(near) == (255, 127, 0)
    assert far[0] == pytest.approx(255 * _DEPTH_SHADE_MIN, abs=1)
    assert "depth_rgb" not in box.point_data  # input mesh untouched


def test_collect_visible_part_names_hides_component_internal_parts(tmp_path):
    from tiacad_core.parser.tiacad_parser import TiaCADParser

    (tmp_path / "comp.yaml").write_text(
        'schema_version: "3.0"\n'
        "parts:\n"
        "  block: {primitive: box, size: [10, 10, 10], origin: corner}\n"
        "  cutter: {primitive: box, size: [2, 2, 20], origin: corner}\n"
        "operations:\n"
        "  holed: {type: boolean, operation: difference, base: block, subtract: [cutter]}\n"
    )
    (tmp_path / "main.yaml").write_text(
        "imports:\n  - {path: ./comp.yaml, as: c}\n"
        "operations:\n"
        "  moved: {type: transform, input: c.holed, transforms: [{translate: [20, 0, 0]}]}\n"
        "  both: {type: boolean, operation: union, inputs: [c.holed, moved]}\n"
    )
    doc = TiaCADParser.parse_file(str(tmp_path / "main.yaml"))

    assert _collect_visible_part_names(doc) == ["both"]


def test_collect_visible_part_names_keeps_unreferenced_imported_part(tmp_path):
    from tiacad_core.parser.tiacad_parser import TiaCADParser

    (tmp_path / "comp.yaml").write_text(
        'schema_version: "3.0"\n'
        "parts:\n"
        "  block: {primitive: box, size: [10, 10, 10], origin: corner}\n"
    )
    (tmp_path / "main.yaml").write_text(
        "imports:\n  - {path: ./comp.yaml, as: c}\n"
        "parts:\n"
        "  base: {primitive: box, size: [5, 5, 5], origin: corner}\n"
    )
    doc = TiaCADParser.parse_file(str(tmp_path / "main.yaml"))

    assert set(_collect_visible_part_names(doc)) == {"c.block", "base"}
