"""Tests for `tiacad validate-geometry` (cmd_validate_geometry) — TCAD-VAL-9."""

from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_validate_geometry

_SIMPLE_MODEL = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""

# Two non-overlapping boxes unioned: a real disconnected-component case, the
# exact scenario this command exists to catch (see cli/validate_geometry.py
# module docstring: "union operations actually merge").
_DISCONNECTED_MODEL = """
parts:
  box_a:
    primitive: box
    size: [10, 10, 10]
  box_b:
    primitive: box
    size: [10, 10, 10]

operations:
  box_b_moved:
    type: transform
    input: box_b
    transforms:
      - translate: [100, 0, 0]
  merged:
    type: boolean
    operation: union
    base: box_a
    add: [box_b_moved]

export:
  default_part: merged
"""


def _args(input_path, part=None, verbose=False):
    return SimpleNamespace(input=str(input_path), part=part, verbose=verbose)


def test_validate_geometry_watertight_single_part_passes(tmp_path, capsys):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)

    exit_code = cmd_validate_geometry(_args(model, part="box"))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Geometry is valid" in out


def test_validate_geometry_disconnected_components_fails(tmp_path, capsys):
    model = tmp_path / "disconnected.tiacad"
    model.write_text(_DISCONNECTED_MODEL)

    exit_code = cmd_validate_geometry(_args(model, part="merged"))
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "disconnected" in out.lower()


def test_validate_geometry_missing_file_fails(capsys):
    exit_code = cmd_validate_geometry(_args("does_not_exist.tiacad"))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.out + captured.err


# --- advisory printability section (TCAD-VAL-15) ---

def _print_args(input_path, **extra):
    return SimpleNamespace(input=str(input_path), part="box", verbose=False, **extra)


def test_validate_geometry_reports_printability_section(tmp_path, capsys):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)

    assert cmd_validate_geometry(_print_args(model)) == 0
    out = capsys.readouterr().out
    assert "Printability (advisory)" in out
    assert "Wall thickness: thinnest sampled 10.00 mm" in out
    assert "Overhangs: 0.0 mm2" in out
    assert "Build volume" not in out  # only with --bed


def test_validate_geometry_bed_misfit_is_advisory_not_failure(tmp_path, capsys):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)

    exit_code = cmd_validate_geometry(_print_args(model, bed="5x5x5"))
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "does not fit 5 x 5 x 5 mm in any axis-aligned orientation" in out


def test_validate_geometry_bed_fit_and_min_wall_flag(tmp_path, capsys):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)

    exit_code = cmd_validate_geometry(_print_args(model, bed="250x210x200", min_wall=12.0))
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "fits 250 x 210 x 200 mm as modeled" in out
    assert "below 12 mm" in out


def test_validate_geometry_rejects_malformed_bed(tmp_path, capsys):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)

    assert cmd_validate_geometry(_print_args(model, bed="junk")) == 1
    assert "--bed expects XxYxZ" in capsys.readouterr().err


# --- --set parameter overrides (TCAD-UX-15) ---

_PARAM_MODEL = """
parameters:
  t: 10
parts:
  box:
    primitive: box
    size: [40, 40, '${t}']
"""


def test_validate_geometry_set_overrides_parameter(tmp_path, capsys):
    model = tmp_path / "param.tiacad"
    model.write_text(_PARAM_MODEL)

    assert cmd_validate_geometry(_print_args(model, set=["t=3"])) == 0
    out = capsys.readouterr().out
    assert "Overrides: t=3" in out
    assert "thinnest sampled 3.00 mm" in out


def test_validate_geometry_without_set_uses_default_parameter(tmp_path, capsys):
    model = tmp_path / "param.tiacad"
    model.write_text(_PARAM_MODEL)

    assert cmd_validate_geometry(_print_args(model)) == 0
    out = capsys.readouterr().out
    assert "Overrides" not in out
    assert "thinnest sampled 10.00 mm" in out


@pytest.mark.parametrize("item", ["nope=1", "t"])
def test_validate_geometry_set_rejects_bad_item(tmp_path, capsys, item):
    model = tmp_path / "param.tiacad"
    model.write_text(_PARAM_MODEL)

    assert cmd_validate_geometry(_print_args(model, set=[item])) == 1
    assert "Validation failed" in capsys.readouterr().err
