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

import cadquery as cq
import pytest

from tiacad_core.parser import TiaCADParser
from tiacad_core.part import Part
from tiacad_core.geometry import CadQueryBackend
from tiacad_core.testing.contracts import (
    ContractError,
    check_contract,
    count_solids,
    discover_models_with_expect,
    get_manifold_stats,
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


class TestSolidCounting:
    """The `expect: components:` gate counts disjoint bodies at the BREP/kernel
    level (count_solids), not mesh islands.

    See docs/developer/VALIDATION_STRENGTHENING.md section 4.6 "Critical detail":
    mesh-island counting over-counts a hollow body with an enclosed cavity (two
    surface shells → 2 islands), and the is_watertight fallback can't catch two
    truly disjoint bodies (both are watertight). BREP Solids() is correct for
    both. These tests lock in that distinction so it can't silently regress.
    """

    def _part(self, name, wp):
        return Part(name=name, geometry=wp, backend=CadQueryBackend())

    def test_solid_box_is_one_solid(self):
        part = self._part("box", cq.Workplane("XY").box(20, 20, 20))
        assert count_solids(part) == 1

    def test_hollow_body_with_enclosed_cavity_is_one_solid(self):
        # 20mm cube minus a fully enclosed 10mm cube void: one hollow solid.
        # Mesh-island counting reports 2 (outer + inner shell) — the false
        # positive that motivated the BREP fix. count_solids must say 1.
        outer = cq.Workplane("XY").box(20, 20, 20)
        inner = cq.Workplane("XY").box(10, 10, 10)
        hollow = self._part("hollow", outer.cut(inner))

        assert count_solids(hollow) == 1
        stats = get_manifold_stats(hollow)
        assert stats["components"] == 1           # BREP: the correct signal
        assert stats["mesh_islands"] == 2         # mesh: the misleading one
        assert stats["watertight"] is True

    def test_two_disjoint_solids_are_counted_as_two(self):
        # Two separated boxes: both watertight, so is_watertight can't tell them
        # apart from one body. BREP Solids() correctly reports 2.
        a = cq.Workplane("XY").box(10, 10, 10)
        b = cq.Workplane("XY").center(30, 0).box(10, 10, 10)
        part = self._part("disjoint", a.add(b))

        assert count_solids(part) == 2
        stats = get_manifold_stats(part)
        assert stats["components"] == 2
        assert stats["watertight"] is True        # weaker check would pass this
