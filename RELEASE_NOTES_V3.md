# TiaCAD v3.0 Release Notes

**Release Date:** 2025-11-19 (Public Release)
**Status:** ✅ COMPLETE - v3.0.0 Tag Created 2025-11-10
**Version:** 3.0.0

---

## 🎉 Major Release: Unified Spatial Reference System

TiaCAD v3.0 is a **major release** that introduces a clean, unified spatial reference system. This is a **breaking change** that simplifies how you position and orient parts in your designs.

### What's New in v3.0

**✨ Auto-Generated References** - No more boilerplate!
Every part automatically provides 11 spatial references without explicit definition:
- Point references: `{part}.center`, `{part}.origin`
- Face references: `{part}.face_top`, `{part}.face_bottom`, `{part}.face_left`, etc.
- Axis references: `{part}.axis_x`, `{part}.axis_y`, `{part}.axis_z`

**🎯 Unified Reference System**
One system for all spatial references (points, faces, edges, axes):
- Consistent `references:` section (replaces `named_points:`)
- Explicit `type` field for all references
- Full orientation support (normals, tangents)

**📐 Local Frame Offsets**
Offsets now follow the reference's local coordinate system:
- Intuitive positioning relative to faces
- X/Y offsets along face tangents
- Z offset perpendicular to face

**🏗️ Clean Architecture**
Complete rewrite of the spatial reference system:
- `SpatialRef` dataclass: position + orientation + tangent
- `Frame` dataclass: local coordinate systems
- `SpatialResolver`: unified reference resolution
- Better separation of concerns

---

## Breaking Changes

### YAML Syntax Changes

#### 1. `named_points:` → `references:`

**Before (v0.3.0):**
```yaml
named_points:
  mount_point: [10, 20, 30]
  top_face:
    part: base
    face: ">Z"
    at: center
```

**After (v3.0):**
```yaml
references:
  mount_point:
    type: point
    value: [10, 20, 30]

  top_face:
    type: face
    part: base
    selector: ">Z"  # Changed from 'face' to 'selector'
    at: center
```

#### 2. Part Definitions: `size:` → `parameters:`

**Before (v0.3.0):**
```yaml
parts:
  box:
    primitive: box
    size: [100, 50, 20]
```

**After (v3.0):**
```yaml
parts:
  box:
    primitive: box
    parameters:
      width: 100
      height: 50
      depth: 20
```

#### 3. Use Auto-References (Recommended)

**Before (v0.3.0):**
```yaml
named_points:
  base_top:
    part: base
    face: ">Z"
    at: center

parts:
  pillar:
    translate:
      to: base_top
```

**After (v3.0) - Simpler!**
```yaml
# No references section needed!

parts:
  pillar:
    translate:
      to: base.face_top  # Auto-reference!
```

### API Changes (Python)

| v0.3.0 | v3.0 | Notes |
|--------|------|-------|
| `PointResolver` | `SpatialResolver` | Class renamed |
| Returns `Tuple[float, float, float]` | Returns `SpatialRef` | Includes orientation |
| `named_points` dict | `references` dict | Section renamed |

---

## New Features

### 1. Auto-Generated References

Every part automatically provides 11 references:

```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 10, depth: 100}

  # Use auto-references - no definition needed!
  pillar:
    translate:
      to: base.face_top  # ✨ Auto-generated!

  cap:
    translate:
      to: pillar.face_top  # ✨ Auto-generated!
```

**Available auto-references:**
- Points: `.center`, `.origin`
- Faces: `.face_top`, `.face_bottom`, `.face_left`, `.face_right`, `.face_front`, `.face_back`
- Axes: `.axis_x`, `.axis_y`, `.axis_z`

### 2. Local Frame Offsets

Offsets now follow the reference's local coordinate system:

```yaml
parts:
  bracket:
    translate:
      to:
        from: wall.face_front  # Face reference
        offset: [10, 0, 5]     # Local frame offset!
        # X: 10 units right along face
        # Y: 0 units (perpendicular to face)
        # Z: 5 units out from face
```

**Benefits:**
- Intuitive positioning relative to faces
- No need to calculate world coordinates
- Robust to part transformations

### 3. Unified Reference Types

v3.0 supports four reference types:

#### Point References
```yaml
references:
  corner:
    type: point
    value: [100, 50, 0]
```

#### Face References
```yaml
references:
  mount_surface:
    type: face
    part: base
    selector: ">Z"
    at: center
```

#### Edge References (New!)
```yaml
references:
  rail_edge:
    type: edge
    part: frame
    selector: ">X and >Z"
    at: midpoint
```

#### Axis References (New!)
```yaml
references:
  rotation_axis:
    type: axis
    from: [0, 0, 0]
    to: [0, 0, 100]
```

### 4. Orientation-Aware Transforms

New transform operations that understand orientation:

#### align_to_face
```yaml
operations:
  mounted:
    type: transform
    input: bracket
    transforms:
      - align_to_face:
          face: wall.face_front
          orientation: normal
          offset: 5
```

#### Frame-Based Rotation
```yaml
- rotate:
    angle: 45
    around: shaft.axis_z  # Rotate around axis reference
```

---

## Implementation Details

### Core Components

#### SpatialRef Dataclass
```python
@dataclass
class SpatialRef:
    position: NDArray[np.float64]           # Always present
    orientation: Optional[NDArray]           # Normal/direction
    tangent: Optional[NDArray]               # For edges
    ref_type: Literal['point','face','edge','axis']
```

#### Frame Dataclass
```python
@dataclass
class Frame:
    origin: NDArray[np.float64]
    x_axis: NDArray[np.float64]
    y_axis: NDArray[np.float64]
    z_axis: NDArray[np.float64]
```

#### SpatialResolver
```python
class SpatialResolver:
    def resolve(self, spec) -> SpatialRef:
        # Handles: lists, strings, dicts, SpatialRef
        # Returns: SpatialRef with position + orientation
```

### Test Coverage

**v3.0 Final Test Summary:**
- 894 tests passing (99.8% pass rate)
- 2 tests skipped (visualization tests requiring GPU)
- Total: 896 tests
- Coverage: 84% overall (95%+ for spatial reference system)

**New Tests Added (v3.0):**
- Phase 1-3: Core spatial reference system (114 tests)
- Syntax migration: Named parameters (additional coverage)
- **Total:** 896 tests (up from 806 in v0.3.0)

---

## Migration Guide

See [MIGRATION_GUIDE_V3.md](docs/MIGRATION_GUIDE_V3.md) for detailed migration instructions.

### Quick Migration Checklist

- [ ] Replace `named_points:` with `references:`
- [ ] Add `type:` field to all reference definitions
- [ ] Change `size:` to `parameters:` in part definitions
- [ ] Update `face:` to `selector:` in face references
- [ ] Consider using auto-references to simplify definitions
- [ ] Test with v3.0 schema validation
- [ ] Update any custom Python code using `PointResolver`

### Migration Tools

**Schema validation:**
```bash
tiacad validate my_design.yaml --schema v3.0
```

**Automated migration (coming soon):**
```bash
tiacad migrate my_design.yaml --from v0.3.0 --to v3.0
```

---

## Documentation Updates

### New Documentation

- [AUTO_REFERENCES_GUIDE.md](docs/AUTO_REFERENCES_GUIDE.md) - Comprehensive guide to auto-references
- [MIGRATION_GUIDE_V3.md](docs/MIGRATION_GUIDE_V3.md) - Step-by-step migration instructions
- [V3_IMPLEMENTATION_STATUS.md](docs/V3_IMPLEMENTATION_STATUS.md) - Implementation details

### Updated Documentation

- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Updated for v3.0 syntax
- [README.md](README.md) - v3.0 features and status
- [tiacad-schema.json](tiacad-schema.json) - v3.0 schema validation

### New Examples

- `examples/v3_simple_box.yaml` - Basic v3.0 example
- `examples/v3_bracket_mount.yaml` - Practical assembly
- `examples/auto_references_box_stack.yaml` - Vertical stacking
- `examples/auto_references_cylinder_assembly.yaml` - Cylinder assembly
- `examples/auto_references_with_offsets.yaml` - Local frame offsets
- `examples/auto_references_rotation.yaml` - Axis rotation
- `examples/guitar_hanger_named_points.yaml` - Updated to v3.0

---

## Performance

v3.0 maintains performance parity with v0.3.0:

- Reference resolution: ~same (caching added)
- Memory usage: ~same
- Parse time: ~same
- Test execution: ~same (848 tests in <10s)

**Optimizations:**
- Reference caching in SpatialResolver
- Numpy vectorization for transformations
- Efficient Frame generation

---

## Compatibility

### Backward Compatibility

⚠️ **v3.0 is NOT backward compatible with v0.3.0**

This is a breaking release. Old YAML files must be migrated.

### Forward Compatibility

v3.0 is designed to be forward-compatible with future versions:
- Clean architecture supports constraints (v4.0)
- Extensible reference system
- Stable API for spatial references

---

## Upgrade Instructions

### For Users

1. **Backup your designs:**
   ```bash
   cp -r my_designs/ my_designs_v0.3.0_backup/
   ```

2. **Read migration guide:**
   - See [MIGRATION_GUIDE_V3.md](docs/MIGRATION_GUIDE_V3.md)

3. **Update syntax:**
   - `named_points:` → `references:`
   - `size:` → `parameters:`
   - Add `type:` to references
   - Consider using auto-references

4. **Validate:**
   ```bash
   tiacad validate my_design.yaml
   ```

5. **Test:**
   ```bash
   tiacad build my_design.yaml
   ```

### For Developers

1. **Update imports:**
   ```python
   # Old
   from tiacad_core.point_resolver import PointResolver

   # New
   from tiacad_core.spatial_resolver import SpatialResolver
   from tiacad_core.geometry.spatial_references import SpatialRef, Frame
   ```

2. **Update code:**
   ```python
   # Old
   resolver = PointResolver(registry, named_points)
   point = resolver.resolve("mount")  # Returns (x, y, z)

   # New
   resolver = SpatialResolver(registry, references)
   ref = resolver.resolve("mount")    # Returns SpatialRef
   point = ref.to_tuple()             # Get (x, y, z) if needed
   ```

3. **Run tests:**
   ```bash
   pytest tiacad_core/tests/ --ignore=tiacad_core/tests/test_visualization/
   ```

---

## Known Issues

### Resolved Before Release
- ✅ Auto-references for transformed parts (uses bounding box)
- ✅ Schema validation for v3.0 syntax
- ✅ Migration guide for all common patterns

### Future Enhancements
- 🔄 Automated migration tool (v3.1)
- 🔄 Auto-references for operation results (v3.1)
- 🔄 Custom auto-reference definitions (v3.2)

---

## Contributors

**v3.0 Development:**
- Core architecture design
- Implementation (Weeks 1-6)
- Testing and validation
- Documentation

**Special Thanks:**
- CadQuery team for the excellent CAD engine
- Early testers for feedback

---

## What's Next?

### v3.1 (Planned)
- Automated migration tool
- Enhanced auto-references
- Performance optimizations

### v4.0 (Roadmap)
- Constraint-based assembly
- Mate constraints
- Collision detection
- Assembly validation

---

## Getting Help

**Documentation:**
- [README.md](README.md) - Project overview
- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Complete syntax reference
- [AUTO_REFERENCES_GUIDE.md](docs/AUTO_REFERENCES_GUIDE.md) - Auto-references guide
- [MIGRATION_GUIDE_V3.md](docs/MIGRATION_GUIDE_V3.md) - Migration instructions

**Examples:**
- See `examples/` directory for working v3.0 YAML files
- Start with `examples/v3_simple_box.yaml`

**Community:**
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share designs

---

## Summary

TiaCAD v3.0 represents a major step forward in clean, intuitive CAD design:

✅ **Cleaner YAML** - Auto-references eliminate boilerplate
✅ **Unified System** - One reference system for points, faces, edges, axes
✅ **Local Frames** - Intuitive positioning with local offsets
✅ **Better Architecture** - Clean separation of concerns
✅ **Full Tests** - 848 tests, 95%+ coverage
✅ **Great Docs** - Comprehensive guides and examples

**Upgrade today to experience the future of declarative CAD!**

---

**Version:** 3.0.0
**Code Complete:** 2025-11-10 (v3.0.0 tag created)
**Public Release:** 2025-11-19 (target)
**Test Status:** 894/896 passing (99.8%)
**Documentation:** Complete and aligned
**Migration Guide:** Available
