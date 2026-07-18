"""
Standalone ``${...}`` parameter resolution for ``parts:``/``operations:`` blocks.

Used by :mod:`differential` to get plain-number specs from a raw YAML model
without going through the production parser/builder pipeline -- the whole
point of a differential check is to reconstruct geometry via an independent
path, so it must not depend on ``tiacad_core.parser.parts_builder`` or
``tiacad_core.parser.boolean_builder``. Reusing :class:`ParameterResolver`
for the ``${...}`` arithmetic itself is fine: that's expression evaluation,
not geometry construction, and duplicating it would only add risk without
adding independence.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from ..parser.parameter_resolver import ParameterResolver


def resolve_parts_and_operations(
    yaml_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Resolve ``${...}`` expressions in a model's ``parts:`` and ``operations:``."""
    resolver = ParameterResolver(yaml_data.get("parameters", {}) or {})
    parts_spec = {
        name: resolver.resolve(spec)
        for name, spec in (yaml_data.get("parts") or {}).items()
    }
    operations_spec = {
        name: resolver.resolve(spec)
        for name, spec in (yaml_data.get("operations") or {}).items()
    }
    return parts_spec, operations_spec
