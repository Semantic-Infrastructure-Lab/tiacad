# TiaCAD Known Limitations

**Version:** Current
**Status:** Active limitations and workarounds reference

This document honestly describes what TiaCAD **cannot do**, with practical workarounds.

---

## What TiaCAD CAN Do (For Context)

Before limitations, here's what works great:

✅ **Solid Math Foundations:**
- Full spatial references (position + orientation + tangent)
- Frame-based transformations (local coordinate systems)
- Auto-generated part references (box.face_top, cylinder.axis_z)
- Proper rotation math (Rodrigues formula, explicit origins)

✅ **Complete Primitives & Operations:**
- All primitives (box, cylinder, sphere, cone, polygon)
- Boolean ops (union, difference, intersection)
- Patterns (linear, polar, grid)
- Finishing (fillet, chamfer)
- Sketch ops (extrude, revolve, sweep, loft)
- Advanced ops (hull, gusset, text)

✅ **Component System:**
- Local file imports (`./bracket.yaml`)
- Bundled stdlib (`tiacad://std/hardware/m3_screw`)
- GitHub imports (`github:user/repo/path.yaml`, cached to `~/.tiacad/cache/github/`)
- Hardware stdlib: m3/m4/m5/m6 screws, m3/m4/m5/m6 nuts, m3 washer, m3 standoff, mounting bracket

✅ **Dependency Graph + Watch Mode:**
- Incremental rebuild — only recomputes parts that changed
- `tiacad watch model.yaml` — auto-rebuild on file save
- `tiacad watch model.yaml --export /tmp/model.stl` — auto-export on each rebuild
- Cycle detection at build time

✅ **Project Quality:**
- Broad automated coverage across parser, correctness, DAG, and visualization workflows
  (see `TEST_STATUS.json` in the repo root for current pass/fail/coverage counts)
- 3MF export with color/metadata
- Schema validation

---

## Current Limitations

### 1. Constraint Solver — flush/offset/coaxial/tangent shipped

**What Works (as of 2026-07-19):**
```yaml
constraints:
  - type: flush
    faces: [bracket.face_bottom, base.face_top]   # [reference, moving]
  - type: offset
    faces: [surface.face_top, mount.face_bottom]
    distance: 5mm
  - type: coaxial
    edges:
      - {type: edge, part: bearing, selector: "%CIRCLE and >Z"}
      - {type: edge, part: shaft, selector: "%CIRCLE and >Z"}
  - type: tangent
    face: rail.face_top
    edge: {type: edge, part: roller, selector: "%CIRCLE and <X"}
```
`flush`/`offset`/`coaxial` wrap CadQuery's own `Assembly.constrain()`/`.solve()`; solves once
per build and compiles to ordinary `transform` operations (rigid propagation, not a
live/bidirectional solve). `tangent` (TCAD-1) mates a cylindrical part flush against a
reference plane without their surfaces intersecting — e.g. a roller resting on a rail — by
measuring the cylinder's radius directly off its geometry (`Edge.radius()`) and translating
along the reference normal until the axis sits exactly one radius from the plane. It
deliberately does NOT go through CadQuery's solver: the only fitting constraint kind
(`PointInPlane`) leaves 5 of 6 rigid-body freedoms open, so `.solve()` can rotate the part
into an arbitrary orientation rather than just sliding it — verified empirically. Like
`offset`, it requires the moving part's cylinder axis to already be parallel to the
reference plane (e.g. via a prior `rotate` transform) — no auto-alignment. Scope is
cylinder-face-vs-plane only, not cylinder-cylinder tangency. See
`tiacad_core/parser/constraint_builder.py` and ROADMAP.md "Constraint Solver".

**Also missing:**
- Constraint contradiction validation — CadQuery's solver currently just fails to converge
  on a contradiction, with no targeted "these two constraints conflict" message
- ModelGraph/DAG integration — constraints run as a standalone post-operations pass, not DAG
  edges
- Cylinder-to-cylinder tangency, and tangent auto-alignment (forcing the axis parallel to
  the plane instead of requiring it pre-rotated) — no documented use case yet; would need
  hand-rolled solver geometry CadQuery doesn't provide out of the box

**Workaround (for anything constraints don't cover yet):**
```yaml
# Use spatial references for relative positioning
parts:
  bracket:
    primitive: box
    parameters: {width: 50, height: 10, depth: 50}

operations:
  position_bracket:
    type: transform
    input: bracket
    transforms:
      # Manual positioning to align with base
      - translate:
          to: base.face_top  # Use auto-generated reference
          offset: [0, 0, 5]  # Manual offset for clearance
```

**Best Practice:**
- Define logical anchor points in `references:` section
- Use descriptive names (`motor_mount_point` not `point_1`)
- Comment the intent ("5mm clearance for wiring")
- Test assembly fit with multiple parameter values

---

### 2. Limited Export Formats

**What Works:**
- ✅ STL (widely supported)
- ✅ 3MF (with color and metadata)
- ✅ STEP (via CadQuery, basic)

**What's Missing:**
- ❌ DXF (2D laser cutting profiles)
- ❌ IGES (older CAD interchange)
- ❌ G-code (CNC toolpaths)
- ❌ SVG (2D projections)

**Impact:**
- Limited CAM integration
- No direct laser cutting export
- Manual conversion needed for some workflows
- STL/STEP export is still tied to CadQuery-compatible parts

**Workaround:**
- Export STEP → import to FreeCAD → export to other formats
- Use external tools for CAM (Fusion360, FreeCAD Path)
- Prefer 3MF when the model may come from non-CadQuery-backed geometry with tessellation support

**Future:** Community-driven — add if there's demand

---

### 3. CadQuery Coupling (Internal Issue)

**What It Means:**
- TiaCAD uses CadQuery as its geometry kernel
- The backend boundary is stronger than it was, but the system is still CadQuery-first
- Cannot easily swap to FreeCAD, build123d, or other kernels

**Impact:**
- Tied to CadQuery's capabilities and limitations
- Testing slower than with pure mock backend
- Cannot leverage alternative CAD kernels
- Some runtime surfaces are split:
  - 3MF export and visualization can use backend tessellation
  - STL/STEP export and many advanced operations still require CadQuery-compatible geometry

**For Users:** This doesn't affect YAML usage — you won't notice it

**For Contributors:**
- New code should use `GeometryBackend` abstraction
- Gradual refactoring during feature work
- CadQuery-only paths should be explicit in code and docs rather than implicit
- No plan to support multiple backends (maintenance burden)

**Decision:** Stay with CadQuery — it works well, no strong reason to change

---

### 4. Fixed — GitHub Import Branch Override

**Fixed 2026-07-11.** A trailing `@branch` suffix now selects the branch
(default `main`); branch names may contain slashes:
```yaml
imports:
  - path: github:user/repo/path.yaml         # main branch
  - path: github:user/repo/path.yaml@develop # branch override
  - path: github:user/repo/path.yaml@feature/x
```
Fetches from `raw.githubusercontent.com/{user}/{repo}/{branch}/{path}` and
caches under `~/.tiacad/cache/github/{user}/{repo}/{branch}/{path}`.
See `tiacad_core/parser/component_importer.py::_fetch_github`.

---

### 5. Assembly Parts Not Auto-Positioned

**What It Means:**
- When using component imports in an assembly, parts float at their default origin
- No spatial placement without explicit transforms in the parent YAML

**Impact:**
- Visual demos may show parts interpenetrating or floating in space
- Functional geometry (volume, dimensions) is correct; visual assembly is not

**Workaround:**
```yaml
operations:
  place_screw:
    type: transform
    input: screw
    transforms:
      - translate: {to: bracket.hole_1}
```

**Future:** Constraint solver (next milestone) will address this.

---

### 6. Fixed — `awesome_guitar_hanger.yaml` mounting holes now pierce the plate

**What it was:** The four screw-hole `difference` cuts subtracted from empty air — the
mounting plate shipped with **no holes**. The shafts floated above the plate
(`Z[16.5, 33.5]` vs plate `Z[-7.5, 7.5]`); the countersinks projected past the front
edge (`Y[65, 75]`).

**Root cause:** Axis-mapping mental-model error. The `box` primitive maps `height`→Z
and `depth`→Y, so the parameter named `plate_height` (90) is the plate's **Y** extent
while `plate_thickness` (15) is the **Z** thickness. The screw references put the
vertical positioning value in the Z offset (assuming Z is the tall axis), so the holes
landed off the plate.

**Fix applied:** shaft offsets swap the Y/Z components (verified: volume drops by
exactly two through-holes, `589 mm³ = 2 × π·2.5²·15`). Countersinks retarget from
`face_front` to `face_top` with the vertical value in the face-tangent offset that
maps to world Y — verified numerically (`get_bounds()`) that both countersinks now sit
centered on the shafts' X/Y and straddle the plate's top surface (`Z[4, 8]` vs top face
at `Z=7.5`).

**Why it matters beyond one example:** 1,599 passing tests never caught it — the
`TestGuitarHanger*` contracts check volume *ranges*, not hole presence. The systemic gap
(no assertion that a `difference` actually removes volume) is now closed by
`BooleanEffectRule` — see
[docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md](docs/developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md)
and [MODEL_VALIDATION.md](docs/developer/MODEL_VALIDATION.md#best-next-improvements). The
new rule caught a second, independent instance of this exact bug class in
`guitar_hanger_named_points.yaml` the same session it shipped (also fixed).

---

### 7. Fixed — `polygon` primitive's `circumscribed` flag was inverted (all stdlib hex nuts oversized)

**What it was:** `_build_polygon`'s own docstring says `circumscribed: true` (the
default) means "diameter is outer [tip-to-tip] circle." It passed that flag straight
through to `cq.Workplane.polygon(circumscribed=...)` — but CadQuery's flag means the
opposite: `circumscribed=True` makes the *given* diameter the polygon's **inscribed**
(across-flats) circle, with vertices landing *outside* it at `radius/cos(π/N)`.
Result: every part built with `primitive: polygon` came out ~15.5% oversized across
flats (for a hexagon) relative to what its own `diameter` parameter and docstring said.

**Caught by:** building the Tier-0 ladder-corpus `T0_polygon` model
(`examples/validation/T0_polygon.tiacad`) and cross-checking its bbox against the
closed-form regular-hexagon formula — the measured across-corners extent (23.09mm for
`diameter: 20`) didn't match a tip-to-tip diameter of 20mm at all.

**Real-world impact:** all four stdlib hex nuts (`m3_nut.yaml`…`m6_nut.yaml`) — the only
users of the `polygon` primitive — were built with across-flats 6.35/8.08/9.24/11.55mm
instead of the intended ISO 4032 5.5/7.0/8.0/10.0mm. A printed M3 nut from stdlib would
not fit an M3 wrench.

**Fix applied:** invert the flag when calling into CadQuery
(`tiacad_core/parser/parts_builder.py::_build_polygon`), so TiaCAD's own documented
contract holds. Verified all four nuts now build at their ISO across-flats dimensions;
added `test_hex_body_across_flats_matches_iso4032` regression tests to
`test_example_contracts.py` (none of the pre-existing nut tests asserted AF at all).

---

### 8. Fixed — curved geometry (spheres, fillets): mesh-based `watertight` check was a false negative

**What it was:** the `expect: watertight` contract check exported the built solid to
STL (CadQuery default tessellation: `tolerance=0.001`, `angularTolerance=0.1`) and
asked `trimesh` whether the resulting mesh was watertight. This was **always False**
for any solid with curved surfaces sharing a seam or fillet blend:
- The `sphere` primitive — reproduced at radii 1/5/10/18/25mm and at STL tolerances
  down to 1e-4 — because OCCT's sphere tessellation leaves the two pole-seam vertices
  unwelded, producing 3 disconnected mesh islands (`trimesh.split(only_watertight=False)`).
- A box with all 12 edges filleted (`T1_fillet.tiacad`) — 9 disconnected mesh islands,
  presumably one per rounded-corner region not welding to its neighbors.

**Why it was a false negative, not a real defect:** `count_solids` (the exact
BREP-level solid count, not mesh-derived) reports 1 for both cases, and `get_volume`
(also BREP-exact) matches the respective closed-form formula (`4/3·π·r³` for the
sphere; the Minkowski-sum-with-a-ball rounded-box formula for the fillet) to full
kernel precision — the geometry itself was a single valid closed solid in both cases.
Only the STL round-trip used for the mesh watertight check was affected.

**Fix applied (2026-07-18):** `get_manifold_stats` (`tiacad_core/testing/contracts.py`)
now checks watertightness at the BREP level — `Shape.isValid()` per solid (CadQuery's
wrapper over OCCT's `BRepCheck_Analyzer`) — instead of an STL/trimesh round-trip. This
sees through tessellation-only seam/blend artifacts while still catching genuine
topological defects (verified with a solid deliberately built from an open, 5-of-6-face
shell — reports `watertight: False` as expected). `mesh_islands` is retained in the
returned stats for diagnostics only; it no longer drives the `watertight` contract
check. `examples/validation/T0_sphere.tiacad` and `T1_fillet.tiacad` both now assert
`expect: watertight: true`. 2 new tests in
`test_embedded_contracts.py::TestWatertightBrepCheck`.

---

### 9. Fixed — part-level `translate:`/`rotate:` were dead schema syntax

**What it was:** the schema documents `translate:` (and, less formally, `rotate:`)
as valid keys directly on a `parts:` entry — the "auto-generated anchors" feature
demonstrated by `anchors_demo.yaml` and the `auto_references_*.yaml` examples, e.g.
`left_pillar: {translate: {to: platform.face_top, offset: [-30, 0, 0]}}`.
`parts_builder.py::build_part` never read either key — confirmed by inspecting the
raw CadQuery `BoundingBox()` of the built geometry, not just a wrapper measurement.
Every part positioned this way silently built at its untranslated local origin.

**Caught by:** building the Tier-1 ladder-corpus union model
(`examples/validation/T1_union_overlap.tiacad`) — a `box_b` positioned via inline
`translate:` produced the *same* volume as `box_a` alone (8000mm³, not the expected
12000mm³ for two overlapping cubes), because the two boxes were secretly coincident.

**Real-world impact:** 27 usages across 12 example files, including files whose sole
purpose is demonstrating this feature (`anchors_demo.yaml`,
`auto_references_with_offsets/rotation/box_stack/cylinder_assembly.yaml`). E.g.
`anchors_demo.yaml`'s `left_pillar`/`right_pillar` were meant to sit at opposite
edges of a platform; they actually both sat exactly at world origin, fully
overlapping. `pcb_standoff_assembly.yaml` (one of the two examples seeded with an
`expect:` contract in the prior session) had its `pcb` part silently stuck at Z=0
instead of its intended height. None of the existing per-example dimensional
contracts caught any of this — they only ever asserted a part's own local
width/height/depth/volume, never its absolute position relative to siblings
(exactly the class of gap Tier 4 relational contracts exist to close).

**Fix applied:** `OperationsBuilder.apply_inline_part_transforms()` (new method,
`tiacad_core/parser/operations_builder.py`) reuses the exact same
`TransformTracker` + `_apply_translate`/`_apply_rotate` + `spatial_resolver`
machinery that already powers `operations: type: transform`, applied once per part
right after `PartsBuilder.build_parts()` and the document's `SpatialResolver` both
exist (so any part may anchor to any sibling's auto-generated references) and
before `operations:` runs (`parser/parse_pipeline.py`). `PartRegistry.replace()`
(new) swaps each part's geometry in place under its own name. Supports both schema
forms: a single spec (vector / `{to: ...}` / named-point string) and the "sequence
of translation vectors" form. Dedicated regression coverage:
`tiacad_core/tests/test_parser/test_inline_part_transforms.py`.
`TestV3BracketMount.test_bounding_box` (`v3_bracket_mount.yaml`) had asserted the
bug-compatible bbox (`height: 100.0`); corrected to the geometrically-derived true
value (`140.0` — base plate ∪ bracket, whose center now correctly lands on
`base_plate.face_back`). Full non-visual suite (1732 tests at the time of this
fix — current count is higher, see ROADMAP.md) and visual regression
(67 tests) both green after the fix; no visual golden PNGs cover the 12 affected
files.

---

### 10. Fixed — `lego_brick_2x1`/`lego_brick_3x1` cavity floor was 1.5mm, not the declared 1.0mm

**What it was:** `cavity_positioned`'s translate used `[wall_thickness, wall_thickness,
bottom_thickness]` for `[X, Y, Z]`. `brick_cavity` is built with `width` = length-inset
(maps to X), `height` = width-inset (maps to Z), `depth` = height-inset (maps to Y) — box
maps `width->X, depth->Y, height->Z` (`tiacad_core/geometry/base.py`). So this cavity's own
"depth" param (`brick_height - bottom_thickness`, the *vertical* cavity dimension) lands on
Y, and its "height" param (`brick_width - 2*wall_thickness`, the *lateral* inset) lands on
Z — but the translate offset wall_thickness/wall_thickness/bottom_thickness assumed the
opposite (X/Y both lateral insets via wall_thickness, Z vertical via bottom_thickness). The
Y and Z offsets were effectively swapped relative to what those axes actually needed.

**Caught by:** hand-deriving the closed-form inclusion-exclusion volume oracle for
`examples/validation/T3_lego_2x1.tiacad` — the naive formula (`brick_vol - cavity_vol +
studs`) didn't match the measured build until `cavity_positioned`'s actual bounds were
inspected directly: `Y:[1.5, 10.1]` against a brick body whose Y extent is only `[0, 9.6]`
— the cavity undershot the intended floor offset by 0.5mm at the bottom and overshot the
top face by 0.5mm (silently clipped there, since no material exists past the body's own
extent).

**Real-world impact:** every brick printed from these two examples had a 1.5mm floor
instead of the `bottom_thickness: 1.0` parameter's declared value — a genuine dimensional
defect (not a connectivity/printability one; both files were already `components: 1` /
watertight before and after). Volume was off by ~15-27mm³ (2x1: 906.707→891.306mm³; 3x1:
1309.96→1283.109mm³), each within the pre-existing `test_example_contracts.py` tolerance
(`abs=50`/`abs=100`), so no test caught it before this session's Tier 3 work demanded an
exact oracle instead of a wide-tolerance sanity range.

**Fix applied:** swap the translate's Y/Z components to `[wall_thickness, bottom_thickness,
wall_thickness]` in both `examples/lego_brick_2x1.yaml` and `examples/lego_brick_3x1.yaml`.
Both files' `expect: volume:` were updated to the corrected, verified value.
`examples/validation/T3_lego_2x1.tiacad` reproduces the fixed geometry from the start with
a full inclusion-exclusion derivation in its header comment and a hard `components: 1` /
`watertight: true` gate — the exact "measures fine but is secretly disconnected" bug class
this model is named for in `docs/developer/VALIDATION_STRENGTHENING.md` section 3 Tier 3
(confirmed this specific defect was dimensional, not connectivity, but Tier 3's manifold
gate is what forced the exact-oracle derivation that caught it).

---

### 11. Fixed — screw/bolt heads floated disconnected from their own shafts

**What it was, two distinct bugs caught by the Tier 4 assembly relational corpus
(`docs/developer/VALIDATION_STRENGTHENING.md` section 3):**

1. **Component-internal axial gap.** Every fastener component
   (`m3_screw`/`m4_screw`/`m5_screw`/`m6_bolt`, both the `examples/components/`
   copies and their `tiacad_core/stdlib/hardware/` counterparts — 8 files total,
   identical bug in each) builds `shaft` and `head` as separate cylinders, then
   positions the head with `operations: position_head: transforms: [translate:
   [0, 0, '${length}']]`. Since `shaft` is a default-centered cylinder (spans
   `[-length/2, +length/2]`), translating `head` to `Z=length` (the shaft's
   *full* length, not its top) leaves the head floating `length/2 -
   head_height/2` above the shaft's actual tip instead of sitting flush on it.
   Confirmed by direct `get_bounds()` measurement before the fix: m3 (length=8,
   head_height=3) had shaft top at `Z=4.0` and head bottom at `Z=6.5` — a
   2.5mm gap, not contact.
2. **Assembly-level disconnect**, found while extending
   `examples/hardware_assembly_demo.yaml` with a Tier 4 `expect: relations:`
   contract. Its `m3_pos`/`m4_pos`/`m5_pos`/`m6_pos` operations translate only
   each screw's `shaft` sub-part to the fastener's final position on the plate
   — the `head`/`position_head` sub-part was never transformed at all, so it
   stayed stranded at the imported component's local origin (near world
   origin) regardless of where the shaft ended up. A `flush:`/`coaxial:`
   relation between the two (once bug #1 was fixed) still failed — the head
   and shaft were nowhere near each other in the final assembly.

**Caught by:** hand-deriving the Tier 4 `flush:` relation for
`examples/validation/T4_bolted_bracket.tiacad` (a from-scratch model, not
derived from the buggy components) surfaced the correct pattern — `translate:
{to: X.face_top, offset: [0,0,own_half_height]}` — which made the existing
components' `translate: [0,0,length]` pattern look wrong by comparison;
confirmed by direct measurement of the imported components' actual built
geometry.

**Real-world impact:** every screw/bolt built through these components (in any
example, not just `hardware_assembly_demo.yaml`) has a head that visually
floats above its shaft with a gap, and in `hardware_assembly_demo.yaml`
specifically the head never appeared anywhere near its assembled shaft at all.
Neither defect affected volume/bbox of any individual sub-part (the bug is
purely positional), so no dimension-only contract or test caught it —
exactly the class of gap Tier 4 relational contracts exist to close.

**Fix applied:** (1) changed `position_head`'s translate to `[0, 0,
'${length / 2 + head_height / 2}']` in all 8 fastener component files, so the
head's bottom face lands exactly on the shaft's top face. (2) added
`m{3,4,5,6}_head_pos` operations to `hardware_assembly_demo.yaml`, each
translating its screw's `position_head` sub-part by the *same* offset already
used for that screw's `_pos` shaft operation, so the head now travels with
its shaft into the final assembly position. `hardware_assembly_demo.yaml`'s
`expect: relations:` now asserts `coaxial`/`flush` between each
`m{3,4,5,6}_pos` (shaft) and `m{3,4,5,6}_head_pos` (head) with zero gap — this
would have failed before either fix and passes after both. Part count in that
file rose from 25 to 29 (`test_example_contracts.py::TestHardwareAssemblyDemo`
updated accordingly); no other example references the affected `.head`/
`position_head` sub-parts as an input, so the blast radius is contained to
these two files' geometry.

**Known resolver limitation surfaced in the process — fixed 2026-07-11:**
relation endpoints in `expect: relations:` used to require flat (non-dotted)
part/operation names. `SpatialResolver._resolve_name`
(`tiacad_core/spatial_resolver.py`) split a dotted reference on the *first*
dot to get `part.ref` — so a namespaced import part like `m3.shaft` (itself
containing a dot from the `as: m3` namespace) couldn't be combined with a
`.face_top`/`.axis_z` suffix: `"m3.shaft.face_top"` resolved as part `m3`
(not found), ref `shaft.face_top`, and failed. Workaround used at the time:
give the part a flat top-level name via an `operations: type: transform`
(even a same-position no-op) and reference that instead — every Tier 4
relation in `hardware_assembly_demo.yaml` uses `m3_pos`/`m3_head_pos`-style
flat names for exactly this reason; those still work unchanged and were left
as-is (no need to churn a working example). **Fix:** `SpatialResolver` gained
`_split_part_ref`, which tries split points from the last dot backward and
picks the longest prefix that's an actual registered part name, falling back
to the old first-dot split (for its "part not found" error message) only
when no prefix matches. `"m3.shaft.face_top"` now resolves to part
`m3.shaft`, ref `face_top` directly — the flat-name workaround is no longer
required for new models. Covered by
`tiacad_core/tests/test_spatial_resolver.py::TestNamespacedPartLocalReferences`.

---

### 12. Fixed — two silent/opaque-failure gaps found while building the Tier 5 negative-input corpus

**What they were, found while building `examples/validation/negative/` (`docs/developer/VALIDATION_STRENGTHENING.md` section 3, Tier 5) and verifying — by actually running each broken file, not just reading code — that the parser fails loudly and specifically on bad input:**

1. **Message-less error on a negative/zero primitive dimension.** `PartsBuilder._build_box`/`_build_cylinder`/`_build_sphere`/`_build_cone`/`_build_torus`
   (`tiacad_core/parser/parts_builder.py`) passed dimensions straight to the OCCT
   kernel with no positivity check (unlike `_build_polygon`/`_build_text`, which
   already validated). A negative box width raised
   `OCP.OCP.Standard.Standard_DomainError` with an **empty message string**; wrapped
   by `build_parts()`'s generic `except Exception` into a `PartsBuilderError`, the
   final surfaced message was `"Failed to build part 'block': "` — technically a
   typed `TiaCADError`, not a raw traceback, but useless for actually diagnosing the
   problem. Confirmed by running `examples/validation/negative/N3_negative_dimension.tiacad`
   through `TiaCADParser.parse_file()` before any fix.
2. **Duplicate part names silently discarded the first definition.** PyYAML's
   default `SafeLoader` behavior lets a later duplicate mapping key clobber an
   earlier one with **no error and no warning** —
   `tiacad_core/parser/yaml_with_lines.py::construct_mapping_with_lines` inherited
   this. Two `block:` entries under `parts:` parsed and built successfully, silently
   keeping only the second — a "built, plausible, but wrong" bug, not a parse
   failure. Confirmed by running `examples/validation/negative/N6_duplicate_part_name.tiacad`
   before any fix: it parsed with no error at all.

**Fix applied:** (1) added `PartsBuilder._require_positive()`, called from
`_build_box`/`_build_cylinder`/`_build_sphere`/`_build_torus` (plus a
tailored radius/height check in `_build_cone`, since a cone's radii may
legitimately be 0 at the apex but not negative, and torus additionally
checks `minor_radius < major_radius` to reject a self-intersecting tube) —
raises `PartsBuilderError` naming the exact parameter and value, e.g. `"Box
'block' has invalid width: -10 (must be a positive number)"`. (2)
`construct_mapping_with_lines` now tracks keys seen at each mapping level and
raises `yaml.constructor.ConstructorError` (surfaced through `parse_file()`'s
existing `except yaml.YAMLError` handling as a typed `TiaCADParserError`) on
a same-level duplicate key, naming the key and its first-seen line number.
Both verified against the negative corpus (`N3`/`N6`) and against the full
non-visual suite (no examples in this repo rely on merge keys (`<<:`) or
intentional duplicate keys, confirmed by grep — the change is not
regression-risky). See `tiacad_core/tests/test_correctness/test_negative_contracts.py`.

---

### 13. Fixed — `pcb_standoff_assembly.yaml`'s plate/PCB had `height`/`depth` swapped, rendering as a vertical wall instead of a flat plate

**Found while doing the trust-gallery visual sign-off pass** (`docs/developer/VALIDATION_STRENGTHENING.md` section 4.7): the box primitive maps `width→X, depth→Y, height→Z` (`tiacad_core/geometry/cadquery_backend.py::create_box`, `cq.Workplane.box(width, depth, height)`). `examples/trust/pcb_standoff_assembly.yaml`'s `plate` and `pcb` parts assigned their in-plane footprint dimension (`plate_height`/`pcb_height`, meant to be the Y-axis extent) to the box's `height` parameter (which is actually Z, the thickness axis), and the thickness (`plate_thickness`/`pcb_thickness`) to `depth` (Y). The rendered result was a 100×5×80 vertical panel standing on edge, not the documented "flat plate (100×80×5) with PCB centered on top" — a "built, plausible-looking, but wrong" bug that a volume-only check can't catch (volume is identical regardless of axis assignment) but a visual render immediately exposes. The pre-existing hand-written `TestTrustPcbStandoffAssembly.test_plate_dimensions` had encoded the same swapped values, so it silently passed against the bug instead of catching it.

**Fix applied:** swapped `height`/`depth` in both parts' `parameters:` blocks so the plate's thickness (Z) and footprint (Y) map to the correct axes; updated the hand-written dimension test to match the corrected geometry. Confirmed visually (re-rendered trust gallery) and re-ran `test_trust_contracts.py`. See `examples/trust/SIGNOFF.md`.

---

## Test Health

TiaCAD has broad automated coverage for parser behavior, geometry correctness, DAG rebuild behavior, visualization, and example contracts.

Known areas to keep an eye on:
- Geometry regressions around boolean merges in complex examples
- **Booleans that silently do nothing** — `BooleanEffectRule`
  (`tiacad_core/validation/rules/boolean_effect_rule.py`, shipped 2026-07-10) now checks
  every `difference`/`intersection`/`union` for a measurable effect on every model, with
  no per-model contract to write. See
  [MODEL_VALIDATION.md](docs/developer/MODEL_VALIDATION.md#best-next-improvements). Known
  gap: the `union` check is whole-result only — an input that fully overlaps an
  already-placed part (contributing nothing) is not flagged per-input.
- Visual/regression scenarios that depend on OCCT behavior
- Example-specific limitations documented in `examples/` and the active test suite

---

## Best Practices for Working Within Limitations

### For Missing Constraints:
1. Use spatial references (`base.face_top`)
2. Create named anchors for assembly points
3. Comment design intent ("5mm clearance")
4. Validate fits with measurement tests

### For Limited Export:
1. Export STEP as CAD interchange format
2. Use FreeCAD for secondary format conversion
3. STL/3MF for direct printing

---

## How This Document Works

- **Updated:** On releases when capabilities change
- **Honest:** Real limitations, real workarounds
- **Practical:** Focus on "how to work around" not "why we can't"
- **Forward-looking:** Links to ROADMAP.md for future plans

**Not Listed:** Bugs (those go in GitHub issues), planned features (see ROADMAP.md)

---

**Feedback:** If a limitation blocks your work, file an issue with your use case. Real user needs guide priorities.
