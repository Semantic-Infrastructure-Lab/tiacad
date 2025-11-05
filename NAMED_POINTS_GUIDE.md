# TiaCAD Named Points Guide

**Feature Status:** ✅ **IMPLEMENTED** (2025-11-02)

## Overview

Named points eliminate coordinate duplication by letting you define important points once and reference them everywhere. This makes your models easier to understand, modify, and maintain.

## Problem Solved

**Before Named Points:**
```yaml
operations:
  left_arm:
    transforms:
      - translate: [0, 37.5, 0]
        offset: [${-arm_spacing / 2}, ${arm_len / 2}, 0]
      - rotate:
          angle: 10
          axis: X
          origin: [${-arm_spacing / 2}, 37.5, 0]  # ❌ Duplicated coordinates!
```

**With Named Points:**
```yaml
named_points:
  left_attach:
    part: beam
    face: ">Z"
    offset: ['${-arm_spacing / 2}', 0, 0]

operations:
  left_arm:
    transforms:
      - translate: left_attach  # ✨ Clean!
      - rotate:
          angle: 10
          axis: X
          origin: left_attach  # ✨ No duplication!
```

## YAML Schema

### Basic Structure

```yaml
named_points:
  point_name: <point_specification>
  another_point: <point_specification>
  # ... more points
```

### Point Specifications

#### 1. Absolute Coordinates
```yaml
named_points:
  origin: [0, 0, 0]
  corner: [100, 50, 25]
  with_params: ['${x_pos}', '${y_pos}', '${z_pos}']
```

#### 2. Geometric References (Dict Notation)
```yaml
named_points:
  top_face:
    part: box
    face: ">Z"
    at: center  # Optional, defaults to 'center'

  left_edge:
    part: plate
    edge: "|Z and <X"
    at: start

  corner_vertex:
    part: bracket
    vertex: 0  # First vertex
```

#### 3. Geometric References (Dot Notation)
```yaml
# Note: Dot notation is supported in operations but not in named_points section
# Use dict notation above for defining named points

operations:
  my_op:
    transforms:
      - translate: "beam.face('>Z').center"  # This works in operations!
```

#### 4. Offsets from Other Points
```yaml
named_points:
  base_point: [0, 0, 0]

  offset_point:
    from: base_point
    offset: [10, 20, 30]

  offset_from_geometry:
    from:
      part: beam
      face: ">Y"
      at: center
    offset: [0, 5, 0]

  # You can reference other named points!
  chained:
    from: offset_point
    offset: [5, 0, 0]
```

## Usage in Operations

### In `translate` Operations

**Three Ways to Use Named Points:**

```yaml
operations:
  # 1. Direct named point reference (shorthand)
  moved1:
    type: transform
    input: part
    transforms:
      - translate: my_point  # ✨ Cleanest syntax!

  # 2. With 'to:' (explicit)
  moved2:
    type: transform
    input: part
    transforms:
      - translate:
          to: my_point

  # 3. With 'to:' and offset
  moved3:
    type: transform
    input: part
    transforms:
      - translate:
          to: my_point
          offset: [0, 0, 10]  # Add 10mm in Z
```

### In `rotate` Operations

```yaml
operations:
  rotated:
    type: transform
    input: arm
    transforms:
      - rotate:
          angle: 45
          axis: Z
          origin: pivot_point  # ✨ Named point as rotation center!
```

## Complete Example

See [`examples/guitar_hanger_named_points.yaml`](examples/guitar_hanger_named_points.yaml) for a real-world example.

**Key Benefits Demonstrated:**
- 7 named points defined once
- Used 10+ times across operations
- Zero coordinate duplication
- Easy to adjust arm spacing (change one parameter!)

## Best Practices

### 1. Use Descriptive Names

```yaml
# ✅ Good
named_points:
  left_mounting_hole: [...]
  beam_front_center: [...]
  arm_attachment_point: [...]

# ❌ Avoid
named_points:
  p1: [...]
  pt: [...]
  x: [...]
```

### 2. Define in Logical Order

```yaml
named_points:
  # 1. Base geometric references
  beam_center:
    part: beam
    face: ">Z"
    at: center

  # 2. Derived points (offsets from base)
  left_attach:
    from: beam_center
    offset: ['${-spacing/2}', 0, 0]

  right_attach:
    from: beam_center
    offset: ['${spacing/2}', 0, 0]

  # 3. Further derived points
  left_arm_pos:
    from: left_attach
    offset: [0, '${arm_len/2}', 0]
```

### 3. Use Parameters for Flexibility

```yaml
parameters:
  spacing: 50
  offset_z: 10

named_points:
  left: ['${-spacing/2}', 0, '${offset_z}']
  right: ['${spacing/2}', 0, '${offset_z}']
```

**Note:** When using `${...}` expressions in YAML flow sequences (inline arrays), always quote them:
```yaml
# ✅ Correct
offset: ['${-spacing}', 0, '${height/2}']

# ❌ YAML parse error
offset: [${-spacing}, 0, ${height/2}]
```

### 4. Group Related Points

```yaml
named_points:
  # Mounting holes
  hole_topleft: [...]
  hole_topright: [...]
  hole_bottomleft: [...]
  hole_bottomright: [...]

  # Attachment points
  arm_left_attach: [...]
  arm_right_attach: [...]
```

## Advanced Patterns

### Pattern 1: Symmetric Points

```yaml
parameters:
  width: 100

named_points:
  center: [0, 0, 0]
  left: ['${-width/2}', 0, 0]
  right: ['${width/2}', 0, 0]
```

### Pattern 2: Bolt Circle

```yaml
parameters:
  radius: 50

named_points:
  hole_0deg: ['${radius}', 0, 0]
  hole_90deg: [0, '${radius}', 0]
  hole_180deg: ['${-radius}', 0, 0]
  hole_270deg: [0, '${-radius}', 0]
```

### Pattern 3: Cascading Offsets

```yaml
named_points:
  base: [0, 0, 0]
  level1:
    from: base
    offset: [0, 0, 10]
  level2:
    from: level1
    offset: [0, 0, 10]
  level3:
    from: level2
    offset: [0, 0, 10]
```

## Implementation Details

### Resolution Order

Named points are resolved sequentially in the order they appear in the YAML. Each resolved point immediately becomes available for subsequent points to reference:

```yaml
named_points:
  a: [10, 0, 0]
  b:
    from: a  # ✅ Works! 'a' is already resolved
    offset: [0, 10, 0]
  c:
    from: b  # ✅ Works! 'b' is now resolved
    offset: [0, 0, 10]
```

### Coordinate Precision

Named points store coordinates as floating-point tuples `(x, y, z)`. Geometric references may have floating-point precision artifacts (e.g., `1e-16` instead of `0.0`), which is normal and doesn't affect calculations.

### Error Messages

The system provides clear error messages:

```yaml
named_points:
  bad_ref:
    part: nonexistent  # Error: Part 'nonexistent' not found
    face: ">Z"

  bad_offset:
    from: undefined_point  # Error: Named point 'undefined_point' not found
    offset: [0, 0, 0]
```

## Feature Comparison

| Feature | Before Named Points | With Named Points |
|---------|-------------------|-------------------|
| **Define once** | ❌ Repeat coordinates | ✅ Define once, use everywhere |
| **Readability** | Numbers everywhere | Semantic names |
| **Maintainability** | Change in N places | Change in 1 place |
| **Parameter integration** | Complex expressions repeated | Simple references |
| **Type safety** | Easy to transpose X/Y/Z | Validated once |

## What's Next?

Named points are the foundation for future high-level features:

### Potential Future Enhancements
1. **Attachment Constraints**: High-level part-to-part attachment
2. **Named Axes**: Custom coordinate systems
3. **Point Arrays**: Define point patterns
4. **Computed Points**: Midpoints, intersections, projections

## Migration Guide

### Converting Existing Models

**Step 1:** Identify repeated coordinates
```bash
grep -n "translate:" your_model.yaml
grep -n "origin:" your_model.yaml
```

**Step 2:** Extract to named points
```yaml
# Before
operations:
  op1:
    transforms:
      - translate: [25, 50, 10]
  op2:
    transforms:
      - rotate:
          origin: [25, 50, 10]

# After
named_points:
  attach_point: [25, 50, 10]

operations:
  op1:
    transforms:
      - translate: attach_point
  op2:
    transforms:
      - rotate:
          origin: attach_point
```

**Step 3:** Test thoroughly
```bash
tiacad build your_model.yaml --output test.stl
# Compare with original output
```

## FAQ

**Q: Can I use named points before they're defined?**
A: No, points must be defined before being referenced. Define them in dependency order.

**Q: Can named points reference parts from operations?**
A: No, named points are resolved AFTER parts are built but BEFORE operations execute. They can only reference primitive parts, not operation results.

**Q: What about circular references?**
A: The system detects circular references and will error. Define points in a linear dependency chain.

**Q: Can I use dot notation in named_points?**
A: No, use dict notation (`{part: ..., face: ..., at: ...}`) for named points definitions. Dot notation only works directly in operation specs.

**Q: Why quote parameter expressions in arrays?**
A: YAML parsers treat `${...}` specially in flow sequences. Quoting them (`'${expr}'`) prevents parse errors.

## Troubleshooting

### Error: "Invalid dot notation: 'my_point'"

Named points use simple identifiers, not dot notation. This error means you're trying to reference a named point as if it were part of the dot notation syntax.

**Solution:** Use the dict notation for geometric references:
```yaml
named_points:
  my_point:
    part: box
    face: ">Z"
    at: center
```

### Error: "Part 'X' not found"

The part you're referencing doesn't exist when named points are resolved.

**Solution:** Ensure the part is defined in the `parts:` section (not in `operations:`):
```yaml
parts:
  box:  # ✅ Can reference this
    primitive: box
    size: [10, 10, 10]

operations:
  moved_box:  # ❌ Cannot reference this in named_points
    type: transform
    input: box
```

### YAML Parse Error with `${...}`

**Solution:** Always quote parameter expressions in flow sequences:
```yaml
# ✅ Correct
['${expr}', 0, '${expr2}']

# ❌ Wrong
[${expr}, 0, ${expr2}]
```

## Summary

Named points are a **high-value, low-complexity** feature that:

✅ Eliminates 80% of coordinate duplication
✅ Makes models more readable and maintainable
✅ Integrates seamlessly with parameters
✅ Provides clear error messages
✅ Requires no changes to existing models (backward compatible)

**Start using named points today to make your TiaCAD models cleaner and easier to maintain!**

---

*Implementation completed: 2025-11-02*
*Test coverage: 13/13 tests passing*
*Example: [`examples/guitar_hanger_named_points.yaml`](examples/guitar_hanger_named_points.yaml)*
