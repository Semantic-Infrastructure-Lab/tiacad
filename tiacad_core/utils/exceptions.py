"""
TiaCAD Exception Hierarchy

Defines all custom exceptions used throughout TiaCAD.
Provides better error handling and debugging than generic exceptions.

Enhanced with YAML line tracking for better error messages.
"""

from typing import Optional, List


class TiaCADError(Exception):
    """
    Base exception for all TiaCAD errors.

    Supports YAML line tracking for better error messages.

    Args:
        message: Error message
        path: Key path where error occurred (e.g., ["parts", "box1"])
        line: Line number in YAML file (1-indexed)
        column: Column number in YAML file (1-indexed)
        file_path: Path to YAML file
        suggestion: Optional suggestion for fixing the error
    """

    def __init__(
        self,
        message: str,
        path: Optional[List[str]] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        file_path: Optional[str] = None,
        suggestion: Optional[str] = None,
        yaml_string: Optional[str] = None
    ):
        self.message = message
        self.path = path
        self.line = line
        self.column = column
        self.file_path = file_path
        self.suggestion = suggestion
        self.yaml_string = yaml_string

        # Build formatted message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with location context"""
        # If yaml_string provided, use with_context() for full formatting
        if self.yaml_string and self.line is not None:
            return self.with_context(self.yaml_string)

        parts = []

        # Location info
        if self.file_path:
            location = f"Error in {self.file_path}"
            if self.line is not None:
                location += f":{self.line}"
                if self.column is not None:
                    location += f":{self.column}"
            parts.append(location)
        elif self.line is not None:
            location = f"Error at line {self.line}"
            if self.column is not None:
                location += f", column {self.column}"
            parts.append(location)

        # Path info
        if self.path:
            path_str = " → ".join(str(p) for p in self.path)
            parts.append(f"At: {path_str}")

        # Main message
        parts.append(self.message)

        # Suggestion
        if self.suggestion:
            parts.append(f"💡 {self.suggestion}")

        return "\n".join(parts) if len(parts) > 1 else parts[0] if parts else self.message

    def with_context(
        self,
        yaml_string: str,
        context_lines: int = 2
    ) -> str:
        """
        Format error with YAML context and caret pointer.

        Args:
            yaml_string: Original YAML content
            context_lines: Number of lines before/after to show

        Returns:
            Formatted error message with context
        """
        from .yaml_context import format_error_with_context

        return format_error_with_context(
            message=self.message,
            yaml_string=yaml_string,
            line=self.line,
            column=self.column,
            filename=self.file_path,
            suggestion=self.suggestion,
            context_lines=context_lines
        )


class GeometryError(TiaCADError):
    """Errors related to geometry operations"""
    pass


class InvalidGeometryError(GeometryError):
    """Geometry is invalid, empty, or cannot be processed"""
    pass


class TransformError(TiaCADError):
    """Errors during transform operations"""
    pass


class SelectorError(TiaCADError):
    """Errors during selector resolution"""
    pass


class PointResolutionError(TiaCADError):
    """Errors during point resolution"""
    pass
