#!/usr/bin/env python3
"""
Trust Gallery Sign-off Ledger

Formalizes scripts/trust_render.py --gallery into a committed, dated
artifact (VALIDATION_STRENGTHENING.md section 4.7): a table pairing each
trust scenario's *numeric* contract status (its embedded expect: block, if
any) with its *visual* sign-off (a human or AI reviewer who actually looked
at the render and approved it, or flagged an issue).

Neither half alone is enough — a passing expect: contract only proves the
volume/bbox/topology are right, not that the model looks like what it's
supposed to (orientation, which color is which, whether "centered" reads as
centered); a visual glance alone can't catch a wrong dimension. Together
they're the auditable correctness-of-record the trust gallery was always
meant to be, not just an ad-hoc debugging aid.

Usage:
    # Refresh contract/render status for every scenario, preserving any
    # existing reviewer sign-off notes (matched by scenario name).
    python scripts/trust_signoff.py

    # Then render the gallery for visual review:
    python scripts/trust_render.py --gallery
    # ... look at trust_output/gallery.html or the individual PNGs ...
    # ... hand-edit examples/trust/SIGNOFF.md's Reviewed/Reviewer/Note columns ...

This script never overwrites a scenario's Reviewed/Reviewer/Note columns —
only a human (or an AI reviewer acting deliberately, the same way this
session did) should do that, by editing SIGNOFF.md directly. Re-running
this script after adding a new trust scenario will not silently mark it
reviewed; it appears as "PENDING" until someone actually looks at it.

Author: TIA
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.contracts import ContractError, check_contract

PROJECT_ROOT = Path(__file__).parent.parent
TRUST_DIR = PROJECT_ROOT / "examples" / "trust"
SIGNOFF_PATH = TRUST_DIR / "SIGNOFF.md"

TABLE_HEADER = "| Scenario | Contract | Reviewed | Reviewer | Note |"
TABLE_SEP = "|---|---|---|---|---|"
ROW_RE = re.compile(r"^\|\s*`?([\w.]+)`?\s*\|.*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*$")


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _contract_status(yaml_path: Path) -> str:
    try:
        doc = TiaCADParser.parse_file(str(yaml_path))
    except Exception as e:
        return f"parse error: {e}"
    expect = getattr(doc, "expect", {}) or {}
    if not expect:
        return "no expect: block"
    try:
        result = check_contract(doc)
    except ContractError as e:
        return f"contract error: {e}"
    return "PASS" if result.ok else f"FAIL: {result.summary()}"


def _parse_existing_reviews() -> dict:
    """Preserve Reviewed/Reviewer/Note columns from a prior SIGNOFF.md, keyed by scenario."""
    reviews = {}
    if not SIGNOFF_PATH.exists():
        return reviews
    for line in SIGNOFF_PATH.read_text().splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        name, reviewed, reviewer, note = m.groups()
        reviews[name.strip()] = (reviewed.strip(), reviewer.strip(), note.strip())
    return reviews


def main() -> int:
    existing = _parse_existing_reviews()
    sha = _git_sha()

    scenarios = sorted(TRUST_DIR.glob("*.yaml"))
    if not scenarios:
        print(f"No trust scenarios found in {TRUST_DIR}")
        return 1

    rows = []
    for yf in scenarios:
        name = yf.stem
        contract = _contract_status(yf)
        reviewed, reviewer, note = existing.get(name, ("PENDING", "", ""))
        rows.append((name, contract, reviewed, reviewer, note))

    lines = [
        "# TiaCAD Trust Gallery Sign-off",
        "",
        f"Auto-refreshed (contract/render columns) at commit `{sha}` by "
        "`scripts/trust_signoff.py`. The Reviewed/Reviewer/Note columns are "
        "hand-maintained — re-running the script never overwrites them; a new "
        "scenario appears as PENDING until someone actually looks at its render.",
        "",
        "Render the gallery for review with:",
        "```",
        "python scripts/trust_render.py --gallery",
        "```",
        "then open `trust_output/gallery.html` (or the individual PNGs under `trust_output/`).",
        "",
        TABLE_HEADER,
        TABLE_SEP,
    ]
    for name, contract, reviewed, reviewer, note in rows:
        lines.append(f"| `{name}` | {contract} | {reviewed} | {reviewer} | {note} |")
    lines.append("")

    SIGNOFF_PATH.write_text("\n".join(lines))
    pending = sum(1 for r in rows if r[2] == "PENDING")
    print(f"Wrote {len(rows)} scenario(s) to {SIGNOFF_PATH.relative_to(PROJECT_ROOT)} ({pending} pending review)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
