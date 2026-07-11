# TiaCAD Architecture Next Steps

This is the canonical near-term architecture plan for TiaCAD.

It answers five questions:

1. What architecture do we have now?
2. What parts are working well enough to keep?
3. What architectural debt is real today?
4. What work should happen next?
5. What work is explicitly not the current roadmap?

This document is intentionally practical. It is not a full design spec and it is not a research vision.

---

## Progress

### 2026-04-17

Practical architecture work completed:

- `PartsBuilder` no longer hardwires `CadQueryBackend` internally.
- `PartsBuilder` now accepts an injected backend and otherwise uses the configured default backend.
- The simple primitive path now goes through `GeometryBackend` for `box`, `cylinder`, `sphere`, and `cone`.
- CadQuery-only primitives are now explicit instead of implicit: `torus`, `polygon`, and `text` fail clearly on non-CadQuery backends.
- `BooleanBuilder` now preserves the source backend on results and uses backend boolean methods when a backend is present.
- `PatternBuilder` now preserves the source backend on generated parts and uses backend translate/rotate methods when a backend is present.
- `OperationsBuilder` transform results now preserve the source part backend.
- `TransformTracker` now uses `GeometryBackend` for translate/rotate/center lookups when a backend is present.
- CadQuery-native builders now attach `CadQueryBackend` to their outputs consistently: `extrude`, `revolve`, `sweep`, `loft`, `gusset`, `text`, and multi-input `hull`.
- CadQuery-only input paths now fail earlier and more clearly: `text` and multi-input `hull` reject non-CadQuery-backed input parts instead of failing later on missing geometry methods.
- Single-input `hull` remains a passthrough and now preserves the source part backend explicitly.
- 3MF export and visualization tessellation now use `GeometryBackend.tessellate()` when a backend is present instead of assuming raw CadQuery geometry.
- STL/STEP export paths now enforce their CadQuery-only status explicitly, including watch-mode auto-export.
- Single-part 3MF export now constructs a correct temporary `PartRegistry` instead of relying on an invalid registry call shape.
- The parser import boundary is cleaner: the shared parse pipeline now lives outside `TiaCADParser`, import loading is injected instead of hardwired, and the static parser/importer circular dependency has been removed.
- The CLI maintenance surface is cleaner: `cmd_build`, `cmd_check`, `cmd_audit`, and `cmd_watch` now rely more on shared helper paths for export dispatch, final-part selection, measurement, watch output formatting, and reporting instead of embedding the full control flow inline.

This is not full backend decoupling. It is a narrow but real step that makes the abstraction less aspirational in the production build path.

Remaining gaps on this track:

- Several operation-specific builders still depend directly on CadQuery-based geometry behavior.
- Sketch-based and advanced primitives are still effectively CadQuery-bound.
- STL/STEP export remains intentionally CadQuery-only.
- Visualization and 3MF export now use backend tessellation, but the full export/render surface is not backend-neutral.

What changed here is not portability. It is boundary clarity:

- backend-aware paths now use backend methods and preserve backend identity
- CadQuery-only paths now declare themselves as CadQuery-only in code and tests
- mesh consumers use the backend contract where it exists instead of bypassing it
- parser/import orchestration no longer depends on a circular module relationship

---

## Current Architecture

TiaCAD today is built around three stable ideas:

1. A YAML model that describes parts, references, imports, and operations.
2. A v3 spatial-reference system with unified frames and auto-generated part references.
3. A CadQuery-backed realization pipeline that turns the intermediate model into solids and exports.

That means the project is currently:

- Strong on spatial/reference semantics
- Strong enough on parser/build flow to keep building on
- Still operationally tied to CadQuery as the geometry kernel

The current codebase is not truly backend-agnostic, even though it has a `GeometryBackend` abstraction.

---

## Keep These Decisions

These architectural choices are worth preserving:

- Keep the v3 reference/frame model as the core spatial abstraction.
- Keep YAML as the user-facing model format.
- Keep the DAG/import/watch model as a first-class part of the build system.
- Keep CadQuery as the production kernel unless there is a strong and concrete reason to replace it.

The project does not need a foundational rewrite to keep progressing.

---

## Current Architectural Debt

The highest-value debt is not theoretical. It is concrete and already visible in the codebase.

### 1. Backend boundary is ambiguous

`GeometryBackend` exists, but large parts of the production path still construct or use CadQuery directly.

This creates the worst middle state:

- We pay abstraction complexity cost
- We do not get real decoupling
- It is unclear to contributors which boundary is intended to be stable

### 2. Constraint/assembly intent is still missing

The reference system is strong, but there is no real constraint solver.

That means:

- assemblies require manual positioning
- design intent is not captured declaratively
- higher-level relationships are missing from the model

### 3. Analytic geometry and solid realization are not separated cleanly enough

The project conceptually distinguishes references/frames from solid generation, but the implementation still mixes these concerns in places.

This makes future work on constraints, alternate realizations, and testing harder than it should be.

### 4. Reliability gaps become architecture problems

Packaging mismatches, schema drift, watch-mode blind spots, and documentation drift all weaken the trustworthiness of the architecture.

These are not side issues. If the public contract is inconsistent, the architecture is effectively unstable.

---

## Recommended Work

### Priority 1: Make the kernel boundary explicit

This is the most important architectural decision still open.

Choose one of these two paths:

**Path A: Commit to `GeometryBackend` as a real boundary**

Do this if the project wants cleaner testing seams and a credible future path to alternate realizations.

Required work:

- stop constructing `CadQueryBackend` directly inside builders
- inject the backend through the build path
- move primitive creation, selection queries, and realization steps behind backend-facing interfaces where practical
- document which modules are allowed to depend on CadQuery directly

**Path B: Make CadQuery the intentional kernel boundary**

Do this if backend portability is not actually a goal.

Required work:

- simplify or narrow the abstraction
- document CadQuery as the expected geometry engine
- stop implying that swappable backends are a near-term capability

Either path is better than the current ambiguous state.

### Priority 2: Build constraints incrementally on top of v3 references

The next major architecture improvement should be a v4-style constraint layer, not a full kernel rewrite.

Recommended scope:

- define a small set of high-value constraints first: `flush`, `coaxial`, `offset`, `align`
- represent constraints in the model cleanly before solving everything
- start with deterministic assembly helpers or partial solving rather than a fully general solver
- keep constraints expressed in terms of existing references and frames

This work fits the current architecture. It does not require CGA.

### Priority 3: Tighten the separation between reference logic and BREP realization

The spatial model should remain useful even before solid generation happens.

That suggests:

- reference resolution should stay independent of CadQuery specifics as much as possible
- placement logic should be testable without needing full solid construction
- assembly reasoning should operate on references/frames first and solids second

This is the most important precondition for future constraint work.

### Priority 4: Keep architecture contracts enforceable

Near-term engineering work should continue to harden the public and internal contracts:

- keep schema/version/docs aligned
- keep packaging metadata aligned with actual runtime features
- keep watch/import behavior correct for multi-file models
- keep internal documentation linked and current

This is maintenance, but it is also architecture stewardship.

---

## What Not To Do Now

These are poor near-term priorities for the current repo:

- Do not start with full multi-backend support.
- Do not begin a large CGA rewrite as the main roadmap item.
- Do not introduce broad abstraction layers without first deciding their ownership and boundaries.
- Do not mix a constraint-system effort with a kernel-replacement effort.

The project should prefer narrower, testable steps.

---

## Practical Roadmap

### Phase 1: Clarify the geometry boundary

- decide whether `GeometryBackend` is strategic or incidental
- document that decision
- refactor the main builders to follow it consistently

### Phase 2: Prepare for constraints

- identify the minimal model/API additions needed for assembly intent
- keep them reference-based
- add tests around placement semantics before solver complexity

### Phase 3: Add a small constraint layer

- start with a few high-value constraint types
- support simple and predictable solving behavior
- avoid over-generalizing early

### Phase 4: Re-evaluate future kernel work

Only after the earlier phases are in place should the project revisit larger questions like:

- richer analytic kernels
- alternate realization backends
- CGA experimentation

---

## Relationship To Other Docs

- [ARCHITECTURE_DECISION_V3.md](ARCHITECTURE_DECISION_V3.md): explains the current architectural foundation
- [CLEAN_ARCHITECTURE_PROPOSAL.md](CLEAN_ARCHITECTURE_PROPOSAL.md): explains design intent and separation-of-concerns ideas
- [KNOWN_LIMITATIONS.md](../../KNOWN_LIMITATIONS.md): states active product and architectural limitations
- [BACKLOG.md](../../BACKLOG.md) — "Architecture debt" section: current open
  issues and coupling hubs, re-verified against code 2026-07-11 (supersedes
  the archived `OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md` and
  `ARCHITECTURE_REVIEW_2026-04-18.md`, both now in `docs/archive/`)
- [CGA_V5_FUTURE_VISION.md](CGA_V5_FUTURE_VISION.md): long-term research vision, not the current execution plan

---

## Bottom Line

TiaCAD does have a clear architectural direction, but until now it did not have one short document that separated near-term architecture work from long-term vision.

The right work now is:

1. resolve the CadQuery/backend boundary
2. prepare and add constraints incrementally on top of the v3 reference system
3. keep tightening the reliability of the architecture's public contracts

That is the most credible path to a stronger system without turning the project into a rewrite.
