---
name: TiaCAD
type: project
status: active
phase: phase-1-implementation
priority: high
started: 2024-10-18
last_active: 2025-10-25
lead_sessions:
  - laser-destroyer-1025
  - bright-launch-1024
  - boundless-energy-1024
  - cagapigo-1024
  - revealed-spear-1024
  - peaceful-flood-1024
progress: 75
beth_topics:
  - tiacad
  - parametric-cad
  - yaml-cad
  - cadquery
  - declarative-design
  - transform-tracking
tags:
  - cad
  - 3d-modeling
  - parametric
  - yaml
  - cadquery
  - python
description: Declarative parametric CAD system using YAML - Build 3D models with readable, explicit, composable syntax
tech_stack:
  - Python 3.10+
  - CadQuery 2.6.0
  - pytest
  - YAML
---

# TiaCAD Project

## Vision

Enable anyone to create parametric 3D models using simple YAML syntax instead of code. Make CAD accessible, verifiable, and composable.

## Current Status

**Phase:** 1 - Core Implementation (75% complete)

**Components Complete:**
- ✅ Part representation (42 tests)
- ✅ SelectorResolver (22 tests)
- ✅ TransformTracker (21 tests)
- ✅ PointResolver (36 tests)
- ✅ CadQuery integration validated (6/6 tests)

**Next Steps:**
- YAML parser implementation
- End-to-end integration
- Guitar hanger demo (YAML → STL)

## Project Goals

### Phase 1: Prove Feasibility (75% done)
Build core components and demonstrate YAML → STL pipeline works.

**Deliverable:** Guitar hanger YAML → STL demo

### Phase 2: Production Ready
Add constraint system, patterns, full schema v2.0.

**Deliverable:** Complete TiaCAD v2.0

### Phase 3: Tooling
Web editor, real-time preview, error visualization.

**Deliverable:** Production-ready tool suite

## Key Innovations

1. **Explicit Rotation Origins** - No ambiguous behavior
2. **Dot Notation** - `"beam.face('>Y').center"` for geometric references
3. **Sequential Transforms** - Clear composition rules
4. **Comprehensive Testing** - 121 tests, real CadQuery validation

## Documentation

Main docs in `/home/scottsen/src/tia/docs/projects/tiacad/`:
- Design specifications
- Implementation guides
- API reference
- Session summaries

## Related Projects

- **CadQuery**: Underlying CAD engine
- **OpenSCAD**: Similar declarative approach (inspiration)
- **FreeCAD**: Visual CAD tool (complementary)

## Success Metrics

- [x] All 3 critical gaps solvable
- [x] Core components tested
- [x] CadQuery integration validated
- [ ] YAML → STL working
- [ ] Guitar hanger demo complete
- [ ] Documentation complete

## Contact

**Primary**: Session artifacts and documentation
**Discussions**: Session summaries in `/home/scottsen/src/tia/sessions/`

---

**Project Location:** `/home/scottsen/src/tia/projects/tiacad/`
**Documentation:** `/home/scottsen/src/tia/docs/projects/tiacad/`
**Test Coverage:** 121 tests, ~98% passing
