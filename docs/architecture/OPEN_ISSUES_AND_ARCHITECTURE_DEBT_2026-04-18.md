# Open Issues And Architecture Debt 2026-04-18

Current-state review of open issues and architectural debt in TiaCAD.

This document is intentionally narrower than the broader architecture review docs. It focuses on what still looks open now, based on the current codebase, current docs, current example behavior, and a fresh Reveal pass.

## Scope

Inputs used for this pass:

- current code in `tiacad_core/`
- active docs under `docs/`
- current example-model behavior via `tiacad debug`
- Reveal structural review across:
  - `stats://tiacad_core?hotspots=true`
  - `ast://tiacad_core?complexity>10`
  - `imports://tiacad_core?circular`
  - `depends://tiacad_core?top=25`
  - `reveal check tiacad_core`

## Summary

The repo is in materially better shape than it was at the start of this cleanup cycle:

- parser/import cycles are gone
- watch-mode export behavior is more consistent
- backend boundaries are clearer than before
- `tiacad debug` is real and usable
- the example corpus now mostly passes under the debug path

The remaining debt is not “rewrite territory.” It is concentrated in a handful of seams:

1. schema/version contract drift is still real
2. backend selection is still partly ambient global state
3. parser and watch orchestration are still heavy coordinators
4. `OperationsBuilder`, `Part`, and `cli.py` remain central coupling hubs
5. visualization is still split across two packages with overlapping responsibility
6. validation is still largely heuristic and bbox-driven

## Open Issues

### 1. Schema version contract is still inconsistent

This is still the clearest active contract issue.

The parser now defaults to schema `3.0`, but a large amount of active repo content still declares `schema_version: "2.0"`:

- active examples such as `examples/color_demo.yaml`, `examples/component_import_demo.yaml`, `examples/pipe_sweep.yaml`
- trust examples under `examples/trust/`
- stdlib/component YAML such as `tiacad_core/stdlib/hardware/*.yaml`
- active tests such as `tiacad_core/tests/test_parser/test_color_integration.py`

Impact:

- parser warnings on legitimate repo-owned files
- unclear migration status for contributors
- continued ambiguity about what schema version is actually current

This is not just documentation drift. It is a live public contract inconsistency inside the repo.

### 2. Backend selection still relies on process-global state

`TiaCADParser` entry points now accept explicit backend injection, which is good progress. But `tiacad_core/geometry/__init__.py` still exposes global mutable backend state through:

- `get_default_backend()`
- `set_default_backend()`
- `reset_default_backend()`

And that state is still used in production-oriented codepaths:

- `tiacad_core/parser/parts_builder.py`
- `tiacad_core/parser/backend_utils.py`

Impact:

- hidden configuration dependency
- possible test leakage across cases
- weaker guarantees for embedding, concurrency, and reproducibility

This is the main remaining architecture issue on the backend-boundary track.

### 3. `OperationsBuilder` is still the main parser coordination bottleneck

`tiacad_core/parser/operations_builder.py` still owns:

- operation dispatch
- builder construction
- transform execution
- the open/closed pressure point for new operation types

`execute_operation()` is better than before, but the module is still a centralized coordinator rather than a registry-driven dispatch surface.

Impact:

- new operations require editing a central switch
- operation wiring is harder to extend cleanly
- operation-specific concerns are still coupled through one module

### 4. `Part` remains the strongest coupling hub in the repo

Reveal still shows `tiacad_core/part.py` as the top reverse-dependency center in the codebase.

`Part` currently mixes:

- geometry storage
- backend identity
- metadata
- transform history
- current position tracking
- geometry queries like bounds/center

This is workable, but it is a broad abstraction with a large blast radius.

Impact:

- future behavior tends to accumulate on the same type
- seemingly local changes can affect many layers
- boundaries between domain data and helper/service behavior remain blurry

### 5. Parse/watch orchestration is still heavy

`tiacad_core/parser/parse_pipeline.py` remains one of the top hotspots from Reveal. The main concerns are:

- `prepare_build_context()` does a lot of work in one pass
- `parse_tiacad_dict()` still combines validation, section extraction, build prep, part build, registry merge, operation execution, and document construction

`tiacad_core/watcher.py` is improved, but still has visible debt:

- `_resolve_watch_paths()` contains a nested recursive `walk()` with nontrivial logic
- watch mode still depends on the private helper `ComponentImporter._resolve_stdlib()`
- `start()` and `_rebuild()` are still the main watch-mode orchestration hotspots

Impact:

- parser/watch behavior is harder to evolve safely
- watch mode still carries some implementation-specific coupling to importer internals
- future debug/incremental work has to thread through already-busy orchestration code

### 6. CLI remains a large monolithic module

Recent refactors substantially improved the worst command handlers, but Reveal still flags `tiacad_core/cli.py` as the top hotspot file:

- file size remains large
- `create_parser()` is still oversized
- `cmd_validate_geometry()` and `cmd_check()` are still locally dense
- there are still duplicate imports and function-local imports in the file

Impact:

- harder navigation for contributors
- output/presentation logic and command orchestration still live together
- command-specific changes still land in one large file

### 7. Visualization package boundaries are still muddy

The repo still has two parallel packages:

- `tiacad_core.visual`
- `tiacad_core.visualization`

Current rough split:

- `visual` contains trust/debug-facing rendering
- `visualization` contains general rendering APIs

That split is understandable historically, but it is still not a crisp public boundary.

Impact:

- contributor confusion about where new render/debug code belongs
- duplicated conceptual surface for “visual output”
- harder packaging and dependency hygiene over time

### 8. Validation remains mostly heuristic, not strongly semantic

Validation architecture is decent structurally, but many rules still lean on coarse geometric heuristics:

- bbox comparisons in rule helpers
- operation-level heuristics in rules such as `boolean_gaps_rule.py`
- limited intent-aware validation for assemblies and fixtures

This is especially relevant given the recent AI-debug and trust-render work. TiaCAD now has better observability, but the validation layer still lags behind that observability in semantic depth.

Impact:

- validation is good at catching obvious geometry/layout issues
- validation is weaker at proving assembly intent or functional correctness
- AI-assisted review currently has better artifacts than first-class semantic validators

### 9. Parameter resolution remains a quiet complexity hotspot

`tiacad_core/parser/parameter_resolver.py` is still one of the current complexity hotspots.

The core issue is not correctness failure. It is that:

- dependency extraction
- cycle detection
- recursive name building
- expression evaluation concerns

all still cluster closely in one module.

Impact:

- parameter behavior is harder to extend confidently
- cycle/reporting logic is more coupled than ideal

## Lower-Priority But Real Debt

These are not the top issues, but they are still worth tracking:

- `tiacad_core/visualization/renderer.py` still has several long, argument-heavy helper methods
- `tiacad_core/dag/incremental_builder.py` still has oversized coordinator methods and some unused imports
- `tiacad_core/exporters/threemf_exporter.py` still has local import/style debt and dense helper methods
- `reveal check tiacad_core` still reports a large amount of low-grade maintainability noise across the repo

This category is mostly “steady cleanup” rather than architecture-defining debt.

## Priority Order

### Priority 1

- resolve the schema-version contract mismatch across active examples, stdlib files, and tests
- reduce remaining reliance on ambient backend defaults in production codepaths

### Priority 2

- split parser/watch orchestration into smaller helpers with cleaner ownership
- move `OperationsBuilder` toward a registry-driven dispatch model

### Priority 3

- decide whether `Part` remains intentionally broad or should be slimmed down
- break `cli.py` into per-command modules and shared presentation helpers
- choose one canonical visualization package boundary

### Priority 4

- deepen validation from bbox heuristics toward more meaningful intent checks
- continue low-grade maintainability cleanup surfaced by Reveal

## Recommended Next Actions

1. Unify active repo-owned YAML to one schema version, ideally `3.0`, or explicitly support both without warning on repo-owned assets.
2. Treat global backend selection as a test convenience rather than a normal production dependency.
3. Extract an operation-handler registry from `OperationsBuilder`.
4. Split watch rebuild/path resolution into smaller internal helpers and remove dependence on importer private methods.
5. Start a CLI modularization pass with command modules rather than more helper accumulation inside `cli.py`.
6. Write one short package-boundary note choosing the canonical visualization surface.
7. Add one or two higher-value semantic validation rules that can consume the new debug/summary artifacts.

## Bottom Line

The codebase no longer has major structural breakage, but it still has a clear set of open debt:

- one active public-contract inconsistency around schema versions
- one still-important architecture seam around backend configuration
- a few central coordinator modules that remain broader than they should be

That is a healthy place to be, but it is not a finished place. The next round of work should focus on these concrete seams rather than broad redesign.
