# TiaCAD YAML Reference Guide

**Version:** Current
**Status:** Active syntax reference

---

## Table of Contents

1. [Document Structure](#document-structure)
2. [Metadata](#metadata)
3. [Imports (Component System)](#imports-component-system)
4. [Parameters](#parameters)
4. [References (v3.0)](#references-v30)
   - [Auto-Generated References](#auto-generated-references)
   - [Named References](#named-references)
   - [Reference Types](#reference-types)
   - [Using References](#using-references)
5. [Parts](#parts)
6. [Operations](#operations)
   - [Transform Operations](#transform-operations)
   - [Boolean Operations](#boolean-operations)
   - [Pattern Operations](#pattern-operations)
   - [Finishing Operations](#finishing-operations)
   - [Sketch + Revolve](#sketch--revolve-lathed--rotationally-symmetric-shapes)
7. [Export](#export)
8. [Contracts (expect:)](#contracts-expect)
9. [Complete Examples](#complete-examples)

---

## Document Structure

Every TiaCAD YAML file follows this structure:

```yaml
imports:            # Optional: component imports (local, stdlib, GitHub)
  - path: tiacad://std/hardware/m3_screw
    as: m3
  - path: github:user/repo/path/to/component.yaml
    as: my_part
  - path: ./local_component.yaml
    as: local_part

metadata:           # Optional: document information
  name: My Design
  description: ...
  version: 1.0

parameters:         # Optional: parametric values
  width: 100
  height: 50

references:         # Optional (v3.0): named spatial references
  mount_point:      # Note: Many references are auto-generated!
    type: face
    part: base
    selector: ">Z"

parts:             # Required (unless the file imports components): define primitive parts
  part_name:
    primitive: box
    size: [100, 50, 10]

operations:        # Optional: transform, boolean, pattern, finish
  operation_name:
    type: boolean
    operation: union
    inputs: [...]

export:            # Optional: export defaults
  default_part: final_part
```

---

## Metadata

Optional section for documentation and version tracking.

```yaml
metadata:
  name: "My Design"              # Design name
  description: "What it does"    # Brief description
  version: "1.0"                 # Version number
  author: "Your Name"            # Who created it
  created: "2025-10-25"          # Creation date
  phase: 2                       # TiaCAD phase used

  # NEW in v3.2: Optional type and composition fields
  type: assembly                 # Document purpose (see below)
  composition: reference-based   # Makes mental model explicit
```

All fields are optional and for documentation only.

### Enhanced Metadata Fields (v3.2+)

**type** - Declares the document purpose:
- `part` - Single part design
- `assembly` - Multiple parts combined
- `model` - Complete model/design
- `mechanism` - Moving parts assembly
- `fixture` - Jig or mounting fixture

**composition** - Makes the mental model explicit:
- `reference-based` - TiaCAD's composition model (recommended)

These fields help readers immediately understand the document's purpose and design approach.

---

## Imports (Component System)

The `imports:` section lets you reuse YAML components from three sources.
Each entry requires a `path:` and `as:` (namespace) key.

### Stdlib (Bundled Hardware)

```yaml
imports:
  - path: tiacad://std/hardware/m3_screw
    as: m3

  - path: tiacad://std/hardware/m3_nut
    as: m3_nut

  - path: tiacad://std/hardware/m3_washer
    as: washer

  - path: tiacad://std/hardware/m3_standoff
    as: standoff
    parameters:
      height: 10          # override default height

  - path: tiacad://std/hardware/m4_screw
    as: m4
  - path: tiacad://std/hardware/m5_screw
    as: m5
  - path: tiacad://std/hardware/m6_bolt
    as: m6
  - path: tiacad://std/hardware/m4_nut
    as: m4_nut
  - path: tiacad://std/hardware/m5_nut
    as: m5_nut
  - path: tiacad://std/hardware/m6_nut
    as: m6_nut
  - path: tiacad://std/hardware/mounting_bracket
    as: bracket
```

These resolve to `tiacad_core/stdlib/hardware/*.yaml` — no install needed.

### GitHub (Remote, Cached)

```yaml
imports:
  - path: github:scottsen/guitar-hangers/components/hook.yaml
    as: hook

  - path: github:org/repo/path/to/component.yaml
    as: my_part
```

Fetched from `raw.githubusercontent.com/user/repo/{branch}/...`, cached to
`~/.tiacad/cache/github/{user}/{repo}/{branch}/...`. Default branch is `main`;
override with a trailing `@branch` suffix on the file path, e.g.
`github:user/repo/file.yaml@dev` (branch names may contain slashes).

### Local Files

```yaml
imports:
  - path: ./bracket.yaml
    as: bracket

  - path: ../shared/fasteners/m3_standoff.yaml
    as: standoff
```

### Parameter Overrides

Any parameter defined in the component can be overridden at import time:

```yaml
imports:
  - path: tiacad://std/hardware/m3_screw
    as: m3
    parameters:
      length: 20          # override the default length
```

### Using Imported Parts

After importing, access parts as `{namespace}.{part_name}`:

```yaml
imports:
  - path: tiacad://std/hardware/m3_screw
    as: m3
    parameters:
      length: 12

  - path: ./bracket.yaml
    as: bracket

operations:
  place_screw:
    type: transform
    input: m3.shaft        # namespace.part_name
    transforms:
      - translate: [10, 0, 5]

  place_bracket:
    type: transform
    input: bracket.base    # namespace.part_name
    transforms:
      - translate: [0, 0, 0]
```

---

## Parameters

Define reusable values with expressions.

### Basic Parameters

```yaml
parameters:
  width: 100
  height: 50
  thickness: 8
```

### Expression Parameters

Parameters can reference other parameters using `${...}` syntax:

```yaml
parameters:
  base_width: 100
  total_width: '${base_width * 2}'
  half_width: '${base_width / 2}'
  hole_radius: '${bolt_diameter / 2}'
```

### Supported Operators

- Addition: `${a + b}`
- Subtraction: `${a - b}`
- Multiplication: `${a * b}`
- Division: `${a / b}`
- Exponentiation: `${a ** b}`
- Modulo: `${a % b}`

### Units

All lengths are millimetres internally. To write a dimension in other units, give it a unit
suffix: `mm`, `cm`, `in` or `ft`. It is converted to mm when parameters are resolved.

```yaml
parameters:
  drawer_len: 9.5in                  # whole value: 241.3
  gap: 0.016in
  inner: '${drawer_len - 2 * 0.1in}' # inside ${...}: no space between number and unit
  tab: '${3mm + 1in}'                # units can be mixed
```

Unit suffixes work in `parameters:` values, inside `${...}` expressions, and with
`--set NAME=9.5in`. They are not converted in other fields (a bare `9.5in` written directly in a
part's `parameters:` or in text content stays a string); put the value in a top-level parameter
and reference it. A bare number
is always mm. Inside `${...}` the number and unit must touch (`9.5in`, not `9.5 in`).

### Functions

Available inside `${...}`:

| Function | Result |
|---|---|
| `min(a, b, ...)`, `max(a, b, ...)`, `abs(x)` | as in Python |
| `sqrt(x)`, `pow(x, y)` | square root, power |
| `round(x)`, `floor(x)`, `ceil(x)` | rounding |
| `sin(deg)`, `cos(deg)`, `tan(deg)` | trig of an angle in **degrees** |
| `asin(x)`, `acos(x)`, `atan(x)`, `atan2(y, x)` | inverse trig, result in **degrees** |

`pi` is also available as a constant (`${2 * pi * r}`).

### Angles

Every angle in TiaCAD is in **degrees**: `rotate: {angle: 45}`, `start_angle`, and the arguments
and results of the trig functions above. So `tan(20)` is 0.364 (the slope of a 20 degree ramp),
and `atan(0.364)` is about 20.

A `rad` suffix converts a radian value to degrees, the same way `in` converts to mm. It works on a
whole parameter value, inside `${...}` (number and `rad` must touch: `0.35rad`), with `--set`, and
as a `rotate` angle:

```yaml
parameters:
  ramp_deg: 20
  ramp_slope: '${tan(ramp_deg)}'        # rise / run
  rise: '${slot_l * ramp_slope}'
  tilt: 0.35rad                         # 20.05 (degrees)
  half_turn: '${pi * 1rad}'             # 180.0 (degrees)
```

Pass an angle override the same way: `--set ramp_deg=15`.

**Changed 2026-10-17:** `sin`, `cos` and `tan` used to take radians (undocumented). They now take
degrees. A model that relied on the old behavior should write `sin(0.5rad)` or `sin(x * 1rad)`.

### Quoting `${...}` in inline YAML

Inside an inline mapping or list (`{...}` / `[...]`), a bare `${w}` is invalid YAML because
`{` opens a flow mapping, and the parse error never mentions `${}`. Quote every template:

```yaml
size: ['${base_width}', 5, 5]                                # ✅
origin: ['${wall}', 0, '${floor}']                           # ✅
size: [${base_width}, 5, 5]                                  # ❌ "expected ',' or ']'"
```

In block style (one key or `- item` per line) the quotes are optional but harmless; the
examples quote them consistently.

### Using Parameters

Reference parameters in any numeric field:

```yaml
parts:
  plate:
    primitive: box
    size: ['${width}', '${depth}', '${thickness}']
```

---

## References (Spatial Anchors) - v3.0

**What are references?** Spatial references (we call them **anchors**) are marked positions in 3D space where parts can be positioned or attached - like marking spots on a workbench. Think of `base.face_top` as "the anchor at the top of the base".

**New in v3.0:** TiaCAD introduces a unified spatial reference system that replaces the old `named_points:` section. This system supports not just points, but also faces, edges, and axes with full orientation information (position + direction).

**Key concept**: Instead of calculating coordinates manually, you position parts using anchors: `translate: to: base.face_top` instead of `translate: [50, 25, 10]`.

**Visual Guides:**
- [Auto-Reference Visualization](../architecture/diagrams/auto-reference-visualization.md) - See all auto-generated anchors
- [Local Frame Offsets](../architecture/diagrams/local-frame-offsets.md) - Understand how offsets work
- [Reference Chain Dependencies](../architecture/diagrams/reference-chain-dependencies.md) - Learn how parts reference each other

### Auto-Generated References

Every part automatically provides these references **without explicit definition**:

#### Universal auto-generated anchors (All Primitives)

Available for all parts (box, cylinder, sphere, cone):

| Reference | Description | Type | Example |
|-----------|-------------|------|---------|
| `{part}.center` | Bounding box center | point | `base.center` |
| `{part}.origin` | Part origin | point | `pillar.origin` |
| `{part}.face_top` | Top face (>Z) | face | `platform.face_top` |
| `{part}.face_bottom` | Bottom face (<Z) | face | `platform.face_bottom` |
| `{part}.face_left` | Left face (<X) | face | `wall.face_left` |
| `{part}.face_right` | Right face (>X) | face | `wall.face_right` |
| `{part}.face_front` | Front face (>Y) | face | `panel.face_front` |
| `{part}.face_back` | Back face (<Y) | face | `panel.face_back` |
| `{part}.axis_x` | X-axis through center | axis | `shaft.axis_x` |
| `{part}.axis_y` | Y-axis through center | axis | `shaft.axis_y` |
| `{part}.axis_z` | Z-axis through center | axis | `shaft.axis_z` |

**Benefits:**
- No need to define common references manually
- Consistent naming across all parts
- Works with transforms and offsets
- Full orientation support (normals, tangents)

**Example Usage:**

```yaml
parts:
  platform:
    primitive: box
    size: [100, 100, 10]

  pillar:
    primitive: cylinder
    parameters:
      radius: 5
      height: 50
    translate:
      to: platform.face_top  # auto-generated anchor - no definition needed!

  cap:
    primitive: box
    size: [15, 15, 5]
    translate:
      to:
        from: pillar.face_top  # auto-generated anchor with offset
        offset: [0, 0, 2]      # 2 units above pillar
```

### Named References (Custom Anchors)

You can define custom anchors in the `references:` section when auto-generated ones don't suffice. Think of this as marking additional attachment points beyond the automatic ones.

**New in v3.2:** You can use `anchors:` as a user-friendly alias for `references:`. Both work identically!

```yaml
# Option 1: Using 'references:' (canonical, all versions)
references:
  mount_surface:
    type: face
    part: base
    selector: ">Z and <X"
    at: center

  hinge_axis:
    type: axis
    from: [0, 0, 0]
    to: [0, 0, 100]

  corner_point:
    type: point
    value: [50, 50, 0]

# Option 2: Using 'anchors:' (v3.2+, more intuitive)
anchors:
  mount_surface:
    type: face
    part: base
    selector: ">Z and <X"
    at: center

  hinge_axis:
    type: axis
    from: [0, 0, 0]
    to: [0, 0, 100]

  corner_point:
    type: point
    value: [50, 50, 0]
```

**Note:** Use either `references:` or `anchors:`, not both. They're aliases for the same thing!

### Reference Types

v3.0 supports four reference types:

#### 1. Point References

Simple 3D coordinates:

```yaml
references:
  corner:
    type: point
    value: [100, 50, 0]

  # Or inline
parts:
  bracket:
    translate:
      to: [100, 50, 0]  # Direct coordinate array
```

#### 2. Face References

Face with position + normal vector:

```yaml
references:
  mount_face:
    type: face
    part: base_plate
    selector: ">Z"     # Face selector (CadQuery syntax)
    at: center         # Optional: center (default), min, max

  # Using auto-generated face
parts:
  bracket:
    translate:
      to: base_plate.face_top  # Auto-generated face reference
```

**Face selectors:**
- `">Z"` - faces pointing in +Z direction
- `"<X"` - faces pointing in -X direction
- `">Z and <X"` - faces matching both conditions
- See CadQuery documentation for full selector syntax

#### 3. Edge References

Edge with position + tangent vector:

```yaml
references:
  rail_edge:
    type: edge
    part: frame
    selector: ">X and >Z"  # Edge parallel to X, on +Z face
    at: midpoint           # Optional: midpoint (default), start, end
```

#### 4. Axis References

Axis defined by direction vector:

```yaml
references:
  rotation_axis:
    type: axis
    from: [0, 0, 0]
    to: [0, 1, 0]       # Y-axis

  # Or use auto-generated axis
operations:
  rotated:
    type: transform
    input: gear
    transforms:
      - rotate:
          angle: 90
          around: shaft.axis_z  # Auto-generated axis
```

### Using References

References can be used anywhere a spatial location is needed:

#### In Translate Operations

```yaml
parts:
  mounted_part:
    translate:
      to: base.face_top  # Position at reference

  offset_part:
    translate:
      to:
        from: base.face_top
        offset: [0, 0, 5]  # Offset in face's local frame
```

#### In Rotate Operations

```yaml
operations:
  rotated:
    type: transform
    input: part
    transforms:
      - rotate:
          angle: 45
          around: base.face_top  # Rotate around face normal
```

#### Local Frame Offsets

Offsets follow the reference's local local frame:

```yaml
parts:
  bracket:
    translate:
      to:
        from: wall.face_front  # Face on +Y side
        offset: [5, 0, 10]     # X=5 right, Y=0 (perpendicular), Z=10 up
```

**Local frame orientation:**
- Face: Normal as Z-axis, tangent as X/Y
- Edge: Tangent as X-axis, normal as Z
- Axis: Direction as Z-axis
- Point: World local frame

---

## Parts

Parts are the basic building blocks. Each part starts from a primitive shape.

### Box Primitive

```yaml
parts:
  my_box:
    primitive: box
    size: [100, 30, 20]
    origin: center                # center, corner, or [x,y,z]
```

`size` is the extent along **X, Y, Z**, in that order (`+Z` is up, so for a flat plate the thickness is
the third value). A single number is a cube: `size: 20` is `[20, 20, 20]`. Values may be numbers,
`'${...}'` templates, or unit literals (`[9.5in, 2cm, 3]`).

> The old `width` / `depth` / `height` keys are gone (`width` → x, `depth` → y, `height` → z). A model that
> still uses them fails with a message saying so; `python3 scripts/migrations/box_size.py FILE...`
> rewrites them for you.

**Origin modes:** one vocabulary for every primitive, see [Origin Modes](#origin-modes). For a box,
`center` (default) puts the middle at (0, 0, 0), `base` the middle of the bottom face, `corner` the min
corner, and `[x, y, z]` the min corner at that point.

### Cylinder Primitive

```yaml
parts:
  my_cylinder:
    primitive: cylinder
    parameters:
      radius: 10                  # Cylinder radius
      height: 50                  # Cylinder height
    origin: center                # center (default), base (bottom-center at 0,0,0),
                                   # or [x,y,z] (bottom-center at this point instead)
```

### Sphere Primitive

```yaml
parts:
  my_sphere:
    primitive: sphere
    parameters:
      radius: 15                  # Sphere radius
    origin: center                # Usually center
```

### Cone Primitive

```yaml
parts:
  my_cone:
    primitive: cone
    parameters:
      radius1: 20                 # Base radius
      radius2: 5                  # Top radius (0 = pointed cone)
      height: 40                  # Cone height
    origin: center                # center, corner, or [x,y,z]
```

### Polygon Primitive

Regular N-sided extruded prism (hexagonal, triangular, octagonal, etc.).

```yaml
parts:
  hex_nut_body:
    primitive: polygon
    parameters:
      sides: 6              # Number of sides (≥ 3)
      diameter: 8.0         # Diameter of circumscribed circle (vertex to vertex)
      height: 4.0           # Extrusion height
      circumscribed: true   # Optional, default true
```

**Common `sides` values:**
- `3` — triangle
- `4` — square (same as box, but rotation-centered)
- `6` — hex (nuts, standoffs)
- `8` — octagon

**Tip:** For hex nuts and standoffs, use `diameter = AF / cos(30°)` where `AF` is the across-flats dimension.
- M3 nut: AF=5.5mm → `diameter: 6.35`
- M4 nut: AF=7mm → `diameter: 8.08`
- M6 nut: AF=10mm → `diameter: 11.55`

---

### Parts with Transforms

Apply transforms directly to parts:

```yaml
parts:
  rotated_box:
    primitive: box
    size: [10, 30, 20]
    transforms:
      - translate: [50, 0, 0]
      - rotate:
          axis: Z
          angle: 45
          origin: [0, 0, 0]
```

**v3.0 Transform Enhancements:**

You can also use auto-generated anchors and spatial references in transforms:

```yaml
parts:
  mounted_bracket:
    primitive: box
    size: [20, 30, 5]
    translate:
      to: base.face_top  # auto-generated anchor

  aligned_gear:
    primitive: cylinder
    parameters: {radius: 15, height: 10}
    transforms:
      - translate:
          to:
            from: shaft.face_top
            offset: [0, 0, 2]  # Local frame offset
      - rotate:
          angle: 45
          around: shaft.axis_z  # Rotate around axis reference
```

---

## Operations: Understanding the Four Types

Operations in TiaCAD fall into four categories, each with different purposes:

### Operation Categories

| Category | What It Does | Operations | Think Of It As |
|----------|--------------|------------|----------------|
| **1. Positioning** | Change position/orientation (not geometry) | `translate`, `rotate`, `align_to_face` | Moving pieces on a workbench |
| **2. Modifications** | Change geometry itself | `fillet`, `chamfer`, `extrude`, `revolve`, `sweep`, `loft` | Shaping material |
| **3. Combining** | Create relationships between parts | `union`, `difference`, `intersection` | Joining or cutting |
| **4. Replication** | Create multiple copies | `linear_pattern`, `circular_pattern`, `grid_pattern` | Stamping copies |

**Key Insight**: Positioning operations affect WHERE parts are, modification operations affect WHAT they look like, combining operations create NEW geometry, and replication creates COPIES.

**Visual Guide:** See [Operation Categories](../architecture/diagrams/operation-categories.md) for detailed examples and decision tree.

---

## 1. Positioning Operations (Transforms)

**Purpose**: Move, rotate, or scale parts WITHOUT modifying their geometry.

Move, rotate, or scale parts.

```yaml
operations:
  moved_part:
    type: transform
    input: original_part
    transforms:
      - translate: [x, y, z]      # Move part
      - rotate:                    # Rotate part
          axis: Z                  # X, Y, Z, or [x,y,z]
          angle: 45                # Degrees (or radians with a suffix: 0.785rad)
          origin: [0, 0, 0]        # Rotation center (REQUIRED)
      - scale: 2.0                 # Uniform scale
      - scale: [2, 1, 1]          # Non-uniform scale
```

**Important:** Transforms apply in order (top to bottom)!

**Rotation origins:**
- `current`: Current part position
- `initial`: Original part position
- `[x, y, z]`: Specific point
- `"part.face('>Z').center"`: Geometric reference (dot notation)

---

### Orientation-Aware Transforms (v3.0+)

New in v3.0: Transform operations that understand both position AND orientation.

#### align_to_face

Align a part to a face reference, matching both position and orientation:

```yaml
operations:
  mounted_bracket:
    type: transform
    input: bracket
    transforms:
      - align_to_face:
          face: base.face_top        # Face reference (auto-generated or named)
          orientation: normal        # Align part's -Z to face normal
          offset: 5                  # Distance from face (optional, default: 0)
```

**How it works:**
1. Rotates part so its -Z axis aligns with the face normal
2. Translates part to face center + offset along normal

**Face references:**
- Named: `mount_surface` (defined in `references:` section)
- Auto-generated: `part.face_top`, `part.face_bottom`, etc.
- Inline: `{type: face, part: base, selector: '>Z'}`

**Common use cases:**
- Mounting brackets to surfaces
- Aligning components to mounting faces
- Positioning parts at specific orientations

#### Frame-Based Rotation

Rotate around spatial references (faces, edges, axes) using the `around:` parameter:

```yaml
operations:
  rotated_gear:
    type: transform
    input: gear
    transforms:
      - rotate:
          angle: 90
          around: shaft_axis        # Spatial reference (not just a point!)
```

**How it works:**
- Uses the reference's orientation as the rotation axis
- Uses the reference's position as the rotation origin

**Supported references:**
- **Face**: Rotates around face normal through face center
- **Edge**: Rotates around edge tangent
- **Axis**: Rotates around axis direction
- **Auto-generated**: `part.face_top`, `part.axis_z`, etc.

**Examples:**

Rotate around a face normal:
```yaml
- rotate:
    angle: 45
    around: base.face_top  # Rotates around normal (Z-axis) through face center
```

Rotate around a custom axis:
```yaml
- rotate:
    angle: 90
    around:
      type: axis
      from: [0, 0, 0]
      to: [0, 1, 0]  # Y-axis
```

Rotate around an edge:
```yaml
- rotate:
    angle: 30
    around:
      type: edge
      part: hinge
      selector: ">X and >Z"
```

**Backward compatibility:**
Traditional rotation (axis + origin) still works:
```yaml
- rotate:
    angle: 90
    axis: Z                 # or [x,y,z]
    origin: [0, 0, 0]       # or 'current' or 'initial'
```

---

---

## 3. Combining Operations (Booleans)

**Purpose**: Create relationships between parts - merge them, subtract one from another, or find their overlap.

Combine parts using set operations.

#### Union (Combine)

```yaml
operations:
  combined:
    type: boolean
    operation: union
    inputs:
      - part1
      - part2
      - part3
```

#### Difference (Subtract)

```yaml
operations:
  plate_with_hole:
    type: boolean
    operation: difference
    base: plate              # Part to subtract from
    subtract:
      - hole1
      - hole2
```

#### Intersection (Overlap)

```yaml
operations:
  overlap:
    type: boolean
    operation: intersection
    inputs:
      - part1
      - part2
```

---

## 4. Replication Operations (Patterns)

**Purpose**: Create multiple copies of a part arranged in a pattern.

Create arrays of parts.

#### Linear Pattern

Repeat along one or more axes:

```yaml
operations:
  linear_array:
    type: pattern
    pattern: linear
    input: bolt_hole
    count: 5                 # Number of copies
    spacing: [20, 0, 0]      # [dx, dy, dz] - X direction spacing
```

**2D Linear Pattern:**

```yaml
operations:
  grid_2d:
    type: pattern
    pattern: linear
    input: hole
    count: [3, 4]           # 3 in X, 4 in Y
    spacing: [20, 25]       # Spacing in each direction
    direction: [X, Y]       # Directions
```

**3D Linear Pattern:**

```yaml
operations:
  grid_3d:
    type: pattern
    pattern: linear
    input: hole
    count: [3, 4, 2]        # X, Y, Z counts
    spacing: [20, 25, 30]   # X, Y, Z spacing
    direction: [X, Y, Z]
```

#### Circular Pattern

Arrange in a circle:

```yaml
operations:
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: 6                # Number of copies
    radius: 50              # Circle radius
    axis: Z                 # Rotation axis (X, Y, Z)
    center: [0, 0, 0]       # Circle center point
    start_angle: 0          # Optional: starting angle (degrees)
```

#### Grid Pattern

2D rectangular grid:

```yaml
operations:
  hole_grid:
    type: pattern
    pattern: grid
    input: hole
    count_x: 4              # Columns
    count_y: 3              # Rows
    spacing_x: 20           # Column spacing
    spacing_y: 25           # Row spacing
```

**Pattern Naming:**
Generated parts are named `{pattern_name}_{index}` (`{pattern_name}_{i}_{j}` for 2D grids).
`bolt_circle` creates `bolt_circle_0`, `bolt_circle_1`, etc.

**Using a pattern's copies:** don't list the copies by name. Refer to the whole pattern with
`{pattern: name}` and the list follows `count` when you change it:

```yaml
    plate_with_holes:
      type: boolean
      operation: difference
      base: plate
      subtract:
        - {pattern: bolt_circle}     # every copy, however many bolt_count makes
```

This works wherever a boolean takes a list (`subtract`, `inputs`). Also accepted: a wildcard
string (`"bolt_circle_*"`) and ranges (`{range: "bolt_circle[0..2]"}` or `{range: "bolt_circle[*]"}`).

---

## 2. Shape Modification Operations (Features)

**Purpose**: Change the geometry itself - add or remove material, round edges, create 3D shapes from 2D sketches.

Add professional finishing to parts.

#### Sketch + Revolve (Lathed / Rotationally-Symmetric Shapes)

The box/cylinder/sphere/cone/polygon primitives (see [Parts](#parts)) aren't the
only way to build geometry — a `sketches:` block defines a 2D profile, and a
`type: revolve` operation spins it around an axis to produce a solid. This is
the way to model anything a machinist would put on a lathe: bottles, barrels,
bosses, tapered/flared bodies — shapes the primitives alone can't express.

```yaml
sketches:
  bottle_profile:
    plane: XZ                     # profile lives in this plane
    origin: [0, 0, 0]
    shapes:
      - type: polygon              # or: rectangle, circle, ellipse, path, text
        points:
          - [0, 0]
          - [${bottle_radius}, 0]
          - [${bottle_radius}, ${bottle_height - neck_height}]
          - [${neck_radius}, ${bottle_height - neck_height}]
          - [${neck_radius}, ${bottle_height}]
          - [0, ${bottle_height}]
        closed: true

operations:
  bottle:
    type: revolve
    sketch: bottle_profile        # required — a name from `sketches:`
    axis: X | Y | Z                # required
    angle: 360                     # optional, degrees, default 360 (full revolve)
    origin: [0, 0, 0]              # optional, revolve axis origin, default [0,0,0]
```

`parts:` is still required even for sketch-only designs — use a small
placeholder part named with a leading underscore (e.g. `_placeholder`, see
`examples/bottle_revolve.yaml`) and export the revolved operation's result
instead. The underscore prefix isn't cosmetic — `UnusedPartsRule` and
`MissingPositionRule` specifically recognize it and skip validation warnings
for it (see `KNOWN_LIMITATIONS.md` #20); a placeholder named anything else
will generate 2 permanent spurious warnings. Full worked examples:
`examples/bottle_revolve.yaml`, `examples/duck_call_insert.yaml` (revolve +
interior bore cut + fillet/chamfer passes — also see `KNOWN_LIMITATIONS.md`
#14 for fillet/chamfer pitfalls on lathed seams).

Beyond `polygon`'s straight-line points, `type: ellipse` (`x_radius`,
`y_radius`, `center`, `rotation`) draws a standalone closed ellipse, and
`type: path` (`start`, `segments`, `closed`) builds a profile from mixed
`line`/`arc` segments — e.g. `segments: [{line: [x,y]}, {arc: {through:
[x,y], to: [x,y]}}]` — for profiles with a genuinely curved edge instead of
a hand-faceted polygon corner. See `examples/curved_vase.yaml`. Note
`spline` and `ellipse_arc` are deliberately *not* supported as `path`
segments — both hit real geometry defects in development; see
`KNOWN_LIMITATIONS.md` #18 and `tiacad_core/sketch.py`'s `Path2D` docstring.

Sketch-based solids aren't limited to revolve — `type: extrude` (straight or
tapered extrusion), `type: sweep` (profile along a path), `type: loft`
(blend between profile sections), and `type: hull` (convex hull of parts) all
build from the same `sketches:` block. See `examples/pipe_sweep.yaml`,
`examples/bracket_with_hole.yaml`, and the sketch-based `*_builder.py` modules
under `tiacad_core/parser/` for their specs.

#### Sketch Planes and Extrude

A sketch's `plane` decides which world axes its 2D coordinates map to, and which
way `type: extrude` pushes the solid. Measured against the builder (a rectangle
`width: 2, height: 4, center: [10, 20]`, `distance: 5`):

| `plane` | sketch x | sketch y | extrudes toward | solid occupies |
|---|---|---|---|---|
| `XY` | world X | world Y | +Z | z from 0 to `distance` |
| `XZ` | world X | world Z | **-Y** | y from `-distance` to 0 |
| `YZ` | world Y | world Z | +X | x from 0 to `distance` |

```yaml
sketches:
  ramp_profile:
    plane: YZ                  # sketch x = world Y, sketch y = world Z
    shapes:
      - {type: polygon, points: [[0, 0], [30, 0], [30, 10]], closed: true}
operations:
  ramp:
    type: extrude
    sketch: ramp_profile
    distance: 20               # solid spans x = 0..20 (add reverse: true for -20..0)
```

- **`origin:` shifts only the in-plane axes.** For `XY` the X and Y components
  apply, for `XZ` X and Z, for `YZ` Y and Z. The component along the plane's
  normal is ignored, so the solid always starts at 0 on that axis. Move it
  afterwards with a `translate` transform.
- **`distance` must be positive.** To extrude the other way, add `reverse: true`
  (`XY` then goes toward -Z, `XZ` toward +Y, `YZ` toward -X). The solid stays
  anchored on the sketch plane, so `reverse` flips which side it grows on, and
  it works with subtract shapes and text.
- **`direction:` is optional and may only restate the plane's axis** (`Z` for
  `XY`, `Y` for `XZ`, `X` for `YZ`; note `XZ`'s axis is Y even though its default
  side is -Y). Any other value is an error, because the plane alone decides the
  axis. Use `reverse: true` for the opposite side.
- Check the result by building and reading the bounding box (`tiacad build`,
  then the contract's `bbox:`), not by assuming; `XZ` is the surprising one.

#### Fillet (Round Edges)

```yaml
operations:
  rounded_part:
    type: finishing
    finish: fillet
    input: my_part
    radius: 2.0             # Fillet radius
    edges: all              # Which edges to fillet
```

#### Chamfer (Bevel Edges)

**Uniform chamfer:**

```yaml
operations:
  chamfered_part:
    type: finishing
    finish: chamfer
    input: my_part
    length: 1.5             # Chamfer size
    edges: all
```

**Asymmetric chamfer:**

```yaml
operations:
  asymmetric_chamfer:
    type: finishing
    finish: chamfer
    input: my_part
    length: 1.5             # First length
    length2: 1.0            # Second length (different)
    edges: all
```

#### Edge Selection

Control which edges are affected:

**All edges:**

```yaml
edges: all
```

**Direction-based:**

```yaml
edges:
  direction: Z             # Edges aligned with Z axis
  # Also: X, Y, or [x,y,z] vector
```

**Parallel to axis:**

```yaml
edges:
  parallel_to: X           # Edges parallel to X axis
```

**Perpendicular to axis:**

```yaml
edges:
  perpendicular_to: Z      # Edges perpendicular to Z
```

**Advanced (CadQuery selector string):**

```yaml
edges:
  selector: ">Z"           # CadQuery string selector
```

**Important:** Finishing creates a **new named part** (the operation name becomes the result). The input part is unchanged and the result is registered under the operation name — use it in `export: default_part:` or as input to subsequent operations.

---

## Export

Specify which part to export. The output format is determined by the CLI command.

### Simple Export

```yaml
export:
  default_part: final_part   # Name of part to export
```

### Supported Output Formats

TiaCAD supports three output formats via the CLI:

| Format | Extension | Use Case | Quality |
|--------|-----------|----------|---------|
| **3MF** | `.3mf` | 3D printing (multi-material, modern slicers) | ⭐⭐⭐⭐⭐ Recommended |
| **STEP** | `.step` | CAD exchange, engineering, precise geometry | ⭐⭐⭐⭐ |
| **STL** | `.stl` | Legacy 3D printing only | ⭐ (binary mesh) |

### CLI Usage

```bash
# Default: outputs modern 3MF format
tiacad build examples/bracket_with_hole.yaml              # → bracket_with_hole.3mf (recommended)

# Specify output format with extension
tiacad build examples/bracket_with_hole.yaml -o bracket.step   # → STEP for CAD
tiacad build examples/bracket_with_hole.yaml -o bracket.stl    # → STL for legacy

# Multi-material designs (3MF only)
tiacad build examples/multi_material_demo.yaml  # → preserves colors/materials
```

**Note:** The `format:` field in YAML is not used. Output format is determined by the file extension in the CLI command.

---

## Contracts (expect:)

An optional top-level `expect:` block embeds the model's own ground truth. `tiacad check --contract`
and `tiacad verify` compare the built part against it, so a wrong dimension fails instead of just
looking plausible.

```yaml
parameters:
  w: 40
  d: 20
  h: 10
  wall: 2

parts:
  tray:
    primitive: box
    size: ['${w}', '${d}', '${h}']

expect:
  final: tray                      # part the contract applies to (default: the exported part)
  volume: '${w * d * h}'           # mm^3; number or ${...} over parameters (after --set)
  bbox: ['${w}', '${d}', '${h}']   # [X, Y, Z] extents in mm
  watertight: true
  components: 1                    # connected solids
  thickness: { min: '${wall}' }    # thinnest wall/floor, must be > 0
  tol: { volume: 0.01, length: 0.01 }
```

Other keys: `relations` (`flush`, `coaxial`, `clearance` with `min`/`max`, `gap`) and `no_overlap`
for assemblies. Because numeric values accept `${...}`, one contract stays correct for every
`tiacad verify --set NAME=VALUE` variant. See [MODEL_VALIDATION.md](../developer/MODEL_VALIDATION.md)
(how to write good contracts), [VALIDATION_STRENGTHENING.md](../developer/VALIDATION_STRENGTHENING.md)
section 4.1 (design) and `examples/sticker_drawer/sticker_tray.yaml` (a worked parametric contract).

---

## Complete Examples

### Example 1: Simple Box

```yaml
metadata:
  name: Basic Box
  description: Simple 100x100x10 box

parts:
  box:
    primitive: box
    size: [100, 100, 10]
    origin: center

export:
  default_part: box
```

### Example 2: Parametric Plate with Holes

```yaml
metadata:
  name: Mounting Plate
  description: Plate with 4 mounting holes

parameters:
  plate_width: 150
  plate_height: 100
  plate_thickness: 8
  hole_diameter: 6.5
  hole_spacing: 40

parts:
  plate:
    primitive: box
    size: ['${plate_width}', '${plate_height}', '${plate_thickness}']
    origin: center

  hole:
    primitive: cylinder
    radius: '${hole_diameter / 2}'
    height: '${plate_thickness + 2}'
    origin: center

operations:
  # Create 2x2 grid of holes
  hole_pattern:
    type: pattern
    pattern: grid
    input: hole
    count_x: 2
    count_y: 2
    spacing_x: '${hole_spacing}'
    spacing_y: '${hole_spacing}'

  # Subtract holes from plate
  finished_plate:
    type: boolean
    operation: difference
    base: plate
    subtract:
      - {pattern: hole_pattern}   # all 2 x 2 copies

export:
  default_part: plate
```

### Example 3: Bolt Circle with Filleted Edges

```yaml
metadata:
  name: Rounded Mounting Plate
  description: Circular bolt pattern with filleted edges

parameters:
  plate_diameter: 150
  bolt_count: 6
  bolt_circle_diameter: 100
  bolt_diameter: 6.5
  fillet_radius: 2.0

parts:
  plate:
    primitive: cylinder
    radius: '${plate_diameter / 2}'
    height: 8
    origin: center

  bolt_hole:
    primitive: cylinder
    radius: '${bolt_diameter / 2}'
    height: 10
    origin: center

operations:
  # Create circular pattern of bolt holes
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: '${bolt_count}'
    radius: '${bolt_circle_diameter / 2}'
    axis: Z
    center: [0, 0, 0]

  # Subtract all bolt holes
  plate_with_holes:
    type: boolean
    operation: difference
    base: plate
    subtract:
      - {pattern: bolt_circle}   # all bolt_count holes; change the count freely

  # Round the top edges
  finished_plate:
    type: finishing
    finish: fillet
    input: plate_with_holes
    radius: '${fillet_radius}'
    edges:
      direction: Z

export:
  default_part: plate_with_holes
```

### Example 4: L-Bracket with Chamfer

```yaml
metadata:
  name: L-Bracket
  description: Structural bracket with chamfered edges

parameters:
  base_width: 80
  base_depth: 80
  base_thickness: 6
  vertical_height: 60
  vertical_thickness: 6
  chamfer_size: 1.5

parts:
  base_plate:
    primitive: box
    size: ['${base_width}', '${base_depth}', '${base_thickness}']
    origin: corner

  vertical_plate:
    primitive: box
    size: ['${base_width}', '${vertical_thickness}', '${vertical_height}']
    origin: corner

operations:
  # Position vertical plate
  vertical_positioned:
    type: transform
    input: vertical_plate
    transforms:
      - translate: [0, 0, '${base_thickness}']

  # Combine into L-shape
  bracket_body:
    type: boolean
    operation: union
    inputs:
      - base_plate
      - vertical_positioned

  # Chamfer vertical edges
  finished_bracket:
    type: finishing
    finish: chamfer
    input: bracket_body
    length: '${chamfer_size}'
    edges:
      direction: Z

export:
  default_part: finished_bracket
```

---

## Tips & Best Practices

### 1. Use Parameters for Flexibility

Make designs parametric from the start:

```yaml
parameters:
  # Master dimensions
  base_size: 100

  # Derived dimensions
  half_size: '${base_size / 2}'
  quarter_size: '${base_size / 4}'
```

### 2. Order Matters for Transforms

Transforms apply sequentially. These are different:

```yaml
# Move THEN rotate
transforms:
  - translate: [10, 0, 0]
  - rotate: {axis: Z, angle: 90, origin: [0,0,0]}

# Rotate THEN move (different result!)
transforms:
  - rotate: {axis: Z, angle: 90, origin: [0,0,0]}
  - translate: [10, 0, 0]
```

### 3. Always Specify Rotation Origins

Rotations REQUIRE explicit origins:

```yaml
# ✅ Good
rotate:
  axis: Z
  angle: 45
  origin: [0, 0, 0]

# ❌ Will fail
rotate:
  axis: Z
  angle: 45
```

### 4. Pattern Naming Convention

Patterns generate numbered parts. Refer to all of them with `{pattern: name}` instead of
listing each one, so changing `count` can't leave a copy behind:

```yaml
operations:
  my_pattern:
    type: pattern
    pattern: circular
    input: hole
    count: 4

  # Creates: my_pattern_0, my_pattern_1, my_pattern_2, my_pattern_3

  result:
    type: boolean
    operation: difference
    base: plate
    subtract:
      - {pattern: my_pattern}     # same as listing my_pattern_0 .. my_pattern_3
```

### 5. Use Finishing Last

Apply finishing operations after all boolean/pattern operations:

```yaml
operations:
  # 1. Create parts
  # 2. Pattern them
  # 3. Boolean operations
  # 4. Finishing (last!)
  finished:
    type: finishing
    finish: fillet
    input: assembled_part
```

### 6. Test Incrementally

Build complex designs step by step:

1. Start with basic parts
2. Add one operation at a time
3. Export and verify each step
4. Add complexity gradually

---

## Common Patterns

### Mounting Plate with Bolt Circle

```yaml
parameters:
  bolt_count: 6
  bolt_circle_radius: 50

operations:
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: '${bolt_count}'
    radius: '${bolt_circle_radius}'
    axis: Z
    center: [0, 0, 0]
```

### Grid of Holes

```yaml
operations:
  hole_grid:
    type: pattern
    pattern: grid
    input: hole
    count_x: 4
    count_y: 3
    spacing_x: 20
    spacing_y: 25
```

### Rounded Edges (Safety)

```yaml
operations:
  rounded:
    type: finishing
    finish: fillet
    input: sharp_part
    radius: 2.0
    edges: all
```

### Chamfered Edges (Strength)

```yaml
operations:
  chamfered:
    type: finishing
    finish: chamfer
    input: part
    length: 1.5
    edges:
      direction: Z
```

---

## Reference Tables

### Primitives

| Primitive | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| box | parameters: width (X), depth (Y), height (Z) | origin |
| cylinder | radius, height | origin |
| sphere | radius | origin |
| cone | radius1 (base), radius2 (top), height | origin |
| polygon | sides, diameter, height | circumscribed (default true) |

### Origin Modes

Every primitive (box, cylinder, cone, sphere, torus, polygon) takes the same `origin:` values and
measures them from its own bounding box. Anything else, such as `bottom` or `centre`, is an error that
lists the valid modes; it is never silently treated as `center`.

| Mode | Puts this point at (0, 0, 0) | Example |
|------|------------------------------|---------|
| center | bounding-box center (default; polygon defaults to `base`) | `origin: center` |
| base | bottom-center, the middle of the z-min face, so the part sits on the bed | `origin: base` |
| corner | bounding-box min corner | `origin: corner` |
| custom | `[x, y, z]` is where the reference point goes: min corner for a box, bottom-center for cylinder/cone/polygon, center for sphere/torus | `origin: [x, y, z]` |

`tiacad validate-geometry` prints a `Placement:` line when a part does not start at z=0.

### Axes

| Axis | Description |
|------|-------------|
| X | [1, 0, 0] |
| Y | [0, 1, 0] |
| Z | [0, 0, 1] |
| [x,y,z] | Custom vector |

### Boolean Operations

| Operation | Purpose | Syntax |
|-----------|---------|--------|
| union | Combine parts | `inputs: [...]` |
| difference | Subtract | `base: ..., subtract: [...]` (entries may be `{pattern: name}` for every copy of a pattern) |
| intersection | Overlap only | `inputs: [...]` |

### Pattern Types

| Type | Purpose | Key Fields |
|------|---------|-----------|
| linear | Line or grid | count, spacing, direction |
| circular | Circle/arc | count, radius, axis, center |
| grid | 2D rectangular | count_x, count_y, spacing_x, spacing_y |

### Finishing Operations

| Operation | Purpose | Key Fields |
|-----------|---------|-----------|
| fillet | Round edges | radius, edges |
| chamfer | Bevel edges | length (+ length2), edges |

---

## Error Messages

TiaCAD provides clear error messages:

### Missing Required Field

```
Error: Missing required field 'radius' in part 'my_cylinder'
Available fields: primitive, height, origin
```

### Unknown Part Reference

```
Error: Part 'unknown_part' not found in operation 'my_operation'
Available parts: plate, hole, bracket
```

### Invalid Parameter Expression

```
Error: Cannot evaluate parameter expression '${width * }'
Syntax error in expression
```

### Invalid Edge Selector

```
Error: Invalid edge selector direction 'W'
Valid axes: X, Y, Z, or vector [x,y,z]
```

---

## Next Steps

- See [TUTORIAL.md](TUTORIAL.md) for step-by-step guides
- See [EXAMPLES_GUIDE.md](EXAMPLES_GUIDE.md) for annotated examples
- See [README.md](README.md) for project overview
- Try the examples in `examples/` directory

---

## Migration from v0.3.0

If you have existing v0.3.0 YAML files, see [MIGRATION_GUIDE_V3.md](../developer/MIGRATION_GUIDE_V3.md) for detailed migration instructions.

**Key Changes:**
- `named_points:` → `references:` with explicit `type` field
- Auto-generated references (e.g., `part.face_top`)
- box dimensions are `size: [x, y, z]` (v0.3.0's `size:` returned in v3.x after a `width`/`depth`/`height` interlude)
- Local frame offsets for intuitive positioning
- Face/edge/axis references (not just points)

---

**Version:** Current
**Status:** Active syntax reference
