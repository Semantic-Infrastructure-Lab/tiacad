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

    def check(self, document) -> List[ValidationIssue]:
        issues = []
        try:
            parts_dict = self._get_parts_dict(document)
            if hasattr(document, 'operations') and document.operations:
                for op_name, operation in document.operations.items():
                    op_type = self._get_operation_attr(operation, 'type')
                    op_operation = self._get_operation_attr(operation, 'operation')
                    subtract_list = self._get_operation_attr(operation, 'subtract', [])

                    if op_type == 'boolean' and op_operation == 'difference' and subtract_list:
                        base_name = self._get_operation_attr(operation, 'base') or self._get_operation_attr(operation, 'input')

                        if not base_name or base_name not in parts_dict:
                            continue

                        base_part = parts_dict[base_name]
                        if not hasattr(base_part, 'geometry') or base_part.geometry is None:
                            continue

                        base_bbox = self._get_bounding_box(base_part.geometry)

                        for subtract_name in subtract_list:
                            if subtract_name not in parts_dict:
                                continue

                            subtract_part = parts_dict[subtract_name]
                            if not hasattr(subtract_part, 'geometry') or subtract_part.geometry is None:
                                continue

                            subtract_bbox = self._get_bounding_box(subtract_part.geometry)
                            extends_beyond = []
                            tol = self.constants.FEATURE_EXTENSION_TOLERANCE

                            if subtract_bbox.xmin < base_bbox.xmin - tol:
                                extends_beyond.append(f"X-min by {base_bbox.xmin - subtract_bbox.xmin:.2f}mm")
                            if subtract_bbox.xmax > base_bbox.xmax + tol:
                                extends_beyond.append(f"X-max by {subtract_bbox.xmax - base_bbox.xmax:.2f}mm")
                            if subtract_bbox.ymin < base_bbox.ymin - tol:
                                extends_beyond.append(f"Y-min by {base_bbox.ymin - subtract_bbox.ymin:.2f}mm")
                            if subtract_bbox.ymax > base_bbox.ymax + tol:
                                extends_beyond.append(f"Y-max by {subtract_bbox.ymax - base_bbox.ymax:.2f}mm")
                            if subtract_bbox.zmin < base_bbox.zmin - tol:
                                extends_beyond.append(f"Z-min by {base_bbox.zmin - subtract_bbox.zmin:.2f}mm")
                            if subtract_bbox.zmax > base_bbox.zmax + tol:
                                extends_beyond.append(f"Z-max by {subtract_bbox.zmax - base_bbox.zmax:.2f}mm")

                            if extends_beyond:
                                issues.append(ValidationIssue(
                                    severity=Severity.INFO,
                                    category=self.category,
                                    part_name=subtract_name,
                                    message=f"Feature '{subtract_name}' extends beyond parent '{base_name}': {', '.join(extends_beyond)}",
                                    suggestion="This is often intentional for through-holes, but verify if unexpected"
                                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message=f"Feature bounds check skipped: {str(e)}"
            ))
        return issues
