"""
Validation Constants for TiaCAD Assembly Validator

Centralized location for all validation thresholds and magic numbers.
"""


class ValidationConstants:
    """Validation thresholds and limits"""

    # Distance tolerances (mm)
    DEFAULT_TOLERANCE = 0.1  # Default distance tolerance for connectivity checks
    PROXIMITY_TOLERANCE = 0.1  # Floating point comparison tolerance

    # Dimension limits (mm)
    MIN_DIMENSION = 0.001  # Minimum dimension before considering degenerate
    SUSPICIOUS_SMALL_DIMENSION = 0.01  # Dimensions smaller than this trigger warnings
    LARGE_DIMENSION = 1000.0  # Dimensions larger than this may indicate unit errors

    # Hole proximity safety factors
    HOLE_EDGE_SAFETY_FACTOR = 1.2  # Multiply hole radius by this for safe edge distance
    FEATURE_EXTENSION_TOLERANCE = 0.1  # mm - allow features to extend slightly beyond bounds

    # Numeric thresholds
    MIN_PARTS_FOR_CONNECTIVITY_CHECK = 2  # Need at least 2 parts to check connectivity

    # Formatting
    SUMMARY_LINE_WIDTH = 70  # Character width for report summary separator
