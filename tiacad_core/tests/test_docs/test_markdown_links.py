"""
Markdown link integrity tests for active project documentation.

These tests target the current docs surface, not historical archive material.
"""

from pathlib import Path
import re


ROOT = Path(__file__).parents[3]
DOCS = ROOT / "docs"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _active_markdown_files():
    yield ROOT / "README.md"
    yield ROOT / "PROJECT.md"

    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("docs/archive/"):
            continue
        yield path


def _is_external(target: str) -> bool:
    return (
        target.startswith("http://")
        or target.startswith("https://")
        or target.startswith("mailto:")
        or target.startswith("#")
    )


def _normalize_target(target: str) -> str:
    normalized = target.strip()
    if normalized.startswith("<") and normalized.endswith(">"):
        normalized = normalized[1:-1]
    return normalized.split("#", 1)[0]


def test_internal_markdown_links_resolve():
    failures = []

    for doc_path in _active_markdown_files():
        text = doc_path.read_text(encoding="utf-8")
        for _, target in LINK_RE.findall(text):
            if _is_external(target):
                continue

            normalized = _normalize_target(target)
            if not normalized:
                continue

            resolved = (doc_path.parent / normalized).resolve()
            if not resolved.exists():
                failures.append(
                    f"{doc_path.relative_to(ROOT)} -> {target}"
                )

    assert not failures, "Broken markdown links:\n" + "\n".join(failures)
