"""
The self-contained examples in docs/user/YAML_REFERENCE.md must actually build.

TCAD-DOC-1: the reference showed `size: [x,y,z]` on boxes, which the parser
rejects. Only blocks under the headings below are checked; other snippets in
the reference are deliberate fragments (they reference parts defined elsewhere).
"""

from pathlib import Path
import re

import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser

REFERENCE = Path(__file__).parents[3] / "docs" / "user" / "YAML_REFERENCE.md"
CHECKED_HEADING = re.compile(
    r"^#{2,3} (?:(?:Box|Cylinder|Sphere|Cone|Polygon) Primitive|Example \d+:.*|Contracts \(expect:\))$"
)
YAML_BLOCK = re.compile(r"```yaml\n(.*?)```", re.S)


def _checked_blocks():
    heading = None
    section = []
    sections = []
    for line in REFERENCE.read_text().splitlines():
        if line.startswith("#"):
            if heading and section:
                sections.append((heading, "\n".join(section)))
            heading = line.lstrip("# ").strip() if CHECKED_HEADING.match(line) else None
            section = []
        elif heading is not None:
            section.append(line)
    if heading and section:
        sections.append((heading, "\n".join(section)))
    return [
        (name, block) for name, text in sections for block in YAML_BLOCK.findall(text)
    ]


BLOCKS = _checked_blocks()


def test_reference_has_checked_examples():
    # Guards the extractor: a heading rename must not silently empty this suite.
    assert len(BLOCKS) >= 9, [name for name, _ in BLOCKS]


@pytest.mark.parametrize("name,block", BLOCKS, ids=[n for n, _ in BLOCKS])
def test_reference_example_builds(name, block):
    doc = TiaCADParser.parse_string(block)
    assert doc.parts.list_parts()
