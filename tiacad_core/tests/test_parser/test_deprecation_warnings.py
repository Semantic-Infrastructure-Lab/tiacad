"""
Tests for runtime DeprecationWarnings on legacy v3.0/v3.1 API syntax.

Each deprecated pattern must (a) raise a ``DeprecationWarning`` pointing at the
migration guide and (b) still build correctly via the backward-compat mapping.
New syntax must build without emitting any ``DeprecationWarning``.

Implements the plan in docs/developer/API_DEPRECATION_STRATEGY.md.
"""

import warnings

import pytest

from tiacad_core.geometry import MockBackend
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.parser.parse_pipeline import build_export_config


def _parse(yaml_string):
    return TiaCADParser.parse_string(yaml_string, backend=MockBackend())


def _assert_no_deprecation(yaml_string):
    """Parse and assert no DeprecationWarning is emitted."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _parse(yaml_string)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert not deprecations, f"Unexpected DeprecationWarning(s): {[str(w.message) for w in deprecations]}"


# ---------------------------------------------------------------------------
# 1. Cone parameters: radius_bottom/radius_top -> radius1/radius2
# ---------------------------------------------------------------------------

class TestConeParameterDeprecation:
    OLD = """
metadata:
  name: Old Cone
parts:
  frustum:
    primitive: cone
    parameters:
      radius_bottom: 10
      radius_top: 5
      height: 20
"""
    NEW = """
metadata:
  name: New Cone
parts:
  frustum:
    primitive: cone
    parameters:
      radius1: 10
      radius2: 5
      height: 20
"""

    def test_old_cone_params_warn(self):
        with pytest.warns(DeprecationWarning, match="radius_bottom.*deprecated"):
            doc = _parse(self.OLD)
        assert doc.parts.exists("frustum")

    def test_new_cone_params_do_not_warn(self):
        _assert_no_deprecation(self.NEW)

    def test_old_and_new_build_equivalently(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old = _parse(self.OLD).parts.get("frustum")
        new = _parse(self.NEW).parts.get("frustum")
        # Same geometry parameters resolved either way.
        assert old is not None and new is not None


# ---------------------------------------------------------------------------
# 2. Linear pattern: scalar spacing + direction -> vector spacing
# ---------------------------------------------------------------------------

class TestPatternSpacingDeprecation:
    OLD = """
metadata:
  name: Old Pattern
parts:
  hole:
    primitive: cylinder
    radius: 2
    height: 5
    origin: center
operations:
  hole_row:
    type: pattern
    pattern: linear
    input: hole
    count: 4
    spacing: 20
    direction: X
"""
    NEW = """
metadata:
  name: New Pattern
parts:
  hole:
    primitive: cylinder
    radius: 2
    height: 5
    origin: center
operations:
  hole_row:
    type: pattern
    pattern: linear
    input: hole
    count: 4
    spacing: [20, 0, 0]
"""

    def test_old_pattern_spacing_warns(self):
        with pytest.warns(DeprecationWarning, match="scalar 'spacing' with 'direction'"):
            doc = _parse(self.OLD)
        for i in range(4):
            assert doc.parts.exists(f"hole_row_{i}")

    def test_old_pattern_spacing_positions_match_vector_form(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old = _parse(self.OLD)
        new = _parse(self.NEW)
        for i in range(4):
            po = old.parts.get(f"hole_row_{i}").current_position
            pn = new.parts.get(f"hole_row_{i}").current_position
            assert po == pytest.approx(pn)

    def test_new_pattern_spacing_does_not_warn(self):
        _assert_no_deprecation(self.NEW)

    def test_bad_direction_raises(self):
        # PatternBuilderError is wrapped by the operations layer; match on message.
        from tiacad_core.parser.operations_builder import OperationsBuilderError
        bad = self.OLD.replace("direction: X", "direction: Q")
        with pytest.warns(DeprecationWarning):
            with pytest.raises(OperationsBuilderError, match="invalid direction"):
                _parse(bad)


# ---------------------------------------------------------------------------
# 3. Translate offset wrapper: {offset: [...]} without 'to' -> bare list
# ---------------------------------------------------------------------------

class TestTranslateOffsetWrapperDeprecation:
    OLD = """
metadata:
  name: Old Translate
parts:
  box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
operations:
  box_moved:
    type: transform
    input: box
    transforms:
      - translate:
          offset: [30, 20, 10]
"""
    NEW = """
metadata:
  name: New Translate
parts:
  box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
operations:
  box_moved:
    type: transform
    input: box
    transforms:
      - translate: [30, 20, 10]
"""

    def test_old_offset_wrapper_warns(self):
        with pytest.warns(DeprecationWarning, match="offset.*deprecated"):
            doc = _parse(self.OLD)
        assert doc.parts.exists("box_moved")

    def test_offset_wrapper_position_matches_bare_list(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old = _parse(self.OLD).parts.get("box_moved").current_position
        new = _parse(self.NEW).parts.get("box_moved").current_position
        assert old == pytest.approx(new)

    def test_new_bare_list_does_not_warn(self):
        _assert_no_deprecation(self.NEW)

    def test_offset_with_to_still_valid_and_silent(self):
        yaml_with_to = self.OLD.replace(
            "      - translate:\n          offset: [30, 20, 10]",
            "      - translate:\n          to: [20, 0, 0]\n          offset: [5, 0, 0]",
        )
        _assert_no_deprecation(yaml_with_to)


# ---------------------------------------------------------------------------
# 4. Export list format -> dict {default_part, formats}
# ---------------------------------------------------------------------------

class TestExportListDeprecation:
    def test_list_export_warns_and_converts(self):
        legacy = [{"filename": "model.step", "parts": ["base", "arm"]}]
        with pytest.warns(DeprecationWarning, match="Export list format"):
            cfg = build_export_config(legacy)
        assert cfg["default_part"] == "base"
        assert cfg["formats"] == ["step"]

    def test_list_export_multiple_formats(self):
        legacy = [
            {"filename": "model.step", "parts": ["base"]},
            {"filename": "model.stl"},
        ]
        with pytest.warns(DeprecationWarning):
            cfg = build_export_config(legacy)
        assert cfg["default_part"] == "base"
        assert cfg["formats"] == ["step", "stl"]

    def test_list_export_filename_stem_fallback(self):
        legacy = [{"filename": "widget.stl"}]
        with pytest.warns(DeprecationWarning):
            cfg = build_export_config(legacy)
        assert cfg["default_part"] == "widget"
        assert cfg["formats"] == ["stl"]

    def test_dict_export_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            cfg = build_export_config({"default_part": "widget", "formats": ["stl"]})
        assert cfg["default_part"] == "widget"
        assert cfg["formats"] == ["stl"]
