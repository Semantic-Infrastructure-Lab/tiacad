# Changelog

All notable changes to TiaCAD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-07-11 (legacy-syntax deprecation warnings + GitHub `@branch` import)

Two API-surface additions (session `weightless-universe-0711`):
- **Deprecation warnings** for the four legacy syntaxes that were replaced in
  v3.1.x — cone `radius_bottom`/`radius_top`, linear-pattern scalar `spacing`
  with `direction`, the `translate: {offset:}` wrapper used without `to:`, and
  the list-form `export:` section. Each now raises a runtime
  `DeprecationWarning` pointing at MIGRATION_GUIDE_V3.md *and* applies a
  backward-compat mapping so old models still build. Implements the long-open
  plan in `docs/developer/API_DEPRECATION_STRATEGY.md`.
- **GitHub import branch override.** `github:user/repo/file.yaml@branch` now
  selects a branch (default `main`, slashes allowed), branch-namespaced in the
  download cache. Closes KNOWN_LIMITATIONS.md #4.

Full non-visual suite: 1859 passed (was 1840), 0 failed (+20 tests:
`test_deprecation_warnings.py`, GitHub-branch cases in `test_component_import.py`).

### Fixed - 2026-07-11 (SpatialResolver longest-prefix-match for dotted names)

`SpatialResolver._resolve_name` split a `"part.ref"` reference on the *first*
dot, so a namespaced import part like `m3.shaft` (itself containing a dot
from `as: m3`) couldn't be combined with a `.face_top`/`.axis_z` suffix —
`"m3.shaft.face_top"` resolved as part `m3` (not found) instead of part
`m3.shaft`. Documented as a known gap in KNOWN_LIMITATIONS.md #11, worked
around in `hardware_assembly_demo.yaml` with flat operation-name aliases.
Added `SpatialResolver._split_part_ref`, which tries split points from the
last dot backward and picks the longest prefix that's an actual registered
part, falling back to the old first-dot split only when nothing matches.
3 new tests in `test_spatial_resolver.py::TestNamespacedPartLocalReferences`.
Full non-visual suite: 1840 passed (was 1837), 0 failed.

### Removed - 2026-07-11 (redundant Tier-2 pytest classes trimmed)

Per VALIDATION_STRENGTHENING.md §4.1's deferred-trim note: 14 legacy pytest
classes deleted outright (asserted only a final part's volume/bbox, now fully
subsumed by that example's embedded `expect:` block — e.g. `TestSimpleBox`,
`TestChamferedBracket`, `TestFormatsDemo`), plus final-only *methods* trimmed
from 7 more classes while keeping their sub-part/cross-file methods. Two
near-misses that looked redundant by name but measured a different sub-part
than their file's `expect: final:` covers (`TestAutoRefsCylinderAssembly`,
`TestAnchorsDemoPlatform`) were kept in full rather than trimmed. 39 test
methods removed from `test_correctness/test_example_contracts.py` (160→121).
Full non-visual suite: 1837 passed (was 1876 before the trim), 0 failed —
this is the full T0→T5 confidence-ladder checklist closing out, not a
regression: the removed tests' coverage now lives in `expect:` contracts.

### Added - 2026-07-11 (Tier 5 corpus — negative-input testing, ladder complete)

#### Negative-input validation corpus (VALIDATION_STRENGTHENING.md section 5, Tier 5)

`examples/validation/negative/`: 6 new intentionally-broken `.tiacad` models —
`N1_bad_spatial_ref`, `N2_cyclic_parameter`, `N3_negative_dimension`,
`N4_unknown_primitive`, `N5_malformed_schema`, `N6_duplicate_part_name` — each
triggering one specific error class. New
`tiacad_core/tests/test_correctness/test_negative_contracts.py` asserts each
raises a specific, typed `TiaCADError` subclass (`OperationsBuilderError`,
`ParameterResolutionError`, `PartsBuilderError` x3, `TiaCADParserError`) with a
message that names the actual problem — never a bare exception, never an
uncaught traceback, never a silent success. Every case was verified by
actually running the broken file through `TiaCADParser.parse_file()` before
the assertion was written, per this tier's own "verify, don't assume" mandate.
This is the last unchecked item on the confidence-ladder deliverables
checklist (VALIDATION_STRENGTHENING.md section 5) — **the full T0→T5 ladder is
now shipped.**

### Fixed - 2026-07-11 (Tier 5 corpus)

#### Two silent/opaque-failure gaps found while verifying the negative corpus

Found while confirming each Tier 5 fixture actually fails the way it should
(not assumed from reading code): (1) a negative or zero primitive dimension
(box/cylinder/sphere/cone/torus) reached the OCCT kernel unchecked and raised
a **message-less** `Standard_DomainError`, surfacing as a `PartsBuilderError`
with an empty message body — typed, but not "loud and correct." Fixed with a
new `PartsBuilder._require_positive()` validation, called before the backend
for all five primitives (`tiacad_core/parser/parts_builder.py`), producing
messages like `"Box 'block' has invalid width: -10 (must be a positive
number)"`. (2) a duplicate part name (same key twice under `parts:`) parsed
and built **with no error at all** — PyYAML's default loader silently let the
second definition clobber the first. Fixed in
`tiacad_core/parser/yaml_with_lines.py::construct_mapping_with_lines`, which
now tracks keys per mapping level and raises on a same-level duplicate,
naming the key and its first-seen line. See KNOWN_LIMITATIONS.md #12.

Full non-visual suite: 1876 passed (was 1863), 0 failed — 13 new tests, no
regressions; visual suite unchanged at 67 passed.

### Added - 2026-07-11 (Tier 4 corpus)

#### T4 assembly relational validation corpus (VALIDATION_STRENGTHENING.md section 5)

`examples/validation/`: 3 new Tier-4 models — `T4_two_boxes_flush`, `T4_standoff_stack`,
`T4_bolted_bracket` — plus a new `expect: relations:` contract on the existing 29-part
`examples/hardware_assembly_demo.yaml`. These prove parts are correctly positioned
*relative to each other*, the thing single-part volume/bbox and visual regression both
miss. `T4_two_boxes_flush` uses part-level `translate:` (the KNOWN_LIMITATIONS.md #9 fix)
to butt two boxes face-to-face with an exact zero gap. `T4_standoff_stack` derives from
`examples/pcb_standoff_assembly.yaml` and stacks a standoff + spacer + screw, exercising
`coaxial` and `flush` together across three interfaces. `T4_bolted_bracket` drills a
through-hole and positions a bolt whose shaft is coaxial with the hole (with real
clearance, `shaft_r < hole_r`) and whose head sits flush on the bracket face. All three
were hand-derived (closed-form volumes, exact face/axis positions from the declared
transforms) and independently re-verified against direct `get_bounds()` measurement
before being written into `expect:`.

Added `expect: no_overlap:` (`tiacad_core/testing/contracts.py::_check_no_overlap`,
schema in `tiacad-schema.json`): a new no-interpenetration contract check — for each
named `[partA, partB]` pair, `vol(A) + vol(B)` must equal `vol(union(A, B))` within
tolerance, so parts that only touch (or don't touch) pass and parts that overlap fail.
Verified against a deliberately-overlapping synthetic pair (`test_assembly_contracts.py::
TestNoOverlapEngine::test_interpenetrating_boxes_fail_no_overlap`) to confirm it actually
detects the bug class it exists for, not just passes vacuously on the corpus.

New `tiacad_core/tests/test_correctness/test_assembly_contracts.py`: direct synthetic
coverage for the new `no_overlap` engine (touching/disjoint/overlapping/missing-part
cases) plus a second, independently-derived hand-verification pass over the Tier 4
corpus's relational claims (raw `get_bounds()` math, not routed through `check_contract`)
— the generic `test_embedded_contracts.py` sweep already discovers and checks every
`expect:` block including `relations:`/`no_overlap:`, so this file deliberately does not
duplicate that; see its module docstring.

Regenerated `golden_hashes.json` for the 3 new T4 models only (verified via diff — no
existing entries changed).

### Fixed - 2026-07-11 (Tier 4 corpus)

#### Screw/bolt heads floated disconnected from their own shafts

Two bugs, found while building the Tier 4 relational contract for
`examples/hardware_assembly_demo.yaml`: (1) all 8 fastener component files
(`examples/components/m{3,4,5,6}_{screw,bolt}.yaml` and their
`tiacad_core/stdlib/hardware/` counterparts) positioned each screw's `head` at
`Z=length` instead of `Z=length/2+head_height/2`, leaving the head floating with a gap
above the shaft's actual tip instead of sitting flush on it (m3: 2.5mm gap). (2)
`hardware_assembly_demo.yaml` itself only ever translated each screw's `shaft` to its
assembly position, never the `head`, so the head stayed stranded near the origin
regardless of where the shaft ended up. Fixed both: corrected the translate formula in
all 8 component files, and added `m{3,4,5,6}_head_pos` operations to
`hardware_assembly_demo.yaml` (same offset as each shaft's own `_pos`) so the head now
travels with its shaft. `hardware_assembly_demo.yaml`'s new `expect: relations:` asserts
`coaxial`/`flush` (zero gap) between each shaft and its head — confirmed this would have
failed before the fix and passes after. Part count in that file rose from 25 to 29;
`test_example_contracts.py::TestHardwareAssemblyDemo` updated accordingly. See
`KNOWN_LIMITATIONS.md` #11, which also documents a related resolver limitation found in
the process (dotted namespaced part names can't be combined with `.face_top`/`.axis_z`
suffixes in `expect: relations:` — worked around with flat operation names, not fixed).

### Added - 2026-07-11 (Tier 3 corpus)

#### T3 composite-part validation corpus (VALIDATION_STRENGTHENING.md section 5)

`examples/validation/`: 4 new Tier-3 models — `T3_plate_one_hole`, `T3_plate_bolt_circle`,
`T3_bracket_fillet`, `T3_lego_2x1` — each a multi-feature composite part (plate + hole(s),
fillet-all-edges box + hole, LEGO 2x1 brick) with an `expect:` volume derived from
inclusion-exclusion of the closed-form Tier-0/1 oracles, plus a hard `components: 1`
manifold-health gate (BREP solid count, not mesh islands). `T3_lego_2x1` is the model
named in section 3's Tier 3 motivation — "a part that measures fine but is secretly two
solids" — and explicitly asserts `components: 1` / `watertight: true`. Found and fixed a
real bug while deriving it (see Fixed, below). `test_geometry_validation.py`'s
`test_mounting_plate_bolt_circle_watertight` and `test_lego_brick_2x1_is_single_component`
were strengthened from mesh-island/watertight-only observations to a hard BREP-level
`count_solids() == 1` assertion, per section 3's "extend `test_geometry_validation.py` to
assert component count ... as failures, not observations."

### Fixed - 2026-07-11 (Tier 3 corpus)

#### `lego_brick_2x1`/`lego_brick_3x1`: cavity floor was 1.5mm, not the declared 1.0mm

`cavity_positioned`'s translate used `[wall_thickness, wall_thickness, bottom_thickness]`
for `[X, Y, Z]`, but `brick_cavity`'s own box params put its "depth" (the vertical cavity
dimension, `brick_height - bottom_thickness`) on the Y axis and its "height" (the lateral
inset, `brick_width - 2*wall_thickness`) on Z (box maps `width->X, depth->Y, height->Z`).
The translate's Y/Z components were swapped relative to what those axes actually needed:
the vertical (Y) offset used `wall_thickness` (1.5mm) instead of `bottom_thickness`
(1.0mm), so the printed floor was 1.5mm thick regardless of the `bottom_thickness`
parameter's value, and the cavity silently overshot the top face by 0.5mm (clipped, no
visible effect there). Found while hand-deriving `T3_lego_2x1.tiacad`'s inclusion-exclusion
volume oracle — the naive closed-form total didn't match the measured build until the
actual (clipped) cavity bounds were inspected. Did not affect connectivity or
watertightness (both were already `true`); only the floor thickness/volume. Fixed by
swapping the Y/Z translate components; `expect: volume:` updated in both examples
(2x1: 906.707→891.306, 3x1: 1309.96→1283.109, both well within their existing
`test_example_contracts.py` tolerances). See `KNOWN_LIMITATIONS.md` #10.

### Fixed - 2026-07-11

#### Part-level `translate:`/`rotate:` were dead schema syntax

The schema documents `translate:`/`rotate:` as valid keys directly on a `parts:` entry
(the "auto-generated anchors" feature demoed by `anchors_demo.yaml` and the
`auto_references_*.yaml` examples) — `parts_builder.py::build_part` never read either
key, so every part positioned this way silently built at its untranslated local origin.
27 usages across 12 example files were affected, including `pcb_standoff_assembly.yaml`
(one of the two examples seeded with an `expect:` contract last session — its `pcb` part
never reached its intended Z height). Found while building the T0/T1 ladder corpus (a
`T1_union_overlap` model came out at half its expected volume because the two boxes were
secretly coincident). Fixed by `OperationsBuilder.apply_inline_part_transforms()`, which
reuses the same `TransformTracker`/`spatial_resolver` machinery as `operations: type:
transform`, wired into the build pipeline right after all parts + the document's
`SpatialResolver` exist. See `KNOWN_LIMITATIONS.md` #9 and
`test_parser/test_inline_part_transforms.py` for full detail and regression coverage.

#### `polygon` primitive's `circumscribed` flag was inverted (all stdlib hex nuts oversized)

`_build_polygon` passed its own `circumscribed` flag straight through to
`cq.Workplane.polygon(circumscribed=...)` — but CadQuery's flag means the opposite of
what the docstring (and this primitive's own contract) claims. Result: all four stdlib
hex nuts (`m3_nut.yaml`…`m6_nut.yaml`, the only users of `polygon`) built ~15.5%
oversized across flats (6.35/8.08/9.24/11.55mm instead of ISO 4032's 5.5/7.0/8.0/10.0mm)
— a printed M3 nut would not fit an M3 wrench. Found while building the `T0_polygon`
ladder-corpus model. Fixed by inverting the flag at the call site; added
`test_hex_body_across_flats_matches_iso4032` regression tests (none of the pre-existing
nut tests asserted across-flats at all). See `KNOWN_LIMITATIONS.md` #7.

### Added - 2026-07-11

#### T0/T1 validation ladder corpus (VALIDATION_STRENGTHENING.md section 5)

`examples/validation/`: 6 Tier-0 primitive models (box/cylinder/sphere/cone/torus/polygon),
each checked against its closed-form analytic volume/bbox formula, and 9 Tier-1
single-operation models (translate/rotate90/union/difference/intersection/pattern-linear/
pattern-polar/fillet/chamfer), each isolating exactly one operation on Tier-0 primitives.
Directly found the two bugs above.

#### `expect:` contracts for the full Tier-2 example corpus

Seeded reviewed `expect:` contracts (via `tiacad audit --write-contract`, cross-checked
against each file's existing hand-derived pytest assertions) for the 25 examples with a
Tier-2 pytest class in `test_example_contracts.py` that didn't already have one.
`test_embedded_contracts.py`'s generic parametrized test now discovers and checks 50
models total, up from 2.

### Fixed - 2026-07-10

#### Zero-volume torus primitive

The `torus` primitive produced a **degenerate zero-volume solid** on the CadQuery 2.8 /
OCP 7.9 kernel — `_build_torus` revolved a profile 360° about an axis lying in the
profile's own plane, which the kernel collapses to the flat 2D profile. Latent for the
life of the primitive because the only torus test asserted `part is not None`. Found by
the new property-based suite (section 4.2); fixed by using `cq.Solid.makeTorus` directly,
and `test_simple_torus` now asserts the Pappus volume and bounding box.

### Added - 2026-07-10

#### Property-based correctness tests (VALIDATION_STRENGTHENING.md section 4.2)

`test_correctness/test_property_based.py`: 18 Hypothesis property tests that check the
Tier-0/1 analytic oracles (volume, bounding box, surface area) over machine-generated
parameters for every primitive, plus translate/rotate volume-invariance, uniform-scale
`k³`, and boolean inclusion-exclusion. Runs `derandomize=True` so examples reproduce
bit-for-bit in CI. This suite immediately found a real, long-latent bug (see Fixed).
`hypothesis` added to `requirements.txt`/`pyproject.toml` and the CI import-guard.

#### Schema truth reconciliation (VALIDATION_STRENGTHENING.md section 4.8)

`test_schema_validation.py` now validates **every** example under `examples/` against
`tiacad-schema.json` (parametrized, 82 files), guarded against vacuous discovery. Standing
this gate up surfaced 27 committed-but-schema-invalid examples — all cases where the schema
was stricter than the parser. Reconciled the schema to parser reality (top-level
`name`/`description`/`anchors`/`imports`; string-or-object `export.formats`, `edges`, rotate
`around`; `{r,g,b}`/`{h,s,l}` colors; scalar text `size`; two-point axis refs; vector-list
`translate`; rich palette entries) while keeping all 32 negative tests rejecting bad input.

#### Determinism gate (VALIDATION_STRENGTHENING.md section 4.4)

`test_correctness/test_determinism.py`: proves the same YAML always produces the same
geometry. Two checks over the `expect:` corpus — self-consistency (build each model 3×
in one run, assert volume/bbox/mesh-hash agree exactly, no golden file needed) and a
golden comparison against a small, reviewed `golden_hashes.json` that catches drift
across sessions or CadQuery/OCCT kernel upgrades. `tiacad_core/testing/determinism.py`
hashes the raw exported-STL bytes (not canonicalized — canonicalizing would hide the
tessellation drift this gate exists to catch). Goldens are regenerated only by the
explicit, human-run `scripts/update_determinism_goldens.py`, mirroring the existing
`UPDATE_VISUAL_REFERENCES` pattern — never by the test suite itself. All 6 corpus models
build bit-identical mesh hashes across repeated builds on CadQuery 2.8.0 / OCP 7.9.3.1.1
(Python 3.12).

#### Embedded `expect:` contracts (VALIDATION_STRENGTHENING.md section 4.1)

The keystone of `docs/developer/VALIDATION_STRENGTHENING.md`: a model can now declare its
own ground-truth contract inline (`expect: {volume, bbox, watertight, components,
relations}`) instead of needing a hand-written pytest class. One generic parametrized test,
`test_correctness/test_embedded_contracts.py`, discovers and checks every example that
declares an `expect:` block — `tiacad_core/testing/contracts.py::check_contract()` does the
work, including `flush`/`coaxial` relation checks between named parts built on the existing
`SpatialResolver` dot-notation face/axis lookups (e.g. `standoff.axis_z` coaxial with
`screw.axis_z`). `tiacad check --contract` and `tiacad audit --write-contract` expose the
same engine on the CLI — the latter seeds a contract from a current build for human review,
never auto-writing to the file. Also closes G4: the dead, unused `validation:` schema block
is deleted, superseded by `expect:`.

Seeded first two reviewed contracts: `examples/simple_guitar_hanger.yaml` (Tier 1) and
`examples/pcb_standoff_assembly.yaml` (Tier 4, with a `coaxial` relation). Building this
tooling surfaced a real bug it wasn't even designed to look for:
`examples/mounting_plate_with_bolt_circle.yaml`'s boolean difference produces 3 disconnected
mesh components instead of 1 (confirmed via `tiacad validate-geometry`) — see below, now
fixed.

#### `mounting_plate_with_bolt_circle.yaml` / `rounded_mounting_plate.yaml` — bolt holes now actually pierce the plate

Both files produced 3 disconnected mesh components instead of 1: the bolt/center holes are
cylinders (default axis Z) patterned circularly around `axis: Z`, but the plate's actual thin
dimension is Y (box primitive maps `width->X, depth->Y, height->Z`). Rotating hole copies
around Z only translates a Z-cylinder's position in the XY-plane without reorienting it, so
only 2 of 6 holes ever lined up with the Y-thin face — and even those didn't reach the Y
faces (hole radius 3.25mm < plate half-thickness 4mm), leaving them as fully enclosed internal
cavities that mesh out as extra disconnected shells. Fixed by rotating the hole primitives 90°
about X before patterning (so their axis runs along Y) and patterning around `axis: Y` instead
of `Z`; `rounded_mounting_plate.yaml`'s fillet `edges: direction` also moved from `Z` to `Y` to
match (it was targeting the wrong, non-thin edges as "vertical corners"). Both examples now
build as a single watertight component and carry `expect:` contracts (`components: 1`) to
guard against regression. The plate's own box parameters were correct all along — the fix is
entirely in `operations:`, not the primitive dimensions.

#### Boolean-effect assertions (`BooleanEffectRule`)

Closes the systemic validation gap identified by the `awesome_guitar_hanger` mounting-hole
bug (`docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md`): every `difference` must
remove measurable volume from its base, every `intersection` must be non-empty, and a
`union`'s result cannot be smaller than its largest input. Runs automatically as part of
`AssemblyValidator` (`tiacad_core/validation/rules/boolean_effect_rule.py`) on every model,
in CI, with no per-model contract to write — flows into `validation_report.json` via the
existing debug-bundle pipeline for free.

The rule caught a second, previously-unknown instance of the exact same bug class in
`examples/guitar_hanger_named_points.yaml` the same session it shipped: `plate_with_holes`'s
screw holes had the same Y/Z axis-mapping error as `awesome_guitar_hanger` and never
actually cut the plate. Fixed alongside the rule; `TestGuitarHangerNamedPoints` gained a
hole-piercing regression test.

Also adds `TestAwesomeGuitarHangerHoles` to `test_example_contracts.py`, closing the gap
where that example had only a generic positive-volume smoke test — nothing previously
guarded the 2026-07-09 hole fix against silently regressing.

#### Metamorphic invariant suite (VALIDATION_STRENGTHENING.md section 4.3)

`test_correctness/test_metamorphic.py`: 26 self-contained geometric-relationship tests
that need no generators and no hand-picked expected values — translate/rotate/mirror
conservation, scale `k³`, union commutativity/idempotency, and boolean self-consistency
(inclusion-exclusion, difference-equals-minus-intersection, disjoint-subtract-is-a-no-op).
Run against deliberately asymmetric shapes so a bug that silently ignores a transform
can't pass by symmetry accident. This is the systematic version of the manual audit that
found the mounting-plate bug above — an inclusion-exclusion check would have caught that
whole bug class automatically instead of requiring a by-hand sweep of every example.

Also closed part of the G5 safety-net gap (section 4.5): `test_schema_validation.py`'s
32 tests were silently skipped whenever `jsonschema` failed to import, even though it's a
required dependency — converted to a hard assertion so a missing/broken dependency fails
loudly instead of vanishing the schema-validation net with no signal.

### Changed - 2026-07-09

#### Trust renderer: 8-panel grid with opposite-diagonal isometrics (restores rear coverage)

The trust render went from 6 panels (one isometric + X-Ray at the *same* angle) to 8
(2×4). Two isometrics now view from opposite diagonals (front-right-top and back-left-top),
plus a new Rear orthographic. Previously the rear iso added in `5fd8d05` had been silently
replaced by X-Ray at the front angle, leaving back faces and one side invisible from every
panel — a part mirrored to the wrong side or a back-face feature could pass visual review
unseen. All 24 `trust_output/*.png` regenerated. Render width 1800→2200 to keep 4 columns
legible. (`tiacad_core/visual/trust_renderer.py`)

#### Trust renderer: composite assemblies decompose into per-component colors

When the final part is a union of multiple components (a printable assembly fused into one
solid), the renderer now walks the operation DAG and draws each additive component in its
own color, with subtracted parts shown as translucent-red voids in the X-Ray panel. Before,
a fused assembly rendered as one flat-colored blob — you could judge its silhouette but not
whether parts were actually connected or correctly placed. Metadata colors are ignored for
decomposition (assembly parts frequently share one color). Activates only for 2+ additive
components; single primitives, finishing ops, patterns, and already-separate multi-part
scenes keep the existing single-render path. Shaded panels are now fully opaque (was 0.97)
so overlapping components read crisply; X-Ray carries see-through duty.

### Fixed - 2026-07-09

#### `awesome_guitar_hanger.yaml` — mounting screw holes now actually pierce the plate

The four screw-hole `difference` cuts subtracted from empty air (shafts floated
9mm above the plate, countersinks landed 20-30mm off its edge) — an axis-mapping
error where the vertical positioning value went into the wrong offset component,
and 1,599 passing tests never noticed because contracts check volume ranges, not
hole presence. Shaft offsets now swap Y/Z so the vertical value follows the plate
face; countersinks retarget from `face_front` to `face_top` with the vertical
value in the offset component that maps to that face's tangent frame. Verified
via `Part.get_bounds()` and volume deltas (589 mm³ for the two through-holes,
412.4 mm³ more for the two countersinks). Full root-cause writeup in
`docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md`. The systemic gap this
exposed — no assertion that a `difference`/`union` actually changes volume — is
still open, tracked as the top item in `docs/developer/MODEL_VALIDATION.md`.

### Added - 2026-04-18

#### AI-assisted debug bundle workflow (`tiacad debug`)

Implements the debug-artifact model proposed in `docs/developer/AI_DEBUG_WORKFLOW.md`:
- `tiacad debug model.yaml --bundle out/` writes `resolved_model.json`, `build_trace.json`,
  `part_summaries.json`, `validation_report.json`, `trust_render_manifest.json`, and
  `final_trust.png` (when trust rendering succeeds)
- `tiacad debug model.yaml --compare PREVIOUS_BUNDLE` adds `compare_report.json`, diffing
  against a prior bundle
- Reusable geometry-summary helpers added in `tiacad_core.testing.geometry_summary`

Still open: richer node-level diffing beyond parts/operations, changed-node summaries,
incremental-rebuild dirty-node integration, automatic render diffs, changed-node trust
renders, model-local `contracts:` + `tiacad verify`, and negative trust scenarios.

### Fixed - 2026-03-17 (session: lightning-mountain-0317)

#### `lego_brick_3x1.yaml` — same 3 coordinate bugs as 2x1 had (3 bodies disconnected)

The 3x1 example was never updated when the 2x1 was fixed in hoyeduwu-0317. Identical bugs:
1. `stud_1`, `chamfer_1`, `post_outer_1`, `post_inner_1` and `_2` variants double-counted
   the linear pattern X offset. Pattern already shifts `_N` by `N×stud_pitch`; the translate
   also added `stud_pitch×N`. Fixed all `_1` and `_2` positioned operations to `unit_size/2` only.
2. Stud Z positions used `brick_height=9.6` (the Y extent) instead of
   `brick_width - 0.1 + stud_height/2`. Studs were floating 1.6mm above the brick top.
3. Post cylinder Z centers used `bottom_thickness` instead of
   `bottom_thickness + connection_tube_height/2`.
After fix: W=24, H=9.6, D=9.6, vol≈1310mm³, watertight. Bounding box now 39.25→24mm in X.

### Added - 2026-03-17 (session: lightning-mountain-0317)

#### 19 new geometric contracts across 8 example files (`test_example_contracts.py`)

New test classes, all assertions derived from first principles (test count 1519 → 1538):
- `TestLegoBrick3x1` (3 tests): bbox W=24/H=9.6/D=9.6; volume ≈1310mm³; 3x1 > 2x1
- `TestV3BracketMount` (3 tests): bbox W=150/H=100/D=60 from params; volume < sum-of-parts
- `TestSimpleGuitarHanger` (3 tests): W=plate_w=100; volume between plate-alone and sum-of-parts
- `TestGuitarHangerNamedPoints` (4 tests): plate and beam dimensions + volumes from YAML params
- `TestWeek5Assembly` (2 tests): gear cylinder W=H=24/D=8; vol = π×12²×8 = 3619.1mm³
- `TestWeek5FrameBasedRotation` (2 tests): W=D=30/H=5; vol = π×15²×5 ≈ 3534.3mm³
- `TestDagTestSimple` (2 tests): stacked boxes bbox 50×50×20; vol = 50,000mm³

### Fixed - 2026-03-17 (session: hoyeduwu-0317)

#### `chamfered_bracket.yaml` — vertical plate was disconnected from base (2 bodies)

Root cause: `vertical_positioned` translate `[0, base_depth, base_thickness]` placed the
vertical plate 74mm past the base plate in Y (confused `base_depth` which is the Z extent,
not Y). Fixed to `[0, base_thickness, 0]` — plates now share the Y=6 face and union correctly.
`test_chamfered_bracket_is_single_component` promoted from xfail → passing.

#### `lego_brick_2x1.yaml` — 6 disconnected bodies (3 separate bugs)

Three coordinate/offset bugs caused studs, chamfers, and one post to float in space:
1. `stud_1`, `chamfer_1`, `post_1` positioned operations double-counted the pattern X offset —
   the linear pattern already shifts `_1` instances by `stud_pitch=8`, but the translate also
   added `unit_size/2 + stud_pitch`. Fixed to `unit_size/2` only.
2. Stud Z positions used `brick_height=9.6` (which maps to Y in box semantics) instead of
   `brick_width=8` (the actual Z extent). Studs were 0.75mm above the brick top. Fixed to
   `brick_width - 0.1 + stud_height/2` for a 0.1mm overlap.
3. Post cylinder Z centers placed at `bottom_thickness` instead of
   `bottom_thickness + connection_tube_height/2`, positioning half the post outside the brick.
Test assertion changed from `components==1` to `watertight=True` — hollow tubes produce
multiple trimesh components but one valid watertight solid. Volume contract updated 988→907mm³
(988 was the erroneous sum of 6 disconnected bodies).

### Added - 2026-03-17 (session: hoyeduwu-0317)

#### 18 new geometric contracts across 8 example files (`test_example_contracts.py`)

New test classes, all assertions derived from first principles:
- `TestChamferedBracket` (3 tests): bounding box W=80/H=66/D=80 from params; volume bounds
- `TestPipeSweepSimple` (2 tests): exact formula π×5²×40=3141.6mm³; full bounding box
- `TestBottleRevolve` (2 tests): W=H=2×radius=20, D=height=30; Pappus theorem volume
- `TestMountingPlateWithBoltCircle` (3 tests): bbox W=D=150/H=8; volume < solid plate
- `TestRoundedMountingPlate` (2 tests): bbox; volume < sharp-edge variant
- `TestAutoRefsCylinderAssembly` (2 tests): shaft bbox W=H=10/D=50; π×5²×50=3927mm³
- `TestAnchorsDemoPlatform` (2 tests): platform bbox 100×100; volume=100,000mm³
- `TestWeek5AlignToFace` (2 tests): rotation preserves volume=6000mm³; depth=10 unchanged

#### Boot sequence: README continuation now proposes likely next work

Updated `templates/CLAUDE.md` boot sequence — for README continuation sessions, TIA now
reasons from the README's "Next Steps" / "Open Items" and asks "Do you want me to continue
working on [specific thing]?" instead of generic "What are we working on?"

### Added - 2026-03-17 (session: rainbow-glow-0317)

#### Partial-angle revolve trust contracts

Two new trust YAMLs + three new test classes covering angle scaling:
- `examples/trust/revolve_180.yaml` — half-cylinder (180°, r=15, L=40): volume = π×15²×40/2
- `examples/trust/revolve_90.yaml` — quarter-cylinder wedge (90°): volume = π×15²×40/4
- `TestTrustRevolve180` (3 tests): volume = half of 360°, length along X, Z diameter
- `TestTrustRevolve90` (3 tests): volume = quarter of 360°, length along X, positive
- `TestRevolveAngleScaling` (3 tests): 180° = half of 360°, 90° = quarter, 90° = half of 180°
All assert from formula — no "snapshot of buggy output" risk.

#### Expanded printability contracts (`test_geometry_validation.py`)

Five new `TestExampleGeometry` tests covering sweep, revolve, and loft examples:
- `test_pipe_sweep_simple_is_valid` — L-pipe sweep: 1 component, watertight, positive volume
- `test_bottle_revolve_is_valid` — bottle revolve: 1 component, watertight, positive volume
- `test_transition_loft_is_valid` — loft: 1 component, watertight, positive volume
- `test_mounting_plate_bolt_circle_watertight` — plate with bolt-holes: watertight + positive
  volume (component count not asserted — CadQuery STL exports inner hole surfaces as
  separate shells, so body_count > 1 is expected for solids with through-holes)
- `test_chamfered_bracket_is_single_component` (xfail) — chamfered_bracket produces 2
  disconnected solids; translate `[0, base_depth, base_thickness]` places vertical plate
  74mm away from base_plate in Y
- `test_lego_brick_2x1_is_single_component` (xfail) — lego brick produces 6 disconnected
  bodies; boolean union fails to merge studs/posts with main body

### Fixed - 2026-03-17 (session: kasola-0317)

#### Revolve axis bug (`tiacad_core/parser/revolve_builder.py`)

`wp.revolve()` was passing axis direction vectors as workplane-local coordinate points.
After `shape.build()` shifts the workplane via `center()`, these coords became wrong,
producing incorrect geometry for all revolve operations. Fix: use `Solid.revolve()`
from `cadquery.occ_impl.shapes` with world-coordinate `cq.Vector` objects, bypassing
the workplane-frame entirely. Result: Z-axis spool now produces correct bbox (50×50×36)
and volume (37,699 mm³) instead of the previously wrong dimensions.

#### Guitar hanger union bug (`examples/awesome_guitar_hanger.yaml`)

`awesome_guitar_hanger.yaml` produced 7 disconnected components instead of 1. Two root causes:

1. **Arm gap**: `left_arm_start` / `right_arm_start` offsets used `arm_length / 2` (Y=40)
   instead of `arm_thickness / 2` (Y=6), placing arm centers 18.9mm away from the beam.
   Fixed to `arm_thickness / 2` → arm and beam now overlap → `structure_assembled` = 1 component.

2. **Grip misalignment**: 4 grip cylinders used world-Y offsets `[0, ±grip_spacing, 0]`
   from `left/right_arm_start`. The arm is tilted 12° around X, so those Y positions
   don't intersect the arm body. Fixed to world-Z offsets `[0, 0, ±grip_spacing]`,
   placing grips along the arm's length where they physically overlap it.

`test_awesome_guitar_hanger_union_fails` (xfail) promoted to `test_awesome_guitar_hanger_is_valid`
in `TestExampleGeometry` (regular passing test). `TestKnownFailures` class removed.

### Added - 2026-03-17 (session: kasola-0317)

#### Revolve X/Y axis trust contracts

Two new trust YAMLs + test classes covering the axes previously untested:
- `examples/trust/revolve_x_axis.yaml`: rectangle in XZ plane → 360° around X → cylinder r=15, h=40
- `examples/trust/revolve_y_axis.yaml`: rectangle in XY plane → 360° around Y → cylinder r=15, h=40

Both assert: correct axis length, equal perpendicular extents (circular cross-section),
volume = π×15²×40 ≈ 28,274 mm³.

#### Cross-validation test class (`TestCrossValidation`)

Three independent code paths producing the same cylinder (r=15, h=40) must agree:
primitive cylinder, revolve-X, revolve-Y. Ensures a regression in one path is caught
by the others, not masked by consistent-but-wrong behavior.

#### Tighter surface operation bounds

- **Sweep**: lower bound tightened from `> one_arm` to `> 1.5 × one_arm` (catches
  one-arm-only builds that previously passed the test)
- **Loft**: replaced extreme-bounds check with ±30% around prismatoid approximation
  (~34,600 mm³), narrowing the acceptable window from 2.3× to 1.6× ratio

**Test suite: 1486 passing, 1 skipped, 0 failing, 0 xfailed** (was 1406 in v3.1.2)

### Added - 2026-03-17 (session: rainbow-ember-0316)

#### Trust Scenario Geometric Contracts (`tiacad_core/tests/test_correctness/test_trust_contracts.py`)

66 new passing tests covering all 20 trust YAMLs in `examples/trust/`. Each trust YAML
documents its own ground truth in comments and description text — these tests translate
that prose into assertions. Coverage:

- **Primitives**: exact bbox + volume for box, cylinder, sphere, cone; revolve symmetry check
- **Assemblies**: per-part dims + volumes + positional assertions (flush contact, centroid
  alignment, symmetry) for stacked_boxes, cylinder_on_plate, side_by_side, three_part_assembly
- **Booleans**: exact volume formulas for subtract (box − hole), union (A+B−overlap),
  intersect (result is 20×20×20 cube)
- **Finishing**: bbox unchanged + material removed for chamfer and fillet
- **Surfaces**: height contract for loft, arm-presence for sweep, containment bounds for hull
- **Patterns**: 5-instance coverage for linear_pattern, volume + footprint for circular_pattern
- **Complex assembly**: plate + standoffs + PCB + screws for pcb_standoff_assembly

Closed the "trust YAMLs have no contracts" gap: the 20 trust files were the most
precisely-documented examples in the codebase but had zero geometric test coverage.
Total suite: 1474 passing tests.

### Added - 2026-03-16 (session: awakened-shrine-0316)

- `tiacad_core/visual/trust_renderer.py` — pyvista-based 4-panel trust renderer (iso + front XZ + top XY + side YZ) with per-part colors, axis indicator, legend; filters consumed intermediate parts automatically
- `scripts/trust_render.py` — CLI: render single file, directory, or `--gallery` (all trust scenarios + HTML gallery)
- `examples/trust/` — 7 curated trust scenarios: box_basic, cylinder_basic, boolean_subtract, stacked_boxes, side_by_side, cylinder_on_plate, three_part_assembly
- `trust_output/` — pre-rendered PNGs + gallery.html

### Fixed - 2026-03-16 (session: awakened-shrine-0316)

- `docs/user/YAML_REFERENCE.md` — box axis comments were inverted (`height`↔`depth`); fixed + added ⚠️ gotcha callout
- `ROADMAP.md` — test count 1382→1405, stdlib list corrected (m4/m5/m6 nuts added), PCB assembly example added
- `docs/developer/TESTING_GUIDE.md` — test count 1244→1405, Option A contracts marked done, Option D trust renderer added

**Key lessons:** `position:` key in part spec is silently ignored; use
`operations: { type: transform, translate: [x,y,z] }`. PBR rendering kills
colors without HDR env; use smooth_shading + specular. Consumed parts
(boolean base/subtract, transform input) must be filtered from renders.

### Added - 2026-03-16 (session: infernal-cyclops-0316)

#### Trust Renderer: Verification Checklist in Legend (`tiacad_core/visual/trust_renderer.py`)

Added "Trust Check" section at the bottom of the legend strip. Reads `doc.metadata.description`
and renders it as word-wrapped text (~32 chars/line). Makes trust renders self-documenting —
human or AI can read the legend to know what to verify in the panels.

#### Trust Renderer: Named Dimension Labels (`tiacad_core/visual/trust_renderer.py`)

Orthographic panel dimension overlays now back-map scene extents to document parameter names.
Instead of `X: 100.0  Z: 8.0`, renders `plate_size: 100.0  plate_thickness: 8.0`. Falls back
to axis letter if no parameter matches within 0.5mm tolerance. Connects rendered geometry
directly to YAML source parameters.

#### Trust Renderer: Part Callout Labels on Iso View (`tiacad_core/visual/trust_renderer.py`)

For assemblies with 2–8 parts, draws part name labels at each part's centroid in the Iso
(shaded) panel. Uses PyVista `add_point_labels()` with white rounded-rect backgrounds for
legibility. Suppressed for single-part models (no value) and 9+ part assemblies (too cluttered).

#### Legend Width Expanded to 250px + `_find_named_dims()` Helper

Legend strip widened from 220 → 250px to accommodate description text and longer parameter names.
`_find_named_dims(sizes, parameters)` helper maps scene X/Y/Z extents to parameter names with
axis-hint tie-breaking (prefers "width" for X, "height" for Z, "depth" for Y).

#### Trust YAML Descriptions: 6 Scenarios Enriched (`examples/trust/`)

Six trust scenarios with short one-liner descriptions upgraded to full verification checklists:
`boolean_subtract`, `cylinder_basic`, `cylinder_on_plate`, `side_by_side`, `stacked_boxes`,
`three_part_assembly`. Each now has explicit "Trust check: view = expected shape" statements.
All 20 trust PNGs regenerated.

### Fixed - 2026-03-16 (session: infernal-cyclops-0316)

#### Trust Renderer: Feature Edge Angle 25° → 40° (`tiacad_core/visual/trust_renderer.py`)

OCCT seam edges on revolved solids produce a dihedral discontinuity at the 0°/360° boundary
that spikes above 25°, appearing as an artifact line. Raising `_FEATURE_ANGLE` to 40° skips
the seam while retaining all real geometric boundaries (box edges, cylinder rims, step transitions).

#### `simple_guitar_hanger.yaml` — Disconnected Bodies (`examples/simple_guitar_hanger.yaml`)

The guitar hanger union produced 3 disconnected bodies instead of 1. Root cause: the cradle
arms were positioned at Y≈44.7 (after 10° tilt) but the plate front face was only at Y=40,
leaving a 4.7mm gap that no-overlapping-geometry boolean union preserved as separate shells.
Fix: increased `plate_h` from 80 → 100, plate front face now at Y=50, arms now physically
penetrate the plate. Test `test_simple_guitar_hanger_is_valid` now passes.
**Tests: 1408 passed (was 1407 + 1 failing), 0 failed.**

### Fixed - 2026-03-16 (session: lightning-mage-0316)

#### `position:` Key Now Raises a Clear Error (`tiacad_core/parser/parts_builder.py`)

Parts with a `position:` key silently ignored it. Now raises `PartsBuilderError` with a
message directing users to `origin: [x, y, z]` (build-time placement) or
`operations: transform` (post-build placement). Test added.

#### YAML_REFERENCE.md — Stale "Finishing modifies in-place" Note Corrected

The finishing section stated "Finishing operations modify parts in-place!" which was
incorrect since the x-ray-beta-0316 fix. Updated to accurately describe that finishing
creates a new named part registered under the operation name.

### Added - 2026-03-16 (session: lightning-mage-0316)

#### Two More Blocked Examples Re-enabled with Finishing Operations

`rounded_mounting_plate.yaml` and `v3_bracket_mount.yaml` both had finishing ops
commented out since the original bug. Now fully enabled:
- `rounded_mounting_plate.yaml` — `plate_finished` fillet (r=2mm, direction: Z)
- `v3_bracket_mount.yaml` — `assembly_finished` fillet (r=1.5mm, direction: Z)
Both have `export: default_part:` sections added.

#### Trust Scenario: Fillet Basic (`examples/trust/fillet_basic.yaml`)

Box with all 12 edges filleted (r=3mm). Trust check: all corners softened, no
sharp 90° angles anywhere. Rendered to `trust_output/fillet_basic.png`.

### Fixed - 2026-03-16 (session: lightning-mage-0316) — examples export sweep

All 14 examples that lacked `export:` sections now have them. This fixes the `exports:`
(plural) schema error in 3 files (`text_engraved`, `text_label`, `text_simple`) — the
plural key is silently ignored by the parser; only `export:` (singular) is read.

| File | default_part | Notes |
|---|---|---|
| `dag_test_simple.yaml` | `stacked` | |
| `formats_demo.yaml` | `demo_box_filleted` | |
| `text_engraved.yaml` | `final_sign` | Fixed: `exports:` → `export:` |
| `text_label.yaml` | `final_label` | Fixed: `exports:` → `export:` |
| `text_simple.yaml` | `text_3d` | Fixed: `exports:` → `export:` |
| `text_operation_emboss_simple.yaml` | `product_label` | |
| `text_operation_multi_face.yaml` | `right_label` | |
| `text_operation_product_label.yaml` | `serial_text` | |
| `color_demo.yaml` | `custom` | |
| `multi_material_demo.yaml` | `custom_knob` | |
| `simple_guitar_hanger.yaml` | `right_arm` | |
| `week5_align_to_face.yaml` | `bracket_rotated` | |
| `week5_assembly.yaml` | `rotated_gear` | |
| `week5_frame_based_rotation.yaml` | `gear_multi_rotation` | |

### Added - 2026-03-16 (session: lightning-mage-0316) — trust scenarios

#### Trust Scenario: Chamfer Basic (`examples/trust/chamfer_basic.yaml`)

Box with all 12 edges chamfered (length=3mm). Trust check: flat 45° bevels everywhere,
octagonal perimeter in top view. Rendered to `trust_output/chamfer_basic.png`.

Trust gallery regenerated to include both `fillet_basic` and `chamfer_basic`.

### Fixed - 2026-03-16 (session: x-ray-beta-0316)

#### Finishing Builder — Fillet/Chamfer Now Create Named Result Parts (`tiacad_core/parser/finishing_builder.py`)

Previously `finishing` operations (fillet/chamfer) modified the input part
in-place and never registered the result under the operation name. Any YAML
with `export: default_part: <finishing-op-name>` would fail at export (part
not found). Root cause: all other builders use `registry.add(Part(name=name,
...))` but finishing builder only mutated `part.geometry`.

- **Fix**: replace in-place mutation with `registry.add(Part(name=name, ...))` in
  both `_execute_fillet` and `_execute_chamfer`
- **Re-enabled**: `examples/chamfered_bracket.yaml` and `examples/formats_demo.yaml`
  had finishing ops commented out with "temporarily disabled" — now active
- **Tests updated**: 22 finishing tests rewritten to check the result part, not
  the input (which is now correctly left unchanged)

### Added - 2026-03-16 (session: x-ray-beta-0316)

#### Trust Scenario: PCB Standoff Assembly (`examples/trust/pcb_standoff_assembly.yaml`)

Richest multi-component trust scenario. Exercises stdlib imports, transforms,
and multi-part rendering: base plate → 4 M3 standoffs at corners → PCB board →
4 M3 screws. 26 parts total. Key visual tells: 3-layer Z-stack in Front/Side
views, 4 corner circles + two nested rectangles in Top view.

#### Trust Renderer: Smooth Mesh to Reduce Tessellation Stripes (`tiacad_core/visual/trust_renderer.py`)

Added `mesh.smooth(n_iter=20, relaxation_factor=0.1)` after STL import in
`_geometry_to_pyvista()`. Eliminates visible tessellation stripes on curved
surfaces (cylinders, spheres, swept pipes) without changing geometry.

### Fixed - 2026-03-16 (session: crystalline-dawn-0316)

#### Sweep Multi-Segment Bug (`tiacad_core/parser/sweep_builder.py`)

`sweep(..., multisection=True)` was silently discarding all path segments after
the first. All multi-point sweeps (pipes, rails) were producing a single straight
cylinder regardless of path. Fix: removed `multisection=True`; added spline
fallback for non-planar paths with sharp 3D corners that OCCT cannot sweep as a
polyline. Visual regression reference for `pipe_sweep` updated accordingly.
Tests: 1406 pass, 0 fail.

### Added - 2026-03-16 (session: crystalline-dawn-0316)

#### 10 New Trust Scenarios (`examples/trust/`)

Extended trust renderer coverage from 7 scenarios to 17, covering features
that had zero visual verification:

| File | Feature verified |
|---|---|
| `sphere_basic.yaml` | Sphere primitive — circle in all 4 views |
| `cone_basic.yaml` | Cone — triangle front/side, circle top |
| `boolean_union.yaml` | Union op — plus/cross shape in top view |
| `boolean_intersect.yaml` | Intersection op — small cube from two crossing slabs |
| `linear_pattern.yaml` | 5 colored boxes in a row (distinct colors per instance) |
| `circular_pattern.yaml` | Flat plate with 6-hole bolt circle + center hole |
| `revolve_basic.yaml` | Spool profile — I-beam in side view confirms revolve |
| `sweep_basic.yaml` | L-pipe — 90° bend visible in front (XZ) view |
| `hull_spheres.yaml` | Rounded-triangle blob from 3 positioned spheres |
| `loft_rect_to_circle.yaml` | Trapezoid front, circle top, square bottom |

Gallery: `trust_output/gallery.html` (17 scenarios, all 17 pass).

Discovered along the way: `origin:` as list `[x,y,z]` on parts is valid
positioning (not the same as the silently-ignored `position:` key).
Expression parameters `${expr}` cannot appear inside YAML flow sequences `[...]`;
use block sequences for any point that involves a parameter expression.

### Added - 2026-03-16 (session: turbulent-mist-0316)

#### M4/M5/M6 Hex Nuts (ISO 4032)

Three new stdlib components completing the nut set alongside `m3_nut`:
- `tiacad_core/stdlib/hardware/m4_nut.yaml` — 8.08mm dia, 3.2mm thick, 4mm bore
- `tiacad_core/stdlib/hardware/m5_nut.yaml` — 9.24mm dia, 4.7mm thick, 5mm bore
- `tiacad_core/stdlib/hardware/m6_nut.yaml` — 11.55mm dia, 5.2mm thick, 6mm bore

All use `polygon` primitive (6 sides) + boolean difference for bore. 15 Tier 2
contracts in `TestM4NutContracts`, `TestM5NutContracts`, `TestM6NutContracts`.

#### PCB Standoff Assembly Example

`examples/pcb_standoff_assembly.yaml` — first properly-positioned multi-component
assembly example. Demonstrates 4-corner PCB mount using stdlib imports:
- Base plate: 100×80×5mm (thickness along Z for natural standoff alignment)
- 4× M3 standoffs (10mm) from stdlib, positioned at ±(38mm, 30mm)
- PCB board: 80×60×2mm, resting on standoff tops at Z=12.5mm
- 4× M3 screws (16mm) passing through plate + standoff

All 34 parts build correctly. 7 Tier 2 geometric contracts in
`TestPcbStandoffAssembly`. Visual reference generated.

#### Documentation Accuracy Pass

All planning/reference docs updated to reflect v3.1 completion (both docs commits):
- `ROADMAP.md`: Component System + DAG marked done, Constraint Solver as Q4 2026 next
- `KNOWN_LIMITATIONS.md`: removed 3 resolved limitations, added 2 real current ones
- `PROJECT.md`: test counts, completed milestones, next milestone
- `docs/developer/CLI.md`: added watch/check/audit/validate-geometry command docs
- `docs/user/YAML_REFERENCE.md`: fixed import syntax (path:/as: format), added polygon
  primitive docs, added full imports section with stdlib/GitHub/local examples
- `docs/DOCUMENTATION_MAP.md`: added DAG_INCREMENTAL_REBUILD.md entry

**Suite: 1382 → 1405 pass (+23)**

### Added - 2026-03-16 (session: ninja-xenarch-0316)

#### GitHub + Stdlib URI Schemes for Component Imports

`component_importer.py` now supports two new URI schemes alongside local `path:`:

- `tiacad://std/hardware/m3_screw` — resolves to `tiacad_core/stdlib/hardware/*.yaml` (bundled)
- `github:user/repo/path/to/file.yaml` — fetches from `raw.githubusercontent.com/user/repo/main/...`, cached to `~/.tiacad/cache/github/`

New `_resolve_path()` routes all three schemes. 18 new tests (TestResolvePath, TestStdlibImports, TestGithubImports — GitHub mocked, no network required).

#### `primitive: polygon` — Regular N-sided Extruded Prism

New primitive in `parts_builder.py`:
```yaml
primitive: polygon
parameters:
  sides: 6          # number of sides (≥ 3)
  diameter: 8.0     # circumscribed circle diameter
  height: 4.0       # extrusion height
  circumscribed: true  # optional, default true
```
Backed by CadQuery `Workplane.polygon(nSides, diameter).extrude(height)`. 13 new tests in `TestPolygon`.

#### M3 Hex Nut Stdlib Component

`tiacad_core/stdlib/hardware/m3_nut.yaml` — ISO 4032 M3 hex nut using polygon + boolean difference:
- Circumscribed diameter: 6.35mm (5.5mm AF / cos30°)
- Thickness: 2.4mm, bore radius: 1.5mm
- 5 Tier 2 geometric contracts in `TestM3NutContracts`

#### Tier 2 Contracts — Hardware Assembly Demo

12 new contracts in `TestHardwareAssemblyDemo` locking shaft diameters (M3–M6), washer OD/volume, standoff height, plate dimensions, boolean subtract correctness.

**Suite: 1330 → 1378 pass (+48)**

### Added - 2026-03-16 (session: enchanted-hydra-0316)

#### Tier 2 Geometric Contracts — Component Import Demo

9 new tests in `test_correctness/test_example_contracts.py::TestComponentImportDemo`
that independently verify geometry from parameter math, not snapshots:

- Panel: 200×3×150mm, vol=90,000mm³
- `bracket.base`: 60×35×5mm, vol=10,500mm³
- `bracket.flange`: 60×5×50mm, vol=15,000mm³
- `screw_short.shaft` height=12mm, `screw_long.shaft` height=25mm
- Parameter override isolation: two imports of same file produce independent geometry

**Axis convention documented:** `get_dimensions` returns X/Y/Z bounding box extents.
CadQuery box YAML `depth` → Y axis → `dims["height"]`; YAML `height` → Z → `dims["depth"]`.

#### `tiacad watch --export <path>` flag

Auto-export final part to STL/3MF/STEP on each successful rebuild:

```
tiacad watch examples/bracket.yaml --export /tmp/bracket.stl
[14:32:07]  changed   ✓   112ms  1 rebuilt, 3 cached  → bracket.stl
```

- `WatchBuildResult.exported_path` field
- `FileWatcher(export_path=...)` + `_export()` method handles all 3 formats
- Validates extension before starting the watch loop

#### Component Standard Library (`examples/components/`)

Five new reusable hardware components:

| File | Spec | Key parameters |
|---|---|---|
| `m4_screw.yaml` | M4 pan head (DIN 7985) | shaft_radius=2.0, head_radius=4.0 |
| `m5_screw.yaml` | M5 pan head (DIN 7985) | shaft_radius=2.5, head_radius=5.0 |
| `m6_bolt.yaml` | M6 hex bolt (DIN 931) | shaft_radius=3.0, head_radius=5.5 |
| `m3_washer.yaml` | DIN 125 flat washer | OD=7mm, ID=3.2mm via boolean diff |
| `m3_standoff.yaml` | Cylindrical standoff | M3 bore via boolean diff |

New demo: `examples/hardware_assembly_demo.yaml` — 25-part assembly importing all 6 hardware components. Added to Tier 1 BUILDABLE_EXAMPLES list.

**Test baseline:** 1330 pass, 0 fail (up from 1319, +11 new tests).

### Added - 2026-03-15 (session: drifting-expedition-0315)

#### Phase 4 — Watch Mode (`tiacad watch <file>`)

Capstone of the DAG incremental rebuild arc. Watches a YAML file for saves
and rebuilds immediately, reusing cached geometry via IncrementalBuilder.

**`tiacad watch examples/bracket.yaml`** — live rebuild loop:
```
[14:32:01] initial     ✓  1842ms  1 rebuilt, 0 cached
[14:32:07] changed     ✓   112ms  1 rebuilt, 3 cached
```

- `tiacad_core/watcher.py` — `FileWatcher` class with watchdog + 300ms debounce
- Handles atomic saves (editor write-rename patterns)
- Connects directly to `IncrementalBuilder` (not parser shortcut) — real cache hits
- 11 tests: 8 unit (mocked, ~1s), 3 integration (real builds, marked `slow`)

#### Bug fix — lib3mf locale corruption

`lib3mf.WriteToFile()` calls `setlocale(LC_ALL, "C")` internally and never
restores it, corrupting Python file I/O encoding to ASCII for all subsequent
code in the same process. Fixed with save/restore in `threemf_exporter.py`.

This was causing `test_namespace_collision_raises` to fail in full suite runs
(the test writes a YAML comment containing `→` which ASCII can't encode).

**Test baseline:** 1323 pass, 0 fail (was 1 ordering failure). Full suite clean.

#### Visual regression references

45 reference PNGs committed to `tiacad_core/visual_references/`, closing the
"6 missing visual regression tests" item. Visual suite now: 81 pass, 2 skip
(dag_test_cycle and pipe_sweep — known OCCT limitations).

### Added - 2026-03-15 (session: sutegaku-0315)

#### Correctness Infrastructure — `tiacad check`, `tiacad audit`, geometric contracts

**Problem:** TiaCAD had 1244 tests but none verified that example files produce correct
geometry. Visual regression proved "looks the same as before" not "looks right."

**`tiacad check <file>`** — new CLI command (no file output):
- Builds all parts, reports W×H×D and volume for each
- Highlights final part (★ = last operation result), shows parameters inline
- Fast dev loop: "did my boolean subtract actually remove material?"

**`tiacad audit <files...>`** — batch across many files, summary table:
- 44 OK, 1 WARN (pipe_sweep_simple zero volume), 4 FAIL on all 49 examples
- Identified 1 real bug: component_import_demo uses old translate dict syntax

**`test_example_contracts.py`** — 64 geometric contract tests:
- Tier 1: all 44 buildable examples must have positive volume (parametrized)
- Tier 2: dimensional contracts for 8 key examples (independently verifiable)
  - `bracket_with_hole`: hole subtract confirmed, exact vol ~9,214
  - `auto_references_box_stack`: each of 3 boxes checked individually
  - `lego_brick`: 3×1 > 2×1 volume relationship asserted
  - `text_engraved`: engraving confirmed (volume < uncut base plate)

**Test baseline:** 1308 pass (was 1244, +64). Pre-existing failure unchanged.

### Added - 2026-03-15 (session: metallic-shade-0315)

#### DAG Incremental Rebuild — Phases 0–3

Full incremental rebuild infrastructure. On repeated builds, only nodes downstream
of changed parameters/parts are rebuilt; everything else is restored from cache.

**Phase 0 — GraphBuilder fix:** Operations (extrude/revolve/sweep) now track their
`sketch:` dependency. Was silently missing, meaning sketch changes didn't invalidate
downstream operations.

**Phase 1 — `InvalidationTracker`** (`tiacad_core/dag/invalidation_tracker.py`):
- `compute_dirty_set(new_graph)` → changed nodes + all transitive dependents
- `compute_deleted_set()` → nodes to evict from cache
- `compute_full_report()` → hit_rate + added/deleted/modified breakdown

**Phase 2 — `BuildCache`** (`tiacad_core/dag/build_cache.py`):
- In-memory cache keyed by `(node_id, content_hash)` — stale results never returned
- `put/get/evict/evict_many/has/get_stats()`

**Phase 3 — `IncrementalBuilder`** (`tiacad_core/dag/incremental_builder.py`):
- `build(yaml_data, parts_spec, ops_spec, registry, parts_builder, ops_builder, old_state)`
- Full build when `old_state=None`; incremental otherwise
- `IncrementalState(graph, cache)` — caller preserves and passes back next call
- `BuildStats`: rebuilt/cached counts, hit_rate, total_ms
- Operations executed in topological order; cached results restored before downstream ops run

**Test baseline:** 101 DAG tests (was 53), +48 new. Full suite: 1244 pass.

**Still to build:** Phase 4 — Watch Mode (`tiacad_core/watcher.py`, `watchdog` dependency)

#### Testing Docs

Rewrote `docs/developer/TESTING_GUIDE.md` and `TESTING_QUICK_REFERENCE.md`:
- Accurate test counts and category breakdown
- New **Correctness Gap** section: what tests verify vs what's missing, "snapshot of a bug" risk
- Three concrete next-step options for improving geometric correctness coverage
- Removed broken links to files that don't exist

### Added - 2026-03-15 (session: astral-warrior-0315)

#### Component/Module Import System (`tiacad_core/parser/component_importer.py`)

**New `imports:` section in TiaCAD YAML** — reuse parts from other YAML files:

```yaml
imports:
  - path: ./components/m3_screw.yaml
    as: screw
    parameters:
      length: 20          # override component defaults

  - path: ./components/bracket.yaml
    as: bracket
```

Imported parts appear as `{namespace}.{part_name}` (e.g. `screw.shaft`, `bracket.base`)
and are available for use in any `operations:` section of the importing file.

**Features:**
- Local file imports with relative path resolution
- Optional parameter overrides per import (merged over component defaults)
- Namespace prefix required (`as:`) — prevents name collisions
- Circular import detection (raises `ComponentImportError` with full chain)
- Nested imports: B imports C, A imports B → `b_comp.c_comp.part` available in A
- Designs with only imports (no local `parts:`) are valid
- Same component importable twice with different namespaces and parameters

**New files:**
- `tiacad_core/parser/component_importer.py` — `ComponentImporter` class
- `tiacad_core/tests/test_parser/test_component_import.py` — 20 tests
- `examples/components/m3_screw.yaml` — reusable M3 screw component
- `examples/components/mounting_bracket.yaml` — reusable L-bracket component
- `examples/component_import_demo.yaml` — demo of import composition

**Tests:** 20 new tests covering basic import, parameter overrides, multiple imports,
nested imports, error cases (missing file, missing fields, circular imports, namespace collisions)

---

### Fixed - 2026-03-15 (session: ruby-shine-0315)

#### Test Health: 1132 → 1177 passing (+45 tests, 47 → 2 skipped)

**`TiaCADDocument.get_assembly()` added** (`tiacad_core/parser/tiacad_parser.py`)
- 47 visual regression tests were silently skipping due to missing method
- Same priority logic as `export_stl`: export_config default → last operation → first part
- 45 tests now pass; 2 remain skipped (dag_test_cycle.yaml parse error, pipe_sweep.yaml OCCT limitation)

**Visual regression baselines generated**
- 45 reference images created in `tiacad_core/tests/visual_references/`
- All example YAML files now have rendering baselines

### Changed - 2026-03-15 (session: ruby-shine-0315)

#### Code Quality

**`spatial_resolver._resolve_dict` refactored** (`tiacad_core/spatial_resolver.py`)
- Decomposed 157-line, complexity-24 dispatch method into 4 focused methods:
  `_resolve_point`, `_resolve_face_ref`, `_resolve_edge_ref`, `_resolve_axis`
- `_resolve_dict` is now a 12-line dispatch table

**`PatternBuilder` deduplicated** (`tiacad_core/parser/pattern_builder.py`)
- Extracted shared helpers: `_require()`, `_get_input_part()`, `_make_and_register_part()`
- `_execute_linear`: 108L → 43L | `_execute_circular`: 159L → 67L | `_execute_grid`: 151L → 25L
- Moved 3 inline `from .metadata_utils import` to module-level import

**Unused imports removed** (13 imports across 10 files)
- `testing/visual_regression.py`: `hashlib`, `json`, `matplotlib.figure.Figure`
- `testing/orientation.py`, `testing/measurements.py`: `SpatialRef` (docstring-only)
- `testing/dimensions.py`: `math` (docstring-only)
- Test files: `pytest`, `numpy`, `assert_array_almost_equal`, `measure_distance`

---

## [3.1.3] - 2026-02-15

### Documentation - Major Consolidation

**Established Single Sources of Truth:**
- **ROADMAP.md** (NEW) - Clear, honest assessment of what's next (maintenance mode, component system vs DAG under consideration)
- **KNOWN_LIMITATIONS.md** (NEW) - Accurate v3.1.2 limitations with workarounds (not outdated v0.3.0 state)
- **README.md** - Updated test counts (1125), coverage (92%), pass rate (94.4%), removed outdated "Known Limitations" section
- **PROJECT.md** - Fixed dates (2026-02-15), current focus (maintenance mode), test statistics

**Fixed Documentation Contradictions:**
- Test count consistency: All docs now agree on 1125 tests (was 806/1080/1025 across different docs)
- Coverage consistency: 92% everywhere (was 87%/92% mixed)
- Pass rate honesty: 94.4% with 17 known failures being fixed (was claiming 100%)
- Version clarity: v3.1.2 + 19 maintenance commits (was ambiguous)

**Archive Cleanup:**
- Added clear disclaimers to archived docs (CURRENT_STATUS.md, TIACAD_EVOLUTION_ROADMAP.md)
- Created DOCUMENTATION_CONSOLIDATION_PLAN.md as reference

**Impact:** Users can now find accurate, current information without contradictions or outdated plans.

---

### Fixed - 2026-02-15

#### Examples API Compatibility (21 examples fixed, 50% → 95% pass rate)

**Auto-references examples** (4 fixed):
- Updated export format from deprecated list syntax to current dict syntax
- Examples: auto_references_{box_stack, cylinder_assembly, rotation, with_offsets}.yaml
- Now showcase auto-generated anchors feature correctly

**LEGO brick examples** (2 fixed):
- Updated cone primitive: `radius_bottom`/`radius_top` → `radius1`/`radius2`
- Updated pattern spacing: scalar + `direction: X` → vector `spacing: [dx, dy, dz]`
- Examples: lego_brick_2x1.yaml, lego_brick_3x1.yaml
- Created fix_pattern_api.py tool for automated migration

**Week5 examples** (2 fixed):
- Updated translate format: removed deprecated `offset:` wrapper for direct offsets
- Examples: week5_assembly.yaml, week5_frame_based_rotation.yaml
- Note: `offset:` still valid when used with `to:` parameter

**Multi-material example** (1 fixed):
- Updated pattern spacing API (same as LEGO bricks)
- Example: multi_material_enclosure.yaml

**Build artifacts**:
- Added *.3mf to .gitignore (generated output files)

**Result**: Examples now at 95.7% pass rate (44/46), up from 50% (23/46)

**Known limitations documented**:
- pipe_sweep.yaml - OCCT boolean limitation (sweep + cut operations on sharp corners)
  - Not a TiaCAD bug - fundamental OCCT constraint
  - Workaround documented: Use pipe_sweep_simple.yaml or shell operations

---

### Infrastructure - 2026-02-15

#### Development Environment Verification
- **Dependencies validated** - CadQuery 2.7.0, pytest, all core dependencies installed
- **Test suite verified** - 1125 total tests (1062 passing, 45 skipped, 17 failing, 1 xfailed)
- **Test count updated** - Documentation now reflects actual 1125 tests vs outdated 896/1080 counts
- **Geometry validation confirmed** - Nov 2025 work successfully integrated (test_geometry_validation.py with 8 tests)

#### Known Issues Identified
- **Hull builder tests** (11 failures) - CadQuery 2.7.0 STL import compatibility issue in `cq.importers.importShape()`
  - Impact: Convex hull operations fail with "Unsupported import type: 'STL'"
  - Workaround needed: Alternative STL import method or CadQuery version adjustment
- **Visual regression tests** (6 failures) - Missing reference images in `visual_references/` directory
  - Impact: Visual regression tests cannot run without baseline images
  - Fix: Generate reference images with `update_references=True` flag
  - Note: Empty directory exists, needs one-time population

#### Documentation Updates
- **PROJECT.md** - Updated from v3.0 (896 tests) to v3.1.2 (1125 tests)
- **README.md** - Updated test count from 1080+ to accurate 1125
- **Version consistency** - All documentation now references v3.1.2 as current version

---

## [3.1.2] - 2025-12-02

### Fixed - CI/Testing Infrastructure & Bug Fixes

#### GitHub Actions & CI
- **test_renderer.py** - Added `@pytest.mark.visual` to all visualization test classes
  - Properly excludes 63 rendering tests from headless CI
  - Prevents VTK cleanup crashes in GitHub Actions
  - Main workflow now runs 1025 tests successfully in ~67 seconds
  - Visual tests run separately in dedicated workflow

- **.github/workflows/** - Multiple CI workflow improvements
  - Exclude visual tests from main workflow (`-m "not visual"`)
  - Updated libgl1 dependencies for headless rendering
  - Simplified test workflow configuration
  - All workflows now passing ✅

#### Bug Fixes
- **tiacad_core/parser/__init__.py** - Fixed PartRegistry import path in `export_3mf()`
  - Corrected from incorrect import location
  - 3MF export now works correctly

- **tiacad_core/tests/test_visualization/test_renderer.py** - Improved 3MF test robustness
  - Added lib3mf availability detection
  - Skip 3MF tests gracefully if lib3mf not installed
  - Clearer test output for missing dependencies

- **tiacad_core/tests/test_spatial_resolver.py** - Fixed mock part positioning
  - Set `current_position` on mock parts in tests
  - Enables accurate origin tracking tests
  - Aligns with spatial resolver improvements

### Added - Documentation & Project Infrastructure

#### Documentation Improvements
- **docs/DOCUMENTATION_MAP.md** - Complete navigation guide (167 lines)
  - Task-oriented organization ("I want to...")
  - Clear paths for learning, contributing, understanding architecture
  - Quick reference for all 28 documentation files
  - Documentation statistics and FAQ

- **docs/archive/ARCHIVE_SUMMARY.md** - Archive navigation (100 lines)
  - Context for historical documents
  - Pointers to current documentation
  - Explanation of archive purpose

- **docs/CGA_V5_FUTURE_VISION.md** - Renamed from `CGA_V5_ARCHITECTURE_SPEC.md`
  - Added prominent "FUTURE VISION" disclaimer
  - Clarifies this is aspirational v5.0+ content
  - Prevents confusion with current v3.1 architecture

- **docs/archive/** - Added archive disclaimers to 5 historical documents
  - Clear "ARCHIVED DOCUMENT" warnings
  - Links to current documentation
  - Preserves historical context without confusion

- **README.md, docs/user/TUTORIAL.md** - Updated test counts
  - Corrected to current 1025 tests passing
  - Updated last modified dates

#### Licensing & Packaging
- **LICENSE** - Added Apache 2.0 license (full text)
  - Copyright: Semantic Infrastructure Lab Contributors
  - Aligns with SIL ecosystem unified licensing standard
  - Patent protection for contributors
  - Clear contributor license terms

- **README.md** - Updated license section
  - Changed from "TBD" to Apache 2.0
  - Added copyright attribution

- **pyproject.toml** - Added Python packaging configuration
  - Project metadata (name, version, description, authors)
  - Dependencies from requirements.txt
  - CLI entry point: `tiacad` command
  - Development dependencies (pytest, black, mypy)
  - Tool configurations (black, pytest, coverage)
  - PyPI classifiers and keywords
  - Ready for PyPI distribution

### Changed - Version Consistency
- **tiacad_core/__init__.py** - Version 3.1.1 → 3.1.2
- **pyproject.toml** - Version 3.1.1 → 3.1.2
- All versions consistent across codebase

---

## [3.1.1] - 2025-11-16

### Added - Code Feature Improvements

#### Backend Enhancements
- **tiacad_core/geometry/base.py** - Added `create_cone()` abstract method to GeometryBackend interface
  - Standardized cone/frustum creation across backends
  - Support for both true cones (radius2=0) and frustums
  - Parameters: radius1 (base), radius2 (top), height

- **tiacad_core/geometry/mock_backend.py** - Implemented `create_cone()` for MockBackend
  - Fast mock cone creation for unit testing
  - Automatic bounds calculation for cone geometry
  - Face selection support (top/bottom faces with normals)
  - Enables testing of cone-based designs without CadQuery overhead

- **tiacad_core/geometry/cadquery_backend.py** - Implemented `create_cone()` for CadQueryBackend
  - Uses loft between two circles for cone geometry
  - Handles true cones (pointed top) and frustums (truncated)
  - Automatically centers cone vertically for consistent origin

#### Spatial Reference Improvements
- **tiacad_core/spatial_resolver.py** - Fixed part position tracking for origin references
  - Now uses `part.current_position` instead of hardcoded [0,0,0]
  - Enables accurate origin tracking after transforms
  - Supports dynamic part positioning in assemblies

#### Loft Operation Enhancements
- **tiacad_core/parser/loft_builder.py** - Added full support for XZ and YZ base planes
  - Previously only supported XY plane lofts
  - Now supports all three orthogonal planes (XY, XZ, YZ)
  - Automatic offset direction calculation based on plane normal
  - Proper in-plane coordinate mapping for each orientation
  - Enables vertical and side-facing loft operations

#### Test Coverage
- **tiacad_core/tests/test_auto_references.py** - Added comprehensive cone auto-reference tests
  - 6 new test cases for cone primitives
  - Tests for cone.center, cone.origin, cone.face_top, cone.face_bottom
  - Tests for cone.axis_x, cone.axis_z references
  - Validates normal vectors and positioning
  - Completes auto-reference testing for all primitive types

#### Benefits
- Complete cone primitive support across all backends
- More accurate part positioning with origin tracking
- Expanded loft capabilities for complex geometries
- Full test coverage for all primitive auto-references
- Foundation for Phase 3 spatial enhancements

### Added - v3.1 Phase 2: Visual Regression Testing (2025-11-14)

#### Visual Regression Testing Framework
- **tiacad_core/testing/visual_regression.py** - Complete visual testing framework (NEW)
  - `VisualRegressionTester` class for automated visual regression testing
  - `RenderConfig` for configurable rendering (resolution, camera, background)
  - `VisualDiffResult` dataclass with comprehensive comparison metrics
  - `pytest_visual_compare()` helper for easy pytest integration
  - PNG/SVG export support using CadQuery + trimesh + matplotlib
  - Pixel-diff comparison with configurable thresholds
  - Automatic diff image generation with enhanced visibility
  - HTML report generation with side-by-side comparisons
  - Update reference mode for creating/updating baseline images

#### Comprehensive Test Coverage
- **tiacad_core/tests/test_visual_regression.py** - Full test harness (NEW)
  - Parametrized tests for all 44 example YAML files
  - Core operation tests (box, cylinder, sphere, booleans, fillets, chamfers)
  - Automatic test skipping for unparseable files
  - Configurable thresholds (default: 1% pixel difference)
  - Environment variable support: `UPDATE_VISUAL_REFERENCES=1` to update baselines
  - Detailed failure messages with metrics and file paths

#### CI/CD Integration
- **.github/workflows/visual-regression.yml** - Automated visual testing workflow (NEW)
  - Runs on all pushes and pull requests
  - Headless rendering with xvfb for Ubuntu CI
  - Automatic reference image generation on first run
  - Artifact uploads for test outputs, diffs, and reports
  - Matrix testing across Python 3.10, 3.11, 3.12
  - Coverage reporting via Codecov

- **.github/workflows/tests.yml** - Main test workflow (NEW)
  - Separate jobs for unit, integration, parser, and correctness tests
  - Parallel test execution with pytest-xdist
  - Comprehensive coverage reporting
  - Multi-Python version support

#### Image Comparison Metrics
- **Pixel-diff percentage**: Count of differing pixels
- **RMS difference**: Root mean square color difference
- **Mean difference**: Average color difference across all pixels
- **Max pixel difference**: Maximum single-pixel color difference (0-255)
- **Configurable thresholds**: Per-test tolerance for acceptable differences

#### Dependencies & Requirements
- Added **Pillow >= 10.0.0** for image processing
- Added **pytest-xdist >= 3.0.0** for parallel test execution
- Uses existing **trimesh**, **matplotlib**, and **pyvista** for 3D rendering

#### Benefits
- Catch visual regressions automatically in CI/CD
- Reference images for all 40+ example assemblies
- Detailed diff reports when changes occur
- Easy baseline updates with environment variable
- Fast execution with parallel pytest
- Clear visual feedback with diff images

### Added - Software Issues Documentation (2025-11-14)

#### Known Limitations & Improvement Plans
- **docs/KNOWN_ISSUES.md** - Comprehensive documentation of technical limitations (NEW)
  - Current limitations: CadQuery coupling, PointResolver limitations, no DAG, no constraints
  - Workarounds & best practices for each limitation
  - Complete improvement roadmap (Phases 3-5, 40-50 weeks total)
  - Explicitly rejected approaches (persistent JSON, units system, multiple backends)
  - Minor technical debt tracking
  - Clear timeline to constraint-based CAD
- **README.md updates**:
  - Added "Known Limitations & Future Roadmap" section
  - Clear summary of 4 current limitations with workarounds and fixes
  - Linked to docs/KNOWN_ISSUES.md for detailed information
  - Added KNOWN_ISSUES.md to Project Planning documentation section
- **Purpose**: Transparent communication of architectural constraints and strategic plans
- **Impact**: Users understand current capabilities, workarounds, and future direction

### Added - Phase 2 Improvements (2025-11-14)

#### Visual Diagrams (Phase 2.1)
- **docs/diagrams/reference-based-vs-hierarchical.md** - Visual comparison of TiaCAD vs traditional CAD
  - Side-by-side Mermaid diagrams showing assembly structure differences
  - Comparison table of key aspects
  - Mental model explanation
- **docs/diagrams/auto-reference-visualization.md** - Complete visual guide to auto-generated anchors
  - Shows all anchor types (center, origin, faces, axes)
  - Organized by category with color coding
  - Usage examples and 3D visualization concept
- **docs/diagrams/local-frame-offsets.md** - How offsets work in local coordinate frames
  - World coordinates vs local frames comparison
  - Visual examples with tilted surfaces
  - Code comparison showing benefits
- **docs/diagrams/reference-chain-dependencies.md** - How parts reference each other
  - Simple and complex reference chains
  - Dependency resolution order
  - Invalid patterns (circular, forward references)
  - Best practices
- **docs/diagrams/operation-categories.md** - The four operation types explained
  - Visual breakdown of each category (positioning, modification, combining, replication)
  - Decision tree for choosing operation types
  - Detailed examples and use cases
  - Best practices and anti-patterns
- Integrated diagram links into README.md, YAML_REFERENCE.md, AUTO_REFERENCES_GUIDE.md, GLOSSARY.md

#### YAML Alias Support (Phase 2.2)
- **`anchors:` as alias for `references:`** - User-friendly alternative (v3.2+)
  - Added `TiaCADParser._normalize_yaml_aliases()` method
  - Validates that both sections aren't used simultaneously
  - Fully backward compatible - `references:` still works
  - Updated YAML_REFERENCE.md to show both syntaxes
  - Added 3 new tests in test_tiacad_parser.py
  - Created examples/anchors_demo.yaml demonstrating new syntax

#### Enhanced Metadata Fields (Phase 2.3)
- **Optional `type` and `composition` metadata fields** (v3.2+)
  - `type`: Declares document purpose (part, assembly, model, mechanism, fixture)
  - `composition`: Makes mental model explicit (reference-based)
  - Fully optional - backward compatible with existing files
  - Updated YAML_REFERENCE.md with detailed field documentation
  - Created examples/enhanced_metadata_demo.yaml demonstrating usage
  - Helps readers immediately understand document purpose and design approach

#### Terminology Standardization (Phase 2.5)
- **docs/TERMINOLOGY_GUIDE.md** - Canonical terminology reference (622 lines)
  - Established official terminology for 30+ concepts with rationale
  - Spatial terms: "local frame" (not "coordinate system"), "world space" (not "global coordinates")
  - Anchor terms: "auto-generated anchors" (not "auto-references"), "anchor" in user docs (not "reference")
  - Geometry terms: "face" (not "surface"), "normal" for vectors, "orientation" for frames
  - Operation categories: "Positioning (Transforms)", "Shape Modification (Features)", etc.
  - Documentation voice: "you" in tutorials, "users" in reference docs
  - Quick reference table for all terminology decisions
  - Version evolution notes for v4.0 planned changes
- **Applied standardization across 20 files**:
  - 9 documentation files (README, GLOSSARY, guides, specs)
  - 8 example YAML files
  - All technical documentation updated for consistency
- **scripts/audit_terminology.py** - Tool for finding terminology inconsistencies
- **Impact**: Clear authority on terminology, reduced ambiguity, faster doc writing, easier PR reviews
- **Changes**: 22 files changed (+1,052 insertions, -110 deletions)

### Added - Documentation Improvements (2025-11-13)

#### Mental Model & Language Clarity
- Added "TiaCAD's Design Philosophy: Reference-Based Composition" section to README.md
  - Explains how TiaCAD differs from traditional CAD (hierarchical assemblies)
  - Explains how TiaCAD differs from procedural tools (OpenSCAD)
  - Comparison tables showing TiaCAD vs SolidWorks vs OpenSCAD
  - Links to new GLOSSARY.md for term definitions

#### New Documentation Files
- **GLOSSARY.md** (650+ lines) - Comprehensive terminology guide
  - Core concepts: Part, Anchor, Reference-Based Composition, Operations
  - TiaCAD vs Traditional CAD comparisons
  - TiaCAD vs Procedural Tools comparisons
  - Spatial concepts: Face, Normal, Local Frame, Offset
  - Operation type categories explained
  - Technical terms decoded (SpatialRef, SpatialResolver, etc.)
  - Common confusion points addressed
  - Quick reference term translation table
  - Learning path guidance

- **docs/LANGUAGE_IMPROVEMENTS_STATUS.md** - Tracks language/documentation improvements
  - Phase 1 (Complete): Quick wins (mental model, glossary, anchors language)
  - Phase 2 (Planned): Visual diagrams, YAML aliases, enhanced metadata
  - Phase 3 (Planned): v4.0 breaking changes (rename core concepts)
  - Success metrics and user feedback collection plan
  - Version milestone tracking

#### Enhanced Existing Documentation
- **AUTO_REFERENCES_GUIDE.md**: Added "anchors" metaphor
  - Introduction explains anchors as "marked spots on a workbench"
  - Added "Why anchors?" explanation with ship's anchor metaphor
  - Listed 4 key benefits of anchor-based positioning

- **YAML_REFERENCE.md**: Added "anchors" language throughout
  - Changed section header to "References (Spatial Anchors) - v3.0"
  - Added "What are references?" introduction with anchor metaphor
  - Renamed "Named References" → "Named References (Custom Anchors)"
  - **Categorized Operations**: Reorganized into 4 clear types
    1. Positioning Operations (Transforms) - Move/rotate/scale
    2. Shape Modification Operations (Features) - Fillet/chamfer/extrude
    3. Combining Operations (Booleans) - Union/difference/intersection
    4. Replication Operations (Patterns) - Linear/circular/grid
  - Each category includes purpose statement and "Think of it as..." metaphor

- **TUTORIAL.md**: Added new section "Positioning Parts with Anchors"
  - Located after "Creating Holes" section
  - Explains anchor concept with workbench metaphor
  - Example: stacking boxes with `translate: to: base.face_top`
  - Table of common auto-generated anchors
  - Using anchors with offsets example
  - Benefits list (no coordinate math, self-updating, readable, error-proof)

- **README.md**: Reorganized documentation section
  - Separated User Documentation vs Technical Documentation
  - Added links to all major documentation files
  - Added GLOSSARY.md and LANGUAGE_IMPROVEMENTS_STATUS.md to index

#### Impact
- Users can now understand TiaCAD's reference-based mental model from documentation
- "Anchor" is now the primary user-facing term for spatial references
- Operations are categorized by purpose, making intent clearer
- Comprehensive glossary available for term lookup
- Documentation improvements tracked for future phases

**Related**: PR #14 (MENTAL_MODELS_AND_LANGUAGE.md), Session regavela-1113

---

## [3.0.0] - 2025-11-05

### Added - Major Architecture Redesign
- Unified spatial reference system (`SpatialRef`) replacing old `named_points`
- Auto-generated references for all parts (`.face_top`, `.center`, `.axis_z`, etc.)
- Local frame offsets for intuitive positioning
- Full orientation support (position + normal + tangent)

### Changed - Breaking Changes
- Replaced `named_points:` section with `references:` section
- Removed `PointResolver`, replaced with unified `SpatialResolver`
- YAML syntax breaking changes (see MIGRATION_GUIDE_V3.md)

### Migration
- See [MIGRATION_GUIDE_V3.md](docs/developer/MIGRATION_GUIDE_V3.md) for complete migration guide
- See [RELEASE_NOTES_V3.md](RELEASE_NOTES_V3.md) for detailed changes

---

## [0.3.0] - Previous Version

### Added - Phase 2 Complete
- Boolean operations (union, difference, intersection)
- Pattern operations (linear, circular, grid)
- Finishing operations (fillet, chamfer)
- Named points system (later replaced in v3.0)

### Added - Phase 1 Foundation
- Core primitives (box, cylinder, sphere, cone)
- Parameters with expressions
- Transform operations
- Schema validation

---

## Version History Overview

| Version | Release Date | Status | Key Features |
|---------|--------------|--------|--------------|
| **3.0.0** | 2025-11-05 | Current | Unified spatial references, auto-generated anchors |
| 0.3.0 | 2025-10-XX | Previous | Boolean ops, patterns, finishing, named points |
| 0.2.0 | 2025-09-XX | Legacy | Transforms, primitives, parameters |
| 0.1.0 | 2025-08-XX | Initial | Basic primitives and transforms |

---

## Upcoming

### v3.1 Phase 2 - Visual Regression Testing (2025-11-14)
**Status**: ✅ COMPLETE

**Features Implemented**:
- ✅ Visual regression framework using trimesh + matplotlib
- ✅ Reference images for 40+ examples
- ✅ 50+ visual regression tests (parametrized test suite)
- ✅ Automated visual diff reporting in CI
- ✅ Pixel-diff comparison with configurable thresholds
- ✅ HTML report generation with side-by-side image comparisons
- ✅ CI/CD integration via GitHub Actions
- ✅ Comprehensive documentation in TESTING_GUIDE.md

**Duration**: 1 session (2025-11-14)

### v3.2 - Dependency Graph (DAG) (Q3 2026)
**Status**: Planned (follows v3.1 Phase 2)

**Features**:
- ModelGraph using NetworkX for dependency tracking
- Incremental rebuild (10x faster for parameter changes)
- `--watch` mode for auto-rebuild on YAML changes
- `--show-deps` command for graph visualization
- Circular dependency detection

**Duration**: 6-8 weeks

### v3.3 - Explicit Constraints (Q4 2026)
**Status**: Planned (requires v3.2 DAG)

**Features**:
- Constraint YAML schema (flush, coaxial, offset)
- Manual constraint specification (user sets positions)
- Constraint validation and conflict detection
- Integration with ModelGraph
- 3+ assembly examples

**Duration**: 4-6 weeks

### v4.0 - Future (Breaking Changes)
- Rename core concepts (`parts:` → `shapes:`, `references:` → `anchors:`)
- Categorized operations in YAML structure
- Explicit model/assembly declaration
- Consistent spatial language
- See [docs/archive/LANGUAGE_IMPROVEMENTS_STATUS.md](docs/archive/LANGUAGE_IMPROVEMENTS_STATUS.md) for details

---

## Links

- [GitHub Repository](https://github.com/scottsen/tiacad)
- [Documentation](README.md#documentation)
- [Language Improvements Status](docs/archive/LANGUAGE_IMPROVEMENTS_STATUS.md)
- [Evolution Roadmap](docs/archive/TIACAD_EVOLUTION_ROADMAP.md)

### Key lessons
- `position:` key in part spec is silently ignored; use `operations: { type: transform, translate: [x,y,z] }`
- PBR rendering kills colors without HDR env; use smooth_shading + specular
- Consumed parts (boolean base/subtract, transform input) must be filtered from renders
