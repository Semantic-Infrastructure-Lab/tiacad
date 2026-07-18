"""
Golden STEP topology baselines (VALIDATION_STRENGTHENING.md section 4.9).

Volume/bbox/mesh-hash contracts (see :mod:`.contracts`, :mod:`.determinism`)
can miss a *topology* regression — e.g. a fillet silently stops applying to
one edge, or a boolean leaves an extra sliver face — while volume and bbox
stay within tolerance. A committed STEP export is an exact-geometry baseline
for a small set of anchor models; this module compares the BREP topology of
a freshly built part against a committed golden STEP file.

Comparing STEP *files* byte-for-byte is not viable (timestamps, kernel
version metadata), so the check re-imports the golden STEP and compares
BREP entity counts (solids/faces/edges/vertices) — a coarse but real
topology signature that catches face/edge count drift a volume number
would not.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..backend_support import require_cadquery_part
from ..part import Part

_FIELDS = ("solids", "faces", "edges", "vertices")


@dataclass
class TopologySignature:
    solids: int
    faces: int
    edges: int
    vertices: int

    def as_dict(self) -> dict:
        return {f: getattr(self, f) for f in _FIELDS}

    def diff(self, other: "TopologySignature") -> List[str]:
        return [
            f"{f}: golden={getattr(other, f)} actual={getattr(self, f)}"
            for f in _FIELDS
            if getattr(self, f) != getattr(other, f)
        ]


class GoldenStepError(Exception):
    """Raised when a golden STEP file is missing or unreadable."""


def _signature_from_shapes(shapes) -> TopologySignature:
    return TopologySignature(
        solids=sum(len(v.Solids()) for v in shapes),
        faces=sum(len(v.Faces()) for v in shapes),
        edges=sum(len(v.Edges()) for v in shapes),
        vertices=sum(len(v.Vertices()) for v in shapes),
    )


def topology_signature(part: Part) -> TopologySignature:
    """BREP-level topology signature (solids/faces/edges/vertices) of a built part."""
    require_cadquery_part(part, "Golden STEP topology check")
    return _signature_from_shapes(part.geometry.vals())


def topology_signature_from_step(step_path: str) -> TopologySignature:
    """Re-import a committed golden STEP file and compute its topology signature."""
    import cadquery as cq

    path = Path(step_path)
    if not path.exists():
        raise GoldenStepError(f"Golden STEP file not found: {path}")
    imported = cq.importers.importStep(str(path))
    return _signature_from_shapes(imported.vals())


def check_against_golden_step(part: Part, step_path: str) -> List[str]:
    """Compare a freshly built part's topology against a committed golden STEP.

    Returns a list of human-readable mismatch descriptions (empty = match).
    """
    actual = topology_signature(part)
    golden = topology_signature_from_step(step_path)
    return actual.diff(golden)


def export_golden_step(part: Part, step_path: str) -> None:
    """Export a part's geometry to a STEP file (used by the golden-regeneration script)."""
    require_cadquery_part(part, "Golden STEP export")
    Path(step_path).parent.mkdir(parents=True, exist_ok=True)
    part.geometry.val().exportStep(str(step_path))
