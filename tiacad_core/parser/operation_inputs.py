"""Which parts do a document's operations consume as inputs?

Shared by the trust renderer (hide consumed intermediates) and the component
importer (flag a component's internal parts so a model that imports it does not
draw them as solids).
"""

from typing import Any, Dict, List, Optional, Set


def consumed_part_names(operations: Optional[Dict[str, Any]], part_names: List[str]) -> Set[str]:
    """Names of parts that some operation uses as base/tool/input/subtract/inputs/tools.

    ``{"pattern": X}`` entries consume every part named ``X_*``; ``{"range": ...}``
    entries reference already-consumed pattern instances, so add nothing new.
    """
    consumed: Set[str] = set()
    for op in (operations or {}).values():
        for field in ("base", "tool", "input"):
            if field in op:
                consumed.add(op[field])
        for field in ("subtract", "inputs", "tools"):
            for name in op.get(field, []):
                if isinstance(name, dict):
                    if "pattern" in name:
                        prefix = f"{name['pattern']}_"
                        consumed.update(p for p in part_names if p.startswith(prefix))
                else:
                    consumed.add(name)
    return consumed
