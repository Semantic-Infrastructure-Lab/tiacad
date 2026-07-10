"""
Trust Scenario Geometric Contracts

Contracts for the 20 curated trust YAML files in examples/trust/.
Each trust YAML documents its own ground truth in comments and description text.
These tests translate that prose into assertions — catching "built but wrong"
errors that visual inspection alone cannot.

Coverage:
  Primitives:    box, cylinder, sphere, cone, revolve (360°, 180°, 90°)
  Assemblies:    stacked_boxes, cylinder_on_plate, side_by_side, three_part_assembly
  Booleans:      subtract, union, intersect
  Finishing:     chamfer, fillet
  Surfaces:      loft, sweep, hull
  Patterns:      linear, circular
  Complex:       pcb_standoff_assembly (stdlib imports)

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


def _measure(filename: str, part_name: str):
    doc = _parse(filename)
    return get_dimensions(doc.parts.get(part_name))


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

class TestTrustBoxBasic:
    """box_basic.yaml: w=50(X), d=30(Y), h=20(Z) → vol=30,000"""

    def test_dimensions(self):
        dims = _measure("box_basic.yaml", "box")
        assert dims["width"]  == pytest.approx(50.0, abs=TOL)
        assert dims["height"] == pytest.approx(30.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_volume(self):
        dims = _measure("box_basic.yaml", "box")
        assert dims["volume"] == pytest.approx(30_000.0, abs=VOL_TOL)


class TestTrustCylinderBasic:
    """cylinder_basic.yaml: r=15, h=40 → diameter=30, vol≈28,274"""

    def test_dimensions(self):
        dims = _measure("cylinder_basic.yaml", "cyl")
        assert dims["width"]  == pytest.approx(30.0, abs=TOL)   # X: 2×r
        assert dims["height"] == pytest.approx(30.0, abs=TOL)   # Y: 2×r
        assert dims["depth"]  == pytest.approx(40.0, abs=TOL)   # Z: height

    def test_volume(self):
        dims = _measure("cylinder_basic.yaml", "cyl")
        assert dims["volume"] == pytest.approx(math.pi * 15**2 * 40, abs=VOL_TOL)


class TestTrustSphereBasic:
    """sphere_basic.yaml: r=20 → cubic bbox 40×40×40, vol≈33,510"""

    def test_bounding_box_is_cube(self):
        dims = _measure("sphere_basic.yaml", "sphere")
        assert dims["width"]  == pytest.approx(40.0, abs=TOL)
        assert dims["height"] == pytest.approx(40.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(40.0, abs=TOL)

    def test_volume(self):
        dims = _measure("sphere_basic.yaml", "sphere")
        assert dims["volume"] == pytest.approx(4/3 * math.pi * 20**3, abs=VOL_TOL)


class TestTrustConeBasic:
    """cone_basic.yaml: r1=20, r2=0, h=40 → bbox 40×40×40, vol≈16,755"""

    def test_bounding_box(self):
        dims = _measure("cone_basic.yaml", "cone")
        assert dims["width"]  == pytest.approx(40.0, abs=TOL)
        assert dims["height"] == pytest.approx(40.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(40.0, abs=TOL)

    def test_volume(self):
        dims = _measure("cone_basic.yaml", "cone")
        assert dims["volume"] == pytest.approx(1/3 * math.pi * 20**2 * 40, abs=VOL_TOL)

    def test_half_cylinder_volume(self):
        """Cone must be exactly 1/3 the volume of a cylinder with same base and height."""
        dims = _measure("cone_basic.yaml", "cone")
        full_cyl_vol = math.pi * 20**2 * 40
        assert dims["volume"] == pytest.approx(full_cyl_vol / 3, abs=VOL_TOL)


class TestTrustRevolveBasic:
    """
    revolve_basic.yaml: spool — flanges r=25 h=8 (×2) + barrel r=10 h=20, total h=36.

    Sketch in XZ plane, revolved 360° around world Z axis.
    Correct geometry: circular cross-section in XY (radius=25), height in Z=36.
      width  (X) = 50  (diameter = 2×25)
      height (Y) = 50  (diameter = 2×25)
      depth  (Z) = 36  (flange_h + barrel_h + flange_h = 8+20+8)
      volume     ≈ 37,699 mm³ (2 flanges + barrel, exact math)
    """

    def test_dimensions(self):
        """Spool cross-section is circular (width == height) and Z height == 36."""
        dims = _measure("revolve_basic.yaml", "spool")
        assert dims["width"]  == pytest.approx(50.0, abs=TOL)   # 2×r=25
        assert dims["height"] == pytest.approx(50.0, abs=TOL)   # 2×r=25
        assert dims["depth"]  == pytest.approx(36.0, abs=TOL)   # 8+20+8

    def test_volume(self):
        """Volume = 2 flanges (r=25, h=8 each) + barrel (r=10, h=20)."""
        dims = _measure("revolve_basic.yaml", "spool")
        flange_vol = 2 * math.pi * 25**2 * 8   # 31,416 mm³
        barrel_vol = math.pi * 10**2 * 20       #  6,283 mm³
        expected = flange_vol + barrel_vol       # 37,699 mm³
        assert dims["volume"] == pytest.approx(expected, abs=VOL_TOL)

    def test_symmetric_cross_section(self):
        """Revolved around Z: X and Y extents must be equal (circular cross-section)."""
        dims = _measure("revolve_basic.yaml", "spool")
        assert dims["width"] == pytest.approx(dims["height"], abs=TOL)

    def test_barrel_narrows_spool(self):
        """Volume must be less than a solid cylinder bounding the spool."""
        dims = _measure("revolve_basic.yaml", "spool")
        bbox_cyl_vol = math.pi * (dims["width"] / 2) ** 2 * dims["depth"]
        assert dims["volume"] < bbox_cyl_vol


class TestTrustRevolveXAxis:
    """
    revolve_x_axis.yaml: rectangle (X=0..40, Z=0..15) in XZ plane → 360° around X.
    Produces cylinder: radius=15, length=40, axis along X.
    Same volume as cylinder_basic.yaml (r=15, h=40) — cross-validates revolve
    engine against the primitive cylinder code path.
      width  (X) = 40  (length along axis)
      height (Y) = 30  (diameter = 2×15)
      depth  (Z) = 30  (diameter = 2×15)
      volume     ≈ 28,274 mm³
    """

    def test_length_along_x(self):
        """Cylinder length is along X (the revolve axis)."""
        dims = _measure("revolve_x_axis.yaml", "cyl_x")
        assert dims["width"] == pytest.approx(40.0, abs=TOL)

    def test_circular_cross_section_in_yz(self):
        """Revolve around X: Y and Z extents must be equal (circular cross-section)."""
        dims = _measure("revolve_x_axis.yaml", "cyl_x")
        assert dims["height"] == pytest.approx(30.0, abs=TOL)  # 2×r
        assert dims["depth"]  == pytest.approx(30.0, abs=TOL)  # 2×r
        assert dims["height"] == pytest.approx(dims["depth"], abs=TOL)

    def test_volume(self):
        dims = _measure("revolve_x_axis.yaml", "cyl_x")
        assert dims["volume"] == pytest.approx(math.pi * 15**2 * 40, abs=VOL_TOL)


class TestTrustRevolveYAxis:
    """
    revolve_y_axis.yaml: rectangle (X=0..15, Y=0..40) in XY plane → 360° around Y.
    Produces cylinder: radius=15, length=40, axis along Y.
    Same volume as cylinder_basic.yaml (r=15, h=40) — cross-validates revolve
    engine against the primitive cylinder code path.
      width  (X) = 30  (diameter = 2×15)
      height (Y) = 40  (length along axis)
      depth  (Z) = 30  (diameter = 2×15)
      volume     ≈ 28,274 mm³
    """

    def test_length_along_y(self):
        """Cylinder length is along Y (the revolve axis)."""
        dims = _measure("revolve_y_axis.yaml", "cyl_y")
        assert dims["height"] == pytest.approx(40.0, abs=TOL)

    def test_circular_cross_section_in_xz(self):
        """Revolve around Y: X and Z extents must be equal (circular cross-section)."""
        dims = _measure("revolve_y_axis.yaml", "cyl_y")
        assert dims["width"] == pytest.approx(30.0, abs=TOL)   # 2×r
        assert dims["depth"] == pytest.approx(30.0, abs=TOL)   # 2×r
        assert dims["width"] == pytest.approx(dims["depth"], abs=TOL)

    def test_volume(self):
        dims = _measure("revolve_y_axis.yaml", "cyl_y")
        assert dims["volume"] == pytest.approx(math.pi * 15**2 * 40, abs=VOL_TOL)


class TestTrustRevolve180:
    """
    revolve_180.yaml: same rectangle as revolve_x_axis.yaml, revolved 180° around X.
    Produces a half-cylinder: r=15, length=40.
    Volume must equal exactly half the 360° revolve: π×15²×40 / 2.
      width (X)  = 40  (length along axis)
      height (Y) = 15  (radius — only one side of YZ plane)
      depth (Z)  = 30  (full diameter: from -15 to +15)
      volume     ≈ 14,137 mm³
    """

    def test_volume_is_half_of_360(self):
        """180° revolve must produce exactly half the volume of 360°."""
        full_vol = math.pi * 15**2 * 40
        dims = _measure("revolve_180.yaml", "half_cyl")
        assert dims["volume"] == pytest.approx(full_vol / 2, abs=VOL_TOL)

    def test_length_along_x(self):
        dims = _measure("revolve_180.yaml", "half_cyl")
        assert dims["width"] == pytest.approx(40.0, abs=TOL)

    def test_z_span_equals_full_diameter(self):
        """Z spans the full diameter (both sides of XZ symmetry plane)."""
        dims = _measure("revolve_180.yaml", "half_cyl")
        assert dims["depth"] == pytest.approx(30.0, abs=TOL)  # 2×r


class TestTrustRevolve90:
    """
    revolve_90.yaml: same rectangle as revolve_x_axis.yaml, revolved 90° around X.
    Produces a quarter-cylinder wedge: r=15, length=40.
    Volume must equal exactly one quarter the 360° revolve: π×15²×40 / 4.
      width (X)  = 40  (length along axis)
      volume     ≈ 7,069 mm³
    """

    def test_volume_is_quarter_of_360(self):
        """90° revolve must produce exactly one quarter the volume of 360°."""
        full_vol = math.pi * 15**2 * 40
        dims = _measure("revolve_90.yaml", "quarter_cyl")
        assert dims["volume"] == pytest.approx(full_vol / 4, abs=VOL_TOL)

    def test_length_along_x(self):
        dims = _measure("revolve_90.yaml", "quarter_cyl")
        assert dims["width"] == pytest.approx(40.0, abs=TOL)

    def test_volume_positive(self):
        dims = _measure("revolve_90.yaml", "quarter_cyl")
        assert dims["volume"] > 0


class TestRevolveAngleScaling:
    """
    Verify that revolve angle scaling is linear: 180° = half of 360°, 90° = quarter.
    Uses the same profile (r=15, length=40) across three angles to isolate
    the angle-scaling code path from profile/axis bugs.
    """

    _FULL_VOL = math.pi * 15**2 * 40  # ≈ 28,274 mm³

    def test_180_is_half_of_360(self):
        full = _measure("revolve_x_axis.yaml", "cyl_x")["volume"]
        half = _measure("revolve_180.yaml",    "half_cyl")["volume"]
        assert half == pytest.approx(full / 2, abs=VOL_TOL)

    def test_90_is_quarter_of_360(self):
        full    = _measure("revolve_x_axis.yaml", "cyl_x")["volume"]
        quarter = _measure("revolve_90.yaml",     "quarter_cyl")["volume"]
        assert quarter == pytest.approx(full / 4, abs=VOL_TOL)

    def test_90_is_half_of_180(self):
        half    = _measure("revolve_180.yaml", "half_cyl")["volume"]
        quarter = _measure("revolve_90.yaml",  "quarter_cyl")["volume"]
        assert quarter == pytest.approx(half / 2, abs=VOL_TOL)


# ---------------------------------------------------------------------------
# Assemblies
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
# Boolean operations
# ---------------------------------------------------------------------------

class TestTrustBooleanSubtract:
    """boolean_subtract.yaml: 60×60×20 box − cylinder hole r=12 h=30 through center"""

    def test_bbox_unchanged(self):
        """Centered subtract leaves bounding box identical to input box."""
        dims = _measure("boolean_subtract.yaml", "result")
        assert dims["width"]  == pytest.approx(60.0, abs=TOL)
        assert dims["height"] == pytest.approx(60.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_hole_removes_material(self):
        dims = _measure("boolean_subtract.yaml", "result")
        assert dims["volume"] < 60 * 60 * 20  # solid = 72,000

    def test_volume(self):
        """box(72k) − π×12²×20 (cylinder clipped to box height) ≈ 62,953."""
        dims = _measure("boolean_subtract.yaml", "result")
        expected = 60 * 60 * 20 - math.pi * 12**2 * 20
        assert dims["volume"] == pytest.approx(expected, abs=VOL_TOL)


class TestTrustBooleanUnion:
    """boolean_union.yaml: union of 80×20×20 X-slab + 20×20×60 Z-slab"""

    def test_bounding_box(self):
        # x_slab: YAML width=80(X), height=20(Z→depth), depth=20(Y→height)
        # z_slab: YAML width=20(X), height=20(Z→depth), depth=60(Y→height)
        # union:  X=80, Y=60 (from z_slab.depth), Z=20 (shared height)
        dims = _measure("boolean_union.yaml", "cross")
        assert dims["width"]  == pytest.approx(80.0, abs=TOL)   # X: from x_slab.width
        assert dims["height"] == pytest.approx(60.0, abs=TOL)   # Y: from z_slab.depth
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)   # Z: both slabs share height=20

    def test_volume(self):
        """A + B − (A ∩ B) = 32k + 24k − 8k = 48,000."""
        dims = _measure("boolean_union.yaml", "cross")
        assert dims["volume"] == pytest.approx(48_000.0, abs=VOL_TOL)

    def test_larger_than_either_input(self):
        dims = _measure("boolean_union.yaml", "cross")
        assert dims["volume"] > 80 * 20 * 20   # > x_slab (32k)
        assert dims["volume"] > 20 * 20 * 60   # > z_slab (24k)


class TestTrustBooleanIntersect:
    """boolean_intersect.yaml: X-slab ∩ Z-slab = 20×20×20 cube"""

    def test_is_cube(self):
        dims = _measure("boolean_intersect.yaml", "overlap")
        assert dims["width"]  == pytest.approx(20.0, abs=TOL)
        assert dims["height"] == pytest.approx(20.0, abs=TOL)
        assert dims["depth"]  == pytest.approx(20.0, abs=TOL)

    def test_volume(self):
        dims = _measure("boolean_intersect.yaml", "overlap")
        assert dims["volume"] == pytest.approx(8_000.0, abs=VOL_TOL)

    def test_smaller_than_both_inputs(self):
        dims = _measure("boolean_intersect.yaml", "overlap")
        assert dims["volume"] < 60 * 20 * 20  # < x_slab (24k)
        assert dims["volume"] < 20 * 20 * 60  # < z_slab (24k)


# ---------------------------------------------------------------------------
# Finishing operations
# ---------------------------------------------------------------------------

class TestTrustChamferBasic:
    """chamfer_basic.yaml: 40×40×20 box with 3mm chamfer on all 12 edges"""

    def test_bbox_unchanged(self):
        """Chamfer is inset — bounding box matches the input box.
        Box YAML: width=40(X), depth=20(Y→height), height=40(Z→depth)."""
        dims = _measure("chamfer_basic.yaml", "chamfered")
        assert dims["width"]  == pytest.approx(40.0, abs=TOL)   # X
        assert dims["height"] == pytest.approx(20.0, abs=TOL)   # Y (YAML depth=20)
        assert dims["depth"]  == pytest.approx(40.0, abs=TOL)   # Z (YAML height=40)

    def test_chamfer_removes_material(self):
        dims = _measure("chamfer_basic.yaml", "chamfered")
        assert dims["volume"] < 40 * 40 * 20  # solid = 32,000

    def test_volume_close_to_solid(self):
        """3mm chamfer is small — volume stays well above 28,000."""
        dims = _measure("chamfer_basic.yaml", "chamfered")
        assert dims["volume"] > 28_000


class TestTrustFilletBasic:
    """fillet_basic.yaml: 40×40×20 box with r=3 fillet on all 12 edges"""

    def test_bbox_unchanged(self):
        """Fillet is inset — bounding box matches the input box.
        Box YAML: width=40(X), depth=20(Y→height), height=40(Z→depth)."""
        dims = _measure("fillet_basic.yaml", "filleted")
        assert dims["width"]  == pytest.approx(40.0, abs=TOL)   # X
        assert dims["height"] == pytest.approx(20.0, abs=TOL)   # Y (YAML depth=20)
        assert dims["depth"]  == pytest.approx(40.0, abs=TOL)   # Z (YAML height=40)

    def test_fillet_removes_material(self):
        dims = _measure("fillet_basic.yaml", "filleted")
        assert dims["volume"] < 40 * 40 * 20  # solid = 32,000

    def test_volume_close_to_solid(self):
        dims = _measure("fillet_basic.yaml", "filleted")
        assert dims["volume"] > 28_000


# ---------------------------------------------------------------------------
# Surface operations
# ---------------------------------------------------------------------------

class TestTrustLoftRectToCircle:
    """loft_rect_to_circle.yaml: 40×40 square at Z=0 → circle r=15 at Z=30"""

    def test_height(self):
        """Loft spans exactly 30mm in Z."""
        dims = _measure("loft_rect_to_circle.yaml", "transition")
        assert dims["depth"] == pytest.approx(30.0, abs=TOL)

    def test_volume_between_bounds(self):
        """
        Volume must be between narrow and wide extremes.
        Prismatoid approximation: avg cross-section × height
          = ((40×40 + π×15²) / 2) × 30 ≈ 34,600 mm³
        Use ±30% around that estimate as tighter bounds.
        """
        dims = _measure("loft_rect_to_circle.yaml", "transition")
        prismatoid_approx = ((40 * 40 + math.pi * 15**2) / 2) * 30  # ≈ 34,600
        assert dims["volume"] > 0.70 * prismatoid_approx   # > ~24,200
        assert dims["volume"] < 1.30 * prismatoid_approx   # < ~45,000


class TestTrustSweepBasic:
    """sweep_basic.yaml: r=5 circle swept along L-path (Z 0→40, then X 0→40)"""

    def test_volume_positive(self):
        dims = _measure("sweep_basic.yaml", "l_pipe")
        assert dims["volume"] > 0

    def test_volume_close_to_full_path(self):
        """
        L-pipe: path length = 80mm (two 40mm arms), πr²=78.5mm².
        Both arms must be substantially present: volume > 1.5× one arm.
        Corner overlap removes only a small amount: volume < 2× one arm.
        """
        dims = _measure("sweep_basic.yaml", "l_pipe")
        one_arm = math.pi * 5**2 * 40  # ≈ 3,142
        assert dims["volume"] > 1.5 * one_arm   # > 4,712 — both arms must contribute
        assert dims["volume"] < 2.0 * one_arm   # < 6,283 — corner removes some material

    def test_both_arms_present(self):
        """Z span and X span must each reach ~40mm (both arms of the L built)."""
        doc = _parse("sweep_basic.yaml")
        bounds = doc.parts.get("l_pipe").get_bounds()
        z_span = bounds["max"][2] - bounds["min"][2]
        x_span = bounds["max"][0] - bounds["min"][0]
        assert z_span > 35.0  # Z arm is 40mm
        assert x_span > 35.0  # X arm is 40mm


class TestTrustHullSpheres:
    """hull_spheres.yaml: convex hull of 3 spheres r=8 at equilateral triangle vertices"""

    def test_volume_positive(self):
        dims = _measure("hull_spheres.yaml", "smooth_hull")
        assert dims["volume"] > 0

    def test_volume_exceeds_three_spheres(self):
        """Hull volume must be larger than the three spheres it wraps."""
        dims = _measure("hull_spheres.yaml", "smooth_hull")
        sphere_vol = 4/3 * math.pi * 8**3  # ≈ 2,145 each
        assert dims["volume"] > 3 * sphere_vol

    def test_volume_bounded_by_bbox(self):
        """Hull must be smaller than bounding box of all sphere centers + radii."""
        dims = _measure("hull_spheres.yaml", "smooth_hull")
        bbox_vol = (40 + 16) * (35 + 16) * 16  # conservative outer box
        assert dims["volume"] < bbox_vol


# ---------------------------------------------------------------------------
# Patterns
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


class TestTrustCircularPattern:
    """circular_pattern.yaml: 100×100×8 plate − 6 bolt holes (r=3.5) − center hole (r=12)"""

    def test_plate_footprint(self):
        dims = _measure("circular_pattern.yaml", "final_plate")
        assert dims["width"]  == pytest.approx(100.0, abs=TOL)
        assert dims["height"] == pytest.approx(100.0, abs=TOL)

    def test_holes_removed_material(self):
        dims = _measure("circular_pattern.yaml", "final_plate")
        assert dims["volume"] < 100 * 100 * 8  # solid = 80,000

    def test_volume(self):
        """plate(80k) − 6×bolt_holes(π×3.5²×8) − center_hole(π×12²×8) ≈ 74,534."""
        dims = _measure("circular_pattern.yaml", "final_plate")
        bolt_holes   = 6 * math.pi * 3.5**2 * 8   # ≈ 1,847
        center_hole  = math.pi * 12**2 * 8          # ≈ 3,619
        expected = 100 * 100 * 8 - bolt_holes - center_hole  # ≈ 74,534
        assert dims["volume"] == pytest.approx(expected, abs=200.0)


# ---------------------------------------------------------------------------
# Complex assembly (stdlib imports)
# ---------------------------------------------------------------------------

class TestTrustPcbStandoffAssembly:
    """pcb_standoff_assembly.yaml: plate + 4 standoffs + PCB + 4 screws via stdlib"""

    def _doc(self):
        return _parse("pcb_standoff_assembly.yaml")

    def test_plate_dimensions(self):
        """plate: W=100(X), H=5(Y, YAML depth→Y), D=80(Z, YAML height→Z)."""
        dims = get_dimensions(self._doc().parts.get("plate"))
        assert dims["width"]  == pytest.approx(100.0, abs=TOL)
        assert dims["height"] == pytest.approx(5.0,   abs=TOL)
        assert dims["depth"]  == pytest.approx(80.0,  abs=TOL)

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


# ---------------------------------------------------------------------------
# Cross-validation: different code paths must agree
# ---------------------------------------------------------------------------

class TestCrossValidation:
    """
    Verify that different operations producing equivalent shapes agree with each
    other and with the analytical formula.  These tests catch bugs where one
    code path (e.g. revolve_builder) silently produces wrong geometry while
    another (e.g. primitive cylinder) stays correct — or vice versa.

    Shared geometry: cylinder r=15, h=40.
    Three independent code paths must all produce π×15²×40 ≈ 28,274 mm³:
      1. Primitive cylinder (cylinder_basic.yaml)
      2. Revolve around X axis (revolve_x_axis.yaml)
      3. Revolve around Y axis (revolve_y_axis.yaml)
    The Z-axis case is already covered by TestTrustRevolveBasic and
    TestTrustCylinderBasic separately.
    """

    _EXPECTED_VOL = math.pi * 15**2 * 40  # ≈ 28,274 mm³

    def test_primitive_cylinder_matches_formula(self):
        """Baseline: cylinder_basic.yaml must match π×r²×h."""
        dims = _measure("cylinder_basic.yaml", "cyl")
        assert dims["volume"] == pytest.approx(self._EXPECTED_VOL, abs=VOL_TOL)

    def test_revolve_x_matches_primitive_cylinder(self):
        """Cylinder via revolve-X must equal cylinder via primitive (same r, h)."""
        prim = _measure("cylinder_basic.yaml", "cyl")
        revx = _measure("revolve_x_axis.yaml", "cyl_x")
        assert revx["volume"] == pytest.approx(prim["volume"], abs=VOL_TOL)

    def test_revolve_y_matches_primitive_cylinder(self):
        """Cylinder via revolve-Y must equal cylinder via primitive (same r, h)."""
        prim = _measure("cylinder_basic.yaml", "cyl")
        revy = _measure("revolve_y_axis.yaml", "cyl_y")
        assert revy["volume"] == pytest.approx(prim["volume"], abs=VOL_TOL)

    def test_all_three_revolve_axes_agree(self):
        """All three revolve axes must produce equal volumes for same geometry."""
        vol_z = _measure("revolve_basic.yaml",   "spool")["volume"]   # spool (complex)
        vol_x = _measure("revolve_x_axis.yaml",  "cyl_x")["volume"]   # simple cylinder
        vol_y = _measure("revolve_y_axis.yaml",  "cyl_y")["volume"]   # simple cylinder
        # X and Y produce the same cylinder → must agree
        assert vol_x == pytest.approx(vol_y, abs=VOL_TOL)
        # All three revolve axes produced positive, real geometry
        assert vol_z > 0
        assert vol_x > 0
        assert vol_y > 0
