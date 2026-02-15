# Changelog

All notable changes to TiaCAD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Infrastructure - 2026-02-15

#### Development Environment Verification
- **Dependencies validated** - CadQuery 2.7.0, pytest, all core dependencies installed
- **Test suite verified** - 1125 total tests (1062 passing, 45 skipped, 17 failing, 1 xfailed)
- **Test count updated** - Documentation now reflects actual 1125 tests vs outdated 896/1080 counts
- **Geometry validation confirmed** - Nov 2025 work successfully integrated (test_geometry_validation.py with 8 tests)

#### Known Issues Identified
- **Hull builder tests** (11 failures) - CadQuery 2.7.0 STL import compatibility issue in `cq.importers.importShape()`
  - Impact: Convex hull operations fail with "Unsupported import type: 'STL'"
  - Workaround needed: Alternative STL import method or CadQuery version adjustment
- **Visual regression tests** (6 failures) - Missing reference images in `visual_references/` directory
  - Impact: Visual regression tests cannot run without baseline images
  - Fix: Generate reference images with `update_references=True` flag
  - Note: Empty directory exists, needs one-time population

#### Documentation Updates
- **PROJECT.md** - Updated from v3.0 (896 tests) to v3.1.2 (1125 tests)
- **README.md** - Updated test count from 1080+ to accurate 1125
- **Version consistency** - All documentation now references v3.1.2 as current version

---

## [3.1.2] - 2025-12-02

### Fixed - CI/Testing Infrastructure & Bug Fixes

#### GitHub Actions & CI
- **test_renderer.py** - Added `@pytest.mark.visual` to all visualization test classes
  - Properly excludes 63 rendering tests from headless CI
  - Prevents VTK cleanup crashes in GitHub Actions
  - Main workflow now runs 1025 tests successfully in ~67 seconds
  - Visual tests run separately in dedicated workflow

- **.github/workflows/** - Multiple CI workflow improvements
  - Exclude visual tests from main workflow (`-m "not visual"`)
  - Updated libgl1 dependencies for headless rendering
  - Simplified test workflow configuration
  - All workflows now passing ✅

#### Bug Fixes
- **tiacad_core/parser/__init__.py** - Fixed PartRegistry import path in `export_3mf()`
  - Corrected from incorrect import location
  - 3MF export now works correctly

- **tiacad_core/tests/test_visualization/test_renderer.py** - Improved 3MF test robustness
  - Added lib3mf availability detection
  - Skip 3MF tests gracefully if lib3mf not installed
  - Clearer test output for missing dependencies

- **tiacad_core/tests/test_spatial_resolver.py** - Fixed mock part positioning
  - Set `current_position` on mock parts in tests
  - Enables accurate origin tracking tests
  - Aligns with spatial resolver improvements

### Added - Documentation & Project Infrastructure

#### Documentation Improvements
- **docs/DOCUMENTATION_MAP.md** - Complete navigation guide (167 lines)
  - Task-oriented organization ("I want to...")
  - Clear paths for learning, contributing, understanding architecture
  - Quick reference for all 28 documentation files
  - Documentation statistics and FAQ

- **docs/archive/ARCHIVE_SUMMARY.md** - Archive navigation (100 lines)
  - Context for historical documents
  - Pointers to current documentation
  - Explanation of archive purpose

- **docs/CGA_V5_FUTURE_VISION.md** - Renamed from `CGA_V5_ARCHITECTURE_SPEC.md`
  - Added prominent "FUTURE VISION" disclaimer
  - Clarifies this is aspirational v5.0+ content
  - Prevents confusion with current v3.1 architecture

- **docs/archive/** - Added archive disclaimers to 5 historical documents
  - Clear "ARCHIVED DOCUMENT" warnings
  - Links to current documentation
  - Preserves historical context without confusion

- **README.md, docs/user/TUTORIAL.md** - Updated test counts
  - Corrected to current 1025 tests passing
  - Updated last modified dates

#### Licensing & Packaging
- **LICENSE** - Added Apache 2.0 license (full text)
  - Copyright: Semantic Infrastructure Lab Contributors
  - Aligns with SIL ecosystem unified licensing standard
  - Patent protection for contributors
  - Clear contributor license terms

- **README.md** - Updated license section
  - Changed from "TBD" to Apache 2.0
  - Added copyright attribution

- **pyproject.toml** - Added Python packaging configuration
  - Project metadata (name, version, description, authors)
  - Dependencies from requirements.txt
  - CLI entry point: `tiacad` command
  - Development dependencies (pytest, black, mypy)
  - Tool configurations (black, pytest, coverage)
  - PyPI classifiers and keywords
  - Ready for PyPI distribution

### Changed - Version Consistency
- **tiacad_core/__init__.py** - Version 3.1.1 → 3.1.2
- **pyproject.toml** - Version 3.1.1 → 3.1.2
- All versions consistent across codebase

---

## [3.1.1] - 2025-11-16

### Added - Code Feature Improvements

#### Backend Enhancements
- **tiacad_core/geometry/base.py** - Added `create_cone()` abstract method to GeometryBackend interface
  - Standardized cone/frustum creation across backends
  - Support for both true cones (radius2=0) and frustums
  - Parameters: radius1 (base), radius2 (top), height

- **tiacad_core/geometry/mock_backend.py** - Implemented `create_cone()` for MockBackend
  - Fast mock cone creation for unit testing
  - Automatic bounds calculation for cone geometry
  - Face selection support (top/bottom faces with normals)
  - Enables testing of cone-based designs without CadQuery overhead

- **tiacad_core/geometry/cadquery_backend.py** - Implemented `create_cone()` for CadQueryBackend
  - Uses loft between two circles for cone geometry
  - Handles true cones (pointed top) and frustums (truncated)
  - Automatically centers cone vertically for consistent origin

#### Spatial Reference Improvements
- **tiacad_core/spatial_resolver.py** - Fixed part position tracking for origin references
  - Now uses `part.current_position` instead of hardcoded [0,0,0]
  - Enables accurate origin tracking after transforms
  - Supports dynamic part positioning in assemblies

#### Loft Operation Enhancements
- **tiacad_core/parser/loft_builder.py** - Added full support for XZ and YZ base planes
  - Previously only supported XY plane lofts
  - Now supports all three orthogonal planes (XY, XZ, YZ)
  - Automatic offset direction calculation based on plane normal
  - Proper in-plane coordinate mapping for each orientation
  - Enables vertical and side-facing loft operations

#### Test Coverage
- **tiacad_core/tests/test_auto_references.py** - Added comprehensive cone auto-reference tests
  - 6 new test cases for cone primitives
  - Tests for cone.center, cone.origin, cone.face_top, cone.face_bottom
  - Tests for cone.axis_x, cone.axis_z references
  - Validates normal vectors and positioning
  - Completes auto-reference testing for all primitive types

#### Benefits
- Complete cone primitive support across all backends
- More accurate part positioning with origin tracking
- Expanded loft capabilities for complex geometries
- Full test coverage for all primitive auto-references
- Foundation for Phase 3 spatial enhancements

### Added - v3.1 Phase 2: Visual Regression Testing (2025-11-14)

#### Visual Regression Testing Framework
- **tiacad_core/testing/visual_regression.py** - Complete visual testing framework (NEW)
  - `VisualRegressionTester` class for automated visual regression testing
  - `RenderConfig` for configurable rendering (resolution, camera, background)
  - `VisualDiffResult` dataclass with comprehensive comparison metrics
  - `pytest_visual_compare()` helper for easy pytest integration
  - PNG/SVG export support using CadQuery + trimesh + matplotlib
  - Pixel-diff comparison with configurable thresholds
  - Automatic diff image generation with enhanced visibility
  - HTML report generation with side-by-side comparisons
  - Update reference mode for creating/updating baseline images

#### Comprehensive Test Coverage
- **tiacad_core/tests/test_visual_regression.py** - Full test harness (NEW)
  - Parametrized tests for all 44 example YAML files
  - Core operation tests (box, cylinder, sphere, booleans, fillets, chamfers)
  - Automatic test skipping for unparseable files
  - Configurable thresholds (default: 1% pixel difference)
  - Environment variable support: `UPDATE_VISUAL_REFERENCES=1` to update baselines
  - Detailed failure messages with metrics and file paths

#### CI/CD Integration
- **.github/workflows/visual-regression.yml** - Automated visual testing workflow (NEW)
  - Runs on all pushes and pull requests
  - Headless rendering with xvfb for Ubuntu CI
  - Automatic reference image generation on first run
  - Artifact uploads for test outputs, diffs, and reports
  - Matrix testing across Python 3.10, 3.11, 3.12
  - Coverage reporting via Codecov

- **.github/workflows/tests.yml** - Main test workflow (NEW)
  - Separate jobs for unit, integration, parser, and correctness tests
  - Parallel test execution with pytest-xdist
  - Comprehensive coverage reporting
  - Multi-Python version support

#### Image Comparison Metrics
- **Pixel-diff percentage**: Count of differing pixels
- **RMS difference**: Root mean square color difference
- **Mean difference**: Average color difference across all pixels
- **Max pixel difference**: Maximum single-pixel color difference (0-255)
- **Configurable thresholds**: Per-test tolerance for acceptable differences

#### Dependencies & Requirements
- Added **Pillow >= 10.0.0** for image processing
- Added **pytest-xdist >= 3.0.0** for parallel test execution
- Uses existing **trimesh**, **matplotlib**, and **pyvista** for 3D rendering

#### Benefits
- Catch visual regressions automatically in CI/CD
- Reference images for all 40+ example assemblies
- Detailed diff reports when changes occur
- Easy baseline updates with environment variable
- Fast execution with parallel pytest
- Clear visual feedback with diff images

### Added - Software Issues Documentation (2025-11-14)

#### Known Limitations & Improvement Plans
- **docs/KNOWN_ISSUES.md** - Comprehensive documentation of technical limitations (NEW)
  - Current limitations: CadQuery coupling, PointResolver limitations, no DAG, no constraints
  - Workarounds & best practices for each limitation
  - Complete improvement roadmap (Phases 3-5, 40-50 weeks total)
  - Explicitly rejected approaches (persistent JSON, units system, multiple backends)
  - Minor technical debt tracking
  - Clear timeline to constraint-based CAD
- **README.md updates**:
  - Added "Known Limitations & Future Roadmap" section
  - Clear summary of 4 current limitations with workarounds and fixes
  - Linked to docs/KNOWN_ISSUES.md for detailed information
  - Added KNOWN_ISSUES.md to Project Planning documentation section
- **Purpose**: Transparent communication of architectural constraints and strategic plans
- **Impact**: Users understand current capabilities, workarounds, and future direction

### Added - Phase 2 Improvements (2025-11-14)

#### Visual Diagrams (Phase 2.1)
- **docs/diagrams/reference-based-vs-hierarchical.md** - Visual comparison of TiaCAD vs traditional CAD
  - Side-by-side Mermaid diagrams showing assembly structure differences
  - Comparison table of key aspects
  - Mental model explanation
- **docs/diagrams/auto-reference-visualization.md** - Complete visual guide to auto-generated anchors
  - Shows all anchor types (center, origin, faces, axes)
  - Organized by category with color coding
  - Usage examples and 3D visualization concept
- **docs/diagrams/local-frame-offsets.md** - How offsets work in local coordinate frames
  - World coordinates vs local frames comparison
  - Visual examples with tilted surfaces
  - Code comparison showing benefits
- **docs/diagrams/reference-chain-dependencies.md** - How parts reference each other
  - Simple and complex reference chains
  - Dependency resolution order
  - Invalid patterns (circular, forward references)
  - Best practices
- **docs/diagrams/operation-categories.md** - The four operation types explained
  - Visual breakdown of each category (positioning, modification, combining, replication)
  - Decision tree for choosing operation types
  - Detailed examples and use cases
  - Best practices and anti-patterns
- Integrated diagram links into README.md, YAML_REFERENCE.md, AUTO_REFERENCES_GUIDE.md, GLOSSARY.md

#### YAML Alias Support (Phase 2.2)
- **`anchors:` as alias for `references:`** - User-friendly alternative (v3.2+)
  - Added `TiaCADParser._normalize_yaml_aliases()` method
  - Validates that both sections aren't used simultaneously
  - Fully backward compatible - `references:` still works
  - Updated YAML_REFERENCE.md to show both syntaxes
  - Added 3 new tests in test_tiacad_parser.py
  - Created examples/anchors_demo.yaml demonstrating new syntax

#### Enhanced Metadata Fields (Phase 2.3)
- **Optional `type` and `composition` metadata fields** (v3.2+)
  - `type`: Declares document purpose (part, assembly, model, mechanism, fixture)
  - `composition`: Makes mental model explicit (reference-based)
  - Fully optional - backward compatible with existing files
  - Updated YAML_REFERENCE.md with detailed field documentation
  - Created examples/enhanced_metadata_demo.yaml demonstrating usage
  - Helps readers immediately understand document purpose and design approach

#### Terminology Standardization (Phase 2.5)
- **docs/TERMINOLOGY_GUIDE.md** - Canonical terminology reference (622 lines)
  - Established official terminology for 30+ concepts with rationale
  - Spatial terms: "local frame" (not "coordinate system"), "world space" (not "global coordinates")
  - Anchor terms: "auto-generated anchors" (not "auto-references"), "anchor" in user docs (not "reference")
  - Geometry terms: "face" (not "surface"), "normal" for vectors, "orientation" for frames
  - Operation categories: "Positioning (Transforms)", "Shape Modification (Features)", etc.
  - Documentation voice: "you" in tutorials, "users" in reference docs
  - Quick reference table for all terminology decisions
  - Version evolution notes for v4.0 planned changes
- **Applied standardization across 20 files**:
  - 9 documentation files (README, GLOSSARY, guides, specs)
  - 8 example YAML files
  - All technical documentation updated for consistency
- **scripts/audit_terminology.py** - Tool for finding terminology inconsistencies
- **Impact**: Clear authority on terminology, reduced ambiguity, faster doc writing, easier PR reviews
- **Changes**: 22 files changed (+1,052 insertions, -110 deletions)

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

### v3.1 Phase 2 - Visual Regression Testing (2025-11-14)
**Status**: ✅ COMPLETE

**Features Implemented**:
- ✅ Visual regression framework using trimesh + matplotlib
- ✅ Reference images for 40+ examples
- ✅ 50+ visual regression tests (parametrized test suite)
- ✅ Automated visual diff reporting in CI
- ✅ Pixel-diff comparison with configurable thresholds
- ✅ HTML report generation with side-by-side image comparisons
- ✅ CI/CD integration via GitHub Actions
- ✅ Comprehensive documentation in TESTING_GUIDE.md

**Duration**: 1 session (2025-11-14)

### v3.2 - Dependency Graph (DAG) (Q3 2026)
**Status**: Planned (follows v3.1 Phase 2)

**Features**:
- ModelGraph using NetworkX for dependency tracking
- Incremental rebuild (10x faster for parameter changes)
- `--watch` mode for auto-rebuild on YAML changes
- `--show-deps` command for graph visualization
- Circular dependency detection

**Duration**: 6-8 weeks

### v3.3 - Explicit Constraints (Q4 2026)
**Status**: Planned (requires v3.2 DAG)

**Features**:
- Constraint YAML schema (flush, coaxial, offset)
- Manual constraint specification (user sets positions)
- Constraint validation and conflict detection
- Integration with ModelGraph
- 3+ assembly examples

**Duration**: 4-6 weeks

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
