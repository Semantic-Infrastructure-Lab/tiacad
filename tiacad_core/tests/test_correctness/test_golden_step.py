"""
Golden STEP Topology Gate (VALIDATION_STRENGTHENING.md section 4.9).

Volume/bbox contracts (test_embedded_contracts.py) and mesh-hash goldens
(test_determinism.py) can both miss a pure *topology* regression — a fillet
that silently stops applying to one edge, or a boolean that leaves an extra
sliver face — while volume and bbox stay within tolerance and the mesh hash
(tessellation-derived) doesn't change enough to trip. A committed STEP
export is an exact-geometry baseline for a small, curated set of anchor
models; this test rebuilds each one and compares its BREP topology (solid /
face / edge / vertex counts) against the golden file.

Deliberately small (see 4.9: "keep the set tiny") — this is a supplement to
the oracle-based contracts, not a replacement. Regenerate with
`scripts/generate_golden_steps.py` and review the diff; never auto-regenerate
from a test.
"""

from pathlib import Path

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.contracts import resolve_contract_part
from tiacad_core.testing.golden_step import (
    GoldenStepError,
    check_against_golden_step,
    topology_signature,
)

PROJECT_ROOT = Path(__file__).parents[3]
GOLDEN_DIR = PROJECT_ROOT / "examples" / "validation" / "golden_step"

# Keep in sync with scripts/generate_golden_steps.py's ANCHOR_MODELS.
ANCHOR_MODELS = [
    "examples/validation/T1_chamfer.tiacad",
    "examples/validation/T1_fillet.tiacad",
    "examples/validation/T3_lego_2x1.tiacad",
    "examples/validation/T3_bracket_fillet.tiacad",
    "examples/validation/T4_bolted_bracket.tiacad",
]


def _golden_path(model_path: str) -> Path:
    return GOLDEN_DIR / (Path(model_path).stem + ".step")


def test_anchor_list_is_not_empty():
    """Guards against a silently-empty list (e.g. everything commented out)."""
    assert ANCHOR_MODELS, "ANCHOR_MODELS is empty — the golden STEP gate has nothing to check."


@pytest.mark.parametrize("model_path", ANCHOR_MODELS, ids=lambda p: Path(p).name)
def test_golden_step_exists(model_path):
    golden = _golden_path(model_path)
    assert golden.exists(), (
        f"{golden.relative_to(PROJECT_ROOT)} does not exist — run "
        f"'python scripts/generate_golden_steps.py --model {model_path}' and review the diff."
    )


@pytest.mark.parametrize("model_path", ANCHOR_MODELS, ids=lambda p: Path(p).name)
def test_topology_matches_golden_step(model_path):
    golden = _golden_path(model_path)
    if not golden.exists():
        pytest.skip(f"{golden.name} missing — covered by test_golden_step_exists")

    doc = TiaCADParser.parse_file(model_path)
    expect = getattr(doc, "expect", {}) or {}
    part, part_name = resolve_contract_part(doc, expect)

    try:
        diffs = check_against_golden_step(part, str(golden))
    except GoldenStepError as e:
        pytest.fail(str(e))

    assert not diffs, (
        f"{Path(model_path).name} (part={part_name!r}) topology drifted from "
        f"{golden.name}: " + "; ".join(diffs) + " — if this is a deliberate "
        "geometry change, regenerate with scripts/generate_golden_steps.py "
        "and review the diff."
    )


@pytest.mark.parametrize("model_path", ANCHOR_MODELS, ids=lambda p: Path(p).name)
def test_topology_signature_is_self_consistent(model_path):
    """Build twice; topology counts must agree run-to-run (no BREP nondeterminism)."""
    doc = TiaCADParser.parse_file(model_path)
    expect = getattr(doc, "expect", {}) or {}
    part_a, _ = resolve_contract_part(doc, expect)
    sig_a = topology_signature(part_a)

    doc2 = TiaCADParser.parse_file(model_path)
    part_b, _ = resolve_contract_part(doc2, expect)
    sig_b = topology_signature(part_b)

    assert sig_a.as_dict() == sig_b.as_dict(), (
        f"{Path(model_path).name}: topology signature is non-deterministic "
        f"across builds: {sig_a.as_dict()} != {sig_b.as_dict()}"
    )
