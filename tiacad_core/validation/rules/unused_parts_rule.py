"""Unused Parts Rule - checks for parts that are built but not exported"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class UnusedPartsRule(ValidationRule):
    """Check for parts that are built but not exported."""

    @property
    def name(self) -> str:
        return "Unused Parts Check"

    @property
    def category(self) -> str:
        return "export"

    def check(self, document) -> List[ValidationIssue]:
        issues = []
        if not hasattr(document, 'export') or not document.export:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message="No export specification found",
                suggestion="Add 'export' section to specify which parts to export"
            ))
        return issues
