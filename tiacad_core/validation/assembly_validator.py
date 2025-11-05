"""
Assembly Validator for TiaCAD

Validates TiaCAD assemblies for common design issues such as:
- Disconnected parts
- Missing position operations
- Invalid parameter values
- Geometric impossibilities

Refactored 2025-11-03: Now uses rule-based architecture for better maintainability.
"""

from typing import List, Optional, Dict

# Import common types
from .validation_constants import ValidationConstants
from .validation_types import Severity, ValidationIssue, ValidationReport

# Import validation rules
from .rules import (
    MissingPositionRule,
    DisconnectedPartsRule,
    HoleEdgeProximityRule,
    ParameterSanityRule,
    BoundingBoxRule,
    BooleanGapsRule,
    FeatureBoundsRule,
    UnusedPartsRule,
)

# Re-export for backward compatibility
__all__ = ['AssemblyValidator', 'ValidationReport', 'ValidationIssue', 'Severity']


class AssemblyValidator:
    """
    Validates TiaCAD assemblies for common design issues.

    Uses rule-based architecture where each validation check is implemented
    as an independent, testable rule.

    Example usage:
        validator = AssemblyValidator()
        report = validator.validate_document(document)
        if not report.passed:
            report.print_summary()
    """

    def __init__(self, tolerance: float = ValidationConstants.DEFAULT_TOLERANCE):
        """
        Initialize validator with validation rules.

        Args:
            tolerance: Distance tolerance for connectivity checks (mm)
        """
        self.tolerance = tolerance
        self.constants = ValidationConstants

        # Initialize validation rules
        self.rules = [
            MissingPositionRule(tolerance),
            ParameterSanityRule(tolerance),
            UnusedPartsRule(tolerance),
            BoundingBoxRule(tolerance),
            DisconnectedPartsRule(tolerance),
            HoleEdgeProximityRule(tolerance),
            BooleanGapsRule(tolerance),
            FeatureBoundsRule(tolerance),
        ]

    def _add_yaml_location(self, issue: ValidationIssue, document, yaml_path: Optional[List] = None):
        """
        Add YAML location information to a validation issue.

        Args:
            issue: ValidationIssue to enhance
            document: TiaCADDocument with line tracking
            yaml_path: Optional YAML path (e.g., ["parts", "plate"])
        """
        if not hasattr(document, 'line_tracker') or not document.line_tracker:
            return

        # Determine YAML path
        if yaml_path is None and issue.part_name:
            yaml_path = ["parts", issue.part_name]

        if not yaml_path:
            return

        # Get location from line tracker
        location = document.line_tracker.get(yaml_path)
        if location:
            line, column = location
            issue.location = {
                'line': line,
                'column': column,
                'path': yaml_path,
                'file_path': getattr(document, 'file_path', None)
            }

    def validate_document(self, document) -> ValidationReport:
        """
        Perform all validation checks on a TiaCAD document.

        Uses rule-based architecture - each rule runs independently and
        contributes its findings to the report.

        Args:
            document: TiaCADDocument instance

        Returns:
            ValidationReport with all issues found
        """
        report = ValidationReport()

        # Run all validation rules
        for rule in self.rules:
            try:
                issues = rule.check(document)
                report.issues.extend(issues)
            except Exception as e:
                # If a rule fails completely, add a warning but continue
                report.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    category="system",
                    message=f"Validation rule '{rule.name}' failed: {str(e)}",
                    suggestion="This may indicate a bug in the validator"
                ))

        # Add YAML location information to all issues
        for issue in report.issues:
            self._add_yaml_location(issue, document)

        return report

    # ========================================================================
    # BACKWARD COMPATIBILITY: Legacy check methods delegate to rules
    # These methods are kept for backward compatibility but now use the
    # rule-based architecture internally.
    # ========================================================================

    def check_missing_positions(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to MissingPositionRule."""
        return MissingPositionRule(self.tolerance).check(document)

    def check_parameter_sanity(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to ParameterSanityRule."""
        return ParameterSanityRule(self.tolerance).check(document)

    def check_unused_parts(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to UnusedPartsRule."""
        return UnusedPartsRule(self.tolerance).check(document)

    def check_bounding_boxes(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to BoundingBoxRule."""
        return BoundingBoxRule(self.tolerance).check(document)

    def check_disconnected_parts(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to DisconnectedPartsRule."""
        return DisconnectedPartsRule(self.tolerance).check(document)

    def check_hole_edge_proximity(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to HoleEdgeProximityRule."""
        return HoleEdgeProximityRule(self.tolerance).check(document)

    def check_boolean_gaps(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to BooleanGapsRule."""
        return BooleanGapsRule(self.tolerance).check(document)

    def check_feature_bounds(self, document) -> List[ValidationIssue]:
        """Legacy method - delegates to FeatureBoundsRule."""
        return FeatureBoundsRule(self.tolerance).check(document)

    # Helper method for backward compatibility with tests
    def _find_connected_components(self, adjacency: Dict) -> List:
        """Legacy helper - delegates to DisconnectedPartsRule implementation."""
        from typing import Set
        rule = DisconnectedPartsRule(self.tolerance)
        return rule._find_connected_components(adjacency)
