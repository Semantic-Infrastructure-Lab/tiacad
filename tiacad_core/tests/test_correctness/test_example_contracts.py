"""
Example Geometric Contracts

Tests that lock in the expected geometric output for example YAML files.
Catches "built but wrong" errors that visual regression cannot detect:
  - Wrong dimensions (a 50mm box built as 100mm)
  - Boolean that silently failed (volume unchanged after subtract)
  - Zero-volume geometry (sweep or revolve produced nothing)

Audit ground truth established 2026-03-15 (session: sutegaku-0315).
Bugs fixed same session: component_import_demo (translate dict syntax), pipe_sweep_simple (coplanar path).
Run `tiacad audit examples/*.yaml` to regenerate.

Two tiers:
  1. Volume sanity — all 44 buildable examples: final part has positive volume
  2. Dimensional contracts — key examples with independently verifiable values
"""

import pytest
from pathlib import Path

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.dimensions import get_dimensions

EXAMPLES = Path(__file__).parents[3] / "examples"


def _parse_and_measure_final(filename: str):
    """Parse a YAML, build it, return (dims_dict, final_part_name).

    Selection priority:
      1. Last operation result (most common — final boolean/transform)
      2. First visible part (fallback for part-only designs)
    """
    path = EXAMPLES / filename
    doc = TiaCADParser.parse_file(str(path))
    if doc.operations:
        final_name = list(doc.operations.keys())[-1]
    else:
        parts = [p for p in doc.parts.list_parts() if not p.startswith("_")]
        final_name = parts[0]
    part = doc.parts.get(final_name)
    dims = get_dimensions(part)
    return dims, final_name


# ---------------------------------------------------------------------------
# Tier 1: Volume sanity — every buildable example must have positive volume
# ---------------------------------------------------------------------------

# Ground truth from audit 2026-03-15. Volume > 0 = geometry was produced.
# fmt: off
BUILDABLE_EXAMPLES = [
    "anchors_demo.yaml",
    "auto_references_box_stack.yaml",
    "component_import_demo.yaml",
    "auto_references_cylinder_assembly.yaml",
    "auto_references_rotation.yaml",
    "auto_references_with_offsets.yaml",
    "awesome_guitar_hanger.yaml",
    "bottle_revolve.yaml",
    "bracket_with_hole.yaml",
    "chamfered_bracket.yaml",
    "color_demo.yaml",
    "color_showcase.yaml",
    "dag_test_simple.yaml",
    "enhanced_metadata_demo.yaml",
    "formats_demo.yaml",
    "guitar_hanger_named_points.yaml",
    "guitar_hanger_with_holes.yaml",
    "hardware_assembly_demo.yaml",
    "hull_enclosure.yaml",
    "hull_simple.yaml",
    "lego_brick_2x1.yaml",
    "lego_brick_3x1.yaml",
    "mounting_plate_with_bolt_circle.yaml",
    "multi_material_demo.yaml",
    "multi_material_enclosure.yaml",
    "pipe_sweep_simple.yaml",
    "references_demo.yaml",
    "rounded_mounting_plate.yaml",
    "simple_box.yaml",
    "simple_extrude.yaml",
    "simple_guitar_hanger.yaml",
    "text_engraved.yaml",
    "text_label.yaml",
    "text_operation_emboss_simple.yaml",
    "text_operation_multi_face.yaml",
    "text_operation_product_label.yaml",
    "text_primitive_sign.yaml",
    "text_primitive_simple.yaml",
    "text_primitive_styles.yaml",
    "text_primitive_vs_sketch.yaml",
    "text_simple.yaml",
    "transition_loft.yaml",
    "v3_bracket_mount.yaml",
    "v3_simple_box.yaml",
    "week5_align_to_face.yaml",
    "week5_assembly.yaml",
    "week5_frame_based_rotation.yaml",
]
# fmt: on

# Known failures — intentional or documented OCCT limitations, not TiaCAD bugs.
KNOWN_FAILURES = {
    "dag_test_cycle.yaml": "intentional: cycle detection test",
    "error_demo.yaml": "intentional: error handling demo",
    "pipe_sweep.yaml": "known OCCT limitation: boolean cut on swept geometry (Null TopoDS_Shape)",
}


@pytest.mark.parametrize("filename", BUILDABLE_EXAMPLES)
def test_example_builds_with_positive_volume(filename):
    """Every example in BUILDABLE_EXAMPLES must produce a final part with positive volume."""
    dims, final_name = _parse_and_measure_final(filename)
    assert dims["volume"] > 0, (
        f"{filename}: final part '{final_name}' has non-positive volume {dims['volume']:.2f} mm³ — "
        f"geometry was not produced (silent boolean failure, zero-depth extrude, or build error)"
    )


# ---------------------------------------------------------------------------
# Tier 2: Dimensional contracts — independently verifiable expected values
#
# These are examples where the expected geometry can be derived directly
# from the YAML parameters, not just "whatever the snapshot says."
# Tolerance: 0.5mm (CadQuery tessellation rounds small values).
# ---------------------------------------------------------------------------

TOL = 0.5  # mm tolerance for all dimensional checks
VOL_TOL = 50  # mm³ tolerance for volume checks


class TestSimpleBox:
    """simple_box.yaml: width=50, height=30, depth=20 → 50×30×20, vol=30,000"""

    def test_dimensions(self):
        dims, _ = _parse_and_measure_final("simple_box.yaml")
        # Bounding box: 50mm × 20mm × 30mm (audit confirmed)
        assert dims["width"] == pytest.approx(50.0, abs=TOL)

    def test_volume(self):
        dims, _ = _parse_and_measure_final("simple_box.yaml")
        assert dims["volume"] == pytest.approx(30_000.0, abs=VOL_TOL)


class TestSimpleExtrude:
    """simple_extrude.yaml: width=20, height=10, depth=5 → 20×10×5, vol=1,000"""

    def test_dimensions(self):
        dims, _ = _parse_and_measure_final("simple_extrude.yaml")
        assert dims["width"] == pytest.approx(20.0, abs=TOL)
        assert dims["height"] == pytest.approx(10.0, abs=TOL)

    def test_volume(self):
        dims, _ = _parse_and_measure_final("simple_extrude.yaml")
        assert dims["volume"] == pytest.approx(1_000.0, abs=VOL_TOL)


class TestAutoReferencesBoxStack:
    """auto_references_box_stack.yaml: three stacked boxes, each independently measurable."""

    def _parse(self):
        doc = TiaCADParser.parse_file(str(EXAMPLES / "auto_references_box_stack.yaml"))
        return doc

    def test_base_box_dimensions(self):
        doc = self._parse()
        part = doc.parts.get("base")
        dims = get_dimensions(part)
        assert dims["width"] == pytest.approx(100.0, abs=TOL)
        assert dims["height"] == pytest.approx(50.0, abs=TOL)
        assert dims["depth"] == pytest.approx(20.0, abs=TOL)

    def test_base_box_volume(self):
        doc = self._parse()
        part = doc.parts.get("base")
        dims = get_dimensions(part)
        assert dims["volume"] == pytest.approx(100_000.0, abs=VOL_TOL)

    def test_middle_box_dimensions(self):
        doc = self._parse()
        part = doc.parts.get("middle")
        dims = get_dimensions(part)
        assert dims["width"] == pytest.approx(80.0, abs=TOL)
        assert dims["height"] == pytest.approx(40.0, abs=TOL)
        assert dims["depth"] == pytest.approx(15.0, abs=TOL)

    def test_top_box_volume(self):
        doc = self._parse()
        part = doc.parts.get("top")
        dims = get_dimensions(part)
        assert dims["volume"] == pytest.approx(18_000.0, abs=VOL_TOL)


class TestBracketWithHole:
    """bracket_with_hole.yaml: extrude with subtract — volume must be less than solid."""

    def _parse(self):
        return TiaCADParser.parse_file(str(EXAMPLES / "bracket_with_hole.yaml"))

    def test_final_part_has_material_removed(self):
        """The hole subtract must actually reduce volume below a solid bracket."""
        doc = self._parse()
        bracket = doc.parts.get("bracket")
        dims = get_dimensions(bracket)
        # bracket_width=50, bracket_height=20, bracket_depth=10 → solid = 10,000 mm³
        solid_volume = 50 * 20 * 10
        assert dims["volume"] < solid_volume, (
            f"Hole subtract did not reduce volume: {dims['volume']:.1f} >= {solid_volume} mm³"
        )

    def test_final_part_volume_positive(self):
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bracket"))
        assert dims["volume"] > 0

    def test_final_part_volume_in_range(self):
        """Volume should be audit-verified ~9,214 mm³ (solid - hole cylinder)."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bracket"))
        assert dims["volume"] == pytest.approx(9_214.0, abs=100.0)


class TestV3SimpleBox:
    """v3_simple_box.yaml: base=100×100×10 (vol=100k), top=50×50×20 (vol=50k)."""

    def _parse(self):
        return TiaCADParser.parse_file(str(EXAMPLES / "v3_simple_box.yaml"))

    def test_base_volume(self):
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("base"))
        assert dims["volume"] == pytest.approx(100_000.0, abs=VOL_TOL)

    def test_top_volume(self):
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("top"))
        assert dims["volume"] == pytest.approx(50_000.0, abs=VOL_TOL)


class TestTransitionLoft:
    """transition_loft.yaml: loft between two profiles — must produce positive volume."""

    def test_volume_positive(self):
        dims, _ = _parse_and_measure_final("transition_loft.yaml")
        assert dims["volume"] > 0

    def test_volume_in_range(self):
        """Audit: ~5,371 mm³."""
        dims, _ = _parse_and_measure_final("transition_loft.yaml")
        assert dims["volume"] == pytest.approx(5_371.0, abs=200.0)


class TestFormatsDemo:
    """formats_demo.yaml: simple box exported in multiple formats — geometry must be correct."""

    def test_volume(self):
        dims, _ = _parse_and_measure_final("formats_demo.yaml")
        assert dims["volume"] == pytest.approx(50_000.0, abs=VOL_TOL)


class TestLegoMath:
    """Lego bricks: 2×1 and 3×1 should have correct relative volumes."""

    def test_3x1_larger_than_2x1(self):
        dims_2x1, _ = _parse_and_measure_final("lego_brick_2x1.yaml")
        dims_3x1, _ = _parse_and_measure_final("lego_brick_3x1.yaml")
        assert dims_3x1["volume"] > dims_2x1["volume"], (
            f"3×1 brick ({dims_3x1['volume']:.0f}) should be larger than 2×1 ({dims_2x1['volume']:.0f})"
        )

    def test_2x1_volume_in_range(self):
        """Audit: ~988 mm³."""
        dims, _ = _parse_and_measure_final("lego_brick_2x1.yaml")
        assert dims["volume"] == pytest.approx(988.0, abs=50.0)


class TestTextOperations:
    """Text operations must actually engrave/emboss: reduce/increase volume vs solid base."""

    def test_engraved_volume_below_solid(self):
        """text_engraved.yaml: engraving removes material from base plate."""
        dims, _ = _parse_and_measure_final("text_engraved.yaml")
        # Base plate is 100×60×5 = 30,000 mm³. Engraving reduces volume.
        assert dims["volume"] < 30_000.0, (
            f"Engraving did not remove material: volume {dims['volume']:.1f} >= 30,000 mm³"
        )
        assert dims["volume"] > 0

    def test_emboss_simple_positive_volume(self):
        """text_operation_emboss_simple.yaml: embossing must produce geometry."""
        dims, _ = _parse_and_measure_final("text_operation_emboss_simple.yaml")
        assert dims["volume"] > 0


class TestComponentImportDemo:
    """
    component_import_demo.yaml: wall panel assembly using imported components.

    Imports:
      - mounting_bracket.yaml as 'bracket' (width=60, base_depth=35, flange_height=50, thickness=5)
      - m3_screw.yaml as 'screw_short' (length=12) and 'screw_long' (length=25)

    Local parts:
      - panel: box width=200, depth=3 (panel_thickness), height=150
        → vol = 200 × 3 × 150 = 90,000 mm³

    Imported part ground truth (derived from component YAML + overrides):
      - bracket.base:   box  60 × 35 × 5  → vol = 10,500 mm³
      - bracket.flange: box  60 × 5  × 50 → vol = 15,000 mm³
      - screw_short.shaft: cylinder r=1.5, h=12
      - screw_long.shaft:  cylinder r=1.5, h=25
    """

    def _parse(self):
        doc = TiaCADParser.parse_file(str(EXAMPLES / "component_import_demo.yaml"))
        return doc

    def test_panel_dimensions(self):
        """Panel box: YAML width=200, depth=3, height=150.
        get_dimensions maps: X=width(200), Y=height(3), Z=depth(150).
        YAML 'depth' → CadQuery Y → dims['height'].
        YAML 'height' → CadQuery Z → dims['depth'].
        """
        doc = self._parse()
        part = doc.parts.get("panel")
        dims = get_dimensions(part)
        assert dims["width"] == pytest.approx(200.0, abs=TOL)   # X: YAML width
        assert dims["height"] == pytest.approx(3.0, abs=TOL)    # Y: YAML depth (panel_thickness)
        assert dims["depth"] == pytest.approx(150.0, abs=TOL)   # Z: YAML height

    def test_panel_volume(self):
        """Panel vol = 200 × 3 × 150 = 90,000 mm³."""
        doc = self._parse()
        part = doc.parts.get("panel")
        dims = get_dimensions(part)
        assert dims["volume"] == pytest.approx(90_000.0, abs=VOL_TOL)

    def test_bracket_base_dimensions(self):
        """bracket.base: YAML width=60, base_depth=35, thickness=5.
        dims: width(X)=60, height(Y)=35, depth(Z)=5.
        """
        doc = self._parse()
        part = doc.parts.get("bracket.base")
        dims = get_dimensions(part)
        assert dims["width"] == pytest.approx(60.0, abs=TOL)    # X
        assert dims["height"] == pytest.approx(35.0, abs=TOL)   # Y: base_depth
        assert dims["depth"] == pytest.approx(5.0, abs=TOL)     # Z: thickness

    def test_bracket_base_volume(self):
        """bracket.base vol = 60 × 35 × 5 = 10,500 mm³."""
        doc = self._parse()
        part = doc.parts.get("bracket.base")
        dims = get_dimensions(part)
        assert dims["volume"] == pytest.approx(10_500.0, abs=VOL_TOL)

    def test_bracket_flange_dimensions(self):
        """bracket.flange: YAML width=60, depth=thickness=5, height=flange_height=50.
        dims: width(X)=60, height(Y)=5, depth(Z)=50.
        """
        doc = self._parse()
        part = doc.parts.get("bracket.flange")
        dims = get_dimensions(part)
        assert dims["width"] == pytest.approx(60.0, abs=TOL)    # X
        assert dims["height"] == pytest.approx(5.0, abs=TOL)    # Y: thickness
        assert dims["depth"] == pytest.approx(50.0, abs=TOL)    # Z: flange_height

    def test_bracket_flange_volume(self):
        """bracket.flange vol = 60 × 5 × 50 = 15,000 mm³."""
        doc = self._parse()
        part = doc.parts.get("bracket.flange")
        dims = get_dimensions(part)
        assert dims["volume"] == pytest.approx(15_000.0, abs=VOL_TOL)

    def test_screw_short_shaft_height(self):
        """screw_short imported with length=12. Cylinder along Z: depth(Z)=12, width(X)=3mm diameter."""
        doc = self._parse()
        part = doc.parts.get("screw_short.shaft")
        dims = get_dimensions(part)
        assert dims["depth"] == pytest.approx(12.0, abs=TOL)    # Z: cylinder height
        assert dims["width"] == pytest.approx(3.0, abs=TOL)     # X: M3 diameter

    def test_screw_long_shaft_height(self):
        """screw_long imported with length=25. Cylinder along Z: depth(Z)=25."""
        doc = self._parse()
        part = doc.parts.get("screw_long.shaft")
        dims = get_dimensions(part)
        assert dims["depth"] == pytest.approx(25.0, abs=TOL)    # Z: cylinder height

    def test_parameter_override_isolation(self):
        """screw_short and screw_long have different lengths — imports are independent."""
        doc = self._parse()
        short = get_dimensions(doc.parts.get("screw_short.shaft"))
        long_ = get_dimensions(doc.parts.get("screw_long.shaft"))
        assert short["depth"] < long_["depth"], (
            f"screw_short ({short['depth']:.1f}mm) should be shorter than "
            f"screw_long ({long_['depth']:.1f}mm)"
        )


# ---------------------------------------------------------------------------
# Tier 2: hardware_assembly_demo — 25-part assembly geometric contracts
# ---------------------------------------------------------------------------

# Ground truth from `tiacad check examples/hardware_assembly_demo.yaml` 2026-03-16
# Axis convention: get_dimensions() → X=width, Y=height, Z=depth
# CadQuery maps: YAML width→X, YAML height→Y/Z depending on build orientation.
# plate: box with width=100, height=4 (thin), depth=80 → X=100, Y=4, Z=80

class TestHardwareAssemblyDemo:
    """
    hardware_assembly_demo.yaml: 25-part assembly using 6 imported components.

    Imported: m3_screw (shaft r=1.5, length=8), m4_screw (shaft r=2.0, length=16),
              m5_screw (shaft r=2.5, length=20), m6_bolt (shaft r=3.0, length=25),
              m3_washer (OD=7mm, thickness=0.5mm),
              m3_standoff (body OD=6mm, height=8mm).
    Local: plate box 100×4×80.
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(EXAMPLES / "hardware_assembly_demo.yaml"))

    def test_plate_dimensions(self):
        """Plate: width=100, thickness=4, depth=80 → vol=32,000mm³."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("plate"))
        assert dims["volume"] == pytest.approx(32_000.0, abs=VOL_TOL)
        assert dims["width"] == pytest.approx(100.0, abs=TOL)

    def test_m3_shaft_dimensions(self):
        """M3 screw shaft: radius=1.5mm (diameter=3mm), length=8mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("m3.shaft"))
        assert dims["width"] == pytest.approx(3.0, abs=TOL)    # diameter
        assert dims["depth"] == pytest.approx(8.0, abs=TOL)    # length

    def test_m4_shaft_dimensions(self):
        """M4 screw shaft: radius=2mm (diameter=4mm), length=16mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("m4.shaft"))
        assert dims["width"] == pytest.approx(4.0, abs=TOL)
        assert dims["depth"] == pytest.approx(16.0, abs=TOL)

    def test_m5_shaft_dimensions(self):
        """M5 screw shaft: radius=2.5mm (diameter=5mm), length=20mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("m5.shaft"))
        assert dims["width"] == pytest.approx(5.0, abs=TOL)
        assert dims["depth"] == pytest.approx(20.0, abs=TOL)

    def test_m6_shaft_dimensions(self):
        """M6 bolt shaft: radius=3mm (diameter=6mm), length=25mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("m6.shaft"))
        assert dims["width"] == pytest.approx(6.0, abs=TOL)
        assert dims["depth"] == pytest.approx(25.0, abs=TOL)

    def test_washer_outer_diameter(self):
        """M3 washer outer disc: OD=7mm, thickness=0.5mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("washer.disc"))
        assert dims["width"] == pytest.approx(7.0, abs=TOL)
        assert dims["depth"] == pytest.approx(0.5, abs=0.05)

    def test_washer_boolean_smaller_than_disc(self):
        """Boolean washer has bore removed — volume < disc volume."""
        doc = self._parse()
        disc_vol = get_dimensions(doc.parts.get("washer.disc"))["volume"]
        washer_vol = get_dimensions(doc.parts.get("washer.washer"))["volume"]
        assert washer_vol < disc_vol, "boolean subtract must remove material from washer"
        assert washer_vol > 0, "washer must have positive volume after subtract"

    def test_washer_volume(self):
        """M3 washer: π × (3.5² - 1.6²) × 0.5 ≈ 15.2 mm³."""
        import math
        expected = math.pi * (3.5**2 - 1.6**2) * 0.5
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("washer.washer"))
        assert dims["volume"] == pytest.approx(expected, abs=0.5)

    def test_standoff_height(self):
        """M3 standoff: height=8mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("standoff.body"))
        assert dims["depth"] == pytest.approx(8.0, abs=TOL)

    def test_standoff_outer_diameter(self):
        """M3 standoff body: OD=6mm (radius=3mm)."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("standoff.body"))
        assert dims["width"] == pytest.approx(6.0, abs=TOL)

    def test_standoff_boolean_smaller_than_body(self):
        """Boolean standoff has M3 bore — volume < body volume."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("standoff.body"))["volume"]
        standoff_vol = get_dimensions(doc.parts.get("standoff.standoff"))["volume"]
        assert standoff_vol < body_vol, "bore must remove material from standoff"
        assert standoff_vol > 0

    def test_all_25_parts_present(self):
        """All 25 parts build without error."""
        doc = self._parse()
        assert len(doc.parts.list_parts()) == 25


# ---------------------------------------------------------------------------
# Tier 2: m3_nut stdlib component — polygon primitive geometric contracts
# ---------------------------------------------------------------------------

import math as _math
_NUT_STDLIB = Path(__file__).parents[3] / "tiacad_core" / "stdlib" / "hardware" / "m3_nut.yaml"


class TestM3NutContracts:
    """
    tiacad_core/stdlib/hardware/m3_nut.yaml: ISO 4032 M3 hex nut.

    Parameters (defaults): diameter=6.35, thickness=2.4, bore_radius=1.5
    Expected geometry:
      - hex_body: hexagonal prism, circumscribed diameter=6.35, height=2.4
      - bore: cylinder r=1.5, height≈2.41 (slight oversize for clean cut)
      - nut (boolean difference): positive volume, outer = hex dims
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(_NUT_STDLIB))

    def test_hex_body_builds(self):
        doc = self._parse()
        assert doc.parts.get("hex_body") is not None

    def test_nut_has_positive_volume(self):
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("nut"))
        assert dims["volume"] > 0

    def test_nut_height_matches_thickness(self):
        """Thickness=2.4 → nut Z extent ≈ 2.4mm."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("nut"))
        assert dims["depth"] == pytest.approx(2.4, abs=TOL)

    def test_nut_volume_less_than_full_hex(self):
        """Bore must remove material — nut.vol < hex_body.vol."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("hex_body"))["volume"]
        nut_vol = get_dimensions(doc.parts.get("nut"))["volume"]
        assert nut_vol < body_vol

    def test_bore_volume_matches_formula(self):
        """bore: cylinder r=1.5, h≈2.41 → vol = π × 1.5² × 2.41 ≈ 17.0mm³."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bore"))
        expected = _math.pi * 1.5**2 * 2.41
        assert dims["volume"] == pytest.approx(expected, abs=0.5)


# Tier 2: m4_nut stdlib component
# ---------------------------------------------------------------------------

_M4_NUT_STDLIB = Path(__file__).parents[3] / "tiacad_core" / "stdlib" / "hardware" / "m4_nut.yaml"


class TestM4NutContracts:
    """
    tiacad_core/stdlib/hardware/m4_nut.yaml: ISO 4032 M4 hex nut.

    Parameters (defaults): diameter=8.08, thickness=3.2, bore_radius=2.0
    AF=7mm → circumscribed=7/cos(30°)≈8.08mm
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(_M4_NUT_STDLIB))

    def test_hex_body_builds(self):
        doc = self._parse()
        assert doc.parts.get("hex_body") is not None

    def test_nut_has_positive_volume(self):
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["volume"] > 0

    def test_nut_height_matches_thickness(self):
        """Thickness=3.2 → nut Z extent ≈ 3.2mm."""
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["depth"] == pytest.approx(3.2, abs=TOL)

    def test_nut_volume_less_than_hex_body(self):
        """Bore must remove material."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("hex_body"))["volume"]
        nut_vol = get_dimensions(doc.parts.get("nut"))["volume"]
        assert nut_vol < body_vol

    def test_bore_volume_matches_formula(self):
        """bore: cylinder r=2.0, h≈3.21 → vol = π × 2.0² × 3.21 ≈ 40.3mm³."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bore"))
        expected = _math.pi * 2.0**2 * 3.21
        assert dims["volume"] == pytest.approx(expected, abs=0.5)


# Tier 2: m5_nut stdlib component
# ---------------------------------------------------------------------------

_M5_NUT_STDLIB = Path(__file__).parents[3] / "tiacad_core" / "stdlib" / "hardware" / "m5_nut.yaml"


class TestM5NutContracts:
    """
    tiacad_core/stdlib/hardware/m5_nut.yaml: ISO 4032 M5 hex nut.

    Parameters (defaults): diameter=9.24, thickness=4.7, bore_radius=2.5
    AF=8mm → circumscribed=8/cos(30°)≈9.24mm
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(_M5_NUT_STDLIB))

    def test_hex_body_builds(self):
        doc = self._parse()
        assert doc.parts.get("hex_body") is not None

    def test_nut_has_positive_volume(self):
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["volume"] > 0

    def test_nut_height_matches_thickness(self):
        """Thickness=4.7 → nut Z extent ≈ 4.7mm."""
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["depth"] == pytest.approx(4.7, abs=TOL)

    def test_nut_volume_less_than_hex_body(self):
        """Bore must remove material."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("hex_body"))["volume"]
        nut_vol = get_dimensions(doc.parts.get("nut"))["volume"]
        assert nut_vol < body_vol

    def test_bore_volume_matches_formula(self):
        """bore: cylinder r=2.5, h≈4.71 → vol = π × 2.5² × 4.71 ≈ 92.5mm³."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bore"))
        expected = _math.pi * 2.5**2 * 4.71
        assert dims["volume"] == pytest.approx(expected, abs=0.5)


# Tier 2: m6_nut stdlib component
# ---------------------------------------------------------------------------

_M6_NUT_STDLIB = Path(__file__).parents[3] / "tiacad_core" / "stdlib" / "hardware" / "m6_nut.yaml"


class TestM6NutContracts:
    """
    tiacad_core/stdlib/hardware/m6_nut.yaml: ISO 4032 M6 hex nut.

    Parameters (defaults): diameter=11.55, thickness=5.2, bore_radius=3.0
    AF=10mm → circumscribed=10/cos(30°)≈11.55mm
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(_M6_NUT_STDLIB))

    def test_hex_body_builds(self):
        doc = self._parse()
        assert doc.parts.get("hex_body") is not None

    def test_nut_has_positive_volume(self):
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["volume"] > 0

    def test_nut_height_matches_thickness(self):
        """Thickness=5.2 → nut Z extent ≈ 5.2mm."""
        doc = self._parse()
        assert get_dimensions(doc.parts.get("nut"))["depth"] == pytest.approx(5.2, abs=TOL)

    def test_nut_volume_less_than_hex_body(self):
        """Bore must remove material."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("hex_body"))["volume"]
        nut_vol = get_dimensions(doc.parts.get("nut"))["volume"]
        assert nut_vol < body_vol

    def test_bore_volume_matches_formula(self):
        """bore: cylinder r=3.0, h≈5.21 → vol = π × 3.0² × 5.21 ≈ 147.3mm³."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("bore"))
        expected = _math.pi * 3.0**2 * 5.21
        assert dims["volume"] == pytest.approx(expected, abs=0.5)


# Tier 2: pcb_standoff_assembly — correctly positioned multi-component assembly
# ---------------------------------------------------------------------------

_PCB_ASSEMBLY = EXAMPLES / "pcb_standoff_assembly.yaml"


class TestPcbStandoffAssembly:
    """
    examples/pcb_standoff_assembly.yaml: 4-corner PCB standoff mount.

    Geometry (all centered at origin, thickness along Z):
      plate: 100 × 80 × 5mm (W × H × D)
      pcb:    80 × 60 × 2mm
      standoffs (×4): 6mm OD, 10mm tall
      screws (×4): M3, 16mm shaft
    """

    def _parse(self):
        return TiaCADParser.parse_file(str(_PCB_ASSEMBLY))

    def test_plate_dimensions(self):
        """Plate: W=100, H=5 (YAML depth→Y), D=80 (YAML height→Z)."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("plate"))
        assert dims["width"] == pytest.approx(100.0, abs=TOL)   # YAML width=100
        assert dims["height"] == pytest.approx(5.0, abs=TOL)    # YAML depth=5 → Y
        assert dims["depth"] == pytest.approx(80.0, abs=TOL)    # YAML height=80 → Z

    def test_plate_volume(self):
        """Plate: 100 × 80 × 5 = 40,000mm³."""
        doc = self._parse()
        assert get_dimensions(doc.parts.get("plate"))["volume"] == pytest.approx(40000.0, abs=1.0)

    def test_pcb_dimensions(self):
        """PCB: W=80, H=2 (YAML depth=2→Y), D=60 (YAML height=60→Z)."""
        doc = self._parse()
        dims = get_dimensions(doc.parts.get("pcb"))
        assert dims["width"] == pytest.approx(80.0, abs=TOL)    # YAML width=80
        assert dims["height"] == pytest.approx(2.0, abs=TOL)    # YAML depth=2 → Y
        assert dims["depth"] == pytest.approx(60.0, abs=TOL)    # YAML height=60 → Z

    def test_standoff_height(self):
        """All 4 standoffs are 10mm tall."""
        doc = self._parse()
        for name in ("standoff_fl", "standoff_fr", "standoff_bl", "standoff_br"):
            dims = get_dimensions(doc.parts.get(name))
            assert dims["depth"] == pytest.approx(10.0, abs=TOL), f"{name} height wrong"

    def test_standoff_volume_matches_body_minus_bore(self):
        """Each standoff (body - bore) must have less volume than body."""
        doc = self._parse()
        body_vol = get_dimensions(doc.parts.get("s_fl.body"))["volume"]
        standoff_vol = get_dimensions(doc.parts.get("s_fl.standoff"))["volume"]
        assert standoff_vol < body_vol

    def test_screw_shaft_dimensions(self):
        """All 4 screw shafts: M3 (3mm dia) × 16mm."""
        doc = self._parse()
        for name in ("screw_fl", "screw_fr", "screw_bl", "screw_br"):
            dims = get_dimensions(doc.parts.get(name))
            assert dims["depth"] == pytest.approx(16.0, abs=TOL), f"{name} length wrong"
            assert dims["width"] == pytest.approx(3.0, abs=TOL), f"{name} diameter wrong"

    def test_all_parts_have_positive_volume(self):
        """Every final assembly part must have positive volume."""
        doc = self._parse()
        final_parts = ["plate", "pcb",
                       "standoff_fl", "standoff_fr", "standoff_bl", "standoff_br",
                       "screw_fl", "screw_fr", "screw_bl", "screw_br"]
        for name in final_parts:
            vol = get_dimensions(doc.parts.get(name))["volume"]
            assert vol > 0, f"{name} has zero or negative volume"
