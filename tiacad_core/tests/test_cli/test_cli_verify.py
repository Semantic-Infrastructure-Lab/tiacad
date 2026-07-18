"""Tests for `tiacad verify` (cmd_verify).

Implements docs/developer/MODEL_VALIDATION.md "Best Next Improvements" #3:
evaluate a model's embedded expect: contract and emit a console summary plus,
with --json, a machine-readable result.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tiacad_core.cli import cmd_verify

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


def _args(input_path, json_out=False, verbose=False):
    return SimpleNamespace(input=str(input_path), json=json_out, verbose=verbose)


def test_verify_passing_contract_returns_zero(capsys):
    exit_code = cmd_verify(_args(EXAMPLES_DIR / "validation" / "T0_sphere.tiacad"))
    assert exit_code == 0
    assert "contract OK" in capsys.readouterr().out


def test_verify_passing_contract_json_output(capsys):
    exit_code = cmd_verify(_args(EXAMPLES_DIR / "validation" / "T0_sphere.tiacad", json_out=True))
    assert exit_code == 0

    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{"):])
    assert payload["ok"] is True
    assert payload["part_name"] == "ball"
    assert payload["violations"] == []


def test_verify_no_contract_block_fails(capsys):
    exit_code = cmd_verify(_args(EXAMPLES_DIR / "color_demo.yaml"))
    assert exit_code == 1
    assert "no expect: block" in capsys.readouterr().err


def test_verify_missing_file_fails(capsys):
    exit_code = cmd_verify(_args("does_not_exist.tiacad"))
    assert exit_code == 1
    assert "File not found" in capsys.readouterr().err


def test_verify_violated_contract_reports_failure_json(tmp_path, capsys):
    model = tmp_path / "bad_contract.tiacad"
    model.write_text(
        """
schema_version: "3.0"
metadata:
  name: Bad Contract Test
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
"""
    )

    exit_code = cmd_verify(_args(model, json_out=True))
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "contract FAILED" in captured.err
    payload = json.loads(captured.out[captured.out.index("{"):])
    assert payload["ok"] is False
    assert payload["violations"] == [
        {"check": "volume", "message": "actual=1000.0000 expected=9999 (tol 0.0100)"}
    ]
