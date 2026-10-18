"""
Cylinder, cone and polygon: `length` along `axis:` (TCAD-5).

`length` replaces `height` (kept as a deprecated alias), and `axis: X|Y|Z`
(default Z) turns the primitive onto that axis. `origin:` follows the axis:
`base` puts the base face's centre at the origin, `corner` the bounding-box
min corner, a literal [x, y, z] the base centre.
"""

import warnings

import pytest

from tiacad_core.parser.parts_builder import PartsBuilder, PartsBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver

PRIMS = {
    "cylinder": {"radius": 3, "length": 10},
    "cone": {"radius1": 3, "radius2": 3, "length": 10},   # equal radii: a plain cylinder bbox
    "polygon": {"sides": 4, "diameter": 6, "length": 10},  # tip-to-tip 6: corners on the axes, bbox +-3
}


def _bounds(primitive, extra=None, origin=None):
    spec = {"primitive": primitive, **PRIMS[primitive], **(extra or {})}
    if origin is not None:
        spec["origin"] = origin
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        part = PartsBuilder(ParameterResolver({})).build_parts({"p": spec}).get("p")
    bb = part.geometry.val().BoundingBox()
    return tuple(round(v, 3) + 0.0 for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))


# (x range, y range, z range) of each primitive: 6 across (r=3) and length 10
EXTENTS = {
    "Z": lambda lo, hi: ((-3, 3), (-3, 3), (lo, hi)),
    "X": lambda lo, hi: ((lo, hi), (-3, 3), (-3, 3)),
    "Y": lambda lo, hi: ((-3, 3), (lo, hi), (-3, 3)),
}


def _flat(ranges):
    return tuple(v for r in ranges for v in r)


@pytest.mark.parametrize("primitive", list(PRIMS))
@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_center_origin_straddles_the_origin(primitive, axis):
    assert _bounds(primitive, {"axis": axis}, "center") == pytest.approx(_flat(EXTENTS[axis](-5, 5)), abs=1e-3)


@pytest.mark.parametrize("primitive", list(PRIMS))
@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_base_origin_starts_the_primitive_at_the_origin(primitive, axis):
    assert _bounds(primitive, {"axis": axis}, "base") == pytest.approx(_flat(EXTENTS[axis](0, 10)), abs=1e-3)


@pytest.mark.parametrize("primitive", list(PRIMS))
@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_corner_origin_puts_the_bbox_min_corner_at_the_origin(primitive, axis):
    got = _bounds(primitive, {"axis": axis}, "corner")
    assert (got[0], got[2], got[4]) == pytest.approx((0, 0, 0), abs=1e-3)


@pytest.mark.parametrize("primitive", list(PRIMS))
@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_literal_origin_is_the_base_centre(primitive, axis):
    shifted = tuple(EXTENTS[axis](0, 10))
    offset = (100, 200, 300)
    expected = _flat(tuple((lo + o, hi + o) for (lo, hi), o in zip(shifted, offset)))
    assert _bounds(primitive, {"axis": axis}, [100, 200, 300]) == pytest.approx(expected, abs=1e-3)


def test_axis_defaults_to_z_and_is_case_insensitive():
    assert _bounds("cylinder") == _bounds("cylinder", {"axis": "Z"}) == _bounds("cylinder", {"axis": "z"})
    assert _bounds("cylinder", {"axis": "x"}) == _bounds("cylinder", {"axis": "X"})


def test_cone_radius1_is_the_base_end_on_every_axis():
    # radius1 (wide) at the base, radius2 (narrow) at the far end
    for axis, sl in (("X", 0), ("Y", 1), ("Z", 2)):
        spec = {"primitive": "cone", "radius1": 4, "radius2": 1, "length": 10, "axis": axis, "origin": "base"}
        part = PartsBuilder(ParameterResolver({})).build_parts({"c": spec}).get("c")
        bb = part.geometry.val().BoundingBox()
        lo = (bb.xmin, bb.ymin, bb.zmin)[sl]
        assert lo == pytest.approx(0, abs=1e-6)
        # volume of a frustum r1=4 r2=1 L=10
        assert part.geometry.val().Volume() == pytest.approx(3.141592653589793 * 10 / 3 * (16 + 4 + 1), rel=1e-4)


def test_invalid_axis_is_an_error():
    with pytest.raises(PartsBuilderError, match="invalid axis"):
        _bounds("cylinder", {"axis": "W"})


@pytest.mark.parametrize("primitive", list(PRIMS))
def test_height_still_works_but_warns(primitive):
    spec = {"primitive": primitive, **{("height" if k == "length" else k): v for k, v in PRIMS[primitive].items()}}
    with pytest.warns(DeprecationWarning, match="'height' is deprecated; use 'length'"):
        part = PartsBuilder(ParameterResolver({})).build_parts({"p": spec}).get("p")
    assert part.geometry.val().BoundingBox().zlen == pytest.approx(10)


@pytest.mark.parametrize("primitive", list(PRIMS))
def test_length_and_height_together_is_an_error(primitive):
    with pytest.raises(PartsBuilderError, match="both 'length' and 'height'"):
        _bounds(primitive, {"height": 10})


@pytest.mark.parametrize("primitive", list(PRIMS))
def test_length_does_not_warn(primitive):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        spec = {"primitive": primitive, **PRIMS[primitive]}
        PartsBuilder(ParameterResolver({})).build_parts({"p": spec})


@pytest.mark.parametrize("primitive", list(PRIMS))
def test_missing_length_names_length(primitive):
    spec = {"primitive": primitive, **{k: v for k, v in PRIMS[primitive].items() if k != "length"}}
    with pytest.raises(PartsBuilderError, match="length"):
        PartsBuilder(ParameterResolver({})).build_parts({"p": spec})
