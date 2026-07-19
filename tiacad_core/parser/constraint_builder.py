"""
ConstraintBuilder - Declarative assembly constraints (TCAD-CON-1 MVP)

Wraps CadQuery's own `Assembly.constrain()`/`.solve()` (casadi+IPOPT) rather
than implementing a constraint solver from scratch — see ROADMAP.md "Next
Milestone: Constraint Solver" and `tt show TCAD-CON-1` for the scoping
investigation that found this already-working, already-a-dependency solver.

MVP scope: 'flush' (coincident faces, opposed normals) and 'offset' (flush,
plus an additional translate along the reference face's normal) are
implemented via CadQuery's 'Plane' constraint kind — the exact pairing
verified working end-to-end during TCAD-CON-1's scoping (a 5mm cube flush-
mated onto a 10mm cube). 'coaxial' (two edges made concentric — e.g. a pin
mated into a hole) is implemented via CadQuery's 'Axis' + 'Point' constraint
kinds together, run against the same edge pair: 'Axis' aligns the edges'
directions (Face.normalAt() for planar edges, Edge.normal() for circular
edges, Edge.tangentAt() for other curves — see cadquery's solver.py
`_getAxis`), 'Point' pins their centers coincident. `Assembly._query`'s
grammar (`getattr(workplane, query.selector_kind)(query.selector)`) already
supports "part@edges@<selector>" out of the box — the TCAD-CON-1-era
docstring here assumed it didn't and deferred coaxial; TCAD-CON-3's
validation (see `tt show TCAD-CON-3`) found it does. Verified live: a 3mm
pin cylinder mated coaxial to a 6mm hole in a plate lands with its center
exactly on the hole's axis (X=0, Y=0), confirmed via the solved
`Assembly.toCompound()` geometry (not just the raw `Location`, which a
naive re-application can silently corrupt — see the task notes for the
verification pitfall this ran into).

'tangent' (TCAD-1) mates a cylindrical part flush against a reference plane
without their surfaces intersecting — e.g. a roller resting on a rail —
by measuring the moving part's cylinder radius (`Edge.radius()` on a
selected circular edge) and translating it along the reference face's
normal until its axis sits exactly one radius away from the plane, so the
curved surface touches the plane instead of piercing or floating clear of
it. Unlike flush/offset/coaxial, this is deliberately NOT built on
CadQuery's `Assembly.constrain()`/`.solve()`: the only constraint kind that
fits (`PointInPlane`, pinning the edge's center into the plane) leaves 5 of
6 rigid-body freedoms open, so IPOPT is free to satisfy it by rotating the
part into some arbitrary orientation rather than just sliding it along the
normal — verified empirically (a cylinder lying along X came out of
`.solve()` tilted onto a diagonal axis, not translated straight up).
`_apply_tangent_translate` computes the same result directly: resolve the
reference face and moving edge via `SpatialResolver` (giving exact
position+normal for the face and the edge's center point), take the
signed distance from that point to the plane, and translate by
`radius - current_distance` — exact, and with zero risk of an
unintended rotation. Scope is deliberately narrow: cylinder-face vs. plane
only (not cylinder-cylinder, not auto-alignment), because it's the only
case documented anywhere (ROADMAP.md / KNOWN_LIMITATIONS.md's
`roller.face_side`/`rail.face_top` example). Like 'offset', 'tangent' does
NOT rotate anything: the caller is responsible for the moving part's
cylinder axis already being parallel to the reference plane (e.g. via a
prior `rotate` transform) before the constraint runs.

Design notes:
- Convention: `faces: [reference, moving]` / `edges: [reference, moving]`
  — the reference's part is the one `Assembly.solve()` auto-locks (it locks
  the first entity referenced across all constraints); the moving
  reference's part is the one repositioned to satisfy the constraint.
- 'coaxial' requires inline `{type: edge, part, selector}` refs only — there
  is no auto-generated edge-name vocabulary (like `face_top`/`FACE_SELECTOR_MAP`
  for faces) to resolve a dotted `part.edge_name` shorthand against, so the
  caller must supply a real CadQuery edge selector (e.g. `%CIRCLE and >Z`).
- The solved `cq.Location` per part is decomposed into a single rotation
  (axis+angle, from the transform's quaternion) plus a translation, and
  baked in through the same `TransformTracker` machinery every other
  transform uses — so `Part.current_position`/`current_orientation` stay
  consistent with the rest of the pipeline, and a constrained part's own
  auto-generated references (axis_x, face_top, ...) resolve correctly
  afterward (this is exactly what TCAD-CON-2 fixed).
- 'offset' schema deliberately requires `faces:` (like flush), not the
  `parts:` shorthand in ROADMAP.md's illustrative pseudocode — that
  shorthand leaves which two faces get the gap underspecified, which
  CadQuery's face-selector-based solve needs to be explicit about.
- 'tangent' uses named `face:`/`edge:` fields, not a `[reference, moving]`
  list like the other three — its two sides are different *kinds* of
  reference (a plane vs. a circular edge), so there's no symmetric pair to
  order positionally; naming the roles is clearer than a list where item 0
  and item 1 mean different things depending on which key holds the list.
  `face:` is always the reference (locked) side, `edge:` the moving side.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import cadquery as cq
from OCP.gp import gp_Vec

from ..part import Part, PartRegistry
from ..transform_tracker import TransformTracker
from ..spatial_resolver import SpatialResolver, FACE_SELECTOR_MAP
from ..utils.exceptions import TiaCADError

IMPLEMENTED_CONSTRAINT_TYPES = {'flush', 'offset', 'coaxial', 'tangent'}
# Named and reserved so requesting one of these errors as "planned" rather than
# "unknown type" (TCAD-CON-9) — none are implemented; see ROADMAP.md
# 'Constraint Solver' for the shipped flush/offset/coaxial/tangent family.
RESERVED_CONSTRAINT_TYPES = {'parallel', 'perpendicular', 'angle', 'symmetric'}

# type -> (reference field name in the YAML spec, CadQuery query selector_kind,
#          CadQuery constraint kinds to apply between the resolved pair)
_CONSTRAINT_QUERY_KIND = {'flush': 'faces', 'offset': 'faces', 'coaxial': 'edges'}
_CONSTRAINT_CQ_KINDS = {'flush': ('Plane',), 'offset': ('Plane',), 'coaxial': ('Axis', 'Point')}


def referenced_part_names(spec: Dict[str, Any]) -> set:
    """Best-effort extraction of the part name(s) a single constraint spec
    references, for DAG dependency-edge purposes (see GraphBuilder /
    TCAD-CON-5) — tolerant of malformed specs (returns whatever it can
    parse), unlike ConstraintBuilder._parse_constraint/_parse_tangent, which
    validate strictly and raise. Graph building runs before parts exist and
    before the real parse/solve pass, so it can't afford to be strict here;
    malformed specs still surface their real error later via apply_constraints."""
    names: set = set()

    def _from_ref(ref: Any) -> None:
        if isinstance(ref, dict):
            part = ref.get('part')
            if isinstance(part, str):
                names.add(part)
        elif isinstance(ref, str) and '.' in ref:
            names.add(ref.split('.', 1)[0])

    for ref in spec.get('faces') or []:
        _from_ref(ref)
    for ref in spec.get('edges') or []:
        _from_ref(ref)
    if 'face' in spec:
        _from_ref(spec['face'])
    if 'edge' in spec:
        _from_ref(spec['edge'])

    return names


class ConstraintBuilderError(TiaCADError):
    """Raised when a constraint spec is invalid or cannot be solved."""

    def __init__(self, message: str, constraint_index: Optional[int] = None):
        self.constraint_index = constraint_index
        super().__init__(message)


class ConstraintBuilder:
    """
    Solves `constraints:` YAML specs and bakes the result into part transforms.

    Args:
        registry: PartRegistry containing all built parts (mutated in place —
            constrained parts are replaced with their solved position/orientation).
        spatial_resolver: SpatialResolver over the same registry, used to
            resolve face normals for the 'offset' post-solve translate.
    """

    def __init__(self, registry: PartRegistry, spatial_resolver: SpatialResolver):
        self.registry = registry
        self.spatial_resolver = spatial_resolver

    def apply_constraints(self, constraints_spec: List[Dict[str, Any]]) -> set:
        """Solve every constraint in `constraints_spec` and bake the results
        into the registry. No-op for an empty/missing list.

        Returns the set of part names whose geometry/position was touched
        (baked into), so a caller like the watcher (TCAD-CON-5) can refresh
        any incremental-build cache entries for exactly those parts — the
        cache stores pre-constraint geometry (populated before this runs),
        so a stale entry would silently un-apply the constraint on the next
        cache restore."""
        if not constraints_spec:
            return set()

        parsed = [self._parse_constraint(i, spec) for i, spec in enumerate(constraints_spec)]

        for ctype, ref_part, _, mov_part, _, _ in parsed:
            if not self.registry.exists(ref_part):
                raise ConstraintBuilderError(
                    f"Constraint references unknown part '{ref_part}'. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )
            if not self.registry.exists(mov_part):
                raise ConstraintBuilderError(
                    f"Constraint references unknown part '{mov_part}'. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )

        # 'tangent' never touches CadQuery's Assembly/solve() — see
        # _apply_tangent_translate for why (a lone PointInPlane constraint
        # leaves 5 of 6 rigid-body freedoms open, so a real solve() there can
        # rotate the part arbitrarily instead of just translating it).
        solved_indexed = [(i, p) for i, p in enumerate(parsed) if p[0] != 'tangent']
        solved = [p for _, p in solved_indexed]
        tangents = [p for p in parsed if p[0] == 'tangent']

        self._check_plane_conflicts(solved_indexed)

        touched_parts: set = {mov_part for _ctype, _rp, _rs, mov_part, _ms, _d in tangents}

        if solved:
            involved_parts: List[str] = []
            seen = set()
            for _ctype, ref_part, _, mov_part, _, _ in solved:
                for p in (ref_part, mov_part):
                    if p not in seen:
                        seen.add(p)
                        involved_parts.append(p)

            touched_parts.update(involved_parts)

            assembly = cq.Assembly()
            for part_name in involved_parts:
                assembly.add(self.registry.get(part_name).geometry, name=part_name, loc=cq.Location())

            for ctype, ref_part, ref_sel, mov_part, mov_sel, _distance in solved:
                query_kind = _CONSTRAINT_QUERY_KIND[ctype]
                ref_query = f"{ref_part}@{query_kind}@{ref_sel}"
                mov_query = f"{mov_part}@{query_kind}@{mov_sel}"
                for cq_kind in _CONSTRAINT_CQ_KINDS[ctype]:
                    assembly.constrain(ref_query, mov_query, cq_kind)

            try:
                assembly.solve()
            except Exception as e:
                raise ConstraintBuilderError(f"Constraint solve failed: {e}") from e

            # Bake the solved position into every involved part (locked parts
            # solve to an identity location, so this is a no-op for them).
            for part_name in involved_parts:
                self._bake_location(part_name, assembly.objects[part_name].loc)

            # 'offset' constraints add a translate on top of the now-baked flush
            # position, along the reference face's normal (resolved fresh, so it
            # reflects the reference part's actual — possibly also-constrained — pose).
            for ctype, ref_part, ref_sel, mov_part, _mov_sel, distance in solved:
                if ctype == 'offset':
                    self._apply_offset_translate(mov_part, ref_part, ref_sel, distance)

        # 'tangent' is applied last (after any other constraints in the same
        # batch have been baked), so its reference face is resolved from its
        # actual — possibly also-constrained — current pose.
        for _ctype, ref_part, ref_sel, mov_part, mov_sel, radius in tangents:
            self._apply_tangent_translate(mov_part, mov_sel, ref_part, ref_sel, radius)

        return touched_parts

    def _check_plane_conflicts(self, solved_indexed: List[Tuple[int, Tuple[str, str, str, str, str, float]]]) -> None:
        """Detect 'flush'/'offset' constraints that mate the same moving face
        against two reference planes that don't coincide, before calling
        CadQuery's `.solve()`.

        Both 'flush' and 'offset' apply the identical zero-gap 'Plane'
        constraint kind during solve() ('offset' only adds its extra
        translate afterward — see module docstring), so if the same
        (mov_part, mov_sel) face is mated 'Plane' against two reference
        faces that aren't the same plane in space, IPOPT is asked to
        satisfy two contradictory equations at once. This is exactly the
        "ambiguity bug with two overlapping planar constraints on the same
        pair" flagged as a known CadQuery rough edge during TCAD-CON-1's
        scoping — instead of letting that surface as an opaque solve
        failure (or a silent, arbitrary compromise), catch it here with a
        precise error naming the two conflicting constraints.

        Reference planes that *are* coincident (parallel normals, same
        offset — e.g. two different reference parts whose faces happen to
        share a plane) are legitimate and not flagged. Scope is deliberately
        'flush'/'offset' only: 'coaxial' mates edges via 'Axis'+'Point', a
        different consistency question this pass doesn't address.
        """
        by_moving_face: Dict[Tuple[str, str], List[Tuple[int, str, str]]] = {}
        for i, (ctype, ref_part, ref_sel, mov_part, mov_sel, _distance) in solved_indexed:
            if ctype not in ('flush', 'offset'):
                continue
            by_moving_face.setdefault((mov_part, mov_sel), []).append((i, ref_part, ref_sel))

        for (mov_part, mov_sel), entries in by_moving_face.items():
            if len(entries) < 2:
                continue
            first_i, first_ref_part, first_ref_sel = entries[0]
            first_ref = self.spatial_resolver.resolve(
                {'type': 'face', 'part': first_ref_part, 'selector': first_ref_sel}
            )
            for i, ref_part, ref_sel in entries[1:]:
                ref = self.spatial_resolver.resolve({'type': 'face', 'part': ref_part, 'selector': ref_sel})
                if not self._planes_coincide(first_ref.position, first_ref.orientation, ref.position, ref.orientation):
                    raise ConstraintBuilderError(
                        f"Constraints {first_i} and {i} both mate '{mov_part}.{mov_sel}' flush/offset "
                        f"against a different reference plane ('{first_ref_part}.{first_ref_sel}' vs "
                        f"'{ref_part}.{ref_sel}') that isn't coincident with the first — CadQuery's "
                        f"solver can't satisfy both simultaneously. Constrain a different face of "
                        f"'{mov_part}' for the second mate, or drop one of the two constraints.",
                        constraint_index=i,
                    )

    @staticmethod
    def _planes_coincide(pos1: np.ndarray, normal1: np.ndarray, pos2: np.ndarray, normal2: np.ndarray,
                          tol: float = 1e-6) -> bool:
        """True if two (position, normal) planes are the same plane in space
        (normals parallel or antiparallel, and coplanar — a point on one
        plane lies on the other)."""
        if np.linalg.norm(np.cross(normal1, normal2)) > tol:
            return False
        return abs(float(np.dot(pos2 - pos1, normal1))) <= tol

    def _parse_constraint(self, index: int, spec: Dict[str, Any]) -> Tuple[str, str, str, str, str, float]:
        """Validate one constraint spec, returning
        (type, ref_part, ref_selector, mov_part, mov_selector, distance)."""
        ctype = spec.get('type')
        if ctype in RESERVED_CONSTRAINT_TYPES:
            raise ConstraintBuilderError(
                f"Constraint {index}: type '{ctype}' is reserved for a future revision and "
                f"not yet implemented (see tt show TCAD-CON-9, or ROADMAP.md 'Constraint Solver').",
                constraint_index=index,
            )
        if ctype not in IMPLEMENTED_CONSTRAINT_TYPES:
            raise ConstraintBuilderError(
                f"Constraint {index}: unknown type '{ctype}'. "
                f"Implemented: {sorted(IMPLEMENTED_CONSTRAINT_TYPES)}; "
                f"reserved for later: {sorted(RESERVED_CONSTRAINT_TYPES)}.",
                constraint_index=index,
            )

        if ctype == 'tangent':
            return self._parse_tangent(index, spec)

        if ctype == 'coaxial':
            refs = spec.get('edges')
            ref_field, resolver = 'edges', self._edge_selector
        else:
            refs = spec.get('faces')
            ref_field, resolver = 'faces', self._face_selector

        if not isinstance(refs, list) or len(refs) != 2:
            raise ConstraintBuilderError(
                f"Constraint {index} (type '{ctype}') requires a '{ref_field}' list of exactly "
                f"2 entries [reference, moving], got: {refs}",
                constraint_index=index,
            )
        ref_part, ref_sel = resolver(refs[0], index)
        mov_part, mov_sel = resolver(refs[1], index)
        if ref_part == mov_part:
            raise ConstraintBuilderError(
                f"Constraint {index}: reference and moving {ref_field} both belong to part "
                f"'{ref_part}' — a constraint needs two distinct parts.",
                constraint_index=index,
            )

        distance = 0.0
        if ctype == 'offset':
            if 'distance' not in spec:
                raise ConstraintBuilderError(
                    f"Constraint {index} (type 'offset') requires a 'distance' field.",
                    constraint_index=index,
                )
            distance = self._parse_distance(spec['distance'], index)

        return ctype, ref_part, ref_sel, mov_part, mov_sel, distance

    def _edge_selector(self, ref_spec: Any, constraint_index: int) -> Tuple[str, str]:
        """Resolve a constraint edge reference to (part_name, cadquery_selector_string).
        Inline {type: edge, part, selector} only — there is no auto-generated
        edge-name vocabulary (unlike faces' FACE_SELECTOR_MAP) to resolve a
        dotted 'part.edge_name' shorthand against."""
        if isinstance(ref_spec, dict) and ref_spec.get('type') == 'edge' and 'part' in ref_spec and 'selector' in ref_spec:
            return ref_spec['part'], ref_spec['selector']

        raise ConstraintBuilderError(
            f"Constraint {constraint_index}: edge reference must be an inline "
            f"{{type: edge, part, selector}} spec (e.g. {{type: edge, part: pin, selector: '%CIRCLE and >Z'}}), "
            f"got: {ref_spec!r}",
            constraint_index=constraint_index,
        )

    def _face_selector(self, ref_spec: Any, constraint_index: int) -> Tuple[str, str]:
        """Resolve a constraint face reference to (part_name, cadquery_selector_string)."""
        if isinstance(ref_spec, dict):
            if ref_spec.get('type') != 'face' or 'part' not in ref_spec or 'selector' not in ref_spec:
                raise ConstraintBuilderError(
                    f"Constraint {constraint_index}: inline face reference must be "
                    f"{{type: face, part: ..., selector: ...}}, got: {ref_spec}",
                    constraint_index=constraint_index,
                )
            return ref_spec['part'], ref_spec['selector']

        if isinstance(ref_spec, str):
            if '.' not in ref_spec:
                raise ConstraintBuilderError(
                    f"Constraint {constraint_index}: face reference '{ref_spec}' must be "
                    f"'part.face_name' (e.g. 'bracket.face_bottom') or an inline "
                    f"{{type: face, part, selector}} spec.",
                    constraint_index=constraint_index,
                )
            part_name, ref_name = self.spatial_resolver._split_part_ref(ref_spec)
            selector = FACE_SELECTOR_MAP.get(ref_name)
            if selector is None:
                raise ConstraintBuilderError(
                    f"Constraint {constraint_index}: unknown face reference '{ref_name}' in "
                    f"'{ref_spec}'. Valid auto face names: {', '.join(FACE_SELECTOR_MAP)}, or use "
                    f"an inline {{type: face, part, selector}} spec for a custom selector.",
                    constraint_index=constraint_index,
                )
            return part_name, selector

        raise ConstraintBuilderError(
            f"Constraint {constraint_index}: face reference must be a string ('part.face_name') "
            f"or dict ({{type: face, part, selector}}), got: {ref_spec!r}",
            constraint_index=constraint_index,
        )

    def _parse_tangent(self, index: int, spec: Dict[str, Any]) -> Tuple[str, str, str, str, str, float]:
        """Validate a 'tangent' spec: a 'face' (reference plane) and an 'edge'
        (moving cylindrical edge). Unlike the other constraint types there's no
        symmetric [reference, moving] list — the two sides are different kinds
        of reference, so the roles are named explicitly instead. The moving
        edge's radius is measured here (via CadQuery's `Edge.radius()`) rather
        than supplied in YAML, since 'tangent' means "touching", not
        "offset by a distance you pick" — the whole point is deriving that
        distance from the geometry."""
        if 'face' not in spec or 'edge' not in spec:
            raise ConstraintBuilderError(
                f"Constraint {index} (type 'tangent') requires a 'face' (reference plane) "
                f"and an 'edge' (moving cylindrical edge) field, got: {spec}",
                constraint_index=index,
            )
        ref_part, ref_sel = self._face_selector(spec['face'], index)
        mov_part, mov_sel = self._edge_selector(spec['edge'], index)
        if ref_part == mov_part:
            raise ConstraintBuilderError(
                f"Constraint {index}: reference face and moving edge both belong to part "
                f"'{ref_part}' — a constraint needs two distinct parts.",
                constraint_index=index,
            )

        radius = 0.0
        if self.registry.exists(mov_part):
            # Existence is re-checked (and raises a clearer, consistent error)
            # by apply_constraints right after parsing every constraint — skip
            # the lookup here rather than let a missing part surface as a raw
            # KeyError from inside radius measurement.
            try:
                edge = self.registry.get(mov_part).geometry.edges(mov_sel).val()
                radius = edge.radius()
            except Exception as e:
                raise ConstraintBuilderError(
                    f"Constraint {index} (type 'tangent'): edge selector '{mov_sel}' on part "
                    f"'{mov_part}' must resolve to a single circular edge to measure a radius "
                    f"from ({e}).",
                    constraint_index=index,
                ) from e

        return 'tangent', ref_part, ref_sel, mov_part, mov_sel, radius

    @staticmethod
    def _parse_distance(value: Any, constraint_index: int) -> float:
        """Parse a 'distance' value — plain number, or a string with an 'mm' suffix."""
        if isinstance(value, str):
            stripped = value[:-2] if value.endswith('mm') else value
            try:
                return float(stripped)
            except ValueError as e:
                raise ConstraintBuilderError(
                    f"Constraint {constraint_index}: invalid distance '{value}'", constraint_index=constraint_index
                ) from e
        try:
            return float(value)
        except (TypeError, ValueError) as e:
            raise ConstraintBuilderError(
                f"Constraint {constraint_index}: invalid distance {value!r}", constraint_index=constraint_index
            ) from e

    def _bake_location(self, part_name: str, loc: cq.Location) -> None:
        """Decompose a solved cq.Location into rotation+translation and apply
        it to `part_name` via TransformTracker, keeping current_position/
        current_orientation consistent with every other transform path."""
        part = self.registry.get(part_name)
        trsf = loc.wrapped.Transformation()

        axis_vec = gp_Vec()
        angle_rad = trsf.GetRotation().GetVectorAndAngle(axis_vec)[0]
        translation_part = trsf.TranslationPart()
        translation = (translation_part.X(), translation_part.Y(), translation_part.Z())

        tracker = TransformTracker(
            part.geometry, backend=part.backend, initial_orientation=part.current_orientation
        )
        if abs(angle_rad) > 1e-9:
            axis = (axis_vec.X(), axis_vec.Y(), axis_vec.Z())
            tracker.apply_transform({
                'type': 'rotate',
                'angle': math.degrees(angle_rad),
                'axis': axis,
                'origin': [0.0, 0.0, 0.0],
            })
        if any(abs(c) > 1e-12 for c in translation):
            tracker.apply_transform({'type': 'translate', 'offset': list(translation)})

        self.registry.replace(Part(
            name=part_name,
            geometry=tracker.get_geometry(),
            metadata=part.metadata,
            current_position=tracker.current_position,
            current_orientation=tracker.current_orientation,
            backend=part.backend,
        ))

    def _apply_offset_translate(self, mov_part_name: str, ref_part: str, ref_sel: str, distance: float) -> None:
        """Apply the 'offset' distance as an additional translate on the
        already flush-solved moving part, along the reference face's normal."""
        ref_face_ref = self.spatial_resolver.resolve({'type': 'face', 'part': ref_part, 'selector': ref_sel})
        normal = ref_face_ref.orientation
        offset_vec = (normal * distance).tolist()

        part = self.registry.get(mov_part_name)
        tracker = TransformTracker(
            part.geometry, backend=part.backend, initial_orientation=part.current_orientation
        )
        tracker.apply_transform({'type': 'translate', 'offset': offset_vec})

        self.registry.replace(Part(
            name=mov_part_name,
            geometry=tracker.get_geometry(),
            metadata=part.metadata,
            current_position=tracker.current_position,
            current_orientation=tracker.current_orientation,
            backend=part.backend,
        ))

    def _apply_tangent_translate(
        self, mov_part_name: str, mov_sel: str, ref_part: str, ref_sel: str, radius: float
    ) -> None:
        """Translate the moving part along the reference face's normal so its
        selected circular edge's center sits exactly `radius` away from the
        plane — i.e. the cylinder's curved surface touches the plane instead
        of crossing or floating clear of it. Computed directly rather than via
        CadQuery's solver: see the module docstring for why a real
        `PointInPlane` solve leaves rotation freedom open that this avoids
        entirely by never invoking `.solve()` in the first place.

        The edge's center is read straight off the CadQuery geometry (not via
        `SpatialResolver`'s generic edge extraction) because that path also
        computes a tangent direction we don't need here, and does so via a
        start/end-point difference that raises on a closed circular edge
        (start == end, zero length) rather than the circle's own derivative."""
        ref_face_ref = self.spatial_resolver.resolve({'type': 'face', 'part': ref_part, 'selector': ref_sel})
        normal = ref_face_ref.orientation
        edge = self.registry.get(mov_part_name).geometry.edges(mov_sel).val()
        edge_center = np.array(edge.Center().toTuple())
        current_distance = float(np.dot(edge_center - ref_face_ref.position, normal))
        self._apply_offset_translate(mov_part_name, ref_part, ref_sel, radius - current_distance)
