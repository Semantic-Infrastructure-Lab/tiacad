"""
Tests for ColorParser - all supported color formats
"""

import pytest
from tiacad_core.parser.color_parser import ColorParser, Color, ColorParseError


class TestColorBasics:
    """Test Color class"""

    def test_color_creation(self):
        """Create color with RGB values"""
        c = Color(1.0, 0.0, 0.0)
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert c.a == 1.0

    def test_color_with_alpha(self):
        """Create color with alpha"""
        c = Color(1.0, 0.0, 0.0, 0.5)
        assert c.a == 0.5

    def test_color_clamping(self):
        """Values should be clamped to 0-1"""
        c = Color(1.5, -0.5, 0.5)
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.5

    def test_to_rgb(self):
        """Convert to RGB tuple"""
        c = Color(0.5, 0.6, 0.7, 0.8)
        assert c.to_rgb() == (0.5, 0.6, 0.7)

    def test_to_rgba(self):
        """Convert to RGBA tuple"""
        c = Color(0.5, 0.6, 0.7, 0.8)
        assert c.to_rgba() == (0.5, 0.6, 0.7, 0.8)

    def test_to_hex(self):
        """Convert to hex string"""
        c = Color(1.0, 0.0, 0.0)
        assert c.to_hex() == "#FF0000"

        c = Color(0.0, 0.0, 1.0)
        assert c.to_hex() == "#0000FF"

    def test_color_equality(self):
        """Test color equality"""
        c1 = Color(1.0, 0.0, 0.0)
        c2 = Color(1.0, 0.0, 0.0)
        c3 = Color(0.0, 1.0, 0.0)
        assert c1 == c2
        assert c1 != c3


class TestNamedColors:
    """Test parsing named colors"""

    def test_basic_colors(self):
        """Parse basic color names"""
        parser = ColorParser()

        # Test basic colors
        red = parser.parse("red")
        assert red.r == 1.0
        assert red.g == 0.0
        assert red.b == 0.0

        blue = parser.parse("blue")
        assert blue.r == 0.0
        assert blue.b == 1.0

        white = parser.parse("white")
        assert white == Color(1.0, 1.0, 1.0)

    def test_case_insensitive(self):
        """Color names should be case-insensitive"""
        parser = ColorParser()
        red1 = parser.parse("red")
        red2 = parser.parse("RED")
        red3 = parser.parse("Red")
        assert red1 == red2 == red3

    def test_material_colors(self):
        """Parse material library colors"""
        parser = ColorParser()

        # Aluminum should be in material library
        aluminum = parser.parse("aluminum")
        assert aluminum is not None
        # Should be grayish
        assert 0.7 < aluminum.r < 0.8
        assert 0.7 < aluminum.g < 0.8
        assert 0.7 < aluminum.b < 0.8

    def test_unknown_color(self):
        """Unknown color names should raise error with suggestions"""
        parser = ColorParser()

        with pytest.raises(ColorParseError) as exc:
            parser.parse("unknown-color-xyz")

        assert "unknown" in str(exc.value).lower()
        # Should have suggestions
        assert hasattr(exc.value, 'suggestions')


class TestPalette:
    """Test palette (color references)"""

    def test_palette_reference(self):
        """Reference colors from palette"""
        palette = {
            'primary': '#0066CC',
            'secondary': 'red'
        }
        parser = ColorParser(palette=palette)

        # Reference palette color
        primary = parser.parse('primary')
        assert primary == parser.parse('#0066CC')

        # Reference basic color through palette
        secondary = parser.parse('secondary')
        assert secondary == parser.parse('red')

    def test_palette_precedence(self):
        """Palette colors override basic colors"""
        palette = {
            'red': '#0000FF'  # Override red to be blue!
        }
        parser = ColorParser(palette=palette)

        # Should get blue (from palette)
        color = parser.parse('red')
        assert color.b > 0.9  # Should be blue
        assert color.r < 0.1

    def test_nested_palette_reference(self):
        """Palette can reference other palette entries"""
        palette = {
            'base': '#FF0000',
            'derived': 'base'  # Reference another palette entry
        }
        parser = ColorParser(palette=palette)

        base = parser.parse('base')
        derived = parser.parse('derived')
        assert base == derived


class TestHexColors:
    """Test hex color parsing"""

    def test_hex_6_digit(self):
        """Parse #RRGGBB format"""
        parser = ColorParser()

        red = parser.parse("#FF0000")
        assert red == Color(1.0, 0.0, 0.0)

        blue = parser.parse("#0000FF")
        assert blue == Color(0.0, 0.0, 1.0)

        custom = parser.parse("#0066CC")
        assert custom.r < 0.1
        assert 0.35 < custom.g < 0.45
        assert 0.75 < custom.b < 0.85

    def test_hex_3_digit(self):
        """Parse #RGB format (shorthand)"""
        parser = ColorParser()

        red = parser.parse("#F00")
        assert red == Color(1.0, 0.0, 0.0)

        white = parser.parse("#FFF")
        assert white == Color(1.0, 1.0, 1.0)

    def test_hex_8_digit_alpha(self):
        """Parse #RRGGBBAA format with alpha"""
        parser = ColorParser()

        # Red, 50% transparent
        color = parser.parse("#FF000080")
        assert color.r == 1.0
        assert color.g == 0.0
        assert color.b == 0.0
        assert 0.48 < color.a < 0.52  # ~0.5

    def test_hex_case_insensitive(self):
        """Hex should accept both upper and lower case"""
        parser = ColorParser()

        c1 = parser.parse("#ff0000")
        c2 = parser.parse("#FF0000")
        c3 = parser.parse("#Ff0000")
        assert c1 == c2 == c3

    def test_hex_invalid(self):
        """Invalid hex should raise error"""
        parser = ColorParser()

        # Invalid length
        with pytest.raises(ColorParseError):
            parser.parse("#FF")

        # Invalid characters
        with pytest.raises(ColorParseError):
            parser.parse("#GGGGGG")

        # Missing #
        with pytest.raises(ColorParseError):
            parser.parse("FF0000")


class TestRGBArrays:
    """Test RGB/RGBA array parsing"""

    def test_rgb_array(self):
        """Parse [r, g, b] array (0-1 range)"""
        parser = ColorParser()

        red = parser.parse([1.0, 0.0, 0.0])
        assert red == Color(1.0, 0.0, 0.0)

        custom = parser.parse([0.5, 0.6, 0.7])
        assert custom == Color(0.5, 0.6, 0.7)

    def test_rgba_array(self):
        """Parse [r, g, b, a] array"""
        parser = ColorParser()

        color = parser.parse([1.0, 0.0, 0.0, 0.5])
        assert color.r == 1.0
        assert color.a == 0.5

    def test_rgb_array_invalid_length(self):
        """Array must have 3 or 4 elements"""
        parser = ColorParser()

        with pytest.raises(ColorParseError) as exc:
            parser.parse([1.0, 0.0])

        assert "length" in str(exc.value).lower()

    def test_rgb_array_out_of_range(self):
        """Values must be in 0-1 range"""
        parser = ColorParser()

        with pytest.raises(ColorParseError):
            parser.parse([1.5, 0.0, 0.0])

        with pytest.raises(ColorParseError):
            parser.parse([-0.5, 0.0, 0.0])


class TestRGBObjects:
    """Test RGB object parsing {r, g, b}"""

    def test_rgb_object(self):
        """Parse {r: 255, g: 0, b: 0} (0-255 range)"""
        parser = ColorParser()

        red = parser.parse({'r': 255, 'g': 0, 'b': 0})
        assert red == Color(1.0, 0.0, 0.0)

        custom = parser.parse({'r': 128, 'g': 128, 'b': 128})
        assert 0.48 < custom.r < 0.52  # ~0.5

    def test_rgba_object(self):
        """Parse with alpha"""
        parser = ColorParser()

        color = parser.parse({'r': 255, 'g': 0, 'b': 0, 'a': 128})
        assert color.r == 1.0
        assert 0.48 < color.a < 0.52  # ~0.5

    def test_rgb_object_default_alpha(self):
        """Alpha defaults to 255 (opaque) if not specified"""
        parser = ColorParser()

        color = parser.parse({'r': 255, 'g': 0, 'b': 0})
        assert color.a == 1.0

    def test_rgb_object_out_of_range(self):
        """Values must be 0-255"""
        parser = ColorParser()

        with pytest.raises(ColorParseError):
            parser.parse({'r': 256, 'g': 0, 'b': 0})

        with pytest.raises(ColorParseError):
            parser.parse({'r': -1, 'g': 0, 'b': 0})


class TestHSLColors:
    """Test HSL color parsing"""

    def test_hsl_red(self):
        """Parse red in HSL"""
        parser = ColorParser()

        red = parser.parse({'h': 0, 's': 100, 'l': 50})
        assert red.r > 0.99
        assert red.g < 0.01
        assert red.b < 0.01

    def test_hsl_blue(self):
        """Parse blue in HSL"""
        parser = ColorParser()

        blue = parser.parse({'h': 240, 's': 100, 'l': 50})
        assert blue.r < 0.01
        assert blue.g < 0.01
        assert blue.b > 0.99

    def test_hsl_gray(self):
        """Parse gray (no saturation)"""
        parser = ColorParser()

        gray = parser.parse({'h': 0, 's': 0, 'l': 50})
        # Should be equal RGB values (gray)
        assert abs(gray.r - gray.g) < 0.01
        assert abs(gray.g - gray.b) < 0.01

    def test_hsl_with_alpha(self):
        """Parse HSL with alpha"""
        parser = ColorParser()

        color = parser.parse({'h': 0, 's': 100, 'l': 50, 'a': 0.5})
        assert color.a == 0.5

    def test_hsl_out_of_range(self):
        """HSL values must be in valid ranges"""
        parser = ColorParser()

        # Hue out of range (0-360)
        with pytest.raises(ColorParseError):
            parser.parse({'h': 361, 's': 100, 'l': 50})

        # Saturation out of range (0-100)
        with pytest.raises(ColorParseError):
            parser.parse({'h': 0, 's': 101, 'l': 50})

        # Lightness out of range (0-100)
        with pytest.raises(ColorParseError):
            parser.parse({'h': 0, 's': 100, 'l': 101})


class TestErrorHandling:
    """Test error handling and messages"""

    def test_none_value(self):
        """None should raise error"""
        parser = ColorParser()

        with pytest.raises(ColorParseError):
            parser.parse(None)

    def test_invalid_type(self):
        """Invalid types should raise error"""
        parser = ColorParser()

        with pytest.raises(ColorParseError):
            parser.parse(123)

        with pytest.raises(ColorParseError):
            parser.parse(True)

    def test_invalid_object_keys(self):
        """Object without r,g,b or h,s,l keys should error"""
        parser = ColorParser()

        with pytest.raises(ColorParseError) as exc:
            parser.parse({'x': 0, 'y': 0, 'z': 0})

        assert 'r,g,b' in str(exc.value) or 'h,s,l' in str(exc.value)

    def test_error_includes_suggestions(self):
        """Errors should include helpful suggestions"""
        parser = ColorParser()

        with pytest.raises(ColorParseError) as exc:
            parser.parse("redd")  # Typo

        # Should suggest "red"
        assert exc.value.suggestions
        assert "red" in exc.value.suggestions


class TestRealWorldExamples:
    """Test realistic usage patterns"""

    def test_design_system_palette(self):
        """Test a complete design system palette"""
        palette = {
            'brand-blue': '#0066CC',
            'brand-orange': '#CC6600',
            'primary': 'brand-blue',
            'secondary': 'brand-orange',
            'neutral': 'aluminum',
            'accent': {'h': 180, 's': 70, 'l': 50}
        }
        parser = ColorParser(palette=palette)

        # All should parse successfully
        primary = parser.parse('primary')
        assert primary is not None

        secondary = parser.parse('secondary')
        assert secondary is not None

        neutral = parser.parse('neutral')
        assert neutral is not None

        accent = parser.parse('accent')
        assert accent is not None

    def test_mixed_formats(self):
        """Different parts can use different formats"""
        palette = {
            'part1': 'red',
            'part2': '#0066CC',
            'part3': [0.5, 0.6, 0.7],
            'part4': {'r': 128, 'g': 128, 'b': 128},
            'part5': {'h': 120, 's': 100, 'l': 50}
        }
        parser = ColorParser(palette=palette)

        # All should parse
        for name in ['part1', 'part2', 'part3', 'part4', 'part5']:
            color = parser.parse(name)
            assert color is not None
            assert isinstance(color, Color)

    def test_transparent_colors(self):
        """Test transparency in various formats"""
        parser = ColorParser()

        # Hex with alpha
        c1 = parser.parse("#FF000080")
        assert c1.a < 0.6

        # RGBA array
        c2 = parser.parse([1.0, 0.0, 0.0, 0.5])
        assert c2.a == 0.5

        # RGB object with alpha
        c3 = parser.parse({'r': 255, 'g': 0, 'b': 0, 'a': 128})
        assert c3.a < 0.6

        # HSL with alpha
        c4 = parser.parse({'h': 0, 's': 100, 'l': 50, 'a': 0.3})
        assert c4.a == 0.3
