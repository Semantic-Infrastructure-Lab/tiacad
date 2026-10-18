#!/usr/bin/env python3
"""
Rename `height` to `length` on cylinder, cone and polygon parts (TCAD-5).

Old:                                   New:
  primitive: cylinder                    primitive: cylinder
  parameters: {radius: 5, height: 12}    parameters: {radius: 5, length: 12}

`height` meant "extent along Z", which misleads once a primitive lies along another
axis (`axis: X|Y|Z`). The meaning is unchanged, only the key is renamed, and nothing
else on the line moves. Only parts with `primitive: cylinder|cone|polygon` are touched
(box has no height since TCAD-DSL-6; text keeps its `height`).

Handles YAML files, fenced yaml blocks in .md, and YAML held in Python triple-quoted
strings or dict literals (tests). Anything it cannot parse is left alone; the
deprecation warning on `height` finds what remains.

Usage:
  python3 scripts/migrations/primitive_length.py FILE [FILE ...]
  python3 scripts/migrations/primitive_length.py --check FILE ...    # report only
Needs ruamel.yaml.
"""

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

PRIMITIVES = ("cylinder", "cone", "polygon")


def _yaml():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    return y


def _targets(node, found):
    """Mappings that carry a legacy `height` key for a cylinder/cone/polygon part."""
    if isinstance(node, CommentedMap):
        parts = node.get("parts")
        if isinstance(parts, CommentedMap):
            for part in parts.values():
                if isinstance(part, CommentedMap) and part.get("primitive") in PRIMITIVES:
                    holder = part.get("parameters") if isinstance(part.get("parameters"), CommentedMap) else part
                    if "height" in holder and "length" not in holder:
                        found.append(holder)
        for value in node.values():
            _targets(value, found)
    elif isinstance(node, list):
        for value in node:
            _targets(value, found)


def migrate_yaml_text(text):
    """Return (new_text, parts_changed)."""
    try:
        data = _yaml().load(text)
    except Exception:
        return text, 0
    found = []
    _targets(data, found)
    lines = text.split("\n")
    changed = 0
    for holder in found:
        line_no, col = holder.lc.key("height")
        line = lines[line_no]
        if line[col:col + 6] != "height":
            continue
        lines[line_no] = line[:col] + "length" + line[col + 6:]
        changed += 1
    return "\n".join(lines), changed


def migrate_markdown_text(text):
    total = [0]

    def repl(match):
        new, n = migrate_yaml_text(match.group(2))
        total[0] += n
        return f"{match.group(1)}{new}{match.group(3)}" if n else match.group(0)

    return re.sub(r"(```yaml\n)(.*?)(```)", repl, text, flags=re.S), total[0]


def _dict_edits(source):
    """(line, col) of each 'height' key in a dict literal that names a cylinder/cone/polygon."""
    edits = []
    tree = ast.parse(source)

    def const(node):
        return node.value if isinstance(node, ast.Constant) else None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = {const(k): v for k, v in zip(node.keys, node.values) if const(k) is not None}
        if const(keys.get("primitive")) not in PRIMITIVES:
            continue
        holder = node
        params = keys.get("parameters")
        if isinstance(params, ast.Dict):
            holder = params
        for k in holder.keys:
            if const(k) == "height" and "length" not in [const(x) for x in holder.keys]:
                edits.append((k.lineno - 1, k.col_offset, k.end_col_offset))
    return edits


def migrate_python_text(text):
    """Rewrite YAML in triple-quoted strings and dict-literal specs."""
    total = 0
    lines = text.split("\n")
    # dict literals: the key token is `'height'` or `"height"` (8 columns wide)
    try:
        for line_no, start, end in sorted(_dict_edits(text), reverse=True):
            seg = lines[line_no][start:end]
            if seg in ("'height'", '"height"'):
                lines[line_no] = lines[line_no][:start] + seg[0] + "length" + seg[-1] + lines[line_no][end:]
                total += 1
    except SyntaxError:
        return text, 0
    text = "\n".join(lines)

    # triple-quoted YAML strings (no escapes, no f-string braces to worry about)
    out = []
    pos = 0
    line_starts = [0]
    for m in re.finditer(r"\n", text):
        line_starts.append(m.end())
    toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    for tok in toks:
        if tok.type != tokenize.STRING or not (tok.string.startswith(('"""', "'''"))):
            continue
        body = tok.string[3:-3]
        if "primitive:" not in body or "\\" in body:
            continue
        new, n = migrate_yaml_text(body)
        if not n:
            continue
        start = line_starts[tok.start[0] - 1] + tok.start[1]
        end = line_starts[tok.end[0] - 1] + tok.end[1]
        out.append((start, end, tok.string[:3] + new + tok.string[-3:]))
        total += n
    for start, end, repl in sorted(out, reverse=True):
        text = text[:start] + repl + text[end:]
    return text, total


def main(argv):
    check = "--check" in argv
    files = [Path(a) for a in argv if not a.startswith("--")]
    changed = 0
    for path in files:
        text = path.read_text()
        if path.suffix == ".md":
            fn = migrate_markdown_text
        elif path.suffix == ".py":
            fn = migrate_python_text
        else:
            fn = migrate_yaml_text
        new, n = fn(text)
        if n:
            changed += n
            print(f"{path}: {n} part(s)")
            if not check:
                path.write_text(new)
    print(f"{changed} part(s) {'would change' if check else 'rewritten'}")


if __name__ == "__main__":
    main(sys.argv[1:])
