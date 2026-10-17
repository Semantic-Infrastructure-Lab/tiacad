#!/usr/bin/env python3
"""
Rewrite box parts from width/depth/height to `size: [x, y, z]` (TCAD-DSL-6).

Old:                                   New:
  primitive: box                         primitive: box
  parameters: {width: 10,                size: [10, 20, 30]
               depth: 20, height: 30}

width -> X, depth -> Y, height -> Z, so the geometry is unchanged. Values (numbers,
'${...}' templates) are carried over as written. Comments inside the removed
block are dropped; every other line is left byte-for-byte as it was. Only parts with `primitive: box` are touched.

Usage:
  python3 scripts/migrations/box_size.py FILE [FILE ...]     # .yaml/.tiacad/.md (fenced yaml blocks)
  python3 scripts/migrations/box_size.py --check FILE ...    # report only, change nothing
Needs ruamel.yaml.
"""

import io
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

LEGACY = ("width", "depth", "height")


def _yaml():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _size_line(part, indent):
    """`size: [...]` text built from the part's legacy values, or None if it cannot be rewritten."""
    params = part.get("parameters")
    if not isinstance(params, CommentedMap) or set(params) != set(LEGACY) or "size" in part:
        return None
    seq = CommentedSeq([params["width"], params["depth"], params["height"]])
    seq.fa.set_flow_style()
    out = io.StringIO()
    y = _yaml()
    y.dump(CommentedMap([("size", seq)]), out)
    return " " * indent + out.getvalue().rstrip("\n")


def _block_end(lines, start, indent):
    """First line after `start` that is not part of the value: indent <= key indent (blank lines skipped)."""
    end = start + 1
    last = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip():
            if len(line) - len(line.lstrip(" ")) <= indent:
                break
            last = end + 1
        end += 1
    return last


def _boxes(node, found):
    if isinstance(node, CommentedMap):
        parts = node.get("parts")
        if isinstance(parts, CommentedMap):
            for part in parts.values():
                if isinstance(part, CommentedMap) and part.get("primitive") == "box":
                    found.append(part)
        for value in node.values():
            _boxes(value, found)
    elif isinstance(node, list):
        for value in node:
            _boxes(value, found)


def migrate_yaml_text(text):
    """Return (new_text, parts_changed). Only the `parameters:` block of each box is replaced."""
    y = _yaml()
    try:
        data = y.load(text)
    except Exception:
        return text, 0
    found = []
    _boxes(data, found)
    lines = text.split("\n")
    edits = []
    for part in found:
        if all(k in part for k in LEGACY) and "size" not in part:
            # legacy keys written directly on the part (no `parameters:` block): one line each
            seq = CommentedSeq([part["width"], part["depth"], part["height"]])
            seq.fa.set_flow_style()
            out = io.StringIO()
            y.dump(CommentedMap([("size", seq)]), out)
            rows = sorted(part.lc.key(k) for k in LEGACY)
            first_line, col = rows[0]
            edits.append((first_line, first_line + 1, " " * col + out.getvalue().rstrip("\n")))
            edits.extend((r, r + 1, None) for r, _ in rows[1:])
            continue
        line_no, col = part.lc.key("parameters") if "parameters" in part else (None, None)
        if line_no is None:
            continue
        size_line = _size_line(part, col)
        if size_line is None:
            continue
        edits.append((line_no, _block_end(lines, line_no, col), size_line))
    for start, end, new_line in sorted(edits, reverse=True, key=lambda e: e[0]):
        lines[start:end] = [] if new_line is None else [new_line]
    return "\n".join(lines), sum(1 for e in edits if e[2] is not None)


def migrate_markdown_text(text):
    total = [0]

    def repl(match):
        new, n = migrate_yaml_text(match.group(2))
        total[0] += n
        return f"{match.group(1)}{new}{match.group(3)}" if n else match.group(0)

    return re.sub(r"(```yaml\n)(.*?)(```)", repl, text, flags=re.S), total[0]


def main(argv):
    check = "--check" in argv
    files = [Path(a) for a in argv if not a.startswith("--")]
    changed = 0
    for path in files:
        text = path.read_text()
        fn = migrate_markdown_text if path.suffix == ".md" else migrate_yaml_text
        new, n = fn(text)
        if n:
            changed += n
            print(f"{path}: {n} box part(s)")
            if not check:
                path.write_text(new)
    print(f"{changed} box part(s) {'would change' if check else 'rewritten'}")


if __name__ == "__main__":
    main(sys.argv[1:])
