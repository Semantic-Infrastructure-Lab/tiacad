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
