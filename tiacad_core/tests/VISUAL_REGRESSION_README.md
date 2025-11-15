# Visual Regression Testing

**Version:** TiaCAD v3.1 Phase 2
**Status:** Complete

## Overview

Visual regression testing automatically detects unintended visual changes in 3D model rendering by comparing test outputs against reference images.

## Quick Start

### Run Visual Tests

```bash
# Run all visual regression tests
pytest -m visual

# Run specific test
pytest -m visual -k "simple_box"

# Verbose output
pytest -m visual -v
```

### Update Reference Images

```bash
# Update all references
UPDATE_VISUAL_REFERENCES=1 pytest -m visual

# Update specific test
UPDATE_VISUAL_REFERENCES=1 pytest -m visual -k "simple_box"

# Or use the helper script
python scripts/update_visual_references.py
```

### Manage References

```bash
# List all reference images
python scripts/update_visual_references.py --list

# Clean test outputs
python scripts/update_visual_references.py --clean
```

## Directory Structure

```
tiacad_core/
├── visual_references/     # Reference images (committed to git)
│   ├── simple_box.png
│   ├── simple_extrude.png
│   └── ...
├── visual_output/         # Test output images (gitignored)
│   ├── simple_box.png
│   └── ...
└── visual_diffs/          # Diff images (gitignored)
    ├── simple_box_diff.png
    └── ...
```

## How It Works

1. **Render**: Test geometry is rendered to PNG using trimesh + matplotlib
2. **Compare**: Rendered image is compared pixel-by-pixel against reference
3. **Threshold**: Difference percentage must be below threshold (default: 1%)
4. **Report**: If test fails, diff image is generated showing differences

## Writing Visual Tests

### Simple Test

```python
import pytest
from tiacad_core.testing.visual_regression import pytest_visual_compare
import cadquery as cq

@pytest.mark.visual
def test_my_model():
    # Create geometry
    box = cq.Workplane("XY").box(10, 10, 10)

    # Visual regression test
    result = pytest_visual_compare(
        geometry=box,
        test_name="my_model",
        threshold=1.0
    )

    assert result.passed
```

### Advanced Test with Custom Config

```python
from tiacad_core.testing.visual_regression import (
    VisualRegressionTester,
    RenderConfig
)

@pytest.mark.visual
def test_complex_assembly(visual_tester):
    # Custom render config
    config = RenderConfig(
        width=1024,
        height=768,
        camera_position=(100, 100, 100),
        background_color='lightgray',
        dpi=150
    )

    # Test
    result = visual_tester.render_and_compare(
        geometry=assembly,
        test_name="complex_assembly",
        threshold=2.0,  # More tolerance
        config=config
    )

    assert result.passed
```

## Comparison Metrics

Each test returns a `VisualDiffResult` with:

- **pixel_diff_percentage**: % of pixels that differ (0-100)
- **rms_diff**: Root mean square color difference
- **mean_pixel_diff**: Average difference across all pixels
- **max_pixel_diff**: Maximum single-pixel difference (0-255)
- **passed**: Boolean (True if diff ≤ threshold)
- **diff_path**: Path to generated diff image

## Configuring Thresholds

Different models need different thresholds:

| Model Type | Recommended Threshold | Reason |
|------------|----------------------|---------|
| Simple primitives | 0.1% | Very consistent |
| Complex assemblies | 1.0% | Small variations OK |
| Text/curved features | 2.0% | Anti-aliasing varies |

## CI/CD Integration

Visual tests run automatically on:
- Every push to main or claude/* branches
- Every pull request

### Workflow Behavior

1. **First run**: Generates references automatically
2. **Normal runs**: Compares against committed references
3. **On failure**: Uploads diff images as artifacts

### Downloading Artifacts

If visual tests fail in CI:

1. Go to GitHub Actions run
2. Scroll to "Artifacts" section
3. Download `visual-regression-outputs`
4. Review diff images locally

## Best Practices

### DO:
- ✅ Commit reference images to git
- ✅ Review diff images when tests fail
- ✅ Use consistent render settings
- ✅ Update references deliberately
- ✅ Set appropriate thresholds

### DON'T:
- ❌ Update references without reviewing
- ❌ Commit output/diff directories
- ❌ Use random camera positions
- ❌ Set thresholds too high
- ❌ Ignore failing visual tests

## Troubleshooting

### "Reference image not found"

**Solution**: Generate references first:
```bash
UPDATE_VISUAL_REFERENCES=1 pytest -m visual
```

### Tests fail with tiny differences

**Cause**: Anti-aliasing or rendering variations

**Solutions**:
1. Increase threshold slightly (0.1% → 0.5%)
2. Ensure consistent rendering environment
3. Check if changes are acceptable

### Slow test execution

**Solutions**:
1. Lower DPI in RenderConfig (150 → 100)
2. Run tests in parallel: `pytest -m visual -n auto`
3. Run specific tests only: `pytest -m visual -k "simple"`

### CI tests pass locally but fail in CI

**Cause**: Different rendering environment

**Solutions**:
1. Use same Python version as CI (3.11)
2. Check if system dependencies differ
3. Slightly increase threshold for CI tolerance

## Example Workflow

### After Making Changes

```bash
# 1. Run visual tests
pytest -m visual

# 2. If tests fail, review diff images
ls tiacad_core/visual_diffs/

# 3a. If changes are bugs, fix code and re-run
#     (repeat until tests pass)

# 3b. If changes are intentional, update references
UPDATE_VISUAL_REFERENCES=1 pytest -m visual

# 4. Verify updates
pytest -m visual

# 5. Commit
git add tiacad_core/visual_references/
git commit -m "Update visual references for feature X"
```

## Architecture

### Rendering Pipeline

```
CadQuery Geometry
    ↓
Export to STL bytes
    ↓
Load with trimesh
    ↓
Render with matplotlib 3D
    ↓
Save as PNG
```

### Comparison Pipeline

```
Reference PNG + Test PNG
    ↓
Load with Pillow
    ↓
Pixel-by-pixel difference
    ↓
Calculate metrics (RMS, mean, max, %)
    ↓
Generate diff image (enhanced 10x)
    ↓
Return VisualDiffResult
```

## Related Documentation

- [TESTING_GUIDE.md](../../docs/TESTING_GUIDE.md) - Complete testing documentation
- [TESTING_QUICK_REFERENCE.md](../../docs/TESTING_QUICK_REFERENCE.md) - Quick command reference
- [CHANGELOG.md](../../CHANGELOG.md) - v3.1 Phase 2 changes

## Support

For issues or questions:
1. Check this README
2. Review TESTING_GUIDE.md
3. Open a GitHub issue
4. Check GitHub Actions logs

---

**Last Updated:** 2025-11-14
**TiaCAD Version:** v3.1 Phase 2
