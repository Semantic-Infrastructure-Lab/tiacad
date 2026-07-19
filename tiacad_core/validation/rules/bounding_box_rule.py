"""Bounding Box Rule - checks for degenerate or suspiciously large geometries"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class BoundingBoxRule(ValidationRule):
    """Analyze bounding boxes for geometric issues."""

    @property
    def name(self) -> str:
        return "Bounding Box Check"

    @property
    def category(self) -> str:
        return "geometry"

    def _check_part_bbox(self, part_name: str, part) -> List[ValidationIssue]:
        """Return bounding box issues for a single part."""
        try:
            bbox = self._get_bounding_box(part)
            dims = [bbox.xlen, bbox.ylen, bbox.zlen]
            issues = []
            if any(d < self.constants.MIN_DIMENSION for d in dims):
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category=self.category,
                    part_name=part_name,
                    message=f"Part has near-zero dimension: [{dims[0]:.4f}, {dims[1]:.4f}, {dims[2]:.4f}]",
                    suggestion="Check part definition - may be degenerate geometry",
                    world_position=self._part_center(part)
                ))
            if any(d > self.constants.LARGE_DIMENSION for d in dims):
                issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category=self.category,
                    part_name=part_name,
                    message=f"Large part detected: max dimension = {max(dims):.1f}mm",
                    suggestion="Verify dimensions are in millimeters",
                    world_position=self._part_center(part)
                ))
            return issues
        except Exception as e:
            return [ValidationIssue(
                severity=Severity.WARNING,
                category=self.category,
                part_name=part_name,
                message=f"Could not compute bounding box: {str(e)}",
                suggestion="Part geometry may be invalid"
            )]

    def check(self, document) -> List[ValidationIssue]:
        issues = []
        try:
            parts_dict = self._get_parts_dict(document)
            for part_name, part in parts_dict.items():
                if not hasattr(part, 'geometry') or part.geometry is None:
                    continue
                issues.extend(self._check_part_bbox(part_name, part))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category=self.category,
                message=f"Bounding box analysis skipped: {str(e)}"
            ))
        return issues
