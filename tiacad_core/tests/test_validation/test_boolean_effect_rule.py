"""
Unit tests for BooleanEffectRule

Guards against boolean operations that silently do nothing: a `difference`
whose subtract tool misses the base, a `union` result smaller than its
largest input, or an `intersection` of non-overlapping parts. This is the
systemic check proposed after the awesome_guitar_hanger mounting-hole bug
(see docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md) — volume-range
contracts alone did not catch a difference that removed ~0mm³.
"""

import textwrap
from pathlib import Path

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.validation.rules.boolean_effect_rule import BooleanEffectRule

EXAMPLES = Path(__file__).parents[3] / "examples"


def _parse_yaml(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return TiaCADParser.parse_file(str(path))


DIFFERENCE_TEMPLATE = """\
parts:
  base_box:
    primitive: box
    parameters:
      width: 20
      height: 20
      depth: 20
    origin: center
  cutter:
    primitive: cylinder
    parameters:
      radius: 3
      height: 30
    origin: center

operations:
  cutter_positioned:
    type: transform
    input: cutter
    transforms:
      - translate: [{offset}, 0, 0]

  result:
    type: boolean
    operation: difference
    base: base_box
    subtract:
      - cutter_positioned

export:
  default_part: result
"""

INTERSECTION_TEMPLATE = """\
parts:
  box_a:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
    origin: center
  box_b:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
    origin: center

operations:
  box_b_positioned:
    type: transform
    input: box_b
    transforms:
      - translate: [{offset}, 0, 0]

  result:
    type: boolean
    operation: intersection
    inputs:
      - box_a
      - box_b_positioned

export:
  default_part: result
"""


class TestBooleanEffectRuleDifference:
    def test_hole_that_pierces_base_is_clean(self, tmp_path):
        """Cutter through the center of the box: a real cut, no issue."""
        doc = _parse_yaml(tmp_path, "diff_ok.yaml", DIFFERENCE_TEMPLATE.format(offset=0))
        issues = BooleanEffectRule().check(doc)
        assert issues == []

    def test_hole_that_misses_base_is_flagged(self, tmp_path):
        """Cutter offset far enough to miss the box entirely: silent no-op difference."""
        doc = _parse_yaml(tmp_path, "diff_miss.yaml", DIFFERENCE_TEMPLATE.format(offset=100))
        issues = BooleanEffectRule().check(doc)
        assert len(issues) == 1
        assert issues[0].severity.value == "ERROR"
        assert "Difference" in issues[0].message
        assert "result" in issues[0].message


class TestBooleanEffectRuleIntersection:
    def test_overlapping_boxes_is_clean(self, tmp_path):
        doc = _parse_yaml(tmp_path, "intersect_ok.yaml", INTERSECTION_TEMPLATE.format(offset=5))
        issues = BooleanEffectRule().check(doc)
        assert issues == []

    def test_barely_overlapping_boxes_is_flagged(self, tmp_path):
        """Boxes overlap by 0.005mm — a real but negligible sliver, not zero."""
        doc = _parse_yaml(tmp_path, "intersect_sliver.yaml", INTERSECTION_TEMPLATE.format(offset=9.995))
        issues = BooleanEffectRule().check(doc)
        assert len(issues) == 1
        assert issues[0].severity.value == "ERROR"
        assert "Intersection" in issues[0].message

    def test_fully_disjoint_boxes_fails_at_build_time(self, tmp_path):
        """A fully empty intersection is already caught by the CAD kernel itself (Bnd_Box is void)."""
        from tiacad_core.parser.operations_builder import OperationsBuilderError
        with pytest.raises(OperationsBuilderError):
            _parse_yaml(tmp_path, "intersect_miss.yaml", INTERSECTION_TEMPLATE.format(offset=100))


class TestBooleanEffectRuleUnion:
    def test_touching_boxes_is_clean(self, tmp_path):
        """A normal union (chamfered_bracket.yaml) must not be flagged."""
        doc = TiaCADParser.parse_file(str(EXAMPLES / "chamfered_bracket.yaml"))
        issues = BooleanEffectRule().check(doc)
        assert issues == []


MOUNTING_HOLE_TEMPLATE = """\
parts:
  mounting_plate:
    primitive: box
    parameters:
      width: 120
      height: 15
      depth: 90
    origin: center
  screw_hole_shaft:
    primitive: cylinder
    parameters:
      radius: 2.5
      height: 17
    origin: center

operations:
  left_screw_shaft:
    type: transform
    input: screw_hole_shaft
    transforms:
      # Bug reproduction: the vertical positioning value (25) lands in the
      # Z offset instead of Y, so the shaft floats above the plate instead
      # of piercing it (matches the awesome_guitar_hanger regression fixed
      # 2026-07-09 — see docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md).
      - translate: [-35, {y_offset}, {z_offset}]

  result:
    type: boolean
    operation: difference
    base: mounting_plate
    subtract:
      - left_screw_shaft

export:
  default_part: result
"""


class TestBooleanEffectRuleRegression:
    """Regression guard for the awesome_guitar_hanger mounting-hole bug class."""

    def test_current_fixed_example_is_clean(self):
        doc = TiaCADParser.parse_file(str(EXAMPLES / "awesome_guitar_hanger.yaml"))
        issues = BooleanEffectRule().check(doc)
        assert issues == []

    def test_shaft_piercing_plate_is_clean(self, tmp_path):
        """Correct axis mapping: vertical value in Y, shaft actually pierces the plate."""
        doc = _parse_yaml(
            tmp_path, "mounting_hole_ok.yaml",
            MOUNTING_HOLE_TEMPLATE.format(y_offset=25, z_offset=0),
        )
        issues = BooleanEffectRule().check(doc)
        assert issues == []

    def test_shaft_floating_above_plate_is_flagged(self, tmp_path):
        """Bug reproduction: vertical value in Z instead of Y, shaft floats off the plate."""
        doc = _parse_yaml(
            tmp_path, "mounting_hole_bug.yaml",
            MOUNTING_HOLE_TEMPLATE.format(y_offset=0, z_offset=25),
        )
        issues = BooleanEffectRule().check(doc)
        assert len(issues) == 1
        assert issues[0].severity.value == "ERROR"
        assert "Difference" in issues[0].message
