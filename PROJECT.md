---
name: TiaCAD
type: project
status: active
phase: v3-complete
priority: high
started: 2024-10-18
last_active: 2025-11-10
lead_sessions:
  - fafecoha-1103
  - magical-altar-1103
  - pulsing-gravity-1102
  - padibugo-1102
  - sunny-rainbow-1102
  - kinetic-abyss-1031
progress: 100
beth_topics:
  - tiacad
  - parametric-cad
  - yaml-cad
  - cadquery
  - declarative-design
  - spatial-references
tags:
  - cad
  - 3d-modeling
  - parametric
  - yaml
  - cadquery
  - python
  - production-ready
description: Declarative parametric CAD system using YAML - Build 3D models with readable, explicit, composable syntax. v3.0 complete with unified spatial reference system.
tech_stack:
  - Python 3.10+
  - CadQuery 2.6.0
  - pytest
  - YAML
  - networkx (planned for v3.1 DAG)
---

# TiaCAD Project

## Vision

Enable anyone to create parametric 3D models using simple YAML syntax instead of code. Make CAD accessible, verifiable, and composable.

## Current Status

**Version:** v3.0 (Production Ready)
**Phase:** v3.0 Complete ✅
**Release Date:** 2025-11-19 (planned)

**Test Suite:**
- 896 tests collected
- 896 passing (100%)
- 0 skipped
- 0 failing

**Components Complete:**
- ✅ Named parameter syntax (width/height/depth for all primitives)
- ✅ Spatial reference system (SpatialRef, Frame, SpatialResolver)
- ✅ GeometryBackend abstraction (20 methods)
- ✅ Complete YAML parser
- ✅ All primitives (box, cylinder, sphere, cone)
- ✅ Boolean operations (union, difference, intersection)
- ✅ Pattern operations (linear, polar)
- ✅ Finishing operations (fillet, chamfer)
- ✅ Sketch-based operations (extrude, revolve, sweep, loft)
- ✅ Advanced operations (gusset, hull, text)
- ✅ 3MF export with color and metadata
- ✅ Rule-based assembly validator (8 validation rules)
- ✅ Auto-generated references (box.face_top, cylinder.axis_z, etc.)

**Next Milestone:** v3.1 - Dependency Graph (DAG) System

## Project Evolution

### v3.0: Unified Spatial References (COMPLETE ✅)
**Duration:** Nov 2-10, 2025
**Status:** Production ready

**Major Features:**
- Unified spatial reference system (position + orientation)
- Auto-generated part-local references
- Frame-based transformations
- Backward compatible with v2.x syntax

**Deliverables:**
- 896 tests (up from 806)
- 84% test coverage
- Complete documentation
- Migration guide
- Working examples

### v3.1: Dependency Graph (PLANNED 📋)
**Duration:** 6-8 weeks
**Status:** Not started

**Goal:** True parametric modeling with incremental rebuilds

**Features:**
- ModelGraph using networkx
- Dependency tracking (params → parts → operations)
- Invalidation propagation
- `--watch` mode for auto-rebuild
- `--show-deps` for graph visualization

**Deliverable:** v3.1.0 release

### v3.2: Explicit Constraints (PLANNED 📋)
**Duration:** 4-6 weeks
**Dependencies:** v3.1 complete

**Goal:** Declarative constraints (manual solving)

**Features:**
- Constraint YAML schema (flush, coaxial, offset)
- Constraint validation
- Integration with ModelGraph
- Assembly examples

**Deliverable:** v3.2.0 release

### Future: Advanced Features
- Constraint solver (symbolic + numeric)
- Shell/offset operations
- Additional export formats (STEP, IGES, DXF)
- CAM integration (g-code generation)
- Web-based editor

## Key Innovations

1. **Explicit Origins** - No ambiguous transformation behavior
2. **Unified Spatial References** - Position + orientation in one system
3. **Auto-Generated References** - `box.face_top`, `cylinder.axis_z` automatic
4. **Sequential Transforms** - Clear, predictable composition rules
5. **Rule-Based Validation** - Extensible validation architecture
6. **Test-Driven Development** - 896 tests, 99.7% passing

## Documentation

**Primary Documentation:**
- `README.md` - Project overview and quick start
- `YAML_REFERENCE.md` - Complete YAML syntax guide
- `RELEASE_NOTES_V3.md` - v3.0 release notes
- `AUTO_REFERENCES_GUIDE.md` - auto-generated anchor system guide
- `TUTORIAL.md` - User tutorial
- `EXAMPLES_GUIDE.md` - Example gallery

**Design Documentation:**
- `docs/ARCHITECTURE_DECISION_V3.md` - ADR for v3.0
- `docs/CLEAN_ARCHITECTURE_PROPOSAL.md` - Architecture design
- `docs/TIACAD_EVOLUTION_ROADMAP.md` - Strategic roadmap
- `docs/V3_IMPLEMENTATION_STATUS.md` - Implementation tracking
- `docs/MIGRATION_GUIDE_V3.md` - v3.0 migration guide

**Archived Documentation:**
- `~/Archive/tiacad/2025-11-10-v3-cleanup/` - Historical docs

## Related Projects

- **CadQuery** - Underlying CAD engine
- **OpenSCAD** - Declarative approach inspiration
- **FreeCAD** - Visual CAD tool
- **build123d** - Modern Python CAD library

## Success Metrics

### v3.0 Milestones (All Complete ✅)
- [x] All core components implemented
- [x] Spatial reference system working
- [x] CadQuery integration validated
- [x] YAML → STL pipeline working
- [x] 896 tests passing
- [x] Documentation complete
- [x] Migration guide published
- [x] Release notes ready

### v3.1 Goals (Planned)
- [ ] ModelGraph implementation
- [ ] Dependency tracking working
- [ ] Incremental rebuild 10x faster
- [ ] `--watch` mode functional
- [ ] 50+ DAG-specific tests

## Repository Structure

```
/home/scottsen/src/projects/tiacad/
├── tiacad_core/           # Core implementation (896 tests)
│   ├── geometry/          # Backend abstraction
│   ├── parser/            # YAML parsing
│   ├── validation/        # Rule-based validator
│   ├── exporters/         # 3MF exporter
│   └── tests/             # Test suite
├── examples/              # Working examples
├── docs/                  # Design documentation
├── README.md              # Primary docs
├── YAML_REFERENCE.md      # Syntax reference
└── RELEASE_NOTES_V3.md    # Release notes
```

## Contact & Sessions

**Active Development Sessions:**
- astral-gravity-1110 - v3.0 finalization: fix tests, commit, tag release
- quantum-blackhole-1110 - Documentation cleanup & syntax migration
- fafecoha-1103 - Assembly validator refactoring
- magical-altar-1103 - Week 5 orientation transforms
- pulsing-gravity-1102 - v3.0 week 2 completion

**Session Archive:** `/home/scottsen/src/tia/sessions/`

---

**Project Status:** ✅ v3.0 Production Ready (v3.0.0 tag created)
**Current Focus:** v3.0 Release (2025-11-19) & v3.1 Planning
**Last Updated:** 2025-11-10
**Test Suite:** 896 tests (896 passing, 100%)
