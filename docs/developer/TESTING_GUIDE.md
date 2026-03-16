---
title: "TiaCAD Testing Guide"
type: guide
beth_topics:
  - tiacad
  - testing
  - correctness
  - visual-regression
---

# TiaCAD Testing Guide

**Updated:** 2026-03-15 (session: metallic-shade-0315)
**Status:** Active

---

## Table of Contents

1. [Current State](#current-state)
2. [Correctness Gap — What We Know](#correctness-gap--what-we-know)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Testing Utilities](#testing-utilities)
6. [Writing New Tests](#writing-new-tests)
7. [Troubleshooting](#troubleshooting)

---

## Current State

TiaCAD has **1405 passing tests** as of March 2026.

| Category | Location | Tests | Notes |
|---|---|---|---|
| Parser | `test_parser/` | ~520 | YAML → geometry pipeline |
| Correctness | `test_correctness/` | ~90 | Attachment, rotation, dimensions, example contracts |
| Visual regression | `test_visual_regression.py` | 57 | Pixel-diff vs reference images — catches regressions, not original correctness |
| DAG (incremental rebuild) | `test_dag/` | 101 | Graph, invalidation, cache, builder |
| Testing utilities | `test_testing/` | ~40 | Tests for the test utilities themselves |
| Integration | scattered | ~200 | Multi-component workflows |
| Unit | scattered | ~400 | Backend, part, spatial, stdlib contracts, etc. |

```bash
pytest                          # full suite — ~2 min
pytest tiacad_core/tests/test_correctness/   # geometric correctness — ~2s
pytest -m visual                # visual regression — ~60s
pytest tiacad_core/tests/test_dag/           # DAG tests — <1s
```

---

## Correctness Gap — What We Know

**The core problem:** TiaCAD can produce geometry that looks plausible but is wrong in ways the test suite doesn't catch.

### What the tests actually verify

| Layer | Tested | How |
|---|---|---|
| Primitive dimensions (box width, cylinder radius) | ✅ | `test_dimensional_accuracy.py` |
| Boolean volume math (union, difference, intersection) | ✅ | `test_dimensional_accuracy.py` |
| Attachment distance between parts | ✅ | `test_attachment_correctness.py` |
| Rotation angles on primitives | ✅ | `test_rotation_correctness.py` |
| Mesh validity (watertight, no self-intersections) | ✅ | `test_geometry_validation.py` — 3 examples |
| Visual pixel consistency vs reference images | ✅ | `test_visual_regression.py` — 49 examples |

### What's missing

**End-to-end geometric contracts on example files.**

49 example YAML files exist. The visual regression tests prove they "render the same as before" — but they cannot catch:

- A part built with **wrong dimensions** (a 50mm box instead of 100mm)
- **Misplaced geometry** — a hole that ended up in the wrong position
- A **boolean that silently failed** and left the solid untouched
- An **assembly with correct-shaped parts in wrong relative positions**

The visual regression tests only catch *looks different from the last snapshot*. They don't know if the snapshot was correct. And for subtle errors (a 2mm mistake, a 10° rotation error), pixel diff won't catch it at typical render resolution.

The `test_geometry_validation.py` covers 3 examples with `trimesh` validity checks. Zero of the 49 examples have dimension/volume assertions.

### The "snapshot of a bug" risk

The 51 visual reference images were generated at some point. If a bug existed at snapshot time, the reference *is* the bug. Visual regression tests would then actively protect incorrect behavior.

### What we've done about it

**Option A** (geometric contracts) is now in place — `test_correctness/test_example_contracts.py` covers all assembly examples with Tier 2 contracts. This is the primary regression net.

### Remaining approaches

**Option A — Geometric tests on key examples (highest value)**

For each important example, assert what the geometry should measure:
```python
# test_correctness/test_example_contracts.py
doc = TiaCADParser().parse_file("examples/bracket_with_hole.yaml")
part = doc.get_part("final")
dims = get_dimensions(part)
assert dims["width"] == pytest.approx(80.0, abs=0.1)
assert dims["height"] == pytest.approx(40.0, abs=0.1)
# Hole present: volume less than solid bounding box
assert get_volume(part) < 80 * 40 * 10
```
Start with 5–10 examples where you know the intended dimensions. This catches "built but wrong" directly.

**Option B — `--check` CLI flag (fast manual loop)**

```bash
python -m tiacad examples/bracket_with_hole.yaml --check
# ✓ Geometry valid (watertight, 1 component)
# ✓ Dimensions: 80.0 × 40.0 × 10.0 mm
# ✓ Volume: 28,450 mm³
# ✓ Parts in registry: final, base, hole_cyl
```
No test writing needed. Run this after any YAML change to see "does this look sane?" within 2 seconds. Highest value per hour for catching regressions during development.

**Option C — Audit all examples (ground truth establishment)**

Run all 49 examples, print dimensions + validity + volume for each, review together:
```bash
python -c "
from tiacad_core.parser import TiaCADParser
from tiacad_core.testing.dimensions import get_dimensions, get_volume
import os, glob

for f in sorted(glob.glob('examples/*.yaml')):
    try:
        doc = TiaCADParser().parse_file(f)
        asm = doc.get_assembly()
        from tiacad_core.part import Part
        from tiacad_core.geometry import CadQueryBackend
        p = Part('tmp', asm, {}, CadQueryBackend())
        d = get_dimensions(p)
        print(f'{os.path.basename(f)}: {d[\"width\"]:.1f}×{d[\"height\"]:.1f}×{d[\"depth\"]:.1f} vol={get_volume(p):.0f}')
    except Exception as e:
        print(f'{os.path.basename(f)}: ERROR {e}')
"
```
This establishes ground truth for what each example actually produces, so you can tell if something changed.

**Option D — Trust renderer (human + AI visual verification)**

The trust renderer is a multi-view colored rendering tool for visually confirming that TiaCAD operations produce the expected 3D structure. It renders each part in a distinct color with 4 viewpoints (isometric, front, top, side), an axis indicator, and a color legend — producing a single PNG you (or AI) can inspect and say "yep, that's right."

```bash
python scripts/trust_render.py examples/trust/stacked_boxes.yaml
# → trust_output/stacked_boxes.png: 4-panel render, red box on bottom, blue on top
```

This is especially useful for:
- Validating new primitives and operations as you build them
- Catching positioning bugs that geometric assertions miss (a part in the wrong place but correct shape)
- AI-assisted review — show the render and ask "is the blue cylinder centered on top of the red plate?"

The trust renderer lives in `tiacad_core/visual/trust_renderer.py`. Curated trust scenarios are in `examples/trust/`.

---

## Running Tests

```bash
# All tests
pytest

# Fast only (skip visual, ~10s)
pytest -m "not visual"

# Geometric correctness only (~2s)
pytest tiacad_core/tests/test_correctness/

# Visual regression (~60s)
pytest -m visual

# DAG tests (<1s)
pytest tiacad_core/tests/test_dag/

# Update visual reference images (creates new baselines)
UPDATE_VISUAL_REFERENCES=1 pytest -m visual

# Run only failed tests from last run
pytest --lf

# With coverage
pytest --cov=tiacad_core --cov-report=html
```

### Run by directory

```bash
pytest tiacad_core/tests/test_correctness/
pytest tiacad_core/tests/test_parser/
pytest tiacad_core/tests/test_dag/
pytest tiacad_core/tests/test_testing/
```

---

## Test Categories

### Pytest Markers

| Marker | Description | Command |
|---|---|---|
| `attachment` | Parts connect at correct locations | `pytest -m attachment` |
| `rotation` | Parts orient correctly | `pytest -m rotation` |
| `dimensions` | Measurements match spec | `pytest -m dimensions` |
| `visual` | Pixel-diff vs reference images | `pytest -m visual` |
| `integration` | Multi-component workflows | `pytest -m integration` |
| `parser` | YAML parser tests | `pytest -m parser` |
| `slow` | Tests taking >5s | `pytest -m "not slow"` |

### Test directories

```
tiacad_core/tests/
├── test_correctness/        # geometric correctness (68 tests)
│   ├── test_attachment_correctness.py   — part positioning
│   ├── test_dimensional_accuracy.py     — dimensions, volume, surface area
│   ├── test_geometry_validation.py      — mesh validity via trimesh
│   └── test_rotation_correctness.py     — rotation angles, normals
├── test_dag/                # DAG + incremental rebuild (101 tests)
│   ├── test_graph_builder.py
│   ├── test_model_graph.py
│   ├── test_invalidation_tracker.py
│   ├── test_build_cache.py
│   ├── test_incremental_builder.py
│   └── test_visualizer.py
├── test_parser/             # YAML → geometry pipeline (~520 tests)
├── test_testing/            # tests for testing utilities (~40 tests)
├── test_visualization/      # renderer tests
├── test_validation/         # validation rules
├── test_visual_regression.py  — pixel-diff for all examples
└── visual_references/       — 51 reference PNGs
```

---

## Testing Utilities

Import from `tiacad_core.testing.*`.

### Measurements

```python
from tiacad_core.testing.measurements import measure_distance, get_bounding_box_dimensions

# Distance between part centers
dist = measure_distance(part1, part2)

# Distance between specific faces
dist = measure_distance(box, cyl, ref1="face_top", ref2="face_bottom")
assert dist < 0.01  # should be touching

# Bounding box
dims = get_bounding_box_dimensions(part)
assert abs(dims['width'] - 50.0) < 0.1
```

### Orientation

```python
from tiacad_core.testing.orientation import get_orientation_angles, get_normal_vector, parts_aligned

angles = get_orientation_angles(part)  # {"roll": 0, "pitch": 45, "yaw": 90}
normal = get_normal_vector(part, "face_top")  # [0, 0, 1]
aligned = parts_aligned(part1, part2, axis="z", tolerance=0.01)
```

### Dimensions

```python
from tiacad_core.testing.dimensions import get_dimensions, get_volume, get_surface_area

dims = get_dimensions(part)
# → {"width": 80.0, "height": 40.0, "depth": 10.0, "volume": 28450, "surface_area": ...}

vol = get_volume(part)
area = get_surface_area(part)
```

### Visual Regression

```python
from tiacad_core.testing.visual_regression import VisualRegressionTester, RenderConfig, pytest_visual_compare

@pytest.mark.visual
def test_my_model():
    result = pytest_visual_compare(geometry=assembly, test_name="my_model", threshold=1.0)
    assert result.passed, f"Pixel diff: {result.pixel_diff_percentage:.2f}%"
```

**Updating references:**
```bash
UPDATE_VISUAL_REFERENCES=1 pytest -m visual -k "test_name"
```

---

## Writing New Tests

### Correctness test template

```python
import pytest
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.testing.dimensions import get_dimensions, get_volume

@pytest.mark.dimensions
def test_bracket_dimensions():
    """Bracket should be 80mm wide, hole reduces volume below solid."""
    doc = TiaCADParser().parse_file("examples/bracket_with_hole.yaml")
    part = doc.get_part("final")
    dims = get_dimensions(part)
    assert dims["width"] == pytest.approx(80.0, abs=0.1)
    assert dims["height"] == pytest.approx(40.0, abs=0.1)
    assert get_volume(part) < 80 * 40 * 10  # hole present
```

### Tolerances

- Distances: `< 0.01` mm
- Angles: `< 0.1` degrees
- Volumes: within `1%` of expected
- Dimensions: `abs=0.1` mm

### What to assert for each example

| Example type | What to test |
|---|---|
| Simple primitive | Dimensions match spec parameters |
| Boolean (difference) | Volume < solid bounding volume |
| Boolean (union) | Volume ≤ sum of parts |
| Transformed part | Position/angle matches transform spec |
| Pattern | Part count × spacing matches spec |
| Assembly | Key parts exist, relative positions correct |

---

## Troubleshooting

**Import errors:**
```bash
pip install -e .
```

**Tests too slow:**
```bash
pytest -m "not slow and not visual"
```

**Visual test fails but model looks correct:**
```bash
# Regenerate reference
UPDATE_VISUAL_REFERENCES=1 pytest -m visual -k "failing_test_name"
```

**Visual test passes but model was wrong:**
This is the "snapshot of a bug" problem — the reference captured incorrect geometry. Fix the bug, visually confirm the new output is correct, then regenerate the reference intentionally.

**Coverage report:**
```bash
pytest --cov=tiacad_core --cov-report=html
open htmlcov/index.html
```
