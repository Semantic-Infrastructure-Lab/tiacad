"""
Tests for SketchBuilder's ellipse/path shape parsing (TCAD-DSL-1).

No dedicated SketchBuilder test file existed before this -- these cover the
new `_build_ellipse`/`_build_path` YAML-to-Shape2D parsing paths directly.
End-to-end coverage (full YAML -> revolve -> watertight solid) lives in
examples/curved_vase.yaml and tiacad_core/tests/test_cli/test_cli_build.py.
"""

import pytest

from tiacad_core.parser.sketch_builder import SketchBuilder, SketchBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.sketch import Ellipse2D, Path2D


@pytest.fixture
def builder():
    return SketchBuilder(ParameterResolver({}))


class TestBuildEllipse:
    def test_builds_ellipse_with_defaults(self, builder):
        shape = builder.build_shape('s', 0, {
            'type': 'ellipse', 'x_radius': 20, 'y_radius': 10,
        })
        assert isinstance(shape, Ellipse2D)
        assert shape.x_radius == 20
        assert shape.y_radius == 10
        assert shape.center == (0, 0)
        assert shape.rotation == 0.0

    def test_builds_ellipse_with_center_and_rotation(self, builder):
        shape = builder.build_shape('s', 0, {
            'type': 'ellipse', 'x_radius': 20, 'y_radius': 10,
            'center': [5, 5], 'rotation': 30,
        })
        assert shape.center == (5, 5)
        assert shape.rotation == 30

    def test_missing_x_radius_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'ellipse', 'y_radius': 10})
        assert "missing 'x_radius'" in str(exc_info.value)

    def test_missing_y_radius_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'ellipse', 'x_radius': 20})
        assert "missing 'y_radius'" in str(exc_info.value)

    def test_invalid_center_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {
                'type': 'ellipse', 'x_radius': 20, 'y_radius': 10, 'center': [1, 2, 3],
            })
        assert "center must be [x, y]" in str(exc_info.value)


class TestBuildPath:
    def test_builds_path_with_line_and_arc(self, builder):
        shape = builder.build_shape('s', 0, {
            'type': 'path',
            'start': [0, 0],
            'segments': [
                {'line': [10, 0]},
                {'arc': {'through': [15, 5], 'to': [10, 10]}},
            ],
        })
        assert isinstance(shape, Path2D)
        assert shape.start == (0, 0)
        assert len(shape.segments) == 2
        assert shape.closed is True

    def test_respects_closed_false(self, builder):
        shape = builder.build_shape('s', 0, {
            'type': 'path', 'start': [0, 0],
            'segments': [{'line': [10, 0]}], 'closed': False,
        })
        assert shape.closed is False

    def test_missing_start_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'path', 'segments': [{'line': [1, 0]}]})
        assert "missing 'start'" in str(exc_info.value)

    def test_missing_segments_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'path', 'start': [0, 0]})
        assert "missing 'segments'" in str(exc_info.value)

    def test_empty_segments_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'path', 'start': [0, 0], 'segments': []})
        assert "non-empty list" in str(exc_info.value)

    def test_invalid_start_raises(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {
                'type': 'path', 'start': [0, 0, 0], 'segments': [{'line': [1, 0]}],
            })
        assert "start must be [x, y]" in str(exc_info.value)

    def test_unsupported_spline_segment_type_raises_at_shape_construction(self, builder):
        """
        'spline' is a deliberately unsupported Path2D segment (see the
        Path2D docstring in tiacad_core/sketch.py) -- SketchBuilder passes
        segments through untouched, so the rejection happens in Path2D's
        own validation, surfaced here as a wrapped SketchBuilderError.
        """
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {
                'type': 'path', 'start': [0, 0], 'segments': [{'spline': [[1, 1]]}],
            })
        assert "unknown type 'spline'" in str(exc_info.value)

    def test_unknown_shape_type_lists_path_and_ellipse(self, builder):
        with pytest.raises(SketchBuilderError) as exc_info:
            builder.build_shape('s', 0, {'type': 'hexagon'})
        assert "ellipse" in str(exc_info.value)
        assert "path" in str(exc_info.value)
