---
project: tiacad
schema_version: '1.0'
id_prefix: TCAD
next_id: 5
archival: inline
areas:
  VAL: 19
  UX: 16
  API: 3
  ARCH: 10
  CON: 13
  FIN: 2
  BUG: 6
  DSL: 7
  DOC: 2
  EX: 2
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
status: done
priority: low
created: '2026-07-18T02:32:58Z'
updated: '2026-07-19T06:45:38Z'
session: electric-glaze-0717
links:
  relates_to:
  - docs/developer/MODEL_VALIDATION.md
  commits:
  - 9b938ab822b0cf726b79506e146a95bb3ada720c
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T23:27:10Z session:zatuhipi-0718] Scoped (zatuhipi-0718): tiacad_core/visual/trust_renderer.py (684 lines) already imports PIL ImageDraw and uses it for legend annotations (_draw_parts_legend/_draw_axes_legend/_draw_voids_legend), so image-annotation plumbing exists -- but only for a static legend, not for pointing at a specific failure location on the 3D render. Real gap: ValidationIssue.location (validation_types.py:28) is typed for YAML line:column tracking only, not 3D world coordinates -- rule files compute bboxes/positions internally but don't currently surface a 3D point on the issue object. Implementing this needs (1) rules to attach a 3D failure location, (2) projecting that point through pyvista's active camera transform to a 2D pixel, (3) an ImageDraw arrow/marker at that pixel. Well-defined but nontrivial; low priority is appropriate.
- [#2 2026-07-19T06:24:26Z session:unsettled-storm-0718] Shipped for HoleEdgeProximityRule only; other rules don't yet compute world_position — see MODEL_VALIDATION.md item 6 for scope.
- [#3 2026-07-19T06:45:38Z session:descending-asteroid-0718] Extended world_position coverage to BooleanEffectRule + DisconnectedPartsRule (commit 8de1d2e), via shared ValidationRule._bbox_center/_part_center helper. Now 3 of 9 rules populate world_position; remaining 6 (FeatureBoundsRule, ParameterSanityRule, MissingPositionRule, BooleanGapsRule, UnusedPartsRule, BoundingBoxRule) still don't -- see MODEL_VALIDATION.md item 6.


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
updated: '2026-07-18T23:27:10Z'
session: electric-glaze-0717
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T23:27:10Z session:zatuhipi-0718] Reviewed (zatuhipi-0718): no new scoping needed -- 'community-driven, add on demand' is already the resolution, not a placeholder awaiting a decision. Leave as backlog until a specific export format is actually requested.


## TASK-TCAD-ARCH-1 · Backend global state — Part/backend selection still falls back to process-global state (get_default_backend/set_default_backend) in parts_builder.py, backend_utils.py

```yaml
status: done
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T23:22:48Z'
session: electric-glaze-0717
links:
  relates_to:
  - TCAD-VAL-2
  commits:
  - 02e97e2c6f2d8e4000193b6f671db44e462b93ee
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T22:58:32Z session:arctic-drizzle-0718] Investigated (arctic-drizzle-0718): confirmed this is live in production, not test-only. CLI (cli.py) never passes backend= anywhere, so get_default_backend() IS hit on every CLI run, lazily creating/caching a module-global CadQueryBackend in tiacad_core/geometry/__init__.py's _default_backend. There's a SECOND, separate module-global cache in parser/backend_utils.py (_cadquery_backend) used by 7 CadQuery-native builders (hull/loft/sweep/text/gusset/extrude/revolve builders) via get_cadquery_backend() — its fallback logic re-derives from get_default_backend() first, only using its own cache when the default has been swapped to a non-CadQuery backend (e.g. MockBackend in tests). Only 2 test files mutate the global via set_default_backend/reset_default_backend. A real fix means deciding: (a) keep the singleton-with-test-override pattern as intentional/documented (like visual/visualization ARCH-4 turned out to be), or (b) thread an explicit backend/context object through PartsBuilder + all 7 builders + CLI — a cross-cutting signature change touching every builder module. Did not change code — this is a design call, not a mechanical fix. Recommend scoping (a) vs (b) with Scott before starting.
- [#2 2026-07-18T23:22:37Z session:zatuhipi-0718] Fixed (zatuhipi-0718): threaded the resolved backend from PreparedBuildContext through _apply_transforms_and_operations -> OperationsBuilder -> the 7 sketch-based builders (extrude/revolve/sweep/loft/hull/text/gusset). Each now takes an optional backend param and falls back to get_cadquery_backend()/get_default_backend() only when none is given, mirroring PartsBuilder's existing pattern. Global remains as the CLI-path default (CLI still doesn't pass backend=) -- this was a plumbing gap, not a redesign. Verified end-to-end: explicit backend passed to TiaCADParser.parse_string() is now the exact instance stamped on operation-produced parts (identity-checked against hull_simple.yaml), not a separately-fetched global. test_parser/ (727 passed), test_geometry_backends.py + test_dag/ (144 passed).
- [#3 2026-07-18T23:22:48Z session:zatuhipi-0718] resolving commit


## TASK-TCAD-ARCH-2 · Part coupling hub — part.py (237 lines) is #1 fan-in file in repo (21 importers in tiacad_core/, 59 repo-wide)

```yaml
status: done
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T23:30:19Z'
session: electric-glaze-0717
links:
  commits:
  - ccb255328c775309865a1964699f474e87ede30d
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T23:27:10Z session:zatuhipi-0718] Scoped (zatuhipi-0718): part.py is a small, cohesive dataclass module (237 lines, 17 simple methods -- Part + PartRegistry, mostly getters/bounds/clone). The high fan-in isn't a symptom of the file doing too much; it's the natural result of Part/PartRegistry being the central domain data types every builder and operation touches, similar to a core model class in an app. Recommend closing this as 'investigated, not a defect' (same resolution as ARCH-4) rather than attempting a split -- there's no internal-cohesion problem to fix, and splitting a data model to reduce fan-in just moves the coupling around. Needs Scott's confirmation before closing since it reverses the original framing.
- [#2 2026-07-18T23:30:19Z session:cunning-chimera-0718] Investigated: high fan-in is expected — part.py is the central domain type (Part + PartRegistry), 237 lines / 17 cohesive methods, same resolution class as ARCH-4. Not a defect; closing.


## TASK-TCAD-ARCH-3 · cli.py monolith — #1 quality hotspot (1201 lines, 57 functions, 59/100); create_parser() alone 122 lines

```yaml
status: done
priority: medium
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T23:38:29Z'
session: electric-glaze-0717
links:
  commits:
  - 8d56ca6c9393a79cd4c218999fb954ab3625090c
notes_next: 3
```

cli.py monolith — #1 quality hotspot (1,260 lines, 58 functions); create_parser() alone 132 lines

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T05:05:22Z session:electric-glaze-0717] Numbers refreshed 2026-07-18 (were 1201/57/122 when filed) — this session's tiacad verify addition grew the file further, confirming the direction (still #1 hotspot, needs splitting), just updating the exact counts.
- [#2 2026-07-18T23:38:29Z session:cunning-chimera-0718] Split into tiacad_core/cli/ package: output.py + _common.py (shared helpers) + one module per subcommand (build/validate/info/validate_geometry/check/measure/verify/audit/watch/debug) + parser.py (argparse wiring). Largest file now 211 lines vs original 1329. __init__.py re-exports for backward compat; updated one test patch target (_measure_part_dimensions now resolved in cli.audit's namespace, not cli's re-export) since mock.patch targets where a name is looked up, not where it's re-exported. Verified: test_cli/ 33 passed, live python -m tiacad_core build/check/info/audit runs against examples/.


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
status: done
priority: low
tags: [validation]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-19T01:27:23Z'
session: electric-glaze-0717
links:
  references:
  - tiacad_core/validation/rules/hole_edge_proximity_rule.py
  commits:
  - f96112ae839376ac61269ed6c36fe3939241b978
notes_next: 5
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T23:27:10Z session:zatuhipi-0718] Scoped (zatuhipi-0718): confirmed 5 of 9 rule files in tiacad_core/validation/rules/ use bbox/bounds heuristics -- boolean_gaps_rule.py, bounding_box_rule.py, disconnected_parts_rule.py, feature_bounds_rule.py, hole_edge_proximity_rule.py (grep-verified bbox/bounding_box/get_bounds reference counts). Concrete example: hole_edge_proximity_rule.py's _estimate_hole_radius(bbox) infers a hole's radius from its axis-aligned bounding box rather than querying the actual BREP cylindrical face -- same class of heuristic-vs-actual-geometry gap that TCAD-VAL-5 already fixed for watertight checks (switched to BREP-level checks). A real fix means rewriting each of the 5 rules to query CadQuery/BREP face-level geometry instead of estimating from bbox -- real, non-trivial rework across 5 files, not a mechanical change. Priority/low is appropriate; needs design input on how much BREP-query infrastructure to build once vs. per-rule.
- [#2 2026-07-19T00:23:45Z session:volatile-glacier-0718] Web research validates the plan (2026-07-18, volatile-glacier-0718). Checked against installed cadquery==2.8.0 directly (python -c imports), not just docs.

  API findings:
  - Face.geomType() returns PLANE/CYLINDER/CONE/SPHERE/etc -- selecting "the cylindrical face" is public, one-line: face.geomType() == "CYLINDER" or selector string "%CYLINDER".
  - Face has NO public .radius() in 2.8.0 (verified: dir(Face) has no 'radius'). Getting a cylindrical face's radius via Face._geomAdaptor() -> raw OCCT Geom_Surface -> downcast to Geom_CylindricalSurface -> .Radius() works but leans on a `_`-prefixed CadQuery internal -- avoid.
  - Better public path (verified Edge.radius() exists in 2.8.0): get the face's circular boundary edges (face.edges() filtered by geomType()=="CIRCLE") and call edge.radius() on one of them. This is the pattern to use for hole_edge_proximity_rule.py's _estimate_hole_radius() replacement.

  Design validation: build123d (CadQuery's OCCT-based successor) solved this exact "avoid bbox, query real geometry" problem with a composable filter layer: part.faces().filter_by(GeomType.CYLINDER).filter_by(lambda f: f.radius == r). Independent confirmation that a small shared query-helper module (not per-rule ad hoc geometry math) is the standard shape of this fix, not a TiaCAD-specific idea.

  Performance: no evidence BREP face/edge queries themselves are a bottleneck in CadQuery. Known slowness is in tessellation and multi-part assembly constraint solving (github.com/CadQuery/cadquery issues #1868, #705), not topology/geometry queries -- and the 5 validation rules run per-part, not full-assembly solving, so this class of slowdown shouldn't apply. Worth one timing check against the largest example assembly once implemented, not a reason to design around preemptively.

  Recommended implementation: new tiacad_core/validation/brep_queries.py (or similar) with 2-3 helpers -- cylindrical_faces(solid), face_radius(face) implemented via boundary-edge .radius() not the private adaptor route -- shared across the 5 rule files (boolean_gaps_rule.py, bounding_box_rule.py, disconnected_parts_rule.py, feature_bounds_rule.py, hole_edge_proximity_rule.py). Still needs Scott's go-ahead to start, but the technical unknowns from note #1 (how much infra to build once vs per-rule, and whether the CadQuery API even supports this cleanly) are now resolved -- build the shared module.
- [#3 2026-07-19T00:57:00Z session:breezy-glacier-0718] Session breezy-glacier-0718: implemented the hole-radius fix only (1 of 5 files), scoped down after review -- the other 4 flagged files (boolean_gaps_rule, feature_bounds_rule, disconnected_parts_rule, bounding_box_rule) use bbox for legitimately bbox-shaped part-to-part spatial questions (gap distance, overlap, adjacency, overall size), not radius estimation. Converting those to real solid-solid BREP intersection would be a separate, much bigger, unresearched rework -- not the same class of fix as this one. Shipped: GeometryBackend.get_cylindrical_radius() (CadQueryBackend + MockBackend), used by hole_edge_proximity_rule.HoleEdgeProximityRule._get_hole_radius() with bbox fallback. Commit edf9453, NOT pushed. 7 new tests added (test_geometry_backends.py, test_assembly_validator.py), full 1984-test suite passes.
- [#4 2026-07-19T01:27:22Z session:breezy-glacier-0718] Session breezy-glacier-0718 (part 2, 'adult it'): completed the remaining 3 files -- boolean_gaps_rule, disconnected_parts_rule, feature_bounds_rule -- all genuinely had the same heuristic-vs-real gap as the hole-radius fix. bounding_box_rule (4th) confirmed correct as-is: pure size-sanity check, not a heuristic standing in for something more precise, left untouched. Added GeometryBackend.get_distance()/get_overflow_volume() (real via CadQuery Shape.distance()/.cut(), approximated in MockBackend). Caught and fixed a real correctness gap during implementation: bbox proximity/containment is a sound lower bound but not complete for non-convex parts (an L-shaped part's bbox includes its own empty notch) -- verified with concrete L-shape+notch fixtures that the naive 'only check real geometry when bbox already flags something' design would have silently missed connectivity/overflow errors in that notch. Also caught and fixed a 3x full-suite slowdown (210s->669s) from an unconditional real-query version; final version uses bbox as a sound fast-reject filter (skip real query when bbox already proves the answer) and lands at 196s, faster than pre-session baseline. Commit f96112a (stacked on edf9453 from part 1), NOT pushed. All 5 rule files from the original scope are now resolved -- closing this ticket.


## TASK-TCAD-ARCH-8 · parameter_resolver.py high coupling — 3rd-highest fan-in in repo; _check_cycles() mixes DFS+regex+error formatting (complexity 10, depth 6)

```yaml
status: done
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T23:43:49Z'
session: electric-glaze-0717
links:
  commits:
  - fb6d689252041f86b1b1c2c5c6db67b8bfb9e79b
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T21:36:39Z session:fuchsia-tint-0718] Partial progress (fb6d689): split _check_cycles into _extract_dependencies/_find_cycle/_check_cycles, resolving the complexity/depth complaint. Fan-in (3rd-highest importer count) is unaddressed — that's a coupling question needing a broader design decision, not a mechanical split.
- [#2 2026-07-18T23:43:49Z session:volatile-glacier-0718] Non-issue, same resolution class as ARCH-2/ARCH-4: 16 production importers are all parser/*_builder.py modules resolving YAML parameter expressions -- the shared domain function every builder needs, not accidental coupling. Complexity/depth already fixed via fb6d689 (_check_cycles split); reveal --check now clean except trivial Optional[]/line-length lint. No further action needed.


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


## TASK-TCAD-ARCH-9 · Remove dead visual_debug.py

```yaml
status: done
priority: low
tags: [cleanup]
created: '2026-07-18T23:26:06Z'
updated: '2026-07-18T23:32:21Z'
session: zatuhipi-0718
links:
  commits:
  - e918060760e369958be0be6cac5d5e33924e97d0
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-18T23:26:11Z session:zatuhipi-0718] Confirmed dead across two sessions (arctic-drizzle-0718, zatuhipi-0718): tiacad_core/visual/visual_debug.py has zero callers anywhere in the codebase (grep-verified), is __main__-guarded example code hardcoded to one demo, and is not imported by tiacad_core/visual/__init__.py's public surface. Safe to delete outright; not scoping-blocked like the other ARCH items -- just needs an explicit go-ahead since I didn't author it. One-line PR: git rm the file, confirm no import errors via a full parser test run.
- [#2 2026-07-18T23:32:21Z session:cunning-chimera-0718] Deleted visual_debug.py and its __init__.py re-export; confirmed zero external callers, full test suite (visual/parser/dag/geometry_backends) green after removal.


## TASK-TCAD-CON-1 · Constraint solver MVP — wrap cadquery.Assembly.constrain()/solve() instead of building from scratch

```yaml
status: done
priority: medium
tags: [feature, constraints]
created: '2026-07-19T01:52:47Z'
updated: '2026-07-19T02:28:22Z'
session: flux-lens-0718
depends_on: [TCAD-CON-2]
links:
  references:
  - ROADMAP.md
  commits:
  - 74100605905ff274e7604c4750b16f80263873ad
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T01:53:12Z session:flux-lens-0718] Investigation (session flux-lens-0718, 2026-07-18): CadQuery's Assembly.constrain()/.solve() is a real 6-DOF rigid-body geometric constraint solver (casadi+IPOPT, exact Hessian), already a transitive dependency (casadi==3.7.2 via cadquery-ocp) -- confirmed importable and correct in this repo's venv with zero new installs. Its constraint types (Plane, Point, Axis, PointInPlane, PointOnLine, Fixed/FixedPoint/FixedAxis/FixedRotation) map almost directly onto TiaCAD's flush/coaxial/offset/tangent vocabulary from ROADMAP.md. Verified live: a Plane constraint correctly placed a 5mm cube flush on a 10mm cube (Z=7.5 exactly, X/Y/rotation undisturbed) -- the exact ROADMAP worked example. Academic DOF-graph-reduction solvers and hand-rolled options (SolveSpace-style symbolic+Newton, FreeCAD's OndselSolver) were surveyed and rejected as unnecessary engineering for TiaCAD's assembly sizes -- CadQuery's face/edge-selector-based constraints also match TiaCAD's existing face_top/axis_z spatial-reference model more closely than mate-connector-based systems (Onshape/FreeCAD Assembly3) would.
- [#2 2026-07-19T01:53:16Z session:flux-lens-0718] MVP design: parse constraints: block into cq.Assembly.constrain() calls (reuse SpatialResolver's existing face/edge/axis resolution to get underlying OCCT shapes), call .solve() once per build, compile resulting Locations into the existing transform operation machinery (operations_builder.py/_execute_transform, transform_tracker.py). No DAG execution-model change needed -- matches ROADMAP's original MVP framing (compile constraints to transforms at build time), just reuses a tested solver instead of hand-written propagation. Two structural gaps to fill first: (1) Part has no persisted orientation state (part.py current_position is position-only) -- constraint math needs full pose in/out. (2) axis_x/y/z part-local refs in spatial_resolver.py always point along WORLD axes regardless of a part's actual rotation -- filed separately as TCAD-CON-2, a latent bug independent of this milestone but blocking for it. Known CadQuery solver rough edges (upstream GH issues): crash on .solve() with zero constraints (trivial guard), ambiguity bug with two overlapping planar constraints on same pair, repeated-solve angle drift under iterative/animation use (N/A here, TiaCAD solves once per build). None architecture-blocking. Revised effort estimate: ~2-4 weeks for MVP, down from ROADMAP's original 10-16 week from-scratch estimate. Not yet prioritized/started -- Scott has not committed to building this, this is scoping only.
- [#3 2026-07-19T02:28:22Z session:polar-drought-0718] MVP implemented: 'flush' and 'offset' constraint types, both via cq.Assembly.constrain()/.solve() ('Plane' kind). ConstraintBuilder (tiacad_core/parser/constraint_builder.py) resolves face refs via SpatialResolver/FACE_SELECTOR_MAP, builds an ad-hoc Assembly, solves, and bakes the result into parts via TransformTracker (consistent with TCAD-CON-2's orientation tracking). Wired into parse_pipeline.py after parts+operations build. 17 new tests in tiacad_core/tests/test_parser/test_constraint_builder.py, reproducing the exact ROADMAP.md worked example (Z=7.5) plus a rotation case, offset, inline face specs, and error paths. 'coaxial'/'tangent' deliberately deferred (schema-recognized, raise a clear not-yet-implemented error) since they need edge/axis-selector support this session didn't validate -- filed as TCAD-CON-3.


## TASK-TCAD-CON-2 · axis_x/y/z part-local spatial references always point along world axes, ignore part's actual rotation

```yaml
status: done
priority: low
tags: [bug, spatial-resolver]
created: '2026-07-19T01:53:01Z'
updated: '2026-07-19T02:15:50Z'
session: flux-lens-0718
links:
  commits:
  - 3dbc150e885f83c5fde5463c1f6d942b8cb230ba
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T01:53:21Z session:flux-lens-0718] Found during constraint-solver scoping (session flux-lens-0718, 2026-07-18): spatial_resolver.py's _resolve_part_local() handles axis_x/axis_y/axis_z by returning world X/Y/Z unit vectors through the part's bbox center, never consulting the part's actual applied rotation (Part has no persisted orientation state to consult -- see TCAD-CON-1 note #2). Currently latent because nothing rotates a part and then chains an axis_ reference off it in a way that would expose the discrepancy, but it will produce silently wrong results the moment (a) the constraint solver rotates a part and something downstream reads its axis_z, or (b) any existing manual rotate + axis_ chain that happens to rely on this today. Needs Part to track a real pose (position+orientation), then axis_* to derive from that pose rather than hardcoded world unit vectors.
- [#2 2026-07-19T02:15:50Z session:polar-drought-0718] Fixed by tracking current_orientation (3x3 rotation matrix) on Part/TransformTracker, accumulated across rotate transforms and inline part rotate:, applied in SpatialResolver._resolve_part_local for axis_x/y/z. Regression tests in tiacad_core/tests/test_part_orientation.py.


## TASK-TCAD-CON-3 · Implement coaxial/tangent constraints

```yaml
status: done
priority: low
tags: [feature, constraints]
created: '2026-07-19T02:28:15Z'
updated: '2026-07-19T02:56:31Z'
session: polar-drought-0718
depends_on: [TCAD-CON-1]
links:
  commits:
  - 2f805db3ba61edf1e70b1b41c5defde4dd205d55
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T02:56:31Z session:maritime-blizzard-0718] Implemented coaxial (Axis+Point on edges via part@edges@selector, validated empirically that CadQuery's Assembly._query grammar already supports edges). tangent split out as follow-up — needs radius-aware offset math.


## TASK-TCAD-1 · Implement tangent constraint (radius-aware offset)

```yaml
status: done
priority: low
tags: [feature, constraints]
created: '2026-07-19T02:56:31Z'
updated: '2026-07-19T04:18:43Z'
session: maritime-blizzard-0718
parent: TCAD-CON-3
links:
  commits:
  - a1cee056bbe2d26f9c052b51750b94a6eca67ca8
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T04:18:43Z session:molten-ultimatum-0718] Implemented via direct radius measurement (no CadQuery solve) rather than PointInPlane solve — see constraint_builder.py module docstring


## TASK-TCAD-2 · Extend trust-render world_position to remaining rules: ParameterSanityRule, MissingPositionRule, UnusedPartsRule, BoundingBoxRule

```yaml
status: done
priority: low
tags: [trust-render, validation]
created: '2026-07-19T06:59:16Z'
updated: '2026-07-19T08:03:16Z'
session: earthly-unicorn-0718
links:
  references:
  - docs/developer/MODEL_VALIDATION.md
  commits:
  - 2dc9e4b585cf0fb630cf99d90a4fc3771a063e5e
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T08:03:16Z session:sapphire-stone-0719] Shipped world_position for the 2 rules that fit (MissingPositionRule, BoundingBoxRule). ParameterSanityRule and UnusedPartsRule excluded — see MODEL_VALIDATION.md item 6 and TCAD-VAL-8.


## TASK-TCAD-CON-4 · Constraint contradiction validation — detect conflicting constraints before .solve() fails opaquely

```yaml
status: done
priority: low
tags: [constraints]
created: '2026-07-19T07:53:52Z'
updated: '2026-07-19T09:01:42Z'
session: sapphire-stone-0719
links:
  references:
  - KNOWN_LIMITATIONS.md
  commits:
  - 4435ea8c37b8a7ed4ba358c54b929e9553ed9196
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T09:01:42Z session:garnet-gem-0719] Plane-conflict pre-solve check shipped; ROADMAP.md + VALIDATION_STRENGTHENING.md updated


## TASK-TCAD-CON-5 · ModelGraph/DAG integration for constraints — currently a standalone post-operations pass, not real DAG edges

```yaml
status: done
priority: low
tags: [constraints, architecture]
created: '2026-07-19T07:53:53Z'
updated: '2026-07-19T19:49:11Z'
session: sapphire-stone-0719
links:
  references:
  - KNOWN_LIMITATIONS.md
  commits:
  - 4ce3527fc05b29b4a98f25f71852fbb7eb0a1332
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T19:49:11Z session:umber-gem-0719] Constraints are now ModelGraph nodes/edges; watch skips re-solve when nothing constraint-relevant changed. Per-constraint partitioning left explicitly out of scope (no perf need).


## TASK-TCAD-VAL-8 · UnusedPartsRule doesn't check per-part usage — stub since initial commit, only checks for missing export: section

```yaml
status: done
priority: medium
tags: [validation, bug]
created: '2026-07-19T08:02:29Z'
updated: '2026-07-19T08:35:22Z'
session: sapphire-stone-0719
links:
  commits:
  - d6d11ba6f03520c36846183c4f25eedbbe1f5a8a
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T08:35:22Z session:whispered-demon-0719] Fixed real per-part/per-operation usage detection; also fixed a shared dict-vs-attribute bug in MissingPositionRule/_get_used_parts/_get_exported_parts and restored dropped export.parts parsing. See docs/developer/MODEL_VALIDATION.md item 6.


## TASK-TCAD-CON-6 · tiacad watch silently dropped constraints: entirely (IncrementalBuilder has no constraints_spec, watcher.py never called ConstraintBuilder)

```yaml
status: done
priority: high
tags: [constraints, watch, bug]
created: '2026-07-19T09:11:38Z'
updated: '2026-07-19T09:11:49Z'
session: garnet-gem-0719
links:
  commits:
  - 10b8c2cdd0e4a97bf148b7f616822c2bc0533e10
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T09:11:49Z session:garnet-gem-0719] Fixed: constraints now re-solved every watched rebuild; see KNOWN_LIMITATIONS.md #1 and ROADMAP.md


## TASK-TCAD-3 · Add examples/validation model exercising constraints: with an expect: block

```yaml
status: done
priority: low
tags: [constraints, examples]
created: '2026-07-19T19:21:16Z'
updated: '2026-07-19T19:21:27Z'
session: umber-gem-0719
links:
  commits:
  - c822b2c8d7a3ecb4bf59ec838ead2e6b47463e78
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T19:21:27Z session:umber-gem-0719] Added T4_constraint_flush.tiacad (ROADMAP.md worked example) + golden hash


## TASK-TCAD-CON-7 · tiacad-schema.json: tangent constraint schema is stale/incomplete — still says 'reserved for a future revision, not yet implemented' despite shipping, and doesn't declare tangent's actual face/edge fields (schema silently accepts malformed tangent specs)

```yaml
status: done
priority: high
tags: [schema, constraints]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T21:36:14Z'
session: astral-sun-0719
links:
  commits:
  - f2ed0fc3687a81a187820387dba75550ced8e931
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T21:36:14Z session:astral-sun-0719] Fixed stale tangent schema text + added face/edge field declarations; added TestConstraintSchema coverage (flush/tangent/unknown-type).


## TASK-TCAD-CON-8 · Dead 'reserved for future revision' error branch in ConstraintBuilder._parse_constraint — RESERVED_CONSTRAINT_TYPES is now empty (tangent shipped) but branch still exists, printing empty list on unknown-type errors

```yaml
status: done
priority: low
tags: [cleanup, constraints]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T21:38:52Z'
session: astral-sun-0719
links:
  commits:
  - 730556833b29d865eab93a7db36bbb3fe4600ffa
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T21:38:52Z session:astral-sun-0719] Resolved together with TCAD-CON-9: RESERVED_CONSTRAINT_TYPES is now populated (parallel/perpendicular/angle/symmetric), so the branch is live again instead of dead.


## TASK-TCAD-CON-9 · No angular/parallel/perpendicular/symmetric constraint family, and not even scoped as reserved — RESERVED_CONSTRAINT_TYPES is empty so requesting type: parallel errors as unknown rather than planned

```yaml
status: done
priority: low
tags: [constraints, scoping]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T21:38:52Z'
session: astral-sun-0719
links:
  commits:
  - 730556833b29d865eab93a7db36bbb3fe4600ffa
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T21:38:52Z session:astral-sun-0719] Named+reserved parallel/perpendicular/angle/symmetric in constraint_builder.py and schema enum; added test_reserved_type_raises_distinct_error; documented in KNOWN_LIMITATIONS.md #1.


## TASK-TCAD-VAL-9 · CLI command entrypoints mostly untested — cmd_build (primary user path: parse->export->stats), cmd_watch, cmd_info, cmd_check, cmd_validate/cmd_validate_geometry have no direct tests

```yaml
status: done
priority: high
tags: [testing, cli]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T22:11:36Z'
session: astral-sun-0719
links:
  commits:
  - 4b4d28b38f37184ec9bbe5611bc9493e1fc51bdc
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T22:11:36Z session:astral-sun-0719] Added test_cli_build/info/check/validate/validate_geometry/watch.py (29 tests). cmd_watch tested via mocked FileWatcher since the real loop blocks on a filesystem observer; test_dag/test_watcher.py already covers FileWatcher/IncrementalBuilder directly.


## TASK-TCAD-VAL-10 · Confidence-ladder validation corpus covers only flush constraint — no oracle-backed Tier example for offset/coaxial/tangent; tangent is highest-risk since it bypasses CadQuery's solver with hand-rolled geometry

```yaml
status: done
priority: high
tags: [testing, constraints]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T21:57:39Z'
session: astral-sun-0719
links:
  commits:
  - c1c28a26fc1aa1eb89740f78c4634c6539623afe
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T21:57:39Z session:astral-sun-0719] Added T4_constraint_offset/coaxial/tangent.tiacad to examples/validation/, all with expect: oracle contracts, discovered by test_embedded_contracts.py's auto-discovery. Golden hashes regenerated. Also surfaced and filed TCAD-CON-10 (flush/offset arbitrary in-plane rotation for some size ratios).


## TASK-TCAD-VAL-11 · No integration test for constraints -> DAG incremental build -> export in the normal (non-watch) cmd_build pipeline — only watch mode is covered, and build/watch use separately-patched code paths (root cause of a prior watch-mode constraint bug)

```yaml
status: done
priority: high
tags: [testing, constraints, dag]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T21:41:02Z'
session: astral-sun-0719
links:
  commits:
  - 1e9bd8fda91c5734c0d284bba9986a731b297849
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T21:41:02Z session:astral-sun-0719] Added TestConstraintsIntegration in test_tiacad_parser.py: multi-constraint (flush+offset) full-pipeline test via parse_string, and parse_file->export_stl->trimesh bbox check. Verified both fail when constraint application is disabled (non-vacuous).


## TASK-TCAD-VAL-12 · Tier-5 negative-input corpus has no malformed/contradictory constraint case, despite TCAD-CON-4's contradiction detector being unit-tested only in isolation

```yaml
status: done
priority: medium
tags: [testing, constraints]
created: '2026-07-19T20:39:51Z'
updated: '2026-07-19T22:05:21Z'
session: astral-sun-0719
links:
  commits:
  - 41b84acf55e1d1ccf3c3031d66a06993780a750b
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-19T22:05:21Z session:astral-sun-0719] Added N7_contradictory_constraints.tiacad + TestContradictoryConstraints, folded into cross-cutting typed-error sweep. Also found and fixed a real bug while doing this: ConstraintBuilderError subclassed bare Exception instead of TiaCADError like every sibling builder error — fixed.


## TASK-TCAD-CON-10 · flush/offset constraint solve can converge to an arbitrary in-plane rotation for certain moving-part/reference-size combinations (e.g. 20x20x2 surface + 4x4x4 mount), inflating the AABB and misaligning non-square parts, even though the physical position/gap is still correct — CadQuery's Plane constraint kind leaves rotation-about-normal unconstrained and IPOPT doesn't reliably land on zero. Discovered building the TCAD-VAL-10 offset validation example (20/4 size ratio triggered it; 10/5 and 12/4 did not).

```yaml
status: done
priority: medium
tags: [constraints, solver, bug]
created: '2026-07-19T21:57:11Z'
updated: '2026-07-20T01:18:03Z'
session: astral-sun-0719
links:
  commits:
  - 3d02925a8a43310688dbdbf4e0d5290c929a7365
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T01:18:03Z session:icy-elysium-0719] Fixed: swing-twist post-solve correction in constraint_builder.py's _flush_swing_location; root cause was CadQuery's Plane constraint leaving rotation-about-normal exactly unconstrained + IPOPT's fixed nonzero seed. See KNOWN_LIMITATIONS.md section 1.


## TASK-TCAD-CON-11 · Multi-face flush/offset coupling on same moving part: currently rejected, not solved (coupled least-squares rotation fit needed)

```yaml
status: done
priority: low
tags: [constraints, solver]
created: '2026-07-20T02:04:14Z'
updated: '2026-07-20T23:45:35Z'
session: kojucese-0719
links:
  references:
  - KNOWN_LIMITATIONS.md
  commits:
  - c540d48c104cf2c257716aa4f75113eb98cbdabe
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T23:45:35Z session:icy-leviathan-0720] Solved the common shape: two mutually-opposite flush/offset faces against two independently-fixed references, via _multi_face_swing_location (reuses TCAD-CON-10's shortest-arc shortcut) plus a position-consistency check. 3+ faces or non-opposite face pairs remain rejected (no reproduced use case for general coupled multi-axis fitting). 4 new regression tests, KNOWN_LIMITATIONS.md updated.


## TASK-TCAD-FIN-1 · Localized 'near'/radius edge selector for blend fillets on curved-surface boss seams

```yaml
status: backlog
priority: low
tags: [finishing, selector, backlog]
created: '2026-07-20T03:40:55Z'
updated: '2026-07-20T03:40:55Z'
session: revealed-dimension-0719
links:
  references:
  - KNOWN_LIMITATIONS.md
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-VAL-13 · check/audit CLI 'W x H x D' table swaps H and D columns vs box primitive's width/height/depth axis convention

```yaml
status: done
priority: high
tags: [bug]
created: '2026-07-20T21:03:00Z'
updated: '2026-07-20T21:50:44Z'
session: cerulean-gradient-0720
links:
  commits:
  - b8ca20204e985a103c96665d422766fc672d0a4f
notes_next: 2
```

get_dimensions() in tiacad_core/testing/dimensions.py:87-91 labels Y-extent as 'height' and Z-extent as 'depth', but the box primitive (cadquery_backend.py:31-33, create_box) maps width->X, depth->Y, height->Z per docs/user/YAML_REFERENCE.md. Result: 'tiacad check'/'tiacad audit' print H and D swapped relative to the part's own declared width/height/depth parameters. Confirmed via a box with height=100,depth=6 (intending tall/thin) printing as '100.0 x 6.0 x 100.0' (H and D reversed). Only affects check/audit's human-readable table -- debug bundle's geometry_summary.py uses raw bbox arrays, not this labeling, so it's unaffected. Fix get_dimensions to use the same X/Y/Z->width/depth/height convention as create_box.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T21:50:44Z session:descending-protostar-0720] Fixed axis mapping in get_dimensions(); tests updated and repro verified


## TASK-TCAD-UX-7 · tiacad render computes validation issues (for PNG annotation) but never prints them to console

```yaml
status: done
priority: medium
tags: [usability]
created: '2026-07-20T21:03:00Z'
updated: '2026-07-20T21:55:03Z'
session: cerulean-gradient-0720
links:
  commits:
  - 7868cda1a72ceee115b7d85d8a6a9c5240198776
notes_next: 2
```

cli/render.py:29 runs AssemblyValidator().validate_document(doc) and passes issues into render_trust() purely for image annotation -- but cmd_render never prints a validation summary line the way 'tiacad debug' does ("Validation failed: N errors, N warnings"). Verified by building a model where a difference operation's subtract tool was mispositioned (removed 0mm^3): 'tiacad render' printed only '✓ Trust render written to ...' with no indication anything was wrong; the only signal was a subtle color change on a small crosshair marker in the PNG, easy to miss. Since render.py already computes 'issues', it should print the same summary debug.py does (or a one-line variant) so a caller isn't silently handed a picture of a failed build.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T21:55:03Z session:descending-protostar-0720] render now prints validation pass/fail summary, matching debug's output


## TASK-TCAD-API-2 · boolean 'operation: difference' requires field 'subtract:' -- accept 'subtract'/'cut' as operation-name aliases

```yaml
status: done
priority: low
tags: [dx]
created: '2026-07-20T21:03:00Z'
updated: '2026-07-20T21:56:05Z'
session: cerulean-gradient-0720
links:
  commits:
  - 4eb8f0b8a9cb5dbf0b14f400106cb839f805c7eb
notes_next: 2
```

The natural guess from common CAD vocabulary is 'operation: subtract' with a 'tool:' field; actual required shape is 'operation: difference' with 'base:'+'subtract: [...]' (boolean_builder.py:238-452). The operation-name (difference) not matching its own operand field name (subtract) costs an extra failed round-trip for anyone (human or agent) guessing from standard terminology. Accept 'subtract'/'cut' as aliases for 'difference' at the operation-type level.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T21:56:05Z session:descending-protostar-0720] subtract/cut now accepted as difference aliases


## TASK-TCAD-UX-8 · translate 'to: {from: X}' requires explicit offset even for zero-offset moves -- default missing offset to [0,0,0]

```yaml
status: done
priority: low
tags: [dx]
created: '2026-07-20T21:03:00Z'
updated: '2026-07-20T21:57:08Z'
session: cerulean-gradient-0720
links:
  commits:
  - c7acdf4cbe0494d0c2121fba6322bb20517d8dfe
notes_next: 2
```

Omitting 'offset:' under a derived reference ({from: part.anchor}) errors with "Derived reference must have both 'from' and 'offset' keys" instead of defaulting to [0,0,0]. This is a needless failure on the most common case (move a part flush to a reference point, no additional offset).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T21:57:08Z session:descending-protostar-0720] offset now defaults to [0,0,0] when omitted from a derived reference


## TASK-TCAD-UX-9 · add a constraints: (flush/offset/coaxial/tangent) example to the main examples/ gallery

```yaml
status: done
priority: low
tags: [docs]
created: '2026-07-20T21:03:00Z'
updated: '2026-07-20T22:02:59Z'
session: cerulean-gradient-0720
links:
  commits:
  - 90963e1fe8edc86274a89b2dc5ea0d41c39c0369
notes_next: 2
```

The constraint solver shipped 2026-07-19 but its only working examples live in examples/validation/*.tiacad (test-corpus files, .tiacad extension, heavily annotated for internal verification, not a teaching example) -- not discoverable via examples/*.yaml. Since constraints are now the preferred way to position assembly parts (KNOWN_LIMITATIONS.md #5), add a plain examples/*.yaml demo.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T22:02:59Z session:descending-protostar-0720] 4 single-concept example files added, verified via check + render + visual inspection; combined-file attempt surfaced TCAD-CON-12


## TASK-TCAD-CON-12 · Multiple independent constraint groups in one document corrupt each other's geometry (solve() only locks first group's reference)

```yaml
status: done
priority: high
tags: [bug, constraints]
created: '2026-07-20T22:01:07Z'
updated: '2026-07-20T22:29:54Z'
session: descending-protostar-0720
links:
  commits:
  - f76f74a283c50be269a8482b54a297d6cedeee5e
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-07-20T22:01:24Z session:descending-protostar-0720] Repro: two independent flush groups in one document (a1/a2 flush + b1/b2 flush) -- b1/b2's bounding box comes out non-round (21.0x6.6x21.0 instead of declared 20x5x20). Root cause: apply_constraints() in constraint_builder.py builds one shared cq.Assembly() across every constraint entry in the file and calls a single assembly.solve() -- CadQuery locks only the first-referenced part globally as the fixed anchor, not one anchor per disjoint constraint component, so every subsequent group's reference part is left as a free body in IPOPT's joint optimization and gets silently perturbed. Single-constraint-per-document files (the existing T4_constraint_*.tiacad corpus) are unaffected -- this only triggers with 2+ constraint entries whose part sets don't overlap. Fix needs per-connected-component partitioning: group constraints by shared parts (union-find), solve each component in its own cq.Assembly(). Verified via /tmp/test_two_flush.yaml and /tmp/test_three_flush.yaml during TCAD-UX-9 example-writing work (not committed, reproducible from this note).
- [#2 2026-07-20T22:29:54Z session:icy-leviathan-0720] Fixed via per-connected-component partitioning: constraints grouped by shared part (union-find), each component solved in its own cq.Assembly(). Regression test added, KNOWN_LIMITATIONS.md updated.


## TASK-TCAD-BUG-1 · python -m tiacad_core.cli fails (no __main__.py); tiacad console script not runnable in dev venv

```yaml
status: rejected
priority: medium
effort: 30m
tags: [cli, dx]
created: '2026-08-02T18:26:21Z'
updated: '2026-08-02T18:29:57Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T18:29:02Z session:luminous-shade-0802] starting: add __main__.py, fix console script install
- [#2 2026-08-02T18:29:57Z session:luminous-shade-0802] False positive: ./tiacad and 'python -m tiacad_core' both work perfectly with plain system python3, no venv/install needed. I had guessed 'python -m tiacad_core.cli' (wrong module -- __main__.py lives at tiacad_core/__main__.py, not tiacad_core/cli/__main__.py) and 'poetry run tiacad' (project doesn't use poetry) instead of checking CLI.md's documented Installation section first. Not a TiaCAD defect -- my own process error in the prior session. Corrected in CASE_STUDY_MODELING_AN_EGG.md.


## TASK-TCAD-BUG-2 · No lint for parameters: declared but never referenced via ${...} -- silently ships fake-parametric files

```yaml
status: done
priority: medium
effort: 2h
tags: [validation, parameters]
created: '2026-08-02T18:26:21Z'
updated: '2026-08-02T18:49:45Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
  commits:
  - 327d7ef778f625e28aecfa1f185c881d7918b0fa
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T18:37:45Z session:luminous-shade-0802] starting: add unused-parameter check
- [#2 2026-08-02T18:47:49Z session:luminous-shade-0802] Fixed: new UnusedParametersRule (tiacad_core/validation/rules/unused_parameters_rule.py) scans raw yaml_string for ${...} spans and warns on any declared parameter never referenced -- correctly treats reference from within another parameter's own formula as legitimate use. Wired into AssemblyValidator. Confirmed on egg.yaml (flags length/max_diameter/blunt_fraction as designed) and clean on bottle_revolve.yaml. Running against all 91 committed examples found 8 pre-existing files with genuinely dead parameters -- filed as TCAD-BUG-5 follow-on. New test in test_assembly_validator.py, all 50 validation tests pass. Code uncommitted pending user approval.
- [#3 2026-08-02T18:49:45Z session:luminous-shade-0802] Committed in 327d7ef


## TASK-TCAD-BUG-3 · tiacad build/validate never check mesh watertightness -- degenerate revolve apex (r=0 tip) silently exports non-manifold STL

```yaml
status: done
priority: high
effort: 3h
tags: [validation, revolve, stl]
created: '2026-08-02T18:26:21Z'
updated: '2026-08-02T18:49:45Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
  commits:
  - 327d7ef778f625e28aecfa1f185c881d7918b0fa
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T18:30:27Z session:luminous-shade-0802] starting: wire watertightness check into tiacad build
- [#2 2026-08-02T18:33:57Z session:luminous-shade-0802] Fixed: tiacad build now runs a best-effort trimesh watertightness check after .stl export and warns (never fails) on non-manifold meshes. See KNOWN_LIMITATIONS.md #19 and docs/developer/CASE_STUDY_MODELING_AN_EGG.md #3. Code changes uncommitted pending user approval (tiacad_core/cli/build.py + new tests in test_cli_build.py, both passing).
- [#3 2026-08-02T18:49:45Z session:luminous-shade-0802] Committed in 327d7ef


## TASK-TCAD-DSL-1 · Sketch DSL has no arc/ellipse/spline primitive -- curved profiles must be hand-faceted outside TiaCAD

```yaml
status: done
priority: medium
effort: 1d
tags: [sketch, revolve, feature]
created: '2026-08-02T18:26:22Z'
updated: '2026-08-02T19:16:20Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
  - KNOWN_LIMITATIONS.md
  commits:
  - 47a5fb57ebb13889d25b2a054f9a583d98dcd125
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T18:49:53Z session:luminous-shade-0802] starting: add Arc2D/Ellipse2D/Spline2D shape types to sketch DSL
- [#2 2026-08-02T19:15:24Z session:luminous-shade-0802] Shipped Ellipse2D (standalone) and Path2D (line/arc segments) -- both verified exact against analytic areas and confirmed watertight through revolve/extrude. New example: examples/curved_vase.yaml. spline and ellipse_arc segments were attempted but both hit real, reproducible geometry defects (non-watertight solid; cusp-tangent instead of rounded cap) and were deliberately not shipped -- filed as follow-on TCAD-DSL-2. Full detail in KNOWN_LIMITATIONS.md #18 and docs/developer/CASE_STUDY_MODELING_AN_EGG.md. Tests: tiacad_core/tests/test_sketch.py (TestEllipse2D, TestPath2D), tiacad_core/tests/test_parser/test_sketch_builder_curves.py (new file). All passing. Code uncommitted pending user approval.
- [#3 2026-08-02T19:16:20Z session:luminous-shade-0802] Committed in 47a5fb5


## TASK-TCAD-BUG-4 · Sketch-only designs require a placeholder part that permanently generates 2 spurious dead-work warnings

```yaml
status: done
priority: low
effort: 1h
tags: [validation, sketch, noise]
created: '2026-08-02T18:27:01Z'
updated: '2026-08-02T18:49:45Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
  commits:
  - 327d7ef778f625e28aecfa1f185c881d7918b0fa
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T18:34:05Z session:luminous-shade-0802] starting: suppress dead-work warning for documented _placeholder convention
- [#2 2026-08-02T18:36:59Z session:luminous-shade-0802] Fixed: UnusedPartsRule and MissingPositionRule now skip leading-underscore part names (_placeholder, _dummy), the documented sketch-only-design convention. Confirmed 0 warnings on examples/egg.yaml (was 2) and 16 other placeholder-using examples; genuine unrelated warnings (e.g. text_simple.yaml's disconnected-groups) still fire correctly. New test in test_assembly_validator.py, all 34 tests pass. Code uncommitted pending user approval.
- [#3 2026-08-02T18:49:45Z session:luminous-shade-0802] Committed in 327d7ef


## TASK-TCAD-BUG-5 · Triage 8 pre-existing example files with dead (unreferenced) parameters, found by new UnusedParametersRule

```yaml
status: done
priority: low
effort: 1h
tags: [parameters, examples, cleanup]
created: '2026-08-02T18:47:43Z'
updated: '2026-08-02T19:31:51Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T19:31:51Z session:airless-antimatter-0802] All 8 files triaged and fixed: lego_brick_2x1/3x1 (dead inner_post_* params, superseded by connection_tube_* — deleted), week5_assembly (dead gear_spacing, single gear no pattern — deleted), pcb_standoff_assembly.yaml + trust/ copy (plate_top_z/standoff_height wired into standoff_center_z/pcb_center_z expressions, same numeric result), formats_demo.yaml (corner_radius wired into fillet radius), thing38359_inside.yaml (overall_height wired into polygon points). Verified: 0 remaining unused-param warnings, all expect: contracts still pass, test_assembly_validator.py 35/35 green. Filed TCAD-4 for an unrelated pre-existing non-watertight formats_demo.yaml export found during verification.


## TASK-TCAD-DSL-2 · ellipse_arc/spline as Path2D segments: both attempted, both hit real geometry defects, not shipped

```yaml
status: done
priority: medium
owner: unassigned
effort: 4h
tags: [sketch, revolve, ellipse, spline]
created: '2026-08-02T19:15:16Z'
updated: '2026-08-02T20:31:58Z'
session: luminous-shade-0802
links:
  references:
  - docs/developer/CASE_STUDY_MODELING_AN_EGG.md
  - KNOWN_LIMITATIONS.md
  commits:
  - 75e2d8959aafb93fa1d9d2d4eac0db378b64b990
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T19:16:20Z session:luminous-shade-0802] Blocked on: (a) correct angle1/angle2/sense derivation for ellipse_arc so composed arcs meet the axis perpendicular like a real ellipsoid cap; (b) root-causing why spline mixed with other Path2D segment types produces a non-watertight solid. Both need dedicated investigation time, not a quick fix.
- [#2 2026-08-02T19:16:31Z session:luminous-shade-0802] Correcting status: this is unscoped future work with no forcing use case, matching TCAD-BUG-5/TCAD-FIN-1/TCAD-API-1 convention -- not blocked on anyone, so 'held' was the wrong status, not 'blocked'. Re-filed as backlog.
- [#3 2026-08-02T20:31:58Z session:cunning-throne-0802] Both blockers misdiagnosed: 'spline non-watertight' = pre-existing axis-apex artifact (#19), unrelated to spline; ellipse_arc angle1/angle2/sense worked on first straightforward attempt. Shipped both segment types + examples/ellipsoid_egg.yaml demo.


## TASK-TCAD-4 · formats_demo.yaml exports non-watertight mesh (fillet on box, pre-existing)

```yaml
status: done
priority: low
effort: 30m
tags: [bug, examples, watertightness]
created: '2026-08-02T19:31:44Z'
updated: '2026-08-02T19:43:43Z'
session: airless-antimatter-0802
links:
  references:
  - examples/formats_demo.yaml
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-02T19:43:43Z session:airless-antimatter-0802] Root-caused: filleting all 12 edges of a box builds a valid OCCT solid but exports a non-watertight STL (9 fragments) regardless of tessellation tolerance/radius -- upstream CadQuery/OCCT tessellation limitation at corner seams, not a tiacad bug. Confirmed via BRepCheck_Analyzer (solid valid) and swept tolerance/radius (crack persists at every setting tried). Fixed formats_demo.yaml by changing edges: all -> edges: {parallel_to: Z} (vertical edges only), which tessellates cleanly. Documented as KNOWN_LIMITATIONS.md #22.


## TASK-TCAD-UX-10 · Flow-style YAML with ${...} fails with an unhelpful parse error (parameters: {width: ${w}}, origin: [${x}, ...])

```yaml
status: done
priority: low
effort: 2h
tags: [dx, yaml]
created: '2026-10-16T18:29:13Z'
updated: '2026-10-16T20:55:23Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  commits:
  - 5e2c71b5a951210e8bde8b1f0b0150a6997e36dd
notes_next: 5
```

Found modeling the sticker-drawer bin. Inline mappings/sequences containing ${param} are invalid YAML because '{' opens a flow mapping, and the error ('expected , or } but got {') never mentions ${}. Options: pre-quote ${...} spans before yaml.safe_load, or catch the parse error and add a hint to use block style. Repro: parameters: {width: ${a}, depth: 5, height: 5} on a box part.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T18:35:30Z session:turbo-nexus-1016] Correction after reading YAML_REFERENCE: docs quote every template ('${w}') and quoted flow-style works (tested). Real gap is only the error text and that the docs never state why quoting is needed; KNOWN_LIMITATIONS #16 covers the -${expr} case. Fix = hint in the parse error + one sentence in YAML_REFERENCE Parameters.
- [#2 2026-10-16T19:25:23Z session:turbo-nexus-1016] Docs half done 2026-10-16: YAML_REFERENCE.md Parameters now has 'Quoting ${...} in inline YAML' (and the Document Structure block says parts is required unless imports). Remaining: the parse-error hint in code.
- [#3 2026-10-16T20:39:27Z session:cobalt-flash-1016] Started by mistake in turbo/cobalt session 2026-10-16 (command interrupted); no work done. Docs half already shipped (YAML_REFERENCE 'Quoting ${...}').
- [#4 2026-10-16T20:55:23Z session:babewugo-1016] Parse-error hint added in yaml_with_lines.py; docs half shipped earlier. 5 tests.


## TASK-TCAD-UX-11 · Add a section/probe CLI command (e.g. tiacad section FILE --plane y=79.5) reporting wall/floor/slot thicknesses

```yaml
status: done
priority: low
effort: 1d
tags: [cli, validation]
created: '2026-10-16T18:29:14Z'
updated: '2026-10-16T20:15:17Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  commits:
  - 0ec2a88e5fe9859a3fe8cc0a8e143f7bdff72fa5
notes_next: 2
```

Verifying wall (1.6), slot skin (0.8), floor (2.0) and cutout height on the sticker bin required hand-slicing the STL with trimesh; its ray queries failed without rtree. check only reports bbox+volume per part and measure works between named references. A section command that lists material intervals along an axis line or plane would make thin-feature verification routine.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T20:15:17Z session:cobalt-flash-1016] tiacad section --plane/--line; verified 0.8 skin/1.6 wall/2.0 floor/14 cutout on sticker_bin; 26 tests


## TASK-TCAD-UX-12 · Trust render: add depth cues/cross-section view; anchor markers clutter; PNG lands next to the input YAML

```yaml
status: done
priority: low
effort: 1d
tags: [render, dx]
created: '2026-10-16T18:29:16Z'
updated: '2026-10-16T19:33:04Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin_trust.png
  commits:
  - b2fd9abbfc5882ef5fd1dd860aa8b135ed41a892
notes_next: 4
```

Flat shading makes the Top/Bottom views of an open box a solid rectangle (cavity invisible). Wants a section view and/or light shading. Anchor crosshairs dominate small parts. Default output writes <stem>_trust.png into the source directory (dropped 3 PNGs into examples/); consider a build-output dir or documenting -o.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T18:53:08Z session:turbo-nexus-1016] Correction: the crosshair markers are validation-issue markers (orange=warning, blue=info), NOT anchors; the 4 warnings on the sticker bin are false positives (filed as the VAL task). Implemented: (1) depth-shaded ortho panels (darker = farther, floor 55%), (2) render --section AXIS=VALUE: capped cutaway, cap = slice + vtkContourTriangulator (vtkClipClosedSurface mis-fills concave U profiles; cap areas verified exact vs hand calc 226.08/304.16/569.28 mm2), (3) render --no-markers, (4) -o/default-path documented in CLI.md. Default output path deliberately NOT changed: examples/trust and thingiverse_rebuilds commit *_trust.png beside the YAML. Tests: 91 pass in test_visualization/test_trust_renderer.py + test_cli. Not yet committed.
- [#2 2026-10-16T19:12:03Z session:turbo-nexus-1016] Final: also widened tiacad-schema.json (parts required unless the doc imports; if/then keeps the 'Missing required field parts' message) because the import-only fit_check.yaml was rejected by test_every_example_validates_against_schema; +2 schema tests, +get_schema_info reads then.required. Determinism goldens added for the 4 sticker_drawer models only. Test sweep (correctness, schema, docs, visualization, cli, visual_regression): 855 pass; 14 fail, none from this change: 13 differential tests need manifold3d (not installed here), and v3_bracket_mount golden_volume differs in the last float digit (255576.8426929166 vs ...163). Found while verifying: TCAD-UX-13 (render of import-heavy models), TCAD-VAL-14 (false-positive hole warnings). Awaiting commit approval; then tt done --commit.
- [#3 2026-10-16T19:33:04Z session:cobalt-flash-1016] render --section, depth-shaded panels, --no-markers shipped


## TASK-TCAD-DSL-3 · Inline cut shorthand: collapse cutter-part + difference boilerplate for pockets/slots

```yaml
status: future
priority: low
effort: 2-3d
tags: [dsl, ergonomics]
created: '2026-10-16T18:29:18Z'
updated: '2026-10-16T18:35:30Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
notes_next: 2
```

sticker_bin.yaml needs 4 cutter box parts (cavity, 2 slots, finger cut) each with an explicit corner origin, plus a difference op. A 'cut:' list on a part (primitive + origin) would cut ~half the file. Future/idea; only worth it if more models show the same shape.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T18:35:30Z session:turbo-nexus-1016] Docs have type: pattern (linear/circular/grid) -- my two divider slots could have been one linear pattern; only the cavity/finger cut are true one-offs, so the boilerplate cost is smaller than first filed. Re-evaluate before building.


## TASK-TCAD-DSL-4 · Declare units in metadata (units: mm|in) and warn on mismatch

```yaml
status: done
priority: low
effort: 1d
tags: [dsl, units]
created: '2026-10-16T18:29:19Z'
updated: '2026-10-16T21:02:02Z'
session: turbo-nexus-1016
links:
  commits:
  - 44061ce44124670325c5ea825bbe8839d60a6656
notes_next: 2
```

All values are implicitly mm. Inch-spec'd designs (sticker-drawer spec) are converted by hand. A units field (with optional conversion) would catch silent mm/inch mix-ups. Idea; confirm there is demand first.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T21:02:02Z session:babewugo-1016] Implemented option B: unit-suffixed literals in parameter values, ${...} expressions and --set. No metadata.units field or mismatch lint (bare numbers stay mm). 16 tests; full suite 2334 passed.


## TASK-TCAD-VAL-14 · Validation false positives on box-shaped cutters: HoleEdgeProximity warns 'very close to edge' (37mm!) on pockets/slots; FeatureBounds INFO on intentional overshoot

```yaml
status: done
priority: low
effort: 3h
tags: [validation, false-positive]
created: '2026-10-16T18:53:08Z'
updated: '2026-10-16T20:12:22Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  commits:
  - 2f3015417b2469b44a8e01618618fe2692f05f42
notes_next: 3
```

sticker_bin.yaml (cavity, 2 slots, finger_cut: box cutters in a difference) yields 4 WARNINGs + 2 INFOs, every one intended. Hole 'cavity' 'very close to edge(s)' with distances of 37 mm: the rule treats any subtracted part as a round hole, estimates radius from the bbox (half the cutter width), so a 70 mm pocket is 'close' to a 74 mm wall. Rectangular pockets/slots/notches are not holes. Also 'extends beyond parent' INFO fires for cutters that deliberately overshoot the shell so the cut is clean (standard CAD practice). Fix direction: only apply HoleEdgeProximity to cutters that are actually cylindrical (backend.get_cylindrical_radius already exists, TCAD-ARCH-7), and don't flag deliberate through-cut overshoot. The warnings were the orange/blue crosshair markers on the render, which is why they read as clutter (TCAD-UX-12).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T20:12:22Z session:cobalt-flash-1016] Residual: finger_cut (corner notch exiting -Y and +Z) still gets one INFO, deliberately: overshoot on 2+ axes cannot be told apart from a cutter partly off the part without an intent signal. Volume outside the base does not separate them (cavity 4%, notch 52%).
- [#2 2026-10-16T20:12:22Z session:cobalt-flash-1016] HoleEdgeProximity cylinder-only; FeatureBounds skips single-axis face openings; bin 4W+2I -> 0W+1I


## TASK-TCAD-UX-13 · Trust render of a model that imports components draws the components' internal parts (cutters, shells) as solids

```yaml
status: done
priority: medium
effort: 4h
tags: [render, imports]
created: '2026-10-16T18:58:17Z'
updated: '2026-10-16T19:59:50Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/fit_check.yaml
  commits:
  - 715ad8e931004d435948a2706b8d75318a2d7fbf
notes_next: 2
```

Repro: examples/sticker_drawer/fit_check.yaml imports sticker_bin.yaml twice + divider + clip and unions the finished parts. tiacad render shows a 22-entry legend (bin_a.shell, bin_a.cavity, bin_a.slot, bin_a.finger_cut, ...) and scene extents Z=64.8/Y=237.6 vs the real assembly 52.8/236 (build, verify and validate-geometry all agree on 52.8/236). Cause: ComponentImporter._import_file clones every part of the component into the importer's registry as 'ns.part' but drops the component's operations, so _collect_visible_part_names (trust_renderer.py) never sees that ns.cavity etc. were consumed by ns.sticker_bin; it then falls back to rendering all unconsumed parts, and _collect_component_parts treats ns.sticker_bin as an opaque leaf instead of the difference it is. --section is affected too (cavity box shows as solid). Fix direction: have the importer record which imported parts the component's own ops consume (or the component's default part) and have the renderer hide those; do not hide imported parts merely for being unreferenced (a doc may display an imported part directly). Add a test with a component whose op consumes helper parts.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T19:59:50Z session:cobalt-flash-1016] importer flags component-internal parts; fit_check legend 22->4, extents 148x236x52.8; 6 new tests


## TASK-TCAD-UX-14 · CLI parameter overrides: --set NAME=VALUE on build/check/render/verify

```yaml
status: done
priority: medium
effort: 3h
tags: [cli, parameters]
created: '2026-10-16T19:16:58Z'
updated: '2026-10-16T19:43:16Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_clip.yaml
  commits:
  - a33fed173eed56efa1e0c47b87ba755be424b5f2
notes_next: 2
```

build/check/render/verify cannot override a parameter; only imports: can. Fit-testing wants variants of one model (clips at gap 0.2/0.3/0.4) without editing the YAML or writing a wrapper. Overrides must flow through the same parameter resolution as imports (so derived ${...} parameters recompute), reject unknown names with the list of valid ones, and be echoed in the output so a printed variant is traceable. Note an expect: contract written for the default values will legitimately fail on a variant; decide whether verify should skip or warn.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T19:43:16Z session:cobalt-flash-1016] --set on build/check/render/verify; variant filenames tagged; 11 new tests; full CLI/parser/docs/correctness suites show only the 14 known unrelated failures


## TASK-TCAD-VAL-15 · validate-geometry printability report: min wall thickness, overhangs, build-volume fit (--bed XxYxZ)

```yaml
status: done
priority: medium
effort: 1d
tags: [validation, printing]
created: '2026-10-16T19:17:00Z'
updated: '2026-10-16T20:03:57Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  relates_to:
  - TCAD-VAL-17
  commits:
  - 83b47e79cf0c153e433bbe05b324ee95775dd446
notes_next: 2
```

validate-geometry only checks watertight + component count. For print work it should also report: minimum wall thickness (the sticker bin's 0.8 mm slot skin is the weak point), faces steeper than a configurable overhang angle needing support, and whether the part fits a build volume (--bed 250x210x200, trying axis-aligned orientations). Had to ask the user their bed size because nothing could check the 236 mm bin. Keep it advisory (warnings), with thresholds as flags.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T20:03:57Z session:cobalt-flash-1016] printability section in validate-geometry (--bed/--min-wall/--overhang-angle); hand-computed tests; bin 0.80 mm skin and clip 49.0 mm2 overhang match closed form


## TASK-TCAD-VAL-16 · Contract relation: clearance (true minimum distance between two parts)

```yaml
status: done
priority: medium
effort: 3h
tags: [contracts, validation]
created: '2026-10-16T19:17:02Z'
updated: '2026-10-16T19:52:00Z'
session: turbo-nexus-1016
links:
  references:
  - examples/sticker_drawer/fit_check.yaml
  commits:
  - aee22d1ff1ce1b8b3a15cd7c94f358141b88a3d8
notes_next: 3
```

no_overlap proves a clearance is not negative but not that it is the designed 0.2 mm, so fit_check.yaml's slot (0.2/side) and clip (0.15/leg) gaps are asserted only indirectly. Add relations: clearance: [partA, partB], min: 0.15 (optionally max) using the real solid-to-solid distance already available on the backend (Shape.distance(), see TCAD-ARCH-7 / get_distance). Include a negative-contract fixture so the check is proven able to fail.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T19:17:08Z session:turbo-nexus-1016] Related: TCAD-UX-3 shipped 'tiacad measure' (distance between two named spatial references). That is reference-point distance; this task is solid-to-solid minimum distance (gap between surfaces), so check whether measure can share the backend call before adding a second code path.
- [#2 2026-10-16T19:52:00Z session:cobalt-flash-1016] clearance relation + schema + 9 tests; fit_check_clearance.yaml asserts measured 0.2/0.15 mm; negative control fails as expected


## TASK-TCAD-VAL-17 · Contract: min thickness assertion (thickness: {min: 0.8}) for walls, floors and slot skins

```yaml
status: done
priority: low
effort: 1d
tags: [contracts, validation]
created: '2026-10-16T19:17:03Z'
updated: '2026-10-16T20:22:36Z'
session: turbo-nexus-1016
depends_on: [TCAD-UX-11]
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  commits:
  - f488d3b7abc4837d29c56b10c14236806e7410c3
notes_next: 2
```

Thin features in the sticker bin (1.6 wall, 2.0 floor, 0.8 slot skin) are verified only by volume and by eye in a --section render. A numeric min-thickness contract would make them regress-proof. Pairs with TCAD-UX-11 (section/probe command) which can share the sampling code; the printability report task can reuse it for min wall reporting.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-16T20:22:36Z session:cobalt-flash-1016] thickness contract; sticker_bin asserts 0.8 skin; --set slot_d=1.0 fails with location


## TASK-TCAD-DOC-1 · YAML_REFERENCE examples use 'size: [x,y,z]' for box, which fails to build; expect: block undocumented

```yaml
status: backlog
priority: medium
effort: 2h
tags: [docs, dx]
created: '2026-10-17T00:40:40Z'
updated: '2026-10-17T00:40:40Z'
session: babewugo-1016
links:
  references:
  - docs/user/YAML_REFERENCE.md
```

Found 2026-10-16 (babewugo-1016). A box written as 'primitive: box, size: [10,20,5]' fails: "Box 'b' missing required parameters: width, height, depth". YAML_REFERENCE.md still shows size: in 'Using Parameters', Examples 1/2/4 and the Primitives table (box row), and my new Units paragraph mentions size: as if valid. Fix: use 'parameters: {width, depth, height}' everywhere (verify each example actually builds, ideally with a doc-example build test), and add an 'expect:' (contracts) section or a pointer to MODEL_VALIDATION.md / VALIDATION_STRENGTHENING.md 4.1 (incl. ${...} in expect values).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-UX-15 · validate-geometry has no --set, so parameter variants cannot be print-checked directly

```yaml
status: backlog
priority: low
effort: 1h
tags: [cli, dx]
created: '2026-10-17T00:40:42Z'
updated: '2026-10-17T00:40:42Z'
session: babewugo-1016
links:
  references:
  - tiacad_core/cli/validate_geometry.py
```

build/check/render/verify accept --set NAME=VALUE (TCAD-UX-14); validate-geometry (--bed/--min-wall/--overhang-angle) does not. Working around it meant building a variant STL then inspecting it by hand. Wire --set through, tag output like the other commands, add a test.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-DSL-5 · No first-class way to lay several parts out on one build plate

```yaml
status: backlog
priority: low
effort: 1d
tags: [dsl, feature]
created: '2026-10-17T00:40:43Z'
updated: '2026-10-17T00:40:43Z'
session: babewugo-1016
```

Putting one tray of each layout (and a test ruler of 18-31 squares) on one print needed a generator script (YAML emitted by Python) plus a trimesh merge outside TiaCAD. Idea: a plate:/layout helper (parts + positions or simple row/grid packing, optional gap, bounds check against a --bed) that exports one multi-body STL/3MF. Only worth building if multi-part print plates recur (sticker drawer will need ~20 trays).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-DSL-6 · Box axis names (width=X, depth=Y, height=Z) are a recurring trap; consider x/y/z (or size_x/y/z) aliases

```yaml
status: backlog
priority: low
effort: 4h
tags: [dsl, dx]
created: '2026-10-17T00:40:45Z'
updated: '2026-10-17T00:41:09Z'
session: babewugo-1016
links:
  references:
  - docs/user/YAML_REFERENCE.md
notes_next: 2
```

YAML_REFERENCE already carries a warning that depth maps to Y and height to Z, and TCAD-VAL-13 was the same class of bug in the CLI table. Weak evidence otherwise: during the 2026-10-16 sticker-drawer work the box axes were written correctly from existing examples (no axis mistake of mine), so this is a judgement about the naming, not a repeated failure. Option: accept x/y/z (or size_x/size_y/size_z) as aliases for the three box parameters, keep width/depth/height working, mention in docs. Needs a decision first (alias vs leave as documented).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-10-17T00:41:09Z session:babewugo-1016] Correction (babewugo-1016): I first reported axis naming 'cost a failed build'. It did not; that failure was 'size:' on a box (see TCAD-DOC-1). Priority stays low; decide alias vs documented-only.


## TASK-TCAD-VAL-18 · Schema: thickness.min lost 'exclusiveMinimum: 0' when widened to numberOrTemplate

```yaml
status: backlog
priority: low
effort: 30m
tags: [validation, contracts]
created: '2026-10-17T00:40:47Z'
updated: '2026-10-17T00:40:47Z'
session: babewugo-1016
links:
  references:
  - tiacad-schema.json
```

4eaf444 let expect: numeric fields be a number or a ${...} template ($defs/numberOrTemplate). thickness.min previously enforced > 0 in the schema; the shared definition cannot carry that, so a literal 0 or negative min now passes the schema (the contract itself would still need a positive value to be meaningful). Restore with a dedicated definition (anyOf [number > 0, template]) for thickness.min, plus a schema test for 0/-1.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-EX-1 · sticker_drawer examples (bin/divider/clip/fit_check) still describe the old swapped drawer axes; reconcile with sticker_tray

```yaml
status: backlog
priority: medium
effort: 3h
tags: [examples]
created: '2026-10-17T00:40:49Z'
updated: '2026-10-17T00:40:49Z'
session: babewugo-1016
links:
  references:
  - examples/sticker_drawer/sticker_bin.yaml
  - examples/sticker_drawer/sticker_tray.yaml
```

Real drawer (measured 2026-10-16): 19.5 in left-right x 15 in front-back; columns run front to back. sticker_bin.yaml comments say 5 across a 381 mm drawer and 2 deep in 489 mm (axes swapped) and its 236 mm length cannot print on the CR-6 SE (~234 mm travel). New sticker_tray.yaml (single-sticker trays; layout A slot_l 71.6, 5/column, layout B 90.6, 4/column) supersedes the design. Decide: retire bin/divider/clip/fit_check or keep as an example of imports; either way fix the comments, update fit_check, trust PNGs, golden hashes, docs/tests that reference them. Physical verification still outstanding: print one of each tray, check stickers (3.5 in diagonal) and the 50.8 vs 63.5 mm clearance.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_
