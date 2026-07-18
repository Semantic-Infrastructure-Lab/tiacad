---
title: "Making TiaCAD Validation Easier and Stronger"
type: strategy
status: proposal
created: 2026-07-10
beth_topics:
  - tiacad
  - testing
  - correctness
  - validation
  - confidence
---

# Making TiaCAD Validation Easier and Stronger

**A strategy for building geometric confidence from simple parts to complex assemblies.**

Status: proposal · Author session: project-validation-review · Date: 2026-07-10

---

## TL;DR

TiaCAD has a large, healthy test suite (~1,859 non-visual passing, 1,926 total as of 2026-07-11), but most of it proves the
wrong thing. Visual regression proves *"looks the same as last time."* The volume
sanity tier proves *"something was built."* Neither proves *"this is the geometry
the YAML actually asked for."* That is the **oracle problem**, and it is the single
biggest lever for stronger validation.

Two moves solve most of it:

1. **Trade snapshots for oracles.** Replace "same as the reference image" with
   properties that are *provable from math* — closed-form volumes, conservation
   under transforms, inclusion–exclusion for booleans, symmetry, determinism.
   These catch subtle "built but wrong" errors that pixels and `volume > 0`
   never will, and they can never encode a snapshot-of-a-bug.

2. **Make a validated model as cheap to write as the model itself.** Add an
   optional `expect:` contract block *inside the `.tiacad` file*. One generic
   test then validates every file against its own declared expectations. Today,
   validating a new example means hand-writing a bespoke pytest class; that
   friction is why only ~30 of 50 examples have real contracts.

Everything else in this document is built on those two moves, organized as a
**confidence ladder**: primitives with closed-form ground truth at the bottom,
assemblies at the top, where each rung only trusts what the rung below has proven.

**But before either — a free fix.** The printability/connectivity/schema checks
are gated on optional-import libraries and quietly *skip* when those libraries
(or a buildable example) are missing, so a green CI run can mean "nothing was
checked." Making those skips into failures is hours of work and closes the single
biggest hole (§4.5). Do it first.

---

## 1. Where validation stands today (honest snapshot)

TiaCAD's safety net has five layers. Here is what each *actually* proves.

| Layer | Location | Proves | Does **not** prove |
|---|---|---|---|
| Volume sanity (Tier 1) | `test_example_contracts.py` | 47 examples build with volume > 0 | Correct dimensions, position, or shape |
| Dimensional contracts (Tier 2) | `test_example_contracts.py` | ~30 examples match hand-derived values | Only the examples someone bothered to hand-write |
| Correctness suite | `test_correctness/` | Primitive dims, boolean volume math, attachment distance, rotation angles, mesh validity | Analytic *coverage* is ad hoc; no property/fuzz generation |
| Visual regression | `test_visual_regression.py` | 49 examples render identically to a stored PNG | Whether that PNG was ever correct; sub-pixel errors |
| Assembly validator | `validation/rules/` (8 rules) | Advisory warnings (gaps, disconnected parts, hole-edge) | Nothing is a hard gate; rules emit WARNING/INFO |

**Real strengths — keep these.** The `tiacad_core.testing.*` measurement API
(`get_dimensions`, `get_volume`, `get_surface_area`, `measure_distance`,
`parts_aligned`, `get_normal_vector`) is a genuinely good foundation — it makes
geometric assertions a one-liner. The trust renderer (6-view colored PNG for
human/AI review) is an excellent complement to automated checks. The correctness
tests already reach for analytic truth in places (Pappus's theorem for the
revolve, `2·r·sin(θ/2)` chord spacing for polar patterns). The raw material for
strong validation is here; it is under-exploited.

### The structural gaps

- **G1 — Oracle/snapshot risk.** Visual regression and any "audit-captured" golden
  value both trust a *prior output*. If a bug existed when the baseline was
  captured, the test now actively protects the bug. The testing guide names this
  the *"snapshot of a bug"* problem — it is real and unaddressed for the ~49
  visual references and for every audit-derived volume constant.

- **G2 — Contracts are manual and sparse.** A validated example requires a
  bespoke pytest class in a 54 KB file. That friction caps coverage: ~20 of ~50
  examples have *no* dimensional contract, only `volume > 0`. Adding a model and
  proving it is correct are two separate, unequal amounts of work.

- **G3 — CI proves "parses," not "correct."** `example-validation.yml` runs
  `validate_examples.py`, which only calls `parse_file()` — it never checks a
  single dimension or volume. Worse, `visual-regression.yml` *generates the
  reference images itself* when they are missing (`UPDATE_VISUAL_REFERENCES=1`),
  so a fresh CI machine silently canonizes whatever it renders. The geometric
  contracts do run (inside `tests.yml`), but the two dedicated "validation"
  workflows add almost no correctness signal.

- **G4 — Schema/reality drift.** `tiacad-schema.json` declares a `validation:`
  block (`clearance_check`, `bounds_check`, `thickness_check`,
  `intersection_check`) that **no code implements and no example uses** — a
  documented feature that does nothing. The schema pins `schema_version: "3.0"`
  while every example uses `2.0`. Feature-detection helpers
  (`find_cylindrical_holes`, `find_fillets`, `parts_in_contact`,
  `is_fully_connected`) are **stubs that raise `NotImplementedError`**. And there
  are *two* pytest configs (`pytest.ini` and a dormant block in
  `pyproject.toml`) that disagree on markers. The declared surface and the real
  surface have quietly diverged.

- **G5 — Skips masquerade as passes (the most dangerous gap).** The tests that
  verify a model is actually *manufacturable* — watertight, single solid, boolean
  actually merged — live in `test_geometry_validation.py` and are **entirely
  gated on `trimesh`** (`skipif(not HAS_TRIMESH)`). Schema conformance is gated on
  `jsonschema`; all 3MF-export correctness on `lib3mf` (~40 skips). These three
  libraries are declared **required** in `requirements.txt` / `pyproject.toml`,
  yet in a clean checkout they may not import at all — in which case the entire
  printability/connectivity/schema safety net **silently degrades from failures
  to skips.** A green run then means "nothing was checked," not "everything
  passed." Two more skip anti-patterns compound it: `test_visual_regression.py`
  does `pytest.skip("Could not parse/build …")` on build failure (a broken
  example becomes a *skip*, not a *failure*), and several tests
  `pytest.skip("Example not found")` — so a deleted or renamed model quietly stops
  being tested. **Skipping is not passing, but a green CI badge cannot tell the
  difference.**

- **Meta-gap — the docs overstate confidence.** The three "quality" summaries
  (`CODE_QUALITY_SUMMARY.md`, `SKIPPED_TESTS_AUDIT.md`, and parts of
  `KNOWN_LIMITATIONS.md`) describe a state that no longer exists (they cite a
  `HACK` comment and `.skip` files that are gone) and report "EXCELLENT /
  APPROVED FOR PRODUCTION." Test counts disagree across documents (1382, 1405,
  1406, 1486, 1519, 1538, 1025) — there is **no single source of truth for test
  health.** `CHANGELOG.md` is the only truthful record, and it shows a run of
  serious geometry bugs in *shipped headline examples* (`lego_brick_2x1` — 6
  disconnected bodies; `lego_brick_3x1` — same 3 coordinate bugs; `chamfered_bracket`
  — plate 74 mm off its base) caught only in March 2026. The contract coverage
  that would have caught them is new and unproven across the corpus. Read
  confidence from the CHANGELOG and the actual assertions, not the summaries.

---

## 2. The guiding principle: oracles over snapshots

An **oracle** is anything that tells you the *right* answer independently of the
system under test. TiaCAD leans almost entirely on the weakest kind — a *golden
snapshot* (a stored render or an audited number). Three stronger kinds are
available and barely used:

- **Analytic oracle** — the answer is a closed-form formula. A box of
  `w×h×d` has volume `w·h·d` and surface area `2(wh+wd+hd)`, *exactly*,
  regardless of what CadQuery returns. A cylinder is `π·r²·h`, a sphere
  `4/3·π·r³`, a cone `1/3·π·r²·h`, a regular N-gon prism
  `½·N·s²·cot(π/N)·h`. Centroids and bounding boxes are equally derivable.
  These need no baseline and cannot rot.

- **Metamorphic oracle** — you don't know the absolute answer, but you know how
  it must *change* when the input changes. Translate a part → volume unchanged.
  Scale every dimension by `k` → volume scales by `k³`. `union(A, B)` == `union(B, A)`.
  `union(A, A)` == `A`. Mirror a symmetric part → identical bbox and volume.
  These catch a huge class of bugs with no golden values at all.

- **Differential / self-consistency oracle** — cross-check the engine against
  itself. Inclusion–exclusion: `vol(A∪B) = vol(A) + vol(B) − vol(A∩B)` must hold
  for *any* A and B the engine produces. If union, intersection, and difference
  don't agree on the same pair, at least one is wrong — and you learn this without
  knowing any of the three answers in advance.

**Why this is the top priority:** analytic and metamorphic oracles are the only
tools that catch *"built, plausible, but wrong"* — a 48 mm box that should be
50 mm, a hole 2 mm off-center, a boolean that silently no-op'd. Pixel diff misses
these at render resolution; `volume > 0` misses them entirely; a snapshot golden
misses them if the snapshot was taken after the bug. Oracles also *generate*:
one property test over random parameters is worth a hundred hand-written cases.

---

## 3. The confidence ladder (simple → complex)

The organizing idea the task asks for: **build confidence bottom-up, each rung
trusting only what is proven below it.** If primitives are proven exact, a
boolean test can assume its *inputs* are correct and isolate the *operation*. If
operations are proven, an assembly test can isolate *placement*. Bugs get caught
at the lowest possible rung, where they are easiest to diagnose.

Each tier below lists: what it proves, the oracle it uses, the `.tiacad` models to
create, and the test script that checks them.

### Tier 0 — Primitives (closed-form ground truth)

- **Proves:** every primitive matches its exact analytic volume, surface area,
  bounding box, and centroid.
- **Oracle:** analytic formulas (above). No baseline.
- **Models:** `examples/validation/T0_box.tiacad`, `T0_cylinder`, `T0_sphere`,
  `T0_cone`, `T0_torus`, `T0_polygon` — one primitive each, parameters chosen so
  the expected values are obvious, with an embedded `expect:` block (§4.1).
- **Script/test:** `test_correctness/test_primitive_invariants.py` — a
  **property-based** test (Hypothesis) that generates random valid parameters and
  asserts `get_volume(part) ≈ formula(params)` within kernel tolerance, for every
  primitive. This alone is stronger than every current primitive test combined,
  because it covers the whole parameter space, not six hand-picked sizes.

### Tier 1 — Single operations (invariants and self-consistency)

- **Proves:** each operation transforms geometry by exactly the amount the math
  predicts, assuming Tier-0 inputs are correct.
- **Oracle:** metamorphic + differential.
  - Transforms: translate/rotate preserve volume and surface area exactly;
    translate shifts centroid by the offset; rotate by 90° permutes bbox axes.
  - Booleans: inclusion–exclusion self-consistency; `union ≤ sum`; `difference ≤
    base`; `intersection ≤ min`; commutativity; idempotency (`A∪A=A`, `A∩A=A`);
    identity (`A − ∅ = A`).
  - Patterns: `vol(linear pattern of n) ≈ n · vol(unit)` for non-overlapping
    copies; polar copies equidistant from the axis.
  - Finishing: fillet/chamfer *reduce* volume, by a *bounded* amount (never to
    zero, never larger than the removed wedge).
  - Scaling: uniform scale by `k` ⇒ volume `×k³`, area `×k²`.
- **Models:** `T1_translate`, `T1_rotate90`, `T1_union_overlap`,
  `T1_difference`, `T1_intersection`, `T1_pattern_linear`, `T1_pattern_polar`,
  `T1_fillet`, `T1_chamfer` — each the *smallest* model that isolates one
  operation on Tier-0 primitives.
- **Script/test:** `test_correctness/test_operation_invariants.py` +
  `test_metamorphic.py`.

### Tier 2 — Determinism and reproducibility

- **Proves:** the same YAML always produces the same geometry — across repeated
  runs and (ideally) across platforms and CadQuery versions.
- **Oracle:** self-equality. Build twice; the exported mesh must be
  byte-identical (or hash-identical after canonical ordering).
- **Why it matters:** OCCT tessellation and boolean ops can be non-deterministic.
  Non-determinism silently defeats *every* golden-based test (visual and mesh)
  with flaky failures, and it undermines the DAG's incremental-rebuild cache
  correctness. This tier is cheap and pays for itself immediately.
- **Models:** reuse the Tier 0–1 corpus.
- **Script/test:** `test_correctness/test_determinism.py` — build each model N
  times, assert stable `get_volume`/bbox to full precision and a stable mesh hash.
  Optionally store a small set of **golden mesh hashes** as an intentional,
  reviewed baseline (distinct from auto-generated visual refs).

### Tier 3 — Composite parts (analytic goldens + manifold health)

- **Proves:** a multi-feature single body (plate + holes, bracket + fillet) has
  the right *net* volume and is manufacturable.
- **Oracle:** inclusion–exclusion arithmetic (plate − Σ holes + overlaps), plus
  **hard** mesh-validity gates: watertight, no self-intersection, expected
  component count.
- **Why it matters:** the recent `lego_brick_3x1` "disconnected body" bug is
  exactly this class — a part that *measures* fine but is secretly two solids.
  Manifold/connectivity checks catch it; volume alone does not.
- **Models:** `T3_plate_one_hole`, `T3_plate_bolt_circle`, `T3_bracket_fillet`,
  `T3_lego_2x1` — derived directly from the existing examples but with
  analytically computed expectations, not audited snapshots.
- **Script/test:** extend `test_geometry_validation.py` to assert component count
  and watertightness as *failures*, not observations; add analytic volume
  contracts via the embedded `expect:` block.

### Tier 4 — Assemblies (relational contracts)

- **Proves:** parts are in the right place *relative to each other* — the thing
  visual regression and single-part volume both miss.
- **Oracle:** relational assertions using the existing measurement API —
  `measure_distance(a, b, ref1, ref2) < ε` for flush contact, `parts_aligned`
  for coaxial, expected pairwise spacing, and **no interpenetration** (sum of
  part volumes ≈ union volume when parts should only touch).
- **Models:** `T4_two_boxes_flush`, `T4_standoff_stack`, `T4_bolted_bracket`,
  and the real `hardware_assembly_demo` (25 parts) with a full relational
  contract, not just "25 parts present."
- **Script/test:** `test_correctness/test_assembly_contracts.py`, backed by the
  embedded `expect: relations:` block (§4.1).

### Tier 5 — Regression corpus and negative testing

- **Proves:** the parser fails *loudly and correctly* on bad input, and
  real-world designs keep working.
- **Oracle:** expected-error matching; round-trip stability.
- **Models:** a `examples/validation/negative/` set of intentionally broken
  files (bad refs, cyclic params, zero dims, unknown primitive) each asserting a
  *specific* error class and message — the counterpart to the happy-path corpus.
- **Script/test:** `test_correctness/test_negative_contracts.py`; optional
  Hypothesis-based parser fuzzing that asserts "either parses to valid geometry
  or raises a typed TiaCAD error — never a raw traceback or a silent empty solid."

---

## 4. The highest-ROI ideas, ranked

Ordered by (payoff ÷ effort). Each is independently shippable.

### 4.1 — Embedded `expect:` contracts *(easier — the biggest single win)*

**Problem (G2):** validating a model requires a separate hand-written test. That
friction is why coverage is sparse and why the `.tiacad` file, the trust comment,
and the pytest assertion drift apart — the truth about a model lives in three
places.

**Proposal:** add one optional, self-describing block to the schema:

```yaml
# examples/validation/T3_plate_one_hole.tiacad
schema_version: "2.0"
parts: { ... }
operations: { ... }

expect:                        # <-- the model declares its own ground truth
  final: bracket               # part whose contract is authoritative
  volume: 9214                 # mm³, tolerance from `tol:` or default
  bbox: [50, 20, 10]           # w × h × d
  watertight: true
  components: 1
  relations:                   # for assemblies (Tier 4)
    - { flush: [top.face_bottom, base.face_top], gap: 0 }
    - { coaxial: [screw.axis_z, hole.axis_z] }
  tol: { length: 0.5, volume: 50 }
```

Then **one** generic, parametrized test discovers every `.tiacad` with an
`expect:` block and validates it — no per-example test code ever again:

```python
# test_correctness/test_embedded_contracts.py
@pytest.mark.parametrize("path", discover_models_with_expect())
def test_embedded_contract(path):
    assert_contract(TiaCADParser.parse_file(path))   # reads expect:, checks it
```

Expose the same engine on the CLI: `tiacad check --contract model.tiacad` and
`tiacad audit --write-contract` to *seed* an `expect:` block from a current build
(which a human then reviews — so a snapshot becomes a *reviewed* contract, not a
silent one). This **supersedes the dead `validation:` block** in the schema:
implement `expect:` and delete the vaporware, closing G4.

**Payoff:** adding a validated model drops from "write a model + a pytest class"
to "write a model + five lines of `expect:`." Coverage stops being gated by
tester patience. The model becomes the single source of truth for its own
correctness. **Effort:** medium (schema addition + one parser hook + one test +
CLI flag). This is the keystone — most other tiers ride on it.

**Shipped 2026-07-10:** `expect:` is now a real schema block (`tiacad-schema.json`),
threaded through the parser onto `TiaCADDocument.expect`, and checked by
`tiacad_core/testing/contracts.py::check_contract()` — volume, bbox,
watertight, component count, and `relations:` (`flush`/`coaxial`, resolved via
the existing `SpatialResolver` dot-notation face/axis lookups). One generic
parametrized test, `test_correctness/test_embedded_contracts.py`, discovers
every example with an `expect:` block and checks it — confirmed working
end-to-end with synthetic flush/coaxial fixtures before rollout. `tiacad check
--contract` and `tiacad audit --write-contract` are live (the latter seeds a
contract from a build for human review; it does not write to the file). This
also closes G4: the dead `validation:` schema block (unused by any parser
code) is deleted, superseded by `expect:`.

Seeded two real examples as the first reviewed contracts:
`examples/simple_guitar_hanger.yaml` (Tier 1: volume/bbox/watertight/components)
and `examples/pcb_standoff_assembly.yaml` (Tier 4: adds a `coaxial` relation
between a standoff and its screw).

**Shipped 2026-07-11:** seeded `expect:` contracts (via `tiacad audit
--write-contract`, cross-checked against each file's pre-existing hand-derived
pytest assertions) for the remaining 25 examples with a Tier-2 pytest class in
`test_example_contracts.py` — every example that class covers now has its own
reviewed ground-truth contract; `test_embedded_contracts.py`'s generic
parametrized test discovers and checks 50 models. The hand-written pytest
classes themselves were **not** deleted/trimmed this pass — many assert
sub-part dimensions (`bracket.base`, `washer.washer`, individual screws in a
25-part assembly) that a single `final:`-part `expect:` block can't replace,
and a handful (`TestLegoMath.test_3x1_larger_than_2x1`, `TestV3BracketMount`'s
sum-of-parts bound) do cross-file or derived-quantity comparisons `expect:`
has no syntax for. A subset (roughly a dozen classes that assert *only* the
final part's volume/bbox, e.g. `TestSimpleBox`, `TestV3SimpleBox.test_top_volume`,
`TestTransitionLoft`, `TestFormatsDemo`) are now fully redundant with their
example's `expect:` block and safe to trim in a focused follow-up — deferred
here rather than rushed, since misclassifying a class as "final-only" and
deleting real sub-part coverage would be a net loss.

**Shipped 2026-07-11 (trim):** went through every Tier-2 class by hand,
cross-checking each asserted value against its example's `expect:` block
before deleting anything (a couple of near-misses: `TestAutoRefsCylinderAssembly`
and `TestAnchorsDemoPlatform` *look* final-only but actually measure a
non-exported sub-part — `shaft`/`platform` — while the file's `expect: final:`
is a different part (`sphere_top`/`crossbar`); both were kept in full since
`expect:` says nothing about the part they check). 14 classes were fully
redundant and deleted outright: `TestSimpleBox`, `TestSimpleExtrude`,
`TestBracketWithHole`, `TestTransitionLoft`, `TestFormatsDemo`,
`TestTextOperations`, `TestChamferedBracket`, `TestPipeSweepSimple`,
`TestBottleRevolve`, `TestMountingPlateWithBoltCircle`, `TestWeek5AlignToFace`,
`TestWeek5Assembly`, `TestWeek5FrameBasedRotation`, `TestDagTestSimple`. 7 more
classes were partially trimmed — the final-only methods removed, sub-part or
cross-file methods kept: `TestAutoReferencesBoxStack.test_top_box_volume`,
`TestV3SimpleBox.test_top_volume`, `TestLegoMath.test_2x1_volume_in_range`,
`TestRoundedMountingPlate.test_bounding_box` (kept
`test_volume_less_than_sharp_edge_variant` — genuinely cross-file),
`TestLegoBrick3x1.test_bounding_box`/`test_volume_in_range` (kept
`test_volume_larger_than_2x1` — cross-file), `TestV3BracketMount.test_bounding_box`/
`test_volume_positive` (kept `test_volume_below_sum_of_parts` — a sum-of-
sub-parts derived bound `expect:` has no syntax for, per this section's own
call-out above), `TestSimpleGuitarHanger.test_width_matches_plate_width` (kept
its two sum-of-parts/derived-bound tests for the same reason). 39 test methods
removed total; full non-visual suite went from 1876 passed / 0 failed / 67
deselected to 1837 passed / 0 failed / 67 deselected — an exact 39-test drop,
no regressions.

**Bug found via this tooling, fixed 2026-07-10:**
`examples/mounting_plate_with_bolt_circle.yaml`'s boolean difference produced
3 disconnected components instead of 1 (48/252/252-vertex islands) — a real
unprintable-geometry bug the old per-example-test-only approach never caught.
Root cause: `bolt_hole`/`center_hole` are cylinders (default axis Z), but the
box primitive maps `width->X, depth->Y, height->Z`, so this plate's actual
thin dimension is Y, not Z. The circular pattern rotated hole copies around
`axis: Z`, which only translates a Z-cylinder's position in the XY-plane
without reorienting it — so only 2 of 6 holes ever lined up with the Y-thin
face at all, and even those didn't reach the Y faces (radius 3.25 < half-
thickness 4mm), leaving them as fully enclosed internal cavities that mesh
out as extra disconnected shells. Fix: rotate `bolt_hole`/`center_hole` 90°
about X (via an `operations: transform`) before patterning, so their axis
runs along Y, and pattern around `axis: Y` instead of `Z`. The same bug
(plus a matching `edges: {direction: Z}` on the fillet, which should target
Y — the true thickness edges) existed in `examples/rounded_mounting_plate.yaml`
and got the identical fix. Both now build as a single watertight component and
have `expect:` contracts seeded (`components: 1`) so this can't silently
regress. The plate's box parameters themselves were correct all along — the
pre-existing `test_bounding_box` tests (`dims["height"] == 8.0`, i.e. Y-extent)
were right and did not need to change; the fix lives entirely in `operations:`.

### 4.2 — Property-based invariant tests with Hypothesis *(stronger)*

**Problem (G1):** hand-picked cases test six sizes; bugs hide in the other
infinity of parameter values.

**Proposal:** add `hypothesis` (already have numpy/scipy) and write generators
for valid primitive parameters and operation combinations. Assert the Tier-0/1
analytic and metamorphic properties over generated inputs. Start with primitive
volume/area/bbox, then transform-conservation, then boolean inclusion–exclusion.

**Payoff:** each property test is worth a hundred examples and shrinks failures to
a minimal reproducer automatically. Directly kills the snapshot-of-a-bug risk for
everything it covers. **Effort:** low–medium; high early yield.

**Shipped 2026-07-10 — and it immediately found a real bug.**
`tiacad_core/tests/test_correctness/test_property_based.py` (18 property tests)
builds each primitive through the real user path (`ParameterResolver` →
`PartsBuilder` → `CadQueryBackend`) and checks the Tier-0/1 analytic oracles
over machine-generated parameters: box/cylinder/sphere/cone/frustum/torus
volume, bounding-box extents (including the `width→X, depth→Y, height→Z` box
mapping that caused the §4.1 disconnected-components bug), and box/cylinder/
sphere surface area; plus translate/rotate volume-invariance, uniform-scale
`k³`, and boolean inclusion-exclusion over generated overlapping pairs. Every
test runs under `@settings(derandomize=True, deadline=None)` — Hypothesis
generates the *same* examples every run, so a failure reproduces bit-for-bit in
CI and the suite can't flake on RNG, while the deadline is lifted for slow OCCT
solid construction. Confirmed non-vacuous two ways: a deliberately wrong box
axis-mapping assertion is correctly rejected, and —

**Bug found and fixed 2026-07-10 (zero-volume torus):** the very first torus
property run reported `volume = 0.0`. The `torus` primitive
(`parts_builder.py::_build_torus`) built its solid by revolving a circle profile
360° about an axis that lay *in the profile's own plane*
(`Workplane("XZ").center(R,0).circle(r).revolve(360,(0,0,0),(0,0,1))`); on the
OCP 7.9 / CadQuery 2.8 kernel that produces a **degenerate zero-volume solid**
(bounding box collapses to the flat 2D profile). It had been broken for the
entire life of the primitive and no test noticed, because the only torus test
asserted `part is not None` — the exact "snapshot of nothing" this section warns
about. Fixed by building the torus with the kernel's direct
`cq.Solid.makeTorus(R, r)` (exact, orientation-stable: donut flat on XY, hole
along +Z), and strengthened `test_parts_builder.py::test_simple_torus` to assert
the Pappus volume `2π²Rr²` and the `2(R+r) × 2(R+r) × 2r` bounding box so it
can't silently regress. `hypothesis` added to `requirements.txt` /
`pyproject.toml` and to the CI import-guard (a required test dep must hard-fail
if missing, not silently skip — §4.5). Full non-visual suite 1701 passed (was
1601: +82 schema gate, +18 property tests), visual suite 67 passed.

### 4.3 — Metamorphic suite *(stronger)*

The self-contained subset of 4.2 that needs *no* generators: translate/rotate
conservation, scale `k³`, union commutativity/idempotency, mirror symmetry,
boolean self-consistency. A dozen assertions that would have caught most historic
geometry bugs. Ship even before Hypothesis. **Effort:** low.

**Shipped 2026-07-10:** `tiacad_core/tests/test_correctness/test_metamorphic.py`,
26 tests over asymmetric box/cylinder/compound shapes (chosen so a bug that
ignores rotation/translation entirely can't pass by symmetry accident):
translate/rotate/mirror conservation, scale `k³` for box and cylinder, union
commutativity/idempotency, and boolean self-consistency (inclusion-exclusion
`|A∪B| + |A∩B| = |A| + |B|`, difference-equals-minus-intersection, and
disjoint-subtract-is-a-no-op). Sanity-checked against a deliberately broken
union (returning one operand unchanged) to confirm the inclusion-exclusion
test actually fails when it should, not just when the author expects it to.

### 4.4 — Determinism gate + reviewed mesh-hash goldens *(stronger + de-flakes)*

Implement Tier 2. Add a `test_determinism.py` that fails on non-reproducible
builds, and a small `golden_hashes.json` that is *only* updated by an explicit,
reviewed command. This both hardens correctness and stabilizes every other
golden-based test. **Effort:** low.

**Shipped 2026-07-10:** `tiacad_core/testing/determinism.py` builds a model
from scratch via `TiaCADParser.parse_file` and captures volume, bounding box,
and a SHA-256 mesh hash (raw exported-STL bytes, deliberately not
canonicalized — canonicalizing would hide the exact tessellation drift this
gate exists to catch). `test_correctness/test_determinism.py` runs two
checks over every model with an `expect:` block (the existing embedded-
contracts corpus, reused per this section's original suggestion): (1)
self-consistency — build the same model 3× in one run and assert every build
agrees exactly, no golden file required, catches non-determinism the moment
it's introduced; (2) golden comparison — one build checked against the
reviewed `tiacad_core/tests/test_correctness/golden_hashes.json`, catching
drift across sessions or CadQuery/OCCT kernel upgrades that self-consistency
alone can't see. A missing golden entry is a hard failure, not a skip,
consistent with §4.5. Goldens are regenerated only by the explicit
`scripts/update_determinism_goldens.py` (mirrors the existing
`UPDATE_VISUAL_REFERENCES` pattern) — never by the test suite itself.
Verified the gate actually detects drift (not just passing vacuously) with a
standalone negative check against `check_against_golden`. All 6 corpus
models build bit-identical mesh hashes across repeated builds on this
machine's stack (CadQuery 2.8.0 / OCP 7.9.3.1.1, Python 3.12) — 13 new tests,
full non-visual suite now 1601 passed (was 1588), 0 failed.

**Fixed 2026-07-18 (TCAD-VAL-6):** the "raw hash, deliberately not
canonicalized" design above was correct for the self-consistency tier but
wrong for the golden-comparison tier — it assumed exact tessellation
reproducibility *across machines*, which CadQuery's `exportStl(parallel=True)`
does not provide. Confirmed via a real GitHub Actions 3.13 run vs a local
build of `T0_torus.tiacad`: every one of 16129 tessellated vertices matched
exactly (nearest-neighbor distance 0.0) while ~35% of 31752 triangles
connected those same points differently — an ambiguous-quad-diagonal choice
at the torus seam, resolved non-deterministically by parallel meshing, not a
real geometry difference. Added `canonical_mesh_hash()`
(`tiacad_core/testing/determinism.py`) — SHA-256 of the sorted, 6-decimal-
rounded vertex point cloud, with triangle connectivity dropped from the
fingerprint — and switched golden comparison to gate on it instead of the
raw STL hash. Self-consistency (`check_determinism`) is untouched: it still
compares raw mesh hashes, which is the correct zero-tolerance check for
"does this one machine's pipeline reproduce its own output." Verified the
new hash is genuinely cross-machine-stable (not just a coincidence for one
pair of runs) three ways: math-only cross-check against the downloaded CI
artifact's raw vertex data, a fresh local Python 3.13 build, and the repo's
Python 3.12 dev venv — all three produce the identical
`canonical_mesh_hash` for `T0_torus.tiacad`. All 53 goldens regenerated
(pure additive diff — added field only, no existing volume/bbox/mesh_hash
values changed). `mesh_hash` is kept in `golden_hashes.json` for provenance
only; it's expected to differ across machines and is no longer gated on.

### 4.5 — Turn skips into failures; make the safety net non-optional *(stronger, closes G5 — do this first)*

**Problem (G5):** the printability/connectivity/schema net vanishes when
`trimesh`/`lib3mf`/`jsonschema` aren't importable, and broken examples become
skips. A green run can mean nothing was checked.

**Proposal — small, mechanical, enormous payoff:**

- Add a **CI import-guard** step that hard-fails if any declared-required
  dependency (`trimesh`, `lib3mf`, `jsonschema`, `pyvista`) does not import.
  Required deps must be *required*, not "skip if missing."
- Convert `skipif(not HAS_TRIMESH)` on the *correctness* suite to a hard
  requirement in CI (keep the graceful skip only for genuinely optional local
  dev). The safety net must run on every merge.
- Replace `pytest.skip("Could not parse/build …")` and
  `pytest.skip("Example not found")` with **failures**. If a listed model can't
  build or is missing, that is the bug, not a reason to look away.

**Effort:** low. **Payoff:** the biggest hole in the current net closes with a
handful of line changes. Nothing else in this plan matters if the checks can
silently not run.

**Partially shipped 2026-07-10:** `test_schema_validation.py`'s
`skipif(not JSONSCHEMA_AVAILABLE)` (32 tests) converted to an assertion that
fails collection outright if `jsonschema` isn't importable — it's a required
dependency (`pyproject.toml`), so a silent skip meant the schema-validation
net could vanish with no signal. `trimesh` was already a hard import
(`test_geometry_validation.py`) and `"Example not found"` was already
`pytest.fail`, not skip — both predate this pass.

**CI import-guard shipped:** `tests.yml` has a "Verify required dependencies
import" step that hard-fails the run if any of `trimesh`, `lib3mf`,
`jsonschema`, `pyvista`, `cadquery` can't import — required deps must be
*required*, not degrade into silent skips. Still open: the `lib3mf`/`pyvista`
skips in the exporter/visualization *test* suites (arguably legitimate — those
are optional-at-runtime rendering/export paths, not the correctness safety net
G5 is about; worth an explicit decision before touching them, not a mechanical
sweep).

### 4.5b — Fix the CI validation gaps *(stronger, closes G3)*

**Update 2026-07-10: `example-validation.yml` deleted, not fixed.** It was
also independently broken by GitHub's `actions/upload-artifact@v3`
deprecation (hard-failed at "Set up job", before checkout, on every run) —
so it was adding zero correctness signal *and* zero parse signal. Since the
geometric contract suite already runs inside `tests.yml`, there is no
standing workflow doing parse-only validation to replace. If a dedicated
contract-gate workflow is wanted later, build it fresh on `tiacad check
--contract examples/**`, not by resurrecting the deleted file.

- **`visual-regression.yml`:** **stop auto-generating missing references in CI.**
  A missing reference should *fail* and require an intentional, reviewed
  regeneration — never a silent canonization of a fresh render.
- Make manifold/watertight and the contract suite **required** checks for merge.

**Shipped 2026-07-10:** `visual-regression.yml`'s `check_refs` /
`Generate reference images (if missing)` / `Upload reference images (for
first run)` steps are gone. CI now runs `pytest -m visual` once,
unconditionally, with no `UPDATE_VISUAL_REFERENCES` fallback — a missing
reference raises `FileNotFoundError` from `render_and_compare()` and fails
the run, matching local dev behavior. Verified both directions locally: full
suite green against the 55 committed references (`67 passed`), and a
deliberately removed reference (`anchors_demo.png`) turned into a hard test
failure rather than a silent regeneration. Updating or adding a reference
still requires the explicit, reviewed `UPDATE_VISUAL_REFERENCES=1 pytest -m
visual` invocation, run locally by a human.

**Shipped 2026-07-18:** branch protection enabled on `main` — all 4 CI checks
(`test (ubuntu-latest, 3.11/3.12/3.13)`, which run the manifold/watertight and
`expect:` contract suites via `pytest -m "not visual"`, plus
`visual-regression (3.11)`) are now required status checks; a red run blocks
merging. No PR-review requirement (kept the existing direct-push-to-main
workflow intact) — force-push and branch deletion are blocked.

### 4.6 — Manifold & connectivity as a first-class gate *(stronger, closes a real bug class)*

Implement the stubbed `parts_in_contact` / `build_contact_graph` /
`is_fully_connected` helpers and promote the `DisconnectedPartsRule` from an
advisory WARNING to a checkable contract (`expect: components: 1`). This is the
class that produced the `lego_brick_2x1` (6 bodies), `lego_brick_3x1`, and
`chamfered_bracket` disconnected-body bugs.

**Critical detail — count solids at the kernel, not mesh islands.** The
single-solid check was recently *weakened* from "exactly 1 component" to
"is_watertight" because `trimesh.split()` reports >1 island for legitimately
hollow parts (tubes, through-holes). But `is_watertight` is strictly weaker: two
separate closed solids are also watertight, so the check that was *supposed* to
catch disconnected bodies now can't. The correct fix is to count solids at the
**BREP level** via CadQuery (`shape.Solids()`), which distinguishes "one hollow
body" from "two disjoint bodies" that mesh-island counting cannot. **Effort:**
medium.

**Shipped 2026-07-10:** the `expect: components:` gate now counts disjoint
bodies at the BREP/kernel level. `tiacad_core/testing/contracts.py` gained
`count_solids(part)` — `sum(len(v.Solids()) for v in part.geometry.vals())` —
and `get_manifold_stats` now returns `components` = BREP solid count (the
correct signal) alongside `mesh_islands` = the old `trimesh.split` count (kept
for diagnostics, no longer used by the contract check). Verified strictly
stronger in both directions: a hollow 20mm cube with a fully enclosed 10mm
void reports `components: 1` (BREP) where mesh islands reported 2 — the
false-positive that had motivated the earlier weakening — and two disjoint
watertight boxes report `components: 2` where `is_watertight` alone (both are
watertight) could not tell them apart. All six existing seeded contracts were
confirmed unchanged (each already `mesh_islands == brep_solids == 1`).
Regression tests: `test_correctness/test_embedded_contracts.py::TestSolidCounting`.

The three previously-stubbed connectivity helpers in
`tiacad_core/testing/measurements.py` (`parts_in_contact`,
`build_contact_graph`, `is_fully_connected`) are now real implementations —
`parts_in_contact` uses exact OCCT `BRepExtrema_DistShapeShape` surface-to-
surface distance (not a bounding-box approximation), and the graph/connectivity
helpers build on it. Tested in `test_testing/test_measurements.py`
(`TestPartsInContact`, `TestContactGraphConnectivity`). Still open: promoting
`DisconnectedPartsRule` itself from an advisory WARNING to a hard gate that
uses `count_solids` (the rule still uses its own bbox-proximity heuristic; the
authoritative check now lives in the contract path via `expect: components:`).

### 4.7 — Trust gallery as a versioned, signed-off artifact + AI review loop

Formalize `scripts/trust_render.py --gallery` into a committed, dated artifact
that a human or an AI reviewer signs off on ("the blue cylinder is centered on
the red plate — approved"). Pair each trust scenario with its `expect:` block so
the *visual* sign-off and the *numeric* contract are captured together. This turns
the trust renderer from an ad-hoc debugging aid into an auditable
correctness-of-record for the things math can't fully pin down (aesthetics,
orientation sanity). **Effort:** low–medium.

### 4.8 — Schema truth reconciliation *(closes G4)*

Add a CI test that validates every example against `tiacad-schema.json`, and a
test that the schema itself matches reality: implement or delete the `validation:`
block, reconcile `schema_version`, and collapse the two pytest configs into one.
A schema that lies is worse than no schema. **Effort:** low.

**Shipped 2026-07-10:** the schema was lying about a lot. A parametrized gate,
`test_schema_validation.py::test_every_example_validates_against_schema`,
discovers every `.yaml` under `examples/` (82 files) and asserts each validates
against `tiacad-schema.json` with zero errors — guarded by
`test_examples_directory_is_discoverable` so an empty glob can't make it pass
vacuously (§4.5 discipline). Standing this gate up surfaced **27 of 82
committed, building examples failing schema validation** — every one a case
where the schema was stricter than the parser, confirmed by building each
failing example first (the model is the reviewed ground truth; the schema was
wrong, not the model). Reconciled `tiacad-schema.json` to parser reality across
every failing construct: added the missing top-level keys `name` /
`description` / `anchors` / `imports`; widened `export.formats` items to accept
bare format strings (not only `{type,path}` objects); `operations.edges` to
accept a keyword string (`"all"`) as well as an object selector; rotate
`origin` and the new rotate `around` to accept a named-reference string / inline
axis object (and required `angle` + *either* `axis` or `around` instead of
mandating `axis`); part `color` to accept `{r,g,b(,a)}` and `{h,s,l(,a)}`
objects; part `size` to accept a scalar (text font size); `colors` palette
entries to accept rich `{value,description,metalness,roughness}` objects;
`materials.color` to accept an `[r,g,b(,a)]` array; a two-point `{type:axis,
from,to}` reference; and `translate` to accept a sequence of vectors. All 82
examples now validate; the 32 pre-existing negative tests (`test_invalid_*`)
still reject bad input, so the schema stayed *discriminating*, not a rubber
stamp. `validation:` block was already deleted (§4.1) — confirmed absent.
`schema_version` is consistent: the enum is `3.0`, every example declares `3.0`,
and the new gate enforces it going forward (legacy `2.0` remains parser-accepted
only in old inline test fixtures, which aren't part of the schema-validated
corpus). The dual pytest config was already collapsed (`pytest.ini` removed
2026-07-10; `[tool.pytest.ini_options]` in `pyproject.toml` is now the single
source). Full parser + correctness suites green after the change (1065 passed).

### 4.9 — Canonical golden STEP set (last, and small)

For ~5 anchor models, commit a STEP export as an exact-geometry baseline,
regenerated only by explicit review. This is a *supplement* to oracles for
catching topology changes that volume/bbox miss — deliberately last, because
goldens without an oracle are the very trap this plan is escaping. **Effort:**
low; **keep the set tiny.**

---

## 5. Concrete deliverables checklist

**New `.tiacad` models** — a ladder corpus under `examples/validation/`, each with
an `expect:` block:

- ~~`T0_*` primitives (6)~~ Shipped 2026-07-11: `T0_box/cylinder/sphere/cone/torus/polygon`,
  each checked against its closed-form analytic volume/bbox formula (Appendix). Found
  and fixed two real bugs in the process (see §4.1's "Bugs found via this tooling"
  list): the `polygon` primitive's inverted `circumscribed` flag (all stdlib hex nuts
  were oversized), and dead part-level `translate:`/`rotate:` schema syntax.
- ~~`T1_*` single ops (9)~~ Shipped 2026-07-11: `T1_translate/rotate90/union_overlap/
  difference/intersection/pattern_linear/pattern_polar/fillet/chamfer`. Translate,
  rotate, union, difference, intersection, and both patterns check an exact closed-form
  value; fillet uses the exact Minkowski-sum-with-a-ball rounded-box formula (confirmed
  to match measured volume to full kernel precision); chamfer uses a reviewed bounded
  value (no closed form for a 12-edge 45° chamfer with corner interactions).
- ~~`T3_*` composites (4)~~ Shipped 2026-07-11: `T3_plate_one_hole/plate_bolt_circle/
  bracket_fillet/lego_2x1`, each a multi-feature composite with a volume `expect:`
  derived from inclusion-exclusion of the closed-form Tier-0/1 oracles, plus a hard
  `components: 1` manifold-health gate (BREP solid count via `count_solids`, not mesh
  islands). `T3_plate_one_hole` and `T3_bracket_fillet` are exact closed-form (the hole
  is deliberately sized/positioned to stay clear of any rounded region, so no
  clipping/overlap correction is needed); `T3_plate_bolt_circle` reproduces the
  Tier-2 `mounting_plate_with_bolt_circle` axis-rotation fix from §4.1 and is also
  exact closed-form; `T3_lego_2x1` — the model VALIDATION_STRENGTHENING.md names as
  the motivating "measures fine but is secretly two solids" case — is closed-form for
  the base/cavity/studs term and a reviewed measured-and-bounded value (T1_chamfer
  precedent) for the two support-tube unions, whose footprint straddles the
  cavity/wall boundary with no simple closed form (0 < Δ < 246.401, measured
  150.004). Found and fixed a real bug while deriving `T3_lego_2x1`: see
  KNOWN_LIMITATIONS.md #10 — `lego_brick_2x1.yaml`/`lego_brick_3x1.yaml`'s cavity
  translate had its Y/Z offsets swapped, giving a 1.5mm floor instead of the
  declared `bottom_thickness: 1.0`; fixed in both examples (volumes corrected
  906.707→891.306 and 1309.96→1283.109). Also strengthened
  `test_geometry_validation.py`'s `test_mounting_plate_bolt_circle_watertight` and
  `test_lego_brick_2x1_is_single_component` from mesh-island/watertight-only
  observations to a hard BREP-level `count_solids() == 1` assertion, per this
  section's "assert component count ... as failures, not observations" directive.
  Full non-visual suite: 1845 passed (was 1833), 0 failed — 12 new tests (4 embedded
  contracts + 8 determinism checks), no regressions.
- ~~`T4_*` assemblies (4)~~ Shipped 2026-07-11: `T4_two_boxes_flush/standoff_stack/
  bolted_bracket`, plus a full `expect: relations:` contract added to the existing
  29-part `hardware_assembly_demo.yaml` (not a new `.tiacad` file, but the fourth
  deliverable named in section 3 Tier 4 — "the real `hardware_assembly_demo` ... with a
  full relational contract"). `T4_two_boxes_flush` uses part-level `translate:` (the
  KNOWN_LIMITATIONS.md #9 fix) to butt two boxes face-to-face at exactly zero gap.
  `T4_standoff_stack` derives from `pcb_standoff_assembly.yaml` and stacks
  standoff+spacer+screw, exercising `coaxial` and `flush` together across three
  interfaces. `T4_bolted_bracket` drills a through-hole and positions a bolt whose
  shaft is coaxial with the hole (with real clearance, `shaft_r < hole_r`) and whose
  head sits flush on the bracket face. Every relation was hand-derived from the
  declared transforms and independently re-verified against `get_bounds()`
  measurement before being written into `expect:`. Added a new contract-engine check,
  `expect: no_overlap:` (`tiacad_core/testing/contracts.py::_check_no_overlap`,
  schema in `tiacad-schema.json`) — the "no-interpenetration" oracle this section
  names (`vol(A)+vol(B) == vol(union(A,B))` for touching-only pairs), verified against
  a deliberately-overlapping synthetic pair to confirm it actually catches
  interpenetration, not just passes vacuously. `negative/*` broken inputs remain open
  (Tier 5, not part of this pass).
  Found and fixed a real bug in the process (see §4.1-style "Bugs found" note):
  every fastener component (`m3_screw`/`m4_screw`/`m5_screw`/`m6_bolt`, 8 files —
  both `examples/components/` and `tiacad_core/stdlib/hardware/` copies) positioned
  its `head` at `Z=length` instead of the shaft's actual top
  (`Z=length/2+head_height/2`), leaving every screw head floating with a gap above its
  shaft instead of sitting flush on it; `hardware_assembly_demo.yaml` compounded this
  by never transforming the head into the shaft's final assembly position at all. Both
  fixed; see KNOWN_LIMITATIONS.md #11 (which also documents a related `SpatialResolver`
  limitation found in the process — dotted namespaced part names like `m3.shaft` can't
  be combined with a `.face_top`/`.axis_z` suffix in a relation reference — worked
  around with flat operation names, not fixed). `tiacad_core/tests/test_correctness/
  test_assembly_contracts.py` added: direct synthetic coverage for the new
  `no_overlap` engine plus a second, independently-derived hand-verification pass over
  the Tier 4 corpus (the generic `test_embedded_contracts.py` sweep already discovers
  and checks every `expect:` block including `relations:`/`no_overlap:`, so this file
  deliberately does not duplicate that — see its module docstring). Full non-visual
  suite: 1863 passed (was 1845), 0 failed — 18 new tests (9 in the new assembly-
  contracts file, 3 embedded-contract discoveries, 6 determinism checks), no
  regressions; visual suite unchanged at 67 passed.
- ~~`negative/*` ~6~~ Shipped 2026-07-11: `N1_bad_spatial_ref/N2_cyclic_parameter/
  N3_negative_dimension/N4_unknown_primitive/N5_malformed_schema/N6_duplicate_part_name`,
  each an intentionally broken `.tiacad` file triggering one specific error class —
  a bad `translate: to:` reference, a circular `${a}`/`${b}` parameter cycle, a
  negative box dimension, a misspelled `primitive:`, a box missing its required
  `depth`, and two `parts:` entries sharing the name `block`. Every fixture was
  verified by actually running it through `TiaCADParser.parse_file()` and observing
  the real exception type/message before any test assertion was written (this
  tier's own "verify, don't assume" mandate) — see `test_negative_contracts.py`.
  Two real gaps found and fixed in the process (small, well-scoped input-validation
  additions, not architectural): N3 originally surfaced a message-less OCCT
  `Standard_DomainError` wrapped into an empty-message `PartsBuilderError`; fixed
  with `PartsBuilder._require_positive()` across box/cylinder/sphere/cone/torus. N6
  originally parsed and built with **no error at all** — PyYAML's default loader
  silently discards an earlier duplicate mapping key; fixed in
  `yaml_with_lines.py::construct_mapping_with_lines`, which now rejects a same-level
  duplicate key by name and line. See KNOWN_LIMITATIONS.md #12. **This is the last
  item on this checklist — the full T0→T5 confidence ladder is now shipped.**

**New scripts / CLI:**

- `expect:` contract engine + `tiacad check --contract` and
  `tiacad audit --write-contract`.
- ~~Implement the stubbed connectivity helpers.~~ Done 2026-07-10:
  `parts_in_contact` / `build_contact_graph` / `is_fully_connected` are real
  (BREP `BRepExtrema` distance); BREP solid counting (`count_solids`) is the
  `expect: components:` gate. See section 4.6.

**New tests** (`test_correctness/`):

- `test_primitive_invariants.py` (Hypothesis) · `test_operation_invariants.py` ·
  `test_metamorphic.py` · `test_determinism.py` · `test_embedded_contracts.py`.
  Promote `test_geometry_validation.py` component/watertight checks to hard
  failures.
- ~~`test_assembly_contracts.py`~~ Shipped 2026-07-11 (§5, Tier 4): synthetic
  coverage for the new `no_overlap` no-interpenetration engine plus an
  independent hand-verification pass over the Tier 4 corpus's relational
  claims — deliberately does not duplicate `test_embedded_contracts.py`'s
  generic discovery sweep, which already checks every `expect: relations:`/
  `no_overlap:` block with no per-example code required.
- ~~`test_negative_contracts.py`~~ Shipped 2026-07-11 (§5, Tier 5): one class per
  negative fixture asserting the specific typed `TiaCADError` subclass and
  message it raises, plus a cross-cutting parametrized test that every fixture
  raises *some* `TiaCADError` (never a bare/builtin exception, never a silent
  parse). See §5's Tier 5 entry for the two real gaps found and fixed while
  building it.

**CI edits:**

- ~~`example-validation.yml` → contract check, not parse check.~~ Deleted
  2026-07-10 (was broken by upload-artifact@v3 deprecation, added no signal).
- ~~`visual-regression.yml` → fail (don't generate) on missing refs.~~ Done
  2026-07-10 (section 4.5b).
- Add schema-conformance + schema-truth checks; make contracts a required gate.

**Housekeeping:**

- ~~Implement or delete the `validation:` schema block; fix `schema_version`
  drift.~~ Done: schema block confirmed nonexistent 2026-07-11 (superseded by
  `expect:`); `schema_version` drift fixed 2026-07-10, verified 2026-07-11.
  ~~Unify the two pytest configs into one.~~ Done 2026-07-10: a legacy
  `pytest.ini` was silently shadowing `[tool.pytest.ini_options]` in
  `pyproject.toml` (pytest.ini wins when both exist), so the pyproject block —
  including its `testpaths` and partial marker list — was dead. `pytest.ini`
  removed; its full marker set + `console_output_style` folded into
  `pyproject.toml`. Collection verified identical (1588/1655, 67 deselected).
- ~~**Delete or archive `fix_pattern_api.py`.**~~ Done 2026-07-10: moved from
  the repo root to `scripts/migrations/fix_pattern_api.py` with a dated
  `scripts/migrations/README.md` warning that it does in-place, no-backup
  rewrites of `examples/*.yaml`. The two doc references (MIGRATION_GUIDE_V3,
  API_DEPRECATION_STRATEGY) were repointed to the new path.
- ~~**Establish one source of truth for test health.**~~ — **shipped
  2026-07-11**: `scripts/generate_test_status.py` parses junit-xml +
  coverage.xml into a committed `TEST_STATUS.json`; `tests.yml`'s python-3.11
  leg generates and (on push to `main`) commits it back to the repo. Stop
  hand-writing test counts into markdown — check `TEST_STATUS.json` instead.
  ~~Retire or clearly date-stamp the stale `CODE_QUALITY_SUMMARY.md` /
  `SKIPPED_TESTS_AUDIT.md`.~~ Done 2026-07-11: both moved to `docs/archive/`
  (a 2026-07-11 doc-coherence pass) — their skip classifications and quality
  snapshot predate Phase 0's skip→hard-failure work and were actively
  misleading.
- **Note on differential testing:** ~90% of geometry code bypasses the
  `GeometryBackend` abstraction and calls CadQuery directly, so the fast
  `MockBackend` can't stand in for most tests and true differential testing
  (kernel-vs-kernel) is currently impossible. Routing new operation code through
  the backend is a prerequisite for the strongest oracle of all — a second
  independent kernel to cross-check against.
- **Dependency posture modernized + CAD kernel unified (shipped 2026-07-10).**
  The old `>=` floors (numpy>=1.21 from 2021, cadquery>=2.6, scipy>=1.9,
  pyvista>=0.43) predated both the numpy-2 API split and the current OCCT
  kernel — they no longer described what CI tested. Raised across
  `requirements.txt` + `pyproject.toml` to the real tested baseline
  (cadquery>=2.8, numpy>=2.0, scipy>=1.13, etc.), and `requires-python` bumped
  to `>=3.11`. This **resolves the CI kernel split**: the old matrix ran
  cadquery 2.7 / OCP 7.8 on the 3.10 leg but 2.8 / OCP 7.9 on 3.11+3.12 —
  every leg now shares OCP 7.9. New matrix is 3.11/3.12/3.13 (the full
  dependency tree — nlopt, casadi, cadquery-ocp — has cp313 wheels). Validated
  end-to-end in a `python:3.13-slim` container against the newest resolvable
  set (cadquery 2.8.0, OCP 7.9.3.1.1, numpy 2.4.6, scipy 1.18): full non-visual
  suite `1588 passed`. That validation also surfaced that CI relied on the
  runner image's *incidental* fonts for OCCT text rendering — both workflows
  now install `fontconfig` + `fonts-liberation` explicitly (the sketch text
  default is "Liberation Sans"), so text tests don't depend on that luck.
  **Shipped 2026-07-18:** `requirements-lock.txt` — `pip-compile`-generated
  exact-version pins for the Python 3.12 CI leg, verified end-to-end (clean
  3.12 venv, installed from the lockfile, full targeted contract-suite run
  green). `tests.yml`'s 3.12 leg now installs from the lockfile instead of
  resolving fresh; the 3.11 (coverage/TEST_STATUS.json) and 3.13 legs still
  resolve from `requirements.txt` floors, preserving the cross-version
  compatibility signal those two legs exist for. Regenerate the lockfile on
  review — instructions in its header comment.

---

## 6. Suggested sequencing

**Phase 0 — Stop the bleeding (hours):** turn skips into failures and make the
required test deps non-optional in CI (4.5). Until the safety net is guaranteed
to *run*, every other number is unreliable. This is the cheapest, highest-value
change in the whole plan.

**Shipped 2026-07-10:** the `HAS_TRIMESH`-gated skips in
`test_geometry_validation.py`, the module-level `lib3mf`-missing skip and its
16 per-test `except ThreeMFExportError: skip` fallbacks in
`test_threemf_integration.py`, and the parse/build-failure and
missing-example skips in `test_visual_regression.py` /
`test_threemf_integration.py` are now hard failures — all three deps
(`trimesh`, `lib3mf`, `jsonschema`) are `pyproject.toml`/`requirements.txt`
required dependencies, so an import failure is a broken environment, not an
optional feature. `tests.yml` also gained an explicit import-guard step that
fails CI immediately if any required dependency can't import, rather than
letting it degrade silently into downstream skips. Not yet done: 4.5b (CI
validation-gap fixes — `example-validation.yml` still only parses, and
`visual-regression.yml` still self-generates missing references) and the rest
of Phase 1.

**Phase 1 — Foundations (days, high yield):** metamorphic suite (4.3, shipped),
determinism gate (4.4, shipped), CI validation-gap fixes (4.5b, shipped),
schema reconciliation (4.8, shipped 2026-07-10). **Phase 1 complete.** No new
infrastructure; immediate strengthening.

**Phase 2 — The keystone (1–2 weeks): complete.** Embedded `expect:` contracts (4.1,
shipped) + Hypothesis property tests (4.2, shipped 2026-07-10) + T0/T1 ladder corpus
(shipped 2026-07-11, §5) + `expect:` contracts seeded for every example with a
Tier-2 pytest class — 50 models now discovered and checked by
`test_embedded_contracts.py` (shipped 2026-07-11). *Adding a validated model is now
trivial* — a model + five lines of `expect:`, no bespoke pytest class required —
which was the "easier" half of the mandate. **Phase 2 fully complete 2026-07-11:**
the now-redundant subset of hand-written Tier-2 pytest classes has been trimmed
(see §4.1's 2026-07-11 "Shipped (trim)" note) — 14 classes deleted outright, 7
more partially trimmed, 39 test methods removed, no regressions.

**Phase 3 — Depth: Tier 3 and Tier 4 shipped 2026-07-11 (§5).** Connectivity gate
(4.6, shipped 2026-07-10) + composite-part ladder corpus (Tier 3, 4 models, §5) +
`test_geometry_validation.py`'s `expect: components:`-style hard connectivity gate
extended to the two Tier-3-adjacent examples (`mounting_plate_with_bolt_circle`,
`lego_brick_2x1`) that previously only asserted watertight/mesh-island counts. Found
and fixed a real dimensional bug in the process (KNOWN_LIMITATIONS.md #10). The
assembly ladder (Tier 4, §5) followed: 3 new relational models plus a full
`expect: relations:` contract on `hardware_assembly_demo.yaml`, a new `no_overlap`
no-interpenetration contract-engine check, and a real screw/bolt head-position bug
found and fixed (KNOWN_LIMITATIONS.md #11). **Tier 5 (negative-input corpus)
shipped 2026-07-11 (§5): 6 intentionally-broken `.tiacad` models, each verified
by actually running it and asserting the specific typed `TiaCADError` it
raises, plus two small input-validation gaps found and fixed in the process
(message-less negative-dimension errors; silently-clobbered duplicate part
names — KNOWN_LIMITATIONS.md #12). This was the last unchecked item on the
§5 ladder-corpus checklist — the full T0→T5 confidence ladder described in
section 3 is now shipped end-to-end.** Still open (deliberately out of this
ladder's scope): trust-gallery sign-off (4.7), golden STEP set (4.9).

---

## 7. Anti-goals (what *not* to do)

- **Don't chase pixel-perfect visual regression.** It is a weak oracle; invest in
  math, keep pixels for gross-change detection and human/AI review only.
- **Don't add a golden without an oracle.** Every stored number or mesh must
  trace to a formula or an explicit, reviewed sign-off — otherwise you are
  canonizing whatever ran first.
- **Don't optimize coverage %.** 92% line coverage already coexists with the
  correctness gap. Coverage measures *executed*, not *verified*.
- **Don't let the schema drift again.** If it is declared, it is tested; if it is
  not implemented, it is deleted.
- **Never let a skip stand in for a pass.** A skipped printability check on a
  disconnected body is more dangerous than a red X, because it reads as green.
  Skips are for genuinely optional local tooling — never for the correctness net
  in CI.
- **Don't trust `is_watertight` as a single-solid check,** and don't trust
  `trimesh.split()` island counts as a body count. Use kernel-level solids.

---

## Appendix — analytic formulas (the Tier-0/1 oracle kit)

| Shape / op | Volume | Surface area |
|---|---|---|
| Box `w×h×d` | `w·h·d` | `2(wh + wd + hd)` |
| Cylinder `r,h` | `π·r²·h` | `2πr·h + 2πr²` |
| Sphere `r` | `4/3·π·r³` | `4π·r²` |
| Cone `r,h` | `1/3·π·r²·h` | `πr(r + √(r²+h²))` |
| Torus `R,r` | `2π²·R·r²` | `4π²·R·r` |
| N-gon prism `N,s,h` | `¼·N·s²·cot(π/N)·h` | perimeter·h + 2·base |
| Revolve (Pappus) | `2π·d_centroid·A_profile` | — |
| Union | `V(A)+V(B)−V(A∩B)` | — |
| Difference | `V(A)−V(A∩B)` | — |
| Uniform scale `k` | `×k³` | `×k²` |
| Rigid transform | invariant | invariant |
