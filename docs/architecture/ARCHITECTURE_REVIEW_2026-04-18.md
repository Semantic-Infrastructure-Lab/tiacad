# Architecture Review 2026-04-18

Senior-engineering review of TiaCAD focused on separation of concerns, single responsibility, reuse, and architectural clarity.

## Current Assessment

TiaCAD is materially stronger than it was earlier in this cleanup cycle:
- parser/import circular dependencies are gone
- builder and export boundaries are clearer
- CLI orchestration is less monolithic
- visualization/trust rendering is more decomposed

The main remaining architectural issues are narrower and more typical of a maturing codebase:
- ambient global backend selection still leaks into core entry points
- operation dispatch is centralized in one coordinator
- `Part` is a heavily shared domain object with broad responsibility
- visualization package boundaries are historically grown rather than sharply defined
- a few public package surfaces still drift from current project reality

## Findings

### 1. Ambient backend state is still part of the parser contract

`PartsBuilder` supports explicit backend injection, but the main parser path still defaulted to process-global backend state. That made backend choice a hidden dependency for the highest-level build API.

Impact:
- harder to reason about embedding behavior
- easier for tests to leak backend state across cases
- weakens architectural claims about backend abstraction

Status:
- In progress
- `TiaCADParser.parse_file()`, `parse_string()`, and `parse_dict()` now accept an explicit `backend`
- the shared parse pipeline now threads that backend into `PartsBuilder`

Remaining work:
- reduce reliance on `get_default_backend()` outside explicit test/setup paths
- decide whether process-global default backend remains supported long-term or becomes test-only convenience

### 2. `OperationsBuilder` is still a centralized coordinator

`OperationsBuilder` currently owns operation dispatch plus construction of operation-specific builders. It works, but it is still the main open/closed pressure point in the parser layer.

Impact:
- new operations require editing central wiring
- dispatch logic remains denser than ideal

Recommended direction:
- move toward a registry-driven operation handler map
- keep command-level orchestration thin and operation implementations local

### 3. `Part` is the main shared domain object and the main coupling hub

`Part` carries geometry, backend identity, metadata, transform history, and convenience queries. That is pragmatic, but it means many layers depend on one broad abstraction.

Impact:
- large change surface
- easy to accumulate more behavior on the same type

Recommended direction:
- document `Part` as an intentionally central domain object if that is the design
- otherwise split history/query concerns into services or helper types

### 4. CLI structure is improved, but still file-centralized

The worst command hotspots were reduced, but `cli.py` still serves as the command registry, formatter layer, and a large amount of orchestration logic.

Recommended direction:
- move to per-command modules when practical
- keep shared formatting/output helpers separate from command entry points

### 5. Visualization boundaries are still historically ambiguous

The split between `tiacad_core.visual` and `tiacad_core.visualization` is understandable, but it is not a crisp boundary for new contributors.

Recommended direction:
- choose one package as the canonical visualization surface
- document whether the other is transitional, internal, or trust/debug-specific

### 6. Public package surfaces must stay current

Stale status/version language in package entry points is a small issue, but it directly degrades contributor trust.

Status:
- In progress
- `tiacad_core.parser.__init__` now reflects the package version and no longer advertises old alpha-phase/test-count text

## Priority Order

1. Make backend configuration explicit at system entry points.
2. Reduce central dispatch pressure in `OperationsBuilder`.
3. Clarify package boundaries for visualization and other contributor-facing modules.
4. Decide whether `Part` stays intentionally broad or is slimmed down.
5. Continue keeping public docs and package surfaces aligned with actual architecture.

## Progress Log

### 2026-04-18

- Added this review document as the canonical record for this review pass.
- Began resolving the highest-priority issue by threading explicit backend injection through the public parser/build path.
- Extended that backend propagation through imported components so explicit parser backend choice applies consistently across local and imported parts.
- Cleaned the stale `tiacad_core.parser` package surface so it no longer advertises outdated alpha/test-count status.
- Ran a fresh Reveal audit across `stats://`, `ast://`, `imports://`, `depends://`, and `reveal check`.
- Used that audit to prioritize `pattern_builder._execute_circular` as the clearest remaining parser hotspot and to clean a small watcher duplication/unused-import issue.
- Refactored `cli.py` info-report printing into smaller helpers and added focused tests so the output contract is covered without full CLI end-to-end coupling.

## Near-Term Next Steps

- Add targeted tests proving parser entry points honor an explicitly supplied backend.
- Audit watcher/import flows for places that still rely on ambient backend state.
- Decide whether to deprecate process-global backend selection for production code.
