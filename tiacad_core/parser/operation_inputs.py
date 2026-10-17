"""Which parts do a document's operations consume as inputs?

Shared by the trust renderer (hide consumed intermediates) and the component
importer (flag a component's internal parts so a model that imports it does not
draw them as solids).
"""

import re
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


def expand_input_item(item: Any, part_names: List[str]) -> List[str]:
    """Part names an operation input entry stands for.

    A plain string is itself. ``{"pattern": X}`` is every part named ``X_*`` and
    ``{"range": "X[a..b]"}`` / ``"X[*]"`` the matching pattern instances, in numeric
    order. Lenient on purpose (unknown shapes expand to nothing): the boolean builder
    is the one that validates and raises; this is for read-only consumers such as the
    renderer that only need the names.
    """
    if not isinstance(item, dict):
        return [item]
    if "pattern" in item:
        spec = f"{item['pattern']}[*]"
    elif "range" in item:
        spec = str(item["range"])
    else:
        return []
    m = re.match(r"^(.+?)\[(.+?)\]$", spec)
    if not m:
        return []
    base, rng = m.groups()
    prefix = f"{base}_"
    matches = [p for p in part_names if p.startswith(prefix)]

    def suffix_key(name: str):
        suffix = name[len(prefix):]
        return (0, int(suffix), "") if suffix.isdigit() else (1, 0, suffix)

    if rng != "*":
        r = re.match(r"^(\d+)\.\.(\d+)$", rng)
        if not r:
            return []
        wanted = {f"{prefix}{i}" for i in range(int(r.group(1)), int(r.group(2)) + 1)}
        matches = [p for p in matches if p in wanted]
    return sorted(matches, key=suffix_key)
