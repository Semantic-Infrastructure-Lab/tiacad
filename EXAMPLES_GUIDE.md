# TiaCAD Examples Guide

**Version:** 0.2.0
**Last Updated:** 2025-10-25
**Status:** Phase 2 Complete

---

## Overview

This guide walks through all 6 working examples in the `examples/` directory, explaining what each one demonstrates and how it works.

Each example builds on previous concepts, teaching you TiaCAD progressively.

---

## Table of Contents

1. [Example 1: Simple Box](#example-1-simple-box) - Primitives and basics
2. [Example 2: Simple Guitar Hanger](#example-2-simple-guitar-hanger) - Transforms
3. [Example 3: Guitar Hanger with Holes](#example-3-guitar-hanger-with-holes) - Boolean operations
4. [Example 4: Mounting Plate with Bolt Circle](#example-4-mounting-plate-with-bolt-circle) - Circular patterns
5. [Example 5: Rounded Mounting Plate](#example-5-rounded-mounting-plate) - Fillet finishing
6. [Example 6: Chamfered L-Bracket](#example-6-chamfered-l-bracket) - Chamfer finishing

---

## Example 1: Simple Box

**File:** `examples/simple_box.yaml`
**Complexity:** ⭐ Beginner
**Concepts:** Primitives, basic structure

### What It Creates

A simple 100x100x10mm box, centered at the origin.

### The Code

```yaml
metadata:
  name: Simple Box
  description: Basic box primitive example
  version: 1.0

parts:
  box:
    primitive: box
    size: [100, 100, 10]
    origin: center

export:
  default_part: box
```

### Key Concepts

1. **Metadata Section**: Documentation (optional)
2. **Parts Section**: Define geometry
3. **Primitive**: `box` with size `[x, y, z]`
4. **Origin**: `center` places center at (0,0,0)
5. **Export**: Specify what to save

### Run It

```bash
tiacad build examples/simple_box.yaml
```

### Output

- **File:** `output/simple_box.stl`
- **Size:** ~1KB
- **Geometry:** Simple rectangular box

### Learning Goals

- Understand YAML structure
- Learn about primitives
- Understand origin modes
- See the basic workflow

---

## Example 2: Simple Guitar Hanger

**File:** `examples/simple_guitar_hanger.yaml`
**Complexity:** ⭐⭐ Intermediate
**Concepts:** Multiple parts, transforms, positioning

### What It Creates

A guitar wall hanger with:
- Horizontal beam (100x50x25mm)
- Angled arm (22x70x16mm) tilted 10° upward

### Key Features

- Two separate parts
- Transform operations (translate, rotate)
- Rotation with explicit origin

### Code Walkthrough

```yaml
parameters:
  # Beam dimensions
  beam_width: 100
  beam_depth: 50
  beam_height: 25

  # Arm dimensions
  arm_width: 22
  arm_depth: 70
  arm_height: 16
  arm_tilt_angle: 10
```

Parameters make the design configurable.

```yaml
parts:
  beam:
    primitive: box
    size: ['${beam_width}', '${beam_depth}', '${beam_height}']
    origin: center

  arm:
    primitive: box
    size: ['${arm_width}', '${arm_depth}', '${arm_height}']
    origin: center
```

Two box primitives using parameters.

```yaml
operations:
  arm_positioned:
    type: transform
    input: arm
    transforms:
      # First: move to front of beam
      - translate: [0, '${beam_depth/2}', 0]

      # Second: push outward
      - translate: [0, '${arm_depth/2}', 0]

      # Third: tilt upward
      - rotate:
          axis: X
          angle: '${arm_tilt_angle}'
          origin: [0, '${beam_depth/2}', 0]
```

**Critical:** Transforms apply in order!
1. Move arm to beam front
2. Push outward
3. Tilt upward (around the beam front edge)

### Run It

```bash
tiacad build examples/simple_guitar_hanger.yaml
```

### Output

- **File:** `output/simple_guitar_hanger.stl`
- **Geometry:** Two separate boxes (beam and positioned arm)

### Learning Goals

- Multiple parts in one design
- Transform operations (translate, rotate)
- Transform order matters
- Rotation origins (explicit positioning)
- Parameter expressions

### Common Mistakes

**Mistake:** Rotating before moving

```yaml
transforms:
  - rotate: {...}    # Rotate first
  - translate: [10, 0, 0]  # Then move - DIFFERENT RESULT!
```

**Correct:** Move then rotate (usually)

```yaml
transforms:
  - translate: [10, 0, 0]  # Position first
  - rotate: {...}           # Then rotate in place
```

---

## Example 3: Guitar Hanger with Holes

**File:** `examples/guitar_hanger_with_holes.yaml`
**Complexity:** ⭐⭐⭐ Advanced
**Concepts:** Boolean operations, difference

### What It Creates

Same guitar hanger, but with mounting holes:
- 2 bolt holes through the beam
- Positioned for wall mounting

### New Concepts

- Boolean difference (subtracting parts)
- Cylinders (for holes)
- Multi-part boolean operations

### Code Walkthrough

```yaml
parts:
  # ... beam and arm as before ...

  # Mounting holes
  mount_hole_1:
    primitive: cylinder
    radius: '${mount_hole_diameter / 2}'
    height: '${beam_height + 2}'  # Slightly taller for clean cut
    origin: center

  mount_hole_2:
    primitive: cylinder
    radius: '${mount_hole_diameter / 2}'
    height: '${beam_height + 2}'
    origin: center
```

**Why `height: beam_height + 2`?**
- Makes holes slightly taller than beam
- Ensures clean cut-through
- CadQuery best practice

```yaml
operations:
  # Position first hole
  hole_1_positioned:
    type: transform
    input: mount_hole_1
    transforms:
      - translate: ['${-mount_hole_spacing/2}', 0, 0]

  # Position second hole
  hole_2_positioned:
    type: transform
    input: mount_hole_2
    transforms:
      - translate: ['${mount_hole_spacing/2}', 0, 0]

  # Position arm (as before)
  arm_positioned:
    type: transform
    input: arm
    transforms: [...]

  # Subtract holes from beam
  beam_with_holes:
    type: boolean
    operation: difference
    base: beam
    subtract:
      - hole_1_positioned
      - hole_2_positioned
```

**Boolean Difference:**
- `base`: The part to cut from
- `subtract`: Parts to remove (list)
- Result: `base` with `subtract` parts removed

### Run It

```bash
tiacad build examples/guitar_hanger_with_holes.yaml
```

### Output

- **File:** `output/guitar_hanger_with_holes.stl`
- **Geometry:** Beam with 2 holes + positioned arm

### Learning Goals

- Boolean operations (difference)
- Creating holes with cylinders
- Multi-part subtraction
- Positioning parts before boolean ops

### Design Pattern: Making Holes

```yaml
# 1. Define the hole geometry
hole:
  primitive: cylinder
  height: '${part_thickness + 2}'  # Always slightly taller!

# 2. Position it
hole_positioned:
  type: transform
  input: hole
  transforms: [translate: [...]]

# 3. Subtract from base part
part_with_hole:
  type: boolean
  operation: difference
  base: my_part
  subtract: [hole_positioned]
```

---

## Example 4: Mounting Plate with Bolt Circle

**File:** `examples/mounting_plate_with_bolt_circle.yaml`
**Complexity:** ⭐⭐⭐ Advanced
**Concepts:** Circular patterns, multi-hole subtraction

### What It Creates

A professional mounting plate (150x150x8mm) with:
- 6 bolt holes in a circular pattern (100mm diameter)
- M6 bolt size (6.5mm holes)
- Center hole (10mm diameter)

### New Concepts

- Circular pattern operation
- Pattern part naming
- Subtracting pattern results

### Code Walkthrough

```yaml
parameters:
  plate_width: 150
  plate_height: 150
  plate_thickness: 8

  bolt_count: 6
  bolt_circle_diameter: 100
  bolt_hole_diameter: 6.5  # M6 bolts

  center_hole_diameter: 10
```

Parametric design - change bolt count or circle size easily!

```yaml
parts:
  plate:
    primitive: box
    size: ['${plate_width}', '${plate_height}', '${plate_thickness}']
    origin: center

  bolt_hole:
    primitive: cylinder
    radius: '${bolt_hole_diameter / 2}'
    height: '${plate_thickness + 2}'
    origin: center
```

**Note:** Only one `bolt_hole` part defined - we'll pattern it!

```yaml
operations:
  # Create 6 holes in a circle
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: '${bolt_count}'
    axis: Z
    center: [0, 0, 0]
    radius: '${bolt_circle_diameter / 2}'
```

**Circular Pattern:**
- Creates `count` copies around a circle
- Evenly spaced (360° / count)
- Rotates around `axis` (Z = horizontal circle)
- Centered at `center` point
- Distance from center = `radius`

**Generated Parts:**
- `bolt_circle_0` (at 0°)
- `bolt_circle_1` (at 60°)
- `bolt_circle_2` (at 120°)
- `bolt_circle_3` (at 180°)
- `bolt_circle_4` (at 240°)
- `bolt_circle_5` (at 300°)

```yaml
  # Subtract all holes
  plate_with_holes:
    type: boolean
    operation: difference
    base: plate
    subtract:
      - center_hole
      - bolt_circle_0
      - bolt_circle_1
      - bolt_circle_2
      - bolt_circle_3
      - bolt_circle_4
      - bolt_circle_5
```

**Pattern Usage:**
- Must list each generated part explicitly
- Names are `{pattern_name}_{index}`
- Index starts at 0

### Run It

```bash
tiacad build examples/mounting_plate_with_bolt_circle.yaml
```

### Output

- **File:** `output/mounting_plate_with_bolt_circle.stl`
- **Size:** ~400KB (complex geometry with many holes)
- **Geometry:** Plate with 7 holes (6 bolt + 1 center)

### Learning Goals

- Circular patterns for bolt circles
- Pattern part naming convention
- Practical mounting hardware design
- Why patterns are better than manual positioning

### Design Pattern: Bolt Circles

```yaml
# Standard M6 bolt circle (6 bolts, 100mm diameter)
parameters:
  bolt_count: 6
  bolt_diameter: 6.5
  bolt_circle_diameter: 100

parts:
  bolt_hole:
    primitive: cylinder
    radius: '${bolt_diameter / 2}'

operations:
  bolt_circle:
    type: pattern
    pattern: circular
    count: '${bolt_count}'
    radius: '${bolt_circle_diameter / 2}'
    axis: Z
    center: [0, 0, 0]
```

---

## Example 5: Rounded Mounting Plate

**File:** `examples/rounded_mounting_plate.yaml`
**Complexity:** ⭐⭐⭐⭐ Expert
**Concepts:** Fillet finishing, edge selection

### What It Creates

Enhanced version of Example 4 with:
- Same bolt circle pattern
- **Rounded top edges** (2mm radius fillet)
- Professional safety feature

### New Concepts

- Finishing operations (fillet)
- Edge selection strategies
- In-place part modification

### Code Walkthrough

All parts and operations same as Example 4, plus:

```yaml
parameters:
  # ... all previous parameters ...
  edge_fillet_radius: 2.0  # NEW: rounded edge size
```

```yaml
operations:
  # ... bolt_circle pattern as before ...

  # ... boolean difference as before ...

  # NEW: Round the top edges
  finished_plate:
    type: finishing
    finish: fillet
    input: plate_with_holes
    radius: '${edge_fillet_radius}'
    edges:
      direction: Z
```

**Fillet Operation:**
- `finish: fillet` - Round edges
- `input: plate_with_holes` - Which part to modify
- `radius: 2.0` - How round (2mm radius)
- `edges: {direction: Z}` - Only Z-aligned edges (top/bottom)

**Edge Selection:**
```yaml
edges:
  direction: Z    # Only edges aligned with Z axis
```

Other options:
- `edges: all` - All edges
- `{parallel_to: X}` - Edges parallel to X
- `{perpendicular_to: Y}` - Edges perpendicular to Y

**Important:** Finishing modifies parts **in-place**!
- `plate_with_holes` is modified, not copied
- Export still uses original part name

### Run It

```bash
tiacad build examples/rounded_mounting_plate.yaml
```

### Output

- **File:** `output/rounded_mounting_plate.stl`
- **Size:** ~3MB (large due to smooth curves from fillet)
- **Geometry:** Plate with holes + smooth rounded edges

### Learning Goals

- Professional finishing touches
- Fillet operation (safety edges)
- Edge selection control
- In-place modification behavior

### Why Fillet?

**Safety:**
- Sharp edges can cut
- Rounded edges safer to handle

**Aesthetics:**
- Professional appearance
- Manufacturing quality

**Strength:**
- Distributes stress better
- Reduces stress concentrations

### Design Pattern: Safety Edges

```yaml
# Always fillet exposed edges on handheld parts
finished:
  type: finishing
  finish: fillet
  input: my_part
  radius: 2.0  # 2mm standard safety radius
  edges:
    direction: Z  # Top/bottom edges only
```

---

## Example 6: Chamfered L-Bracket

**File:** `examples/chamfered_bracket.yaml`
**Complexity:** ⭐⭐⭐⭐ Expert
**Concepts:** Chamfer finishing, complex boolean unions, rotated holes

### What It Creates

A structural L-bracket with:
- 80x80mm base plate (6mm thick)
- 60mm vertical plate (6mm thick)
- 4 mounting holes (2 in base, 2 in vertical)
- **Chamfered vertical edges** (1.5mm) for strength

### New Concepts

- Chamfer finishing (beveled edges)
- Boolean union (joining parts)
- Rotated hole positioning
- Complex assemblies

### Code Walkthrough

#### Part Definitions

```yaml
parts:
  base_plate:
    primitive: box
    size: ['${base_width}', '${base_depth}', '${base_thickness}']
    origin: corner  # Note: corner origin for easier positioning

  vertical_plate:
    primitive: box
    size: ['${base_width}', '${vertical_thickness}', '${vertical_height}']
    origin: corner
```

**Why `origin: corner`?**
- Makes L-bracket positioning easier
- Base corner at (0,0,0)
- Vertical corner at (0, base_depth, base_thickness)

#### L-Bracket Assembly

```yaml
operations:
  # Position vertical plate at back of base
  vertical_positioned:
    type: transform
    input: vertical_plate
    transforms:
      - translate: [0, '${base_depth}', '${base_thickness}']
```

Moves vertical plate to stand up from back edge.

```yaml
  # Join base and vertical into L-shape
  bracket_body:
    type: boolean
    operation: union
    inputs:
      - base_plate
      - vertical_positioned
```

**Boolean Union:**
- `operation: union` - Combine parts
- `inputs: [...]` - Parts to join
- Result: Single solid L-shape

#### Positioning Holes

**Base holes** (simple):
```yaml
  base_hole_1_positioned:
    type: transform
    input: base_hole_1
    transforms:
      - translate: ['${base_width/2 - hole_spacing/2}', '${base_depth/2}', 0]
```

**Vertical holes** (complex - must rotate!):
```yaml
  vertical_hole_1_positioned:
    type: transform
    input: vertical_hole_1
    transforms:
      # Position at hole location
      - translate: ['${base_width/2 - hole_spacing/2}',
                    '${base_depth}',
                    '${base_thickness + vertical_height/2}']

      # Rotate to point forward (was pointing up)
      - rotate:
          angle: 90
          axis: X
          origin: ['${base_width/2 - hole_spacing/2}',
                   '${base_depth}',
                   '${base_thickness + vertical_height/2}']
```

**Why rotate the hole?**
- Cylinder default: vertical (up/down)
- Vertical plate holes: horizontal (forward/back)
- Must rotate 90° around X axis

#### Chamfer Finishing

```yaml
  # Chamfer vertical edges for strength
  finished_bracket:
    type: finishing
    finish: chamfer
    input: bracket_with_holes
    length: '${chamfer_size}'
    edges:
      direction: Z  # Only vertical edges
```

**Chamfer Operation:**
- `finish: chamfer` - Bevel edges (cut at angle)
- `length: 1.5` - Size of bevel
- `edges: {direction: Z}` - Vertical edges only

**Chamfer vs Fillet:**
- **Chamfer:** Flat bevel (angular)
- **Fillet:** Rounded curve (smooth)

**When to use chamfer:**
- Structural parts (distributes force)
- Easier to machine than fillets
- Sharp aesthetic (industrial look)

### Run It

```bash
tiacad build examples/chamfered_bracket.yaml
```

### Output

- **File:** `output/chamfered_bracket.stl`
- **Size:** ~102KB
- **Geometry:** L-bracket with 4 holes + chamfered edges

### Learning Goals

- Boolean union (combining parts)
- Complex part positioning
- Rotated holes (cylinders)
- Chamfer finishing
- Structural part design

### Design Pattern: L-Brackets

```yaml
# Standard L-bracket assembly
parts:
  base: {primitive: box, origin: corner}
  vertical: {primitive: box, origin: corner}

operations:
  # Position vertical at back edge
  vertical_pos:
    transforms:
      - translate: [0, base_depth, base_thickness]

  # Join into L-shape
  bracket:
    type: boolean
    operation: union
    inputs: [base, vertical_pos]

  # Add strength with chamfer
  finished:
    type: finishing
    finish: chamfer
    edges: {direction: Z}
```

---

## Example Comparison Table

| Example | Complexity | File Size | Key Concepts |
|---------|-----------|-----------|--------------|
| 1. Simple Box | ⭐ | ~1KB | Primitives, basics |
| 2. Guitar Hanger | ⭐⭐ | ~2KB | Transforms, positioning |
| 3. Hanger w/ Holes | ⭐⭐⭐ | ~5KB | Boolean difference |
| 4. Bolt Circle | ⭐⭐⭐ | ~400KB | Circular patterns |
| 5. Rounded Plate | ⭐⭐⭐⭐ | ~3MB | Fillet finishing |
| 6. L-Bracket | ⭐⭐⭐⭐ | ~102KB | Chamfer, union |

---

## Learning Path

### Beginner (Start Here)

1. **Simple Box** - Learn YAML structure
2. **Simple Guitar Hanger** - Learn transforms
3. Practice: Create a rotated cube

### Intermediate

4. **Guitar Hanger with Holes** - Learn boolean difference
5. Practice: Create a plate with 2 holes
6. **Mounting Plate** - Learn circular patterns
7. Practice: Create a 4-bolt pattern

### Advanced

8. **Rounded Mounting Plate** - Learn fillet finishing
9. Practice: Add fillets to previous designs
10. **Chamfered L-Bracket** - Learn chamfer and unions
11. Practice: Create a T-bracket

---

## Common Use Cases

### Mounting Plates

**Use:** Examples 4, 5
**Features:** Bolt circles, center holes, optional finishing
**Real-world:** Wall mounts, equipment plates, adapter plates

### Brackets

**Use:** Example 6
**Features:** L-shape, multiple orientations, structural finishing
**Real-world:** Shelf brackets, corner braces, equipment mounts

### Enclosures

**Combine concepts from:**
- Boolean difference (holes for connectors)
- Fillet (safe edges)
- Patterns (ventilation holes)

---

## Tips for Using Examples

### Modify Parameters

All examples are parametric. Try changing:

```yaml
# In rounded_mounting_plate.yaml
parameters:
  bolt_count: 8        # Change from 6 to 8
  bolt_circle_diameter: 120  # Make circle larger
  edge_fillet_radius: 3.0    # Bigger fillet
```

### Mix and Match

Combine techniques from different examples:
- Bolt circle from Example 4
- Fillet from Example 5
- L-bracket from Example 6
= **L-bracket with bolt circle and filleted edges!**

### Learn from Tests

Check `tiacad_core/tests/test_parser/` for more examples:
- Edge cases
- Error handling
- Advanced techniques

---

## Next Steps

### Create Your Own

Now that you understand all 6 examples, create:
1. Your own mounting plate (custom dimensions)
2. A T-bracket (3 plates joined)
3. An enclosure (box with holes for cables)

### Explore Documentation

- [TUTORIAL.md](TUTORIAL.md) - Step-by-step guide
- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Complete language reference
- [README.md](README.md) - Project overview

### Advanced Techniques

Study the test files for:
- Grid patterns
- Linear patterns
- Multiple finishing operations
- Complex assemblies

---

## Troubleshooting

### STL File Too Large

**Cause:** Fillets create many triangles
**Solution:** Reduce fillet radius or use chamfer

### Pattern Parts Not Found

**Error:** `Part 'bolt_circle' not found`
**Fix:** Use `bolt_circle_0`, `bolt_circle_1`, etc.

### Holes Not Cutting Through

**Cause:** Cylinder not tall enough
**Fix:** Make cylinder `height: part_thickness + 2`

### Rotation Origin Confusion

**Problem:** Part rotates weirdly
**Fix:** Visualize rotation point, ensure origin is correct

---

## Example File Locations

All examples are in:
```
/home/scottsen/src/tia/projects/tiacad/examples/
```

Generated STL files appear in:
```
/home/scottsen/src/tia/projects/tiacad/output/
```

---

**Version:** 0.2.0
**Last Updated:** 2025-10-25
**Examples:** 6 working, tested, production-ready
**Status:** Phase 2 Complete
