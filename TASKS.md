---
project: tiacad
schema_version: '1.0'
id_prefix: TCAD
next_id: 1
archival: inline
areas:
  VAL: 6
  UX: 7
  API: 2
  ARCH: 9
---

## TASK-TCAD-VAL-1 · CI validation as required gate — make expect: contract checking a required CI gate

```yaml
status: backlog
priority: high
tags: [validation]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:32:53Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-VAL-2 · Differential testing blocked — route geometry code through GeometryBackend so MockBackend/kernel-vs-kernel testing works

```yaml
status: backlog
priority: high
tags: [validation, architecture]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:32:53Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-VAL-3 · Pinned CI lockfile — exact dependency versions, regenerated on review

```yaml
status: backlog
priority: medium
tags: [ci]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:32:53Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-VAL-4 · Trust-gallery sign-off and golden STEP set (out of scope for T0-T5 ladder)

```yaml
status: backlog
priority: medium
tags: [validation]
created: '2026-07-18T02:32:53Z'
updated: '2026-07-18T02:32:53Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


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
status: backlog
priority: low
tags: [docs]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T02:32:58Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-UX-2 · tiacad verify CLI command — evaluate model-local contracts, emit JSON + console summary

```yaml
status: backlog
priority: medium
tags: [cli]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T02:32:58Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-UX-3 · Reference-based measurements CLI/testing utility — distances/angles/alignment between named spatial references

```yaml
status: backlog
priority: medium
tags: [cli]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T02:32:58Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-UX-4 · Stepwise summaries attached to operations in build_trace.json

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
status: backlog
priority: medium
tags: [validation]
created: '2026-07-18T02:32:58Z'
updated: '2026-07-18T02:32:58Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


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
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-4 · tiacad_core.visual vs tiacad_core.visualization overlap — no canonical-boundary decision documented

```yaml
status: backlog
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-5 · OperationsBuilder dispatch — execute_operation() routes via 12-branch if/elif on op_type, not a registry

```yaml
status: backlog
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-TCAD-ARCH-6 · Parse orchestration hotspot — parse_pipeline.py's parse_tiacad_dict is 110 lines / depth 4 doing 6 distinct jobs

```yaml
status: backlog
priority: low
tags: [architecture]
created: '2026-07-18T02:33:07Z'
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


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
updated: '2026-07-18T02:33:07Z'
session: electric-glaze-0717
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_
