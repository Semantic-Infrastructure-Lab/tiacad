"""
Embedded expect: Contract Tests

Discovers every example file that declares a top-level `expect:` block and
checks it against the model's actual built geometry via a single generic
parametrized test — no per-example test code required.

See docs/developer/VALIDATION_STRENGTHENING.md section 4.1: the model
becomes the single source of truth for its own correctness.

Author: TIA
"""

from pathlib import Path

import pytest

from tiacad_core.parser import TiaCADParser
from tiacad_core.testing.contracts import (
    ContractError,
    check_contract,
    discover_models_with_expect,
)

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


def _discovered_paths():
    return discover_models_with_expect(str(EXAMPLES_DIR))


@pytest.mark.parametrize("path", _discovered_paths(), ids=lambda p: Path(p).name)
def test_embedded_contract(path):
    doc = TiaCADParser.parse_file(path)
    try:
        result = check_contract(doc)
    except ContractError as e:
        pytest.fail(f"{Path(path).name}: {e}")
    assert result.ok, f"{Path(path).name}: {result.summary()}"


def test_at_least_one_model_has_a_contract():
    """
    Guards against a silently-empty parametrize list (e.g. a glob typo) —
    if this ever fails, discover_models_with_expect() found zero examples
    with an expect: block, which defeats the point of this file.
    """
    assert _discovered_paths(), (
        "No examples declare an expect: block — add one to an example "
        "(see docs/developer/VALIDATION_STRENGTHENING.md section 4.1) or "
        "this test file has nothing to guard."
    )
