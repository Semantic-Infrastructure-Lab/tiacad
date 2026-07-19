"""Tests for `tiacad validate-geometry` (cmd_validate_geometry) — TCAD-VAL-9."""

from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_validate_geometry

_SIMPLE_MODEL = """
parts:
  box:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
"""

# Two non-overlapping boxes unioned: a real disconnected-component case, the
# exact scenario this command exists to catch (see cli/validate_geometry.py
# module docstring: "union operations actually merge").
_DISCONNECTED_MODEL = """
parts:
  box_a:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
  box_b:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }

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
