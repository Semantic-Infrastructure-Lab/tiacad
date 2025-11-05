"""
Tests for enhanced error messages with YAML line tracking.

Tests:
- Exception creation with line context
- Error formatting with caret pointers
- YAML context extraction
- Path-based error messages
"""

import pytest
from tiacad_core.utils.exceptions import TiaCADError
from tiacad_core.utils.yaml_context import (
    get_line_context,
    format_error_with_context
)
from tiacad_core.parser.tiacad_parser import TiaCADParserError


class TestBasicErrorMessages:
    """Test basic error message formatting"""

    def test_simple_error(self):
        """Simple error message (backward compatible)"""
        error = TiaCADError("Something went wrong")
        assert "Something went wrong" in str(error)

    def test_error_with_path(self):
        """Error with key path"""
        error = TiaCADError(
            "Part not found",
            path=["parts", "box1", "input"]
        )
        error_str = str(error)
        assert "Part not found" in error_str
        assert "parts → box1 → input" in error_str

    def test_error_with_line(self):
        """Error with line number"""
        error = TiaCADError(
            "Invalid value",
            line=42
        )
        error_str = str(error)
        assert "Invalid value" in error_str
        assert "42" in error_str

    def test_error_with_file(self):
        """Error with file path"""
        error = TiaCADError(
            "Parse error",
            file_path="design.yaml",
            line=15,
            column=10
        )
        error_str = str(error)
        assert "design.yaml" in error_str
        assert "15" in error_str
        assert "10" in error_str

    def test_error_with_suggestion(self):
        """Error with suggestion"""
        error = TiaCADError(
            "Part 'box' not found",
            suggestion="Did you mean 'plate'?"
        )
        error_str = str(error)
        assert "Part 'box' not found" in error_str
        assert "Did you mean 'plate'?" in error_str
        assert "💡" in error_str


class TestYAMLContext:
    """Test YAML context extraction and formatting"""

    def test_get_line_context(self):
        """Extract context lines around error"""
        yaml_str = "\n".join([
            "line 1",
            "line 2",
            "line 3",  # Error here (line 3)
            "line 4",
            "line 5"
        ])

        context, error_idx = get_line_context(yaml_str, line=3, context_lines=1)

        # Should get lines 2, 3, 4 (1 before, error, 1 after)
        assert len(context) == 3
        assert context[0] == "line 2"
        assert context[1] == "line 3"
        assert context[2] == "line 4"
        assert error_idx == 1  # Error is at index 1 in context

    def test_get_line_context_at_start(self):
        """Context at start of file"""
        yaml_str = "\n".join([
            "line 1",  # Error here
            "line 2",
            "line 3"
        ])

        context, error_idx = get_line_context(yaml_str, line=1, context_lines=2)

        assert context[0] == "line 1"
        assert error_idx == 0

    def test_get_line_context_at_end(self):
        """Context at end of file"""
        yaml_str = "\n".join([
            "line 1",
            "line 2",
            "line 3"  # Error here
        ])

        context, error_idx = get_line_context(yaml_str, line=3, context_lines=2)

        assert context[-1] == "line 3"
        assert error_idx == len(context) - 1


class TestErrorFormatting:
    """Test complete error formatting with context"""

    def test_format_error_simple(self):
        """Format error without line info"""
        error_msg = format_error_with_context(
            message="Invalid value",
            yaml_string="parts:\n  box: invalid",
            line=None
        )

        assert "Invalid value" in error_msg
        # Should not include context without line number
        assert "|" not in error_msg

    def test_format_error_with_context(self):
        """Format error with YAML context"""
        yaml_str = """metadata:
  name: Test

parts:
  box:
    primitive: invalid_type
    size: [10, 10, 10]
"""

        error_msg = format_error_with_context(
            message="Invalid primitive type",
            yaml_string=yaml_str,
            line=6,
            column=16,
            filename="test.yaml"
        )

        # Check components
        assert "test.yaml" in error_msg
        assert "6" in error_msg
        assert "Invalid primitive type" in error_msg
        assert "primitive: invalid_type" in error_msg
        assert "^" in error_msg  # Caret pointer
        assert "|" in error_msg  # Line separators

    def test_format_error_with_suggestion(self):
        """Format error with suggestion"""
        yaml_str = "parts:\n  box:\n    primitive: box"

        error_msg = format_error_with_context(
            message="Part not found",
            yaml_string=yaml_str,
            line=2,
            column=3,
            suggestion="Check part name spelling"
        )

        assert "💡" in error_msg
        assert "Check part name spelling" in error_msg


class TestEnhancedExceptions:
    """Test enhanced exception classes"""

    def test_tiacad_error_attributes(self):
        """TiaCADError stores all attributes"""
        error = TiaCADError(
            message="Test error",
            path=["parts", "box1"],
            line=10,
            column=5,
            file_path="test.yaml",
            suggestion="Fix it"
        )

        assert error.message == "Test error"
        assert error.path == ["parts", "box1"]
        assert error.line == 10
        assert error.column == 5
        assert error.file_path == "test.yaml"
        assert error.suggestion == "Fix it"

    def test_tiacad_error_with_context(self):
        """TiaCADError.with_context() method"""
        yaml_str = "line1\nline2\nerror here\nline4"

        error = TiaCADError(
            "Test error",
            line=3,
            column=1
        )

        context_msg = error.with_context(yaml_str)

        assert "error here" in context_msg
        assert "|" in context_msg
        assert "^" in context_msg

    def test_parser_error_with_yaml(self):
        """TiaCADParserError with YAML string"""
        yaml_str = "parts:\n  box:\n    primitive: box"

        error = TiaCADParserError(
            message="Parse error",
            file_path="test.yaml",
            line=2,
            column=3,
            yaml_string=yaml_str
        )

        # __str__ should include context
        error_str = str(error)
        assert "box:" in error_str
        assert "|" in error_str


class TestRealWorldExamples:
    """Test with realistic error scenarios"""

    def test_missing_part_error(self):
        """Error for missing part reference"""
        yaml_str = """parts:
  plate:
    primitive: box
    size: [100, 100, 10]

operations:
  subtract:
    type: boolean
    operation: difference
    base: plate
    subtract: [nonexistent_hole]
"""

        error = TiaCADError(
            'Part "nonexistent_hole" not found',
            path=["operations", "subtract", "subtract"],
            line=11,
            column=16,
            file_path="design.yaml",
            suggestion="Available parts: plate"
        )

        error_msg = error.with_context(yaml_str)

        assert "nonexistent_hole" in error_msg
        assert "design.yaml:11:16" in error_msg
        assert "Available parts: plate" in error_msg
        assert "^" in error_msg

    def test_invalid_primitive_error(self):
        """Error for invalid primitive type"""
        yaml_str = """parts:
  box1:
    primitive: square
    size: [10, 10, 10]
"""

        error = TiaCADError(
            "Invalid primitive type 'square'",
            path=["parts", "box1", "primitive"],
            line=3,
            column=16,
            file_path="design.yaml",
            suggestion="Valid primitives: box, cylinder, sphere, cone, torus"
        )

        error_msg = error.with_context(yaml_str)

        assert "square" in error_msg
        assert "Valid primitives" in error_msg

    def test_parameter_error(self):
        """Error in parameter expression"""
        yaml_str = """parameters:
  width: 100
  height: ${width * invalid}

parts:
  box: {...}
"""

        error = TiaCADError(
            "Invalid parameter expression",
            path=["parameters", "height"],
            line=3,
            column=22,
            file_path="design.yaml",
            suggestion="Check expression syntax"
        )

        error_msg = error.with_context(yaml_str)

        assert "invalid" in error_msg
        assert "expression" in error_msg


class TestBackwardCompatibility:
    """Ensure backward compatibility with old code"""

    def test_old_style_simple_error(self):
        """Old-style simple error still works"""
        try:
            raise TiaCADError("Old style error")
        except TiaCADError as e:
            assert str(e) == "Old style error"

    def test_parser_error_old_style(self):
        """Old-style TiaCADParserError still works"""
        try:
            raise TiaCADParserError("Parse failed", file_path="test.yaml")
        except TiaCADParserError as e:
            assert "Parse failed" in str(e)
            assert "test.yaml" in str(e)
