"""Unit-suffixed length literals (9.5in, 12mm, 2.54cm, 1ft) resolve to mm (TCAD-DSL-4)."""

import pytest

from tiacad_core.parser.parameter_resolver import ParameterResolver, ParameterResolutionError


def _r(**params):
    return ParameterResolver(params)


def test_bare_parameter_value_inches_to_mm():
    r = _r(length="9.5in")
    assert r.get_parameter("length") == pytest.approx(241.3)


@pytest.mark.parametrize("raw,mm", [
    ("12mm", 12.0), ("2.54cm", 25.4), ("1ft", 304.8), ("1in", 25.4),
    ("9.5 in", 241.3), ("-0.25in", -6.35), (".5in", 12.7),
])
def test_all_units_and_spellings(raw, mm):
    assert _r(v=raw).get_parameter("v") == pytest.approx(mm)


def test_unit_literal_in_expression():
    r = _r(gap="0.016in", w="${9.5in + gap}")
    assert r.get_parameter("w") == pytest.approx(241.3 + 0.4064)


def test_mixed_units_in_one_expression():
    assert _r(w="${1in + 5mm}").get_parameter("w") == pytest.approx(30.4)


def test_no_float_noise():
    assert _r(w="9.5in").get_parameter("w") == 241.3


def test_plain_numbers_untouched():
    r = _r(a=5, b="${a * 2}")
    assert r.get_parameter("b") == 10


def test_identifiers_ending_in_unit_are_not_converted():
    r = _r(x5mm=3, y="${x5mm * 2}")
    assert r.get_parameter("y") == 6


def test_unit_value_in_derived_parameter_chain():
    r = _r(drawer="9.5in", half="${drawer / 2}")
    assert r.get_parameter("half") == pytest.approx(120.65)


def test_errors_show_original_expression():
    with pytest.raises(ParameterResolutionError) as exc:
        _r(w="${9.5in + nope}").get_parameter("w")
    assert "9.5in" in str(exc.value)


def test_unit_text_outside_parameters_is_not_converted():
    # resolve() on a non-parameter string leaves it alone (e.g. text content)
    assert _r().resolve("9.5in") == "9.5in"
