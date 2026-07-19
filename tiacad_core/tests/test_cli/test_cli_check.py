"""Tests for `tiacad check` (cmd_check) — TCAD-VAL-9."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_check

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"

_SIMPLE_MODEL = """
parts:
  box:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
"""


def _args(input_path, verbose=False, contract=False):
    return SimpleNamespace(input=str(input_path), verbose=verbose, contract=contract)


@pytest.fixture
def simple_model(tmp_path):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)
    return model


def test_check_reports_dimensions_and_volume(simple_model, capsys):
    exit_code = cmd_check(_args(simple_model))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "box" in out
    assert "1,000" in out or "1000" in out  # 10*10*10 volume


def test_check_missing_file_fails(capsys):
    exit_code = cmd_check(_args("does_not_exist.tiacad"))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.out + captured.err


def test_check_with_passing_contract_succeeds(capsys):
    exit_code = cmd_check(_args(EXAMPLES_DIR / "validation" / "T0_sphere.tiacad", contract=True))
    assert exit_code == 0


def test_check_with_failing_contract_fails(tmp_path, capsys):
    model = tmp_path / "bad_contract.tiacad"
    model.write_text("""
parts:
  block:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
export:
  default_part: block
expect:
  final: block
  volume: 9999
  tol: { volume: 0.01 }
""")
    exit_code = cmd_check(_args(model, contract=True))
    assert exit_code == 1
