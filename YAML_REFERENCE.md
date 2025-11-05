# TiaCAD YAML Reference Guide

**Version:** 0.2.0
**Last Updated:** 2025-10-25
**Status:** Phase 2 Complete

---

## Table of Contents

1. [Document Structure](#document-structure)
2. [Metadata](#metadata)
3. [Parameters](#parameters)
4. [Parts](#parts)
5. [Operations](#operations)
   - [Transform Operations](#transform-operations)
   - [Boolean Operations](#boolean-operations)
   - [Pattern Operations](#pattern-operations)
   - [Finishing Operations](#finishing-operations)
6. [Export](#export)
7. [Complete Examples](#complete-examples)

---

## Document Structure

Every TiaCAD YAML file follows this structure:

```yaml
metadata:           # Optional: document information
  name: My Design
  description: ...
  version: 1.0

parameters:         # Optional: parametric values
  width: 100
  height: 50

parts:             # Required: define primitive parts
  part_name:
    primitive: box
    size: [...]

operations:        # Optional: transform, boolean, pattern, finish
  operation_name:
    type: boolean
    operation: union
    inputs: [...]

export:            # Required: what to export
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
```

All fields are optional and for documentation only.

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

### Using Parameters

Reference parameters in any numeric field:

```yaml
parts:
  plate:
    primitive: box
    size: ['${width}', '${height}', '${thickness}']
```

---

## Parts

Parts are the basic building blocks. Each part starts from a primitive shape.

### Box Primitive

```yaml
parts:
  my_box:
    primitive: box
    size: [width, height, depth]  # X, Y, Z dimensions
    origin: center                # center, corner, or [x,y,z]
```

**Origin modes:**
- `center`: Center at (0, 0, 0) - default
- `corner`: Min corner at (0, 0, 0)
- `[x, y, z]`: Custom origin point

### Cylinder Primitive

```yaml
parts:
  my_cylinder:
    primitive: cylinder
    radius: 10                    # Cylinder radius
    height: 50                    # Cylinder height
    origin: center                # center, corner, or [x,y,z]
```

### Sphere Primitive

```yaml
parts:
  my_sphere:
    primitive: sphere
    radius: 15                    # Sphere radius
    origin: center                # Usually center
```

### Cone Primitive

```yaml
parts:
  my_cone:
    primitive: cone
    radius: 20                    # Base radius
    height: 40                    # Cone height
    origin: center                # center, corner, or [x,y,z]
```

### Parts with Transforms

Apply transforms directly to parts:

```yaml
parts:
  rotated_box:
    primitive: box
    size: [10, 20, 30]
    transforms:
      - translate: [50, 0, 0]
      - rotate:
          axis: Z
          angle: 45
          origin: [0, 0, 0]
```

---

## Operations

Operations modify or combine parts.

### Transform Operations

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
          angle: 45                # Degrees
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

### Boolean Operations

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

### Pattern Operations

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
    spacing: 20              # Distance between copies
    direction: X             # X, Y, Z, or [x,y,z]
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
Generated parts are named: `{pattern_name}_{index}`

Example: `bolt_circle` creates `bolt_circle_0`, `bolt_circle_1`, etc.

---

### Finishing Operations

Add professional finishing to parts.

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

**Important:** Finishing operations modify parts in-place!

---

## Export

Specify what to export as STL.

### Simple Export

```yaml
export:
  default_part: final_part   # Name of part to export
```

### Export Settings (Future)

```yaml
export:
  default_part: assembly
  format: stl                # Currently only STL
  tolerance: 0.01            # (Future) Mesh quality
  output_path: output/       # (Future) Custom path
```

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
      - hole_pattern_0_0
      - hole_pattern_0_1
      - hole_pattern_1_0
      - hole_pattern_1_1

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
      - bolt_circle_0
      - bolt_circle_1
      - bolt_circle_2
      - bolt_circle_3
      - bolt_circle_4
      - bolt_circle_5

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
      - translate: [0, '${base_depth}', '${base_thickness}']

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
  default_part: bracket_body
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

Patterns generate numbered parts. Plan your boolean operations accordingly:

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
      - my_pattern_0
      - my_pattern_1
      - my_pattern_2
      - my_pattern_3
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
| box | size: [x,y,z] | origin |
| cylinder | radius, height | origin |
| sphere | radius | origin |
| cone | radius, height | origin |

### Origin Modes

| Mode | Description | Example |
|------|-------------|---------|
| center | Center at origin | `origin: center` |
| corner | Min corner at origin | `origin: corner` |
| custom | Specific point | `origin: [x, y, z]` |

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
| difference | Subtract | `base: ..., subtract: [...]` |
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

**Version:** 0.2.0
**Last Updated:** 2025-10-25
**Status:** Phase 2 Complete - Production Ready
