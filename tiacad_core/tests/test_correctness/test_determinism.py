"""
Determinism Gate (VALIDATION_STRENGTHENING.md section 4.4, Tier 2).

Proves the same YAML always produces the same geometry: build each model
from the corpus multiple times and assert stable volume, bounding box, and
mesh hash. OCCT tessellation and boolean ops can be non-deterministic; that
silently defeats every golden-based test (visual and mesh) with flaky
failures far from the actual cause, and would undermine any future
incremental-rebuild cache. Catching it here is cheap and pays for itself
immediately.

Two tiers of check:
  - Self-consistency (`test_build_is_self_consistent`): builds a model N
    times in this run and requires every build to agree. Needs no golden
    file — it catches non-determinism the moment it's introduced.
  - Golden comparison (`test_build_matches_golden`): compares one build
    against `golden_hashes.json`, a small reviewed baseline. Catches drift
    across sessions/CadQuery-kernel upgrades that self-consistency alone
    can't see (e.g. a same-run-stable but different-from-last-week hash).
    A missing golden entry is a failure, not a skip — regenerate it with
    `scripts/update_determinism_goldens.py` and review the diff.

Author: TIA
"""

import json
from pathlib import Path

import pytest

from tiacad_core.testing.contracts import discover_models_with_expect, resolve_contract_part
from tiacad_core.testing.determinism import (
    build_snapshot,
    check_against_golden,
    check_determinism,
)

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"
GOLDEN_PATH = Path(__file__).parent / "golden_hashes.json"


def _discovered_paths():
    return discover_models_with_expect(str(EXAMPLES_DIR))


def _project_relative(path: str) -> str:
    return str(Path(path).relative_to(EXAMPLES_DIR.parent))


@pytest.mark.parametrize("path", _discovered_paths(), ids=lambda p: Path(p).name)
def test_build_is_self_consistent(path):
    result = check_determinism(path, n=3)
    assert result.ok, result.summary()


def test_at_least_one_model_is_checked():
    """Guards against a silently-empty parametrize list (e.g. a glob typo)."""
    assert _discovered_paths(), (
        "No models found for the determinism gate — discover_models_with_expect() "
        "found nothing under examples/. Add an expect: block to a model or this "
        "file has nothing to guard."
    )


@pytest.mark.parametrize("path", _discovered_paths(), ids=lambda p: Path(p).name)
def test_build_matches_golden(path):
    if not GOLDEN_PATH.exists():
        pytest.fail(
            f"{GOLDEN_PATH} does not exist — run "
            "'python scripts/update_determinism_goldens.py' and review the diff."
        )
    goldens = json.loads(GOLDEN_PATH.read_text())
    rel = _project_relative(path)
    golden = goldens.get(rel)
    if golden is None:
        pytest.fail(
            f"{rel}: no golden entry in {GOLDEN_PATH.name} — run "
            f"'python scripts/update_determinism_goldens.py --model {rel}' and review the diff."
        )

    from tiacad_core.parser.tiacad_parser import TiaCADParser

    doc = TiaCADParser.parse_file(path)
    expect = getattr(doc, 'expect', {}) or {}
    _, part_name = resolve_contract_part(doc, expect)

    snapshot = build_snapshot(path, part_name)
    violations = check_against_golden(snapshot, part_name, golden)
    assert not violations, f"{rel}: " + "; ".join(f"[{v.check}] {v.message}" for v in violations)
