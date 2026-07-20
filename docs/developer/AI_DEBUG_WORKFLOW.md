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

## Debug Bundle Artifacts

For AI-assisted debugging, TiaCAD emits a compact, machine-readable bundle per build via
`tiacad debug model.yaml --bundle out/`:

- `manifest.json`
- `resolved_model.json`
- `build_trace.json`
- `part_summaries.json`
- `validation_report.json`
- `trust_render_manifest.json`
- `final_trust.png` when trust rendering succeeds
- `compare_report.json` when `--compare PREVIOUS_BUNDLE` is used

This is the preferred input packet for AI-assisted review — see [MODEL_VALIDATION.md](MODEL_VALIDATION.md#ai-review-rules).

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
- `summary_text`: a one-line human-readable description (e.g. `box (depth=30, height=20, width=10)`,
  `boolean: base, lid -> assembly`) — shipped in `build_trace.json` for quick skimming without
  parsing each node's raw `spec`

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

## Shipped Since This Doc Was Written

The two highest-leverage items originally proposed below are done — noted here
so this doc stops telling AI readers a capability doesn't exist when it does:

- **Model-local contracts**: `expect:` blocks in YAML (`final`, `volume`, `bbox`,
  `watertight`, `components`, `relations`, `no_overlap`, `tol`), evaluated by
  `tiacad verify` (CI-friendly, non-zero exit on failure) and `tiacad check
  --contract`. See [MODEL_VALIDATION.md](MODEL_VALIDATION.md) and
  `docs/developer/VALIDATION_STRENGTHENING.md` §4.1 for the authoring workflow
  (`tiacad audit --write-contract` seeds the block from a reviewed build).
- **Negative trust scenarios**: `examples/validation/negative/` holds
  intentionally-broken models (contradictory constraints, disconnected
  assemblies, etc.) that must fail validation — proving the validators catch
  real mistakes, not just that positive examples build.

## Roadmap: Not Yet Implemented

Highest-leverage remaining work, roughly in priority order:

### 1. Named Reference Promotion

Encourage models to expose stable, meaningful named references:

- `left_arm_tip`
- `neck_slot_center`
- `beam_axis`
- `mount_plate_top`

AI and tests both work better when important geometry has stable names.

### 2. Build Diff Support (partially shipped)

`debug --compare PREVIOUS_BUNDLE` already emits `compare_report.json` with
changed/added/removed parts and operations between two bundles — the
node-level diff this item originally asked for. Still missing: exposing the
DAG/incremental builder's own dirty/rebuilt/cached-node classification (from
`tiacad watch`) as part of that report, so an AI can distinguish "this node
was recomputed" from "this node's output changed."

### 3. Render Command Should Surface Validation Issues, Not Just Annotate Them

`tiacad render` already runs `AssemblyValidator` and passes issues into the
trust-render annotator (so failures get plotted at their `world_position`),
but it never prints a text summary the way `tiacad debug` does. An agent
running `render` alone for a quick look can get a PNG for a build that failed
validation with no console indication anything is wrong — see
`tt show TCAD-UX-7`. Fix: print the same `N errors, N warnings` line `debug`
prints, not just draw markers on the image.

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
