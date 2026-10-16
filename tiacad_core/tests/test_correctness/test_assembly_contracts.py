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


class TestClearanceEngine:
    """Synthetic coverage for contracts.py::_check_clearance (relations: - clearance: [a, b])."""

    @staticmethod
    def _doc(relation, offset=12.0, tol=None):
        # Two 10mm cubes along X: centres `offset` apart, so the true gap is offset - 10.
        a = _cq_part("a", cq.Workplane("XY").box(10, 10, 10))
        b = _cq_part("b", cq.Workplane("XY").center(offset, 0).box(10, 10, 10))
        expect = {"final": "a", "relations": [relation]}
        if tol:
            expect["tol"] = tol
        return TestNoOverlapEngine._FakeDoc({"a": a, "b": b}, expect)

    def test_gap_inside_min_max_passes(self):
        result = check_contract(self._doc({"clearance": ["a", "b"], "min": 1.5, "max": 2.5}))
        assert result.ok, result.summary()

    def test_gap_below_min_fails(self):
        result = check_contract(self._doc({"clearance": ["a", "b"], "min": 2.5}))
        assert not result.ok
        assert any(v.check == "clearance" and "below min" in v.message for v in result.violations)

    def test_gap_above_max_fails(self):
        result = check_contract(self._doc({"clearance": ["a", "b"], "max": 1.5}))
        assert not result.ok
        assert any(v.check == "clearance" and "above max" in v.message for v in result.violations)

    def test_tight_length_tol_distinguishes_close_values(self):
        # true gap 2.0: min=2.05 passes at the default 0.1 tol, fails at 0.01
        rel = {"clearance": ["a", "b"], "min": 2.05}
        assert check_contract(self._doc(rel)).ok
        assert not check_contract(self._doc(rel, tol={"length": 0.01})).ok

    def test_touching_parts_fail_a_positive_min_with_note(self):
        result = check_contract(self._doc({"clearance": ["a", "b"], "min": 0.5}, offset=10.0))
        assert not result.ok
        assert "touch or interpenetrate" in result.violations[0].message

    def test_interpenetrating_parts_measure_zero(self):
        result = check_contract(self._doc({"clearance": ["a", "b"], "min": 0.5}, offset=5.0))
        assert not result.ok

    def test_requires_min_or_max(self):
        result = check_contract(self._doc({"clearance": ["a", "b"]}))
        assert not result.ok
        assert "min / max" in result.violations[0].message

    def test_missing_part_is_a_violation_not_a_crash(self):
        result = check_contract(self._doc({"clearance": ["a", "nope"], "min": 1}))
        assert not result.ok
        assert any(v.check == "clearance" for v in result.violations)

    def test_bad_pair_is_a_violation(self):
        result = check_contract(self._doc({"clearance": ["a"], "min": 1}))
        assert not result.ok


class TestThicknessContract:
    """expect: thickness: {min: mm} (contracts.py::_check_thickness), against a shelled box
    whose every wall is exactly 1.0 mm."""

    @staticmethod
    def _doc(thickness, tol=None, wall=1.0):
        shelled = cq.Workplane("XY").box(20, 20, 20).faces(">Z").shell(-wall)
        expect = {"final": "box", "thickness": thickness}
        if tol:
            expect["tol"] = tol
        return TestNoOverlapEngine._FakeDoc({"box": _cq_part("box", shelled)}, expect)

    def test_wall_at_or_above_min_passes(self):
        assert check_contract(self._doc({"min": 0.8})).ok
        assert check_contract(self._doc({"min": 1.0})).ok

    def test_wall_below_min_fails_with_measured_value_and_location(self):
        result = check_contract(self._doc({"min": 1.5}))
        assert not result.ok
        violation = next(v for v in result.violations if v.check == "thickness")
        assert "1.0" in violation.message and "below min 1.5" in violation.message and "near (" in violation.message

    def test_length_tol_is_slack_on_the_minimum(self):
        # 1.0 mm wall vs min 1.05: passes at the default 0.1 tol, fails at 0.01
        assert check_contract(self._doc({"min": 1.05})).ok
        assert not check_contract(self._doc({"min": 1.05}, tol={"length": 0.01})).ok

    def test_thinner_wall_is_caught(self):
        assert not check_contract(self._doc({"min": 0.8}, wall=0.5)).ok

    @pytest.mark.parametrize("bad", [{}, {"min": "thin"}, {"max": 2}, "0.8", None])
    def test_malformed_spec_is_a_violation_not_a_crash(self, bad):
        result = check_contract(self._doc(bad))
        assert not result.ok
        assert any(v.check == "thickness" for v in result.violations)


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
