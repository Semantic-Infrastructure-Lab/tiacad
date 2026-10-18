"""
Box sizing: `size: [x, y, z]` (TCAD-DSL-6).

The box is sized by its extent along X, Y and Z -- there are no width/depth/height
words. Dimensions are deliberately all different (10 x 20 x 30) so any axis swap shows.
"""

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser

X, Y, Z = 10.0, 20.0, 30.0


def _bbox(yaml_text, part="b"):
    doc = TiaCADParser.parse_string(yaml_text)
    bb = doc.parts.get(part).geometry.val().BoundingBox()
    return {
        "min": (bb.xmin, bb.ymin, bb.zmin),
        "max": (bb.xmax, bb.ymax, bb.zmax),
        "size": (bb.xlen, bb.ylen, bb.zlen),
        "volume": doc.parts.get(part).geometry.val().Volume(),
    }


def _sized(origin, size=f"[{X}, {Y}, {Z}]"):
    return f"""
parts:
  b:
    primitive: box
    size: {size}
    origin: {origin}
"""


ORIGINS = ["center", "corner", "[5, 6, 7]"]


# --- 1. geometry: size maps to X, Y, Z and the origin modes place it -------------

@pytest.mark.parametrize("origin", ORIGINS)
def test_size_extents_are_x_y_z(origin):
    got = _bbox(_sized(origin))
    assert got["size"] == pytest.approx((X, Y, Z))
    assert got["volume"] == pytest.approx(X * Y * Z)


def test_size_origin_placement():
    assert _bbox(_sized("center"))["min"] == pytest.approx((-X / 2, -Y / 2, -Z / 2))
    assert _bbox(_sized("corner"))["min"] == pytest.approx((0, 0, 0), abs=1e-5)
    assert _bbox(_sized("[5, 6, 7]"))["min"] == pytest.approx((5, 6, 7))


def test_size_axes_are_x_y_z_in_order():
    assert _bbox(_sized("corner"))["size"] == pytest.approx((X, Y, Z))


def test_size_scalar_is_a_cube():
    got = _bbox(_sized("corner", size="20"))
    assert got["size"] == pytest.approx((20, 20, 20))


def test_size_default_origin_is_centered():
    yaml_text = f"parts:\n  b:\n    primitive: box\n    size: [{X}, {Y}, {Z}]\n"
    assert _bbox(yaml_text)["min"] == pytest.approx((-X / 2, -Y / 2, -Z / 2))


# --- 2. templates, parameters, units -----------------------------------------

def test_size_accepts_templates_and_parameters():
    yaml_text = """
parameters:
  w: 10
  d: '${w * 2}'
  h: 30
parts:
  b:
    primitive: box
    size: ['${w}', '${d}', '${h}']
    origin: corner
"""
    assert _bbox(yaml_text)["size"] == pytest.approx((10, 20, 30))


def test_size_literal_unit_suffixes_convert_to_mm():
    got = _bbox(_sized("corner", size="[1in, 2cm, 3mm]"))
    assert got["size"] == pytest.approx((25.4, 20.0, 3.0))


def test_size_unit_suffix_inside_template_converts():
    got = _bbox(_sized("corner", size="['${1in + 1mm}', 20, 30]"))
    assert got["size"][0] == pytest.approx(26.4)


# --- 3. errors ---------------------------------------------------------------

def _fails(yaml_text, *fragments):
    with pytest.raises(Exception) as exc:
        TiaCADParser.parse_string(yaml_text)
    message = str(exc.value)
    for fragment in fragments:
        assert fragment in message, message


def test_size_wrong_length_is_rejected():
    _fails(_sized("center", size="[1, 2]"), "size", "3")
    _fails(_sized("center", size="[1, 2, 3, 4]"), "size", "3")


@pytest.mark.parametrize("size", ["[0, 1, 1]", "[1, -1, 1]", "0", "-5"])
def test_size_non_positive_is_rejected(size):
    _fails(_sized("center", size=size), "size", "positive")


def test_size_non_numeric_is_rejected():
    _fails(_sized("center", size="[1, two, 3]"), "size")


def test_size_mapping_form_is_rejected():
    _fails(_sized("center", size="{x: 1, y: 2, z: 3}"), "size", "[x, y, z]")


def test_box_without_size_names_the_expected_form():
    _fails("parts:\n  b:\n    primitive: box\n", "size", "[x, y, z]")


@pytest.mark.parametrize("old_key", ["width", "depth", "height"])
def test_removed_width_depth_height_are_rejected_with_a_migration_hint(old_key):
    for yaml_text in (
        f"parts:\n  b:\n    primitive: box\n    parameters: {{{old_key}: 5}}\n",
        f"parts:\n  b:\n    primitive: box\n    {old_key}: 5\n",
        f"parts:\n  b:\n    primitive: box\n    size: [1, 2, 3]\n    parameters: {{{old_key}: 5}}\n",
    ):
        _fails(yaml_text, old_key, "size: [x, y, z]", "width -> x, depth -> y, height -> z")


# --- origin vocabulary: one set of modes for every primitive, bad values rejected ---

_PRIMS = {
    "box": "size: [10, 10, 10]",
    "cylinder": "parameters: {radius: 5, length: 10}",
    "cone": "parameters: {radius1: 5, radius2: 2, length: 10}",
    "sphere": "parameters: {radius: 5}",
    "polygon": "parameters: {sides: 4, diameter: 10, length: 10}",
}


def _origin_bbox(primitive, origin):
    line = "" if origin is None else f"    origin: {origin}\n"
    text = (f"metadata: {{name: t}}\nparts:\n  b:\n    primitive: {primitive}\n"
            f"    {_PRIMS[primitive]}\n{line}")
    return _bbox(text)


@pytest.mark.parametrize("primitive", ["box", "cylinder", "cone", "sphere"])
def test_origin_modes_share_one_meaning(primitive):
    center = _origin_bbox(primitive, "center")
    base = _origin_bbox(primitive, "base")
    corner = _origin_bbox(primitive, "corner")
    assert _origin_bbox(primitive, None) == center
    assert center["min"][2] == pytest.approx(-center["max"][2])
    # OCCT bounding boxes carry ~1e-7 tolerance on curved solids
    assert base["min"][2] == pytest.approx(0, abs=1e-5)
    assert base["min"][:2] == pytest.approx(center["min"][:2], abs=1e-5)
    assert corner["min"] == pytest.approx((0, 0, 0), abs=1e-5)


@pytest.mark.parametrize("primitive", list(_PRIMS))
@pytest.mark.parametrize("bad", ["bottom", "centre", "middle"])
def test_unknown_origin_is_rejected(primitive, bad):
    with pytest.raises(Exception, match="unknown origin"):
        _origin_bbox(primitive, bad)


def test_unknown_origin_suggests_the_close_match():
    with pytest.raises(Exception, match="Did you mean 'center'"):
        _origin_bbox("box", "centre")


@pytest.mark.parametrize("bad", ["[1, 2]", "[1, 2, x]", "5"])
def test_malformed_origin_value_is_rejected(bad):
    with pytest.raises(Exception, match="invalid origin"):
        _origin_bbox("box", bad)


def test_polygon_default_stays_on_the_bed_and_center_mode_is_available():
    default, center = _origin_bbox("polygon", None), _origin_bbox("polygon", "center")
    assert default["min"][2] == pytest.approx(0) and default["max"][2] == pytest.approx(10)
    assert center["min"][2] == pytest.approx(-5) and center["max"][2] == pytest.approx(5)
    assert _origin_bbox("polygon", "base") == default
    assert _origin_bbox("polygon", "corner")["min"] == pytest.approx((0, 0, 0), abs=1e-5)
