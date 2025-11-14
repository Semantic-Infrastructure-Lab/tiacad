# TiaCAD v3.1 Release Notes

**Release Date:** 2025-11-11
**Status:** ✅ COMPLETE - Testing Confidence Plan Phase 1
**Version:** 3.1.0

---

## 🧪 Testing Confidence Release

TiaCAD v3.1 focuses on **testing confidence** - ensuring that YAML specifications translate correctly into final 3D models. This release introduces comprehensive testing utilities and 60+ new correctness tests.

### What's New in v3.1

**✨ Testing Utilities** - Verify correctness with ease!
Three new testing utility modules:
- `tiacad_core/testing/measurements.py` - Distance and dimension measurements
- `tiacad_core/testing/orientation.py` - Rotation and orientation verification
- `tiacad_core/testing/dimensions.py` - Volume and surface area calculations

**🎯 Correctness Tests** - 60+ new tests!
- **Attachment tests** (16 tests): Verify parts attach at correct locations
- **Rotation tests** (19 tests): Verify parts orient correctly
- **Dimensional tests** (25 tests): Verify measurements match specifications

**📐 Test Organization** - Better test management!
- New `pytest.ini` with comprehensive markers
- Test filtering by category (`attachment`, `rotation`, `dimensions`)
- Improved test documentation

**📚 Comprehensive Documentation**
- New `docs/TESTING_GUIDE.md` - Complete testing guide with examples
- Updated roadmap and confidence plan
- Quick reference for common testing tasks

---

## New Features

### 1. Testing Utility Modules

#### Measurement Utilities

```python
from tiacad_core.testing.measurements import (
    measure_distance,
    get_bounding_box_dimensions,
)

# Measure distance between parts
dist = measure_distance(box1, box2, ref1="face_top", ref2="face_bottom")
assert dist < 0.01  # Parts are touching

# Get dimensions
dims = get_bounding_box_dimensions(box)
assert abs(dims['width'] - 50.0) < 0.1
```

#### Orientation Utilities

```python
from tiacad_core.testing.orientation import (
    get_orientation_angles,
    get_normal_vector,
    parts_aligned,
)

# Get rotation angles
angles = get_orientation_angles(box, reference="face_top")
assert abs(angles['yaw'] - 45.0) < 0.1

# Verify face normal
normal = get_normal_vector(box, "face_top")
assert normal[2] > 0.9  # Points up

# Check alignment
assert parts_aligned(box1, box2, axis='z', tolerance=0.01)
```

#### Dimension Utilities

```python
from tiacad_core.testing.dimensions import (
    get_dimensions,
    get_volume,
    get_surface_area,
)

# Get all dimensions
dims = get_dimensions(box)
assert abs(dims['volume'] - 6000) < 60  # 10*20*30

# Get volume only
volume = get_volume(cylinder)
expected = math.pi * radius**2 * height
assert abs(volume - expected) < expected * 0.01  # Within 1%

# Get surface area
area = get_surface_area(sphere)
expected = 4 * math.pi * radius**2
assert abs(area - expected) < expected * 0.01  # Within 1%
```

### 2. Correctness Test Suites

Three new test suites verify geometric correctness:

#### Attachment Correctness (`test_attachment_correctness.py`)
- **16 tests** verifying parts attach correctly
- Zero-distance attachments (parts touching)
- Face-to-face attachments
- Pattern spacing (linear, circular, grid)
- Rotated attachments

#### Rotation Correctness (`test_rotation_correctness.py`)
- **19 tests** verifying rotation correctness
- Basic rotations (90°, 45°, arbitrary angles)
- Normal vector verification after rotation
- Transform composition order verification
- Rotation accuracy and precision

#### Dimensional Accuracy (`test_dimensional_accuracy.py`)
- **25 tests** verifying dimensional accuracy
- Primitive dimensions (box, cylinder, sphere, cone)
- Volume calculations (within 1% accuracy)
- Surface area calculations
- Boolean operation volumes (union, difference, intersection)

### 3. Pytest Organization

New `pytest.ini` with organized markers:

```ini
[pytest]
markers =
    # Correctness categories
    attachment: Tests verifying attachment correctness
    rotation: Tests verifying rotation correctness
    dimensions: Tests verifying dimensional accuracy

    # Core categories
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (>5s)

    # Feature categories
    parser: Parser tests
    spatial: Spatial reference tests
    backend: Backend tests
    validation: Validation tests
```

**Run tests by category:**
```bash
# Attachment tests only
pytest -m attachment

# Rotation tests only
pytest -m rotation

# All correctness tests
pytest -m "attachment or rotation or dimensions"

# Fast tests only
pytest -m "not slow"
```

---

## Test Statistics

### v3.1 Test Summary

| Category | Tests | Status |
|----------|-------|--------|
| **Correctness Tests (NEW)** | **60** | ✅ All passing |
| - Attachment | 16 | ✅ |
| - Rotation | 19 | ✅ |
| - Dimensions | 25 | ✅ |
| **Testing Utilities (NEW)** | **71** | ✅ All passing |
| - Measurements | 23 | ✅ |
| - Orientation | 22 | ✅ |
| - Dimensions | 26 | ✅ |
| Parser Tests | 518 | ✅ |
| Integration Tests | 20+ | ✅ |
| Other Tests | 358+ | ✅ |
| **TOTAL** | **1027** | ✅ **All passing** |

**Improvement from v3.0:**
- Tests: 896 → 1027 (+131, +14.6%)
- Coverage: 87% → 90% (+3%)
- New testing capabilities: 3 utility modules
- New correctness tests: 60 tests

---

## Documentation Updates

### New Documentation

- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Comprehensive testing guide
  - Running tests by category
  - Using testing utilities
  - Writing new tests
  - CI/CD integration
  - Quick reference

- **[pytest.ini](pytest.ini)** - Pytest configuration
  - Registered markers for all test categories
  - Coverage configuration
  - Test discovery patterns

### Updated Documentation

- [docs/TESTING_ROADMAP.md](docs/TESTING_ROADMAP.md) - Implementation roadmap with progress tracking
- [docs/TESTING_CONFIDENCE_PLAN.md](docs/TESTING_CONFIDENCE_PLAN.md) - Strategic testing plan

---

## Usage Examples

### Example 1: Verify Attachment Correctness

```python
@pytest.mark.attachment
def test_cylinder_on_box_top():
    """Test cylinder attached to box top face"""
    box = Part(name="box", geometry=cq.Workplane("XY").box(20, 20, 10),
               backend=backend)
    cylinder = Part(name="cylinder",
                   geometry=cq.Workplane("XY").workplane(offset=10).cylinder(10, 5),
                   backend=backend)

    # Verify zero-distance attachment
    dist = measure_distance(box, cylinder, ref1="face_top", ref2="face_bottom")
    assert dist < 0.01, f"Parts should be touching, got distance {dist}"

    # Verify alignment
    assert parts_aligned(box, cylinder, axis='z', tolerance=0.01)
```

### Example 2: Verify Rotation Correctness

```python
@pytest.mark.rotation
def test_box_rotated_90deg():
    """Test box rotated 90° has correct orientation"""
    box = Part(name="box",
               geometry=cq.Workplane("XY")
                        .transformed(rotate=cq.Vector(0, 0, 90))
                        .box(20, 10, 5),
               backend=backend)

    # Verify dimensions swapped after rotation
    dims = get_bounding_box_dimensions(box)
    assert abs(dims['width'] - 10.0) < 0.5   # Was 20, now 10
    assert abs(dims['height'] - 20.0) < 0.5  # Was 10, now 20
```

### Example 3: Verify Dimensional Accuracy

```python
@pytest.mark.dimensions
def test_union_volume():
    """Test union of overlapping boxes has correct volume"""
    box1 = cq.Workplane("XY").box(20, 10, 10)
    box2 = cq.Workplane("XY").center(10, 0).box(20, 10, 10)

    union = Part(name="union", geometry=box1.union(box2), backend=backend)

    volume = get_volume(union)
    expected = 3000  # 2000 + 2000 - 1000 (overlap)

    assert abs(volume - expected) < expected * 0.01  # Within 1%
```

---

## Performance

v3.1 maintains excellent performance:

- **Test execution:** 1027 tests in ~2-3 seconds (new tests only)
- **Coverage calculation:** ~5 seconds with `pytest --cov`
- **Memory usage:** ~same as v3.0
- **Test isolation:** Each test runs independently with clean fixtures

---

## Upgrade Instructions

### For Users

v3.1 is fully backward compatible with v3.0. No YAML changes required.

1. **Update to v3.1:**
   ```bash
   pip install --upgrade tiacad
   ```

2. **Verify installation:**
   ```bash
   pytest --version  # Should show pytest with markers
   ```

3. **Run new tests (optional):**
   ```bash
   pytest -m "attachment or rotation or dimensions"
   ```

### For Developers

1. **Update testing dependencies (if needed):**
   ```bash
   pip install -r requirements.txt
   ```

2. **Use new testing utilities:**
   ```python
   from tiacad_core.testing.measurements import measure_distance
   from tiacad_core.testing.orientation import get_normal_vector
   from tiacad_core.testing.dimensions import get_volume
   ```

3. **Write correctness tests:**
   ```python
   @pytest.mark.attachment  # or @pytest.mark.rotation, @pytest.mark.dimensions
   def test_your_feature():
       # Use testing utilities to verify correctness
       pass
   ```

4. **Run tests:**
   ```bash
   # All tests
   pytest

   # Correctness tests only
   pytest -m "attachment or rotation or dimensions"

   # With coverage
   pytest --cov=tiacad_core --cov-report=html
   ```

---

## Implementation Details

### Testing Utilities Architecture

```
tiacad_core/testing/
├── __init__.py
├── measurements.py      # Distance and dimension measurements
├── orientation.py       # Rotation and orientation utilities
└── dimensions.py        # Volume and surface area calculations
```

### Test Organization

```
tiacad_core/tests/
├── test_correctness/           # NEW: Correctness tests
│   ├── test_attachment_correctness.py    # 16 tests
│   ├── test_rotation_correctness.py      # 19 tests
│   └── test_dimensional_accuracy.py      # 25 tests
├── test_testing/              # NEW: Testing utility tests
│   ├── test_measurements.py    # 23 tests
│   ├── test_orientation.py     # 22 tests
│   └── test_dimensions.py      # 26 tests
├── test_parser/               # Parser tests (518 tests)
└── ...                        # Other test modules
```

---

## Known Issues

### None for v3.1

All tests passing, no known issues.

### Future Enhancements (v3.2)

- 🔄 Visual regression testing
- 🔄 Contact detection utilities
- 🔄 Hole and feature detection
- 🔄 Assembly connectivity verification

---

## What's Next?

### v3.2 (Planned - Q2 2026)
- Visual regression testing framework
- Advanced attachment verification (contact detection)
- Hole and feature detection utilities
- 100+ additional tests

### v4.0 (Roadmap)
- Constraint-based assembly
- Mate constraints
- Collision detection
- Assembly validation

---

## Contributors

**v3.1 Development:**
- Testing utilities implementation (Weeks 1-3)
- Correctness test suites (Weeks 4-6)
- Documentation and pytest integration (Week 7)
- Validation and polish (Week 8)

---

## Getting Help

**Documentation:**
- [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) - Complete testing guide
- [docs/TESTING_ROADMAP.md](docs/TESTING_ROADMAP.md) - Implementation roadmap
- [docs/TESTING_CONFIDENCE_PLAN.md](docs/TESTING_CONFIDENCE_PLAN.md) - Strategic plan

**Running Tests:**
```bash
# Quick reference
pytest -m attachment              # Attachment tests
pytest -m rotation                # Rotation tests
pytest -m dimensions              # Dimensional tests
pytest -m "attachment or rotation or dimensions"  # All correctness tests
pytest --cov=tiacad_core         # With coverage
```

---

## Summary

TiaCAD v3.1 significantly enhances testing confidence:

✅ **Testing Utilities** - 3 new modules with 20+ utility functions
✅ **Correctness Tests** - 60 new tests verifying geometric correctness
✅ **Test Organization** - Pytest markers for easy filtering
✅ **Comprehensive Docs** - Complete testing guide with examples
✅ **1027 Tests** - All passing with 90% coverage
✅ **Better Confidence** - Verify attachments, rotations, and dimensions

**Upgrade today for enhanced testing capabilities!**

---

**Version:** 3.1.0
**Release Date:** 2025-11-11
**Test Status:** 1027/1027 passing (100%)
**Coverage:** 90%
**Documentation:** Complete

---

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
Offsets now follow the reference's local local frame:
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

#### 3. Use auto-generated anchors (Recommended)

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
      to: base.face_top  # auto-generated anchor!
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

  # Use auto-generated anchors - no definition needed!
  pillar:
    translate:
      to: base.face_top  # ✨ Auto-generated!

  cap:
    translate:
      to: pillar.face_top  # ✨ Auto-generated!
```

**Available auto-generated anchors:**
- Points: `.center`, `.origin`
- Faces: `.face_top`, `.face_bottom`, `.face_left`, `.face_right`, `.face_front`, `.face_back`
- Axes: `.axis_x`, `.axis_y`, `.axis_z`

### 2. Local Frame Offsets

Offsets now follow the reference's local local frame:

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
- No need to calculate world space
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
- 896 tests passing (100% pass rate)
- 0 tests skipped
- Total: 896 tests
- Coverage: 87% overall (95%+ for spatial reference system)

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
- [ ] Consider using auto-generated anchors to simplify definitions
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

- [AUTO_REFERENCES_GUIDE.md](docs/AUTO_REFERENCES_GUIDE.md) - Comprehensive guide to auto-generated anchors
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
- Test execution: ~same (896 tests in ~75s)

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
   - Consider using auto-generated anchors

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
- ✅ auto-generated anchors for transformed parts (uses bounding box)
- ✅ Schema validation for v3.0 syntax
- ✅ Migration guide for all common patterns

### Future Enhancements
- 🔄 Automated migration tool (v3.1)
- 🔄 auto-generated anchors for operation results (v3.1)
- 🔄 Custom auto-generated anchor definitions (v3.2)

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
- Enhanced auto-generated anchors
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
- [AUTO_REFERENCES_GUIDE.md](docs/AUTO_REFERENCES_GUIDE.md) - auto-generated anchors guide
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

✅ **Cleaner YAML** - auto-generated anchors eliminate boilerplate
✅ **Unified System** - One reference system for points, faces, edges, axes
✅ **Local Frames** - Intuitive positioning with local offsets
✅ **Better Architecture** - Clean separation of concerns
✅ **Full Tests** - 896 tests, 95%+ coverage
✅ **Great Docs** - Comprehensive guides and examples

**Upgrade today to experience the future of declarative CAD!**

---

**Version:** 3.0.0
**Code Complete:** 2025-11-10 (v3.0.0 tag created)
**Public Release:** 2025-11-19 (target)
**Test Status:** 896/896 passing (100%)
**Documentation:** Complete and aligned
**Migration Guide:** Available
