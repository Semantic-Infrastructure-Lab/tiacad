"""Tests for `tiacad info` (cmd_info) — TCAD-VAL-9."""

from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_info

_SIMPLE_MODEL = """
parameters:
  size: 10

parts:
  box:
    primitive: box
    parameters: { width: "${size}", height: 10, depth: 10 }

operations:
  moved:
    type: transform
    input: box
    transforms:
      - translate: [5, 0, 0]
"""


def _args(input_path, verbose=False):
    return SimpleNamespace(input=str(input_path), verbose=verbose)


@pytest.fixture
def simple_model(tmp_path):
    model = tmp_path / "model.tiacad"
    model.write_text(_SIMPLE_MODEL)
    return model


def test_info_reports_parts_operations_and_parameters(simple_model, capsys):
    exit_code = cmd_info(_args(simple_model))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "box" in out
    assert "moved" in out
    assert "size" in out
    assert "Statistics" in out


def test_info_missing_file_fails(capsys):
    exit_code = cmd_info(_args("does_not_exist.tiacad"))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.out + captured.err


def test_info_parse_error_fails(tmp_path, capsys):
    model = tmp_path / "bad.tiacad"
    model.write_text("parts:\n  box:\n    primitive: not_a_real_primitive\n")
    exit_code = cmd_info(_args(model))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Failed to read file" in captured.out + captured.err
