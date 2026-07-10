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

TiaCAD has a large, healthy test suite (~1405 passing), but most of it proves the
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

### 4.3 — Metamorphic suite *(stronger)*

The self-contained subset of 4.2 that needs *no* generators: translate/rotate
conservation, scale `k³`, union commutativity/idempotency, mirror symmetry,
boolean self-consistency. A dozen assertions that would have caught most historic
geometry bugs. Ship even before Hypothesis. **Effort:** low.

### 4.4 — Determinism gate + reviewed mesh-hash goldens *(stronger + de-flakes)*

Implement Tier 2. Add a `test_determinism.py` that fails on non-reproducible
builds, and a small `golden_hashes.json` that is *only* updated by an explicit,
reviewed command. This both hardens correctness and stabilizes every other
golden-based test. **Effort:** low.

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

### 4.5b — Fix the CI validation gaps *(stronger, closes G3)*

- **`example-validation.yml`:** replace the parse-only
  `validate_examples.py` with `tiacad check --contract examples/**` (or run the
  embedded-contract pytest). Parsing is not validation.
- **`visual-regression.yml`:** **stop auto-generating missing references in CI.**
  A missing reference should *fail* and require an intentional, reviewed
  regeneration — never a silent canonization of a fresh render.
- Make manifold/watertight and the contract suite **required** checks for merge.

**Effort:** low (workflow edits). **Payoff:** the "validation" workflows finally
validate.

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

- `T0_*` primitives (6) · `T1_*` single ops (9) · `T3_*` composites (4) ·
  `T4_*` assemblies (4) · `negative/*` broken inputs (~6).

**New scripts / CLI:**

- `expect:` contract engine + `tiacad check --contract` and
  `tiacad audit --write-contract`.
- Implement the four stubbed feature-detection / connectivity helpers.

**New tests** (`test_correctness/`):

- `test_primitive_invariants.py` (Hypothesis) · `test_operation_invariants.py` ·
  `test_metamorphic.py` · `test_determinism.py` · `test_embedded_contracts.py` ·
  `test_negative_contracts.py`. Promote `test_geometry_validation.py` component/
  watertight checks to hard failures.

**CI edits:**

- `example-validation.yml` → contract check, not parse check.
- `visual-regression.yml` → fail (don't generate) on missing refs.
- Add schema-conformance + schema-truth checks; make contracts a required gate.

**Housekeeping:**

- Implement or delete the `validation:` schema block; fix `schema_version` drift;
  unify the two pytest configs into one.
- **Delete or archive `fix_pattern_api.py`.** It is a completed one-off migration
  that does in-place, no-backup, no-dry-run regex overwrites of every
  `examples/*.yaml`. Orphaned at repo root, it is exactly the tool that gets
  re-run by mistake. Move to `scripts/migrations/` with a dated README, or remove.
- **Establish one source of truth for test health.** Have CI emit the pass/skip/
  fail counts as a committed badge or `TEST_STATUS.json`; stop hand-writing test
  counts into six different markdown files. Retire or clearly date-stamp the
  stale `CODE_QUALITY_SUMMARY.md` / `SKIPPED_TESTS_AUDIT.md`.
- **Note on differential testing:** ~90% of geometry code bypasses the
  `GeometryBackend` abstraction and calls CadQuery directly, so the fast
  `MockBackend` can't stand in for most tests and true differential testing
  (kernel-vs-kernel) is currently impossible. Routing new operation code through
  the backend is a prerequisite for the strongest oracle of all — a second
  independent kernel to cross-check against.

---

## 6. Suggested sequencing

**Phase 0 — Stop the bleeding (hours):** turn skips into failures and make the
required test deps non-optional in CI (4.5). Until the safety net is guaranteed
to *run*, every other number is unreliable. This is the cheapest, highest-value
change in the whole plan.

**Phase 1 — Foundations (days, high yield):** metamorphic suite (4.3),
determinism gate (4.4), CI validation-gap fixes (4.5b), schema reconciliation
(4.8). No new infrastructure; immediate strengthening.

**Phase 2 — The keystone (1–2 weeks):** embedded `expect:` contracts (4.1) +
Hypothesis property tests (4.2). Migrate the existing Tier-2 pytest classes to
`expect:` blocks; build the T0/T1 ladder corpus. After this, *adding a validated
model is trivial*, which is the "easier" half of the mandate.

**Phase 3 — Depth (as needed):** connectivity gate (4.6), trust-gallery sign-off
(4.7), composite/assembly ladder (Tiers 3–4), golden STEP set (4.9).

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
