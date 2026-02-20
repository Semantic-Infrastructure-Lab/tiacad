# TiaCAD Roadmap

**Last Updated:** 2026-02-15
**Current Version:** v3.1.2 (+19 maintenance commits)

---

## Current Focus (Q1 2026)

**Status:** 🟡 **Maintenance Mode**

TiaCAD v3.1.2 is production-ready with solid mathematical foundations and comprehensive testing. Current work focuses on stability and ecosystem health:

**Active Work:**
- ✅ Fixed 21 examples (50% → 95% pass rate) - API migrations complete
- ✅ Infrastructure validation (dependencies, test suite, CI)
- 🔧 Fixing 17 test failures:
  - 11 hull builder tests (CadQuery 2.7.0 STL import issue)
  - 6 visual regression tests (missing reference images)
- 📝 Documentation consolidation (this roadmap!)

**Reality Check:** No active feature development as of Feb 2026. Focus is on stability, examples, and clarity.

---

## Strategic Recommendation

**🎯 Recommended Path (2026):**

1. **Q2 2026:** Component/Module System (3-4 weeks) - **Ecosystem foundation**
2. **Q3 2026:** Complete DAG implementation (4-6 weeks) - **Performance infrastructure**
3. **Q4 2026:** Constraint Solver (10-16 weeks) - **Parametric design capabilities**
4. **2027+:** CGA v5.0 Architecture (40-80 weeks) - **Research moonshot**

**Rationale:** Build ecosystem value first (components enable community growth), then complete infrastructure (DAG + constraints), then pursue revolutionary architecture (CGA) as 2.0 rewrite.

---

## Near-Term Possibilities (Q2 2026)

**Decision Needed:** What delivers most value to open-source modeling community?

### Option A: Component/Module System 🏆 **(Recommended)**

**Vision:** npm/cargo for CAD - reusable, shareable, parametric components

**Impact:** 🔥🔥🔥🔥🔥 (Ecosystem-defining)
- Build real things without modeling every screw from primitives
- Community contributions create compounding value
- Lower barrier to entry (assemble vs model)
- Git-friendly component sharing

**What You'll Be Able to Do:**
```yaml
imports:
  - tiacad://std/hardware/m3_screw
  - github:scottsen/guitar-hangers/hook
  - ./bracket.yaml

parts:
  bracket:
    component: bracket
    parameters: {width: 50mm}

  screws:
    component: m3_screw
    parameters: {length: 20mm}
    pattern: {positions: [bracket.hole_1, bracket.hole_2, ...]}
```

**Implementation:**
- Week 1-2: Import system (local files, parameter passing)
- Week 2-3: Standard library (ISO hardware, bearings, gears)
- Week 3-4: GitHub imports (github:user/repo/file.yaml)
- Week 4: Documentation & examples

**Effort:** 3-4 weeks
**Timeline:** Mar-Apr 2026 (if prioritized)

---

### Option B: Dependency Graph (DAG) ⚡ **← Week 1-2 Complete!**

**Vision:** True parametric modeling with incremental rebuilds

**Impact:** 🔥🔥🔥 (Essential but invisible)
- 10x faster rebuilds when changing parameters
- Watch mode (auto-rebuild on save)
- Circular dependency detection

**What You'll Be Able to Do:**
```yaml
parameters:
  screw_diameter: 3mm  # Change this
  # ... 500 lines ...

# Only rebuilds parts depending on screw_diameter
# Not the entire model
```

**Current Status (Feb 2026):**
- ✅ Week 1-2: Foundation complete (53 tests passing)
  - Core DAG module (ModelGraph, GraphBuilder, Visualizer)
  - Cycle detection working
  - CLI `--show-deps` flag integrated
  - Session: `hidden-sorcerer-0215`

**Remaining Implementation:**
- Week 3-4: Full dependency tracking (patterns, references, sketches)
- Week 5-6: InvalidationTracker + IncrementalBuilder
- Week 7-8: Watch mode + performance benchmarking

**Effort:** 4-6 more weeks (already 25% done)
**Timeline:** Apr-Jun 2026 (if prioritized)

---

### Option C: Stay in Maintenance Mode

**Rational Choice:** TiaCAD works well for current use cases

- Focus on fixing test failures
- Improve documentation and examples
- Let community feedback guide priorities
- Wait for clear signal on what's needed

---

## Long-Term Vision (6-12 months)

**These require significant investment - only pursue with clear need:**

### Constraint Solver
**What:** Declarative assemblies ("make these flush")
**Requires:** DAG first (Phase 4b + 5 from original plan)
**Effort:** 16-22 weeks total
**Impact:** Intent-based modeling like SolidWorks/Fusion360

```yaml
constraints:
  - type: flush
    faces: [bracket.bottom, base.top]
  - type: coaxial
    axes: [shaft.axis, bearing.inner]
```

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

---

## The Moonshot: CGA v5.0 Architecture (2027+)

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
- ⏱️ 1-2 year project (vs 3-4 weeks for component system)
- 🎓 Genuinely publishable research contribution

**When to Pursue:**
- After component system + DAG + constraints are proven
- When ready for 2.0 architectural rewrite
- If pursuing CAD research/innovation

**Documentation:** See `docs/architecture/CGA_V5_FUTURE_VISION.md` (1549 lines, complete specification)

---

## Explicitly Deferred

**These are NOT planned - documented for clarity:**

❌ **Multiple CAD Backends** (FreeCAD, build123d, etc.)
- **Why Not:** 3x testing burden, CadQuery works well
- **Decision:** Stay with CadQuery, enforce backend abstraction in new code

❌ **Constraint Solver (near-term)**
- **Why Not:** Requires DAG first, complex implementation
- **Decision:** Defer until DAG is proven and working

❌ **Animation/Motion**
- **Why Not:** Static CAD focus, different problem domain
- **Decision:** Out of scope for TiaCAD v1.x

---

## Decision Framework

**When choosing what to build next, prioritize:**

1. **Community Value** - Does it solve real user problems?
2. **Ecosystem Effects** - Does it enable others to contribute?
3. **TiaCAD Strengths** - Does it leverage YAML + Git + Declarative?
4. **Implementation Risk** - Can we deliver in reasonable time?

**Current Assessment (Feb 2026):**
- **Component System** = High value + ecosystem growth + low risk = **Best ROI**
- **DAG Completion** = 25% done, finish infrastructure = **Complete what we started**
- **Constraints** = High complexity + requires DAG = **Future milestone**
- **CGA v5** = World-class moonshot + massive scope = **Research when ready**

---

## How This Roadmap Works

- **Updated:** When priorities change or quarterly reviews
- **Honest:** Reflects actual work, not aspirational plans
- **Flexible:** Options, not commitments
- **Clear:** No promises without timelines

**Feedback:** File issues at `/home/scottsen/src/projects/tiacad` or discuss in sessions

---

**Last Decision:** Feb 2026 - Strategic recommendation: Components → DAG → Constraints → CGA v5
**Next Decision:** Q2 2026 - Component system vs DAG completion vs maintenance

---

## Key Documentation

**Planning & Vision:**
- **This file (ROADMAP.md):** Current priorities and strategic direction
- **CGA_V5_FUTURE_VISION.md:** Complete specification for revolutionary architecture (1549 lines)
- **ARCHITECTURE_DECISION_V3.md:** v3.0 spatial reference design rationale
- **KNOWN_LIMITATIONS.md:** Current constraints and workarounds

**Implementation Reference:**
- **CHANGELOG.md:** History of changes and completed work
- **TESTING_GUIDE.md:** Test strategy and coverage
- **MIGRATION_GUIDE_V3.md:** Upgrading from v0.3.0 to v3.x

**Session References:**
- **hidden-sorcerer-0215:** DAG Week 1-2 implementation (53 tests, foundation complete)
- **charcoal-ray-0215:** DAG implementation plan (8-week roadmap)
