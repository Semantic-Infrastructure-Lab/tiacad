# Archive Summary

This directory contains **historical planning and tracking documents** from TiaCAD's development.

> 📚 **For Current Information:**
> - **Project Status / Roadmap:** See [ROADMAP.md](../../ROADMAP.md)
> - **Known Limitations:** See [KNOWN_LIMITATIONS.md](../../KNOWN_LIMITATIONS.md)
> - **Open backlog items:** See [BACKLOG.md](../../BACKLOG.md)
> - **Testing Guide:** See [TESTING_GUIDE](../developer/TESTING_GUIDE.md)

---

## Document Inventory

### Completed Work & Status Tracking

**✅ v3.0 Implementation** (Completed Nov 2025)
- [`V3_IMPLEMENTATION_STATUS.md`](V3_IMPLEMENTATION_STATUS.md) (278 lines) - v3.0 development tracking
- Status: Complete - 896 tests, unified spatial reference system

**✅ v3.1 Testing Confidence** (Completed Nov 2025)
- [`TESTING_CONFIDENCE_PLAN.md`](TESTING_CONFIDENCE_PLAN.md) (1,472 lines) - Testing strategy & execution plan
- Status: Phase 1 complete - 1025+ tests, testing utilities, correctness tests

**📊 Current Status Snapshot**
- [`CURRENT_STATUS.md`](CURRENT_STATUS.md) (316 lines) - Status as of Nov 16, 2025 (v3.1.1)
- Contains: Recent completions, test stats, documentation status

---

### Planning & Analysis Documents

**🗺️ Strategic Roadmap**
- [`TIACAD_EVOLUTION_ROADMAP.md`](TIACAD_EVOLUTION_ROADMAP.md) (1,011 lines)
- Date: Nov 2, 2025
- Content: Long-term vision from v3.0 → constraint-based CAD
- Note: Phase numbering differs from current README

**⚠️ Known Limitations Analysis**
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) (661 lines)
- Date: Nov 14, 2025
- Content: Detailed technical limitations, workarounds, improvement plans
- See [README - Known Limitations](../../README.md#known-limitations--future-roadmap) for current summary

**📝 Documentation Improvements**
- [`LANGUAGE_IMPROVEMENTS_STATUS.md`](LANGUAGE_IMPROVEMENTS_STATUS.md) (771 lines)
- Date: Nov 13, 2025
- Content: Language improvements tracking from Mental Models analysis
- Status: Most improvements incorporated into documentation

**🧪 Testing Strategy**
- [`TESTING_ROADMAP.md`](TESTING_ROADMAP.md) (699 lines)
- Content: Original testing roadmap and strategies
- Status: Superseded by [TESTING_GUIDE](../developer/TESTING_GUIDE.md)

---

### Archived 2026-07-11 (doc-coherence pass)

**✅ Fully shipped implementation plans**
- [`DAG_INCREMENTAL_REBUILD.md`](DAG_INCREMENTAL_REBUILD.md) - DAG/incremental-rebuild/watch-mode plan; feature shipped March 2026 (doc's own status line hadn't been updated, contradicting 4 other current docs)
- [`SKETCH_ABSTRACTION_DESIGN.md`](SKETCH_ABSTRACTION_DESIGN.md) - 2D sketch backend-abstraction design; all sketch ops (extrude/revolve/sweep/loft) long since shipped

**✅ Closed-out point-in-time reviews**
- [`PROJECT_REVIEW_2026-04-17.md`](PROJECT_REVIEW_2026-04-17.md) - senior review; findings actioned/superseded
- [`CODE_REVIEW_FOLLOWUPS_2026-04-18.md`](CODE_REVIEW_FOLLOWUPS_2026-04-18.md) - 5/5 findings checked off complete

**✅ Proposals that shipped exactly as proposed**
- [`DOCUMENTATION_CONSOLIDATION_PLAN.md`](DOCUMENTATION_CONSOLIDATION_PLAN.md) - proposed creating ROADMAP.md + KNOWN_LIMITATIONS.md; both now exist and match the proposal

**📉 Stale audits, superseded by later infra work**
- [`SKIPPED_TESTS_AUDIT.md`](SKIPPED_TESTS_AUDIT.md) - classified ~29 skips as "valid keep"; Phase-0 work (2026-07-10) turned exactly those into hard failures, making the audit actively misleading
- [`CODE_QUALITY_SUMMARY.md`](CODE_QUALITY_SUMMARY.md) - 7-month-old 10-file sample snapshot

---

### Archived 2026-07-11 (documentation-pass merge)

**🔁 Near-duplicate architecture-debt reviews, both dated 2026-04-18**
- [`OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md`](OPEN_ISSUES_AND_ARCHITECTURE_DEBT_2026-04-18.md) - debt register (backend global state, `OperationsBuilder` dispatch, `Part` coupling, `cli.py` size, visualization split, validation heuristics)
- [`ARCHITECTURE_REVIEW_2026-04-18.md`](ARCHITECTURE_REVIEW_2026-04-18.md) - senior-review pass covering the same findings from the same date
- Both superseded by `BACKLOG.md`'s "Architecture debt" section, which re-verified every claim against current code on 2026-07-11 (session `weightless-universe-0711`) and is the accurate, dated source of truth. `docs/architecture/README.md` and `ARCHITECTURE_NEXT_STEPS.md` updated to point to `BACKLOG.md` instead.

---

## Why Archive These?

These documents served critical roles during development:
- **Planning:** Guided architectural decisions and feature development
- **Tracking:** Monitored progress through complex multi-phase work
- **Analysis:** Deep dives into limitations and improvement opportunities
- **Communication:** Shared vision and status across sessions

They're archived because:
- ✅ **Plans executed** - Work is complete
- 📚 **Historical value** - Document decision-making process
- 📖 **Current docs updated** - Key information moved to active documentation
- 🔄 **Prevent confusion** - Clear what's current vs historical

---

## How to Use This Archive

**If you're looking for:**

| You Want | Go To |
|----------|-------|
| Current project status | [ROADMAP.md](../../ROADMAP.md) |
| Testing information | [TESTING_GUIDE](../developer/TESTING_GUIDE.md) |
| Known limitations | [KNOWN_LIMITATIONS.md](../../KNOWN_LIMITATIONS.md) |
| Open backlog items | [BACKLOG.md](../../BACKLOG.md) |
| How to test | [TESTING_QUICK_REFERENCE](../developer/TESTING_QUICK_REFERENCE.md) |
| Historical context | Browse this archive |
| How decisions were made | See individual archived docs |

---

## Archive Statistics

- **Total Files:** 16 markdown documents (8 from the original Nov-Dec 2025
  archive + 8 archived 2026-07-11)
- **Date Range:** Nov 2, 2025 - 2026-04-18 (content dates; archiving itself
  happened on 2025-12-01 and 2026-07-11)
- **Coverage:** v3.0 → v3.1.2 development cycle, plus the Q2-Q3 2026
  validation-confidence-ladder review cycle
- **Status:** All plans completed, superseded, or incorporated into current docs

---

**Last Updated:** 2026-07-11
