---
project: tiacad
schema_version: '1.0'
id_prefix: TCAD
next_id: 1
archival: inline
areas:
  VAL: 8
  UX: 7
  API: 2
  ARCH: 9
---

## TASK-TCAD-VAL-1 · CI validation as required gate — make expect: contract checking a required CI gate

```yaml
status: done
priority: high
tags: [validation]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:46:06Z'
session: electric-glaze-0717
links:
  commits:
  - 800075c589ac2ccafc78a9da5ae4a1e8898ac594
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T02:46:06Z session:electric-glaze-0717] Enabled GitHub branch protection on main: 4 CI checks (test x3 Python versions + visual-regression) now required for merge; force-push/deletion blocked. No PR-review requirement (kept direct-push-to-main workflow). Applied via gh api (repo setting, not a workflow file).


## TASK-TCAD-VAL-2 · Differential testing blocked — route geometry code through GeometryBackend so MockBackend/kernel-vs-kernel testing works

```yaml
status: done
priority: high
tags: [validation, architecture]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T20:43:25Z'
session: electric-glaze-0717
links:
  commits:
  - 01b2fe505cf197dac48c22cf919417c2c64bb8af
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T20:43:25Z session:yozove-0718] Shipped via manifold3d as a genuine second kernel, not by routing production code through GeometryBackend as originally titled (MockBackend is a stub, would not have delivered real differential coverage). 12/24 trust models eligible; see VALIDATION_STRENGTHENING.md's differential-testing note.


## TASK-TCAD-VAL-3 · Pinned CI lockfile — exact dependency versions, regenerated on review

```yaml
status: done
priority: medium
tags: [ci]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:52:00Z'
session: electric-glaze-0717
links:
  commits:
  - 4a9b6ecd5d053da6a950fc66db0ef5237dd047d4
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T02:52:00Z session:electric-glaze-0717] Generated requirements-lock.txt via pip-compile against a clean Python 3.12 venv; verified by installing into that venv and running the contract-suite tests (59 passed). Wired tests.yml's 3.12 leg to install from the lockfile; 3.11/3.13 legs unchanged (still resolve from requirements.txt floors, preserving cross-version compat signal).


## TASK-TCAD-VAL-4 · Trust-gallery sign-off and golden STEP set (out of scope for T0-T5 ladder)

```yaml
status: done
priority: medium
tags: [validation]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T20:09:20Z'
session: electric-glaze-0717
links:
  commits:
  - 75874678d66efd188412254c879971a53a5acd55
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T20:09:20Z session:yozove-0718] Golden STEP topology gate + trust-gallery sign-off ledger shipped; also fixed pcb_standoff_assembly axis-swap bug (b2c616a) found during the visual review


## TASK-TCAD-VAL-5 · Curved-geometry watertight false negative on spheres/fillets — switch to BREP-level check (BRepCheck_Analyzer)

```yaml
status: done
priority: high
tags: [validation, bug]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:41:01Z'
session: electric-glaze-0717
links:
  relates_to:
  - TCAD-VAL-2
  commits:
  - 7f48d32675f4554a57fb8ca484ded399174965b4
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T02:41:01Z session:electric-glaze-0717] Replaced STL/trimesh mesh check with BREP-level Shape.isValid() (BRepCheck_Analyzer) in get_manifold_stats(). Fixes false negative on spheres/fillets; verified still catches genuine defects (open-shell test). T0_sphere/T1_fillet now assert watertight: true. 2 new tests.


## TASK-TCAD-UX-1 · Reconcile MODEL_VALIDATION.md item 2 (model-local contracts) against shipped expect: engine

```yaml
status: done
priority: low
tags: [docs]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T04:25:28Z'
session: electric-glaze-0717
links:
  commits:
  - f8132bec0a9402d8a5c763aa8c2efff1c5a8f24c
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T04:25:28Z session:electric-glaze-0717] Reconciled: item 2 (model-local contracts) is superseded by the already-shipped expect: contract engine. Updated MODEL_VALIDATION.md accordingly.


## TASK-TCAD-UX-2 · tiacad verify CLI command — evaluate model-local contracts, emit JSON + console summary

```yaml
status: done
priority: medium
tags: [cli]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T04:25:29Z'
session: electric-glaze-0717
links:
  commits:
  - f8132bec0a9402d8a5c763aa8c2efff1c5a8f24c
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T04:25:29Z session:electric-glaze-0717] Added 'tiacad verify INPUT [--json]' CLI command: evaluates expect: contract, console summary + JSON output, non-zero exit on failure/missing contract. 5 tests in test_cli/test_cli_verify.py. Documented in CLI.md.


## TASK-TCAD-UX-3 · Reference-based measurements CLI/testing utility — distances/angles/alignment between named spatial references

```yaml
status: done
priority: medium
tags: [cli]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T22:12:18Z'
session: electric-glaze-0717
links:
  commits:
  - c9ba0c3cfaea82d2c69eb0906f3618bb40644387
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T22:12:18Z session:vermilion-corona-0718] Shipped tiacad measure CLI: distance/angle/coaxial-alignment between named spatial references, --json for tooling. See docs/developer/CLI.md.


## TASK-TCAD-UX-4 · Stepwise summaries attached to operations in build_trace.json

```yaml
status: done
priority: low
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T22:58:09Z'
session: electric-glaze-0717
links:
  commits:
  - 5dc3b3cd461212b704a8440d0019a5cfa7959589
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T22:58:09Z session:arctic-drizzle-0718] Added summary_text field to each build_trace.json node: parts get 'primitive (key=value, ...)' from declared spec/parameters, operations get 'type: input1, input2 -> output' from already-computed inputs/outputs. Purely additive (no existing fields changed/removed). Verified against real examples (auto_references_box_stack.yaml, simple_guitar_hanger.yaml) and unit-tested (5 new tests for _summarize_part_node/_summarize_operation_node). Docs updated in AI_DEBUG_WORKFLOW.md's Build Trace section.


## TASK-TCAD-UX-5 · Annotated trust renders — point at measured failures directly on the rendered image

```yaml
status: backlog
priority: low
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T02:32:58Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-UX-6 · Negative trust scenarios — intentionally-bad models that must fail visual/trust-render validation

```yaml
status: done
priority: medium
tags: [validation]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T04:30:51Z'
session: electric-glaze-0717
links:
  commits:
  - 09a851cb93003e2a560e91a7bb297478b1230b02
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T04:30:51Z session:electric-glaze-0717] Added examples/validation/negative_trust/ (NT1 mounting-hole regression, NT2 disconnected parts) with 4 tests proving AssemblyValidator's BooleanEffectRule/DisconnectedPartsRule catch real defect classes. First-ever committed regression coverage for DisconnectedPartsRule.


## TASK-TCAD-API-1 · Limited export formats — no DXF/IGES/G-code/SVG (community-driven, add on demand)

```yaml
status: backlog
priority: low
tags: [api]
created: '2026-07-18T02:33:00Z'
updated: '2026-07-18T02:33:00Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-1 · Backend global state — Part/backend selection still falls back to process-global state (get_default_backend/set_default_backend) in parts_builder.py, backend_utils.py

```yaml
status: backlog
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:12Z'
session: electric-glaze-0717
links:
  relates_to:
  - TCAD-VAL-2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-2 · Part coupling hub — part.py (237 lines) is #1 fan-in file in repo (21 importers in tiacad_core/, 59 repo-wide)

```yaml
status: backlog
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-3 · cli.py monolith — #1 quality hotspot (1201 lines, 57 functions, 59/100); create_parser() alone 122 lines

```yaml
status: backlog
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T05:05:22Z'
session: electric-glaze-0717
notes_next: 2
```

cli.py monolith — #1 quality hotspot (1,260 lines, 58 functions); create_parser() alone 132 lines

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T05:05:22Z session:electric-glaze-0717] Numbers refreshed 2026-07-18 (were 1201/57/122 when filed) — this session's tiacad verify addition grew the file further, confirming the direction (still #1 hotspot, needs splitting), just updating the exact counts.


## TASK-TCAD-ARCH-4 · tiacad_core.visual vs tiacad_core.visualization overlap — no canonical-boundary decision documented

```yaml
status: done
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T22:52:03Z'
session: electric-glaze-0717
links:
  commits:
  - 3fa989c89fd88d0c20381dc50f888167a9139751
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T22:52:03Z session:arctic-drizzle-0718] Investigated: real functional overlap (both render CadQuery parts to PNG via PyVista) but not ambiguous in practice — visual.trust_renderer is the sole production path (CLI tiacad debug/trust, debug_bundle.py); visualization.renderer.ModelRenderer has zero production callers, only 2 demo scripts + its own tests. Documented the canonical boundary in both __init__.py docstrings. Also surfaced (not removed): visual_debug.py is dead __main__-guarded example code with no callers anywhere — flagged for a future explicit removal decision, not deleted here.


## TASK-TCAD-ARCH-5 · OperationsBuilder dispatch — execute_operation() routes via 12-branch if/elif on op_type, not a registry

```yaml
status: done
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T21:31:47Z'
session: electric-glaze-0717
links:
  commits:
  - 654d4bbbd42d24a1c1ce406e7bd2ca9b0e692328
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T21:31:47Z session:fuchsia-tint-0718] Replaced if/elif dispatch with a dict in OperationsBuilder.__init__


## TASK-TCAD-ARCH-6 · Parse orchestration hotspot — parse_pipeline.py's parse_tiacad_dict is 110 lines / depth 4 doing 6 distinct jobs

```yaml
status: done
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T22:43:25Z'
session: electric-glaze-0717
links:
  commits:
  - 76eda96f2db9ef900a97b87f63db2c0fcf94c24d
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T22:43:25Z session:arctic-drizzle-0718] Split parse_tiacad_dict (110 lines/6 jobs) into _validate_and_extract_sections, _build_parts_registry, _apply_transforms_and_operations. parse_tiacad_dict now 65-line orchestrator. Full test_parser suite (727 tests) passes, no regressions.


## TASK-TCAD-ARCH-7 · Validation heuristic vs semantic — 5 of 9 assembly validation rule files still lean on bbox/bounds heuristics

```yaml
status: backlog
priority: low
tags: [validation]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-8 · parameter_resolver.py high coupling — 3rd-highest fan-in in repo; _check_cycles() mixes DFS+regex+error formatting (complexity 10, depth 6)

```yaml
status: backlog
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T21:37:06Z'
session: electric-glaze-0717
links:
  commits:
  - fb6d689252041f86b1b1c2c5c6db67b8bfb9e79b
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T21:36:39Z session:fuchsia-tint-0718] Partial progress (fb6d689): split _check_cycles into _extract_dependencies/_find_cycle/_check_cycles, resolving the complexity/depth complaint. Fan-in (3rd-highest importer count) is unaddressed — that's a coupling question needing a broader design decision, not a mechanical split.


## TASK-TCAD-VAL-6 · CI 3.13 leg red: T0_torus.tiacad golden_mesh_hash mismatch (pre-existing, predates this session — confirmed failing on commit 0801822 from 2026-07-11 too). Newly-added branch protection (main) now requires this check, so it silently blocks PR merges until fixed. Root cause: 3.13 leg resolves requirements.txt floors fresh each run, so a CadQuery/OCP point release drifted the torus tessellation hash vs the committed golden_hashes.json baseline -- exactly the kernel-drift scenario test_determinism.py's docstring warns about. Fix: regenerate the torus entry with scripts/update_determinism_goldens.py from a real Python 3.13 env (review the diff -- should touch only T0_torus), or extend the requirements-lock.txt pinning (TCAD-VAL-3) to the 3.11/3.13 legs too so this class of drift can't recur silently.

```yaml
status: done
priority: high
tags: [ci, bug]
created: '2026-07-18T04:51:40Z'
updated: '2026-07-18T06:17:37Z'
session: electric-glaze-0717
links:
  commits:
  - 6bb3c45d783829f554e1c3db230e23e1f2022b21
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T06:17:37Z session:electric-glaze-0717] Fixed via canonical_mesh_hash - point-cloud fingerprint immune to parallel-tessellation triangle-connectivity nondeterminism. Verified on real CI (all 3 legs green).


## TASK-TCAD-VAL-7 · CI job reports failure: TEST_STATUS.json auto-commit-back-to-main step blocked by branch protection (GH006), even though real tests pass

```yaml
status: done
priority: high
tags: [ci, bug]
created: '2026-07-18T06:26:59Z'
updated: '2026-07-18T17:28:49Z'
session: electric-glaze-0717
links:
  commits:
  - a5750d4a3b4c572c8c0616f6539ea9aa9e1a170e
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T17:28:49Z session:electric-glaze-0717] Made TEST_STATUS.json auto-commit best-effort instead of job-fatal — branch protection can never let a same-run commit land, so this was a structural false-failure, not a real test regression. Verified: CI run 29653737936 all 3 legs green.
