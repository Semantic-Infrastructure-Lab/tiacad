"""
Tests for part-level inline `translate:`/`rotate:`/`transforms:` (schema v3.0).

Regression coverage for the 2026-07-10 bug where these documented,
schema-legal part keys were silently never applied — parts_builder.py never
read them, so every part built at its untranslated local origin regardless
of what `translate:`/`rotate:` said. Fixed by
OperationsBuilder.apply_inline_part_transforms(), wired into the build
pipeline in parse_pipeline.py right after all parts + the SpatialResolver
exist (so any part may anchor to any sibling's auto-generated references)
and before `operations:` runs. See KNOWN_LIMITATIONS.md #9.

TestInlineTransformsListKey covers a second, later-discovered instance of the
same failure mode: the `transforms:` list form (also schema-documented) was
still silently ignored after the #9 fix, since that fix only ever checked for
`translate`/`rotate` as top-level keys. Found 2026-07-25 while rebuilding
Thingiverse models in TiaCAD.
"""

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser


def _approx_tuple(t):
    return tuple(pytest.approx(v, abs=1e-6) for v in t)


class TestInlinePlainVectorTranslate:
    def test_single_vector_offsets_the_part(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    translate: [100, -50, 30]
""")
        bounds = doc.parts.get("block").get_bounds()
        assert bounds["center"] == (100.0, -50.0, 30.0)

    def test_sequence_of_vectors_applies_in_order(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    translate: [[10, 0, 0], [0, 20, 0], [0, 0, 30]]
""")
        bounds = doc.parts.get("block").get_bounds()
        assert bounds["center"] == (10.0, 20.0, 30.0)

    def test_part_without_translate_or_rotate_is_unaffected(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
""")
        bounds = doc.parts.get("block").get_bounds()
        assert bounds["center"] == (0.0, 0.0, 0.0)


class TestInlineAnchorTranslate:
    def test_to_anchor_positions_on_sibling_auto_reference(self):
        # platform: 100x100x10 box centered at origin -> face_top at Z=5.
        doc = TiaCADParser.parse_string("""
parts:
  platform:
    primitive: box
    size: [100, 100, 10]
    origin: center
  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 20}
    origin: center
    translate:
      to:
        from: platform.face_top
        offset: [30, 0, 0]
""")
        pillar_bounds = doc.parts.get("pillar").get_bounds()
        # pillar's own center anchor lands on platform.face_top (Z=5) + offset,
        # applied in the face's local frame — for a top face that maps the
        # offset's X component onto world Y (established SpatialResolver
        # convention; matches the already-fixed examples/anchors_demo.yaml).
        assert pillar_bounds["center"] == _approx_tuple((0.0, 30.0, 5.0))

    def test_two_siblings_anchored_to_the_same_part_do_not_collide(self):
        doc = TiaCADParser.parse_string("""
parts:
  platform:
    primitive: box
    size: [100, 100, 10]
    origin: center
  left_pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 20}
    origin: center
    translate:
      to:
        from: platform.face_top
        offset: [-30, 0, 0]
  right_pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 20}
    origin: center
    translate:
      to:
        from: platform.face_top
        offset: [30, 0, 0]
""")
        left = doc.parts.get("left_pillar").get_bounds()["center"]
        right = doc.parts.get("right_pillar").get_bounds()["center"]
        assert left != right
        assert left == _approx_tuple((0.0, -30.0, 5.0))
        assert right == _approx_tuple((0.0, 30.0, 5.0))


class TestInlineRotate:
    def test_rotate_about_z_permutes_bbox_xy(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [40, 25, 15]
    origin: center
    rotate: {angle: 90, axis: Z, origin: [0, 0, 0]}
""")
        bounds = doc.parts.get("block").get_bounds()
        # unrotated bbox is X=40,Y=25,Z=15 (width->X, depth->Y, height->Z);
        # a 90-degree rotation about Z swaps X and Y.
        extent = tuple(b - a for a, b in zip(bounds["min"], bounds["max"]))
        assert extent == _approx_tuple((25.0, 40.0, 15.0))

    def test_translate_then_rotate_applies_in_key_order(self):
        # translate to (50,0,0) first, then rotate 90deg about world Z at origin
        # -> final center should land on (0,50,0), not (50,0,0).
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    translate: [50, 0, 0]
    rotate: {angle: 90, axis: Z, origin: [0, 0, 0]}
""")
        cx, cy, cz = doc.parts.get("block").get_bounds()["center"]
        assert abs(cx - 0.0) < 1e-6
        assert abs(cy - 50.0) < 1e-6
        assert abs(cz - 0.0) < 1e-6


class TestInlineTransformVolumeInvariance:
    def test_translate_and_rotate_preserve_volume(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [40, 25, 15]
    origin: center
    translate: [100, -50, 30]
    rotate: {angle: 37, axis: Z, origin: [0, 0, 0]}
""")
        from tiacad_core.testing.dimensions import get_volume
        assert abs(get_volume(doc.parts.get("block")) - 40 * 15 * 25) < 0.01


class TestInlineTransformsListKey:
    """The `transforms:` list form (docs/user/YAML_REFERENCE.md "Parts with
    Transforms") was schema-documented but silently ignored by
    apply_inline_part_transforms(), which only ever checked for the singular
    `translate:`/`rotate:` keys -- a sibling of the #9 bug, missed by the
    original fix because it only tested those two keys. No error, no warning:
    parts using `transforms:` just built at their untranslated local origin."""

    def test_transforms_list_is_applied_not_silently_ignored(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    transforms:
      - translate: [50, 0, 0]
""")
        bounds = doc.parts.get("block").get_bounds()
        assert bounds["center"] == _approx_tuple((50.0, 0.0, 0.0))

    def test_transforms_list_applies_translate_then_rotate_in_order(self):
        # mirrors test_translate_then_rotate_applies_in_key_order, but via the
        # mixed `transforms:` sequence instead of separate translate/rotate keys.
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    transforms:
      - translate: [50, 0, 0]
      - rotate: {angle: 90, axis: Z, origin: [0, 0, 0]}
""")
        cx, cy, cz = doc.parts.get("block").get_bounds()["center"]
        assert abs(cx - 0.0) < 1e-6
        assert abs(cy - 50.0) < 1e-6
        assert abs(cz - 0.0) < 1e-6

    def test_transforms_list_rejects_non_list_value(self):
        with pytest.raises(Exception):
            TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    size: [10, 10, 10]
    origin: center
    transforms: {translate: [50, 0, 0]}
""")
