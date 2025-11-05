"""
Metadata utilities for operation builders

Defines which metadata should propagate through operations
and provides centralized copying logic.

This ensures visual properties (color, material, etc.) are preserved
when creating derived parts through transforms, boolean ops, patterns, etc.
"""

from typing import Dict, Any, Optional


# Define which metadata keys should propagate through operations
# These are appearance/material properties that should be inherited
PROPAGATING_METADATA = {
    'color',           # Appearance color (RGBA tuple)
    'material',        # Named material reference
    'transparency',    # Alpha override (future)
    'texture',         # Texture reference (future)
    'finish',          # Surface finish (future)
}

# Define which metadata is operation-specific (never propagate)
# These describe the part's creation, not its appearance
OPERATION_SPECIFIC_METADATA = {
    'primitive_type',   # Original primitive (box, cylinder, etc.)
    'source',          # Source part name
    'operation_type',  # Transform, boolean, pattern, etc.
    'boolean_op',      # Union, difference, intersection
    'pattern_type',    # Linear, circular, grid
    'pattern_index',   # Index in pattern array
    'grid_position',   # (row, col) in grid pattern
    'angle',           # Rotation angle in circular pattern
}


def copy_propagating_metadata(
    source_metadata: Optional[Dict[str, Any]],
    target_metadata: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Copy appearance/material metadata from source to target.

    This ensures visual properties (color, material, etc.) propagate
    through operations unless explicitly overridden.

    Args:
        source_metadata: Metadata from input part (can be None or empty dict)
        target_metadata: Operation-specific metadata (source, type, etc.)
        overrides: Optional explicit overrides for specific keys

    Returns:
        Merged metadata dictionary with operation metadata + appearance metadata

    Example:
        >>> source = {'color': (1.0, 0, 0, 1.0), 'primitive_type': 'box'}
        >>> target = {'operation_type': 'transform', 'source': 'red_box'}
        >>> result = copy_propagating_metadata(source, target)
        >>> result
        {
            'operation_type': 'transform',
            'source': 'red_box',
            'color': (1.0, 0, 0, 1.0)  # ✅ Copied from source
        }
        # Note: 'primitive_type' NOT copied (operation-specific to source)

    Example with override:
        >>> overrides = {'color': (0, 1.0, 0, 1.0)}  # Override to green
        >>> result = copy_propagating_metadata(source, target, overrides)
        >>> result['color']
        (0, 1.0, 0, 1.0)  # ✅ Override takes precedence
    """
    # Start with operation-specific metadata
    result = dict(target_metadata)

    # Copy propagating metadata from source (if source exists)
    if source_metadata:
        for key in PROPAGATING_METADATA:
            if key in source_metadata:
                result[key] = source_metadata[key]

    # Apply any explicit overrides (highest priority)
    if overrides:
        result.update(overrides)

    return result


def merge_metadata(
    *metadata_dicts: Optional[Dict[str, Any]],
    prefer_last: bool = True
) -> Dict[str, Any]:
    """
    Merge multiple metadata dictionaries.

    Useful for combining metadata from multiple sources.

    Args:
        *metadata_dicts: Variable number of metadata dicts to merge
        prefer_last: If True, later dicts override earlier ones.
                     If False, earlier dicts take precedence.

    Returns:
        Merged metadata dictionary

    Example:
        >>> base = {'color': (1, 0, 0, 1), 'material': 'metal'}
        >>> override = {'color': (0, 1, 0, 1)}
        >>> merge_metadata(base, override, prefer_last=True)
        {'color': (0, 1, 0, 1), 'material': 'metal'}  # Green overrides red
    """
    result = {}

    dicts = metadata_dicts if prefer_last else reversed(metadata_dicts)
    for metadata in dicts:
        if metadata:
            result.update(metadata)

    return result
