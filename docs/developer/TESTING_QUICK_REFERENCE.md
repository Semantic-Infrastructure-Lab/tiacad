# TiaCAD Testing Confidence - Quick Reference

**Version:** 1.0
**Created:** 2025-11-10
**Related:** [TESTING_CONFIDENCE_PLAN.md](./TESTING_CONFIDENCE_PLAN.md) | [TESTING_ROADMAP.md](./TESTING_ROADMAP.md)

---

## At a Glance

**Goal:** Build confidence that TiaCAD YAML specifications translate correctly into 3D models.

**Four Dimensions:**
1. **Attachment** - Parts connect at correct locations
2. **Rotation** - Parts orient correctly
3. **Visual** - Models look correct
4. **Dimensions** - Measurements are accurate

**Current Status (v3.0):** 896 tests, 84% coverage
**Target (v3.1):** 950+ tests, 90% coverage
**Target (v3.2):** 1050+ tests, visual regression
**Target (v3.3+):** 1200+ tests, stress testing

---

## Quick Start

### Running Tests

```bash
# All tests
pytest

# Only attachment tests
pytest -m attachment

# Only rotation tests
pytest -m rotation

# Only dimensional tests
pytest -m dimensions

# Only visual tests
pytest -m visual

# Fast tests (exclude visual and stress)
pytest -m "not visual and not stress"

# With coverage
pytest --cov=tiacad_core
```

### Saving Visual References

```bash
# Save new references for visual tests
SAVE_REFERENCE=1 pytest -m visual

# Save specific example
SAVE_REFERENCE=1 pytest tests/test_correctness/test_visual_correctness.py::test_guitar_hanger
```

---

## Testing Utilities (v3.1+)

### Measurement

```python
from tiacad_core.testing.measurements import measure_distance

# Distance between part centers
dist = measure_distance(part1, part2)

# Distance between specific reference points
dist = measure_distance(
    box, cylinder,
    ref1="face_top.center",
    ref2="face_bottom.center"
)
```

### Orientation

```python
from tiacad_core.testing.orientation import (
    get_orientation_angles,
    get_normal_vector,
    parts_aligned
)

# Get rotation angles
angles = get_orientation_angles(part)  # {"roll": 0, "pitch": 45, "yaw": 90}

# Get face normal
normal = get_normal_vector(part, "face_top")  # [0, 0, 1]

# Check alignment
aligned = parts_aligned(part1, part2, axis="z", tolerance=0.5)
```

### Dimensions

```python
from tiacad_core.testing.dimensions import (
    get_dimensions,
    get_volume,
    get_surface_area
)

# Get bounding box dimensions
dims = get_dimensions(part)  # {"width": 50, "height": 30, "depth": 20}

# Get volume
volume = get_volume(part)  # 30000.0 cubic units

# Get surface area
area = get_surface_area(part)  # 6200.0 square units
```

### Visual (v3.2+)

```python
from tiacad_core.testing.visual_regression import VisualRegression

vr = VisualRegression()

# Save reference
vr.save_reference("my_part", part)

# Verify against reference
assert vr.verify_against_reference("my_part", part, threshold=0.95)
```

---

## Test Patterns

### Attachment Correctness

```python
@pytest.mark.attachment
def test_cylinder_on_box():
    """Verify cylinder sits on box top."""
    yaml = """
    parts:
      - name: base
        type: box
        size: [50, 50, 10]
      - name: post
        type: cylinder
        radius: 5
        height: 20
        position: base.face_top
    """

    model = build_model(yaml)

    # Verify zero distance
    dist = measure_distance(
        model.get("base"),
        model.get("post"),
        ref1="face_top.center",
        ref2="face_bottom.center"
    )
    assert dist < 0.001
```

### Rotation Correctness

```python
@pytest.mark.rotation
def test_rotated_box():
    """Verify box rotated 45° around Z."""
    yaml = """
    parts:
      - name: box
        type: box
        size: [10, 20, 5]
        rotation:
          axis: [0, 0, 1]
          angle: 45
    """

    model = build_model(yaml)
    box = model.get("box")

    # Verify yaw angle
    angles = get_orientation_angles(box)
    assert abs(angles["yaw"] - 45.0) < 0.1
```

### Visual Correctness

```python
@pytest.mark.visual
def test_guitar_hanger_appearance(visual_tester):
    """Verify guitar hanger looks correct."""
    yaml = load_file("examples/guitar_hanger.yaml")
    model = build_model(yaml)

    assert visual_tester.verify_against_reference(
        "guitar_hanger",
        model.get_default_part(),
        threshold=0.95
    )
```

### Dimensional Accuracy

```python
@pytest.mark.dimensions
def test_box_volume():
    """Verify box volume calculation."""
    yaml = """
    parts:
      - name: box
        type: box
        size: [10, 20, 5]
    """

    model = build_model(yaml)
    box = model.get("box")

    volume = get_volume(box)
    expected = 10 * 20 * 5  # 1000

    assert abs(volume - expected) < 0.1
```

---

## Timeline Summary

### Phase 1: v3.1 (Q1 2026) - 6-8 weeks

**Focus:** Core utilities

**Week 1:** Distance & position utilities
**Week 2:** Orientation & rotation utilities
**Week 3:** Dimensional utilities
**Week 4:** Attachment tests
**Week 5:** Rotation tests
**Week 6:** Dimensional tests
**Week 7:** CI/CD integration
**Week 8:** Coverage & polish

**Deliverables:**
- 3 new utility modules
- 48+ new correctness tests
- 950+ total tests
- 90% coverage

### Phase 2: v3.2 (Q2 2026) - 8-10 weeks

**Focus:** Visual regression & advanced features

**Weeks 1-2:** Research & design
**Weeks 3-4:** Visual regression implementation
**Weeks 5-6:** Generate references & tests
**Week 7:** Contact detection
**Week 8:** Feature detection (holes, fillets)
**Week 9:** CI/CD integration
**Week 10:** Polish & documentation

**Deliverables:**
- Visual regression framework
- 50+ visual tests
- Contact detection
- Hole/feature detection
- 1050+ total tests

### Phase 3: v3.3+ (Q3+ 2026) - Ongoing

**Focus:** Stress testing & optimization

**Tasks:**
- Large assembly tests (100+ parts)
- Property-based testing
- Differential testing
- Mutation testing
- Performance benchmarks

**Deliverables:**
- Stress test suite
- Property-based tests
- 1200+ total tests
- 80%+ mutation score

---

## Key Metrics

### Test Count Growth

| Version | Total Tests | New Tests | Coverage |
|---------|-------------|-----------|----------|
| v3.0 | 896 | - | 84% |
| v3.1 | 950+ | +54+ | 90% |
| v3.2 | 1050+ | +100+ | 92% |
| v3.3+ | 1200+ | +150+ | 95% |

### Correctness Coverage

| Dimension | v3.0 | v3.1 | v3.2 | v3.3+ |
|-----------|------|------|------|-------|
| Attachment | 5% | 60% | 90% | 95% |
| Rotation | 20% | 70% | 90% | 95% |
| Visual | 0% | 25% | 100% | 100% |
| Dimensions | 40% | 80% | 95% | 98% |

---

## File Structure

```
tiacad_core/
├── testing/                          # Testing utilities (v3.1+)
│   ├── __init__.py
│   ├── measurements.py               # Distance, contact detection
│   ├── orientation.py                # Rotation, normals, alignment
│   ├── dimensions.py                 # Dimensions, volume, area, holes
│   └── visual_regression.py          # Visual testing (v3.2+)
│
tests/
├── test_testing/                     # Tests for testing utilities
│   ├── test_measurements.py
│   ├── test_orientation.py
│   ├── test_dimensions.py
│   └── test_visual_regression.py
│
├── test_correctness/                 # Correctness tests (v3.1+)
│   ├── test_attachment_correctness.py
│   ├── test_rotation_correctness.py
│   ├── test_dimensional_accuracy.py
│   └── test_visual_correctness.py   # (v3.2+)
│
└── visual_references/                # Reference images (v3.2+)
    ├── guitar_hanger.png
    ├── mounting_bracket.png
    └── ...

docs/
├── TESTING_CONFIDENCE_PLAN.md        # Full strategic plan
├── TESTING_ROADMAP.md                # Week-by-week implementation guide
├── TESTING_QUICK_REFERENCE.md        # This file
├── TESTING_GUIDE.md                  # How-to guide (v3.1+)
├── TESTING_UTILITIES_API.md          # API reference (v3.2+)
└── VISUAL_REGRESSION_GUIDE.md        # Visual testing guide (v3.2+)
```

---

## Common Tasks

### Adding a New Attachment Test

1. Create test in `tests/test_correctness/test_attachment_correctness.py`
2. Mark with `@pytest.mark.attachment`
3. Use `measure_distance()` to verify attachment
4. Run: `pytest -m attachment`

### Adding a New Rotation Test

1. Create test in `tests/test_correctness/test_rotation_correctness.py`
2. Mark with `@pytest.mark.rotation`
3. Use `get_orientation_angles()` or `get_normal_vector()`
4. Run: `pytest -m rotation`

### Adding a New Visual Test (v3.2+)

1. Create test in `tests/test_correctness/test_visual_correctness.py`
2. Mark with `@pytest.mark.visual`
3. Save reference: `SAVE_REFERENCE=1 pytest <test>`
4. Verify: `pytest <test>`

### Updating Coverage

1. Run: `pytest --cov=tiacad_core --cov-report=html`
2. Open: `htmlcov/index.html`
3. Identify gaps
4. Add tests for uncovered code

---

## Troubleshooting

### Visual Test Failing

**Problem:** Visual test fails but model looks correct

**Solutions:**
1. Check similarity threshold (may need adjustment)
2. Regenerate reference: `SAVE_REFERENCE=1 pytest <test>`
3. Check for platform-specific rendering differences

### Attachment Test Failing

**Problem:** `measure_distance()` returns non-zero distance

**Solutions:**
1. Check reference names are correct (`"face_top"` vs `"face_top.center"`)
2. Verify parts exist in model
3. Check tolerance (may need to increase from 0.001)

### Rotation Test Failing

**Problem:** Angles don't match expected

**Solutions:**
1. Check rotation order (axis-angle vs quaternion vs Euler)
2. Verify gimbal lock isn't causing issues
3. Use normal vectors instead of angles for verification

---

## Resources

**Documentation:**
- [TESTING_CONFIDENCE_PLAN.md](./TESTING_CONFIDENCE_PLAN.md) - Full plan
- [TESTING_ROADMAP.md](./TESTING_ROADMAP.md) - Implementation timeline
- [PROJECT.md](../PROJECT.md) - TiaCAD overview

**External:**
- [pytest documentation](https://docs.pytest.org/)
- [numpy.testing](https://numpy.org/doc/stable/reference/routines.testing.html)
- [trimesh documentation](https://trimsh.org/)

---

## Quick Wins

**Easy improvements you can make today:**

1. **Add dimension test for new primitive**
   ```python
   def test_new_primitive_dimensions():
       yaml = """..."""
       model = build_model(yaml)
       dims = get_dimensions(model.get("part"))
       assert dims["width"] == expected_width
   ```

2. **Add attachment test for example**
   ```python
   def test_example_attachment():
       yaml = load_file("examples/my_example.yaml")
       model = build_model(yaml)
       dist = measure_distance(model.get("part1"), model.get("part2"))
       assert dist < 0.001
   ```

3. **Verify rotation correctness**
   ```python
   def test_rotation():
       yaml = """..."""
       model = build_model(yaml)
       angles = get_orientation_angles(model.get("part"))
       assert abs(angles["yaw"] - 45.0) < 0.1
   ```

---

**Last Updated:** 2025-11-10
**Maintainer:** TIA Project
**Status:** Active Development
