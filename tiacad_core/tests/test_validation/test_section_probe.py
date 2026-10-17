"""`tiacad section` engine (validation/section_probe.py) against meshes with hand-computed answers."""

import json
from types import SimpleNamespace

import pytest
import trimesh

from tiacad_core.cli import cmd_section
from tiacad_core.validation.section_probe import (
    SurfaceProbe,
    parse_line_spec,
    parse_plane_spec,
    probe_line,
    section_thicknesses,
)


def _hollow_box(outer=20.0, wall=1.0):
    """Closed box, enclosed cavity: walls exactly `wall` thick, spans -outer/2..outer/2."""
    shell = trimesh.creation.box(extents=[outer] * 3)
    cavity = trimesh.creation.box(extents=[outer - 2 * wall] * 3)
    cavity.invert()
    return trimesh.util.concatenate([shell, cavity])


class TestSpecParsing:
    def test_plane(self):
        assert parse_plane_spec("y=79.5") == (1, 79.5)
        assert parse_plane_spec(" Z = -2 ") == (2, -2.0)

    @pytest.mark.parametrize("bad", ["", "y", "q=1", "y=abc", "=3"])
    def test_plane_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            parse_plane_spec(bad)

    def test_line(self):
        assert parse_line_spec("x@y=79.5,z=25.4") == (0, {1: 79.5, 2: 25.4})

    @pytest.mark.parametrize("bad", ["x", "x@y=1", "x@x=1,y=2", "x@y=1,y=2", "x@y=a,z=1", "q@y=1,z=1"])
    def test_line_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            parse_line_spec(bad)


class TestIntervals:
    def test_hollow_box_line_through_centre_gives_two_walls(self):
        intervals = probe_line(_hollow_box(20.0, 1.0), 0, {1: 0.0, 2: 0.0})
        assert intervals == [pytest.approx((-10.0, -9.0)), pytest.approx((9.0, 10.0))]

    def test_solid_box_is_one_interval(self):
        intervals = probe_line(trimesh.creation.box(extents=[10, 10, 4]), 2, {0: 1.0, 1: 1.0})
        assert intervals == [pytest.approx((-2.0, 2.0))]

    def test_line_missing_the_part_is_empty(self):
        assert probe_line(trimesh.creation.box(extents=[10, 10, 4]), 0, {1: 50.0, 2: 0.0}) == []

    def test_probe_bounds(self):
        probe = SurfaceProbe(trimesh.creation.box(extents=[10, 20, 30]))
        assert probe.bounds[1].tolist() == [5.0, 10.0, 15.0]


class TestSectionThicknesses:
    def test_hollow_box_reports_wall_and_full_span(self):
        report = section_thicknesses(_hollow_box(20.0, 1.0), axis=1, value=0.0, step=1.0)
        along_x = {row.thickness: row for row in report.scans[0]}

        assert 1.0 in along_x            # the 1 mm walls
        assert 20.0 in along_x           # lines through the top/bottom walls span the box
        assert along_x[1.0].lines > along_x[20.0].lines
        assert report.lines_hit == report.lines_cast

    def test_rows_are_sorted_thinnest_first_and_located_on_the_plane(self):
        report = section_thicknesses(_hollow_box(20.0, 0.5), axis=2, value=0.0, step=1.0)

        for rows in report.scans.values():
            assert [r.thickness for r in rows] == sorted(r.thickness for r in rows)
            assert rows[0].thickness == pytest.approx(0.5)
            assert rows[0].first_at[2] == pytest.approx(0.0)

    def test_plane_outside_the_part_finds_nothing(self):
        report = section_thicknesses(trimesh.creation.box(extents=[10, 10, 10]), axis=0, value=99.0)
        assert report.lines_hit == 0 and all(rows == [] for rows in report.scans.values())


_MODEL = """
parts:
  slab:
    primitive: box
    size: [10, 10, 4]
    origin: corner
"""


def _args(path, **kw):
    base = dict(input=str(path), part="slab", plane=None, line=None, step=1.0, set=None, json=False, verbose=False)
    base.update(kw)
    return SimpleNamespace(**base)


class TestCmdSection:
    def _model(self, tmp_path):
        f = tmp_path / "slab.tiacad"
        f.write_text(_MODEL)
        return f

    def test_plane_report_lists_thickness(self, tmp_path, capsys):
        assert cmd_section(_args(self._model(tmp_path), plane="y=5")) == 0
        out = capsys.readouterr().out
        assert "Section y=5" in out and "4.00" in out and "10.00" in out

    def test_line_report(self, tmp_path, capsys):
        assert cmd_section(_args(self._model(tmp_path), line="z@x=5,y=5")) == 0
        assert "thickness 4.000 mm" in capsys.readouterr().out

    def test_json_output(self, tmp_path, capsys):
        assert cmd_section(_args(self._model(tmp_path), line="x@y=5,z=2", json=True)) == 0
        data = json.loads(capsys.readouterr().out)
        assert data["intervals"] == [[pytest.approx(0.0), pytest.approx(10.0)]]

    def test_miss_returns_1(self, tmp_path, capsys):
        assert cmd_section(_args(self._model(tmp_path), plane="y=500")) == 1

    def test_requires_exactly_one_of_plane_or_line(self, tmp_path, capsys):
        f = self._model(tmp_path)
        assert cmd_section(_args(f)) == 1
        assert cmd_section(_args(f, plane="y=1", line="x@y=1,z=1")) == 1

    def test_rejects_bad_spec_and_missing_file(self, tmp_path, capsys):
        assert cmd_section(_args(self._model(tmp_path), plane="q=1")) == 1
        assert cmd_section(_args(tmp_path / "nope.tiacad", plane="y=1")) == 1
