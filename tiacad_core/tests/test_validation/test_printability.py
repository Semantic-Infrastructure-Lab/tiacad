"""Advisory print checks (validation/printability.py) against meshes with hand-computed answers."""

import tempfile
from pathlib import Path

import trimesh
import pytest

from tiacad_core.validation.printability import (
    check_build_volume,
    find_overhangs,
    min_wall_thickness,
    parse_bed_spec,
    printability_warnings,
)


def _hollow_box(outer=20.0, wall=1.0):
    """Closed box with a fully enclosed cavity: every wall is exactly `wall` thick."""
    shell = trimesh.creation.box(extents=[outer] * 3)
    cavity = trimesh.creation.box(extents=[outer - 2 * wall] * 3)
    cavity.invert()
    return trimesh.util.concatenate([shell, cavity])


def _t_shape(tmp_path=None):
    """Solid T: 10x10x10 stem under a 30x10x2 bar -> two 10x10 ceilings (200 mm2) overhang the stem."""
    import cadquery as cq

    stem = cq.Workplane("XY").box(10, 10, 10, centered=(True, True, False))
    bar = cq.Workplane("XY").box(30, 10, 2, centered=(True, True, False)).translate((0, 0, 10))
    out = (tmp_path or Path(tempfile.mkdtemp())) / "t.stl"
    stem.union(bar).val().exportStl(str(out))
    return trimesh.load(str(out))


@pytest.fixture
def t_shape(tmp_path):
    return _t_shape(tmp_path)


class TestParseBedSpec:
    def test_parses_x_separated(self):
        assert parse_bed_spec("250x210x200") == (250.0, 210.0, 200.0)
        assert parse_bed_spec(" 25.5 X 10 x 3 ") == (25.5, 10.0, 3.0)

    @pytest.mark.parametrize("bad", ["", "250x210", "axbxc", "250x0x10", "1x2x3x4", "-1x2x3"])
    def test_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            parse_bed_spec(bad)


class TestBuildVolume:
    def test_fits_as_modeled(self):
        fit = check_build_volume(trimesh.creation.box(extents=[74, 236, 50.8]), (250, 250, 200))
        assert fit.fits and fit.as_modeled

    def test_fits_only_rotated(self):
        # 236 along Y does not fit bed Y=210, but model Y -> bed X (250) does
        fit = check_build_volume(trimesh.creation.box(extents=[74, 236, 50.8]), (250, 210, 200))
        assert fit.fits and not fit.as_modeled
        assert fit.axis_order == (1, 0, 2)

    def test_does_not_fit_any_orientation(self):
        fit = check_build_volume(trimesh.creation.box(extents=[74, 236, 50.8]), (230, 230, 200))
        assert not fit.fits

    def test_exact_fit_counts(self):
        assert check_build_volume(trimesh.creation.box(extents=[10, 20, 30]), (10, 20, 30)).fits


class TestOverhangs:
    def test_plain_box_has_none(self):
        # the bottom face is on the bed, so it needs no support
        assert find_overhangs(trimesh.creation.box(extents=[10, 10, 10])).area == 0.0

    def test_t_shape_ceilings(self, t_shape):
        report = find_overhangs(t_shape)
        assert report.area == pytest.approx(200.0)
        assert 0 < report.fraction < 1

    def test_threshold_angle_controls_flagging(self):
        # cone-like prism leaning outward 60 deg from vertical: flagged at 45, not at 70
        import numpy as np

        mesh = trimesh.creation.box(extents=[10, 10, 10])
        mesh.apply_translation([0, 0, 5])
        tilt = trimesh.transformations.rotation_matrix(np.radians(60), [0, 1, 0])
        tilted = trimesh.creation.box(extents=[10, 10, 1])
        tilted.apply_transform(tilt)
        tilted.apply_translation([0, 0, 20])
        both = trimesh.util.concatenate([mesh, tilted])
        assert find_overhangs(both, angle=45).area > find_overhangs(both, angle=80).area


class TestWallThickness:
    def test_hollow_box_wall(self):
        report = min_wall_thickness(_hollow_box(20.0, 1.0), samples=3000)
        assert report.min_thickness == pytest.approx(1.0, abs=1e-3)

    def test_thinner_wall_is_the_minimum(self):
        report = min_wall_thickness(_hollow_box(20.0, 0.5), samples=3000)
        assert report.min_thickness == pytest.approx(0.5, abs=1e-3)

    def test_solid_box_thickness_is_its_extent(self):
        report = min_wall_thickness(trimesh.creation.box(extents=[10, 10, 4]), samples=2000)
        assert report.min_thickness == pytest.approx(4.0, abs=1e-3)

    def test_location_is_on_the_surface(self):
        report = min_wall_thickness(trimesh.creation.box(extents=[10, 10, 4]), samples=500)
        assert report.location is not None and abs(abs(report.location[2]) - 2.0) < 1e-6


class TestWarnings:
    def test_thin_wall_warns_below_threshold_only(self):
        mesh = _hollow_box(20.0, 0.5)
        _, warnings = printability_warnings(mesh, min_wall=0.8)
        assert any("Wall thickness" in w and "below 0.8" in w for w in warnings)
        _, warnings = printability_warnings(mesh, min_wall=0.4)
        assert not any("Wall thickness" in w for w in warnings)

    def test_bed_misfit_is_a_warning_and_fit_is_info(self):
        mesh = trimesh.creation.box(extents=[10, 10, 10])
        info, warnings = printability_warnings(mesh, bed=(5, 5, 5))
        assert any("does not fit" in w for w in warnings)
        info, warnings = printability_warnings(mesh, bed=(50, 50, 50))
        assert any("fits" in i for i in info) and not any("Build volume" in w for w in warnings)

    def test_overhang_warns_with_supports_note(self, t_shape):
        _, warnings = printability_warnings(t_shape)
        assert any("Overhangs" in w and "supports likely" in w for w in warnings)


class TestPlacement:
    def test_centered_part_reports_it_straddles_the_bed_plane(self):
        info, _ = printability_warnings(trimesh.creation.box(extents=(10, 10, 10)))
        assert any(i.startswith("Placement: spans z -5.0 to 5.0") and "straddles" in i for i in info)

    def test_part_on_z0_has_no_placement_line(self):
        mesh = trimesh.creation.box(extents=(10, 10, 10))
        mesh.apply_translation((0, 0, 5))
        info, warnings = printability_warnings(mesh)
        assert not any(i.startswith("Placement") for i in info + warnings)
