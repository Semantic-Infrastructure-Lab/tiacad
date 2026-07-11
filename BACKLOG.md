# TiaCAD Backlog

Consolidated open action items scattered across the doc set, gathered during
a doc-coherence pass on 2026-07-11. This is the single place to look for
"what's left to do" that isn't the headline roadmap item — see `ROADMAP.md`
for the Constraint Solver (Q4 2026) and CGA v5.0 (2027+) strategic track.

**How this file works:** one line per item, themed, with a pointer to the
doc/code that has the full context. Items move to `CHANGELOG.md` when
shipped (delete from here), not the other way around. Re-verify an item
before starting it — several of these (marked below) haven't been checked
against current code since the date given.

---

## Validation / testing infrastructure

- **CI validation as a required gate.** Add schema-conformance + schema-truth
  checks; make `expect:` contract checking a required CI gate, not just a
  local `tiacad check --contract` command. — `VALIDATION_STRENGTHENING.md` §5
- **One source of truth for test health.** Have CI emit pass/skip/fail counts
  as a committed badge or `TEST_STATUS.json`; stop hand-writing test counts
  into multiple markdown files (this doc-coherence pass found counts stale
  in at least 6 places). — `VALIDATION_STRENGTHENING.md` §5
- **Differential testing blocked.** ~90% of geometry code bypasses the
  `GeometryBackend` abstraction and calls CadQuery directly, so the fast
  `MockBackend` can't stand in for most tests and true kernel-vs-kernel
  differential testing is currently impossible. Routing new operation code
  through the backend is a prerequisite. Same root cause as the CadQuery
  coupling item below. — `VALIDATION_STRENGTHENING.md` §5,
  `KNOWN_LIMITATIONS.md` #3
- **Pinned CI lockfile.** Exact dependency versions, regenerated on review —
  decouples "what the library supports" from "what CI reproducibly tests."
  Explicitly deferred when the dependency-posture pass shipped 2026-07-10.
  — `VALIDATION_STRENGTHENING.md` §5
- **Trust-gallery sign-off** (§4.7) and **golden STEP set** (§4.9) — both
  explicitly out of scope for the T0-T5 ladder, still open.
  — `VALIDATION_STRENGTHENING.md` §6
- **Curved-geometry `watertight` false negative.** Mesh-export tessellation
  artifact on spheres/fillets makes the watertight check unreliable for
  curved surfaces — worth fixing before more Tier-3-style manifold-health
  gates lean on it. — `KNOWN_LIMITATIONS.md` #8
- **`validation:` schema block: implement or delete.** Currently a
  half-implemented no-op in the schema. (The `schema_version` drift half of
  this old bullet is done — verified 2026-07-11, 0 files still say `"2.0"`.)
  — `VALIDATION_STRENGTHENING.md` §5

## Model-validation UX (`docs/developer/MODEL_VALIDATION.md`, items 2-7)

- Reconcile item 2 ("model-local contracts") against the now-shipped
  `expect:` contract engine — likely partially/fully superseded, needs a
  doc pass before carrying forward as open.
- `tiacad verify` CLI command — evaluate model-local contracts, emit JSON +
  console summary.
- Reference-based measurements — distances/angles/alignment between named
  spatial references, exposed as a CLI/testing utility.
- Stepwise summaries attached to operations in `build_trace.json`.
- Annotated trust renders — point at measured failures directly on the
  rendered image.
- Negative trust scenarios — intentionally-bad models that must fail
  *visual/trust-render* validation specifically (distinct from the Tier 5
  parse/build negative corpus, which already covers parse-time failures).

## API / language surface

- **Deprecation warnings for old syntax.** Old cone (`radius_bottom`/
  `radius_top`) and pattern-spacing syntax should raise a runtime
  `DeprecationWarning`; planned since 2026-02-15, not yet implemented (no
  `DeprecationWarning` in `parts_builder.py` as of 2026-07-11).
  — `docs/developer/API_DEPRECATION_STRATEGY.md`
- **GitHub import: no branch override.** `github:user/repo/file.yaml` always
  fetches the default branch; no `@branch` syntax.
  — `KNOWN_LIMITATIONS.md` #4
- **Limited export formats.** No DXF/IGES/G-code/SVG — community-driven, add
  on demand. — `KNOWN_LIMITATIONS.md` #2

## Architecture debt

*Re-verify before relying on any of these — only the schema_version item
(struck through) was independently re-checked against current code on
2026-07-11; the rest are carried forward from an 2026-04-18 review at face
value.*

- Backend selection relies on process-global state (`get_default_backend`/
  `set_default_backend`) rather than being threaded explicitly.
- `OperationsBuilder` is a central-dispatch bottleneck — a registry-driven
  dispatch pattern has been proposed.
- `Part` is the largest coupling hub in the codebase.
- Parse/watch orchestration (`parse_pipeline.py`, `watcher.py`) is still a
  heavy coordinator.
- `cli.py` remains a large monolithic module.
- `tiacad_core.visual` vs `tiacad_core.visualization` — package-boundary
  ambiguity between the two.
- Validation is mostly heuristic (bbox-based), not semantic — the `expect:`
  contract engine (shipped Q2-Q3 2026) is a partial answer to this; worth
  reassessing whether this item is now smaller in scope than when written.
- `parameter_resolver.py` — complexity hotspot.
- ~~Schema/version contract drift~~ — **fixed 2026-07-10**, verified
  2026-07-11 (0 files declare `schema_version: "2.0"`).

— all from `docs/architecture/OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md`

## Docs hygiene

- **CadQuery coupling.** STL/STEP export and several advanced operations
  still require CadQuery-compatible geometry rather than going through
  `GeometryBackend` — same root cause as the differential-testing blocker
  above; worth tracking as one item, not three separate mentions across
  docs. — `KNOWN_LIMITATIONS.md` #3
- **`docs/architecture/README.md` / `ARCHITECTURE_NEXT_STEPS.md` /
  `OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md` overlap.** Three docs
  all present themselves as "the" current architecture-status source: worth
  a follow-up pass to merge into one, or clearly delineate scope (proposal
  vs. review vs. debt register) — not attempted in the 2026-07-11 pass,
  flagged only.
- ~~Two archive-index files~~ — **done 2026-07-11**: deleted the orphaned
  `docs/archive/README.md` duplicate; `docs/archive/ARCHIVE_SUMMARY.md` is
  now the single canonical archive index (already the one
  `docs/DOCUMENTATION_MAP.md` pointed to).

---

*Items resolved during the 2026-07-11 doc-coherence pass have already been
removed from their source docs and are not repeated here — see
`CHANGELOG.md`'s Unreleased section and `git log` for that session's diff if
you want the full list of what got fixed (DAG doc status contradiction,
stale example-count/version numbers, three conflicting constraint-solver
quarter labels, `docs/DOCUMENTATION_MAP.md` regeneration, several archived
docs).*
