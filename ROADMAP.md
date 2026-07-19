# TiaCAD Roadmap

**Last Updated:** 2026-07-11
**Current Version:** v3.1.2

---

## Current Focus (Q3 2026)

**Status:** 🟢 **Active Development** — Q1 milestones shipped ahead of schedule;
Q2-Q3 spent hardening the test/validation infrastructure those milestones sit on.

**Completed this quarter (Q3, in progress):**
- ✅ Confidence-ladder validation corpus (Tiers 0/1/3/4/5) — see "What Was Built
  (Q2-Q3 2026)" below
- ✅ `SpatialResolver` longest-prefix-match fix for dotted namespaced part
  references (2026-07-11)

**Completed Q1 2026:**
- ✅ Fixed all 17 test failures (0 failing as of 2026-03-10)
- ✅ Component/Module Import System — local, stdlib, GitHub URI schemes (Mar 2026)
- ✅ Dependency Graph (DAG) + Incremental Rebuild + Watch Mode (Mar 2026)
- ✅ `polygon` primitive — regular N-sided prism (hex nuts, gears, etc.)
- ✅ Hardware stdlib: m3/m4/m5/m6 screws, m3/m4/m5/m6 nuts, m3 washer, m3 standoff, mounting bracket
- ✅ Tier 2 geometric contracts for all assembly examples
- ✅ PCB standoff assembly example (`examples/pcb_standoff_assembly.yaml`)

**Current test suite:** see `TEST_STATUS.json` (repo root, CI-generated) for live counts.

---

## Strategic Plan (Updated Jul 2026)

**Executed roadmap:**

1. **Q1 2026:** Component System ✅ **DONE** — local/stdlib/GitHub imports + hardware stdlib
2. **Q1 2026:** DAG + Watch ✅ **DONE** — incremental rebuild, wired into watcher.py
3. **Q2-Q3 2026:** Validation Confidence Ladder ✅ **DONE** — see below
4. **Q4 2026:** Constraint Solver — **current next milestone**
5. **2027+:** CGA v5.0 Architecture — research moonshot

---

## What Was Built (Q1 2026)

### Component/Module System ✅ Complete

**Vision realized:** npm/cargo for CAD — reusable, shareable, parametric components

```yaml
imports:
  - tiacad://std/hardware/m3_screw    # bundled stdlib
  - github:scottsen/guitar-hangers/hook  # fetched from GitHub, cached
  - ./bracket.yaml                    # local file

parts:
  screw:
    component: m3_screw
    parameters: {length: 20mm}
```

**What was delivered:**
- `tiacad://std/...` → resolves to bundled `tiacad_core/stdlib/hardware/*.yaml`
- `github:user/repo/path.yaml` → fetches `raw.githubusercontent.com`, cached to `~/.tiacad/cache/github/`
- Local paths → unchanged behavior
- Hardware stdlib: m3/m4/m5/m6 screws, m3 washer, m3 standoff, m3 nut, mounting bracket

**Session:** ninja-xenarch-0316, enchanted-hydra-0316

---

### Dependency Graph (DAG) + Incremental Rebuild ✅ Complete

**Vision realized:** True parametric modeling with incremental rebuilds

```bash
tiacad watch examples/assembly.yaml --export /tmp/assembly.stl
[14:32:07]  changed   ✓   112ms  1 rebuilt, 3 cached  → assembly.stl
```

**What was delivered:**
- `ModelGraph`, `GraphBuilder`, `Visualizer` — core DAG module
- Cycle detection at build time
- CLI `--show-deps` flag
- `InvalidationTracker` + `IncrementalBuilder` — only rebuild changed parts
- `tiacad watch` command — auto-rebuild on save (incremental)
- `--export <path>` flag — auto-export to STL/3MF/STEP on each rebuild

**Session:** enchanted-hydra-0316 (watch + export), prior foundation in hidden-sorcerer-0215

---

### `polygon` Primitive ✅ Complete

Regular N-sided extruded prism:

```yaml
primitive: polygon
parameters:
  sides: 6
  diameter: 8.0     # circumscribed circle
  height: 4.0
```

Unlocks: hex nuts, hex standoffs, gear blanks, decorative prisms.

---

## What Was Built (Q2-Q3 2026)

### Validation Confidence Ladder ✅ Complete

**Vision realized:** oracles over snapshots — every example's geometry is checked
against an independently-derived expected value (closed-form formula, hand-derived
relation, or typed error), not just "did it build without crashing."

**What was delivered** (full plan: `docs/developer/VALIDATION_STRENGTHENING.md`):
- Embedded `expect:` contract engine (volume/bbox/components/relations/no_overlap)
  — a model + five lines of `expect:` is now fully validated, no bespoke pytest
  class required
- Tiers 0/1 — primitive and single-op ladder corpus (`examples/validation/T0_*`,
  `T1_*`) checked against closed-form analytic formulas
- Tier 3 — composite-part corpus (`T3_*`) with inclusion-exclusion-derived volumes
  and hard BREP `count_solids()` connectivity gates
- Tier 4 — assembly relational corpus (`T4_*`) plus a full `expect: relations:`
  contract on `hardware_assembly_demo.yaml`, and a new `no_overlap`
  no-interpenetration contract-engine check
- Tier 5 — negative-input corpus (`examples/validation/negative/N1-N6`), each
  asserting a specific typed `TiaCADError`
- Legacy Tier-2 pytest classes trimmed (39 redundant tests removed, now subsumed
  by embedded `expect:` contracts)

**Bugs found and fixed in the process** (the ladder's actual ROI, not just
process): inverted `polygon` `circumscribed` flag (oversized hex nuts), dead
part-level `translate:`/`rotate:` schema syntax, `lego_brick_2x1`/`3x1` cavity
Y/Z offset swap, all 8 fastener components' heads floating off their shafts,
message-less negative-dimension kernel errors, silently-dropped duplicate YAML
keys. See `KNOWN_LIMITATIONS.md` #7 and #9-#12 for details on each.

**Test suite:** 1,588 (start of Q2) → 1,926 total (1,859 non-visual passing,
0 failing; 67 visual passing).

**Sessions:** the confidence-ladder work spanned multiple sessions in
2026-07 (see `docs/developer/VALIDATION_STRENGTHENING.md` §6 for the full
phase-by-phase history).

---

## Constraint Solver — MVP shipped 2026-07-19 (`TCAD-CON-1`)

**Vision:** Declarative assemblies — specify intent, not coordinates

```yaml
constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]   # [reference, moving]
  - type: offset
    faces: [surface.face_top, mount.face_bottom]
    distance: 5mm
```

`flush` and `offset` are implemented and shipped (`tiacad_core/parser/constraint_builder.py`),
wrapping CadQuery's own `Assembly.constrain()`/`.solve()` (`casadi`+IPOPT) rather than a
hand-written solver — see the 2026-07-18 scoping investigation below for why. Both compile
to ordinary `transform` operations at build time (baked via the same `TransformTracker`
every other transform uses), matching the original MVP framing: rigid constraint
propagation, not a live/bidirectional solve. `coaxial` and `tangent` are recognized by the
schema but intentionally not implemented — they need edge/axis-selector query support this
round didn't validate; raise a clear error instead of guessing. Follow-up filed as
`TCAD-CON-3`.

Convention: in `faces: [reference, moving]`, the first face's part is the one CadQuery's
solver auto-locks (its first-referenced entity); the second is repositioned. `offset`
requires `faces:` (not the `parts:` shorthand sketched in the original vision below) —
that shorthand left which two faces get the gap underspecified.

Prerequisite fixed first: `TCAD-CON-2` (`axis_x`/`axis_y`/`axis_z` part-local references
always pointed along **world** axes regardless of a part's actual rotation) — needed so a
constraint-driven rotation feeds correctly into any further spatial reference on that part.
`Part`/`TransformTracker` now track a cumulative `current_orientation` rotation matrix
alongside position.

**What's required:**
- ~~Constraint YAML schema (flush, coaxial, offset, tangent)~~ Done — `flush`/`offset` implemented, `coaxial`/`tangent` schema-recognized (`TCAD-CON-3`)
- Constraint validator (detect contradictions before solve) — not yet; CadQuery's solver currently just fails to converge on a contradiction
- ~~Solver~~ Done — CadQuery's `Assembly.constrain()`/`.solve()`, not a hand-written one
- Integration with ModelGraph (constraints are just edges) — not yet; constraints currently run as a standalone post-operations pass, not DAG edges

**Effort:** ~~10-16 weeks~~ ~~2-4 weeks~~ MVP (flush + offset) shipped in one session, thanks to reusing CadQuery's existing solver.

---

### 2026-07-18 scoping investigation (`TCAD-CON-1`)

**Note:** Don't build a solver from scratch —
**CadQuery's own `Assembly.constrain()`/`.solve()` already is one**, and it's already a
working transitive dependency (`casadi`+IPOPT, confirmed importable and correct in this
repo's venv with zero new installs). Its constraint types (`Plane`, `Point`, `Axis`,
`PointInPlane`, `PointOnLine`, `Fixed*`) map almost directly onto `flush`/`coaxial`/
`offset`/`tangent`. Verified live: a `Plane` constraint correctly placed a 5mm cube flush
on a 10mm cube (exact expected Z, X/Y/rotation undisturbed) — the exact example above.

Revised MVP: parse `constraints:` into `cq.Assembly` constraint calls (reusing
`SpatialResolver`'s existing face/edge/axis resolution for the underlying OCCT shapes),
call `.solve()` once per build, then compile the resulting `Location`s into the existing
`transform` operation machinery. No DAG execution-model change — this still matches the
original MVP framing below (compile constraints to transforms at build time), it just
reuses a solver instead of writing propagation logic by hand. Two structural gaps to fill
first: `Part` has no persisted orientation (`part.py` tracks position only); and
`axis_x/y/z` part-local references in `spatial_resolver.py` currently always point along
**world** axes regardless of the part's actual rotation, which would silently produce
wrong results the moment a constraint-driven rotation feeds another spatial reference
(tracked as `TCAD-CON-2`, a latent bug independent of the constraint solver itself).
Known rough edges in CadQuery's solver (from upstream issues): a crash on `.solve()` with
zero constraints, an ambiguity bug with two overlapping planar constraints on the same
pair, and repeated-solve angle drift under animation-style iterative solving (irrelevant
here — TiaCAD solves once per build). None are architecture-blocking.

**Note:** A full symbolic constraint solver is hard. MVP approach: compile constraints to
transform operations at build time (rigid constraint propagation, not general solving).
This covers 80% of assembly use cases without PhD-level math — now cheaper, since the
"rigid constraint propagation" step can be CadQuery's solver rather than new code.

---

## Long-Term Vision (2027+)

**These require significant investment - only pursue with clear need:**

### Web-Based Preview/Editor
**What:** Try TiaCAD in browser, share designs via URL
**Requires:** WebAssembly CAD engine or JS alternative
**Effort:** 8-12 weeks (MVP)
**Impact:** Huge for adoption, risky scope

### Manufacturing Integration
**What:** G-code generation, DXF export, CAM toolpaths
**Requires:** Solid core + user demand
**Effort:** 6-10 weeks per feature
**Impact:** Production-ready workflows

### The Moonshot: CGA v5.0 Architecture
**🔮 Research Vision:** Replace BREP with Conformal Geometric Algebra

**What:** Fundamental architectural shift - exact algebraic geometry instead of approximate BREP
- **Current:** YAML → Parser → CadQuery/OCCT → BREP (approximate, tolerances)
- **v5.0:** YAML → Parser → CGA Kernel (exact) → BREP (only for export)

**Why This Would Be World-Class:**
- ✨ **Exact operations:** Intersections, distances, offsets are algebraic (no tolerances)
- ✨ **Native constraints:** Geometric conditions compile to CGA equations
- ✨ **Unified code:** All primitives are multivectors (no special cases)
- ✨ **CAM integration:** Slicing and toolpaths use same geometric foundation
- ✨ **Novel:** No other open-source CAD uses CGA + YAML + constraints

**The Math:** Conformal Geometric Algebra (GA(4,1))
- Points, lines, planes, circles, spheres as **multivectors**
- Operations: `meet` (∧), `join`, `distance`, `project`, `offset`
- Transforms: **Motors** (unified rotation+translation, no matrices)
- Constraints: Natural algebraic equations (perpendicular = `L₁·L₂ = 0`)

**Implementation Phases (40-80 weeks):**
1. CGA Kernel MVP (8-12 weeks) - `Multivector`, semantic types, operations
2. Geometry Integration (6-10 weeks) - Integrate into TiaCAD core
3. Constraint System (10-16 weeks) - CGA-backed solver
4. BREP Refactor (6-8 weeks) - `CGAToCadQueryAdapter`
5. CAM Engine (8-12 weeks) - FDM slicing, CNC toolpaths
6. Performance & Polish (8-12 weeks)

**Reality Check:**
- 📚 Requires deep CGA expertise (PhD-level geometric algebra)
- 🔧 Massive refactor (entire codebase moves to CGA)
- ⏱️ 1-2 year project
- 🎓 Genuinely publishable research contribution

**When to Pursue:**
- After constraints are proven and component ecosystem has grown
- When ready for 2.0 architectural rewrite

**Documentation:** See `docs/architecture/CGA_V5_FUTURE_VISION.md` (1549 lines, complete specification)

---

## Explicitly Deferred

**These are NOT planned - documented for clarity:**

❌ **Multiple CAD Backends** (FreeCAD, build123d, etc.)
- **Why Not:** 3x testing burden, CadQuery works well
- **Decision:** Stay with CadQuery, enforce backend abstraction in new code

❌ **Animation/Motion**
- **Why Not:** Static CAD focus, different problem domain
- **Decision:** Out of scope for TiaCAD v1.x

---

## How This Roadmap Works

- **Updated:** When priorities change or quarterly reviews
- **Honest:** Reflects actual work, not aspirational plans
- **Flexible:** Options, not commitments
- **Clear:** No promises without timelines

---

**Last Decision:** Jul 2026 — Validation confidence ladder (Tiers 0-5) complete.
Next: Constraint Solver (Q4 2026). See `BACKLOG.md` for smaller open items in
the meantime (docs hygiene, CI lockfile, architecture debt).

---

## Key Documentation

**Planning & Vision:**
- **This file (ROADMAP.md):** Current priorities and strategic direction
- **CGA_V5_FUTURE_VISION.md:** Complete specification for revolutionary architecture (1549 lines)
- **ARCHITECTURE_DECISION_V3.md:** v3.0 spatial reference design rationale
- **KNOWN_LIMITATIONS.md:** Current constraints and workarounds

**Implementation Reference:**
- **CHANGELOG.md:** History of changes and completed work
- **BACKLOG.md:** Pointer to `tt` (project-embedded task tracker) — open action items
- **docs/developer/VALIDATION_STRENGTHENING.md:** Validation confidence-ladder plan (complete)
- **docs/archive/DAG_INCREMENTAL_REBUILD.md:** Dependency graph architecture and usage (shipped; kept as design record)
- **TESTING_GUIDE.md:** Test strategy and coverage
- **MIGRATION_GUIDE_V3.md:** Upgrading from v0.3.0 to v3.x

**Session References:**
- **ninja-xenarch-0316:** GitHub/stdlib imports, polygon primitive, m3_nut stdlib
- **enchanted-hydra-0316:** Component stdlib, watch --export, Tier 2 contracts
- **hidden-sorcerer-0215:** DAG foundation (Week 1-2, 53 tests)
