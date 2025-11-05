"""
Parameter Sanity Rule for TiaCAD Assembly Validator

Validates that parameter values make geometric sense.
"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class ParameterSanityRule(ValidationRule):
    """
    Validate parameter values make geometric sense.

    Checks for:
    - Negative dimensions
    - Zero dimensions
    - Suspiciously small values
    """

    # Keywords that indicate dimension parameters
    DIMENSION_KEYWORDS = ['width', 'height', 'length', 'depth', 'radius', 'diameter', 'thickness']

    @property
    def name(self) -> str:
        return "Parameter Sanity Check"

    @property
    def category(self) -> str:
        return "parameters"

    def check(self, document) -> List[ValidationIssue]:
        """Validate all parameters in document."""
        issues = []

        if not hasattr(document, 'parameters') or not document.parameters:
            return issues

        for param_name, value in document.parameters.items():
            param_issues = self._check_parameter(param_name, value)
            issues.extend(param_issues)

        return issues

    def _check_parameter(self, param_name: str, value) -> List[ValidationIssue]:
        """Check a single parameter for sanity."""
        issues = []

        # Only check dimension parameters
        if not self._is_dimension_parameter(param_name):
            return issues

        try:
            numeric_value = float(value)

            if numeric_value <= 0:
                issues.append(self._create_invalid_dimension_issue(param_name, numeric_value))
            elif numeric_value < self.constants.SUSPICIOUS_SMALL_DIMENSION:
                issues.append(self._create_suspicious_dimension_issue(param_name, numeric_value))

        except (ValueError, TypeError):
            # Not a numeric value, skip
            pass

        return issues

    def _is_dimension_parameter(self, param_name: str) -> bool:
        """Check if parameter name indicates a dimension."""
        param_lower = param_name.lower()
        return any(keyword in param_lower for keyword in self.DIMENSION_KEYWORDS)

    def _create_invalid_dimension_issue(self, param_name: str, value: float) -> ValidationIssue:
        """Create issue for invalid (non-positive) dimension."""
        return ValidationIssue(
            severity=Severity.ERROR,
            category=self.category,
            message=f"Invalid dimension: {param_name}={value}",
            suggestion="Dimensions must be positive values"
        )

    def _create_suspicious_dimension_issue(self, param_name: str, value: float) -> ValidationIssue:
        """Create issue for suspiciously small dimension."""
        return ValidationIssue(
            severity=Severity.WARNING,
            category=self.category,
            message=f"Suspiciously small dimension: {param_name}={value}mm",
            suggestion="Verify this dimension is correct"
        )
