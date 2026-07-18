# TiaCAD Model Validation Model

How TiaCAD should prove, review, and debug model correctness.

This document is the conceptual companion to [TESTING_GUIDE.md](TESTING_GUIDE.md)
and [AI_DEBUG_WORKFLOW.md](AI_DEBUG_WORKFLOW.md). The testing guide explains how
to run and write tests. This document explains what counts as evidence that a
generated model is correct.

---

## Core Principle

Do not rely on any single signal.

Correctness in TiaCAD should be reviewed as a stack of independent evidence:

1. **Schema and parser checks** prove the YAML shape is accepted and interpreted.
2. **Analytical contracts** prove dimensions, volumes, positions, and relationships.
3. **Mesh checks** prove output geometry is usable enough for downstream workflows.
4. **Visual artifacts** help humans and AI catch spatial mistakes.
5. **Debug bundles and deltas** explain what changed and where it changed.

Visual review is important, but it is never the oracle by itself. A render can
look plausible while a hole, offset, angle, or boolean result is wrong.

---

## Evidence Layers

| Layer | Primary Question | Current Mechanism | Limits |
|---|---|---|---|
| Schema | Is the YAML structurally valid? | `tiacad-schema.json`, `--validate-schema` | Cannot prove geometry intent |
| Parser/build | Did the model build through the expected path? | parser/unit tests, build trace | Can build wrong-but-plausible geometry |
| Analytical geometry | Do measured facts match known intent? | `test_correctness/`, trust contracts, example contracts | Requires explicit expected values |
| Mesh validity | Is the tessellated result usable? | geometry summary, validation rules, trimesh checks | Mesh validity is not design correctness |
| Visual review | Does the spatial result look right from multiple views? | trust renderer, visual regression | Snapshot baselines can preserve old bugs |
| Delta review | What changed from the prior known-good build? | `tiacad debug --compare` | Needs a meaningful prior bundle |

Use the strongest available layer for the question at hand. For example,
boolean volume formulas are stronger than screenshots; screenshots are stronger
than silence when an assembly relationship has no contract yet.

---

## Existing Validation Surfaces

### Correctness Tests

`tiacad_core/tests/test_correctness/` is the main deterministic correctness net.
It includes:

- primitive dimensions and volumes
- boolean volume relationships
- transform and rotation checks
- attachment/positioning checks
- example-specific contracts
- trust scenario contracts

These tests should assert facts derived from design intent or independent math,
not snapshots of current output.

### Trust Scenarios

`examples/trust/` contains curated operation-focused YAML files. Each trust file
should be understandable as a small correctness specimen:

- metadata explains what should be verified
- geometry is simple enough for analytical expectations
- `test_trust_contracts.py` translates that intent into numeric assertions
- `trust_output/*.png` gives a human/AI visual review artifact

Trust scenarios are the preferred place to validate new primitives, operations,
and subtle geometry fixes.

### Example Contracts

`test_example_contracts.py` covers larger examples where the intent is less
minimal than a trust scenario but still measurable. These tests should focus on
user-visible guarantees:

- final bounding dimensions
- volume ranges
- known part placement
- expected watertightness or component behavior
- assembly relationships that matter to the example

### Debug Bundles

`tiacad debug` writes machine-readable artifacts for review:

- `resolved_model.json`
- `build_trace.json`
- `part_summaries.json`
- `validation_report.json`
- `trust_render_manifest.json`
- `final_trust.png` when rendering succeeds
- `compare_report.json` when `--compare` is used

This is the preferred packet for AI-assisted review. AI should inspect these
facts first and use images as supporting evidence.

---

## How To Review A Model

For a new or changed model, review in this order:

1. **Build it** with normal parser/schema checks when appropriate.
2. **Measure the final/default part**: extents, center, volume, mesh facts.
3. **Check explicit relationships**: contact, alignment, symmetry, clearance.
4. **Inspect the trust render** for spatial mistakes that have no contract yet.
5. **Compare against a prior debug bundle** when reviewing a regression.
6. **Promote repeated manual checks into contracts** once intent is clear.

Do not stop at "the PNG looks fine" for important examples. If the expected
behavior can be stated numerically, add a contract.

---

## Good Contracts

Good contracts are independent, stable, and explainable.

Examples:

```python
assert dims["width"] == pytest.approx(100.0, abs=0.1)
assert final_volume < solid_plate_volume
assert final_volume > plate_volume
assert left_tip_z == pytest.approx(right_tip_z, abs=0.1)
assert shaft_axis_angle < 0.1
assert mesh_summary["watertight"] is True
```

Prefer contracts based on:

- parameter values from the YAML
- closed-form geometry formulas
- invariants such as symmetry, monotonicity, or volume preservation
- named references that encode design intent

Avoid contracts that simply freeze accidental output. If a value comes from the
current implementation rather than from intent, document why it is still useful.

---

## Metamorphic Tests

Metamorphic tests are especially valuable because they prove invariants without
requiring one exact golden answer.

Useful invariants:

- translate preserves volume and surface area
- rotate preserves volume and surface area
- uniform scale changes volume by `scale^3`
- mirror twice returns equivalent bounds
- one-instance pattern equals the original part
- boolean subtract cannot increase volume
- boolean union volume cannot exceed the sum of inputs
- changing one parameter only changes the expected dependent dimensions

Add these when implementing shared operations or fixing geometry bugs.

---

## Visual Review Rules

Use visual artifacts to catch what numbers do not yet express:

- wrong side of a plate
- inverted orientation
- unexpected part overlap
- missing part in an assembly
- disconnected geometry that still has plausible dimensions

But visual artifacts should be strengthened with overlays when possible:

- named dimensions
- part callouts
- reference points and axes
- failed contract labels
- before/after ghosting or image diffs

Visual regression protects against unexpected change. It does not prove the
baseline was correct.

**Visual review is weakest at absence.** A render is good at "this looks wrong" and
bad at "something that should be here is missing" — a solid plate with no holes looks
exactly like a correct plate. Do not rely on a picture for presence/absence
guarantees (a hole exists, a part is connected, a cut removed material); assert those
numerically. See [VALIDATION_CASE_STUDY_MOUNTING_HOLES.md](VALIDATION_CASE_STUDY_MOUNTING_HOLES.md),
where a render prompted suspicion but only measured facts proved the missing holes.

---

## AI Review Rules

AI reviewers should receive structured evidence, not just screenshots.

Best input packet:

1. changed YAML or code
2. `resolved_model.json`
3. `build_trace.json`
4. `part_summaries.json`
5. `validation_report.json`
6. `compare_report.json` when available
7. trust render paths

AI should be asked to:

- identify the first suspicious changed node
- compare measured values against stated contracts
- explain failed validation results
- suggest likely source edits
- propose missing contracts after manual review

AI should not be asked to declare final correctness from a render alone.

---

## Best Next Improvements

These are the highest-value improvements to the current validation model:

1. ~~**Boolean-effect assertions**~~ **Shipped 2026-07-10:** `BooleanEffectRule`
   (`tiacad_core/validation/rules/boolean_effect_rule.py`) checks, on every model, with
   no per-model contract to write: every `difference` must remove measurable volume
   from its base; every `intersection` must be non-empty; a `union`'s result cannot be
   smaller than its largest input. Runs as part of `AssemblyValidator` — flows into
   `validation_report.json` automatically via the existing debug-bundle pipeline. This
   is the check that would have caught the
   [mounting-hole bug](VALIDATION_CASE_STUDY_MOUNTING_HOLES.md) — and did in fact catch
   a second, previously-unknown instance of the same bug class in
   `guitar_hanger_named_points.yaml` the same session it was added (also fixed;
   `plate_with_holes`'s screw holes were floating above the plate the same way).
   Known gap: the `union` check is a whole-result sanity check, not per-input — a union
   input that fully overlaps an already-placed part (contributing nothing) will not be
   flagged. See `tiacad_core/tests/test_validation/test_boolean_effect_rule.py`.
2. ~~**Model-local contracts**~~ **Superseded — shipped as the `expect:`
   contract engine** (`tiacad_core/testing/contracts.py`,
   VALIDATION_STRENGTHENING.md section 4.1): examples and user models declare
   expected volume, bbox, component count, watertightness, and named-part
   relations (flush faces, coaxial axes) directly in YAML. This item as
   originally scoped ("declare expected dimensions/volumes/clearances/
   symmetry/mesh facts") is fully covered.
3. ~~**`tiacad verify`**~~ **Shipped 2026-07-18:** evaluates a model's
   `expect:` contract and emits a concise console summary plus, with `--json`,
   a machine-readable result (`ok`/`part_name`/`violations`) for CI/tooling.
   See [CLI.md](CLI.md) ("tiacad verify"). Sibling of the pre-existing
   `check --contract` (same underlying
   `check_contract()`) but single-purpose and CI-exit-code-friendly. 5 tests
   in `test_cli/test_cli_verify.py`.
4. **Reference-based measurements:** measure distances, angles, and alignments
   between named references such as `plate.face_top` and `shaft.axis_z`.
5. **Stepwise summaries:** attach before/after summaries to operations in
   `build_trace.json` so regressions are easier to localize.
6. **Annotated trust renders:** render failed contracts and named references
   directly onto review images — so a picture *points at* a measured failure instead
   of asking a human to notice it cold.
7. **Negative trust scenarios:** keep intentionally bad models that must fail
   validation, proving validators catch real mistakes.

These improvements all reinforce the same pattern: TiaCAD computes facts and
contracts; humans and AI interpret the evidence.

**Worked example:** [VALIDATION_CASE_STUDY_MOUNTING_HOLES.md](VALIDATION_CASE_STUDY_MOUNTING_HOLES.md)
walks a real committed-example defect end to end — how it was found (render
suspicion → numeric proof → volume-delta confirmation), why the tests missed it, and
why boolean-effect assertions are the fix for the whole class.
