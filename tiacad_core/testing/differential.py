"""
Differential (kernel-vs-kernel) geometry testing.

TiaCAD's production geometry runs entirely on CadQuery/OCCT. Every other
oracle in the validation ladder (analytic formulas, embedded ``expect:``
contracts, golden STEP topology signatures, visual review) still measures
*that same kernel's* output — none of them can catch a bug in OCCT's own
volume/boolean computation, only bugs in how TiaCAD drives it.

This module builds a second, independent interpretation of a trust model's
declarative ``parts:``/``operations:`` graph using `manifold3d
<https://github.com/elalish/manifold>`_ — a mesh-based CSG kernel with no
code in common with OCCT (it's the same engine modern OpenSCAD uses as its
default backend). Comparing its volume/bbox against CadQuery's for the same
model is a genuine cross-kernel check, not just a plumbing exercise.

Coverage is deliberately narrow: only primitives (box/cylinder/sphere/cone),
boolean ops (union/difference/intersection), and plain-vector `translate`
transforms have an independent manifold3d implementation below. Anything
else in a model's dependency graph (patterns, sketches, loft/sweep/revolve,
fillet/chamfer, spatial-reference transforms) makes it ineligible —
:func:`differential_check` reports that explicitly rather than silently
skipping or approximating.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..utils.exceptions import TiaCADError
from .parameter_resolver_compat import resolve_parts_and_operations

# manifold3d's polygon approximation of curved primitives is inscribed, not
# exact, so a cylinder/sphere/cone built from the same parameters as OCCT's
# analytic kernel will always read a hair low. This many segments keeps that
# bias under ~0.05% -- comfortably inside the tolerances below.
_CIRCULAR_SEGMENTS = 256

SUPPORTED_PRIMITIVES = frozenset({"box", "cylinder", "sphere", "cone"})
SUPPORTED_BOOLEAN_OPS = frozenset({"union", "difference", "intersection"})

# Relative volume tolerance and absolute per-axis bbox tolerance (mm) for
# cross-kernel agreement. Both are dominated by the circular-segment
# discretization bias above, not by genuine kernel disagreement.
DEFAULT_VOLUME_TOL = 0.01
DEFAULT_BBOX_TOL = 0.2


class DifferentialError(TiaCADError):
    """Raised when a differential check cannot be built or fails to agree."""


@dataclass
class DifferentialResult:
    """Outcome of cross-checking one model's final part against manifold3d."""
    path: str
    final_part: str
    eligible: bool
    reason: Optional[str] = None
    volume_cadquery: Optional[float] = None
    volume_manifold: Optional[float] = None
    bbox_cadquery: Optional[List[float]] = None
    bbox_manifold: Optional[List[float]] = None

    @property
    def volume_diff_relative(self) -> Optional[float]:
        if self.volume_cadquery is None or self.volume_manifold is None:
            return None
        if self.volume_cadquery == 0:
            return abs(self.volume_manifold)
        return abs(self.volume_manifold - self.volume_cadquery) / abs(self.volume_cadquery)

    @property
    def bbox_diff_max(self) -> Optional[float]:
        if self.bbox_cadquery is None or self.bbox_manifold is None:
            return None
        return max(
            abs(a - b) for a, b in zip(self.bbox_cadquery, self.bbox_manifold)
        )


def _final_part_name(yaml_data: Dict[str, Any]) -> Optional[str]:
    expect = yaml_data.get("expect") or {}
    if "final" in expect:
        return expect["final"]
    export = yaml_data.get("export") or {}
    return export.get("default_part")


def discover_eligible_trust_models(trust_dir: str) -> List[Tuple[str, bool, Optional[str]]]:
    """Scan ``examples/trust/*.yaml`` and classify each for differential eligibility.

    Returns a list of ``(path, eligible, reason)`` -- ``reason`` is set only
    when ``eligible`` is False, explaining what in the graph is unsupported.
    """
    results = []
    for path in sorted(Path(trust_dir).glob("*.yaml")):
        yaml_data = yaml.safe_load(path.read_text())
        final = _final_part_name(yaml_data)
        parts_spec = yaml_data.get("parts", {})
        operations_spec = yaml_data.get("operations", {})
        if not final:
            results.append((str(path), False, "no export.default_part or expect.final"))
            continue
        eligible, reason = _is_eligible(final, parts_spec, operations_spec)
        results.append((str(path), eligible, reason))
    return results


def _is_eligible(
    name: str,
    parts_spec: Dict[str, Any],
    operations_spec: Dict[str, Any],
    _seen: Optional[set] = None,
) -> Tuple[bool, Optional[str]]:
    _seen = _seen or set()
    if name in _seen:
        return False, f"cyclic reference at '{name}'"
    _seen = _seen | {name}

    if name in parts_spec:
        spec = parts_spec[name]
        primitive = spec.get("primitive")
        if primitive not in SUPPORTED_PRIMITIVES:
            return False, f"part '{name}' uses unsupported primitive '{primitive}'"
        return True, None

    if name not in operations_spec:
        return False, f"'{name}' is neither a known part nor a known operation"

    spec = operations_spec[name]
    op_type = spec.get("type")

    if op_type == "boolean":
        operation = spec.get("operation")
        if operation not in SUPPORTED_BOOLEAN_OPS:
            return False, f"operation '{name}' uses unsupported boolean op '{operation}'"
        if operation == "difference":
            deps = [spec.get("base")] + list(spec.get("subtract", []))
        else:
            deps = list(spec.get("inputs", []))
        if any(not isinstance(d, str) or "*" in d for d in deps):
            return False, f"operation '{name}' uses pattern/wildcard part references"
        for dep in deps:
            eligible, reason = _is_eligible(dep, parts_spec, operations_spec, _seen)
            if not eligible:
                return False, reason
        return True, None

    if op_type == "transform":
        transforms = spec.get("transforms", [])
        for t in transforms:
            if set(t.keys()) - {"translate"}:
                return False, f"operation '{name}' uses unsupported transform '{list(t.keys())}'"
            vec = t.get("translate")
            if not (isinstance(vec, list) and len(vec) == 3 and all(isinstance(v, (int, float)) for v in vec)):
                return False, f"operation '{name}' translate is not a plain [dx, dy, dz] vector"
        input_name = spec.get("input")
        if not isinstance(input_name, str):
            return False, f"operation '{name}' has no single 'input' part"
        return _is_eligible(input_name, parts_spec, operations_spec, _seen)

    return False, f"operation '{name}' has unsupported type '{op_type}'"


def _build_manifold(
    name: str,
    parts_spec: Dict[str, Any],
    operations_spec: Dict[str, Any],
    cache: Dict[str, Any],
):
    import manifold3d as m

    if name in cache:
        return cache[name]

    if name in parts_spec:
        spec = parts_spec[name]
        params = spec.get("parameters", spec)
        origin = spec.get("origin", "center")
        primitive = spec["primitive"]

        if primitive == "box":
            width, height, depth = params["width"], params["height"], params["depth"]
            shape = m.Manifold.cube((width, depth, height), center=True)
            if origin == "corner":
                shape = shape.translate((width / 2, depth / 2, height / 2))
        elif primitive == "cylinder":
            radius, height = params["radius"], params["height"]
            shape = m.Manifold.cylinder(height, radius, radius, center=True)
            if origin == "base":
                shape = shape.translate((0, 0, height / 2))
        elif primitive == "sphere":
            shape = m.Manifold.sphere(params["radius"])
        elif primitive == "cone":
            radius1, radius2, height = params["radius1"], params["radius2"], params["height"]
            shape = m.Manifold.cylinder(height, radius1, radius2, center=True)
            if origin == "base":
                shape = shape.translate((0, 0, height / 2))
        else:
            raise DifferentialError(f"unsupported primitive '{primitive}' for '{name}'")

        cache[name] = shape
        return shape

    spec = operations_spec[name]
    op_type = spec["type"]

    if op_type == "boolean":
        operation = spec["operation"]
        if operation == "difference":
            result = _build_manifold(spec["base"], parts_spec, operations_spec, cache)
            for sub_name in spec["subtract"]:
                result = result - _build_manifold(sub_name, parts_spec, operations_spec, cache)
        else:
            inputs = spec["inputs"]
            result = _build_manifold(inputs[0], parts_spec, operations_spec, cache)
            for other_name in inputs[1:]:
                other = _build_manifold(other_name, parts_spec, operations_spec, cache)
                result = (result + other) if operation == "union" else (result ^ other)
    elif op_type == "transform":
        result = _build_manifold(spec["input"], parts_spec, operations_spec, cache)
        for t in spec["transforms"]:
            result = result.translate(tuple(t["translate"]))
    else:
        raise DifferentialError(f"unsupported operation type '{op_type}' for '{name}'")

    cache[name] = result
    return result


def differential_check(yaml_path: str) -> DifferentialResult:
    """Cross-check a trust model's final part between CadQuery and manifold3d.

    Loads and resolves the model's own ``parts:``/``operations:`` graph
    independently of the production parser, builds the final part with
    manifold3d, and compares its volume/bbox against the CadQuery-built
    part measured the normal way (:func:`tiacad_core.testing.get_volume`,
    ``Part.get_bounds()``). Returns a :class:`DifferentialResult` with
    ``eligible=False`` (and a reason) when the model uses constructs this
    module doesn't have an independent implementation for.
    """
    import manifold3d as m

    from ..parser.tiacad_parser import TiaCADParser
    from .dimensions import get_volume

    yaml_data = yaml.safe_load(Path(yaml_path).read_text())
    final = _final_part_name(yaml_data)
    if not final:
        return DifferentialResult(path=yaml_path, final_part="", eligible=False,
                                   reason="no export.default_part or expect.final")

    resolved_parts, resolved_operations = resolve_parts_and_operations(yaml_data)

    eligible, reason = _is_eligible(final, resolved_parts, resolved_operations)
    if not eligible:
        return DifferentialResult(path=yaml_path, final_part=final, eligible=False, reason=reason)

    m.set_circular_segments(_CIRCULAR_SEGMENTS)
    manifold_shape = _build_manifold(final, resolved_parts, resolved_operations, {})
    volume_manifold = manifold_shape.volume()
    xmin, ymin, zmin, xmax, ymax, zmax = manifold_shape.bounding_box()
    bbox_manifold = [xmax - xmin, ymax - ymin, zmax - zmin]

    doc = TiaCADParser.parse_file(yaml_path)
    part = doc.parts.get(final)
    volume_cadquery = get_volume(part)
    bounds = part.get_bounds()
    bbox_cadquery = [bounds["max"][i] - bounds["min"][i] for i in range(3)]

    return DifferentialResult(
        path=yaml_path,
        final_part=final,
        eligible=True,
        volume_cadquery=volume_cadquery,
        volume_manifold=volume_manifold,
        bbox_cadquery=bbox_cadquery,
        bbox_manifold=bbox_manifold,
    )
