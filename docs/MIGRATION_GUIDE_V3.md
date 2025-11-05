# TiaCAD v3.0 Migration Guide

**Upgrading from v0.3.0 to v3.0**

This guide helps you migrate your existing TiaCAD YAML files from v0.3.0 to the new v3.0 architecture.

---

## Overview of Changes

v3.0 introduces a **unified spatial reference system** that replaces the old `named_points:` section with a more powerful `references:` section. This new system:

- Supports not just points, but also faces, edges, and axes
- Provides auto-generated part-local references (e.g., `base.face_top`)
- Enables local frame offsets for more intuitive positioning
- Maintains full orientation information (normals, tangents) for intelligent placement

---

## Breaking Changes

### 1. YAML Syntax Changes

#### Old Syntax (v0.3.0)
```yaml
named_points:
  target: [10, 20, 30]
  top_center:
    part: base
    face: ">Z"
    at: center
```

#### New Syntax (v3.0)
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

### 2. Key Terminology Changes

| v0.3.0 | v3.0 | Notes |
|--------|------|-------|
| `named_points:` | `references:` | New top-level section name |
| `face: ">Z"` | `selector: ">Z"` | Face/edge selectors now use `selector` key |
| Point-only | Points, faces, edges, axes | Support for multiple reference types |

### 3. API Changes (Python Code)

| v0.3.0 | v3.0 | Notes |
|--------|------|-------|
| `PointResolver` | `SpatialResolver` | Class renamed |
| Returns `Tuple[float, float, float]` | Returns `SpatialRef` dataclass | Includes position + orientation |
| No frame support | `Frame` dataclass available | Local coordinate systems |

---

## Migration Steps

### Step 1: Rename `named_points` to `references`

**Before:**
```yaml
named_points:
  mount_point: [10, 0, 20]
```

**After:**
```yaml
references:
  mount_point:
    type: point
    value: [10, 0, 20]
```

### Step 2: Add `type` and Update Structure

All references now need an explicit `type` field:

**Point References:**
```yaml
# Old
named_points:
  corner: [100, 100, 0]

# New
references:
  corner:
    type: point
    value: [100, 100, 0]
```

**Face References:**
```yaml
# Old
named_points:
  top_face:
    part: base
    face: ">Z"
    at: center

# New
references:
  top_face:
    type: face
    part: base
    selector: ">Z"
    at: center
```

**Edge References:**
```yaml
# Old - Not supported in v0.3.0

# New
references:
  front_edge:
    type: edge
    part: base
    selector: ">Z and >Y"
    at: midpoint
```

### Step 3: Use Auto-References (New in v3.0)

Instead of manually defining common references, use auto-generated ones:

**Before (v0.3.0):**
```yaml
named_points:
  base_top:
    part: base
    face: ">Z"
    at: center

parts:
  platform:
    primitive: box
    parameters:
      width: 50
      height: 10
      depth: 50
    translate:
      to: base_top
```

**After (v3.0) - Using Auto-References:**
```yaml
# No need to define references - use auto-generated ones!

parts:
  platform:
    primitive: box
    parameters:
      width: 50
      height: 10
      depth: 50
    translate:
      to: base.face_top  # Auto-generated reference
```

### Step 4: Update Offset Syntax

Offsets in v3.0 use a more explicit structure:

**Before (v0.3.0):**
```yaml
# Offsets were applied in world coordinates
translate:
  to: [0, 0, 10]
  offset: [5, 0, 0]
```

**After (v3.0):**
```yaml
# Offsets follow the reference's local frame
translate:
  to:
    type: point
    from: base.face_top
    offset: [5, 0, 2]  # Offset in face's local coordinate system
```

---

## Auto-Generated References

v3.0 automatically provides these references for every part:

### Universal Auto-References

Available for all primitives (box, cylinder, sphere, cone):

| Reference | Description | Type |
|-----------|-------------|------|
| `{part}.center` | Bounding box center | point |
| `{part}.origin` | Part origin | point |
| `{part}.face_top` | Top face (>Z) | face |
| `{part}.face_bottom` | Bottom face (<Z) | face |
| `{part}.face_left` | Left face (<X) | face |
| `{part}.face_right` | Right face (>X) | face |
| `{part}.face_front` | Front face (>Y) | face |
| `{part}.face_back` | Back face (<Y) | face |
| `{part}.axis_x` | X-axis through center | axis |
| `{part}.axis_y` | Y-axis through center | axis |
| `{part}.axis_z` | Z-axis through center | axis |

### Example Usage

```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 20, depth: 100}

  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 50}
    translate:
      to: base.face_top  # Auto-reference - no definition needed!

  cap:
    primitive: box
    parameters: {width: 15, height: 5, depth: 15}
    translate:
      to:
        from: pillar.face_top
        offset: [0, 0, 2]  # 2 units above pillar top
```

---

## Complete Migration Example

### v0.3.0 YAML

```yaml
parameters:
  platform_size: 100
  post_height: 40

named_points:
  base_top:
    part: platform
    face: ">Z"
    at: center

  post_top:
    part: post_1
    face: ">Z"
    at: center

parts:
  platform:
    primitive: box
    parameters:
      width: ${platform_size}
      height: 5
      depth: ${platform_size}

  post_1:
    primitive: cylinder
    parameters:
      radius: 3
      height: ${post_height}
    translate:
      to: base_top
      offset: [-30, -30, 0]

  top_platform:
    primitive: box
    parameters:
      width: 80
      height: 5
      depth: 80
    translate:
      to: post_top
      offset: [0, 0, 5]

export:
  - filename: assembly.step
    parts: [platform, post_1, top_platform]
```

### v3.0 YAML (Migrated)

```yaml
parameters:
  platform_size: 100
  post_height: 40

# No references section needed - using auto-references!

parts:
  platform:
    primitive: box
    parameters:
      width: ${platform_size}
      height: 5
      depth: ${platform_size}

  post_1:
    primitive: cylinder
    parameters:
      radius: 3
      height: ${post_height}
    translate:
      to:
        type: point
        from: platform.face_top  # Auto-reference!
        offset: [-30, -30, 0]

  top_platform:
    primitive: box
    parameters:
      width: 80
      height: 5
      depth: 80
    translate:
      to:
        type: point
        from: post_1.face_top  # Auto-reference!
        offset: [0, 0, 5]

export:
  - filename: assembly.step
    parts: [platform, post_1, top_platform]
```

**Benefits:**
- No manual reference definitions needed
- More readable and maintainable
- Offsets follow local coordinate systems
- Full orientation support for intelligent placement

---

## Common Migration Patterns

### Pattern 1: Simple Point References

```yaml
# v0.3.0
named_points:
  corner: [50, 50, 0]

# v3.0 - Option 1: Explicit reference
references:
  corner:
    type: point
    value: [50, 50, 0]

# v3.0 - Option 2: Inline usage
parts:
  bracket:
    translate:
      to: [50, 50, 0]  # Direct coordinate still works!
```

### Pattern 2: Face-Based Positioning

```yaml
# v0.3.0
named_points:
  attach_point:
    part: base
    face: ">Y"
    at: center

parts:
  arm:
    translate:
      to: attach_point

# v3.0 - Using auto-references
parts:
  arm:
    translate:
      to: base.face_front  # face_front is auto-generated >Y face
```

### Pattern 3: Offset Positioning

```yaml
# v0.3.0
named_points:
  raised_point:
    part: platform
    face: ">Z"
    at: center

parts:
  elevated_part:
    translate:
      to: raised_point
      offset: [0, 0, 10]  # World coordinate offset

# v3.0 - Local frame offset
parts:
  elevated_part:
    translate:
      to:
        from: platform.face_top
        offset: [0, 0, 10]  # Offset in face's local frame
```

---

## Backwards Compatibility

**Important:** v3.0 is a **breaking release**. Old v0.3.0 YAML files will NOT work without migration.

To maintain both versions during transition:
1. Keep v0.3.0 files in a `legacy/` directory
2. Migrate files incrementally to v3.0 syntax
3. Use version control to track changes
4. Test migrated files thoroughly

---

## Testing Your Migration

After migrating your YAML files:

1. **Syntax Validation:**
   ```bash
   tiacad validate my_design.yaml
   ```

2. **Visual Inspection:**
   ```bash
   tiacad render my_design.yaml --output preview.png
   ```

3. **Export Test:**
   ```bash
   tiacad build my_design.yaml
   ```

4. **Compare Outputs:**
   - Export from v0.3.0 to STEP
   - Export from v3.0 to STEP
   - Compare geometry in CAD viewer

---

## Need Help?

- **Examples:** See `examples/` directory for v3.0 YAML files
- **Documentation:** See `docs/V3_IMPLEMENTATION_STATUS.md` for feature details
- **Issues:** Report migration problems at https://github.com/scottsen/tiacad/issues

---

## Summary of Benefits

v3.0's unified spatial reference system provides:

✅ **Simpler YAML** - Auto-references eliminate boilerplate
✅ **More Expressive** - Face, edge, and axis references
✅ **Intelligent Positioning** - Local frame offsets
✅ **Better Errors** - Clear validation messages
✅ **Future-Proof** - Foundation for constraint-based design

The migration effort is worthwhile for these long-term benefits!
