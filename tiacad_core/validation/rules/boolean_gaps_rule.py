"""Boolean Gaps Rule - detects gaps in union operations"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class BooleanGapsRule(ValidationRule):
    """Detect gaps in union/join operations that may indicate parts aren't touching."""

    @property
    def name(self) -> str:
        return "Boolean Gaps Check"

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

                    if op_type == 'boolean' and op_operation == 'union':
                        base_name = self._get_operation_attr(operation, 'base') or self._get_operation_attr(operation, 'input')
                        add_names = self._get_operation_attr(operation, 'add', [])

                        if not base_name or not add_names:
                            continue

                        if base_name in parts_dict:
                            base_part = parts_dict[base_name]
                            if hasattr(base_part, 'geometry') and base_part.geometry is not None:
                                base_bbox = self._get_bounding_box(base_part.geometry)

                                for add_name in add_names:
                                    if add_name in parts_dict:
                                        add_part = parts_dict[add_name]
                                        if hasattr(add_part, 'geometry') and add_part.geometry is not None:
                                            add_bbox = self._get_bounding_box(add_part.geometry)
                                            if not self._boxes_are_close(base_bbox, add_bbox):
                                                gap = self._calculate_bbox_gap(base_bbox, add_bbox)
                                                issues.append(ValidationIssue(
                                                    severity=Severity.WARNING,
                                                    category=self.category,
                                                    message=f"Union '{op_name}': parts '{base_name}' and '{add_name}' may not be touching (gap ≈ {gap:.2f}mm)",
                                                    suggestion="Verify parts are positioned to touch or overlap. Union of disconnected parts creates separate bodies."
                                                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message=f"Boolean gap check skipped: {str(e)}"
            ))
        return issues

    def _boxes_are_close(self, bbox1, bbox2) -> bool:
        """Check if two bounding boxes are within tolerance distance."""
        x_close = not (bbox1.xmax + self.tolerance < bbox2.xmin or bbox2.xmax + self.tolerance < bbox1.xmin)
        y_close = not (bbox1.ymax + self.tolerance < bbox2.ymin or bbox2.ymax + self.tolerance < bbox1.ymin)
        z_close = not (bbox1.zmax + self.tolerance < bbox2.zmin or bbox2.zmax + self.tolerance < bbox1.zmin)
        return x_close and y_close and z_close

    def _calculate_bbox_gap(self, bbox1, bbox2) -> float:
        """Calculate the approximate minimum gap between two bounding boxes."""
        x_gap = max(0, max(bbox1.xmin - bbox2.xmax, bbox2.xmin - bbox1.xmax))
        y_gap = max(0, max(bbox1.ymin - bbox2.ymax, bbox2.ymin - bbox1.ymax))
        z_gap = max(0, max(bbox1.zmin - bbox2.zmax, bbox2.zmin - bbox1.zmax))
        return max(x_gap, y_gap, z_gap)
