"""
Unit tests for TiaCAD Assembly Validator

Tests validation of common design issues:
- Disconnected parts
- Missing positions
- Invalid parameters
- Geometric issues
"""

import pytest
from tiacad_core.validation.assembly_validator import (
    AssemblyValidator,
    ValidationReport,
    ValidationIssue,
    Severity
)
from tiacad_core.parser.tiacad_parser import TiaCADParser


class TestValidationIssue:
    """Test ValidationIssue data structure"""

    def test_create_issue(self):
        issue = ValidationIssue(
            severity=Severity.ERROR,
            category="geometry",
            message="Test error",
            part_name="test_part",
            suggestion="Fix it"
        )

        assert issue.severity == Severity.ERROR
        assert issue.category == "geometry"
        assert issue.message == "Test error"
        assert issue.part_name == "test_part"
        assert issue.suggestion == "Fix it"

    def test_issue_to_string(self):
        issue = ValidationIssue(
            severity=Severity.WARNING,
            category="connectivity",
            message="Parts disconnected",
            suggestion="Check positions"
        )

        result = str(issue)
        assert "[WARNING]" in result
        assert "(connectivity)" in result
        assert "Parts disconnected" in result
        assert "Check positions" in result

    def test_issue_to_dict(self):
        issue = ValidationIssue(
            severity=Severity.INFO,
            category="parameters",
            message="Info message"
        )

        d = issue.to_dict()
        assert d['severity'] == "INFO"
        assert d['category'] == "parameters"
        assert d['message'] == "Info message"


class TestValidationReport:
    """Test ValidationReport functionality"""

    def test_empty_report(self):
        report = ValidationReport()

        assert report.error_count == 0
        assert report.warning_count == 0
        assert report.info_count == 0
        assert report.passed is True
        assert len(report.issues) == 0

    def test_add_issues(self):
        report = ValidationReport()

        report.add_issue(ValidationIssue(
            severity=Severity.ERROR,
            category="test",
            message="Error 1"
        ))

        report.add_issue(ValidationIssue(
            severity=Severity.WARNING,
            category="test",
            message="Warning 1"
        ))

        report.add_issue(ValidationIssue(
            severity=Severity.INFO,
            category="test",
            message="Info 1"
        ))

        assert report.error_count == 1
        assert report.warning_count == 1
        assert report.info_count == 1
        assert report.passed is False

    def test_report_to_json(self):
        report = ValidationReport()
        report.add_issue(ValidationIssue(
            severity=Severity.ERROR,
            category="test",
            message="Test"
        ))

        json_str = report.to_json()
        assert "ERROR" in json_str
        assert "test" in json_str
        assert "passed" in json_str
        assert "false" in json_str.lower()


class TestAssemblyValidator:
    """Test AssemblyValidator core functionality"""

    def test_create_validator(self):
        validator = AssemblyValidator()
        assert validator.tolerance == 0.1

        validator_custom = AssemblyValidator(tolerance=0.5)
        assert validator_custom.tolerance == 0.5

    def test_parameter_sanity_negative_dimensions(self):
        """Test detection of negative dimensions"""

        class MockDoc:
            parameters = {
                'width': -10,
                'height': 20,
                'length': -5
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1  # Should catch negative width
        assert any('width' in i.message.lower() for i in errors)

    def test_parameter_sanity_zero_dimensions(self):
        """Test detection of zero dimensions"""

        class MockDoc:
            parameters = {
                'beam_width': 0,
                'height': 20
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1
        assert any('beam_width' in i.message for i in errors)

    def test_parameter_sanity_valid_dimensions(self):
        """Test that valid dimensions pass"""

        class MockDoc:
            parameters = {
                'width': 100,
                'height': 75,
                'depth': 10
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_parameter_sanity_suspiciously_small(self):
        """Test detection of suspiciously small dimensions"""

        class MockDoc:
            parameters = {
                'width': 0.001,  # Very small but not zero
                'height': 20
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        warnings = [i for i in issues if i.severity == Severity.WARNING]
        assert len(warnings) >= 1
        assert any('small' in i.message.lower() for i in warnings)


class TestValidatorIntegration:
    """Integration tests using real YAML files"""

    def test_validate_color_demo(self):
        """Test validation on working color demo file"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/color_demo.yaml')

        report = validator.validate_document(doc)

        # Should have no critical errors
        assert report.error_count == 0

    def test_validate_multi_material_demo(self):
        """Test validation on working multi-material demo"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/multi_material_demo.yaml')

        report = validator.validate_document(doc)

        # Should have no critical errors
        assert report.error_count == 0

    def test_validate_guitar_hanger_broken(self):
        """Test validation catches issues in broken guitar hanger"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/guitar_hanger_with_holes.yaml')

        report = validator.validate_document(doc)

        # Should detect missing beam position
        positioning_warnings = [
            i for i in report.issues
            if i.category == "positioning" and 'beam' in (i.part_name or '').lower()
        ]

        assert len(positioning_warnings) > 0, "Should detect beam not positioned"

    def test_validate_guitar_hanger_fixed(self):
        """Test validation on fixed guitar hanger"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/guitar_hanger_named_points.yaml')

        report = validator.validate_document(doc)

        # Fixed design should pass (no errors, warnings are OK)
        assert report.error_count == 0


class TestConnectivityChecks:
    """Test disconnected parts detection"""

    def test_find_connected_components_simple(self):
        """Test connected component detection with simple graph"""
        validator = AssemblyValidator()

        # Graph: A-B, C-D (two components)
        adjacency = {
            'A': {'B'},
            'B': {'A'},
            'C': {'D'},
            'D': {'C'}
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 2
        assert {'A', 'B'} in components
        assert {'C', 'D'} in components

    def test_find_connected_components_all_connected(self):
        """Test when all parts are connected"""
        validator = AssemblyValidator()

        # Graph: A-B-C (one component)
        adjacency = {
            'A': {'B'},
            'B': {'A', 'C'},
            'C': {'B'}
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 1
        assert components[0] == {'A', 'B', 'C'}

    def test_find_connected_components_isolated(self):
        """Test detection of isolated parts"""
        validator = AssemblyValidator()

        # Graph: A-B, C (isolated), D (isolated)
        adjacency = {
            'A': {'B'},
            'B': {'A'},
            'C': set(),
            'D': set()
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 3  # A-B (connected), C (isolated), D (isolated)
        assert {'A', 'B'} in components
        assert {'C'} in components
        assert {'D'} in components


def test_validation_report_summary(capsys):
    """Test that validation report prints correctly"""
    report = ValidationReport()

    report.add_issue(ValidationIssue(
        severity=Severity.ERROR,
        category="test",
        message="Test error"
    ))

    report.add_issue(ValidationIssue(
        severity=Severity.WARNING,
        category="test",
        message="Test warning"
    ))

    report.print_summary()

    captured = capsys.readouterr()
    assert "ERRORS" in captured.out
    assert "WARNINGS" in captured.out
    assert "Test error" in captured.out
    assert "Test warning" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
