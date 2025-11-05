"""
Color utility functions - pure mathematical transformations

These are stateless utility functions for color space conversions
and manipulations.
"""

from typing import Tuple


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[float, float, float]:
    """
    Convert HSL (0-1 range) to RGB (0-1 range)

    Algorithm from CSS Color Module Level 3

    Args:
        h: Hue (0-1 range, 0=red, 0.33=green, 0.67=blue)
        s: Saturation (0-1 range, 0=gray, 1=full color)
        l: Lightness (0-1 range, 0=black, 0.5=pure, 1=white)

    Returns:
        (r, g, b) tuple in 0-1 range

    Examples:
        >>> hsl_to_rgb(0, 1, 0.5)  # Pure red
        (1.0, 0.0, 0.0)

        >>> hsl_to_rgb(0.33, 1, 0.5)  # Pure green
        (0.0, 1.0, 0.0)

        >>> hsl_to_rgb(0, 0, 0.5)  # Gray (no saturation)
        (0.5, 0.5, 0.5)
    """
    if s == 0:
        # Achromatic (gray) - no saturation
        return (l, l, l)

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        """Helper to convert hue to RGB component"""
        # Normalize t to 0-1 range
        if t < 0:
            t += 1
        if t > 1:
            t -= 1

        # Calculate RGB value based on hue segment
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    # Calculate intermediate values
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    # Calculate RGB components with hue offset
    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return (r, g, b)


def hex_to_rgb(hex_str: str) -> Tuple[float, float, float, float]:
    """
    Convert hex color string to RGBA tuple

    Supports:
    - #RGB (3 digits)
    - #RRGGBB (6 digits)
    - #RRGGBBAA (8 digits with alpha)

    Args:
        hex_str: Hex color string (with or without #)

    Returns:
        (r, g, b, a) tuple in 0-1 range

    Raises:
        ValueError: If hex string is invalid format

    Examples:
        >>> hex_to_rgb("#F00")
        (1.0, 0.0, 0.0, 1.0)

        >>> hex_to_rgb("#FF0000")
        (1.0, 0.0, 0.0, 1.0)

        >>> hex_to_rgb("#FF000080")
        (1.0, 0.0, 0.0, 0.5)
    """
    # Remove # if present
    hex_str = hex_str.lstrip('#')

    # Parse based on length
    if len(hex_str) == 3:
        # #RGB -> expand to #RRGGBB
        r = int(hex_str[0] * 2, 16) / 255
        g = int(hex_str[1] * 2, 16) / 255
        b = int(hex_str[2] * 2, 16) / 255
        a = 1.0

    elif len(hex_str) == 6:
        # #RRGGBB
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        a = 1.0

    elif len(hex_str) == 8:
        # #RRGGBBAA
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        a = int(hex_str[6:8], 16) / 255

    else:
        raise ValueError(
            f"Invalid hex length: {len(hex_str)}. "
            f"Expected 3, 6, or 8 hex digits."
        )

    return (r, g, b, a)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """
    Convert RGB (0-1) to hex string

    Args:
        r: Red (0-1)
        g: Green (0-1)
        b: Blue (0-1)

    Returns:
        Hex string #RRGGBB

    Examples:
        >>> rgb_to_hex(1.0, 0.0, 0.0)
        '#FF0000'

        >>> rgb_to_hex(0.5, 0.5, 0.5)
        '#808080'
    """
    r_int = int(r * 255)
    g_int = int(g * 255)
    b_int = int(b * 255)
    return f"#{r_int:02X}{g_int:02X}{b_int:02X}"


def validate_rgb_range(*values: float) -> None:
    """
    Validate RGB values are in 0-1 range

    Args:
        *values: Variable number of RGB values

    Raises:
        ValueError: If any value is not a number or out of range

    Examples:
        >>> validate_rgb_range(0.5, 0.6, 0.7)  # OK

        >>> validate_rgb_range(1.5, 0.0, 0.0)  # Raises ValueError
    """
    for val in values:
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"RGB value must be a number: {val} ({type(val).__name__})"
            )
        if not (0 <= val <= 1):
            raise ValueError(
                f"RGB value {val} out of range (must be 0-1)"
            )


def validate_rgb_255_range(*values: float) -> None:
    """
    Validate RGB values are in 0-255 range

    Args:
        *values: Variable number of RGB values (0-255)

    Raises:
        ValueError: If any value is not a number or out of range
    """
    for val in values:
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"RGB value must be a number: {val} ({type(val).__name__})"
            )
        if not (0 <= val <= 255):
            raise ValueError(
                f"RGB value {val} out of range (must be 0-255)"
            )


def validate_hsl_range(h: float, s: float, l: float) -> None:
    """
    Validate HSL values are in correct ranges

    Args:
        h: Hue (0-360 degrees)
        s: Saturation (0-100 %)
        l: Lightness (0-100 %)

    Raises:
        ValueError: If values are out of range
    """
    if not (0 <= h <= 360):
        raise ValueError(f"HSL hue must be 0-360 degrees: {h}")
    if not (0 <= s <= 100):
        raise ValueError(f"HSL saturation must be 0-100%: {s}")
    if not (0 <= l <= 100):
        raise ValueError(f"HSL lightness must be 0-100%: {l}")


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp a value to a range

    Args:
        value: Value to clamp
        min_val: Minimum value (default 0.0)
        max_val: Maximum value (default 1.0)

    Returns:
        Clamped value

    Examples:
        >>> clamp(1.5)
        1.0

        >>> clamp(-0.5)
        0.0

        >>> clamp(0.5)
        0.5
    """
    return max(min_val, min(max_val, value))
