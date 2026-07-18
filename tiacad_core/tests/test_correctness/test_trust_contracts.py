"""
Trust Scenario Geometric Contracts

Contracts for the curated trust YAML files in examples/trust/.

As of 2026-07-18 (VALIDATION_STRENGTHENING.md section 4.7), every
single-final-part trust scenario (primitives, booleans, finishing, revolve,
loft, sweep, hull, patterns) carries its own embedded `expect:` block and is
discovered and checked automatically by test_embedded_contracts.py's generic
sweep — no per-example test code needed. This mirrors the 2026-07-11 trim of
the Tier-2 example classes (see that file's history): a hand-written
volume/bbox assertion here would just be a strictly weaker duplicate of the
contract (the old ±100mm³/±30% bound checks vs. the contract's exact or
near-exact reviewed values). See each trust YAML's `expect:` block for the
reviewed ground truth and derivation notes.

What remains here are the assembly-style scenarios that build *multiple*
independent, un-merged parts (no single "final" solid for `expect:` to
target) and whose value is in the *relationships between parts* — flush
contact, centering, symmetric placement, per-instance dimensions — which the
single-part contract mechanism doesn't express.

Axis mapping (box primitive → get_dimensions):
  YAML width  → X → dims['width']
  YAML depth  → Y → dims['height']
  YAML height → Z → dims['depth']
"""

import math
import pytest
from pathlib import Path

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.dimensions import get_dimensions

TRUST = Path(__file__).parents[3] / "examples" / "trust"

TOL = 0.5      # mm — CadQuery tessellation tolerance
VOL_TOL = 100  # mm³ — for simple geometry with exact formulas


def _parse(filename: str):
    return TiaCADParser.parse_file(str(TRUST / filename))


# ---------------------------------------------------------------------------
# Assemblies (multiple un-merged parts — no single expect: target)
# ---------------------------------------------------------------------------

class TestTrustStackedBoxes:
    """stacked_boxes.yaml: bottom 60×40×20, top 40×30×15 flush at Z=+10"""

    def _doc(self):
        return _parse("stacked_boxes.yaml")

    def test_bottom_dimensions(self):
        dims = get_dimensions(self._doc().parts.get("bottom"))
        assert dims["width"]  == pytest.approx(60.0, abs=TOL)
        assert dims["height"] == pytest.approx(40.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_bottom_volume(self):
        dims = get_dimensions(self._doc().parts.get("bottom"))
        assert dims["volume"] == pytest.approx(48_000.0, abs=VOL_TOL)

    def test_top_dimensions(self):
        dims = get_dimensions(self._doc().parts.get("top"))
        assert dims["width"]  == pytest.approx(40.0, abs=TOL)
        assert dims["height"] == pytest.approx(30.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(15.0, abs=TOL)

    def test_top_volume(self):
        dims = get_dimensions(self._doc().parts.get("top"))
        assert dims["volume"] == pytest.approx(18_000.0, abs=VOL_TOL)

    def test_top_flush_on_bottom(self):
        """top.min_Z must equal bottom.max_Z (flush contact, no gap, no overlap)."""
        doc = self._doc()
        bottom_bounds = doc.parts.get("bottom").get_bounds()
        top_bounds    = doc.parts.get("top").get_bounds()
        # bottom centered, h=20: Z=-10 to +10
        assert bottom_bounds["max"][2] == pytest.approx(10.0, abs=TOL)
        # top translated to Z=17.5, half-height 7.5: Z=10 to +25
        assert top_bounds["min"][2]    == pytest.approx(10.0, abs=TOL)


class TestTrustCylinderOnPlate:
    """cylinder_on_plate.yaml: plate 80×60×5, cylinder r=10 h=25 centered on top"""

    def _doc(self):
        return _parse("cylinder_on_plate.yaml")

    def test_plate_dimensions(self):
        # YAML: width=80(X), depth=60(Y→height), height=5(Z→depth)
        dims = get_dimensions(self._doc().parts.get("plate"))
        assert dims["width"]  == pytest.approx(80.0, abs=TOL)
        assert dims["height"] == pytest.approx(60.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(5.0,  abs=TOL)

    def test_plate_volume(self):
        dims = get_dimensions(self._doc().parts.get("plate"))
        assert dims["volume"] == pytest.approx(24_000.0, abs=VOL_TOL)

    def test_post_dimensions(self):
        # Cylinder r=10, h=25: bbox 20×20 in XY, 25 in Z
        dims = get_dimensions(self._doc().parts.get("post"))
        assert dims["width"]  == pytest.approx(20.0, abs=TOL)
        assert dims["height"] == pytest.approx(20.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(25.0, abs=TOL)

    def test_post_volume(self):
        dims = get_dimensions(self._doc().parts.get("post"))
        assert dims["volume"] == pytest.approx(math.pi * 10**2 * 25, abs=VOL_TOL)

    def test_post_flush_on_plate(self):
        """Cylinder base must align exactly with plate top face (Z=+2.5)."""
        doc = self._doc()
        plate_bounds = doc.parts.get("plate").get_bounds()
        post_bounds  = doc.parts.get("post").get_bounds()
        # plate centered, height=5: Z=-2.5 to +2.5
        assert plate_bounds["max"][2] == pytest.approx(2.5, abs=TOL)
        # post translated to Z=15, half-height=12.5: Z=+2.5 to +27.5
        assert post_bounds["min"][2]  == pytest.approx(2.5, abs=TOL)

    def test_post_centered_on_plate_xy(self):
        """Cylinder centroid must coincide with plate centroid in XY."""
        doc = self._doc()
        plate_b = doc.parts.get("plate").get_bounds()
        post_b  = doc.parts.get("post").get_bounds()
        plate_cx = (plate_b["min"][0] + plate_b["max"][0]) / 2
        plate_cy = (plate_b["min"][1] + plate_b["max"][1]) / 2
        post_cx  = (post_b["min"][0]  + post_b["max"][0])  / 2
        post_cy  = (post_b["min"][1]  + post_b["max"][1])  / 2
        assert post_cx == pytest.approx(plate_cx, abs=TOL)
        assert post_cy == pytest.approx(plate_cy, abs=TOL)


class TestTrustSideBySide:
    """side_by_side.yaml: two 30×20×20 boxes at X=±25, 20mm gap between them"""

    def _doc(self):
        return _parse("side_by_side.yaml")

    def test_left_dimensions(self):
        dims = get_dimensions(self._doc().parts.get("left"))
        assert dims["width"]  == pytest.approx(30.0, abs=TOL)
        assert dims["height"] == pytest.approx(20.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_right_dimensions(self):
        dims = get_dimensions(self._doc().parts.get("right"))
        assert dims["width"]  == pytest.approx(30.0, abs=TOL)
        assert dims["height"] == pytest.approx(20.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_equal_volumes(self):
        doc = self._doc()
        left_vol  = get_dimensions(doc.parts.get("left"))["volume"]
        right_vol = get_dimensions(doc.parts.get("right"))["volume"]
        assert left_vol  == pytest.approx(12_000.0, abs=VOL_TOL)
        assert right_vol == pytest.approx(12_000.0, abs=VOL_TOL)

    def test_gap_between_boxes(self):
        """20mm gap: left ends at X=-10, right starts at X=+10."""
        doc = self._doc()
        left_b  = doc.parts.get("left").get_bounds()
        right_b = doc.parts.get("right").get_bounds()
        assert left_b["max"][0]  == pytest.approx(-10.0, abs=TOL)
        assert right_b["min"][0] == pytest.approx(+10.0, abs=TOL)

    def test_same_vertical_extent(self):
        """Both boxes share identical Z bounds (same height, no stacking)."""
        doc = self._doc()
        left_b  = doc.parts.get("left").get_bounds()
        right_b = doc.parts.get("right").get_bounds()
        assert left_b["min"][2] == pytest.approx(right_b["min"][2], abs=TOL)
        assert left_b["max"][2] == pytest.approx(right_b["max"][2], abs=TOL)


class TestTrustThreePartAssembly:
    """three_part_assembly.yaml: plate 100×40×8, two posts r=8 h=35 at X=±35"""

    def _doc(self):
        return _parse("three_part_assembly.yaml")

    def test_base_dimensions(self):
        dims = get_dimensions(self._doc().parts.get("base"))
        assert dims["width"]  == pytest.approx(100.0, abs=TOL)
        assert dims["height"] == pytest.approx(40.0,  abs=TOL)
        assert dims["depth"]  == pytest.approx(8.0,   abs=TOL)

    def test_base_volume(self):
        dims = get_dimensions(self._doc().parts.get("base"))
        assert dims["volume"] == pytest.approx(32_000.0, abs=VOL_TOL)

    def test_post_volumes(self):
        doc = self._doc()
        expected = math.pi * 8**2 * 35  # ≈ 7,037
        for name in ("post_left", "post_right"):
            vol = get_dimensions(doc.parts.get(name))["volume"]
            assert vol == pytest.approx(expected, abs=VOL_TOL), f"{name} volume wrong"

    def test_posts_symmetric(self):
        """post_left centroid X = -35, post_right centroid X = +35."""
        doc = self._doc()
        left_b  = doc.parts.get("post_left").get_bounds()
        right_b = doc.parts.get("post_right").get_bounds()
        left_cx  = (left_b["min"][0]  + left_b["max"][0])  / 2
        right_cx = (right_b["min"][0] + right_b["max"][0]) / 2
        assert left_cx  == pytest.approx(-35.0, abs=TOL)
        assert right_cx == pytest.approx(+35.0, abs=TOL)

    def test_posts_sit_on_plate(self):
        """Post bases must align with plate top face."""
        doc = self._doc()
        plate_top_z = doc.parts.get("base").get_bounds()["max"][2]
        for name in ("post_left", "post_right"):
            post_min_z = doc.parts.get(name).get_bounds()["min"][2]
            assert post_min_z == pytest.approx(plate_top_z, abs=TOL), (
                f"{name} base Z={post_min_z:.2f} != plate top Z={plate_top_z:.2f}"
            )


# ---------------------------------------------------------------------------
# Patterns (multi-instance — no single mergeable "final" part)
# ---------------------------------------------------------------------------

class TestTrustLinearPattern:
    """
    linear_pattern.yaml: 20×20×20 box × 5 along X at 30mm spacing.
    Pattern produces individual parts: row_0 … row_4 (not a merged 'row').
    """

    _INSTANCES = ["row_0", "row_1", "row_2", "row_3", "row_4"]

    def _doc(self):
        return _parse("linear_pattern.yaml")

    def test_all_instances_present(self):
        doc = self._doc()
        for name in self._INSTANCES:
            assert doc.parts.get(name) is not None, f"{name} not found"

    def test_each_instance_volume(self):
        """Each of the 5 boxes is 20×20×20 = 8,000mm³."""
        doc = self._doc()
        for name in self._INSTANCES:
            vol = get_dimensions(doc.parts.get(name))["volume"]
            assert vol == pytest.approx(8_000.0, abs=VOL_TOL), f"{name} volume wrong"

    def test_row_spans_multiple_boxes(self):
        """5 boxes at 30mm center-to-center: row_0 at X=0, row_4 at X=120.
        Total span from -10 to +130 = 140mm."""
        doc = self._doc()
        first_b = doc.parts.get("row_0").get_bounds()
        last_b  = doc.parts.get("row_4").get_bounds()
        x_span = last_b["max"][0] - first_b["min"][0]
        assert x_span == pytest.approx(140.0, abs=2.0)


# ---------------------------------------------------------------------------
# Complex assembly (stdlib imports)
# ---------------------------------------------------------------------------

class TestTrustPcbStandoffAssembly:
    """pcb_standoff_assembly.yaml: plate + 4 standoffs + PCB + 4 screws via stdlib"""

    def _doc(self):
        return _parse("pcb_standoff_assembly.yaml")

    def test_plate_dimensions(self):
        """plate: W=100(X), H=80(Y, YAML depth→Y), D=5(Z, YAML height→Z, the thickness)."""
        dims = get_dimensions(self._doc().parts.get("plate"))
        assert dims["width"]  == pytest.approx(100.0, abs=TOL)
        assert dims["height"] == pytest.approx(80.0,  abs=TOL)
        assert dims["depth"]  == pytest.approx(5.0,   abs=TOL)

    def test_plate_volume(self):
        dims = get_dimensions(self._doc().parts.get("plate"))
        assert dims["volume"] == pytest.approx(40_000.0, abs=VOL_TOL)

    def test_standoffs_correct_height(self):
        """All 4 standoffs: h=10mm (depth in get_dims since height→Z)."""
        doc = self._doc()
        for name in ("standoff_fl", "standoff_fr", "standoff_bl", "standoff_br"):
            dims = get_dimensions(doc.parts.get(name))
            assert dims["depth"] == pytest.approx(10.0, abs=TOL), f"{name} wrong height"

    def test_all_parts_positive_volume(self):
        doc = self._doc()
        for name in ("plate", "pcb",
                     "standoff_fl", "standoff_fr", "standoff_bl", "standoff_br",
                     "screw_fl", "screw_fr", "screw_bl", "screw_br"):
            vol = get_dimensions(doc.parts.get(name))["volume"]
            assert vol > 0, f"{name}: zero or negative volume"
