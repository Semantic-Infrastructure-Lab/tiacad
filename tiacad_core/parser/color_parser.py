"""
TiaCAD Color Parser

Parses all supported color value formats:
- Named colors: "red", "blue", "aluminum"
- Hex strings: "#FF0000", "#0066CC80"
- RGB arrays: [1.0, 0.0, 0.0]
- RGBA arrays: [1.0, 0.0, 0.0, 0.5]
- RGB objects: {r: 255, g: 0, b: 0}
- HSL objects: {h: 0, s: 100, l: 50}

Design: Progressive disclosure
- Simple: color: red
- Palette: color: brand-blue (reference to colors section)
- Material: material: aluminum (reference to materials library)
- Advanced: full PBR appearance definition
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from ..materials_library import get_material_library, Material
from .color_utils import hsl_to_rgb, hex_to_rgb, rgb_to_hex, clamp


class ColorParseError(Exception):
    """Error parsing color value"""

    def __init__(self, message: str, value: Any = None, suggestions: Optional[List[str]] = None):
        self.value = value
        self.suggestions = suggestions or []
        super().__init__(message)


class Color:
    """Parsed color with RGBA values (0-1 range)"""

    def __init__(self, r: float, g: float, b: float, a: float = 1.0):
        """
        Args:
            r: Red (0-1)
            g: Green (0-1)
            b: Blue (0-1)
            a: Alpha/opacity (0-1), default 1.0
        """
        self.r = clamp(r)
        self.g = clamp(g)
        self.b = clamp(b)
        self.a = clamp(a)

    def to_rgb(self) -> Tuple[float, float, float]:
        """Return RGB tuple (0-1 range)"""
        return (self.r, self.g, self.b)

    def to_rgba(self) -> Tuple[float, float, float, float]:
        """Return RGBA tuple (0-1 range)"""
        return (self.r, self.g, self.b, self.a)

    def to_hex(self) -> str:
        """Return hex string #RRGGBB"""
        return rgb_to_hex(self.r, self.g, self.b)

    def __repr__(self):
        if self.a < 1.0:
            return f"Color(r={self.r:.2f}, g={self.g:.2f}, b={self.b:.2f}, a={self.a:.2f})"
        return f"Color(r={self.r:.2f}, g={self.g:.2f}, b={self.b:.2f})"

    def __eq__(self, other):
        if not isinstance(other, Color):
            return False
        return (abs(self.r - other.r) < 0.01 and
                abs(self.g - other.g) < 0.01 and
                abs(self.b - other.b) < 0.01 and
                abs(self.a - other.a) < 0.01)


# Basic named colors (CSS/web colors)
BASIC_COLORS = {
    'red': (1.0, 0.0, 0.0),
    'green': (0.0, 0.5, 0.0),
    'blue': (0.0, 0.0, 1.0),
    'yellow': (1.0, 1.0, 0.0),
    'orange': (1.0, 0.65, 0.0),
    'purple': (0.5, 0.0, 0.5),
    'pink': (1.0, 0.75, 0.8),
    'brown': (0.65, 0.16, 0.16),
    'white': (1.0, 1.0, 1.0),
    'black': (0.0, 0.0, 0.0),
    'gray': (0.5, 0.5, 0.5),
    'grey': (0.5, 0.5, 0.5),
    'silver': (0.75, 0.75, 0.75),
    'gold': (1.0, 0.84, 0.0),
    'cyan': (0.0, 1.0, 1.0),
    'magenta': (1.0, 0.0, 1.0),
    'lime': (0.0, 1.0, 0.0),
    'navy': (0.0, 0.0, 0.5),
    'teal': (0.0, 0.5, 0.5),
    'olive': (0.5, 0.5, 0.0),
    'maroon': (0.5, 0.0, 0.0),
}


class ColorParser:
    """
    Parse all color value formats with auto-detection.

    Supports:
    - Named colors: "red", "aluminum", "palette-name"
    - Hex: "#FF0000", "#0066CC80" (with alpha)
    - RGB arrays: [1.0, 0.0, 0.0]
    - RGBA arrays: [1.0, 0.0, 0.0, 0.5]
    - RGB objects: {r: 255, g: 0, b: 0}
    - HSL objects: {h: 0, s: 100, l: 50}
    """

    def __init__(self, palette: Optional[Dict[str, Any]] = None):
        """
        Args:
            palette: Optional color palette dictionary from 'colors:' section
        """
        self.palette = palette or {}
        self.material_library = get_material_library()

    def parse(self, value: Any) -> Color:
        """
        Auto-detect format and parse color value.

        Args:
            value: Color value in any supported format

        Returns:
            Color object with RGBA values

        Raises:
            ColorParseError: If format is invalid
        """
        if value is None:
            raise ColorParseError("Color value cannot be None")

        if isinstance(value, str):
            return self._parse_string(value)
        elif isinstance(value, list):
            return self._parse_array(value)
        elif isinstance(value, dict):
            return self._parse_object(value)
        else:
            raise ColorParseError(
                f"Invalid color format: {type(value).__name__}. "
                f"Expected string, list, or dict.",
                value=value
            )

    def _parse_string(self, s: str) -> Color:
        """Parse string: named color or hex"""
        s = s.strip()

        if s.startswith('#'):
            return self._parse_hex(s)
        else:
            return self._parse_named(s)

    def _parse_hex(self, hex_str: str) -> Color:
        """
        Parse hex color: #RGB, #RRGGBB, #RRGGBBAA

        Examples:
            #F00 -> red
            #FF0000 -> red
            #FF000080 -> red, 50% transparent
        """
        hex_str = hex_str.strip()

        if not hex_str.startswith('#'):
            raise ColorParseError(f"Hex color must start with #: {hex_str}", value=hex_str)

        hex_digits = hex_str[1:]

        # Validate hex characters
        if not re.match(r'^[0-9A-Fa-f]+$', hex_digits):
            raise ColorParseError(
                f"Invalid hex color: {hex_str}. Must contain only 0-9, A-F.",
                value=hex_str
            )

        # Parse based on length
        if len(hex_digits) == 3:
            # #RGB -> #RRGGBB
            r = int(hex_digits[0] * 2, 16) / 255
            g = int(hex_digits[1] * 2, 16) / 255
            b = int(hex_digits[2] * 2, 16) / 255
            return Color(r, g, b)

        elif len(hex_digits) == 6:
            # #RRGGBB
            r = int(hex_digits[0:2], 16) / 255
            g = int(hex_digits[2:4], 16) / 255
            b = int(hex_digits[4:6], 16) / 255
            return Color(r, g, b)

        elif len(hex_digits) == 8:
            # #RRGGBBAA
            r = int(hex_digits[0:2], 16) / 255
            g = int(hex_digits[2:4], 16) / 255
            b = int(hex_digits[4:6], 16) / 255
            a = int(hex_digits[6:8], 16) / 255
            return Color(r, g, b, a)

        else:
            raise ColorParseError(
                f"Invalid hex color length: {hex_str}. "
                f"Expected 3, 6, or 8 hex digits (got {len(hex_digits)}).",
                value=hex_str,
                suggestions=["#RGB", "#RRGGBB", "#RRGGBBAA"]
            )

    def _parse_named(self, name: str) -> Color:
        """
        Parse named color: basic color, material name, or palette reference

        Resolution order:
        1. Palette (from colors: section)
        2. Basic colors (red, blue, etc.)
        3. Material library (aluminum, steel, etc.)
        """
        name = name.strip().lower()

        # 1. Check palette first (user-defined colors take precedence)
        if name in self.palette:
            # Recursively parse palette value (could be hex, RGB, etc.)
            palette_value = self.palette[name]
            return self.parse(palette_value)

        # 2. Check basic colors
        if name in BASIC_COLORS:
            r, g, b = BASIC_COLORS[name]
            return Color(r, g, b)

        # 3. Check material library
        try:
            material = self.material_library.get(name)
            r, g, b = material.color
            return Color(r, g, b)
        except ValueError:
            # Material not found - provide helpful suggestions
            pass

        # Color not found - build error with suggestions
        suggestions = self._find_similar_colors(name)

        raise ColorParseError(
            f"Unknown color name: '{name}'. "
            f"Not found in palette, basic colors, or material library.",
            value=name,
            suggestions=suggestions
        )

    def _parse_array(self, arr: List[float]) -> Color:
        """
        Parse RGB or RGBA array (0-1 range).

        Examples:
            [1.0, 0.0, 0.0] -> red
            [1.0, 0.0, 0.0, 0.5] -> red, 50% transparent
        """
        if len(arr) == 3:
            r, g, b = arr
            self._validate_range(r, g, b, value_range=(0, 1))
            return Color(r, g, b)

        elif len(arr) == 4:
            r, g, b, a = arr
            self._validate_range(r, g, b, a, value_range=(0, 1))
            return Color(r, g, b, a)

        else:
            raise ColorParseError(
                f"Invalid RGB array length: {len(arr)}. Expected 3 (RGB) or 4 (RGBA).",
                value=arr,
                suggestions=["[r, g, b]", "[r, g, b, a]"]
            )

    def _parse_object(self, obj: Dict[str, Any]) -> Color:
        """
        Parse color object: RGB (0-255) or HSL format

        RGB: {r: 255, g: 0, b: 0, a: 128}
        HSL: {h: 0, s: 100, l: 50, a: 0.5}
        """
        # Check if HSL (has 'h' key)
        if 'h' in obj:
            return self._parse_hsl(obj)

        # Otherwise assume RGB
        elif 'r' in obj and 'g' in obj and 'b' in obj:
            return self._parse_rgb_object(obj)

        else:
            raise ColorParseError(
                f"Invalid color object. Expected 'r,g,b' or 'h,s,l' keys.",
                value=obj,
                suggestions=["{r: 255, g: 0, b: 0}", "{h: 0, s: 100, l: 50}"]
            )

    def _parse_rgb_object(self, obj: Dict[str, Any]) -> Color:
        """Parse RGB object (0-255 range)"""
        r = obj['r']
        g = obj['g']
        b = obj['b']
        a = obj.get('a', 255)  # Default alpha = 255 (opaque)

        # Validate ranges (0-255)
        self._validate_range(r, g, b, a, value_range=(0, 255))

        # Convert to 0-1 range
        return Color(r / 255, g / 255, b / 255, a / 255)

    def _parse_hsl(self, obj: Dict[str, Any]) -> Color:
        """
        Parse HSL object

        h: 0-360 (hue in degrees)
        s: 0-100 (saturation %)
        l: 0-100 (lightness %)
        a: 0-1 (alpha, optional)
        """
        h = obj['h']
        s = obj['s']
        l = obj['l']
        a = obj.get('a', 1.0)

        # Validate ranges
        if not (0 <= h <= 360):
            raise ColorParseError(f"HSL hue must be 0-360 degrees: {h}", value=obj)
        if not (0 <= s <= 100):
            raise ColorParseError(f"HSL saturation must be 0-100%: {s}", value=obj)
        if not (0 <= l <= 100):
            raise ColorParseError(f"HSL lightness must be 0-100%: {l}", value=obj)
        if not (0 <= a <= 1):
            raise ColorParseError(f"HSL alpha must be 0-1: {a}", value=obj)

        # Convert HSL to RGB (normalize to 0-1 range)
        r, g, b = hsl_to_rgb(h / 360, s / 100, l / 100)
        return Color(r, g, b, a)

    def _validate_range(self, *values, value_range: Tuple[float, float]):
        """Validate that all values are in range"""
        min_val, max_val = value_range
        for val in values:
            if not isinstance(val, (int, float)):
                raise ColorParseError(
                    f"Color value must be a number: {val} ({type(val).__name__})"
                )
            if not (min_val <= val <= max_val):
                raise ColorParseError(
                    f"Color value {val} out of range ({min_val}-{max_val})"
                )

    def _find_similar_colors(self, name: str) -> List[str]:
        """Find similar color names for suggestions"""
        suggestions = []

        # Check basic colors
        for color_name in BASIC_COLORS.keys():
            if name in color_name or color_name in name:
                suggestions.append(color_name)

        # Check material library (limit to 5 suggestions)
        material_names = self.material_library.list_all()
        for mat_name in material_names:
            if name in mat_name or mat_name in name:
                suggestions.append(mat_name)

        # Check palette
        for palette_name in self.palette.keys():
            if name in palette_name or palette_name in name:
                suggestions.append(f"{palette_name} (from palette)")

        return suggestions[:5]  # Limit to 5 suggestions
