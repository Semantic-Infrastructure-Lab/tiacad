"""
Missing Position Rule for TiaCAD Assembly Validator

Detects parts that are defined but never positioned or used in operations.
"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class MissingPositionRule(ValidationRule):
    """
    Find parts that are defined but never positioned or used.

    This catches issues like:
    - Parts defined in 'parts' section but not referenced in operations
    - Parts not exported
    - Orphaned parts that serve no purpose
    """

    @property
    def name(self) -> str:
        return "Missing Position Check"

    @property
    def category(self) -> str:
        return "positioning"

    def check(self, document) -> List[ValidationIssue]:
        """Find unpositioned parts in the document."""
        issues = []

        # Get all defined base parts (not operations)
        all_parts = self._get_all_parts(document)

        # Get parts referenced in operations
        used_parts = self._get_used_parts(document)

        # Get exported parts
        exported_parts = self._get_exported_parts(document)

        # Parts should either be used in operations or exported
        positioned_or_exported = used_parts | exported_parts

        # Find unpositioned primitives
        unpositioned = all_parts - positioned_or_exported

        # Filter out operations (they're generated parts, not base parts)
        unpositioned = self._filter_out_operations(document, unpositioned)

        # Create issues for each unpositioned part
        for part_name in unpositioned:
            issues.append(self._create_missing_position_issue(part_name))

        return issues

    def _get_all_parts(self, document) -> set:
        """Get set of all defined parts in document."""
        if hasattr(document.parts, 'list_parts'):
            return set(document.parts.list_parts())
        return set()

    def _get_used_parts(self, document) -> set:
        """Get set of parts referenced in operations."""
        used_parts = set()

        if not hasattr(document, 'operations') or not document.operations:
            return used_parts

        for _op_name, operation in document.operations.items():
            # Add input parts
            if hasattr(operation, 'input'):
                used_parts.add(operation.input)

            # Add base parts
            if hasattr(operation, 'base'):
                used_parts.add(operation.base)

            # Add subtracted parts (boolean operations)
            if hasattr(operation, 'subtract') and operation.subtract:
                used_parts.update(operation.subtract)

        return used_parts

    def _get_exported_parts(self, document) -> set:
        """Get set of parts listed in export configuration."""
        exported_parts = set()

        if not hasattr(document, 'export') or not document.export:
            return exported_parts

        # Get parts from export list
        if hasattr(document.export, 'parts') and document.export.parts:
            exported_parts = {p.get('name') or p for p in document.export.parts}

        # Get default export part
        if hasattr(document.export, 'default_part') and document.export.default_part:
            exported_parts.add(document.export.default_part)

        return exported_parts

    def _filter_out_operations(self, document, parts: set) -> set:
        """Remove operation-generated parts from set."""
        if hasattr(document, 'operations') and document.operations:
            operation_names = set(document.operations.keys())
            return parts - operation_names
        return parts

    def _create_missing_position_issue(self, part_name: str) -> ValidationIssue:
        """Create ValidationIssue for missing position."""
        return ValidationIssue(
            severity=Severity.WARNING,
            category=self.category,
            part_name=part_name,
            message=f"Part '{part_name}' defined but never positioned or exported",
            suggestion="Add transform operation, export part, or remove if unused"
        )
