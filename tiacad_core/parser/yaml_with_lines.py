"""
YAML Parser with Line Number Tracking

Provides YAML parsing that preserves line and column information for better error messages.

Features:
- Parse YAML with line/column tracking
- Map keys to their source locations
- Format errors with file context and caret pointers
- Support for nested structures

Usage:
    from tiacad_core.parser.yaml_with_lines import parse_yaml_with_lines, format_error

    data, line_map = parse_yaml_with_lines(yaml_string, filename="design.yaml")

    # Later, when error occurs:
    error_msg = format_error(
        message="Part 'box' not found",
        path=["parts", "box1", "input"],
        line_map=line_map,
        yaml_string=yaml_string,
        filename="design.yaml"
    )
"""

import yaml
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path


class LineTracker:
    """
    Tracks line and column numbers for YAML keys.

    Stores a mapping from key paths to (line, column) tuples.
    """

    def __init__(self):
        self.line_map: Dict[str, Tuple[int, int]] = {}

    def add(self, path: List[str], line: int, column: int):
        """Add line info for a key path"""
        key = ".".join(str(p) for p in path)
        self.line_map[key] = (line, column)

    def get(self, path: List[str]) -> Optional[Tuple[int, int]]:
        """Get line info for a key path"""
        key = ".".join(str(p) for p in path)
        return self.line_map.get(key)

    def get_str(self, path_str: str) -> Optional[Tuple[int, int]]:
        """Get line info for a string path"""
        return self.line_map.get(path_str)


class LinePreservingLoader(yaml.SafeLoader):
    """
    YAML loader that preserves line and column information.

    Adds __line__ and __column__ metadata to dictionaries.
    """
    pass


def construct_mapping_with_lines(loader: yaml.SafeLoader, node: yaml.Node):
    """Construct mapping while preserving line numbers"""
    loader.flatten_mapping(node)
    mapping = {}

    # Store line info for the mapping itself
    mapping['__line__'] = node.start_mark.line + 1  # 1-indexed
    mapping['__column__'] = node.start_mark.column + 1

    # Construct all key-value pairs
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)
        value = loader.construct_object(value_node, deep=False)

        # Store line info for this key
        if isinstance(value, dict):
            # If value is dict, it will have its own __line__
            pass
        elif isinstance(key, str):
            # Store line info for scalar values
            mapping[f'__line_{key}__'] = value_node.start_mark.line + 1
            mapping[f'__column_{key}__'] = value_node.start_mark.column + 1

        mapping[key] = value

    return mapping


def construct_sequence_with_lines(loader: yaml.SafeLoader, node: yaml.Node):
    """Construct sequence while preserving line numbers"""
    sequence = loader.construct_sequence(node, deep=False)

    # For sequences, we wrap in a dict with line info
    return {
        '__type__': 'sequence',
        '__line__': node.start_mark.line + 1,
        '__column__': node.start_mark.column + 1,
        '__value__': sequence
    }


# Register custom constructors
LinePreservingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping_with_lines
)


def parse_yaml_with_lines(
    yaml_string: str,
    filename: Optional[str] = None
) -> Tuple[Dict[str, Any], LineTracker]:
    """
    Parse YAML string and return data with line tracking.

    Args:
        yaml_string: YAML content as string
        filename: Optional filename for error messages

    Returns:
        Tuple of (parsed_data, line_tracker)

    Example:
        data, line_map = parse_yaml_with_lines(yaml_str, "design.yaml")
        line, col = line_map.get(["parts", "box1"])
    """
    # Parse with line-preserving loader
    try:
        data = yaml.load(yaml_string, Loader=LinePreservingLoader)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")

    # Build line tracker
    tracker = LineTracker()
    _extract_line_info(data, [], tracker)

    # Clean up __line__ metadata from data
    _clean_metadata(data)

    return data, tracker


def _extract_line_info(obj: Any, path: List[str], tracker: LineTracker):
    """Recursively extract line info from parsed structure"""
    if isinstance(obj, dict):
        # Get line info for this dict
        if '__line__' in obj:
            line = obj['__line__']
            column = obj.get('__column__', 0)
            tracker.add(path, line, column)

        # Process all keys
        for key, value in obj.items():
            if key.startswith('__') and key.endswith('__'):
                continue  # Skip metadata

            # Check if we have specific line info for this key
            line_key = f'__line_{key}__'
            if line_key in obj:
                line = obj[line_key]
                column = obj.get(f'__column_{key}__', 0)
                tracker.add(path + [key], line, column)

            # Recurse
            _extract_line_info(value, path + [key], tracker)

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _extract_line_info(item, path + [str(i)], tracker)


def _clean_metadata(obj: Any):
    """Remove __line__ and __column__ metadata from structure"""
    if isinstance(obj, dict):
        # Remove metadata keys
        keys_to_remove = [k for k in obj.keys() if k.startswith('__') and k.endswith('__')]
        for key in keys_to_remove:
            del obj[key]

        # Recurse
        for value in obj.values():
            _clean_metadata(value)

    elif isinstance(obj, list):
        for item in obj:
            _clean_metadata(item)


def get_line_context(
    yaml_string: str,
    line: int,
    column: int,
    context_lines: int = 2
) -> Tuple[List[str], int]:
    """
    Get lines of context around an error location.

    Args:
        yaml_string: Full YAML content
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        context_lines: Number of lines before/after to include

    Returns:
        Tuple of (lines_with_context, error_line_index)
    """
    lines = yaml_string.splitlines()

    # Calculate range
    start_line = max(0, line - context_lines - 1)
    end_line = min(len(lines), line + context_lines)

    # Extract context
    context = lines[start_line:end_line]
    error_line_idx = line - start_line - 1

    return context, error_line_idx


def format_error(
    message: str,
    path: Optional[List[str]] = None,
    line_map: Optional[LineTracker] = None,
    yaml_string: Optional[str] = None,
    filename: Optional[str] = None,
    line: Optional[int] = None,
    column: Optional[int] = None
) -> str:
    """
    Format an error message with YAML context and caret pointer.

    Args:
        message: Error message
        path: Key path where error occurred (e.g., ["parts", "box1", "primitive"])
        line_map: LineTracker from parse_yaml_with_lines
        yaml_string: Original YAML string (for context)
        filename: Filename for error message
        line: Optional explicit line number
        column: Optional explicit column number

    Returns:
        Formatted error message with context

    Example output:
        Error in design.yaml:67:7
          |  bolt_circle:
          |    type: pattern
          |    input: bolt_hol
                      ^^^^^^^^
        Part 'bolt_hol' not found. Did you mean 'bolt_hole'?
    """
    # Determine line and column
    if line is None and path and line_map:
        location = line_map.get(path)
        if location:
            line, column = location

    # Build error header
    parts = []
    if filename:
        parts.append(f"Error in {filename}")
    else:
        parts.append("Error")

    if line is not None:
        parts.append(f":{line}")
        if column is not None:
            parts.append(f":{column}")

    error_header = "".join(parts)

    # Add path if available
    if path:
        path_str = " → ".join(str(p) for p in path)
        error_header += f"\nAt: {path_str}"

    # Add context if we have line info and yaml content
    if line is not None and yaml_string:
        context_lines, error_idx = get_line_context(yaml_string, line, column or 0)

        # Format context
        context_parts = [error_header, ""]
        for i, context_line in enumerate(context_lines):
            # Add line number prefix
            line_num = line - error_idx + i
            prefix = f"{line_num:4d} | "
            context_parts.append(prefix + context_line)

            # Add caret pointer on error line
            if i == error_idx and column is not None:
                # Calculate caret position (account for line number prefix)
                caret_pos = len(prefix) + column - 1
                caret = " " * caret_pos + "^" * min(8, len(context_line) - column + 1)
                context_parts.append(caret)

        context_parts.append("")
        context_parts.append(message)

        return "\n".join(context_parts)

    # Fallback: simple format
    return f"{error_header}\n{message}"


def test_line_tracking():
    """Test the line tracking functionality"""
    yaml_content = """
metadata:
  name: Test Design
  author: TIA

parameters:
  width: 100
  height: 50

parts:
  plate:
    primitive: box
    size: [10, 20, 30]

  hole:
    primitive: cylinder
    radius: 5
"""

    print("Testing YAML Line Tracking")
    print("=" * 50)

    # Parse with line tracking
    data, line_map = parse_yaml_with_lines(yaml_content)

    # Test various paths
    test_paths = [
        ["metadata"],
        ["metadata", "name"],
        ["parameters"],
        ["parameters", "width"],
        ["parts"],
        ["parts", "plate"],
        ["parts", "plate", "primitive"],
        ["parts", "hole", "radius"]
    ]

    print("\nLine tracking results:")
    for path in test_paths:
        location = line_map.get(path)
        if location:
            line, col = location
            print(f"  {' → '.join(path):40s} Line {line:3d}, Col {col:2d}")

    # Test error formatting
    print("\n" + "=" * 50)
    print("Example error message:")
    print("=" * 50)

    error_msg = format_error(
        message="Part 'bolt_hol' not found. Did you mean 'bolt_hole'?",
        path=["parts", "plate", "primitive"],
        line_map=line_map,
        yaml_string=yaml_content,
        filename="test_design.yaml"
    )

    print(error_msg)

    return True


if __name__ == "__main__":
    test_line_tracking()
