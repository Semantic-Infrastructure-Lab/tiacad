"""Feature Bounds Rule - checks if features extend beyond their parent part bounds"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class FeatureBoundsRule(ValidationRule):
    """Check if features (holes, chamfers, etc.) extend beyond their parent part bounds."""

    @property
    def name(self) -> str:
        return "Feature Bounds Check"

    @property
    def category(self) -> str:
        return "geometry"

    def _bound_overflows(self, subtract_bbox, base_bbox, tol) -> List[str]:
        """Return descriptions of each dimension where subtract_bbox exceeds base_bbox by more than tol."""
        checks = [
            (subtract_bbox.xmin < base_bbox.xmin - tol, f"X-min by {base_bbox.xmin - subtract_bbox.xmin:.2f}mm"),
            (subtract_bbox.xmax > base_bbox.xmax + tol, f"X-max by {subtract_bbox.xmax - base_bbox.xmax:.2f}mm"),
            (subtract_bbox.ymin < base_bbox.ymin - tol, f"Y-min by {base_bbox.ymin - subtract_bbox.ymin:.2f}mm"),
            (subtract_bbox.ymax > base_bbox.ymax + tol, f"Y-max by {subtract_bbox.ymax - base_bbox.ymax:.2f}mm"),
            (subtract_bbox.zmin < base_bbox.zmin - tol, f"Z-min by {base_bbox.zmin - subtract_bbox.zmin:.2f}mm"),
            (subtract_bbox.zmax > base_bbox.zmax + tol, f"Z-max by {subtract_bbox.zmax - base_bbox.zmax:.2f}mm"),
        ]
        return [msg for cond, msg in checks if cond]

    def _check_difference_op(self, operation, parts_dict) -> List[ValidationIssue]:
        """Check one boolean-difference operation for bound overflows. Returns any issues found."""
        base_name = self._get_operation_attr(operation, 'base') or self._get_operation_attr(operation, 'input')
        if not base_name or base_name not in parts_dict:
            return []
        base_part = parts_dict[base_name]
        if not hasattr(base_part, 'geometry') or base_part.geometry is None:
            return []

        base_bbox = self._get_bounding_box(base_part.geometry)
        tol = self.constants.FEATURE_EXTENSION_TOLERANCE
        issues = []

        for subtract_name in self._get_operation_attr(operation, 'subtract', []):
            if subtract_name not in parts_dict:
                continue
            subtract_part = parts_dict[subtract_name]
            if not hasattr(subtract_part, 'geometry') or subtract_part.geometry is None:
                continue
            overflows = self._bound_overflows(
                self._get_bounding_box(subtract_part.geometry), base_bbox, tol
            )
            if overflows:
                issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category=self.category,
                    part_name=subtract_name,
                    message=f"Feature '{subtract_name}' extends beyond parent '{base_name}': {', '.join(overflows)}",
                    suggestion="This is often intentional for through-holes, but verify if unexpected"
                ))
        return issues

    def _is_difference_op(self, operation) -> bool:
        """Return True if this is a boolean difference op with subtract targets."""
        return (self._get_operation_attr(operation, 'type') == 'boolean'
                and self._get_operation_attr(operation, 'operation') == 'difference'
                and bool(self._get_operation_attr(operation, 'subtract', [])))

    def _check_operations(self, operations, parts_dict) -> List[ValidationIssue]:
        """Check all operations for feature bound overflows; return issues found."""
        issues = []
        for op_name, operation in operations.items():
            if self._is_difference_op(operation):
                issues.extend(self._check_difference_op(operation, parts_dict))
        return issues

    def check(self, document) -> List[ValidationIssue]:
        issues = []
        try:
            parts_dict = self._get_parts_dict(document)
            if hasattr(document, 'operations') and document.operations:
                issues.extend(self._check_operations(document.operations, parts_dict))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message=f"Feature bounds check skipped: {str(e)}"
            ))
        return issues
