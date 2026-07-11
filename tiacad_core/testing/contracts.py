"""
Embedded `expect:` contract checking (VALIDATION_STRENGTHENING.md section 4.1).

Reads the optional `expect:` block from a parsed TiaCADDocument and checks it
against the actual built geometry: volume, bounding box, watertightness,
connected-component count, and named-part relations (flush faces, coaxial
axes). The model becomes the single source of truth for its own correctness;
one generic pytest test (test_embedded_contracts.py) discovers and runs every
model that declares an expect: block instead of requiring hand-written
per-example tests.
"""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..backend_support import require_cadquery_part
from ..part import Part, PartRegistry
from ..spatial_resolver import SpatialResolver, SpatialResolverError
from .dimensions import get_volume, DimensionError

DEFAULT_LENGTH_TOL = 0.1  # mm
DEFAULT_VOLUME_TOL = 1.0  # mm^3 floor; actual tolerance is max(this, 1% of expected)


class ContractError(Exception):
    """Raised when a document has no expect: block to check, or it can't be resolved."""


@dataclass
class ContractViolation:
    check: str
    message: str


@dataclass
class ContractResult:
    ok: bool
    part_name: str
    violations: List[ContractViolation] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            return f"contract OK for '{self.part_name}'"
        lines = [f"contract FAILED for '{self.part_name}' ({len(self.violations)} issue(s)):"]
        for v in self.violations:
            lines.append(f"  - [{v.check}] {v.message}")
        return "\n".join(lines)


def count_solids(part: Part) -> int:
    """Number of disjoint solid bodies, counted at the BREP/kernel level.

    This is the authoritative "how many separate bodies" measure. It counts
    CadQuery ``Solid`` entities across the whole geometry stack — unlike mesh
    islands (``trimesh.split``), which mis-count in both directions:

    - A single hollow body with a fully enclosed cavity meshes as two disjoint
      surface shells → 2 mesh islands, but is 1 solid (BREP is correct).
    - The historical fallback to ``is_watertight`` can't catch two truly
      disjoint bodies, because two separate closed solids are each watertight.

    Counting ``Solids()`` distinguishes "one hollow body" from "two disjoint
    bodies" that neither mesh-island counting nor watertightness can.
    """
    require_cadquery_part(part, "Contract check (solid count)")
    return sum(len(v.Solids()) for v in part.geometry.vals())


def get_manifold_stats(part: Part) -> Dict[str, Any]:
    """Watertightness (mesh) + disjoint-body count (BREP solids).

    ``components`` is the BREP solid count — the correct disjoint-body signal
    (see :func:`count_solids`). ``mesh_islands`` is retained for diagnostics:
    it is the old ``trimesh.split`` count, which over-counts hollow bodies and
    is *not* used for the ``expect: components:`` contract check.
    """
    import trimesh

    require_cadquery_part(part, "Contract check (watertight/components)")

    solids = count_solids(part)
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        part.geometry.val().exportStl(str(tmp_path))
        mesh = trimesh.load(str(tmp_path))
        mesh_islands = len(mesh.split(only_watertight=False))
        return {
            'watertight': bool(mesh.is_watertight),
            'components': solids,
            'mesh_islands': mesh_islands,
        }
    finally:
        tmp_path.unlink(missing_ok=True)


def resolve_contract_part(doc, expect: Dict[str, Any]) -> Tuple[Part, str]:
    """Resolve the part an expect: block refers to (its `final` key, or the doc's default)."""
    from ..parser.tiacad_parser import resolve_default_part_name

    part_name = expect.get('final')
    if part_name is None:
        part_name = resolve_default_part_name(doc.parts, doc.operations, doc.export_config)
    return doc.parts.get(part_name), part_name


def _check_relation(
    resolver: SpatialResolver, relation: Dict[str, Any], tol_length: float
) -> Optional[ContractViolation]:
    if 'flush' in relation:
        a_spec, b_spec = relation['flush']
        gap = relation.get('gap', 0.0)
        try:
            a = resolver.resolve(a_spec)
            b = resolver.resolve(b_spec)
        except SpatialResolverError as e:
            return ContractViolation('flush', f"could not resolve {a_spec!r}/{b_spec!r}: {e}")

        if a.orientation is None or b.orientation is None:
            return ContractViolation('flush', f"{a_spec!r}/{b_spec!r} are not faces (no orientation)")

        normal_a = a.orientation / np.linalg.norm(a.orientation)
        normal_b = b.orientation / np.linalg.norm(b.orientation)
        alignment = float(np.dot(normal_a, normal_b))
        if alignment > -0.999:
            return ContractViolation(
                'flush', f"{a_spec!r}/{b_spec!r} normals not opposed (dot={alignment:.4f})"
            )

        offset_a = float(np.dot(a.position, normal_a))
        offset_b = float(np.dot(b.position, normal_a))
        actual_gap = offset_b - offset_a
        if abs(actual_gap - gap) > tol_length:
            return ContractViolation(
                'flush',
                f"{a_spec!r}/{b_spec!r} gap={actual_gap:.4f} expected {gap} (tol {tol_length})",
            )
        return None

    if 'coaxial' in relation:
        a_spec, b_spec = relation['coaxial']
        try:
            a = resolver.resolve(a_spec)
            b = resolver.resolve(b_spec)
        except SpatialResolverError as e:
            return ContractViolation('coaxial', f"could not resolve {a_spec!r}/{b_spec!r}: {e}")

        if a.orientation is None or b.orientation is None:
            return ContractViolation('coaxial', f"{a_spec!r}/{b_spec!r} are not axes (no orientation)")

        dir_a = a.orientation / np.linalg.norm(a.orientation)
        dir_b = b.orientation / np.linalg.norm(b.orientation)
        parallel = abs(float(np.dot(dir_a, dir_b)))
        if parallel < 0.999:
            return ContractViolation(
                'coaxial', f"{a_spec!r}/{b_spec!r} directions not parallel (|dot|={parallel:.4f})"
            )

        offset = b.position - a.position
        perp = offset - np.dot(offset, dir_a) * dir_a
        distance = float(np.linalg.norm(perp))
        if distance > tol_length:
            return ContractViolation(
                'coaxial', f"{a_spec!r}/{b_spec!r} off-axis by {distance:.4f} (tol {tol_length})"
            )
        return None

    return ContractViolation('relation', f"unrecognized relation keys: {list(relation.keys())}")


def check_contract(doc) -> ContractResult:
    """
    Check a parsed TiaCADDocument's embedded expect: block against its built
    geometry.

    Raises:
        ContractError: If the document has no expect: block, or the named
            final part / relation references can't be resolved.
    """
    expect = getattr(doc, 'expect', {}) or {}
    if not expect:
        raise ContractError("document has no expect: block")

    part, part_name = resolve_contract_part(doc, expect)
    tol = expect.get('tol', {})
    tol_length = tol.get('length', DEFAULT_LENGTH_TOL)

    violations: List[ContractViolation] = []

    if 'volume' in expect:
        expected_volume = expect['volume']
        tol_volume = tol.get('volume', max(DEFAULT_VOLUME_TOL, abs(expected_volume) * 0.01))
        try:
            actual_volume = get_volume(part)
        except DimensionError as e:
            violations.append(ContractViolation('volume', str(e)))
        else:
            if abs(actual_volume - expected_volume) > tol_volume:
                violations.append(ContractViolation(
                    'volume',
                    f"actual={actual_volume:.4f} expected={expected_volume} (tol {tol_volume:.4f})",
                ))

    if 'bbox' in expect:
        bounds = part.get_bounds()
        actual_bbox = [
            bounds['max'][0] - bounds['min'][0],
            bounds['max'][1] - bounds['min'][1],
            bounds['max'][2] - bounds['min'][2],
        ]
        for axis, (actual, expected) in enumerate(zip(actual_bbox, expect['bbox'])):
            if abs(actual - expected) > tol_length:
                axis_name = ['width', 'height', 'depth'][axis]
                violations.append(ContractViolation(
                    'bbox',
                    f"{axis_name} actual={actual:.4f} expected={expected} (tol {tol_length})",
                ))

    if 'watertight' in expect or 'components' in expect:
        try:
            stats = get_manifold_stats(part)
        except Exception as e:
            violations.append(ContractViolation('manifold', f"could not compute manifold stats: {e}"))
        else:
            if 'watertight' in expect and stats['watertight'] != expect['watertight']:
                violations.append(ContractViolation(
                    'watertight', f"actual={stats['watertight']} expected={expect['watertight']}"
                ))
            if 'components' in expect and stats['components'] != expect['components']:
                violations.append(ContractViolation(
                    'components', f"actual={stats['components']} expected={expect['components']}"
                ))

    if expect.get('relations'):
        resolver = SpatialResolver(doc.parts, doc.references)
        for relation in expect['relations']:
            violation = _check_relation(resolver, relation, tol_length)
            if violation is not None:
                violations.append(violation)

    return ContractResult(ok=not violations, part_name=part_name, violations=violations)


def assert_contract(doc) -> None:
    """Check a document's expect: block, raising AssertionError with a readable summary on failure."""
    result = check_contract(doc)
    assert result.ok, result.summary()


def discover_models_with_expect(*roots: str) -> List[str]:
    """Find every .yaml/.tiacad file under the given roots that declares a top-level expect: block."""
    import yaml as _yaml

    found = []
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        for pattern in ('*.yaml', '*.yml', '*.tiacad'):
            for path in sorted(root_path.rglob(pattern)):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = _yaml.safe_load(f)
                except Exception:
                    continue
                if isinstance(data, dict) and data.get('expect'):
                    found.append(str(path))
    return found


def write_contract_yaml(doc, part_name: Optional[str] = None) -> str:
    """
    Seed an expect: YAML block from a document's current build, for a human to
    review before pasting into the model file (`tiacad audit --write-contract`).
    """
    if part_name is None:
        from ..parser.tiacad_parser import resolve_default_part_name
        part_name = resolve_default_part_name(doc.parts, doc.operations, doc.export_config)

    part = doc.parts.get(part_name)
    bounds = part.get_bounds()
    bbox = [
        round(bounds['max'][0] - bounds['min'][0], 3),
        round(bounds['max'][1] - bounds['min'][1], 3),
        round(bounds['max'][2] - bounds['min'][2], 3),
    ]
    volume = round(get_volume(part), 3)
    stats = get_manifold_stats(part)

    lines = [
        "expect:",
        f"  final: {part_name}",
        f"  volume: {volume}",
        f"  bbox: [{bbox[0]}, {bbox[1]}, {bbox[2]}]",
        f"  watertight: {str(stats['watertight']).lower()}",
        f"  components: {stats['components']}",
    ]
    return "\n".join(lines)
