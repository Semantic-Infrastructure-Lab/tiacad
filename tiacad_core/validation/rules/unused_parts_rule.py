"""Unused Parts Rule - checks for parts that are built but never used or exported"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class UnusedPartsRule(ValidationRule):
    """
    Find parts (primitives or operation results) that are built but never
    consumed — not referenced as an input/base/subtract by another operation,
    and not exported. Unlike MissingPositionRule (which only looks at base
    primitives), this also catches dead-end operation results: geometry that
    was built but whose output goes nowhere.
    """

    @property
    def name(self) -> str:
        return "Unused Parts Check"

    @property
    def category(self) -> str:
        return "export"

    def check(self, document) -> List[ValidationIssue]:
        issues = []

        export_config = getattr(document, 'export_config', None) or {}
        if not export_config.get('default_part') and not export_config.get('parts'):
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message="No export specification found",
                suggestion="Add 'export' section to specify which parts to export"
            ))

        parts_dict = self._get_parts_dict(document)
        used_parts = self._get_used_parts(document)
        exported_parts = self._get_exported_parts(document)
        unused = set(parts_dict.keys()) - used_parts - exported_parts

        for part_name in sorted(unused):
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category=self.category,
                part_name=part_name,
                message=f"Part '{part_name}' is built but never used by another operation or exported",
                suggestion="Export this part, reference it from another operation, or remove it if it's dead work",
                world_position=self._part_center(parts_dict[part_name]),
            ))

        return issues
