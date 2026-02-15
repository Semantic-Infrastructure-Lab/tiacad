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

### Option B: Dependency Graph (DAG)

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

**Implementation:**
- Week 1-2: ModelGraph using NetworkX
- Week 3-4: Dependency tracking (params → parts → ops)
- Week 5-6: Invalidation propagation
- Week 7-8: CLI integration (--watch, --show-deps)

**Effort:** 6-8 weeks (per original plan)
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
- **DAG** = Essential foundation + medium risk = **Infrastructure play**
- **Constraints** = High complexity + requires DAG = **Future milestone**

---

## How This Roadmap Works

- **Updated:** When priorities change or quarterly reviews
- **Honest:** Reflects actual work, not aspirational plans
- **Flexible:** Options, not commitments
- **Clear:** No promises without timelines

**Feedback:** File issues at `/home/scottsen/src/projects/tiacad` or discuss in sessions

---

**Last Decision:** Feb 2026 - Consolidate docs, establish clarity
**Next Decision:** Q2 2026 - Component system vs DAG vs maintenance
