"""
Hole Edge Proximity Rule for TiaCAD Assembly Validator

Detects holes positioned too close to edges that may get chopped off.
"""

from typing import List, Tuple
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class HoleEdgeProximityRule(ValidationRule):
    """
    Detect holes positioned too close to edges.

    Checks for:
    - Cylindrical holes near face boundaries
    - Holes that may get chopped off during boolean operations
    - Insufficient material around holes for structural integrity

    Example issue: Guitar hanger with hole too close to edge, causing
    the hole to be partially cut off when the part is exported.
    """

    @property
    def name(self) -> str:
        return "Hole Edge Proximity Check"

    @property
    def category(self) -> str:
        return "geometry"

    def check(self, document) -> List[ValidationIssue]:
        """Check for holes too close to edges."""
        issues = []

        try:
            parts_dict = self._get_parts_dict(document)

            # Check all boolean difference operations (holes)
            if hasattr(document, 'operations') and document.operations:
                for op_name, operation in document.operations.items():
                    operation_issues = self._check_operation(operation, parts_dict)
                    issues.extend(operation_issues)

        except Exception as e:
            issues.append(self._create_skip_issue(str(e)))

        return issues

    def _check_operation(self, operation, parts_dict: dict) -> List[ValidationIssue]:
        """Check a single operation for hole proximity issues."""
        issues = []

        # Only check boolean difference operations (holes)
        if not self._is_boolean_difference(operation):
            return issues

        # Get base part and hole parts
        base_name = self._get_base_name(operation)
        subtract_list = self._get_operation_attr(operation, 'subtract', [])

        if not base_name or not subtract_list or base_name not in parts_dict:
            return issues

        base_part = parts_dict[base_name]
        if not self._has_valid_geometry(base_part):
            return issues

        base_bbox = self._get_bounding_box(base_part.geometry)

        # Check each hole
        for hole_name in subtract_list:
            hole_issues = self._check_hole_proximity(
                hole_name, parts_dict, base_name, base_bbox
            )
            issues.extend(hole_issues)

        return issues

    def _is_boolean_difference(self, operation) -> bool:
        """Check if operation is a boolean difference (hole)."""
        op_type = self._get_operation_attr(operation, 'type')
        op_operation = self._get_operation_attr(operation, 'operation')
        return op_type == 'boolean' and op_operation == 'difference'

    def _get_base_name(self, operation) -> str:
        """Get base part name from operation."""
        return (self._get_operation_attr(operation, 'base') or
                self._get_operation_attr(operation, 'input'))

    def _has_valid_geometry(self, part) -> bool:
        """Check if part has valid geometry."""
        return hasattr(part, 'geometry') and part.geometry is not None

    def _check_hole_proximity(self, hole_name: str, parts_dict: dict,
                             base_name: str, base_bbox) -> List[ValidationIssue]:
        """Check if a single hole is too close to edges."""
        issues = []

        if hole_name not in parts_dict:
            return issues

        hole_part = parts_dict[hole_name]
        if not self._has_valid_geometry(hole_part):
            return issues

        hole_bbox = self._get_bounding_box(hole_part.geometry)

        # Calculate hole properties
        hole_center = self._calculate_bbox_center(hole_bbox)
        hole_radius = self._estimate_hole_radius(hole_bbox)

        # Check proximity to each face
        edge_warnings = self._check_all_faces(hole_center, hole_radius, base_bbox)

        if edge_warnings:
            issues.append(self._create_proximity_issue(
                hole_name, base_name, edge_warnings, hole_radius
            ))

        return issues

    def _calculate_bbox_center(self, bbox) -> Tuple[float, float, float]:
        """Calculate center point of bounding box."""
        center_x = (bbox.xmin + bbox.xmax) / 2
        center_y = (bbox.ymin + bbox.ymax) / 2
        center_z = (bbox.zmin + bbox.zmax) / 2
        return (center_x, center_y, center_z)

    def _estimate_hole_radius(self, bbox) -> float:
        """Estimate hole radius from bounding box (max of half-dimensions)."""
        return max(bbox.xlen, bbox.ylen, bbox.zlen) / 2

    def _check_all_faces(self, hole_center: Tuple[float, float, float],
                         hole_radius: float, base_bbox) -> List[str]:
        """
        Check proximity to all faces of base part.

        Returns list of warning strings for faces that are too close.
        """
        edge_warnings = []
        hole_x, hole_y, hole_z = hole_center
        safe_distance = hole_radius * self.constants.HOLE_EDGE_SAFETY_FACTOR

        # X-axis faces
        self._check_face_proximity(
            hole_x, base_bbox.xmin, base_bbox.xmax,
            safe_distance, "X", edge_warnings
        )

        # Y-axis faces
        self._check_face_proximity(
            hole_y, base_bbox.ymin, base_bbox.ymax,
            safe_distance, "Y", edge_warnings
        )

        # Z-axis faces
        self._check_face_proximity(
            hole_z, base_bbox.zmin, base_bbox.zmax,
            safe_distance, "Z", edge_warnings
        )

        return edge_warnings

    def _check_face_proximity(self, hole_pos: float, bbox_min: float, bbox_max: float,
                              safe_distance: float, axis: str, warnings: List[str]):
        """
        Check proximity to min/max faces on a single axis.

        Args:
            hole_pos: Hole center position on this axis
            bbox_min: Base part minimum on this axis
            bbox_max: Base part maximum on this axis
            safe_distance: Minimum safe distance
            axis: Axis name (X, Y, or Z)
            warnings: List to append warnings to (modified in place)
        """
        dist_to_min = abs(hole_pos - bbox_min)
        dist_to_max = abs(hole_pos - bbox_max)

        if dist_to_min < safe_distance:
            warnings.append(f"{axis}-min face (distance: {dist_to_min:.2f}mm)")

        if dist_to_max < safe_distance:
            warnings.append(f"{axis}-max face (distance: {dist_to_max:.2f}mm)")

    def _create_proximity_issue(self, hole_name: str, base_name: str,
                                edge_warnings: List[str], hole_radius: float) -> ValidationIssue:
        """Create ValidationIssue for hole too close to edge."""
        return ValidationIssue(
            severity=Severity.WARNING,
            category=self.category,
            part_name=hole_name,
            message=f"Hole '{hole_name}' very close to edge(s) of '{base_name}': {', '.join(edge_warnings)}",
            suggestion=f"Move hole inward by at least {hole_radius:.2f}mm from edges to avoid getting chopped off"
        )

    def _create_skip_issue(self, error_message: str) -> ValidationIssue:
        """Create issue when check is skipped due to error."""
        return ValidationIssue(
            severity=Severity.INFO,
            category=self.category,
            message=f"Hole edge proximity check skipped: {error_message}"
        )
