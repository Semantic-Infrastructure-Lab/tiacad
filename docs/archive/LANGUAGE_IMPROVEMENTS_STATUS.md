# TiaCAD Language & Documentation Improvements - Status Tracker

**Purpose**: Track the implementation status of language improvements and documentation enhancements based on PR #14 (Mental Models & Language Design) and subsequent analysis.

**Last Updated**: 2025-11-13
**Session**: regavela-1113
**Related Documents**:
- [MENTAL_MODELS_AND_LANGUAGE.md](../docs/MENTAL_MODELS_AND_LANGUAGE.md) - Original PR #14 recommendations
- [GLOSSARY.md](../GLOSSARY.md) - User-facing glossary
- [TIACAD_LANGUAGE_GAP_ANALYSIS.md](../../tia/sessions/regavela-1113/TIACAD_LANGUAGE_GAP_ANALYSIS.md) - Detailed gap analysis

---

## Executive Summary

**Status as of 2025-11-14**: ✅ **Phase 2 Complete** (Medium-Term Improvements)

| Phase | Status | Items | Completion |
|-------|--------|-------|------------|
| **Phase 1: Quick Wins** | ✅ Complete | 4/4 | 100% |
| **Phase 2: Medium-Term** | ✅ Complete | 4/5 | 80% |
| **Phase 3: Long-Term (v4.0)** | ⏸️ Not Started | 0/5 | 0% |

**Total Effort**:
- Phase 1: 8 hours (COMPLETE ✅)
- Phase 2: 17 hours (COMPLETE ✅ - 4/5 items, deferred auto-reference naming research)
- Phase 3: 200+ hours (estimated, breaking changes)

---

## Timeline

| Date | Event | Impact |
|------|-------|--------|
| 2025-11-06 | PR #14 merged (MENTAL_MODELS_AND_LANGUAGE.md) | Strategic recommendations documented |
| 2025-11-13 | Gap analysis completed (regavela-1113) | Current state assessed vs recommendations |
| 2025-11-13 | Phase 1 implemented (regavela-1113) | Mental model explicit, anchors language added, glossary created |
| 2025-11-14 | Phase 2.1-2.3 implemented (3/5 items) | Visual diagrams, YAML aliases, enhanced metadata |
| 2025-11-14 | Phase 2.5 implemented (terminology) | Canonical terminology guide created, 30+ terms standardized |
| TBD | Phase 3 (v4.0) start | Breaking changes, syntax redesign |

---

## Phase 1: Quick Wins (COMPLETE ✅)

**Goal**: Improve documentation clarity without breaking changes
**Effort**: 8 hours
**Status**: ✅ Complete (2025-11-13)

### 1.1 Mental Model Section in README ✅

**Status**: ✅ Implemented (2025-11-13)
**Effort**: 1 hour
**Files Modified**: `README.md`

**What Was Done**:
- Added section "TiaCAD's Design Philosophy: Reference-Based Composition"
- Location: README.md lines 79-115 (after "What is TiaCAD?")
- Includes comparison tables (TiaCAD vs Traditional CAD, vs OpenSCAD)
- Explains independent parts, spatial anchors, declarative model
- Links to GLOSSARY.md and AUTO_REFERENCES_GUIDE.md

**Impact**: Users immediately understand TiaCAD's paradigm differs from traditional CAD

**Validation**:
- [ ] User feedback collected
- [ ] New user comprehension tested
- [x] Documentation reviewed for clarity

---

### 1.2 Comprehensive Glossary ✅

**Status**: ✅ Implemented (2025-11-13)
**Effort**: 2 hours
**Files Created**: `GLOSSARY.md`

**What Was Done**:
- Created 650+ line glossary with 9 major sections
- Defines: Part, Anchor, Reference-Based Composition, Operations, Parameters
- Includes "TiaCAD vs Traditional CAD" comparisons
- Includes "TiaCAD vs Procedural Tools" comparisons
- Spatial concepts (Face, Normal, Local Frame, Offset)
- Technical terms (SpatialRef, SpatialResolver, Backend)
- Common confusion points with FAQs
- Quick reference term translation table
- Learning path guidance

**Impact**: Users can look up confusing terms and understand them in context

**Future Enhancements**:
- [ ] Add visual diagrams to glossary entries
- [ ] Link from error messages to relevant glossary entries
- [ ] Add examples for each term
- [ ] User-contributed terminology feedback

---

### 1.3 "Anchors" Language Throughout Docs ✅

**Status**: ✅ Implemented (2025-11-13)
**Effort**: 2 hours
**Files Modified**:
- `AUTO_REFERENCES_GUIDE.md`
- `YAML_REFERENCE.md`
- `TUTORIAL.md`

**What Was Done**:

#### AUTO_REFERENCES_GUIDE.md
- Enhanced Overview with "anchor" metaphor
- "Think of anchors as: Marked spots on a workbench..."
- Explains WHY "anchors" (ship's anchor metaphor)
- Lists 4 key benefits of anchors

#### YAML_REFERENCE.md
- Changed section header to "References (Spatial Anchors) - v3.0"
- Added "What are references?" intro
- Changed "Named References" → "Named References (Custom Anchors)"
- Pattern: "spatial references (we call them **anchors**)"

#### TUTORIAL.md
- Added NEW SECTION: "Positioning Parts with Anchors"
- Location: After "Creating Holes" section
- Explains anchor concept with workbench metaphor
- Shows stacking boxes example with `base.face_top`
- Table of common auto-generated anchors
- Using anchors with offsets example
- Benefits list (no math, self-updating, readable, less error-prone)

**Impact**: "Anchor" is now primary user-facing term, "reference" as technical alternative

**Consistency Check**:
- [x] All user-facing docs use "anchor" metaphor
- [x] Technical docs can still use "reference" or "SpatialRef"
- [x] Examples demonstrate anchor usage
- [ ] Error messages updated to use "anchor" terminology

---

### 1.4 Categorized Operations in YAML_REFERENCE ✅

**Status**: ✅ Implemented (2025-11-13)
**Effort**: 3 hours
**Files Modified**: `YAML_REFERENCE.md`

**What Was Done**:
- Reorganized Operations section (line 462+)
- Added "Operations: Understanding the Four Types" introduction
- Created category comparison table with "Think of it as..." metaphors
- Restructured into 4 clear sections:
  1. **Positioning Operations (Transforms)** - Move/rotate/scale
  2. **Shape Modification Operations (Features)** - Fillet/chamfer/extrude/revolve/sweep/loft
  3. **Combining Operations (Booleans)** - Union/difference/intersection
  4. **Replication Operations (Patterns)** - Linear/circular/grid
- Each section has purpose statement and metaphor

**Impact**: Users understand operation categories before learning syntax

**Future Enhancements**:
- [ ] Add visual diagram showing operation categories
- [ ] Cross-reference from GLOSSARY.md operation types section
- [ ] Add "When to use" guidance for each category
- [ ] Examples showing operations used together

---

## Phase 2: Medium-Term Improvements (COMPLETE ✅)

**Goal**: Enhance usability with visual aids and ergonomic improvements
**Effort**: 14 hours actual (22 hours estimated)
**Status**: ✅ Complete (2025-11-14) - 3/4 items (deferred auto-reference naming research)
**Target Milestone**: v3.2

### 2.1 Visual Diagrams 📊 ✅

**Status**: ✅ Complete (2025-11-14)
**Effort**: 8 hours
**Priority**: HIGH (most impactful single improvement)

**Created Diagrams**:
1. **Reference-Based vs Hierarchical Assembly** - Side-by-side Mermaid comparison
2. **Auto-Reference Visualization** - Complete visual guide with all anchor types
3. **Local Frame Offset Illustration** - World vs local coordinates with examples
4. **Reference Chain Dependencies** - Simple/complex chains, validation patterns
5. **Operation Categories Visual** - Four types with decision tree and best practices

**Format**: Mermaid diagrams (editable, version-controllable) ✅

**Target Locations** (all implemented):
- ✅ README.md (mental model section)
- ✅ GLOSSARY.md (term definitions)
- ✅ YAML_REFERENCE.md (operations, references)
- ✅ AUTO_REFERENCES_GUIDE.md (anchor visualization)

**Tasks Completed**:
- [x] Design diagram concepts
- [x] Create Mermaid diagrams (5 comprehensive markdown files)
- [x] Integrate into documentation (4 files updated)
- [ ] Validate clarity with test users (pending user feedback)

---

### 2.2 YAML Alias Support: `anchors:` 🔧 ✅

**Status**: ✅ Complete (2025-11-14)
**Effort**: 4 hours
**Priority**: MEDIUM

**Goal**: Allow `anchors:` as alias for `references:` in YAML files ✅

**Implementation** (completed):
- Added `TiaCADParser._normalize_yaml_aliases()` method
- Normalizes `anchors:` to `references:` before processing
- Validates that both sections aren't used simultaneously
- Fully backward compatible

**Changes Completed**:
- [x] YAML loader update (tiacad_parser.py)
- [x] Documentation showing both forms
- [x] Examples using `anchors:` syntax (examples/anchors_demo.yaml)
- [x] Tests for alias support (3 new tests in test_tiacad_parser.py)
- [x] CHANGELOG.md updated

**Documentation Updates Completed**:
- [x] YAML_REFERENCE.md: Shows both `references:` and `anchors:` with examples
- [x] Examples: Created anchors_demo.yaml demonstrating new syntax

---

### 2.3 Enhanced Metadata Section 📋 ✅

**Status**: ✅ Complete (2025-11-14)
**Effort**: 2 hours
**Priority**: LOW

**Goal**: Add `type:` and `composition:` fields to metadata to make document purpose explicit ✅

**Enhanced Metadata** (implemented):
```yaml
metadata:
  name: Guitar Hanger
  type: assembly              # NEW: model/assembly/part/mechanism/fixture
  description: Wall-mounted guitar hanger
  composition: reference-based # NEW: Explicit mental model declaration
```

**Valid type values**:
- `part` - Single part design
- `assembly` - Multiple parts combined
- `model` - Complete model/design
- `mechanism` - Moving parts assembly
- `fixture` - Jig or mounting fixture

**Changes Completed**:
- [x] Documentation updated (YAML_REFERENCE.md)
- [x] Example created (examples/enhanced_metadata_demo.yaml)
- [x] CHANGELOG.md updated
- [x] Fields are optional (backward compatible)

---

### 2.4 Auto-Reference Naming Research 🔍

**Status**: ⏸️ Deferred (LOW priority, research-only)
**Effort**: 8 hours
**Priority**: LOW (research/validation)

**Goal**: Validate current auto-reference naming is intuitive, consider alternatives

**Current Naming**: `.face_top`, `.face_left`, `.center`, `.axis_z`

**Questions to Research**:
1. Is `.face_top` more intuitive than `.top_face`? (adjective-noun vs noun-adjective)
2. Should we add aliases? (`.top_surface` in addition to `.face_top`?)
3. Are axis names clear? (`.axis_x` vs `.x_axis`?)
4. Should there be more semantic names? (`.mounting_surface` auto-generated for top faces?)

**Research Method**:
- [ ] User testing with new users (5-10 participants)
- [ ] Survey existing users on terminology
- [ ] A/B test documentation with different naming
- [ ] Analyze confusion points in support questions

**Deliverables**:
- [ ] Research report with findings
- [ ] Recommendations for naming improvements
- [ ] If changes needed: Migration plan for v4.0

---

### 2.5 Terminology Standardization 📖 ✅

**Status**: ✅ Complete (2025-11-14)
**Effort**: 3 hours
**Priority**: HIGH (foundation for all documentation)

**Goal**: Lock down canonical terminology for every concept, resolve all ambiguities

**Problem Identified**: Mixed terminology across documentation:
- "local frame" vs "coordinate system" vs "local coordinates"
- "translate" documented as both "move" and "position at"
- "reference" vs "anchor" not fully standardized in all contexts
- Operation categories using both friendly and technical terms inconsistently

**Solution Created**: `docs/TERMINOLOGY_GUIDE.md` (official terminology reference)

**Decisions Made** (30+ terms standardized):

**Spatial Terms**:
- ✅ "Local frame" (not "coordinate system")
- ✅ "World space" (not "global coordinates")
- ✅ "Offset" (not "displacement" or "shift")

**Geometry Terms**:
- ✅ "Face" (not "surface" in CAD contexts)
- ✅ "Normal" for vectors, "orientation" for frames
- ✅ "Edge" (not "line" or "curve")

**Positioning Terms**:
- ✅ "Position" (noun, not "location")
- ✅ "translate" in YAML (document as "position at anchor")

**Anchor Terms**:
- ✅ "Anchor" in all user-facing docs (not "reference")
- ✅ "Auto-generated anchors" (not "auto-references" or "built-in")
- ✅ Both `anchors:` and `references:` valid in YAML (v3.x)

**Operation Terms**:
- ✅ "Positioning (Transforms)", "Shape Modification (Features)", etc.
- ✅ Context-specific recipients: `input:`, `base:`, `targets:`

**Structure Terms**:
- ✅ "Part" (v3.x), "Shape" (v4.0)
- ✅ "Assembly" for multi-part models
- ✅ "Model" for 3D output
- ✅ "Design" for YAML file/intent

**Documentation Voice**:
- ✅ "You" in tutorials
- ✅ "Users" or passive voice in reference docs

**Deliverables**:
- [x] `docs/TERMINOLOGY_GUIDE.md` created (315 lines)
- [x] Quick reference table
- [x] Rationale for each decision
- [x] v4.0 evolution notes
- [ ] Terminology audit script (pending)
- [ ] Fix inconsistencies in existing docs (pending)

**Impact**:
- Clear authority on which terms to use
- Reduces documentation ambiguity
- Faster doc writing (no need to decide each time)
- Easier PR reviews (terminology consistency)

**Next Steps**:
- Create audit script to find terminology inconsistencies
- Update key docs (README, GLOSSARY, YAML_REFERENCE) to fix major issues
- Add terminology checks to PR review process

---

## Phase 3: Long-Term (v4.0 Breaking Changes) ⚠️

**Goal**: Major syntax redesign with improved mental model alignment
**Effort**: 200+ hours estimated
**Status**: ⏸️ Not Started
**Target Milestone**: v4.0 (major version bump)
**Breaking Changes**: YES

**Important**: Phase 3 requires major version bump and migration strategy. Do not start until:
- v3.x is stable and widely adopted
- User base is large enough to justify migration effort
- Migration tooling is planned

---

### 3.1 Rename Core Concepts 🔄

**Status**: ⏸️ Not Started
**Effort**: 40 hours
**Breaking Change**: YES

**Proposed Renames**:

| Current | Proposed | Rationale |
|---------|----------|-----------|
| `parts:` | `shapes:` | Less manufacturing connotation |
| `references:` | `anchors:` | User-friendly spatial metaphor |
| (consider) `operations:` | (consider) categorized sections | Clearer intent |

**Changes Required**:
- [ ] Schema updates (major version)
- [ ] Parser/loader updates
- [ ] All internal code references
- [ ] All documentation updates
- [ ] All example files updates
- [ ] Migration script (v3 → v4 YAML)
- [ ] Compatibility layer (optional: accept both for transition period)

**Migration Strategy**:
- Auto-migration tool for simple cases
- Manual migration guide for complex cases
- Side-by-side examples (v3 vs v4 syntax)
- 6-month deprecation period (v3 warnings, v4 still accepts old syntax)
- Blog post explaining changes and rationale

---

### 3.2 Categorized Operations in YAML Structure 🗂️

**Status**: ⏸️ Not Started
**Effort**: 80 hours
**Breaking Change**: YES

**Current**:
```yaml
operations:
  - transform: [...]
  - fillet: [...]
  - union: [...]
  - pattern: [...]
```

**Proposed v4.0**:
```yaml
positioning:
  tower_positioned:
    translate: [...]
    rotate: [...]

features:
  rounded_edges:
    fillet: [...]
    chamfer: [...]

combinations:
  bracket_assembly:
    union: [...]
    difference: [...]

replications:
  bolt_circle:
    circular_pattern: [...]
```

**Rationale**: Makes operation intent explicit, easier to scan large files

**Challenges**:
- More verbose for simple files
- Must maintain operation order across sections
- Backward compatibility complex

**Changes Required**:
- [ ] Schema redesign
- [ ] Parser rewrite for new structure
- [ ] Update all internal processing
- [ ] Documentation complete rewrite
- [ ] All examples updated
- [ ] Migration tool for v3 → v4
- [ ] Consider: execution order specification

**Alternative**: Keep flat `operations:` but require `category:` field:
```yaml
operations:
  tower_positioned:
    category: positioning    # NEW: Required field
    transform: [...]
```

---

### 3.3 Explicit Model/Assembly Declaration 📦

**Status**: ⏸️ Not Started
**Effort**: 40 hours
**Breaking Change**: YES (if made required)

**Current**: Document purpose is implicit

**Proposed v4.0**:
```yaml
model:
  name: Guitar Hanger
  type: assembly
  composition: reference-based

shapes:  # Renamed from 'parts'
  [...]

anchors:  # Renamed from 'references'
  [...]
```

**Rationale**: Makes document purpose explicit from first lines

**Changes Required**:
- [ ] Schema update (required `model:` block)
- [ ] Parser updates
- [ ] Documentation updates
- [ ] Examples updates
- [ ] Migration script
- [ ] Validation for valid model types

**Alternative**: Make `model:` optional for v4.0, encourage but don't require

---

### 3.4 Consistent Spatial Language 🎯

**Status**: ⏸️ Not Started
**Effort**: 40 hours
**Breaking Change**: PARTIAL

**Goal**: Use consistent verbs for spatial operations

**Current**:
```yaml
parts:
  tower:
    translate: base.face_top
```

**Proposed v4.0 Options**:

**Option A (verbs)**:
```yaml
shapes:
  tower:
    place:
      at: base.face_top
```

**Option B (prepositions)**:
```yaml
shapes:
  tower:
    at: base.face_top
```

**Option C (semantic)**:
```yaml
shapes:
  tower:
    attach:
      to: base.face_top
      offset: [0, 0, 5]
```

**Needs Research**:
- [ ] Which feels most natural to users?
- [ ] Does English-centric language work internationally?
- [ ] Balance between terseness and clarity

**Changes Required**:
- [ ] User testing on proposed syntax
- [ ] Schema updates
- [ ] Parser updates
- [ ] Documentation rewrite
- [ ] Examples updates
- [ ] Migration guide

---

### 3.5 Frame-Based Positioning (Experimental) 🧪

**Status**: ⏸️ Not Started
**Effort**: Unknown (research needed)
**Breaking Change**: NO (additive)

**Goal**: Explore advanced positioning using explicit coordinate frames

**Current**: Implicit local frames from references

**Proposed**:
```yaml
frames:
  mounting_frame:
    origin: base.face_top
    x_axis: [1, 0, 0]
    y_axis: [0, 1, 0]
    z_axis: [0, 0, 1]

shapes:
  bracket:
    in_frame: mounting_frame
    position: [10, 20, 0]  # In frame coordinates
```

**Rationale**: Explicit frames for complex assemblies, robotics use cases

**Research Needed**:
- [ ] Is this actually needed? (use case validation)
- [ ] Does it simplify or complicate?
- [ ] Interaction with existing reference system
- [ ] Learning curve impact

---

## Success Metrics

### Phase 1 Success Criteria ✅

- [x] Mental model explicitly stated in README
- [x] Glossary exists and covers all core terms
- [x] "Anchor" terminology used consistently
- [x] Operations categorized in documentation
- [ ] User feedback: "I understand how TiaCAD is different from SolidWorks"
- [ ] User feedback: "Anchors make sense to me"
- [ ] Reduced confusion in support questions

### Phase 2 Success Criteria (TBD)

- [ ] Visual diagrams in 5+ documentation locations
- [ ] Users can use either `references:` or `anchors:` in YAML
- [ ] Example files demonstrate improved patterns
- [ ] Measured reduction in "how do I position parts?" questions

### Phase 3 Success Criteria (TBD)

- [ ] v4.0 released with breaking changes
- [ ] Migration path validated with real users
- [ ] 90%+ of examples migrated automatically
- [ ] Documentation completely rewritten for v4.0
- [ ] User satisfaction increased (measured via survey)

---

## User Feedback Collection

### Channels for Feedback

1. **GitHub Issues**: Tag with `documentation` or `language-improvement`
2. **User Surveys**: Periodic surveys on terminology clarity
3. **Support Channels**: Track common confusion points
4. **Onboarding Observations**: Watch new users learn TiaCAD

### Feedback Template

```markdown
## Documentation Feedback

**Which document**: [e.g., README.md, GLOSSARY.md, TUTORIAL.md]
**Section**: [e.g., "Mental Model", "Anchors explanation"]
**Issue**: [What was confusing or unclear?]
**Suggestion**: [How could it be clearer?]
**Priority**: [Low/Medium/High]
```

### Current Feedback (2025-11-13)

- No user feedback yet (Phase 1 just completed)
- **Action**: Solicit feedback from test users after 1-2 weeks

---

## Dependency Tracking

### What Depends on Phase 1 Improvements

- Phase 2 visual diagrams (reference the terminology from Phase 1)
- Future tutorial updates (use "anchor" language)
- Error message improvements (use glossary terms)

### What Depends on Phase 2 Improvements

- Phase 3 breaking changes (visual diagrams inform syntax design)
- User testing for v4.0 (test with Phase 2 improvements in place)

### Blocking Issues

- None currently for Phase 2
- Phase 3 blocked on: v3.x stability, user base size, migration strategy decision

---

## Version Milestones

| Version | Phase | Status | Target Date | Notes |
|---------|-------|--------|-------------|-------|
| v3.0 | Initial release | ✅ Complete | 2025-11-05 | Reference-based architecture |
| v3.1 | Testing improvements | ✅ Complete | 2025-11-10 | Test coverage, visual regression |
| v3.2 | Phase 1 + Phase 2 | 🟡 In Progress | 2025-Q4 | Language improvements, visual docs |
| v3.3 | Polish | ⏸️ Planning | 2026-Q1 | User feedback integration |
| v4.0 | Phase 3 (breaking) | ⏸️ Not Started | 2026-Q2+ | Major syntax redesign |

---

## Change Log

### 2025-11-13 - Phase 1 Complete

**Session**: regavela-1113
**Completed**:
- ✅ Mental model section added to README.md
- ✅ GLOSSARY.md created (650+ lines)
- ✅ "Anchors" language added to 3 documentation files
- ✅ Operations categorized in YAML_REFERENCE.md
- ✅ Gap analysis completed (TIACAD_LANGUAGE_GAP_ANALYSIS.md)
- ✅ Status tracking document created (this file)

**Impact**: Users can now understand TiaCAD's reference-based model from documentation rather than inferring from examples.

**Files Modified**:
- `README.md` (added mental model section)
- `GLOSSARY.md` (created)
- `AUTO_REFERENCES_GUIDE.md` (added anchor metaphor)
- `YAML_REFERENCE.md` (renamed sections, added anchors language)
- `TUTORIAL.md` (added "Positioning Parts with Anchors" section)
- `docs/LANGUAGE_IMPROVEMENTS_STATUS.md` (created, this file)

**Next Actions**:
- Collect user feedback over next 2-4 weeks
- Monitor support channels for terminology confusion
- Plan Phase 2 visual diagrams

---

### 2025-11-06 - PR #14 Merged

**PR**: #14 (Modeling and Visualization Composition Patterns)
**Completed**:
- ✅ MENTAL_MODELS_AND_LANGUAGE.md created (368 lines)
- ✅ Strategic recommendations documented
- ✅ Foundation for future language evolution

**Impact**: Provided framework for understanding language/UX issues

---

## References

### Internal Documents

- [MENTAL_MODELS_AND_LANGUAGE.md](MENTAL_MODELS_AND_LANGUAGE.md) - Original PR #14
- [GLOSSARY.md](../GLOSSARY.md) - User-facing glossary
- [AUTO_REFERENCES_GUIDE.md](../AUTO_REFERENCES_GUIDE.md) - Anchors documentation
- [YAML_REFERENCE.md](../YAML_REFERENCE.md) - Complete syntax reference
- [ARCHITECTURE_DECISION_V3.md](ARCHITECTURE_DECISION_V3.md) - v3.0 design rationale
- [TIACAD_EVOLUTION_ROADMAP.md](TIACAD_EVOLUTION_ROADMAP.md) - Overall project roadmap

### Session Archives

- [regavela-1113](../../tia/sessions/regavela-1113/) - Gap analysis and Phase 1 implementation
  - `TIACAD_LANGUAGE_GAP_ANALYSIS.md` - Detailed gap analysis (420 lines)
  - `README.md` - Session summary

### External References

- [PR #14 on GitHub](https://github.com/scottsen/tiacad/pull/14) - Original PR discussion

---

## Maintenance

**Document Owner**: TIA Project
**Update Frequency**: After each phase completion or significant milestone
**Review Cycle**: Quarterly

**Update Triggers**:
- Phase completion (Phase 1 ✅, Phase 2, Phase 3)
- User feedback collection milestones
- Version releases (v3.2, v3.3, v4.0)
- Significant user feedback requiring plan changes

**Next Review Date**: 2025-12-13 (30 days after Phase 1 completion)

---

**End of Status Document**
