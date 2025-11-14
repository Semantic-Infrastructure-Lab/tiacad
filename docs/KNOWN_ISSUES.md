# Known Issues & Technical Limitations

**Version:** 1.0
**Last Updated:** 2025-11-14
**Status:** Active tracking of software limitations and improvement plans

---

## Purpose

This document tracks known limitations in TiaCAD's underlying software architecture, current workarounds, and planned improvements. It serves as a central reference for:

- **Users**: Understanding current constraints and what to expect
- **Contributors**: Knowing where technical debt exists
- **Planning**: Prioritizing future development work

**Related Documents:**
- [TIACAD_EVOLUTION_ROADMAP.md](TIACAD_EVOLUTION_ROADMAP.md) - Strategic evolution plan
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Real-time project health snapshot
- [TESTING_CONFIDENCE_PLAN.md](TESTING_CONFIDENCE_PLAN.md) - Testing strategy and gaps

---

## Table of Contents

1. [Current Limitations](#current-limitations)
2. [Workarounds & Best Practices](#workarounds--best-practices)
3. [Improvement Roadmap](#improvement-roadmap)
4. [Explicitly Rejected Approaches](#explicitly-rejected-approaches)
5. [Minor Technical Debt](#minor-technical-debt)

---

## Current Limitations

### 1. CadQuery Coupling (Medium Priority)

**Issue**: While a `GeometryBackend` abstraction exists, approximately 90% of code still directly calls CadQuery APIs.

**Impact**:
- Cannot easily swap CAD kernels (e.g., to FreeCAD, OpenCascade directly)
- Testing is slower than it could be with MockBackend
- Code is tightly coupled to one geometry implementation

**Current Workaround**: Continue using CadQuery directly

**Code Location**:
- Interface: `tiacad_core/geometry/base.py:139-160`
- Violations: Most builder classes in `tiacad_core/parser/`

**Status**: ⚠️ **NOT PLANNED FOR IMMEDIATE FIX**

**Decision**:
- Don't add multiple backends (FreeCAD, Trimesh) - creates 3x testing burden
- **DO** enforce existing backend abstraction in new code
- Gradually refactor existing builders during feature work
- Keep CadQuery as the only real backend for now

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:450-479

---

### 2. PointResolver Limitations - Position Only (High Priority)

**Issue**: The current `PointResolver` only returns position `(x, y, z)` with no orientation data (normals, directions, local axes).

**Impact**:
- ❌ Cannot support `align_to_face` operations
- ❌ Cannot implement `mate_axes` for assembly constraints
- ❌ Limits intelligent part placement
- ❌ No frame-based transforms

**Current Workaround**: Manual rotation calculations in YAML

**Code Location**: `tiacad_core/point_resolver.py:399-448`

**Example of Current Limitation**:
```yaml
# ❌ NOT POSSIBLE TODAY - No orientation support
operations:
  align_bracket:
    type: transform
    input: bracket
    transforms:
      - align_to_face:
          face: mount_face
          orientation: normal
          offset: 5
```

**Planned Fix**: Phase 3 upgrade to `SpatialResolver`

**What's Needed**:
```python
# Current (Point-only)
def resolve(spec) -> Tuple[float, float, float]:
    return (x, y, z)

# Phase 3 (Spatial with orientation)
def resolve(spec) -> SpatialReference:
    return SpatialReference(
        position=(x, y, z),
        normal=(nx, ny, nz),      # For faces
        direction=(dx, dy, dz),   # For edges/axes
        frame=Frame(...)          # Local coordinate frame
    )
```

**Timeline**: Phase 3 (12-16 weeks) - See [Improvement Roadmap](#improvement-roadmap)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:429-448

---

### 3. No Dependency Graph (High Priority)

**Issue**: Sequential execution only - must rebuild entire model on any parameter change.

**Impact**:
- ❌ No true parametric modeling
- ❌ Cannot re-run partial builds after parameter changes
- ❌ Slow iteration on complex models
- ❌ Cannot detect circular dependencies at parse time

**Current Workaround**: Full rebuild every time (acceptable for small models)

**Example of Limitation**:
```yaml
parameters:
  width: 100   # Change this value
  # ... 500 lines of complex model ...

# Currently: Must rebuild ENTIRE model
# Desired: Only rebuild parts that depend on 'width'
```

**Code Location**: Not implemented (docs/TIACAD_EVOLUTION_ROADMAP.md:176)

**Planned Fix**: Phase 4a - Dependency Graph (DAG)

**What's Needed**:
- `ModelGraph` using NetworkX
- Dependency tracking (params → sketches → parts → operations)
- Invalidation propagation
- Incremental rebuild logic

**Timeline**: Phase 4a (6-8 weeks) - See [Improvement Roadmap](#improvement-roadmap)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:762-798

---

### 4. No Constraint System (High Priority)

**Issue**: No sketch constraint solver or assembly constraints.

**Impact**:
- ❌ Cannot specify design intent declaratively
- ❌ No automatic constraint satisfaction
- ❌ Manual positioning required for assemblies
- ❌ No "mate", "flush", "coaxial" operations

**Current Workaround**: Explicit transforms and manual positioning

**Example of Limitation**:
```yaml
# ❌ NOT POSSIBLE TODAY - No constraints
constraints:
  mount_alignment:
    type: flush
    parts: [bracket, base]
    faces: [bracket.bottom, base.mount_surface]

# ✅ CURRENT WORKAROUND - Manual positioning
parts:
  bracket:
    type: box
    size: [50, 50, 10]
    position: [0, 0, 15]  # Manually calculated
```

**Code Location**: Not implemented (docs/TIACAD_EVOLUTION_ROADMAP.md:172)

**Planned Fix**: Two-phase approach
1. **Phase 4b**: Explicit constraints (manual specification, validation only)
2. **Phase 5**: Constraint solver (automatic satisfaction)

**What's Needed (Phase 4b)**:
- Constraint YAML schema
- Manual constraint specification
- Constraint validation and conflict detection
- Basic types: flush, offset, coaxial

**What's Needed (Phase 5)**:
- Symbolic solver (SymPy) for simple cases
- Numeric solver (scipy.optimize) for assemblies
- Solver integration with DAG
- Error handling for unsolvable systems

**Timeline**:
- Phase 4b: 4-6 weeks (requires Phase 4a DAG first)
- Phase 5: 12-16 weeks (post-1.0 feature, significant R&D)

**Reference**:
- Phase 4b: docs/TIACAD_EVOLUTION_ROADMAP.md:807-830
- Phase 5: docs/TIACAD_EVOLUTION_ROADMAP.md:831-850

---

## Workarounds & Best Practices

### For Missing Orientation Support

**Problem**: Cannot align parts to face normals

**Workaround**: Calculate rotations manually

```yaml
# Manual rotation to align with tilted surface
parts:
  bracket:
    type: box
    size: [50, 50, 10]
    transforms:
      - translate: [0, 0, 0]
      - rotate:
          axis: [1, 0, 0]
          angle: 45  # Manually calculated
          origin: current
```

**When to Use**: Assembly alignment, mounting brackets, tilted surfaces

**Future**: Phase 3 will provide `align_to_face` operation

---

### For Missing Dependency Graph

**Problem**: Slow iteration on large models

**Workaround**: Split model into smaller files

```yaml
# main_assembly.yaml
parameters:
  shared_width: 100

# Import/include would help here (future feature)
# For now: manually copy parameters to separate files
```

**Best Practice**:
- Keep models under 200 lines for fast iteration
- Use parameters to centralize values
- Comment parameter dependencies for clarity

**Future**: Phase 4a DAG will enable incremental rebuilds

---

### For Missing Constraints

**Problem**: Complex assemblies require manual positioning

**Workaround**: Use reference-based positioning with named anchors

```yaml
references:
  mount_point:
    from: base.face_top
    offset: [25, 25, 0]

parts:
  bracket:
    type: box
    size: [50, 50, 10]
    translate:
      to: mount_point
```

**Best Practice**:
- Define logical anchor points in `references:` section
- Use descriptive names (`mounting_hole_1` not `point1`)
- Comment the intent of each reference

**Future**: Phases 4b/5 will add declarative constraints

---

## Improvement Roadmap

### Phase 3: Named Geometry & Orientation (12-16 weeks)

**Goal**: Extend spatial references to include faces/edges/axes with orientation data

**Status**: 🎯 **NEXT MAJOR MILESTONE** (after v3.1 finalization)

**Deliverables**:
1. `SpatialReference` dataclass (position + orientation + frame)
2. `SpatialResolver` (replaces `PointResolver`)
3. Named faces, edges, axes in YAML
4. Frame-based transforms
5. `align_to_face` operation
6. Updated examples and documentation

**What You'll Be Able to Do**:
```yaml
geometry_references:
  faces:
    mount_face:
      part: base
      selector: ">Z"
      # Stores: position + normal

operations:
  align_bracket:
    type: transform
    input: bracket
    transforms:
      - align_to_face:
          face: mount_face
          orientation: normal
          offset: 5
```

**Impact**: Intent-based modeling ("align to face" vs raw coordinates)

**Success Criteria**:
- ✅ 140+ new tests (total: 946+ tests)
- ✅ Backward compatibility maintained
- ✅ 5+ production-ready examples
- ✅ No performance regression

**Timeline**: Weeks 1-16 (3-4 months)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:686-755

---

### Phase 4a: Dependency Graph (DAG) (6-8 weeks)

**Goal**: Track dependencies so parameter changes trigger selective rebuilds

**Status**: 📋 **PLANNED** (follows Phase 3)

**Deliverables**:
1. `ModelGraph` using NetworkX
2. Dependency tracking (params → sketches → parts → operations)
3. Invalidation propagation
4. Incremental rebuild logic
5. `--watch` mode (auto-rebuild on YAML change)
6. `--show-deps` command (visualize graph)

**What You'll Be Able to Do**:
- Change a parameter → only affected parts rebuild (10x faster)
- Detect circular dependencies at parse time
- Visualize dependency relationships

**Impact**: True parametric modeling

**Success Criteria**:
- ✅ 50+ DAG-specific tests
- ✅ Incremental rebuild 10x faster than full rebuild
- ✅ Watch mode works with live reload

**Timeline**: Weeks 1-8 (6-8 weeks after Phase 3)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:762-798

---

### Phase 4b: Explicit Constraints (4-6 weeks)

**Goal**: Declarative constraints without automatic solving

**Status**: 📋 **PLANNED** (follows Phase 4a, requires DAG)

**Deliverables**:
1. Constraint YAML schema
2. Manual constraint specification (user sets positions)
3. Constraint validation (detect conflicts)
4. Basic types: flush, offset, coaxial
5. Integration with ModelGraph

**What You'll Be Able to Do**:
```yaml
constraints:
  mount_flush:
    type: flush
    parts: [bracket, base]
    faces: [bracket.bottom, base.mount_surface]

  shaft_coaxial:
    type: coaxial
    parts: [shaft, bearing]
    axes: [shaft.axis_z, bearing.hole_axis]
```

**Impact**: Better design intent capture (validation only, not automatic solving)

**Success Criteria**:
- ✅ 30+ constraint tests
- ✅ Clear error messages for invalid constraints
- ✅ 3+ assembly examples

**Timeline**: Weeks 1-6 (4-6 weeks after Phase 4a)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:807-830

---

### Phase 5: Constraint Solver (12-16 weeks)

**Goal**: Automatic constraint satisfaction

**Status**: 📋 **POST-1.0 FEATURE** (requires significant R&D)

**Deliverables**:
1. Symbolic solver (SymPy) for simple cases
2. Numeric solver (scipy.optimize) for complex assemblies
3. Solver integration with DAG for recomputation
4. Error reporting for unsolvable systems
5. Constraint priority system

**What You'll Be Able to Do**:
- Specify constraints, let solver find positions
- Over-constrained system detection
- Underconstrained warnings
- Full constraint-based CAD (like SolidWorks/Fusion360)

**Impact**: Professional-grade constraint-based modeling

**Estimated Effort**: 3-4 months full-time

**Timeline**: Post-1.0 (Phase 5, weeks 1-16)

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:831-850

---

### Total Timeline to Constraint-Based CAD

**Sequential Phases**:
- Phase 3: 12-16 weeks (Named Geometry)
- Phase 4a: 6-8 weeks (DAG)
- Phase 4b: 4-6 weeks (Explicit Constraints)
- Phase 5: 12-16 weeks (Solver)

**Total**: ~40-50 weeks (10-12 months)

**Current Progress**: v3.1 Phase 1 Complete ✅

---

## Explicitly Rejected Approaches

These approaches were considered but **intentionally rejected** based on strategic analysis. Do not pursue without strong justification.

### ❌ 1. Persistent `.tiacad.json` Format

**Proposal**: Create a persistent JSON format separate from YAML

**Why Rejected**:
- YAML already serves as the source format
- JSON would be redundant
- Users should edit YAML, not JSON
- Adds complexity without clear benefit

**Decision**: YAML is the canonical format

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:488-491

---

### ❌ 2. Units System via `pint`

**Proposal**: Add explicit units to all dimensions

**Why Rejected**:
- Adds complexity to every dimension expression
- No clear user demand
- Most CAD tools assume single unit (mm)
- Would require significant syntax changes

**Decision**: Defer to post-1.0 (if at all)

**Example of Rejected Syntax**:
```yaml
# ❌ NOT PLANNED
parameters:
  width: 100 mm
  thickness: 0.125 in  # Unit conversion overhead
```

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:494-499

---

### ❌ 3. Multiple Geometry Backends

**Proposal**: Support FreeCAD, Trimesh, Open3D as alternative backends

**Why Rejected**:
- 3x testing burden (test each backend separately)
- CadQuery works fine for current needs
- No user complaints about CadQuery
- Maintenance overhead too high

**Decision**: Defer until 1000+ users request it

**Note**: GeometryBackend abstraction exists for future use, but don't add new backends now

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:501-505

---

### ❌ 4. Immediate Constraint Solver (Before DAG)

**Proposal**: Add constraint solver in Phase 3

**Why Rejected**:
- Requires DAG foundation first
- Complex symbolic math requires research
- 8-12 week effort minimum
- Would delay more valuable features

**Decision**: Phase 5 (post-DAG), not Phase 3

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:507-511

---

### ❌ 5. Schema Version Bump to 2.1

**Proposal**: Bump YAML schema version for new features

**Why Rejected**:
- Already using v2.0
- New features can extend v2.0 without breaking changes
- Backward compatibility more valuable
- No breaking changes needed yet

**Decision**: Stay on v2.0, extend it

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:513-515

---

## Minor Technical Debt

### 1. Documentation Debt (Low Priority)

**Issues** (from docs/CURRENT_STATUS.md:173-175):
- ⚠️ README.md test count needs updating (currently shows 1027+, accurate as of v3.1)
- ✅ All other documentation is current

**Impact**: Minimal - cosmetic only

**Fix**: Update README.md during routine maintenance

---

### 2. Test Infrastructure Debt (Low Priority)

**Issues** (from docs/CURRENT_STATUS.md:177-180):
- ⚠️ Pytest integration requires numpy to collect tests
- ⚠️ CI/CD pipeline needs updates for new test categories
- ✅ Test markers defined but need CI integration

**Impact**: Minor - tests work, just not optimally organized in CI

**Fix**:
- Add numpy to test dependencies
- Update GitHub Actions workflow for pytest markers
- Configure coverage reporting for test categories

**Timeline**: v3.1 finalization (weeks)

---

### 3. GeometryBackend Adoption (Medium Priority)

**Issue**: Backend exists but bypassed by most code

**Components Not Using Backend**:
- `PartsBuilder` - Direct CadQuery calls
- `BooleanBuilder` - Direct CadQuery calls
- `PatternBuilder` - Direct CadQuery calls
- `FinishingBuilder` - Direct CadQuery calls
- `ExtrudeBuilder` - Direct CadQuery calls
- `TransformTracker` - Direct CadQuery calls

**Recommendation**:
- 🔧 Don't add new backends yet
- 🔧 **DO** enforce existing backend in all new code
- 🔧 Gradually refactor during Phase 3 work
- 🔧 Keep CadQuery as only real backend

**Reference**: docs/TIACAD_EVOLUTION_ROADMAP.md:458-479

---

## How to Use This Document

### For Users

**Before Reporting Issues**: Check if limitation is documented here

**Questions to Ask**:
1. Is this a known limitation? (See [Current Limitations](#current-limitations))
2. Is there a workaround? (See [Workarounds](#workarounds--best-practices))
3. When will it be fixed? (See [Improvement Roadmap](#improvement-roadmap))

### For Contributors

**Before Starting Work**: Check if approach is rejected

**Questions to Ask**:
1. Is this in the improvement roadmap?
2. Is this approach explicitly rejected?
3. What's the priority?

### For Maintainers

**When to Update**:
- New limitation discovered → Add to [Current Limitations](#current-limitations)
- Workaround found → Add to [Workarounds](#workarounds--best-practices)
- Roadmap changes → Update [Improvement Roadmap](#improvement-roadmap)
- Feature completed → Remove from limitations, add to CHANGELOG

---

## Related Documentation

**Project Health**:
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Real-time status snapshot
- [CHANGELOG.md](../CHANGELOG.md) - Version history

**Planning**:
- [TIACAD_EVOLUTION_ROADMAP.md](TIACAD_EVOLUTION_ROADMAP.md) - Strategic roadmap (40+ pages)
- [TESTING_CONFIDENCE_PLAN.md](TESTING_CONFIDENCE_PLAN.md) - Testing strategy
- [V3_IMPLEMENTATION_STATUS.md](V3_IMPLEMENTATION_STATUS.md) - v3.0 feature tracking

**User Documentation**:
- [README.md](../README.md) - Project overview
- [GLOSSARY.md](../GLOSSARY.md) - Terminology guide

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-14 | Claude | Initial documentation of known issues and roadmap |

---

**Last Updated:** 2025-11-14
**Next Review:** After Phase 3 completion
**Status:** ✅ Complete and current
