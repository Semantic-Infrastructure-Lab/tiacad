"""
Tests for Sketch2D and Shape2D classes

Tests the core sketch infrastructure for creating 2D profiles.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import pytest
import cadquery as cq

from tiacad_core.sketch import (
    Sketch2D, Shape2D, Rectangle2D, Circle2D, Polygon2D, Text2D, SketchError
)


class TestShape2D:
    """Tests for Shape2D base class and validation"""

    def test_shape2d_requires_valid_operation(self):
        """Shape2D must have 'add' or 'subtract' operation"""
        with pytest.raises(SketchError) as exc_info:
            Shape2D('test', operation='invalid')
        assert "Invalid operation" in str(exc_info.value)

    def test_shape2d_build_not_implemented(self):
        """Shape2D.build() raises NotImplementedError"""
        shape = Shape2D('test', operation='add')
        wp = cq.Workplane("XY")

        with pytest.raises(NotImplementedError):
            shape.build(wp)


class TestRectangle2D:
    """Tests for Rectangle2D shape"""

    def test_rectangle_basic_creation(self):
        """Create a basic rectangle"""
        rect = Rectangle2D(width=10, height=20)
        assert rect.width == 10
        assert rect.height == 20
        assert rect.center == (0, 0)
        assert rect.operation == 'add'

    def test_rectangle_with_center(self):
        """Create rectangle with custom center"""
        rect = Rectangle2D(width=10, height=20, center=(5, 10))
        assert rect.center == (5, 10)

    def test_rectangle_with_operation(self):
        """Create rectangle with subtract operation"""
        rect = Rectangle2D(width=10, height=20, operation='subtract')
        assert rect.operation == 'subtract'

    def test_rectangle_negative_width_rejected(self):
        """Rectangle width must be positive"""
        with pytest.raises(SketchError) as exc_info:
            Rectangle2D(width=-10, height=20)
        assert "width must be positive" in str(exc_info.value)

    def test_rectangle_negative_height_rejected(self):
        """Rectangle height must be positive"""
        with pytest.raises(SketchError) as exc_info:
            Rectangle2D(width=10, height=-20)
        assert "height must be positive" in str(exc_info.value)

    def test_rectangle_build(self):
        """Rectangle builds on workplane"""
        rect = Rectangle2D(width=10, height=20)
        wp = cq.Workplane("XY")
        result = rect.build(wp)
        assert result is not None
        # CadQuery workplane should have the rectangle


class TestCircle2D:
    """Tests for Circle2D shape"""

    def test_circle_basic_creation(self):
        """Create a basic circle"""
        circle = Circle2D(radius=5)
        assert circle.radius == 5
        assert circle.center == (0, 0)
        assert circle.operation == 'add'

    def test_circle_with_center(self):
        """Create circle with custom center"""
        circle = Circle2D(radius=5, center=(10, 15))
        assert circle.center == (10, 15)

    def test_circle_with_operation(self):
        """Create circle with subtract operation"""
        circle = Circle2D(radius=5, operation='subtract')
        assert circle.operation == 'subtract'

    def test_circle_negative_radius_rejected(self):
        """Circle radius must be positive"""
        with pytest.raises(SketchError) as exc_info:
            Circle2D(radius=-5)
        assert "radius must be positive" in str(exc_info.value)

    def test_circle_build(self):
        """Circle builds on workplane"""
        circle = Circle2D(radius=5)
        wp = cq.Workplane("XY")
        result = circle.build(wp)
        assert result is not None


class TestPolygon2D:
    """Tests for Polygon2D shape"""

    def test_polygon_basic_creation(self):
        """Create a basic polygon"""
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly = Polygon2D(points=points)
        assert len(poly.points) == 4
        assert poly.closed is True
        assert poly.operation == 'add'

    def test_polygon_open(self):
        """Create an open polygon"""
        points = [(0, 0), (10, 0), (10, 10)]
        poly = Polygon2D(points=points, closed=False)
        assert poly.closed is False

    def test_polygon_with_operation(self):
        """Create polygon with subtract operation"""
        points = [(0, 0), (10, 0), (10, 10)]
        poly = Polygon2D(points=points, operation='subtract')
        assert poly.operation == 'subtract'

    def test_polygon_too_few_points_rejected(self):
        """Polygon must have at least 3 points"""
        with pytest.raises(SketchError) as exc_info:
            Polygon2D(points=[(0, 0), (10, 0)])
        assert "at least 3 points" in str(exc_info.value)

    def test_polygon_build(self):
        """Polygon builds on workplane"""
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly = Polygon2D(points=points)
        wp = cq.Workplane("XY")
        result = poly.build(wp)
        assert result is not None


class TestText2D:
    """Tests for Text2D shape"""

    def test_text_basic_creation(self):
        """Create basic text shape"""
        text = Text2D(text="Hello", size=10)
        assert text.text == "Hello"
        assert text.size == 10
        assert text.font == "Liberation Sans"
        assert text.style == "regular"
        assert text.halign == "left"
        assert text.valign == "baseline"
        assert text.position == (0, 0)
        assert text.spacing == 1.0
        assert text.operation == 'add'

    def test_text_with_all_parameters(self):
        """Create text with all custom parameters"""
        text = Text2D(
            text="Test",
            size=15,
            font="Arial",
            style="bold",
            halign="center",
            valign="center",
            position=(10, 20),
            spacing=1.2,
            operation="subtract"
        )
        assert text.text == "Test"
        assert text.size == 15
        assert text.font == "Arial"
        assert text.style == "bold"
        assert text.halign == "center"
        assert text.valign == "center"
        assert text.position == (10, 20)
        assert text.spacing == 1.2
        assert text.operation == "subtract"

    def test_text_with_font_path(self):
        """Create text with custom font path"""
        text = Text2D(
            text="Custom",
            size=10,
            font_path="/path/to/font.ttf"
        )
        assert text.font_path == "/path/to/font.ttf"

    def test_text_empty_rejected(self):
        """Empty text is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="", size=10)
        assert "cannot be empty" in str(exc_info.value)

    def test_text_whitespace_only_rejected(self):
        """Whitespace-only text is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="   ", size=10)
        assert "cannot be empty" in str(exc_info.value)

    def test_text_negative_size_rejected(self):
        """Negative text size is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=-5)
        assert "must be positive" in str(exc_info.value)

    def test_text_zero_size_rejected(self):
        """Zero text size is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=0)
        assert "must be positive" in str(exc_info.value)

    def test_text_small_size_warning(self, caplog):
        """Very small text size generates warning"""
        import logging
        with caplog.at_level(logging.WARNING):
            Text2D(text="Test", size=0.3)
        assert "very small" in caplog.text.lower()

    def test_text_invalid_style_rejected(self):
        """Invalid text style is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=10, style="invalid")
        assert "Invalid text style" in str(exc_info.value)

    def test_text_valid_styles_accepted(self):
        """All valid text styles are accepted"""
        for style in ['regular', 'bold', 'italic', 'bold-italic']:
            text = Text2D(text="Test", size=10, style=style)
            assert text.style == style

    def test_text_invalid_halign_rejected(self):
        """Invalid horizontal alignment is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=10, halign="invalid")
        assert "Invalid horizontal alignment" in str(exc_info.value)

    def test_text_valid_halign_accepted(self):
        """All valid horizontal alignments are accepted"""
        for halign in ['left', 'center', 'right']:
            text = Text2D(text="Test", size=10, halign=halign)
            assert text.halign == halign

    def test_text_invalid_valign_rejected(self):
        """Invalid vertical alignment is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=10, valign="invalid")
        assert "Invalid vertical alignment" in str(exc_info.value)

    def test_text_valid_valign_accepted(self):
        """All valid vertical alignments are accepted"""
        for valign in ['top', 'center', 'baseline', 'bottom']:
            text = Text2D(text="Test", size=10, valign=valign)
            assert text.valign == valign

    def test_text_negative_spacing_rejected(self):
        """Negative spacing is rejected"""
        with pytest.raises(SketchError) as exc_info:
            Text2D(text="Test", size=10, spacing=-0.5)
        assert "spacing must be positive" in str(exc_info.value)

    def test_text_unicode_accepted(self):
        """Unicode text is accepted"""
        text = Text2D(text="Hello 世界 🌍", size=10)
        assert text.text == "Hello 世界 🌍"

    def test_text_parametric_string(self):
        """Text can contain parameter placeholders"""
        text = Text2D(text="${product_name} v${version}", size=10)
        assert text.text == "${product_name} v${version}"

    def test_text_build_creates_geometry(self):
        """Text build method creates geometry on workplane"""
        text = Text2D(text="TEST", size=10)
        wp = cq.Workplane("XY")
        # Note: This may fail if fonts aren't available in test environment
        # We'll handle that gracefully
        try:
            result = text.build(wp)
            assert result is not None
        except Exception as e:
            # Font errors are acceptable in test environment
            if 'font' not in str(e).lower():
                raise

    def test_text_repr(self):
        """Text has useful repr"""
        text = Text2D(text="Hello", size=10, font="Arial", style="bold")
        repr_str = repr(text)
        assert "Text2D" in repr_str
        assert "Hello" in repr_str
        assert "10" in repr_str
        assert "Arial" in repr_str
        assert "bold" in repr_str


class TestSketch2D:
    """Tests for Sketch2D composite sketches"""

    def test_sketch_basic_creation(self):
        """Create a basic sketch with one rectangle"""
        rect = Rectangle2D(width=10, height=20)
        sketch = Sketch2D(
            name='test_sketch',
            plane='XY',
            origin=(0, 0, 0),
            shapes=[rect]
        )
        assert sketch.name == 'test_sketch'
        assert sketch.plane == 'XY'
        assert sketch.origin == (0, 0, 0)
        assert len(sketch.shapes) == 1

    def test_sketch_plane_normalization(self):
        """Sketch plane is normalized to uppercase"""
        rect = Rectangle2D(width=10, height=20)
        sketch = Sketch2D(
            name='test',
            plane='xy',  # lowercase
            origin=(0, 0, 0),
            shapes=[rect]
        )
        assert sketch.plane == 'XY'

    def test_sketch_invalid_plane_rejected(self):
        """Invalid plane is rejected"""
        rect = Rectangle2D(width=10, height=20)
        with pytest.raises(SketchError) as exc_info:
            Sketch2D(
                name='test',
                plane='AB',  # Invalid
                origin=(0, 0, 0),
                shapes=[rect]
            )
        assert "Invalid plane" in str(exc_info.value)

    def test_sketch_empty_shapes_rejected(self):
        """Sketch must have at least one shape"""
        with pytest.raises(SketchError) as exc_info:
            Sketch2D(
                name='test',
                plane='XY',
                origin=(0, 0, 0),
                shapes=[]  # Empty
            )
        assert "at least one shape" in str(exc_info.value)

    def test_sketch_build_profile_single_rectangle(self):
        """Build profile from single rectangle"""
        rect = Rectangle2D(width=10, height=20)
        sketch = Sketch2D(
            name='test',
            plane='XY',
            origin=(0, 0, 0),
            shapes=[rect]
        )
        profile = sketch.build_profile()
        assert profile is not None
        assert sketch.profile is not None

    def test_sketch_build_profile_rectangle_with_hole(self):
        """Build profile from rectangle with circular hole"""
        rect = Rectangle2D(width=20, height=20)
        hole = Circle2D(radius=5, center=(0, 0), operation='subtract')
        sketch = Sketch2D(
            name='test',
            plane='XY',
            origin=(0, 0, 0),
            shapes=[rect, hole]
        )
        profile = sketch.build_profile()
        assert profile is not None

    def test_sketch_all_subtract_shapes_rejected(self):
        """Sketch must have at least one 'add' shape"""
        hole = Circle2D(radius=5, operation='subtract')
        sketch = Sketch2D(
            name='test',
            plane='XY',
            origin=(0, 0, 0),
            shapes=[hole]
        )
        with pytest.raises(SketchError) as exc_info:
            sketch.build_profile()
        assert "at least one 'add' shape" in str(exc_info.value)
