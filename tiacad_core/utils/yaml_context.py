"""
YAML Error Context Formatter

Provides utilities for formatting errors with YAML context and caret pointers.
Used by exception classes to show helpful error messages.
"""

from typing import Optional, List


def get_line_context(
    yaml_string: str,
    line: int,
    column: int = 0,
    context_lines: int = 2
) -> tuple[List[str], int]:
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

    # Calculate range (line is 1-indexed, list is 0-indexed)
    error_line_0indexed = line - 1
    start_line = max(0, error_line_0indexed - context_lines)
    end_line = min(len(lines), error_line_0indexed + context_lines + 1)

    # Extract context
    context = lines[start_line:end_line]
    error_line_idx = error_line_0indexed - start_line

    return context, error_line_idx


def format_error_with_context(
    message: str,
    yaml_string: str,
    line: Optional[int] = None,
    column: Optional[int] = None,
    filename: Optional[str] = None,
    suggestion: Optional[str] = None,
    context_lines: int = 2
) -> str:
    """
    Format an error message with YAML context and caret pointer.

    Args:
        message: Error message
        yaml_string: Original YAML string (for context)
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        filename: Filename for error message
        suggestion: Optional suggestion
        context_lines: Number of lines before/after to show

    Returns:
        Formatted error message with context

    Example output:
        Error in design.yaml:67:7
          67 |  bolt_circle:
          68 |    type: pattern
          69 |    input: bolt_hol
                          ^^^^^^^^
          70 |

        Part 'bolt_hol' not found. Did you mean 'bolt_hole'?

        💡 Check the input part name
    """
    if line is None:
        # No line info, return simple format
        parts = []
        if filename:
            parts.append(f"Error in {filename}")
        parts.append(message)
        if suggestion:
            parts.append(f"💡 {suggestion}")
        return "\n".join(parts)

    # Build error header
    header_parts = []
    if filename:
        header = f"Error in {filename}:{line}"
        if column is not None:
            header += f":{column}"
        header_parts.append(header)
    else:
        header = f"Error at line {line}"
        if column is not None:
            header += f", column {column}"
        header_parts.append(header)

    # Get context lines
    context_text_lines, error_idx = get_line_context(
        yaml_string, line, column or 0, context_lines
    )

    # Format context with line numbers
    context_parts = []
    for i, context_line in enumerate(context_text_lines):
        line_num = line - error_idx + i
        prefix = f"{line_num:6d} | "
        context_parts.append(prefix + context_line)

        # Add caret pointer on error line
        if i == error_idx and column is not None and column > 0:
            # Calculate caret position
            caret_pos = len(prefix) + column - 1
            # Determine caret length (highlight the token)
            caret_len = min(10, len(context_line) - column + 1)
            if caret_len < 1:
                caret_len = 1
            caret = " " * caret_pos + "^" * caret_len
            context_parts.append(caret)

    # Assemble full message
    result = []
    result.extend(header_parts)
    result.append("")  # Blank line
    result.extend(context_parts)
    result.append("")  # Blank line
    result.append(message)

    if suggestion:
        result.append("")
        result.append(f"💡 {suggestion}")

    return "\n".join(result)
