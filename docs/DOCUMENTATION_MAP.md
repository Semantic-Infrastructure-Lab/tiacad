# TiaCAD Documentation Map

**Your guide to navigating TiaCAD's documentation** - Find what you need quickly!

*Regenerated 2026-07-11 from a full doc-coherence pass — every link below was
checked against the actual current file layout.*

---

## 🚀 Getting Started (Read These First!)

**New to TiaCAD? Start here:**

1. **[Main README](../README.md)** - Project overview, quick start, and feature list
2. **[TUTORIAL](user/TUTORIAL.md)** - Step-by-step introduction to building your first models
3. **[EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md)** - Practical walkthrough of working examples

**Quick reference:** [GLOSSARY](user/GLOSSARY.md) - Key terminology and concepts

---

## 🧭 Current Status & Planning (Check These for "What's True Right Now")

**The living docs — updated as work ships, not point-in-time snapshots:**

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [ROADMAP](../ROADMAP.md) | Current priorities, what shipped, strategic direction | Understanding where the project is headed |
| [KNOWN_LIMITATIONS](../KNOWN_LIMITATIONS.md) | Current constraints, workarounds, fixed-bug log | Before assuming something works a certain way |
| [BACKLOG](../BACKLOG.md) | Consolidated open action items across all docs | Looking for something concrete to work on |
| [CHANGELOG](../CHANGELOG.md) | History of shipped changes, version by version | What changed and when |
| [VALIDATION_STRENGTHENING](developer/VALIDATION_STRENGTHENING.md) | Testing/validation confidence-ladder plan (complete) | Understanding the test-correctness strategy |

---

## 📖 User Documentation

**Building Models with TiaCAD:**

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [YAML_REFERENCE](user/YAML_REFERENCE.md) | Complete YAML syntax reference | When you need to look up specific syntax |
| [GLOSSARY](user/GLOSSARY.md) | Terminology and concept definitions | When you encounter unfamiliar terms |
| [AUTO_REFERENCES_GUIDE](user/AUTO_REFERENCES_GUIDE.md) | Spatial anchors and positioning | When positioning parts with anchors |
| [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md) | Detailed example walkthroughs | When you want to learn by example |
| [TUTORIAL](user/TUTORIAL.md) | Beginner-friendly introduction | When you're completely new |

**Quick Tips:**
- **Don't know where to start?** → [TUTORIAL](user/TUTORIAL.md)
- **Need syntax help?** → [YAML_REFERENCE](user/YAML_REFERENCE.md)
- **Want to see examples?** → [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md)
- **Confused by terms?** → [GLOSSARY](user/GLOSSARY.md)

---

## 🔧 Developer Documentation

**Contributing to TiaCAD:**

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [TESTING_GUIDE](developer/TESTING_GUIDE.md) | Comprehensive testing strategies | When writing or running tests |
| [TESTING_QUICK_REFERENCE](developer/TESTING_QUICK_REFERENCE.md) | Quick test commands | When you just need the command |
| [MODEL_VALIDATION](developer/MODEL_VALIDATION.md) | Correctness evidence model for numeric, visual, and AI review | When deciding how to prove a model is right |
| [VALIDATION_CASE_STUDY_MOUNTING_HOLES](developer/VALIDATION_CASE_STUDY_MOUNTING_HOLES.md) | Worked example: a real boolean-that-did-nothing bug, how it was found, why tests missed it | When you want the validation model made concrete |
| [AI_DEBUG_WORKFLOW](developer/AI_DEBUG_WORKFLOW.md) | AI-assisted model debugging and debug bundle workflow | When reviewing model behavior with structured artifacts |
| [TERMINOLOGY_GUIDE](developer/TERMINOLOGY_GUIDE.md) | Canonical terminology decisions | When writing docs or code |
| [MIGRATION_GUIDE_V3](developer/MIGRATION_GUIDE_V3.md) | Upgrading from v0.3.0 to v3.x | When migrating old YAML files |
| [API_DEPRECATION_STRATEGY](developer/API_DEPRECATION_STRATEGY.md) | Plan for runtime deprecation warnings on old syntax | Working on cone/pattern syntax deprecation |
| [CLI](developer/CLI.md) | Command-line interface reference | When using tiacad CLI |
| [SCHEMA_VALIDATION](developer/SCHEMA_VALIDATION.md) | Schema validation system | When working with validation |
| [scripts/migrations/README](../scripts/migrations/README.md) | Warning + usage notes for one-off in-place migration scripts | Before running any script in `scripts/migrations/` |

**Quick Tips:**
- **Running tests?** → [TESTING_QUICK_REFERENCE](developer/TESTING_QUICK_REFERENCE.md)
- **Validating model correctness?** → [MODEL_VALIDATION](developer/MODEL_VALIDATION.md)
- **Writing docs?** → [TERMINOLOGY_GUIDE](developer/TERMINOLOGY_GUIDE.md)
- **Contributing code?** → [TESTING_GUIDE](developer/TESTING_GUIDE.md)
- **Upgrading YAML?** → [MIGRATION_GUIDE_V3](developer/MIGRATION_GUIDE_V3.md)
- **Looking for architecture debt / open issues?** → [BACKLOG](../BACKLOG.md)

---

## 🏗️ Architecture & Design

**Understanding TiaCAD's Design:**

| Document | Purpose | Level |
|----------|---------|-------|
| [SIL_INTEGRATION](SIL_INTEGRATION.md) | ⭐ How TiaCAD embodies SIL principles | Beginner |
| [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md) | v3.0 design rationale (✅ implemented) | Intermediate |
| [CLEAN_ARCHITECTURE_PROPOSAL](architecture/CLEAN_ARCHITECTURE_PROPOSAL.md) | v3.0 architecture principles and patterns (✅ implemented; kept as design record) | Advanced |
| [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md) | Language design philosophy | Intermediate |
| [ARCHITECTURE_NEXT_STEPS](architecture/ARCHITECTURE_NEXT_STEPS.md) | Near-term architecture plan | Intermediate |
| [CGA_V5_FUTURE_VISION](architecture/CGA_V5_FUTURE_VISION.md) | 🔮 Future v5.0+ vision (aspirational, 2027+) | Research |

**Architecture Diagrams:**
- [Reference-Based vs Hierarchical](architecture/diagrams/reference-based-vs-hierarchical.md)
- [Local Frame Offsets](architecture/diagrams/local-frame-offsets.md)
- [Operation Categories](architecture/diagrams/operation-categories.md)
- [Auto-Reference Visualization](architecture/diagrams/auto-reference-visualization.md)
- [Reference Chain Dependencies](architecture/diagrams/reference-chain-dependencies.md)

**Quick Tips:**
- **Understanding SIL principles?** → [SIL_INTEGRATION](SIL_INTEGRATION.md) ⭐ Start here!
- **Understanding v3.0 design?** → [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md)
- **Future vision?** → [CGA_V5_FUTURE_VISION](architecture/CGA_V5_FUTURE_VISION.md) ⚠️ Aspirational
- **Design philosophy?** → [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md)

---

## 📚 Historical / Archive

**Historical planning, closed-out reviews, and superseded design docs — all in `docs/archive/`:**

See [Archive Summary](archive/ARCHIVE_SUMMARY.md) for the full inventory. Notable entries:
- `DAG_INCREMENTAL_REBUILD.md` — original implementation plan; feature shipped March 2026
- `SKETCH_ABSTRACTION_DESIGN.md` — design doc; sketch ops (extrude/revolve/sweep/loft) all shipped
- `PROJECT_REVIEW_2026-04-17.md`, `CODE_REVIEW_FOLLOWUPS_2026-04-18.md` — closed-out point-in-time reviews
- `DOCUMENTATION_CONSOLIDATION_PLAN.md` — its own proposal (create ROADMAP.md + KNOWN_LIMITATIONS.md) already executed
- `SKIPPED_TESTS_AUDIT.md`, `CODE_QUALITY_SUMMARY.md` — retired 2026-07-11; superseded by Phase-0 skip→hard-failure work
- `OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md`, `ARCHITECTURE_REVIEW_2026-04-18.md` — retired 2026-07-11; near-duplicate architecture-debt reviews from the same date, superseded by `BACKLOG.md`'s re-verified "Architecture debt" section
- v3.0 & v3.1 implementation status, testing strategy/execution plans, strategic roadmaps, known-issues analysis (all historical)

⚠️ **Note:** These documents are **historical**. For current information, see [ROADMAP](../ROADMAP.md) and [KNOWN_LIMITATIONS](../KNOWN_LIMITATIONS.md).

**Also historical, not yet physically archived (kept in place, marked in-doc):**
`RELEASE_NOTES_V3.md` (v3.1.0, superseded by v3.1.2 — see CHANGELOG.md).

---

## 📊 Quick Navigation by Task

### "I want to..."

**Learn TiaCAD:**
1. Read [Main README](../README.md) overview
2. Follow [TUTORIAL](user/TUTORIAL.md)
3. Explore [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md)
4. Reference [YAML_REFERENCE](user/YAML_REFERENCE.md) as needed

**Build a specific model:**
1. Check [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md) for similar examples
2. Reference [YAML_REFERENCE](user/YAML_REFERENCE.md) for syntax
3. Use [GLOSSARY](user/GLOSSARY.md) for terminology

**Contribute code:**
1. Read [TESTING_GUIDE](developer/TESTING_GUIDE.md)
2. Follow [TERMINOLOGY_GUIDE](developer/TERMINOLOGY_GUIDE.md) conventions
3. See [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md) for context
4. Check [BACKLOG](../BACKLOG.md) for open work

**Understand design decisions:**
1. Start with [SIL_INTEGRATION](SIL_INTEGRATION.md) for high-level principles
2. Then [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md) for v3.0 specifics
3. Read [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md)
4. Deep dive: [CLEAN_ARCHITECTURE_PROPOSAL](architecture/CLEAN_ARCHITECTURE_PROPOSAL.md)

**Run tests:**
1. Quick commands: [TESTING_QUICK_REFERENCE](developer/TESTING_QUICK_REFERENCE.md)
2. Detailed guide: [TESTING_GUIDE](developer/TESTING_GUIDE.md)
3. Correctness model: [MODEL_VALIDATION](developer/MODEL_VALIDATION.md)
4. Confidence-ladder plan: [VALIDATION_STRENGTHENING](developer/VALIDATION_STRENGTHENING.md)

**Use the CLI:**
1. See [CLI](developer/CLI.md) for complete reference

**Find out what's next / what to work on:**
1. [ROADMAP](../ROADMAP.md) for the strategic track (Constraint Solver, CGA v5.0)
2. [BACKLOG](../BACKLOG.md) for smaller, scattered open items

---

## 📈 Documentation Priorities

**Most important documents by usage:**
1. [Main README](../README.md) - Start here
2. [ROADMAP](../ROADMAP.md) - Current priorities and what shipped
3. [KNOWN_LIMITATIONS](../KNOWN_LIMITATIONS.md) - What doesn't work yet, and why
4. [SIL_INTEGRATION](SIL_INTEGRATION.md) - Understanding SIL principles
5. [TUTORIAL](user/TUTORIAL.md) - Learn by doing
6. [YAML_REFERENCE](user/YAML_REFERENCE.md) - Syntax lookup
7. [TESTING_GUIDE](developer/TESTING_GUIDE.md) - For contributors
8. [MODEL_VALIDATION](developer/MODEL_VALIDATION.md) - For correctness and AI review

---

## 🆘 Still Can't Find It?

**Common questions:**

| Question | Answer |
|----------|--------|
| "How do I install TiaCAD?" | [README - Quick Start](../README.md#quick-start) |
| "What version am I using?" | Check `pyproject.toml`, or see `ROADMAP.md` header |
| "Where are the examples?" | `examples/` directory + [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md) |
| "How do I report a bug?" | Create GitHub issue (see README) |
| "What's the roadmap?" | [ROADMAP.md](../ROADMAP.md) |
| "Is feature X supported?" | [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md), then [README - What You Get](../README.md#quick-start) |
| "What's left to do?" | [BACKLOG.md](../BACKLOG.md) |

**For current project status:** Always check [ROADMAP](../ROADMAP.md) and [KNOWN_LIMITATIONS](../KNOWN_LIMITATIONS.md) first!

---

**Status:** Active documentation map — regenerated 2026-07-11
**Scope:** Current user, developer, architecture, planning, and historical docs
