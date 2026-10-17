import math

import pytest

from tiacad_core.parser.parameter_resolver import ParameterResolver, ParameterResolutionError


def _r(**params):
    return ParameterResolver(params)


def _val(expr, **params):
    return _r(x=expr, **params).get_parameter("x")


@pytest.mark.parametrize("expr,expected", [
    ("${sin(30)}", 0.5),
    ("${cos(60)}", 0.5),
    ("${tan(45)}", 1.0),
    ("${tan(20)}", 0.36397023426620234),
    ("${sin(90)}", 1.0),
    ("${cos(0)}", 1.0),
])
def test_trig_takes_degrees(expr, expected):
    assert _val(expr) == pytest.approx(expected)


@pytest.mark.parametrize("expr,expected", [
    ("${asin(0.5)}", 30.0),
    ("${acos(0.5)}", 60.0),
    ("${atan(1)}", 45.0),
    ("${atan2(1, 1)}", 45.0),
    ("${atan2(1, -1)}", 135.0),
])
def test_inverse_trig_returns_degrees(expr, expected):
    assert _val(expr) == pytest.approx(expected)


def test_inverse_round_trip():
    assert _val("${tan(atan(0.75))}") == pytest.approx(0.75)


def test_pi_constant_still_available():
    assert _val("${pi}") == pytest.approx(math.pi)


def test_rad_literal_in_expression_converts_to_degrees():
    assert _val("${0.5rad}") == pytest.approx(math.degrees(0.5))
    assert _val("${tan(0.7853981633974483rad)}") == pytest.approx(1.0)
    assert _val("${sin(.5rad)}") == pytest.approx(math.sin(0.5))


def test_rad_as_whole_parameter_value():
    r = _r(a="1.5707963267948966rad", b="${a / 2}")
    assert r.get_parameter("a") == pytest.approx(90.0)
    assert r.get_parameter("b") == pytest.approx(45.0)
    assert _r(a="-0.5 rad").get_parameter("a") == pytest.approx(-math.degrees(0.5))


def test_rad_suffix_leaves_identifiers_alone():
    assert _val("${xrad + 1}", xrad=4) == 5
    assert _val("${x5rad * 2}", x5rad=3) == 6


def test_derived_angle_slope_chain():
    r = _r(ramp_deg=20, ramp_slope="${tan(ramp_deg)}", rise="${70 * ramp_slope}")
    assert r.get_parameter("rise") == pytest.approx(70 * math.tan(math.radians(20)))


def test_domain_error_is_a_parameter_error():
    with pytest.raises(ParameterResolutionError):
        _val("${asin(2)}")
