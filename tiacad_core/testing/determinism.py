"""
Determinism gate (VALIDATION_STRENGTHENING.md section 4.4, Tier 2).

Proves the same YAML always produces the same geometry: build a model N
times and assert stable volume, bounding box, and mesh hash. OCCT
tessellation and boolean ops can be non-deterministic; that silently defeats
every golden-based test (visual and mesh) with flaky failures downstream,
far from the actual cause. This tier catches non-determinism directly, at
the model that produces it.
"""

import hashlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..backend_support import require_cadquery_part
from ..part import Part
from .contracts import resolve_contract_part
from .dimensions import get_volume

DEFAULT_BUILD_COUNT = 3


class DeterminismError(Exception):
    """Raised when a model can't be built or resolved for a determinism check."""


@dataclass
class BuildSnapshot:
    volume: float
    bbox: List[float]
    mesh_hash: str


@dataclass
class DeterminismViolation:
    check: str
    message: str


@dataclass
class DeterminismResult:
    ok: bool
    part_name: str
    snapshots: List[BuildSnapshot] = field(default_factory=list)
    violations: List[DeterminismViolation] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            return f"determinism OK for '{self.part_name}' ({len(self.snapshots)} builds)"
        lines = [f"determinism FAILED for '{self.part_name}' ({len(self.violations)} issue(s)):"]
        for v in self.violations:
            lines.append(f"  - [{v.check}] {v.message}")
        return "\n".join(lines)


def mesh_hash(part: Part) -> str:
    """SHA-256 of the part's exported STL bytes.

    Deliberately hashes the raw export, not a canonicalized form: the point
    of this check is to catch tessellation order/precision drift between
    builds of the *same* input, so canonicalizing away that drift would hide
    the exact thing being tested for.
    """
    require_cadquery_part(part, "Determinism check (mesh hash)")
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        part.geometry.val().exportStl(str(tmp_path))
        return hashlib.sha256(tmp_path.read_bytes()).hexdigest()
    finally:
        tmp_path.unlink(missing_ok=True)


def build_snapshot(path: str, part_name: Optional[str] = None) -> BuildSnapshot:
    """Parse and build `path` from scratch, returning volume/bbox/mesh_hash for its final part."""
    from ..parser.tiacad_parser import TiaCADParser

    doc = TiaCADParser.parse_file(path)
    expect = getattr(doc, 'expect', {}) or {}
    if part_name is None:
        part, resolved_name = resolve_contract_part(doc, expect)
    else:
        part, resolved_name = doc.parts.get(part_name), part_name

    if part is None:
        raise DeterminismError(f"{path}: could not resolve part {resolved_name!r}")

    bounds = part.get_bounds()
    bbox = [
        bounds['max'][0] - bounds['min'][0],
        bounds['max'][1] - bounds['min'][1],
        bounds['max'][2] - bounds['min'][2],
    ]
    return BuildSnapshot(
        volume=get_volume(part),
        bbox=bbox,
        mesh_hash=mesh_hash(part),
    )


def check_determinism(path: str, n: int = DEFAULT_BUILD_COUNT) -> DeterminismResult:
    """Build `path` from scratch `n` times and assert every build agrees exactly.

    A deterministic pipeline given identical input and no shared mutable
    state must reproduce bit-identical output — there is no "close enough"
    for this check; any drift, however small, is the failure being tested
    for.
    """
    if n < 2:
        raise ValueError("check_determinism needs at least 2 builds to compare")

    from ..parser.tiacad_parser import TiaCADParser

    doc = TiaCADParser.parse_file(path)
    expect = getattr(doc, 'expect', {}) or {}
    _, part_name = resolve_contract_part(doc, expect)

    snapshots: List[BuildSnapshot] = []
    try:
        for _ in range(n):
            snapshots.append(build_snapshot(path, part_name))
    except DeterminismError as e:
        return DeterminismResult(
            ok=False, part_name=part_name,
            violations=[DeterminismViolation('build', str(e))],
        )

    violations: List[DeterminismViolation] = []
    first = snapshots[0]
    for i, snap in enumerate(snapshots[1:], start=2):
        if snap.volume != first.volume:
            violations.append(DeterminismViolation(
                'volume', f"build 1 volume={first.volume!r} != build {i} volume={snap.volume!r}"
            ))
        if snap.bbox != first.bbox:
            violations.append(DeterminismViolation(
                'bbox', f"build 1 bbox={first.bbox!r} != build {i} bbox={snap.bbox!r}"
            ))
        if snap.mesh_hash != first.mesh_hash:
            violations.append(DeterminismViolation(
                'mesh_hash',
                f"build 1 hash={first.mesh_hash[:12]}... != build {i} hash={snap.mesh_hash[:12]}...",
            ))

    return DeterminismResult(ok=not violations, part_name=part_name, snapshots=snapshots, violations=violations)


def golden_snapshot_dict(snapshot: BuildSnapshot, part_name: str) -> dict:
    """Serialize a BuildSnapshot to the golden_hashes.json entry shape."""
    return {
        'part': part_name,
        'volume': snapshot.volume,
        'bbox': snapshot.bbox,
        'mesh_hash': snapshot.mesh_hash,
    }


def check_against_golden(snapshot: BuildSnapshot, part_name: str, golden: dict) -> List[DeterminismViolation]:
    """Compare a fresh build against a reviewed golden_hashes.json entry."""
    violations: List[DeterminismViolation] = []
    if golden.get('part') != part_name:
        violations.append(DeterminismViolation(
            'golden_part', f"actual={part_name!r} golden={golden.get('part')!r}"
        ))
    if golden.get('volume') != snapshot.volume:
        violations.append(DeterminismViolation(
            'golden_volume', f"actual={snapshot.volume!r} golden={golden.get('volume')!r}"
        ))
    if golden.get('bbox') != snapshot.bbox:
        violations.append(DeterminismViolation(
            'golden_bbox', f"actual={snapshot.bbox!r} golden={golden.get('bbox')!r}"
        ))
    if golden.get('mesh_hash') != snapshot.mesh_hash:
        violations.append(DeterminismViolation(
            'golden_mesh_hash',
            f"actual={snapshot.mesh_hash[:12]}... golden={str(golden.get('mesh_hash'))[:12]}...",
        ))
    return violations
