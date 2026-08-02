"""
Unused Parameters Rule for TiaCAD Assembly Validator

Detects `parameters:` entries never referenced by a `${...}` expression
anywhere in the document.
"""

import re
from typing import List
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity

# Matches `${ ... }` template interpolations, capturing the inner expression.
_INTERPOLATION_RE = re.compile(r'\$\{([^}]*)\}')


class UnusedParametersRule(ValidationRule):
    """
    Find parameters declared in `parameters:` but never referenced by any
    `${...}` expression in the document.

    A document can declare `parameters: {length: 58, max_diameter: 44}` and
    have a `sketches:` block whose `points:` are all hardcoded literals — the
    parser accepts this silently, so the file *looks* parametric (the
    parameter is right there, with a plausible name and value) but resizing
    it by editing the declared value has zero effect on the built geometry.
    This was found modeling `examples/egg.yaml` — see
    docs/developer/CASE_STUDY_MODELING_AN_EGG.md and
    KNOWN_LIMITATIONS.md #21 (TCAD-BUG-2).

    Implementation note: this scans `document.yaml_string` (the raw source)
    rather than any resolved/parsed structure, because by the time parameters
    are resolved into parts/sketches, there is no remaining trace of which
    `${...}` expressions were written — only their evaluated numeric results.
    A parameter referenced only from within another parameter's own
    definition (e.g. `blunt_length: "${length * blunt_fraction}"`) still
    counts as used — that's a legitimate dependency, not dead work.
    """

    @property
    def name(self) -> str:
        return "Unused Parameters Check"

    @property
    def category(self) -> str:
        return "parameters"

    def check(self, document) -> List[ValidationIssue]:
        issues = []

        parameters = getattr(document, 'parameters', None) or {}
        yaml_string = getattr(document, 'yaml_string', None)
        if not parameters or not yaml_string:
            return issues

        referenced_text = " ".join(m.group(1) for m in _INTERPOLATION_RE.finditer(yaml_string))

        for param_name in sorted(parameters.keys()):
            pattern = r'\b' + re.escape(param_name) + r'\b'
            if not re.search(pattern, referenced_text):
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category=self.category,
                    message=f"Parameter '{param_name}' is declared but never used in a ${{...}} expression",
                    suggestion="Reference it from a part/sketch/operation with ${...}, or remove it if it's dead",
                ))

        return issues
