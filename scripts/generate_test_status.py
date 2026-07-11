#!/usr/bin/env python3
"""Generate TEST_STATUS.json from a pytest junit-xml + coverage.xml run.

Single source of truth for test/coverage counts, so docs stop hand-writing
numbers that drift (BACKLOG.md "one source of truth for test health";
VALIDATION_STRENGTHENING.md #5). Run from repo root after the non-visual
suite has produced test-results.xml and coverage.xml:

    pytest -m "not visual" --junit-xml=test-results.xml \
        --cov=tiacad_core --cov-report=xml
    python scripts/generate_test_status.py
"""

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    attrib = suite.attrib
    total = int(attrib.get("tests", 0))
    failed = int(attrib.get("failures", 0))
    errors = int(attrib.get("errors", 0))
    skipped = int(attrib.get("skipped", 0))
    passed = total - failed - errors - skipped
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
    }


def parse_coverage(path: Path) -> float | None:
    if not path.exists():
        return None
    root = ET.parse(path).getroot()
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        return None
    return round(float(line_rate) * 100, 1)


def count_visual_tests() -> int | None:
    result = subprocess.run(
        ["pytest", "-m", "visual", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # pytest 9.x: "67/1926 tests collected (1859 deselected) in 1.90s"
    # older pytest: "67 tests collected in 1.90s" / "67/1926 tests collected"
    for line in result.stdout.splitlines():
        match = re.search(r"(\d+)(?:/\d+)? tests? collected", line)
        if match:
            return int(match.group(1))
    return None


def git_commit_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit-xml", default="test-results.xml", type=Path)
    parser.add_argument("--coverage-xml", default="coverage.xml", type=Path)
    parser.add_argument("--python-version", default=f"{sys.version_info.major}.{sys.version_info.minor}")
    parser.add_argument("--skip-visual-collect", action="store_true", help="don't invoke pytest to count visual tests")
    parser.add_argument("-o", "--output", default=REPO_ROOT / "TEST_STATUS.json", type=Path)
    args = parser.parse_args()

    junit_path = args.junit_xml if args.junit_xml.is_absolute() else REPO_ROOT / args.junit_xml
    if not junit_path.exists():
        print(f"error: {junit_path} not found — run pytest with --junit-xml first", file=sys.stderr)
        return 1

    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": git_commit_sha(),
        "python_version": args.python_version,
        "non_visual": parse_junit(junit_path),
        "visual_collected": None if args.skip_visual_collect else count_visual_tests(),
        "coverage_percent": parse_coverage(
            args.coverage_xml if args.coverage_xml.is_absolute() else REPO_ROOT / args.coverage_xml
        ),
    }

    args.output.write_text(json.dumps(status, indent=2) + "\n")
    print(f"wrote {args.output}")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
