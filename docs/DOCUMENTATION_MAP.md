# TiaCAD Documentation Map

**Your guide to navigating TiaCAD's documentation** - Find what you need quickly!

---

## 🚀 Getting Started (Read These First!)

**New to TiaCAD? Start here:**

1. **[Main README](../README.md)** - Project overview, quick start, and feature list
2. **[TUTORIAL](user/TUTORIAL.md)** - Step-by-step introduction to building your first models
3. **[EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md)** - Practical walkthrough of working examples

**Quick reference:** [GLOSSARY](user/GLOSSARY.md) - Key terminology and concepts

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
| [AI_DEBUG_WORKFLOW](developer/AI_DEBUG_WORKFLOW.md) | AI-assisted model debugging and debug bundle workflow | When reviewing model behavior with structured artifacts |
| [DAG_INCREMENTAL_REBUILD](developer/DAG_INCREMENTAL_REBUILD.md) | Dependency graph architecture and watch mode | When working on incremental rebuild or watch |
| [TERMINOLOGY_GUIDE](developer/TERMINOLOGY_GUIDE.md) | Canonical terminology decisions | When writing docs or code |
| [MIGRATION_GUIDE_V3](developer/MIGRATION_GUIDE_V3.md) | Upgrading from v0.3.0 to v3.x | When migrating old YAML files |
| [CLI](developer/CLI.md) | Command-line interface reference | When using tiacad CLI |
| [SCHEMA_VALIDATION](developer/SCHEMA_VALIDATION.md) | Schema validation system | When working with validation |

**Code Quality & Technical Debt:**

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [SKIPPED_TESTS_AUDIT](../SKIPPED_TESTS_AUDIT.md) | Analysis of 69 skipped tests | Understanding test coverage gaps |
| [CODE_QUALITY_SUMMARY](../CODE_QUALITY_SUMMARY.md) | Code quality assessment (reveal --check) | Understanding code health |

**Quick Tips:**
- **Running tests?** → [TESTING_QUICK_REFERENCE](developer/TESTING_QUICK_REFERENCE.md)
- **Validating model correctness?** → [MODEL_VALIDATION](developer/MODEL_VALIDATION.md)
- **Writing docs?** → [TERMINOLOGY_GUIDE](developer/TERMINOLOGY_GUIDE.md)
- **Contributing code?** → [TESTING_GUIDE](developer/TESTING_GUIDE.md)
- **Upgrading YAML?** → [MIGRATION_GUIDE_V3](developer/MIGRATION_GUIDE_V3.md)
- **Understanding technical debt?** → [SKIPPED_TESTS_AUDIT](../SKIPPED_TESTS_AUDIT.md)

---

## 🏗️ Architecture & Design

**Understanding TiaCAD's Design:**

| Document | Purpose | Level |
|----------|---------|-------|
| [SIL_INTEGRATION](SIL_INTEGRATION.md) | ⭐ How TiaCAD embodies SIL principles | Beginner |
| [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md) | v3.0 design rationale and decisions | Intermediate |
| [CLEAN_ARCHITECTURE_PROPOSAL](architecture/CLEAN_ARCHITECTURE_PROPOSAL.md) | Architecture principles and patterns | Advanced |
| [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md) | Language design philosophy | Intermediate |
| [SKETCH_ABSTRACTION_DESIGN](architecture/SKETCH_ABSTRACTION_DESIGN.md) | 2D sketch system design | Advanced |
| [CGA_V5_FUTURE_VISION](architecture/CGA_V5_FUTURE_VISION.md) | 🔮 Future v5.0+ vision (aspirational) | Research |

**Architecture Diagrams:**
- [Reference-Based vs Hierarchical](architecture/diagrams/reference-based-vs-hierarchical.md)
- [Local Frame Offsets](architecture/diagrams/local-frame-offsets.md)
- [Operation Categories](architecture/diagrams/operation-categories.md)
- [Auto-Reference Visualization](architecture/diagrams/auto-reference-visualization.md)

**Quick Tips:**
- **Understanding SIL principles?** → [SIL_INTEGRATION](SIL_INTEGRATION.md) ⭐ Start here!
- **Understanding v3.0 design?** → [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md)
- **Future vision?** → [CGA_V5_FUTURE_VISION](architecture/CGA_V5_FUTURE_VISION.md) ⚠️ Aspirational
- **Design philosophy?** → [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md)

---

## 📚 Historical / Archive

**Historical planning and development tracking:**

See [Archive Summary](archive/ARCHIVE_SUMMARY.md) for:
- v3.0 & v3.1 implementation status
- Testing strategy and execution plans
- Strategic roadmaps and planning docs
- Known issues analysis (historical)

⚠️ **Note:** These documents are **historical**. For current information, see the main README.

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

**Understand design decisions:**
1. Start with [SIL_INTEGRATION](SIL_INTEGRATION.md) for high-level principles
2. Then [ARCHITECTURE_DECISION_V3](architecture/ARCHITECTURE_DECISION_V3.md) for v3.0 specifics
3. Read [MENTAL_MODELS_AND_LANGUAGE](architecture/MENTAL_MODELS_AND_LANGUAGE.md)
4. Deep dive: [CLEAN_ARCHITECTURE_PROPOSAL](architecture/CLEAN_ARCHITECTURE_PROPOSAL.md)

**Run tests:**
1. Quick commands: [TESTING_QUICK_REFERENCE](developer/TESTING_QUICK_REFERENCE.md)
2. Detailed guide: [TESTING_GUIDE](developer/TESTING_GUIDE.md)
3. Correctness model: [MODEL_VALIDATION](developer/MODEL_VALIDATION.md)

**Use the CLI:**
1. See [CLI](developer/CLI.md) for complete reference

---

## 📈 Documentation Priorities

**Most important documents by usage:**
1. [Main README](../README.md) - Start here
2. [SIL_INTEGRATION](SIL_INTEGRATION.md) - ⭐ NEW: Understanding SIL principles
3. [TUTORIAL](user/TUTORIAL.md) - Learn by doing
4. [YAML_REFERENCE](user/YAML_REFERENCE.md) - Syntax lookup
5. [TESTING_GUIDE](developer/TESTING_GUIDE.md) - For contributors
6. [MODEL_VALIDATION](developer/MODEL_VALIDATION.md) - For correctness and AI review

---

## 🆘 Still Can't Find It?

**Common questions:**

| Question | Answer |
|----------|--------|
| "How do I install TiaCAD?" | [README - Quick Start](../README.md#quick-start) |
| "What version am I using?" | Check `pyproject.toml` or run tests |
| "Where are the examples?" | `examples/` directory + [EXAMPLES_GUIDE](user/EXAMPLES_GUIDE.md) |
| "How do I report a bug?" | Create GitHub issue (see README) |
| "What's the roadmap?" | [README - What's Next](../README.md#whats-next) |
| "Is feature X supported?" | [README - What You Get](../README.md#quick-start) |

**For current project status:** Always check [Main README](../README.md) first!

---

**Status:** Active documentation map
**Scope:** Current user, developer, architecture, and historical docs
