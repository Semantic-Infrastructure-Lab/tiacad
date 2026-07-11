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

**Updated:** 2026-07-09
**Status:** Active

---

## Table of Contents

1. [Current State](#current-state)
2. [Testing Model](#testing-model)
3. [Correctness Gap — What We Know](#correctness-gap--what-we-know)
4. [Running Tests](#running-tests)
5. [Test Categories](#test-categories)
6. [Testing Utilities](#testing-utilities)
7. [Writing New Tests](#writing-new-tests)
8. [Troubleshooting](#troubleshooting)

---

## Current State

TiaCAD has a large automated test suite spanning parser, correctness, DAG, visualization, and integration coverage.

| Category | Location | Scope | Notes |
|---|---|---|---|
| Parser | `test_parser/` | broad | YAML → geometry pipeline |
| Correctness | `test_correctness/` | broad | Attachment, rotation, dimensions, example contracts, trust contracts |
| Visual regression | `test_visual_regression.py` | broad | Pixel-diff vs reference images — catches regressions, not original correctness |
| DAG (incremental rebuild) | `test_dag/` | focused | Graph, invalidation, cache, builder |
| Testing utilities | `test_testing/` | focused | Tests for the test utilities themselves |
| Integration | scattered | broad | Multi-component workflows |
| Unit | scattered | broad | Backend, part, spatial, stdlib contracts, etc. |

```bash
pytest                          # full suite — ~2 min
pytest tiacad_core/tests/test_correctness/   # geometric correctness — ~2s
pytest -m visual                # visual regression — ~60s
pytest tiacad_core/tests/test_dag/           # DAG tests — <1s
```

---

## Testing Model

The canonical evidence model — schema → analytical contracts → mesh validity → visual
review → debug bundles/deltas — is documented in [MODEL_VALIDATION.md](MODEL_VALIDATION.md).
The short version: visual regression is useful, but it is not the oracle. If expected
behavior can be stated as a measured fact, prefer a contract.

---

## Correctness Gap — What We Know

**The core problem:** TiaCAD can produce geometry that looks plausible but is wrong in ways the test suite doesn't catch.

### What the tests actually verify

| Layer | Tested | How |
|---|---|---|
| Primitive dimensions (box width, cylinder radius) | ✅ | `test_dimensional_accuracy.py` |
| Boolean volume math (union, difference, intersection) | ✅ | `test_dimensional_accuracy.py` + `test_trust_contracts.py` |
| Attachment distance between parts | ✅ | `test_attachment_correctness.py` |
| Rotation angles on primitives | ✅ | `test_rotation_correctness.py` |
| Mesh validity (watertight, no self-intersections) | ✅ | `test_geometry_validation.py` and geometry summaries |
| Visual pixel consistency vs reference images | ✅ | `test_visual_regression.py` |
| Trust scenario geometry | ✅ | `test_trust_contracts.py` — per-part dims + volumes + positions |

### What visual regression still cannot prove

The visual regression tests prove that rendered output is consistent with a reference image. They cannot prove the reference image was correct, and they cannot reliably catch:

- A part built with **wrong dimensions** (a 50mm box instead of 100mm)
- **Misplaced geometry** — a hole that ended up in the wrong position
- A **boolean that silently failed** and left the solid untouched
- An **assembly with correct-shaped parts in wrong relative positions**

Visual tests only catch *looks different from the last snapshot*. For subtle errors (a 2mm mistake, a 10° rotation error), pixel diff may not catch it at typical render resolution.

### The "snapshot of a bug" risk

The 51 visual reference images were generated at some point. If a bug existed at snapshot time, the reference *is* the bug. Visual regression tests would then actively protect incorrect behavior.

### What we've done about it

Geometric contracts are now in place for the most important correctness paths:
- `test_correctness/test_example_contracts.py` — all assembly examples with Tier 2 contracts
- `test_correctness/test_trust_contracts.py` — all 20 trust YAMLs with per-part dimension, volume, and positional assertions (session: rainbow-ember-0316)

Together these are the primary regression net against "built but wrong" geometry.

### Remaining approaches

**A. Add or improve geometric contracts where intent is clear**

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
This catches "built but wrong" directly. When a manual review finds a meaningful expected value, promote it into a test.

**B. Use `tiacad check` and `tiacad debug` for fast manual and AI-assisted review**

```bash
tiacad check examples/bracket_with_hole.yaml
# ✓ Geometry valid (watertight, 1 component)
# ✓ Dimensions: 80.0 × 40.0 × 10.0 mm
# ✓ Volume: 28,450 mm³
# ✓ Parts in registry: final, base, hole_cyl

tiacad debug examples/bracket_with_hole.yaml --bundle out/debug-bracket
```
No test writing needed. Use this after YAML changes to inspect measured facts, validation reports, build traces, and trust renders.

**C. Audit examples with structured summaries**

Run the example validator or generate debug bundles for changed examples:
```bash
python scripts/validate_examples.py
tiacad debug examples/awesome_guitar_hanger.yaml --bundle out/hanger-debug
```
This gives reviewers a measured baseline for what the examples currently produce.

**D. Use the trust renderer as a human + AI visual review layer**

The trust renderer is a multi-view colored rendering tool for visually confirming that TiaCAD operations produce the expected 3D structure. It renders each part in a distinct color across 8 viewpoints in a 2×4 grid — two opposite isometrics (so no side or back face is hidden from both), an X-Ray pass for internal/occluded features, and Top/Front/Rear/Side/Bottom orthographics with dimension overlays — plus an axis indicator and a color legend, producing a single PNG you (or AI) can inspect and say "yep, that's right." The opposite-diagonal isometrics matter for review: a part mirrored to the wrong side or a feature on a back face is invisible from a single angle but shows up here.

For assemblies fused into one solid by union, the renderer decomposes the final part along its operation DAG and colors each component distinctly (subtracted parts appear as translucent-red voids in the X-Ray panel). Without this, a fused assembly renders as one flat-colored blob where you can judge the silhouette but not whether the parts are actually connected or correctly placed — the exact class of error visual review is supposed to catch. This makes left/right symmetry, part connectivity, and misplacement directly inspectable per-component.

```bash
python scripts/trust_render.py examples/trust/stacked_boxes.yaml
# → trust_output/stacked_boxes.png: 4-panel render, red box on bottom, blue on top
```

This is especially useful for:
- Validating new primitives and operations as you build them
- Catching positioning bugs that geometric assertions miss (a part in the wrong place but correct shape)
- AI-assisted review — show the render and ask "is the blue cylinder centered on top of the red plate?"

The trust renderer lives in `tiacad_core/visual/trust_renderer.py`. Curated trust scenarios are in `examples/trust/`.

### Future validation improvements

The highest-value next steps are:

- model-local `contracts:` in YAML
- a `tiacad verify` command that evaluates those contracts
- reference-based measurements between anchors/faces/axes
- before/after operation summaries in debug bundles
- annotated trust renders with failed contract callouts
- intentionally broken negative trust scenarios

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
├── test_correctness/        # geometric correctness
│   ├── test_attachment_correctness.py   — part positioning
│   ├── test_dimensional_accuracy.py     — dimensions, volume, surface area
│   ├── test_geometry_validation.py      — mesh validity via trimesh
│   └── test_rotation_correctness.py     — rotation angles, normals
├── test_dag/                # DAG + incremental rebuild
│   ├── test_graph_builder.py
│   ├── test_model_graph.py
│   ├── test_invalidation_tracker.py
│   ├── test_build_cache.py
│   ├── test_incremental_builder.py
│   └── test_visualizer.py
├── test_parser/             # YAML → geometry pipeline
├── test_testing/            # tests for testing utilities
├── test_visualization/      # renderer tests
├── test_validation/         # validation rules
├── test_visual_regression.py  — pixel-diff for all examples
└── visual_references/       — visual reference PNGs
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

### Testing deprecation warnings

Legacy v3.0/v3.1 syntax still builds but raises `DeprecationWarning` (see
`docs/developer/API_DEPRECATION_STRATEGY.md`). Assert both the warning *and*
that the backward-compat mapping produces the same result as the new syntax:

```python
import warnings
import pytest
from tiacad_core.geometry import MockBackend
from tiacad_core.parser.tiacad_parser import TiaCADParser

def test_old_cone_params_warn():
    with pytest.warns(DeprecationWarning, match="radius_bottom.*deprecated"):
        doc = TiaCADParser.parse_string(OLD_CONE_YAML, backend=MockBackend())
    assert doc.parts.exists("frustum")

def test_new_syntax_is_silent():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        TiaCADParser.parse_string(NEW_CONE_YAML, backend=MockBackend())
    assert not [w for w in caught if issubclass(w.category, DeprecationWarning)]
```

Run `pytest -W error::DeprecationWarning` to treat any *new* deprecated usage
in the test corpus as a hard failure. Worked examples:
`tiacad_core/tests/test_parser/test_deprecation_warnings.py`.

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

**Inspecting a model interactively (rotate/zoom/pan), not just the static trust render:**
```bash
tiacad build examples/your_model.yaml -o /tmp/model.stl
f3d /tmp/model.stl   # apt install f3d if missing; left-drag orbit, scroll zoom, right-drag pan
```
`pyvista`'s built-in `Plotter.export_html()` is **broken** in this environment — the
`trame_vtk` package's bundled `static_viewer.html` template is corrupted (it's a cached
"404 | VTK.js" doc page, not the real viewer), so it silently writes a useless HTML file
instead of raising. `pip install --force-reinstall trame_vtk` may fix it if that path is
ever needed; `f3d` is the reliable local alternative in the meantime.
