"""Tests for `tiacad validate` (cmd_validate) — TCAD-VAL-9."""

from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_validate

_VALID_MODEL = """
parts:
  box:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
"""

_INVALID_MODEL = """
parts:
  box:
    primitive: not_a_real_primitive
"""


def _args(files):
    return SimpleNamespace(files=[str(f) for f in files])


def test_validate_all_valid_files_returns_zero(tmp_path, capsys):
    model = tmp_path / "good.tiacad"
    model.write_text(_VALID_MODEL)

    exit_code = cmd_validate(_args([model]))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "All files valid" in out


def test_validate_invalid_file_returns_one(tmp_path, capsys):
    model = tmp_path / "bad.tiacad"
    model.write_text(_INVALID_MODEL)

    exit_code = cmd_validate(_args([model]))
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "Invalid" in out


def test_validate_mixed_files_reports_both(tmp_path, capsys):
    good = tmp_path / "good.tiacad"
    good.write_text(_VALID_MODEL)
    bad = tmp_path / "bad.tiacad"
    bad.write_text(_INVALID_MODEL)

    exit_code = cmd_validate(_args([good, bad]))
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "✓ Valid:     1" in out or "Valid" in out
    assert "Invalid" in out


def test_validate_no_matching_files_fails(capsys):
    exit_code = cmd_validate(_args(["does_not_exist_*.tiacad"]))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No files to validate" in captured.out + captured.err
