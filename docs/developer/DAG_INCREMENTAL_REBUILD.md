---
title: "DAG Incremental Rebuild — Implementation Plan"
type: architecture
beth_topics:
  - tiacad
  - dag
  - incremental-rebuild
  - watch-mode
  - invalidation
  - build-cache
---

# DAG Incremental Rebuild — Implementation Plan

**Planned:** 2026-03-15 (session: astral-warrior-0315)
**Status:** 🟡 Not started — foundation complete, implementation not begun
**Effort estimate:** ~14-16 days

## Problem

Every parameter change triggers a full model rebuild. A 500-line YAML with 30 parts
rebuilds all 30, even if only one parameter changed. Goal: rebuild only the nodes
downstream of what changed.

---

## What Already Exists

All in `tiacad_core/dag/`:

| File | What it does | Status |
|---|---|---|
| `model_graph.py` | NetworkX graph: nodes, edges, cycle detection, topological sort, mark_invalid/valid, get_transitive_dependents | ✅ Complete |
| `graph_builder.py` | Extracts dependencies from YAML: param→param, part→param, op→part/param, sketch→param | ✅ Complete (minor gaps) |
| `visualizer.py` | DOT format export + stats printing | ✅ Complete |

- 53 DAG tests passing in `tests/test_dag/`
- `build_graph=True` flag already wired into `TiaCADParser.parse_dict`
- Prior session: `hidden-sorcerer-0215`

---

## What to Build (5 Phases)

### Phase 0 — GraphBuilder gap fixes (1 day) ← START HERE

Fix missing edges in `graph_builder.py`:

1. **Operations that use sketches directly** — `extrude`, `revolve`, `sweep` have a `sketch:` field
   that `_extract_operation_dependencies` doesn't track. Add to that method:
   ```python
   if 'sketch' in op_spec:
       sketch_id = f"sketch:{op_spec['sketch']}"
       if sketch_id in self.graph:
           self.graph.add_dependency(dependent_id, sketch_id)
   ```

2. **Audit boolean chain edge cases** — complex boolean operations with nested `inputs:` lists.
   Run `GraphVisualizer.show_stats` on all examples and verify edge counts look right.

---

### Phase 1 — `InvalidationTracker` (3-4 days)

**New file:** `tiacad_core/dag/invalidation_tracker.py`

```python
tracker = InvalidationTracker(old_graph)
dirty = tracker.compute_dirty_set(new_graph)
# → {"parameter:screw_diameter", "operation:drill_hole", "operation:final"}
```

Algorithm:
1. Compare `hash_value` for each node between old and new graph
2. Collect directly-changed nodes (hash mismatch, added, deleted)
3. For each changed node → `graph.get_transitive_dependents()` → add all downstream
4. Return full dirty set

Also handles: new nodes added, nodes deleted, structural dependency changes.

**New tests:** `tests/test_dag/test_invalidation_tracker.py`

---

### Phase 2 — `BuildCache` (2 days, parallel with Phase 1)

**New file:** `tiacad_core/dag/build_cache.py`

In-memory cache keyed by `(node_id, content_hash)`:
```python
cache = BuildCache()
cache.put("operation:drill", hash_val, part_object)
part = cache.get("operation:drill", hash_val)  # → Part or None
```

Note: CadQuery geometry is not picklable — in-memory only for now.
Future v2: persistent cache via STEP export/import.

**New tests:** `tests/test_dag/test_build_cache.py`

---

### Phase 3 — `IncrementalBuilder` (4-5 days) ← hardest phase

**New file:** `tiacad_core/dag/incremental_builder.py`

```python
builder = IncrementalBuilder(cache=cache)
result = builder.build(yaml_data, old_graph=prior_graph)
# result.registry  → PartRegistry (mix of cached + freshly-built parts)
# result.graph     → new ModelGraph
# result.stats     → {rebuilt: 3, cached: 27, total_ms: 140}
```

Core algorithm:
1. Build new graph via `GraphBuilder`
2. If no old graph → full build, cache everything → done
3. Compute dirty set via `InvalidationTracker`
4. Topological sort all nodes
5. For each node in order: if dirty → build; else → restore from cache
6. Merge into PartRegistry

**Integration into parser:**
Add `incremental_state=None` param to `TiaCADParser.parse_dict`.
When provided, enables incremental mode. Returns `IncrementalState(graph, cache)`.
Caller preserves and passes back on next call.

**The tricky bit:** The current pipeline builds all parts THEN runs all operations.
For incremental, these must be interleaved in topological order.
This means `PartsBuilder` and `OperationsBuilder` need single-node build methods:
- `PartsBuilder.build_one(name, spec) → Part`
- `OperationsBuilder.execute_one(name, spec, registry) → Part`

Both already exist conceptually (build_part, execute_operation) — need to expose them
cleanly for the incremental path.

**New tests:** `tests/test_dag/test_incremental_builder.py`
Heavy focus on: cache hit/miss, parameter change propagation, structural changes (add/remove part).

---

### Phase 4 — Watch Mode (3-4 days)

**New file:** `tiacad_core/watcher.py`

```bash
python -m tiacad --watch examples/bracket.yaml
# [14:32:01] Watching bracket.yaml
# [14:32:05] Changed — rebuilding...
# [14:32:05] Done in 89ms (4 rebuilt, 23 cached)
```

Uses `watchdog` library (add to dependencies).
Maintains `IncrementalState` across rebuilds.
Calls user-specified callback on completion (export STL, render PNG, etc.).

**New tests:** `tests/test_dag/test_watcher.py` — mock file events via `watchdog` test helpers.

---

## Build Order + Effort

| Phase | What | Effort | Prerequisite |
|---|---|---|---|
| 0 | GraphBuilder gap fixes | 1 day | — |
| 1 | InvalidationTracker | 3-4 days | Phase 0 |
| 2 | BuildCache | 2 days | — (parallel with Phase 1) |
| 3 | IncrementalBuilder | 4-5 days | Phases 1+2 |
| 4 | Watch Mode | 3-4 days | Phase 3 |

**Total:** ~14-16 days

---

## Quick Win (after Phase 0+1)

Even before incremental builds work, Phase 0+1 enable **rebuild impact reporting**:
```bash
python -m tiacad examples/bracket.yaml --show-deps
# Changed parameter 'screw_diameter' would require rebuilding:
#   → hole_radius (parameter)
#   → drill_op (operation)
#   → final_assembly (operation)
#   3 of 28 nodes affected (89% cache hit rate)
```

---

## Key Files to Read at Session Start

```bash
reveal tiacad_core/dag/                              # current DAG structure
reveal tiacad_core/dag/model_graph.py                # understand ModelGraph API
reveal tiacad_core/dag/graph_builder.py              # understand dependency extraction
reveal tiacad_core/parser/tiacad_parser.py           # see where to integrate
reveal tiacad_core/tests/test_dag/                   # existing test patterns
```

Then start with Phase 0 — fix the sketch→operation gap in `graph_builder.py:_extract_operation_dependencies`.
