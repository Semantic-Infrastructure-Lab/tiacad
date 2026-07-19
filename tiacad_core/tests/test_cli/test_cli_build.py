"""Tests for `tiacad build` (cmd_build) — TCAD-VAL-9.

The primary user-facing entrypoint (parse -> export -> stats) had no direct
test; only its helpers (`_common.py`) and other commands were covered.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_build

_SIMPLE_MODEL = """
parts:
  box:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
"""


def _args(input_path, output=None, part=None, stats=False, validate_schema=False,
          show_deps=None, verbose=False):
    return SimpleNamespace(
        input=str(input_path), output=output, part=part, stats=stats,
        validate_schema=validate_schema, show_deps=show_deps, verbose=verbose,
    )


@pytest.fixture
def simple_model(tmp_path):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)
    return model


def test_build_default_output_succeeds(simple_model, capsys):
    exit_code = cmd_build(_args(simple_model))
    assert exit_code == 0
    output = simple_model.with_suffix(".3mf")
    assert output.exists()
    assert output.stat().st_size > 0
    assert "Exporting" in capsys.readouterr().out


def test_build_explicit_output_and_format(simple_model, tmp_path):
    output = tmp_path / "out.stl"
    exit_code = cmd_build(_args(simple_model, output=str(output)))
    assert exit_code == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_build_with_stats_prints_statistics(simple_model, tmp_path, capsys):
    output = tmp_path / "out.stl"
    exit_code = cmd_build(_args(simple_model, output=str(output), stats=True))
    assert exit_code == 0
    assert "Statistics" in capsys.readouterr().out or "Parts" in capsys.readouterr().out


def test_build_missing_file_fails(capsys):
    exit_code = cmd_build(_args("does_not_exist.tiacad"))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.out + captured.err


def test_build_parse_error_fails(tmp_path, capsys):
    model = tmp_path / "bad.tiacad"
    model.write_text("parts:\n  box:\n    primitive: not_a_real_primitive\n")
    exit_code = cmd_build(_args(model))
    assert exit_code == 1


def test_build_with_constraints_exports_constrained_geometry(tmp_path):
    """The exact scenario TCAD-VAL-11 added parser-level coverage for, now
    through the real CLI entrypoint end to end."""
    model = tmp_path / "constrained.tiacad"
    model.write_text("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  top:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center

constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]

export:
  default_part: top
""")
    output = tmp_path / "top.stl"
    exit_code = cmd_build(_args(model, output=str(output), part="top"))
    assert exit_code == 0

    import trimesh
    mesh = trimesh.load(str(output))
    assert mesh.bounds[0][2] == pytest.approx(5.0, abs=0.05)
    assert mesh.bounds[1][2] == pytest.approx(10.0, abs=0.05)
