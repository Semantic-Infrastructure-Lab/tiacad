---
project: tiacad
schema_version: '1.0'
id_prefix: TCAD
next_id: 4
archival: inline
areas:
  VAL: 13
  UX: 7
  API: 2
  ARCH: 10
  CON: 11
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
