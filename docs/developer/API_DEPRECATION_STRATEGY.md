# Deprecation Warnings Implementation Plan

**Created**: 2026-02-15
**Session**: mountain-snow-0215
**Status**: Planned (not yet implemented)

---

## Overview

Add runtime deprecation warnings for old API patterns that were updated in v3.1.x. Users should see clear migration messages when using deprecated syntax.

---

## Deprecated Patterns

### 1. Cone Parameters

**Location**: `tiacad_core/parser/parts_builder.py::_build_cone()`

**Old syntax**:
```yaml
parameters:
  radius_bottom: 10
  radius_top: 5
```

**New syntax**:
```yaml
parameters:
  radius1: 10  # Bottom radius
  radius2: 5   # Top radius
```

**Implementation**:
```python
# In _build_cone method, after line 281:
params = spec.get('parameters', spec)

# Add backward compatibility check
if 'radius_bottom' in params or 'radius_top' in params:
    import warnings
    warnings.warn(
        f"Cone '{name}': 'radius_bottom' and 'radius_top' are deprecated. "
        f"Use 'radius1' (bottom) and 'radius2' (top) instead. "
        f"See docs/developer/MIGRATION_GUIDE_V3.md for details.",
        DeprecationWarning,
        stacklevel=2
    )
    # Map old names to new names
    if 'radius_bottom' in params:
        params['radius1'] = params['radius_bottom']
    if 'radius_top' in params:
        params['radius2'] = params['radius_top']
```

---

### 2. Pattern Spacing

**Location**: `tiacad_core/parser/pattern_builder.py::build_pattern()`

**Old syntax**:
```yaml
operations:
  - pattern:
      type: linear
      spacing: 10
      direction: X
```

**New syntax**:
```yaml
operations:
  - pattern:
      type: linear
      spacing: [10, 0, 0]  # [dx, dy, dz]
```

**Implementation**:
```python
# In pattern_builder.py, after extracting spacing parameter:
if 'direction' in pattern_spec and isinstance(spacing, (int, float)):
    import warnings
    warnings.warn(
        "Pattern spacing with scalar + direction is deprecated. "
        "Use vector format: spacing: [dx, dy, dz]. "
        "See docs/developer/MIGRATION_GUIDE_V3.md for details.",
        DeprecationWarning,
        stacklevel=2
    )
    # Convert to vector format
    direction = pattern_spec['direction'].upper()
    spacing_vector = [0, 0, 0]
    if direction == 'X':
        spacing_vector[0] = spacing
    elif direction == 'Y':
        spacing_vector[1] = spacing
    elif direction == 'Z':
        spacing_vector[2] = spacing
    spacing = spacing_vector
```

---

### 3. Transform Translate Offset Wrapper

**Location**: `tiacad_core/parser/operations_builder.py::_apply_translate()`

**Old syntax** (when used alone):
```yaml
translate:
  offset: [60, 40, 0]
```

**New syntax**:
```yaml
translate: [60, 40, 0]
```

**Note**: `offset:` is still valid when used with `to:` parameter!

**Implementation**:
```python
# In operations_builder.py, when parsing translate:
if isinstance(translate_spec, dict) and 'offset' in translate_spec and 'to' not in translate_spec:
    import warnings
    warnings.warn(
        "Using 'offset:' wrapper for simple translation is deprecated. "
        "Use direct coordinate list: translate: [x, y, z]. "
        "Note: 'offset:' is still valid when used with 'to:' parameter. "
        "See docs/developer/MIGRATION_GUIDE_V3.md for details.",
        DeprecationWarning,
        stacklevel=2
    )
    # Extract offset value
    translate_spec = translate_spec['offset']
```

---

### 4. Export List Format

**Location**: `tiacad_core/parser/tiacad_parser.py::parse_dict()`

**Old syntax**:
```yaml
export:
  - filename: model.step
    parts: [base, arm]
```

**New syntax**:
```yaml
export:
  default_part: model
  formats: [step, stl]
```

**Implementation**:
```python
# In tiacad_parser.py, when parsing export section:
export_config = yaml_data.get('export', {})

if isinstance(export_config, list):
    import warnings
    warnings.warn(
        "Export list format is deprecated. "
        "Use dict format: export: {default_part: 'name', formats: [...]}"
        "See docs/developer/MIGRATION_GUIDE_V3.md for details.",
        DeprecationWarning,
        stacklevel=2
    )
    # Convert to new format (best effort)
    # Take first export entry as default
    if export_config:
        first_export = export_config[0]
        export_config = {
            'filename': first_export.get('filename', 'output'),
            'parts': first_export.get('parts', [])
        }
```

---

## Implementation Checklist

- [ ] Add deprecation warning for cone parameters (`radius_bottom`/`radius_top`)
- [ ] Add deprecation warning for pattern spacing (scalar + direction)
- [ ] Add deprecation warning for translate offset wrapper (when used alone)
- [ ] Add deprecation warning for export list format
- [ ] Add backward compatibility logic for all patterns
- [ ] Test with deprecated examples to ensure warnings appear
- [ ] Test that new syntax works without warnings
- [ ] Update TESTING_GUIDE.md with deprecation testing instructions
- [ ] Add pytest tests for deprecation warnings (use `pytest.warns()`)

---

## Testing

### Manual Testing

Test each deprecated pattern generates a warning:

```bash
# Create test files with old syntax
echo "parts:
  cone:
    primitive: cone
    parameters:
      radius_bottom: 10
      radius_top: 5
      height: 20
export:
  default_part: cone" > test_old_cone.yaml

# Run and check for deprecation warning
tiacad build test_old_cone.yaml 2>&1 | grep -i deprecat
```

### Automated Testing

Add to `tiacad_core/tests/test_parser/test_deprecation_warnings.py`:

```python
import pytest
import warnings

def test_cone_deprecated_params():
    """Test that old cone parameters trigger deprecation warning."""
    with pytest.warns(DeprecationWarning, match="radius_bottom.*deprecated"):
        # Parse YAML with old cone syntax
        pass

def test_pattern_deprecated_spacing():
    """Test that old pattern spacing triggers deprecation warning."""
    with pytest.warns(DeprecationWarning, match="scalar.*direction.*deprecated"):
        # Parse YAML with old pattern syntax
        pass

# Similar tests for other deprecation warnings
```

---

## Migration Tool

The `fix_pattern_api.py` script already exists for pattern migration. Consider creating:
- `fix_cone_api.py` - Migrate cone parameters
- `fix_translate_api.py` - Migrate translate offsets
- `fix_export_api.py` - Migrate export format

Or combine into a single `migrate_v31x.py` tool that handles all four patterns.

---

## Documentation Updates

Once implemented, update:
- [x] MIGRATION_GUIDE_V3.md - Already documents the changes
- [ ] CHANGELOG.md - Add note about deprecation warnings in next release
- [ ] README.md - Mention deprecation warnings if relevant
- [ ] TESTING_GUIDE.md - How to test for deprecation warnings

---

## Future: Removal Timeline

**Deprecation warnings** (this release):
- Warn users but still support old syntax
- Give clear migration path

**Removal** (v3.2 or v4.0):
- Remove backward compatibility code
- Update validation to reject old syntax
- Keep deprecation notice in CHANGELOG

---

## Benefits

1. **User-friendly**: Clear messages tell users what to change
2. **Gradual migration**: Old code still works, just with warnings
3. **Documentation**: Warnings link to migration guide
4. **Future cleanup**: Makes eventual removal cleaner

---

## Notes

- Use Python's `warnings` module, not `logging.warning()`
- Set `stacklevel=2` to show warning at caller location
- Test with `python -W error::DeprecationWarning` to treat as errors (CI option)
- Keep backward compatibility logic simple - just map old → new

---

**Status**: Implementation plan documented, ready for future work
**Effort**: ~2-4 hours to implement + test all four patterns
**Priority**: Medium (improves UX, but not critical since examples are fixed)
