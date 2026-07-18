"""Tests for `tiacad measure` (cmd_measure).

Implements TCAD-UX-3: distances/angles/alignment between two named spatial
references, as a CLI dev-loop tool (console + --json output).
"""

import json
from pathlib import Path
from types import SimpleNamespace

from tiacad_core.cli import cmd_measure

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


def _args(input_path, ref1, ref2, json_out=False, verbose=False):
    return SimpleNamespace(input=str(input_path), ref1=ref1, ref2=ref2, json=json_out, verbose=verbose)


def test_measure_distance_and_angle_oriented_refs(capsys):
    exit_code = cmd_measure(_args(
        EXAMPLES_DIR / "auto_references_box_stack.yaml",
        "base.face_top", "middle.face_bottom",
    ))
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "distance:" in out
    assert "angle:" in out
    assert "aligned:" in out


def test_measure_json_output_stacked_faces(capsys):
    exit_code = cmd_measure(_args(
        EXAMPLES_DIR / "auto_references_box_stack.yaml",
        "base.face_top", "middle.face_bottom",
        json_out=True,
    ))
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["distance"] == 7.5  # middle box height / 2
    assert payload["angle_deg"] == 180.0  # opposing faces, touching
    assert payload["alignment"]["aligned"] is True
    assert payload["alignment"]["parallel"] is True


def test_measure_bare_points_skip_angle(capsys):
    exit_code = cmd_measure(_args(
        EXAMPLES_DIR / "auto_references_box_stack.yaml",
        "base.center", "middle.center",
    ))
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "distance:" in captured.out
    assert "angle/alignment skipped" in captured.out


def test_measure_bare_points_json_omits_angle(capsys):
    exit_code = cmd_measure(_args(
        EXAMPLES_DIR / "auto_references_box_stack.yaml",
        "base.center", "middle.center",
        json_out=True,
    ))
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert "distance" in payload
    assert "angle_deg" not in payload
    assert "alignment" not in payload


def test_measure_missing_file_fails(capsys):
    exit_code = cmd_measure(_args("does_not_exist.yaml", "a.center", "b.center"))
    assert exit_code == 1
    assert "File not found" in capsys.readouterr().err


def test_measure_invalid_reference_fails(capsys):
    exit_code = cmd_measure(_args(
        EXAMPLES_DIR / "auto_references_box_stack.yaml",
        "base.nonexistent", "middle.center",
    ))
    assert exit_code == 1
    assert "Failed to resolve references" in capsys.readouterr().err
