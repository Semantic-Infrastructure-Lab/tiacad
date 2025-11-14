# Architecture Decision Record: TiaCAD v3.0 Clean Architecture

**Date:** 2025-11-02
**Status:** ✅ **APPROVED - Implementation Starting**
**Decision:** Adopt clean unified spatial reference architecture, breaking backward compatibility

---

## Context

TiaCAD Phase 2 (v0.3.0) implemented a `named_points` system that resolves point specifications to 3D coordinates `(x, y, z)`. This was a good first step but has fundamental limitations:

1. **Position-only** - No orientation data (normals, tangents, frames)
2. **Type fragmentation** - Would require separate systems for faces, edges, axes
3. **Resolver explosion** - PointResolver, future FaceResolver, EdgeResolver...
4. **No local frames** - Offsets always in world coordinates
5. **Backward compat burden** - Maintaining dual systems (`named_points` + `geometry_references`)

The original Phase 3 roadmap planned to maintain backward compatibility, requiring:
- Both `named_points:` and `geometry_references:` sections
- Both `PointResolver` and `SpatialResolver` classes
- Migration shims and dual code paths
- 12-16 weeks implementation timeline

---

## Decision

**We are implementing TiaCAD v3.0 with a clean, unified spatial reference architecture.**

This means:
- ✅ **Breaking changes** - Old YAML syntax will not work
- ✅ **Single reference system** - Just `references:`, one `SpatialRef` type
- ✅ **Unified resolver** - One `SpatialResolver` for all reference types
- ✅ **Auto-generated references** - Part-local references (e.g., `box.face_top`)
- ✅ **Local frame offsets** - Offsets in reference's local frame
- ✅ **Faster timeline** - 6 weeks vs 12-16 weeks

---

## Consequences

### Positive

1. **Simpler codebase** - One system, one pattern, cleaner architecture
2. **Better UX** - More intuitive YAML, auto-generated references, local frames
3. **Faster development** - No dual maintenance, no migration shims
4. **Future-proof** - Clean foundation for constraints, assemblies, DAG
5. **Easier testing** - Single code path, fewer edge cases
6. **Better documentation** - One way to do things, not multiple

### Negative

1. **Breaking changes** - Existing YAML files need manual migration
2. **Version bump** - v0.3.0 → v3.0.0 (semantic versioning major bump)
3. **Migration burden** - Users need to update their models

### Mitigation

Since TiaCAD is currently:
- Early stage (v0.3.0)
- Internal/personal use
- Small user base (possibly just us)
- Not yet 1.0 (no API stability guarantee)

**The breaking change cost is minimal, and the architectural benefit is massive.**

We will provide:
- Clear migration guide in documentation
- Example conversions (before/after)
- Script to help auto-migrate simple cases (if needed)

---

## Technical Changes

### 1. Core Types

**New:**
```python
@dataclass
class SpatialRef:
    position: np.ndarray           # (3,) always present
    orientation: Optional[np.ndarray]  # (3,) optional normal/direction
    tangent: Optional[np.ndarray]      # (3,) optional tangent (for edges)
    ref_type: Literal['point', 'face', 'edge', 'axis']

@dataclass
class Frame:
    origin: np.ndarray    # (3,)
    x_axis: np.ndarray    # (3,) normalized
    y_axis: np.ndarray    # (3,) normalized
    z_axis: np.ndarray    # (3,) normalized
```

**Removed:**
- Old `PointResolver` returns `Tuple[float, float, float]`

### 2. YAML Syntax

**Old (v0.3.0):**
```yaml
named_points:
  target: [10, 20, 30]
  top_center:
    part: base
    face: ">Z"
    at: center
```

**New (v3.0):**
```yaml
references:
  target:
    type: point
    value: [10, 20, 30]

  top_center:
    type: face
    part: base
    selector: ">Z"
    at: center
```

### 3. Auto-Generated References

**Every primitive automatically provides:**
- `{part}.center` - bounding box center
- `{part}.origin` - part origin
- `{part}.face_top`, `{part}.face_bottom`, etc. - canonical faces
- `{part}.axis_x`, `{part}.axis_y`, `{part}.axis_z` - principal axes

**Example:**
```yaml
parts:
  base:
    primitive: box
    size: [100, 60, 10]

operations:
  mount_bracket:
    transforms:
      - translate: {to: base.face_top}  # Auto-generated, no declaration needed!
```

### 4. Local Frame Offsets

**Killer feature:**
```yaml
references:
  mount_face:
    type: face
    part: base
    selector: ">Z"

  bolt_hole_1:
    type: point
    from: mount_face
    offset: [20, 20, 0]  # In mount_face's LOCAL frame!
                         # X = face's X, Y = face's Y, Z = face normal
```

If the face is tilted, the offset automatically follows the tilt!

---

## Implementation Plan

### Phase 1: Core (2 weeks)
**Week 1:**
- [ ] Create `tiacad_core/geometry/spatial_references.py`
  - `SpatialRef` dataclass
  - `Frame` dataclass
  - Frame math helpers (from_normal, to_transform_matrix)
- [ ] Write 30+ tests for SpatialRef and Frame

**Week 2:**
- [ ] Create `tiacad_core/spatial_resolver.py`
- [ ] Implement resolution methods (point, face, edge, axis)
- [ ] Write 40+ tests for SpatialResolver

### Phase 2: Integration (2 weeks)
**Week 3:**
- [ ] Extend `GeometryBackend` with spatial query methods
- [ ] Implement in `CadQueryBackend`
- [ ] Update `MockBackend` for tests
- [ ] Write 25+ tests

**Week 4:**
- [ ] Update `TiacadParser` to parse `references:` section
- [ ] Update `OperationsBuilder` to use `SpatialResolver`
- [ ] Remove old `PointResolver`
- [ ] Write 30+ integration tests

### Phase 3: auto-generated anchors (1 week)
**Week 5:**
- [ ] Implement part-local reference generation
- [ ] Document canonical references per primitive type
- [ ] Update schema validation
- [ ] Write 30+ tests

### Phase 4: Polish (1 week)
**Week 6:**
- [ ] Update `tiacad-schema.json`
- [ ] Update `YAML_REFERENCE.md`
- [ ] Create 5+ example files
- [ ] Write migration guide
- [ ] Update README.md to v3.0

**Target Test Count:** ~155 new tests (total: 806 + 155 = 961 tests)
**Target Coverage:** Maintain >95%

---

## Migration Guide Preview

### Simple Point References

**Before (v0.3.0):**
```yaml
named_points:
  center: [0, 0, 0]
  top: [0, 0, 50]
```

**After (v3.0):**
```yaml
references:
  center:
    type: point
    value: [0, 0, 0]
  top:
    type: point
    value: [0, 0, 50]
```

### Geometric References

**Before (v0.3.0):**
```yaml
named_points:
  top_face_center:
    part: base
    face: ">Z"
    at: center
```

**After (v3.0):**
```yaml
references:
  top_face_center:
    type: face
    part: base
    selector: ">Z"
    at: center
```

### Using Auto-Generated References (NEW!)

**Before (v0.3.0):**
```yaml
# Had to declare explicitly
named_points:
  base_top:
    part: base
    face: ">Z"
    at: center

operations:
  move_part:
    transforms:
      - translate: base_top
```

**After (v3.0):**
```yaml
# No declaration needed!
operations:
  move_part:
    transforms:
      - translate: {to: base.face_top}  # Auto-generated!
```

---

## Timeline

**Start Date:** 2025-11-02
**Target Completion:** 2025-12-13 (6 weeks)
**Release Version:** v3.0.0

### Milestones

- **2025-11-15** (Week 2): Core classes complete, 70+ tests passing
- **2025-11-29** (Week 4): Integration complete, old PointResolver removed
- **2025-12-06** (Week 5): auto-generated anchors working
- **2025-12-13** (Week 6): Documentation complete, v3.0.0 released

---

## Success Criteria

- ✅ All 961+ tests passing (806 existing + 155 new)
- ✅ Test coverage >95%
- ✅ All examples converted to v3.0 syntax
- ✅ Migration guide complete
- ✅ YAML_REFERENCE.md updated
- ✅ JSON schema updated
- ✅ No performance regression
- ✅ Clean architecture (single SpatialResolver, single SpatialRef type)

---

## References

- **Clean Architecture Proposal:** `docs/CLEAN_ARCHITECTURE_PROPOSAL.md`
- **Original Roadmap (backward compat):** `docs/TIACAD_EVOLUTION_ROADMAP.md`
- **Strategic Proposals:** `docs/notes1-4.md`
- **Current Implementation:** `tiacad_core/point_resolver.py` (to be replaced)

---

## Approval

**Decision Made By:** Project owner
**Date:** 2025-11-02
**Rationale:** Clean architecture outweighs backward compatibility burden for early-stage project

**Next Action:** Begin Phase 1 implementation immediately.

---

**Status:** ✅ **APPROVED - Implementation in progress**
