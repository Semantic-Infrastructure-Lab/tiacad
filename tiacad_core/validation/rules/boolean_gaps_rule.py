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

    def _check_union_gap(self, op_name, operation, parts_dict) -> List[ValidationIssue]:
        """Check if union parts are close enough to touch; return gap issues."""
        issues = []
        base_name = self._get_operation_attr(operation, 'base') or self._get_operation_attr(operation, 'input')
        add_names = self._get_operation_attr(operation, 'add', [])
        if not base_name or not add_names or base_name not in parts_dict:
            return issues
        base_part = parts_dict[base_name]
        if not hasattr(base_part, 'geometry') or base_part.geometry is None:
            return issues
        base_bbox = self._get_bounding_box(base_part)
        for add_name in add_names:
            if add_name not in parts_dict:
                continue
            add_part = parts_dict[add_name]
            if not hasattr(add_part, 'geometry') or add_part.geometry is None:
                continue
            add_bbox = self._get_bounding_box(add_part)
            gap = self._get_gap(base_part, add_part, base_bbox, add_bbox)
            if gap > self.tolerance:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category=self.category,
                    message=f"Union '{op_name}': parts '{base_name}' and '{add_name}' may not be touching (gap ≈ {gap:.2f}mm)",
                    suggestion="Verify parts are positioned to touch or overlap. Union of disconnected parts creates separate bodies.",
                    world_position=self._gap_midpoint(base_part, add_part)
                ))
        return issues

    def _check_operations(self, operations, parts_dict) -> List[ValidationIssue]:
        """Check all operations for boolean union gaps; return issues found."""
        issues = []
        for op_name, operation in operations.items():
            if (self._get_operation_attr(operation, 'type') == 'boolean'
                    and self._get_operation_attr(operation, 'operation') == 'union'):
                issues.extend(self._check_union_gap(op_name, operation, parts_dict))
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
                message=f"Boolean gap check skipped: {str(e)}"
            ))
        return issues

    def _gap_midpoint(self, base_part, add_part):
        """
        World position for a gap issue: the midpoint between the two
        parts' centers, since the gap sits between them rather than
        inside either one. Falls back to whichever center is available
        if the other part's bbox lookup fails.
        """
        base_center = self._part_center(base_part)
        add_center = self._part_center(add_part)
        if base_center is None:
            return add_center
        if add_center is None:
            return base_center
        return tuple((b + a) / 2 for b, a in zip(base_center, add_center))

    def _get_gap(self, base_part, add_part, base_bbox, add_bbox) -> float:
        """
        Get the gap between two parts, using the real BREP distance query
        only when the bbox check can't settle it on its own.

        bbox is a sound lower bound on true distance: if the boxes
        aren't close, the real shapes are provably at least that far
        apart too, so there's no need to pay for an expensive boolean
        query -- the bbox-derived gap is reported directly. Only when
        the boxes *are* close (which a non-convex part, e.g. an
        L-shape, can report even when the real shapes don't touch) is
        the real query needed to disambiguate.
        """
        if not self._boxes_are_close(base_bbox, add_bbox):
            return self._calculate_bbox_gap(base_bbox, add_bbox)

        if base_part.backend is not None and add_part.backend is not None:
            return base_part.backend.get_distance(base_part.geometry, add_part.geometry)

        return 0.0

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
