"""
ConstraintBuilder - Declarative assembly constraints (TCAD-CON-1 MVP)

Wraps CadQuery's own `Assembly.constrain()`/`.solve()` (casadi+IPOPT) rather
than implementing a constraint solver from scratch — see ROADMAP.md "Next
Milestone: Constraint Solver" and `tt show TCAD-CON-1` for the scoping
investigation that found this already-working, already-a-dependency solver.

MVP scope: 'flush' (coincident faces, opposed normals) and 'offset' (flush,
plus an additional translate along the reference face's normal) are
implemented, both via CadQuery's 'Plane' constraint kind — the exact pairing
verified working end-to-end during TCAD-CON-1's scoping (a 5mm cube flush-
mated onto a 10mm cube). 'coaxial' and 'tangent' are recognized by the
schema but not implemented here: only face-based constraints translate
cleanly onto CadQuery's Assembly query grammar ("part@faces@selector"),
since `Assembly._query` only accepts string selectors run against a part's
real geometry — not TiaCAD's synthetic axis_x/y/z references or arbitrary
two-point axes. Making coaxial/tangent work needs either edge-selector
support in that same grammar or a lower-level ConstraintSolver integration
that bypasses Assembly's query strings entirely; both are unvalidated, so
they raise ConstraintBuilderError with a pointer to the follow-up task
rather than guessing at untested constraint-kind semantics.

Design notes:
- Convention: `faces: [reference, moving]` — the reference face's part is
  the one `Assembly.solve()` auto-locks (it locks the first entity
  referenced across all constraints); the moving face's part is the one
  repositioned to satisfy the constraint.
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
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import cadquery as cq
from OCP.gp import gp_Vec

from ..part import Part, PartRegistry
from ..transform_tracker import TransformTracker
from ..spatial_resolver import SpatialResolver, FACE_SELECTOR_MAP

IMPLEMENTED_CONSTRAINT_TYPES = {'flush', 'offset'}
RESERVED_CONSTRAINT_TYPES = {'coaxial', 'tangent'}


class ConstraintBuilderError(Exception):
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

    def apply_constraints(self, constraints_spec: List[Dict[str, Any]]) -> None:
        """Solve every constraint in `constraints_spec` and bake the results
        into the registry. No-op for an empty/missing list."""
        if not constraints_spec:
            return

        parsed = [self._parse_constraint(i, spec) for i, spec in enumerate(constraints_spec)]

        involved_parts: List[str] = []
        seen = set()
        for ref_part, _, mov_part, _, _ in parsed:
            for p in (ref_part, mov_part):
                if p not in seen:
                    seen.add(p)
                    involved_parts.append(p)
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

        assembly = cq.Assembly()
        for part_name in involved_parts:
            assembly.add(self.registry.get(part_name).geometry, name=part_name, loc=cq.Location())

        for ref_part, ref_sel, mov_part, mov_sel, _distance in parsed:
            assembly.constrain(f"{ref_part}@faces@{ref_sel}", f"{mov_part}@faces@{mov_sel}", "Plane")

        try:
            assembly.solve()
        except Exception as e:
            raise ConstraintBuilderError(f"Constraint solve failed: {e}") from e

        # Bake the solved flush/coincident position into every involved part
        # (locked parts solve to an identity location, so this is a no-op for them).
        for part_name in involved_parts:
            self._bake_location(part_name, assembly.objects[part_name].loc)

        # 'offset' constraints add a translate on top of the now-baked flush
        # position, along the reference face's normal (resolved fresh, so it
        # reflects the reference part's actual — possibly also-constrained — pose).
        for ref_part, ref_sel, mov_part, _mov_sel, distance in parsed:
            if distance:
                self._apply_offset_translate(mov_part, ref_part, ref_sel, distance)

    def _parse_constraint(self, index: int, spec: Dict[str, Any]) -> Tuple[str, str, str, str, float]:
        """Validate one constraint spec, returning (ref_part, ref_selector, mov_part, mov_selector, distance)."""
        ctype = spec.get('type')
        if ctype in RESERVED_CONSTRAINT_TYPES:
            raise ConstraintBuilderError(
                f"Constraint {index}: type '{ctype}' is reserved for a future revision and "
                f"not yet implemented (see tt show TCAD-CON-3, or ROADMAP.md 'Constraint Solver').",
                constraint_index=index,
            )
        if ctype not in IMPLEMENTED_CONSTRAINT_TYPES:
            raise ConstraintBuilderError(
                f"Constraint {index}: unknown type '{ctype}'. "
                f"Implemented: {sorted(IMPLEMENTED_CONSTRAINT_TYPES)}; "
                f"reserved for later: {sorted(RESERVED_CONSTRAINT_TYPES)}.",
                constraint_index=index,
            )

        faces = spec.get('faces')
        if not isinstance(faces, list) or len(faces) != 2:
            raise ConstraintBuilderError(
                f"Constraint {index} (type '{ctype}') requires a 'faces' list of exactly "
                f"2 entries [reference, moving], got: {faces}",
                constraint_index=index,
            )
        ref_part, ref_sel = self._face_selector(faces[0], index)
        mov_part, mov_sel = self._face_selector(faces[1], index)
        if ref_part == mov_part:
            raise ConstraintBuilderError(
                f"Constraint {index}: reference and moving faces both belong to part "
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

        return ref_part, ref_sel, mov_part, mov_sel, distance

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
