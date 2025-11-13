# Changelog

All notable changes to TiaCAD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Documentation Improvements (2025-11-13)

#### Mental Model & Language Clarity
- Added "TiaCAD's Design Philosophy: Reference-Based Composition" section to README.md
  - Explains how TiaCAD differs from traditional CAD (hierarchical assemblies)
  - Explains how TiaCAD differs from procedural tools (OpenSCAD)
  - Comparison tables showing TiaCAD vs SolidWorks vs OpenSCAD
  - Links to new GLOSSARY.md for term definitions

#### New Documentation Files
- **GLOSSARY.md** (650+ lines) - Comprehensive terminology guide
  - Core concepts: Part, Anchor, Reference-Based Composition, Operations
  - TiaCAD vs Traditional CAD comparisons
  - TiaCAD vs Procedural Tools comparisons
  - Spatial concepts: Face, Normal, Local Frame, Offset
  - Operation type categories explained
  - Technical terms decoded (SpatialRef, SpatialResolver, etc.)
  - Common confusion points addressed
  - Quick reference term translation table
  - Learning path guidance

- **docs/LANGUAGE_IMPROVEMENTS_STATUS.md** - Tracks language/documentation improvements
  - Phase 1 (Complete): Quick wins (mental model, glossary, anchors language)
  - Phase 2 (Planned): Visual diagrams, YAML aliases, enhanced metadata
  - Phase 3 (Planned): v4.0 breaking changes (rename core concepts)
  - Success metrics and user feedback collection plan
  - Version milestone tracking

#### Enhanced Existing Documentation
- **AUTO_REFERENCES_GUIDE.md**: Added "anchors" metaphor
  - Introduction explains anchors as "marked spots on a workbench"
  - Added "Why anchors?" explanation with ship's anchor metaphor
  - Listed 4 key benefits of anchor-based positioning

- **YAML_REFERENCE.md**: Added "anchors" language throughout
  - Changed section header to "References (Spatial Anchors) - v3.0"
  - Added "What are references?" introduction with anchor metaphor
  - Renamed "Named References" → "Named References (Custom Anchors)"
  - **Categorized Operations**: Reorganized into 4 clear types
    1. Positioning Operations (Transforms) - Move/rotate/scale
    2. Shape Modification Operations (Features) - Fillet/chamfer/extrude
    3. Combining Operations (Booleans) - Union/difference/intersection
    4. Replication Operations (Patterns) - Linear/circular/grid
  - Each category includes purpose statement and "Think of it as..." metaphor

- **TUTORIAL.md**: Added new section "Positioning Parts with Anchors"
  - Located after "Creating Holes" section
  - Explains anchor concept with workbench metaphor
  - Example: stacking boxes with `translate: to: base.face_top`
  - Table of common auto-generated anchors
  - Using anchors with offsets example
  - Benefits list (no coordinate math, self-updating, readable, error-proof)

- **README.md**: Reorganized documentation section
  - Separated User Documentation vs Technical Documentation
  - Added links to all major documentation files
  - Added GLOSSARY.md and LANGUAGE_IMPROVEMENTS_STATUS.md to index

#### Impact
- Users can now understand TiaCAD's reference-based mental model from documentation
- "Anchor" is now the primary user-facing term for spatial references
- Operations are categorized by purpose, making intent clearer
- Comprehensive glossary available for term lookup
- Documentation improvements tracked for future phases

**Related**: PR #14 (MENTAL_MODELS_AND_LANGUAGE.md), Session regavela-1113

---

## [3.0.0] - 2025-11-05

### Added - Major Architecture Redesign
- Unified spatial reference system (`SpatialRef`) replacing old `named_points`
- Auto-generated references for all parts (`.face_top`, `.center`, `.axis_z`, etc.)
- Local frame offsets for intuitive positioning
- Full orientation support (position + normal + tangent)

### Changed - Breaking Changes
- Replaced `named_points:` section with `references:` section
- Removed `PointResolver`, replaced with unified `SpatialResolver`
- YAML syntax breaking changes (see MIGRATION_GUIDE_V3.md)

### Migration
- See [MIGRATION_GUIDE_V3.md](MIGRATION_GUIDE_V3.md) for complete migration guide
- See [RELEASE_NOTES_V3.md](RELEASE_NOTES_V3.md) for detailed changes

---

## [0.3.0] - Previous Version

### Added - Phase 2 Complete
- Boolean operations (union, difference, intersection)
- Pattern operations (linear, circular, grid)
- Finishing operations (fillet, chamfer)
- Named points system (later replaced in v3.0)

### Added - Phase 1 Foundation
- Core primitives (box, cylinder, sphere, cone)
- Parameters with expressions
- Transform operations
- Schema validation

---

## Version History Overview

| Version | Release Date | Status | Key Features |
|---------|--------------|--------|--------------|
| **3.0.0** | 2025-11-05 | Current | Unified spatial references, auto-generated anchors |
| 0.3.0 | 2025-10-XX | Previous | Boolean ops, patterns, finishing, named points |
| 0.2.0 | 2025-09-XX | Legacy | Transforms, primitives, parameters |
| 0.1.0 | 2025-08-XX | Initial | Basic primitives and transforms |

---

## Upcoming

### v3.2 - Planned
- Visual documentation diagrams
- YAML alias support (`anchors:` for `references:`)
- Enhanced metadata section
- User feedback integration from v3.1

### v4.0 - Future (Breaking Changes)
- Rename core concepts (`parts:` → `shapes:`, `references:` → `anchors:`)
- Categorized operations in YAML structure
- Explicit model/assembly declaration
- Consistent spatial language
- See [docs/LANGUAGE_IMPROVEMENTS_STATUS.md](docs/LANGUAGE_IMPROVEMENTS_STATUS.md) for details

---

## Links

- [GitHub Repository](https://github.com/scottsen/tiacad)
- [Documentation](README.md#documentation)
- [Language Improvements Status](docs/LANGUAGE_IMPROVEMENTS_STATUS.md)
- [Evolution Roadmap](docs/TIACAD_EVOLUTION_ROADMAP.md)
