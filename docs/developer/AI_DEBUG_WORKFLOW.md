# AI Debug Workflow

Practical guidance for making TiaCAD easier for agentic AI systems to inspect, test, and debug during iterative model development.

This document does not assume full semantic understanding of the model. The goal is narrower:

- make build behavior easier to observe
- make geometry changes easier to compare
- make failures easier to localize
- give AI systems structured artifacts instead of only raw YAML or a final mesh

---

## Why This Matters

Agentic AI is much better at:

- comparing structured facts across iterations
- noticing regressions in measured outputs
- explaining why a contract failed
- narrowing suspicious operations in a build graph

Agentic AI is much worse at:

- inferring full design intent from a final solid alone
- proving functional correctness from one screenshot
- reconstructing a modeling mistake from only final geometry

So the TiaCAD workflow should optimize for explainability and intermediate visibility.

---

## Core Principle

Do not ask AI to infer everything from the final model.

Instead, emit enough intermediate information that the AI can reason over:

1. what changed
2. which operation introduced the change
3. whether the result still satisfies explicit contracts
4. what geometry facts are true at each step

This is the difference between:

- "Here is the hanger. Does it look right?"

and:

- "Operation `left_arm_rotate` changed the final opening width from `48.2mm` to `33.4mm`, reduced the tip retention height from `6.1mm` to `1.4mm`, and moved the left arm top-face normal from `[0, 0, 1]` to `[0.42, 0, 0.91]`."

The second form is far more tractable.

---

## Recommended Debug Artifacts

For AI-assisted debugging, TiaCAD should emit a compact, machine-readable bundle per build.

### 1. Resolved Model Snapshot

A normalized form of the input after:

- imports are resolved
- parameters are resolved
- aliases are normalized
- defaulted fields are filled where appropriate

Useful outputs:

- resolved YAML or JSON
- resolved imports and namespaces
- final export configuration

This gives the AI the exact model that was built, not the user-authored shorthand.

### 2. Build Trace

A stepwise record of part creation and operations.

For each node or step, include:

- node name
- node type (`part`, `operation`)
- operation type
- input dependencies
- resolved parameters
- output part names
- whether the node was rebuilt or cached

This is the most important artifact for iterative debugging.

### 3. Per-Step Geometry Summary

For each output part, compute a small structured summary.

Recommended fields:

- bounding box
- center
- volume
- surface area if available
- connected-component count
- backend identity
- visible reference points / face normals where available

This should be cheap to compare across iterations.

### 4. Geometry Delta Summary

When a model changes, emit differences relative to the previous build.

Recommended fields:

- changed nodes
- changed final/default part
- bbox delta
- center delta
- volume delta
- connectivity delta
- new/removed parts

This helps AI answer "what changed?" without re-deriving the whole model.

### 5. Trust Images

Save visual outputs alongside the structured summaries.

Recommended outputs:

- final trust render
- optionally, stepwise renders for changed downstream nodes
- optional image diff against previous build or baseline

AI can use images as a secondary signal, not the primary source of truth.

### 6. Validation Report

Emit explicit, structured rule results.

Recommended fields:

- rule name
- pass/fail/warn
- measured values
- threshold/expected values
- implicated parts
- implicated operation if known
- short explanation

Prefer JSON output over plain console text.

---

## Most Valuable Near-Term Improvements

These are the highest-leverage additions for TiaCAD.

### A. Stepwise Geometry Summaries

Implement a reusable summary function for any `Part`:

- `bounds`
- `center`
- `volume`
- `surface_area`
- `component_count`
- `reference_normals`

This supports tests, validation, watch mode, and debug bundles.

### B. Build Diff Support

The DAG and incremental build system already know which nodes changed.

Expose that as a debug artifact:

- dirty nodes
- rebuilt nodes
- cached nodes
- first node whose output summary changed

This gives AI a natural fault-localization path.

### C. Debug Bundle Command

Add a command such as:

```bash
tiacad debug model.yaml --bundle out/
```

Suggested bundle contents:

- `resolved_model.json`
- `build_trace.json`
- `part_summaries.json`
- `compare_report.json` when prior bundle exists
- `validation_report.json`
- `trust_render_manifest.json`
- `final_trust.png`

This would be the best single addition for AI-assisted workflows.

Status:

- `2026-04-18`: MVP implemented as `tiacad debug`
- Current bundle files:
  - `manifest.json`
  - `resolved_model.json`
  - `build_trace.json`
  - `part_summaries.json`
  - `validation_report.json`
  - `trust_render_manifest.json`
  - `final_trust.png` when trust rendering succeeds
  - `compare_report.json` when `--compare PREVIOUS_BUNDLE` is used

Still missing for the fuller workflow:

- richer node-level diffing beyond parts/operations
- changed-node summaries
- incremental rebuild dirty-node integration
- automatic render diffs
- changed-node trust renders

### D. Named Reference Promotion

Encourage models to expose stable, meaningful named references.

Examples:

- `left_arm_tip`
- `neck_slot_center`
- `beam_axis`
- `mount_plate_top`

AI and tests both work better when important geometry has stable names.

### E. Lightweight Contracts

Support small assertions that are easy to evaluate and explain.

Good examples:

- part dimensions in range
- opening width in range
- parts aligned on an axis
- final assembly has one connected component
- selected face normal within angle tolerance
- left/right features symmetric within tolerance

These are much more realistic than asking AI to infer full functional intent.

### F. Model-Local Contracts

The next useful step is to let models declare their own reviewable intent:

```yaml
contracts:
  final_assembly:
    extents: {x: 100, y: 80, z: 12, tolerance: 0.2}
    watertight: true
    component_count: 1
  mounting_hole:
    diameter: 3.2
    coaxial_with: screw.axis_z
```

This would let a future `tiacad verify` command evaluate contracts and emit:

- pass/fail/warn status
- measured values
- expected values and tolerances
- implicated parts/references
- optional annotated trust render callouts

Model-local contracts are especially useful for AI review because the intent
travels with the YAML instead of living only in a Python test file.

### G. Negative Trust Scenarios

Keep a small set of intentionally broken trust models that must fail validation:

- disconnected assembly
- missing boolean cut
- wrong revolve axis
- mirrored part on the wrong side
- imported component floating at origin
- clearance below required minimum

Positive examples prove TiaCAD can build valid models. Negative examples prove
the validators catch real mistakes.

---

## What AI Should Receive

An agentic AI should ideally receive:

1. the resolved model
2. the build trace
3. the final part summary
4. changed-node summaries
5. validation results
6. trust render paths
7. declared contracts when available

That is enough for useful workflows like:

- identify which operation introduced the regression
- explain which measurable property changed
- propose a likely corrective edit
- compare current build against prior successful build
- propose missing contracts after manual review

---

## Example Workflow

User edits a guitar hanger model and says "the arms look wrong now."

TiaCAD should make this workflow possible:

1. Rebuild incrementally.
2. Report dirty and rebuilt nodes.
3. Emit summaries for changed nodes and final part.
4. Compare against prior build:
   - opening width changed
   - arm tip height changed
   - left/right symmetry broken
5. Emit updated trust render.
6. Let AI say:
   - which operation likely caused the change
   - which measured constraints are now failing
   - what to inspect next

Without these artifacts, the AI is forced to reason from the final shape alone.

---

## Implementation Order

Recommended order of work:

1. Add reusable geometry-summary helpers for `Part`
2. Add JSON validation/report output
3. Expose incremental rebuild node-change metadata
4. Add `tiacad debug --bundle`
5. Add optional stepwise trust renders
6. Add lightweight contract assertions tied to named references
7. Add model-local `contracts:` and `tiacad verify`
8. Add negative trust scenarios

Status:

- `2026-04-18`: initial reusable summary helpers added in `tiacad_core.testing.geometry_summary`
- `2026-04-18`: `tiacad debug` implemented with resolved model, build trace, part summaries, validation report, and trust render manifest
- `2026-04-18`: `tiacad debug --compare PREVIOUS_BUNDLE` implemented for bundle comparison

This ordering gives value early and reuses the same data across testing, watch mode, and AI workflows.

---

## Design Guidelines

### Prefer facts over prose

Emit:

- `volume: 18234.2`
- `component_count: 2`
- `left_arm_tip_z: 42.1`

Do not rely on:

- "looks slightly too narrow"
- "probably disconnected"

### Prefer stable identifiers

Use:

- node names
- part names
- reference names
- operation names

AI needs stable handles to compare builds.

### Prefer deltas over full re-analysis

If only three nodes changed, emit detailed summaries for those nodes plus the final part.

### Prefer explainable validation

Every failed check should include:

- what was measured
- what was expected
- what part or node caused it

### Prefer contracts over conclusions

Emit the measurable contract:

- `opening_width_mm: {expected: [45, 55], actual: 33.4, status: "fail"}`

Avoid only emitting:

- "opening looks too narrow"

AI can explain and suggest fixes better when the system provides measurable
facts and lets the AI interpret them.

---

## Non-Goals

This workflow is not trying to:

- make AI infer full product semantics from arbitrary geometry
- replace deterministic validation with LLM judgment
- turn trust rendering into the only testing mechanism

The correct model is:

- TiaCAD computes facts and rule results
- AI helps interpret, compare, explain, and suggest fixes

---

## Summary

The best way to support AI-assisted iterative modeling is not deeper AI.

It is better observability:

- resolved models
- build traces
- geometry summaries
- diffs
- trust renders
- structured validation

If TiaCAD emits those artifacts cleanly, an agentic AI can become a useful debugger and review assistant even without full semantic understanding of the model.
