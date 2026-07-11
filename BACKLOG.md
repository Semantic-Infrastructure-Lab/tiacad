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
- ~~**`validation:` schema block: implement or delete.**~~ — **resolved
  2026-07-11**: the schema no longer has a `validation:` key (top-level
  properties are `…parts, operations, finishing, export, variants, expect`);
  the shipped `expect:` contract block superseded it. (The `schema_version`
  drift half was likewise done — 0 files still say `"2.0"`.)

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

- ~~**Deprecation warnings for old syntax.**~~ — **shipped 2026-07-11**: all
  four legacy patterns (cone `radius_bottom`/`radius_top`, linear-pattern
  scalar `spacing`+`direction`, `translate: {offset:}` wrapper, list-form
  `export:`) now raise a runtime `DeprecationWarning` with a migration pointer
  and a backward-compat mapping. 15 tests in
  `test_parser/test_deprecation_warnings.py`.
  — `docs/developer/API_DEPRECATION_STRATEGY.md`
- ~~**GitHub import: no branch override.**~~ — **shipped 2026-07-11**: trailing
  `@branch` suffix now selects the branch (default `main`, slashes allowed),
  branch-namespaced in the cache. — `KNOWN_LIMITATIONS.md` #4
- **Limited export formats.** No DXF/IGES/G-code/SVG — community-driven, add
  on demand. — `KNOWN_LIMITATIONS.md` #2

## Architecture debt

*All items below re-verified against current code on 2026-07-11 (see
`git log` / session `weightless-universe-0711`). None turned out fully stale —
every claim has at least partial current-code support — but four had their
framing narrowed. Originals from
`docs/archive/OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md`
(now archived — see "Docs hygiene" below).*

**Still fully true:**

- **Backend global state.** Selection still falls back to process-global state
  (`get_default_backend`/`set_default_backend`/`reset_default_backend` in
  `geometry/__init__.py`); production call sites in `parts_builder.py` and
  `backend_utils.py` still depend on the ambient default rather than an
  injected backend. (`TiaCADParser` entry points *do* accept explicit
  injection now — the global fallback path is what remains.)
- **`Part` coupling hub.** `part.py` (237 lines) is confirmed the #1 fan-in
  file in the repo (21 importers within `tiacad_core/`, 59 repo-wide) — small
  file, largest blast radius. Purely a coupling problem, not size/complexity.
- **`cli.py` monolith.** Still the #1 quality hotspot in the repo (1,201
  lines, 57 functions, 59/100); `create_parser()` alone is 122 lines, and
  `TiaCADParser`/`DimensionError` are re-imported locally in 6+ command
  functions instead of once at module scope.
- **`tiacad_core.visual` vs `tiacad_core.visualization`.** Both packages still
  exist with overlapping purpose (trust/debug rendering vs. general rendering);
  no canonical-boundary decision documented. Three non-code sibling dirs
  (`visual_references/`, `visual_output/`, `visual_diffs/`) widen the naming
  confusion though they aren't part of the package-boundary problem itself.

**True but narrower than originally framed:**

- **`OperationsBuilder` dispatch.** `execute_operation()` still routes via a
  12-branch `if/elif` on `op_type` (not a registry), but the operation *logic*
  has already been delegated to per-type builder classes — this is now a
  routing-mechanism issue, not a god-object one.
- **Parse orchestration.** `parse_pipeline.py` remains a confirmed hotspot
  (`parse_tiacad_dict` is 110 lines / depth 4 doing 6 distinct jobs).
  `watcher.py` is moderately complex (`start`/`_rebuild`/`_resolve_watch_paths`
  all 40–70 lines) but is *not* among the repo's top hotspots — lower priority
  than parse_pipeline.py; don't treat both as equally heavy.
- **Validation heuristic vs semantic.** Assembly-level rules
  (`validation/rules/*.py`) are still bbox-heuristic-heavy (5 of 9 rule files
  lean on bbox/bounds helpers), but a real semantic layer now ships and is used
  — the `expect:` contract engine (`testing/contracts.py`, spatial-relation +
  manifold-overlap checks) appears in 53+ example/test files. The claim is now
  accurate only for the rule-based validator, not the codebase as a whole.
- **`parameter_resolver.py`.** High-coupling module (3rd-highest fan-in in the
  repo) but *not* a complexity hotspot by Reveal's thresholds — only
  `_check_cycles()` (complexity 10, depth 6, mixing DFS + regex + error
  formatting) stands out. Track as coupling/consolidation risk, not complexity.

- ~~Schema/version contract drift~~ — **fixed 2026-07-10**, verified
  2026-07-11 (0 files declare `schema_version: "2.0"`).

## Docs hygiene

- **CadQuery coupling.** STL/STEP export and several advanced operations
  still require CadQuery-compatible geometry rather than going through
  `GeometryBackend` — same root cause as the differential-testing blocker
  above; worth tracking as one item, not three separate mentions across
  docs. — `KNOWN_LIMITATIONS.md` #3
- ~~`docs/architecture/README.md` / `ARCHITECTURE_NEXT_STEPS.md` /
  `OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md` overlap.~~ — **resolved
  2026-07-11**: `OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md` and its
  same-date near-duplicate `ARCHITECTURE_REVIEW_2026-04-18.md` (both debt
  registers covering identical findings) archived to `docs/archive/` — their
  content is superseded by this file's own re-verified "Architecture debt"
  section above. `ARCHITECTURE_NEXT_STEPS.md` kept as the canonical
  forward-looking plan (genuinely distinct content: recommendations/roadmap,
  not a debt register). `docs/architecture/README.md`, `docs/README.md`, and
  `docs/DOCUMENTATION_MAP.md` updated to point here instead.
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
