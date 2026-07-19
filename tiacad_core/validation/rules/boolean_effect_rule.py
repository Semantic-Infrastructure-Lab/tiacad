"""Boolean Effect Rule - detects boolean operations that silently do nothing"""

from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class BooleanEffectRule(ValidationRule):
    """
    Detect boolean operations whose result volume shows no evidence of the
    operation having an effect:
      - difference: result volume must be measurably less than the base volume
      - intersection: result volume must be non-empty
      - union: result volume must be at least as large as its biggest input
        (a weaker sanity check than "every input contributed" — see
        docs/developer/MODEL_VALIDATION.md "Best Next Improvements" #1)

    Volume-range contracts alone do not catch this class of bug: a plate with
    no holes still has a volume inside a plausible range. This rule compares
    the operation's actual before/after volumes, which is checkable on every
    model with no per-model contract to write.
    """

    @property
    def name(self) -> str:
        return "Boolean Effect Check"

    @property
    def category(self) -> str:
        return "geometry"

    def _get_volume(self, part) -> float:
        from tiacad_core.testing.dimensions import get_volume, DimensionError
        try:
            return get_volume(part)
        except DimensionError:
            return None

    def _check_difference(self, op_name, operation, parts_dict) -> List[ValidationIssue]:
        issues = []
        base_name = self._get_operation_attr(operation, 'base')
        subtract_names = self._get_operation_attr(operation, 'subtract', [])
        if not base_name or not subtract_names or base_name not in parts_dict:
            return issues
        base_part = parts_dict[base_name]
        result_part = parts_dict.get(op_name)
        if result_part is None:
            return issues

        base_volume = self._get_volume(base_part)
        result_volume = self._get_volume(result_part)
        if base_volume is None or result_volume is None:
            return issues

        removed = base_volume - result_volume
        if removed <= self.constants.MIN_SIGNIFICANT_VOLUME:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category=self.category,
                message=(
                    f"Difference '{op_name}': removed {removed:.3f}mm³ from '{base_name}' "
                    f"({base_volume:.1f}mm³ → {result_volume:.1f}mm³) — subtract input(s) "
                    f"{subtract_names} may not intersect the base"
                ),
                part_name=op_name,
                suggestion="Verify the subtract geometry actually overlaps the base part. "
                           "A difference that removes ~0mm³ usually means the cutting tool "
                           "is positioned off the base entirely.",
                world_position=self._part_center(result_part),
            ))
        return issues

    def _check_intersection(self, op_name, operation, parts_dict) -> List[ValidationIssue]:
        issues = []
        result_part = parts_dict.get(op_name)
        if result_part is None:
            return issues
        result_volume = self._get_volume(result_part)
        if result_volume is None:
            return issues
        if result_volume <= self.constants.MIN_SIGNIFICANT_VOLUME:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category=self.category,
                message=f"Intersection '{op_name}': result volume is {result_volume:.3f}mm³ — inputs do not overlap",
                part_name=op_name,
                suggestion="Verify the intersecting parts actually share volume.",
                world_position=self._part_center(result_part),
            ))
        return issues

    def _check_union(self, op_name, operation, parts_dict) -> List[ValidationIssue]:
        issues = []
        input_names = self._get_operation_attr(operation, 'inputs', [])
        result_part = parts_dict.get(op_name)
        if not input_names or result_part is None:
            return issues

        input_volumes = []
        for input_name in input_names:
            input_part = parts_dict.get(input_name)
            if input_part is None:
                continue
            volume = self._get_volume(input_part)
            if volume is not None:
                input_volumes.append(volume)
        if not input_volumes:
            return issues

        result_volume = self._get_volume(result_part)
        if result_volume is None:
            return issues

        max_input_volume = max(input_volumes)
        if result_volume < max_input_volume - self.constants.MIN_SIGNIFICANT_VOLUME:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category=self.category,
                message=(
                    f"Union '{op_name}': result volume {result_volume:.1f}mm³ is smaller than "
                    f"its largest input ({max_input_volume:.1f}mm³) — the union is geometrically impossible"
                ),
                part_name=op_name,
                suggestion="This usually indicates a backend/geometry error rather than a positioning mistake.",
                world_position=self._part_center(result_part),
            ))
        return issues

    def _check_operations(self, operations, parts_dict) -> List[ValidationIssue]:
        issues = []
        for op_name, operation in operations.items():
            if self._get_operation_attr(operation, 'type') != 'boolean':
                continue
            boolean_op = self._get_operation_attr(operation, 'operation')
            if boolean_op == 'difference':
                issues.extend(self._check_difference(op_name, operation, parts_dict))
            elif boolean_op == 'intersection':
                issues.extend(self._check_intersection(op_name, operation, parts_dict))
            elif boolean_op == 'union':
                issues.extend(self._check_union(op_name, operation, parts_dict))
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
                message=f"Boolean effect check skipped: {str(e)}"
            ))
        return issues
