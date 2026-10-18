"""
Sketch plane -> world axis mapping for extrude (TCAD-9).

docs/user/YAML_REFERENCE.md ("Sketch Planes and Extrude") states this table;
these tests keep it true. XZ extruding toward -Y is the surprising entry.
"""

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser

# rectangle width 2 (sketch x), height 4 (sketch y), centred at (10, 20), distance 5
YAML = """
schema_version: "3.0"
metadata: {{name: plane probe}}
sketches:
  s:
    plane: {plane}
    origin: {origin}
    shapes:
      - {{type: rectangle, width: 2, height: 4, center: [10, 20]}}
parts:
  _placeholder: {{primitive: box, size: [1, 1, 1], origin: center}}
operations:
  e: {{type: extrude, sketch: s, distance: 5{extra}}}
export: {{default_part: e}}
"""


def _bounds(plane, origin="[0, 0, 0]", extra=""):
    doc = TiaCADParser.parse_string(YAML.format(plane=plane, origin=origin, extra=extra))
    bb = doc.parts.get("e").geometry.val().BoundingBox()
    return tuple(round(v, 3) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))


@pytest.mark.parametrize("plane, expected", [
    ("XY", (9, 11, 18, 22, 0, 5)),      # x->X, y->Y, extrude +Z
    ("XZ", (9, 11, -5, 0, 18, 22)),     # x->X, y->Z, extrude -Y
    ("YZ", (0, 5, 9, 11, 18, 22)),      # x->Y, y->Z, extrude +X
])
def test_plane_axes_and_extrude_direction(plane, expected):
    assert _bounds(plane) == pytest.approx(expected)


@pytest.mark.parametrize("plane, expected", [
    ("XY", (109, 111, 218, 222, 0, 5)),     # Z component of origin ignored
    ("XZ", (109, 111, -5, 0, 318, 322)),    # Y component ignored
    ("YZ", (0, 5, 209, 211, 318, 322)),     # X component ignored
])
def test_origin_shifts_only_in_plane_axes(plane, expected):
    assert _bounds(plane, origin="[100, 200, 300]") == pytest.approx(expected)


def test_direction_field_does_not_change_geometry():
    assert _bounds("XY", extra=", direction: X") == _bounds("XY")
