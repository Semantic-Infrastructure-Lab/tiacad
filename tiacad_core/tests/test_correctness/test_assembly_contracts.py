"""
Tier 4 — Assembly relational contracts (VALIDATION_STRENGTHENING.md section 3).

Proves parts are in the right place *relative to each other* -- the thing
single-part volume/bbox and visual regression both miss. The Tier 4 corpus
(`examples/validation/T4_*.tiacad`, plus `examples/pcb_standoff_assembly.yaml`
and `examples/hardware_assembly_demo.yaml`) is already discovered and checked
by the generic `test_embedded_contracts.py::test_embedded_contract` -- every
model with an `expect:` block, `relations:` included, is validated there with
no per-example test code required (the whole point of section 4.1). This file
does NOT duplicate that generic sweep.

What this file adds instead is direct, synthetic regression coverage for the
contract *engine* pieces that are new as of this session and have no other
direct unit test:

  - `no_overlap` (VALIDATION_STRENGTHENING.md section 3's "no-interpenetration"
    check): sum of two named parts' volumes must equal the volume of their
    union, within tolerance. Built from first principles here (not read off
    an example) so a broken implementation that vacuously passes on every
    corpus model would still be caught.
  - The Tier 4 corpus's specific relation claims, hand-verified independently
    of `check_contract` (direct `get_bounds()` calls) as a second, less
    trusting check on top of the generic contract sweep.

Author: TIA
"""

from pathlib import Path

import cadquery as cq
import pytest

from tiacad_core.geometry import CadQueryBackend
from tiacad_core.parser import TiaCADParser
from tiacad_core.part import Part
from tiacad_core.testing.contracts import check_contract

VALIDATION_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "validation"
EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


def _cq_part(name: str, wp: cq.Workplane) -> Part:
    return Part(name=name, geometry=wp, backend=CadQueryBackend())


class TestNoOverlapEngine:
    """Direct, synthetic coverage for contracts.py::_check_no_overlap (via check_contract),
    since it's new code not otherwise unit-tested outside the Tier 4 corpus."""

    class _FakeDoc:
        """Minimal stand-in for a TiaCADDocument -- only the attributes
        check_contract() reads (parts, references, operations, export_config, expect)."""

        def __init__(self, parts_dict, expect):
            from tiacad_core.part import PartRegistry

            self.parts = PartRegistry()
            for p in parts_dict.values():
                self.parts.add(p)
            self.references = {}
            self.operations = {}
            self.export_config = {"default_part": next(iter(parts_dict))}
            self.expect = expect

    def test_touching_boxes_pass_no_overlap(self):
        # Two 10mm cubes, side by side, sharing exactly one face -- no shared volume.
        a = _cq_part("a", cq.Workplane("XY").box(10, 10, 10))
        b = _cq_part("b", cq.Workplane("XY").center(10, 0).box(10, 10, 10))
        doc = self._FakeDoc(
            {"a": a, "b": b},
            {"final": "a", "no_overlap": [["a", "b"]]},
        )
        result = check_contract(doc)
        assert result.ok, result.summary()

    def test_disjoint_boxes_pass_no_overlap(self):
        # Two 10mm cubes with a gap between them -- also no shared volume.
        a = _cq_part("a", cq.Workplane("XY").box(10, 10, 10))
        b = _cq_part("b", cq.Workplane("XY").center(50, 0).box(10, 10, 10))
        doc = self._FakeDoc(
            {"a": a, "b": b},
            {"final": "a", "no_overlap": [["a", "b"]]},
        )
        result = check_contract(doc)
        assert result.ok, result.summary()

    def test_interpenetrating_boxes_fail_no_overlap(self):
        # Two 10mm cubes overlapping by 5mm along X -- a real, positive-volume
        # interpenetration. This is the negative control: if this test ever
        # starts passing, the engine has stopped detecting the bug class it
        # exists for.
        a = _cq_part("a", cq.Workplane("XY").box(10, 10, 10))
        b = _cq_part("b", cq.Workplane("XY").center(5, 0).box(10, 10, 10))
        doc = self._FakeDoc(
            {"a": a, "b": b},
            {"final": "a", "no_overlap": [["a", "b"]]},
        )
        result = check_contract(doc)
        assert not result.ok
        assert any(v.check == "no_overlap" for v in result.violations)

    def test_missing_part_in_pair_is_a_violation_not_a_crash(self):
        a = _cq_part("a", cq.Workplane("XY").box(10, 10, 10))
        doc = self._FakeDoc(
            {"a": a},
            {"final": "a", "no_overlap": [["a", "nonexistent"]]},
        )
        result = check_contract(doc)
        assert not result.ok
        assert any(v.check == "no_overlap" for v in result.violations)


class TestT4CorpusHandVerified:
    """Second, independently-derived check on the Tier 4 corpus's relational
    claims -- direct get_bounds() math, not a call through check_contract().
    Cross-checks the generic contract sweep in test_embedded_contracts.py
    rather than trusting it blindly (this session's stated verification bar)."""

    def test_two_boxes_flush_zero_gap(self):
        doc = TiaCADParser.parse_file(str(VALIDATION_DIR / "T4_two_boxes_flush.tiacad"))
        a = doc.parts.get("box_a").get_bounds()
        b = doc.parts.get("box_b").get_bounds()
        # box_a's +X face and box_b's -X face must coincide exactly.
        assert a["max"][0] == pytest.approx(b["min"][0], abs=1e-6)
        # No interpenetration: box_b starts exactly where box_a ends.
        assert b["min"][0] >= a["max"][0] - 1e-6

    def test_standoff_stack_is_coaxial_and_flush(self):
        doc = TiaCADParser.parse_file(str(VALIDATION_DIR / "T4_standoff_stack.tiacad"))
        plate = doc.parts.get("plate").get_bounds()
        standoff = doc.parts.get("standoff_pos").get_bounds()
        spacer = doc.parts.get("spacer_pos").get_bounds()
        screw = doc.parts.get("screw_pos").get_bounds()

        # Flush stacking: each interface has zero gap.
        assert plate["max"][2] == pytest.approx(standoff["min"][2], abs=1e-6)
        assert standoff["max"][2] == pytest.approx(spacer["min"][2], abs=1e-6)

        # Coaxial: all three share the same (X, Y) center line.
        for part_bounds in (standoff, spacer, screw):
            cx = (part_bounds["min"][0] + part_bounds["max"][0]) / 2
            cy = (part_bounds["min"][1] + part_bounds["max"][1]) / 2
            assert cx == pytest.approx(0.0, abs=1e-6)
            assert cy == pytest.approx(0.0, abs=1e-6)

    def test_bolted_bracket_shaft_clears_hole_and_head_sits_flush(self):
        doc = TiaCADParser.parse_file(str(VALIDATION_DIR / "T4_bolted_bracket.tiacad"))
        bracket = doc.parts.get("bracket_with_hole").get_bounds()
        head = doc.parts.get("bolt_head_pos").get_bounds()
        shaft = doc.parts.get("bolt_shaft_pos").get_bounds()

        # Head sits exactly flush on the bracket's top face.
        assert bracket["max"][2] == pytest.approx(head["min"][2], abs=1e-6)

        # Shaft radius stays within the hole radius (clearance fit, not a
        # collision) -- shaft's X/Y half-extent must be <= the hole's (3.0).
        shaft_radius = (shaft["max"][0] - shaft["min"][0]) / 2
        assert shaft_radius < 3.0

    def test_hardware_assembly_demo_heads_track_their_shafts(self):
        doc = TiaCADParser.parse_file(str(EXAMPLES_DIR / "hardware_assembly_demo.yaml"))
        for prefix in ("m3", "m4", "m5", "m6"):
            shaft = doc.parts.get(f"{prefix}_pos").get_bounds()
            head = doc.parts.get(f"{prefix}_head_pos").get_bounds()
            assert shaft["max"][2] == pytest.approx(head["min"][2], abs=1e-6), (
                f"{prefix}: shaft top {shaft['max'][2]} != head bottom {head['min'][2]} "
                "-- head has drifted away from its shaft again (KNOWN_LIMITATIONS.md #11)"
            )


def test_at_least_one_t4_model_present():
    """Guards against an empty/renamed corpus silently making this file's
    hand-verification tests vacuous (all `parse_file` calls above would
    FileNotFoundError individually, but this gives one clear signal)."""
    assert (VALIDATION_DIR / "T4_two_boxes_flush.tiacad").exists()
    assert (VALIDATION_DIR / "T4_standoff_stack.tiacad").exists()
    assert (VALIDATION_DIR / "T4_bolted_bracket.tiacad").exists()
