---
title: "TiaCAD Testing — Quick Reference"
type: reference
beth_topics:
  - tiacad
  - testing
  - correctness
---

# TiaCAD Testing — Quick Reference

**Updated:** 2026-07-09

---

## At a Glance

**Current baseline:** broad parser, correctness, DAG, visualization, and integration coverage.

| Suite | Scope | Runtime |
|---|---|---|
| Full suite | all automated coverage | ~2 min |
| Correctness only | analytical contracts | ~2s |
| DAG only | graph/cache/watch behavior | <1s |
| Visual regression | pixel-diff baselines | ~60s |
| Fast (not visual) | parser/correctness/DAG/unit coverage | ~10s |

**Core model:** use analytical contracts as the primary correctness oracle, visual renders as review evidence, and debug bundles for AI-assisted diagnosis. See [MODEL_VALIDATION.md](./MODEL_VALIDATION.md).

---

## Common Commands

```bash
# Run everything
pytest

# Skip visual (fast feedback)
pytest -m "not visual"

# Correctness only
pytest tiacad_core/tests/test_correctness/

# DAG tests
pytest tiacad_core/tests/test_dag/

# Visual regression
pytest -m visual

# Update visual references (intentional change)
UPDATE_VISUAL_REFERENCES=1 pytest -m visual

# Failed tests from last run
pytest --lf

# Coverage
pytest --cov=tiacad_core --cov-report=html

# Slowest 10 tests
pytest --durations=10
```

---

## Test Markers

```bash
pytest -m attachment     # part positioning
pytest -m rotation       # orientation correctness
pytest -m dimensions     # dimensional accuracy
pytest -m visual         # pixel-diff vs references
pytest -m integration    # multi-component workflows
pytest -m parser         # YAML parser tests
pytest -m "not slow"     # exclude slow tests
pytest -m "not visual and not slow"   # fast correctness loop
```

---

## Testing Utilities

### Dimensions

```python
from tiacad_core.testing.dimensions import get_dimensions, get_volume, get_surface_area

dims = get_dimensions(part)
# → {"width": 80.0, "height": 40.0, "depth": 10.0, "volume": 28450, "surface_area": ...}

assert dims["width"] == pytest.approx(80.0, abs=0.1)
assert get_volume(part) < 80 * 40 * 10   # hole present
```

### Measurements

```python
from tiacad_core.testing.measurements import measure_distance, get_bounding_box_dimensions

dist = measure_distance(part1, part2)                              # center-to-center
dist = measure_distance(box, cyl, ref1="face_top", ref2="face_bottom")
assert dist < 0.01   # touching

dims = get_bounding_box_dimensions(part)
assert abs(dims["width"] - 50.0) < 0.1
```

### Orientation

```python
from tiacad_core.testing.orientation import get_orientation_angles, get_normal_vector, parts_aligned

angles = get_orientation_angles(part)    # {"roll": 0, "pitch": 45, "yaw": 90}
normal = get_normal_vector(part, "face_top")   # [0, 0, 1]
aligned = parts_aligned(part1, part2, axis="z", tolerance=0.01)
```

### Visual Regression

```python
from tiacad_core.testing.visual_regression import pytest_visual_compare

@pytest.mark.visual
def test_model():
    result = pytest_visual_compare(geometry=asm, test_name="my_model", threshold=1.0)
    assert result.passed, f"Pixel diff: {result.pixel_diff_percentage:.2f}%"
```

---

## Writing a Correctness Test (Template)

```python
import pytest
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.dimensions import get_dimensions, get_volume

@pytest.mark.dimensions
def test_bracket_with_hole():
    """Bracket: 80×40×10mm, hole reduces volume below solid."""
    doc = TiaCADParser().parse_file("examples/bracket_with_hole.yaml")
    part = doc.get_part("final")
    dims = get_dimensions(part)
    assert dims["width"] == pytest.approx(80.0, abs=0.1)
    assert dims["height"] == pytest.approx(40.0, abs=0.1)
    assert get_volume(part) < 80 * 40 * 10
```

### Tolerances

| Type | Tolerance |
|---|---|
| Distances | `< 0.01` mm |
| Angles | `< 0.1` degrees |
| Volumes | within `1%` of expected |
| Dimensions | `abs=0.1` mm |

---

## Model Review Loop

For changed models, use this order:

1. Run focused parser/correctness tests.
2. Run `tiacad check <model>` for dimensions and geometry facts.
3. Run `tiacad debug <model> --bundle out/<name>` for AI/human review artifacts.
4. Inspect the trust render for spatial issues not yet encoded as contracts.
5. Promote repeated manual checks into contracts.

Useful commands:

```bash
tiacad check examples/foo.yaml
tiacad debug examples/foo.yaml --bundle out/foo-debug
tiacad debug examples/foo.yaml --compare out/previous-foo-debug
python scripts/validate_examples.py
```

See [TESTING_GUIDE.md](./TESTING_GUIDE.md#testing-model) and [MODEL_VALIDATION.md](./MODEL_VALIDATION.md) for the full model.

---

## File Map

```
tiacad_core/
├── testing/
│   ├── dimensions.py          get_dimensions, get_volume, get_surface_area
│   ├── measurements.py        measure_distance, get_bounding_box_dimensions
│   ├── orientation.py         get_orientation_angles, get_normal_vector, parts_aligned
│   └── visual_regression.py   VisualRegressionTester, pytest_visual_compare
│
└── tests/
    ├── test_correctness/      analytical contracts and mesh validity
    ├── test_dag/              graph, invalidation, cache, incremental builder
    ├── test_parser/           YAML → geometry pipeline
    ├── test_testing/          tests for testing utilities
    ├── test_visualization/    renderer tests
    ├── test_validation/       validation rules
    ├── test_visual_regression.py   pixel-diff against visual references
    └── visual_references/     reference PNGs
```
