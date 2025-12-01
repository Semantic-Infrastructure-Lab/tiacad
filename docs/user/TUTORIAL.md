# TiaCAD Tutorial - Getting Started

**Version:** 0.2.0
**Difficulty:** Beginner
**Time:** 30 minutes
**Last Updated:** 2025-10-25

---

## Welcome to TiaCAD!

This tutorial will teach you how to create 3D models using YAML. No programming experience required!

By the end, you'll create a professional mounting plate with bolt holes and rounded edges.

---

## Table of Contents

1. [Installation](#installation)
2. [Your First Model](#your-first-model)
3. [Adding Parameters](#adding-parameters)
4. [Creating Holes](#creating-holes)
5. [Making a Bolt Circle](#making-a-bolt-circle)
6. [Professional Finishing](#professional-finishing)
7. [Next Steps](#next-steps)

---

## Installation

### Prerequisites

You'll need Python 3.10+ installed on your system.

### Install TiaCAD

```bash
# Navigate to the TiaCAD directory
cd /home/scottsen/src/tia/projects/tiacad

# Install dependencies
pip install -r requirements.txt

# Verify installation by running tests
pytest tiacad_core/tests/ -v

# You should see: 196 tests passed ✅
```

---

## Your First Model

Let's create a simple box!

### Step 1: Create a YAML File

Create a new file called `my_first_box.yaml` in the `examples/` directory:

```yaml
metadata:
  name: My First Box
  description: A simple 100x100x10mm box

parts:
  box:
    primitive: box
    size: [100, 100, 10]
    origin: center

export:
  default_part: box
```

### Step 2: Generate the Model

```bash
tiacad build examples/my_first_box.yaml
```

### Step 3: Check the Output

```bash
ls -lh
# You should see: my_first_box.3mf (modern 3D printing format)
```

**Congratulations!** You just created your first 3D model in YAML! 🎉

### What Did We Just Do?

- **metadata**: Documentation (optional but helpful)
- **parts**: Define a box 100x100x10mm centered at origin
- **export**: Tell TiaCAD what part to export
- **CLI**: `tiacad build` defaults to 3MF (modern format for 3D printing)

---

## Adding Parameters

Hard-coded numbers are bad. Let's make our box parametric!

### Step 1: Add Parameters

Update your YAML file:

```yaml
metadata:
  name: Parametric Box
  description: A box with configurable dimensions

parameters:
  width: 100
  height: 100
  thickness: 10

parts:
  box:
    primitive: box
    size: ['${width}', '${height}', '${thickness}']
    origin: center

export:
  default_part: box
```

### Step 2: Test It

```bash
tiacad build examples/my_first_box.yaml
```

Same result, but now you can change all three dimensions by editing one place!

### Using Math in Parameters

Parameters can do math:

```yaml
parameters:
  base_size: 100
  double_size: '${base_size * 2}'
  half_size: '${base_size / 2}'
```

**Note:** Put expressions in quotes: `'${...}'`

---

## Creating Holes

Let's add a hole to our box.

### Step 1: Add a Cylinder Part

```yaml
metadata:
  name: Box with Hole
  description: A box with a center hole

parameters:
  box_width: 100
  box_height: 100
  box_thickness: 10
  hole_diameter: 20

parts:
  box:
    primitive: box
    size: ['${box_width}', '${box_height}', '${box_thickness}']
    origin: center

  hole:
    primitive: cylinder
    radius: '${hole_diameter / 2}'
    height: '${box_thickness + 2}'  # Slightly taller for clean cut
    origin: center

export:
  default_part: box
```

### Step 2: Subtract the Hole

Add an `operations` section:

```yaml
metadata:
  name: Box with Hole
  description: A box with a center hole

parameters:
  box_width: 100
  box_height: 100
  box_thickness: 10
  hole_diameter: 20

parts:
  box:
    primitive: box
    size: ['${box_width}', '${box_height}', '${box_thickness}']
    origin: center

  hole:
    primitive: cylinder
    radius: '${hole_diameter / 2}'
    height: '${box_thickness + 2}'
    origin: center

operations:
  box_with_hole:
    type: boolean
    operation: difference
    base: box
    subtract:
      - hole

export:
  default_part: box  # Note: operations modify parts in-place for finishing
```

### Step 3: Generate and View

```bash
tiacad build examples/my_first_box.yaml
```

You now have a box with a hole in the center!

### How Boolean Operations Work

- **difference**: Subtract parts (make holes)
- **union**: Combine parts (join them)
- **intersection**: Keep only overlap

---

## Positioning Parts with Anchors

One of TiaCAD's most powerful features is **automatic anchors** - predefined attachment points on every part.

### What are anchors?

Think of anchors as marked spots on a workbench where things can be attached. Instead of calculating coordinates manually, you say "put this on top of that".

### Example: Stacking Boxes

```yaml
parameters:
  base_width: 100
  base_height: 20
  tower_width: 30
  tower_height: 60

parts:
  base:
    primitive: box
    parameters:
      width: '${base_width}'
      height: '${base_height}'
      depth: 50
    origin: center

  tower:
    primitive: box
    parameters:
      width: '${tower_width}'
      height: '${tower_height}'
      depth: 30
    origin: center
    translate:
      to: base.face_top  # Anchor at top of base!
```

**What just happened?**
- `base.face_top` is an **automatic anchor** at the center of the base's top face
- `translate: to: base.face_top` positions the tower at that anchor
- No manual coordinate calculation needed!

### Common Auto-Generated Anchors

Every part automatically provides these anchors:

| Anchor | Description |
|--------|-------------|
| `{part}.center` | Center of the part |
| `{part}.face_top` | Top face center |
| `{part}.face_bottom` | Bottom face center |
| `{part}.face_left` | Left face center |
| `{part}.face_right` | Right face center |
| `{part}.face_front` | Front face center |
| `{part}.face_back` | Back face center |

### Using Anchors with Offsets

You can add offsets to anchors:

```yaml
cap:
  primitive: cylinder
  parameters:
    radius: 5
    height: 3
  translate:
    from: tower.face_top
    offset: [0, 0, 5]  # 5 units above tower's top
```

**Think of it as**: "Start at the tower's top face anchor, then go 5 units up"

### Benefits of Anchors

1. **No coordinate math**: `to: base.face_top` instead of `[50, 50, 20]`
2. **Self-updating**: If you change `base_width`, anchors update automatically
3. **Readable**: Code clearly shows intent ("on top of base")
4. **Less error-prone**: No manual calculation mistakes

**See also**: [AUTO_REFERENCES_GUIDE.md](AUTO_REFERENCES_GUIDE.md) for complete anchor documentation

---

## Making a Bolt Circle

Now let's create a mounting plate with 6 bolt holes in a circle.

### Step 1: Full Example

Create `my_mounting_plate.yaml`:

```yaml
metadata:
  name: My Mounting Plate
  description: Circular bolt pattern mounting plate

parameters:
  # Plate dimensions
  plate_diameter: 150
  plate_thickness: 8

  # Bolt circle
  bolt_count: 6
  bolt_circle_diameter: 100
  bolt_diameter: 6.5  # M6 bolts

parts:
  plate:
    primitive: cylinder
    radius: '${plate_diameter / 2}'
    height: '${plate_thickness}'
    origin: center

  bolt_hole:
    primitive: cylinder
    radius: '${bolt_diameter / 2}'
    height: '${plate_thickness + 2}'
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

  # Subtract all bolt holes from plate
  finished_plate:
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

export:
  default_part: plate
```

### Step 2: Generate

```bash
tiacad build examples/my_mounting_plate.yaml
```

### Understanding Patterns

The `bolt_circle` operation creates 6 copies of `bolt_hole`:
- `bolt_circle_0`
- `bolt_circle_1`
- `bolt_circle_2`
- `bolt_circle_3`
- `bolt_circle_4`
- `bolt_circle_5`

Then we subtract all 6 from the plate.

### Pattern Types

**Circular Pattern** (what we just used):
```yaml
type: pattern
pattern: circular
count: 6                # How many
radius: 50              # Circle radius
axis: Z                 # Rotation axis
center: [0, 0, 0]       # Circle center
```

**Linear Pattern** (line or grid):
```yaml
type: pattern
pattern: linear
count: 5                # How many
spacing: 20             # Distance between
direction: X            # Which direction
```

**Grid Pattern** (2D array):
```yaml
type: pattern
pattern: grid
count_x: 4              # Columns
count_y: 3              # Rows
spacing_x: 20           # Column spacing
spacing_y: 25           # Row spacing
```

---

## Professional Finishing

Let's add rounded edges for safety and aesthetics.

### Step 1: Add Fillet Operation

Update your mounting plate YAML:

```yaml
metadata:
  name: Rounded Mounting Plate
  description: Professional mounting plate with filleted edges

parameters:
  plate_diameter: 150
  plate_thickness: 8
  bolt_count: 6
  bolt_circle_diameter: 100
  bolt_diameter: 6.5
  edge_fillet_radius: 2.0  # NEW!

parts:
  plate:
    primitive: cylinder
    radius: '${plate_diameter / 2}'
    height: '${plate_thickness}'
    origin: center

  bolt_hole:
    primitive: cylinder
    radius: '${bolt_diameter / 2}'
    height: '${plate_thickness + 2}'
    origin: center

operations:
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: '${bolt_count}'
    radius: '${bolt_circle_diameter / 2}'
    axis: Z
    center: [0, 0, 0]

  finished_plate:
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

  # NEW: Round the top edges
  rounded_plate:
    type: finishing
    finish: fillet
    input: plate  # Note: finishing modifies the part in-place
    radius: '${edge_fillet_radius}'
    edges:
      direction: Z  # Only top/bottom edges

export:
  default_part: plate
```

### Step 2: Generate

```bash
tiacad build examples/my_mounting_plate.yaml
```

The top edges are now beautifully rounded!

### Finishing Operations

**Fillet (round edges):**
```yaml
type: finishing
finish: fillet
input: my_part
radius: 2.0
edges: all  # or selective edges
```

**Chamfer (bevel edges):**
```yaml
type: finishing
finish: chamfer
input: my_part
length: 1.5
edges: all
```

**Edge Selection:**

```yaml
edges: all                    # All edges
edges: {direction: Z}         # Edges aligned with Z
edges: {parallel_to: X}       # Edges parallel to X
edges: {perpendicular_to: Y}  # Edges perpendicular to Y
```

---

## Common Mistakes & Solutions

### 1. Forgetting Rotation Origins

**Error:**
```yaml
rotate:
  axis: Z
  angle: 45
```

**Fix:** Always specify `origin`:
```yaml
rotate:
  axis: Z
  angle: 45
  origin: [0, 0, 0]  # REQUIRED!
```

### 2. Wrong Parameter Syntax

**Error:**
```yaml
size: [${width}, ${height}, ${thickness}]  # Missing quotes!
```

**Fix:** Quote expressions:
```yaml
size: ['${width}', '${height}', '${thickness}']
```

### 3. Forgetting Pattern Part Names

**Error:**
```yaml
operations:
  my_pattern:
    type: pattern
    count: 3

  # Tries to use "my_pattern" as a part
  result:
    base: plate
    subtract: [my_pattern]  # WRONG!
```

**Fix:** Use numbered pattern parts:
```yaml
subtract:
  - my_pattern_0
  - my_pattern_1
  - my_pattern_2
```

### 4. Transform Order Confusion

Transforms apply top-to-bottom:

```yaml
# Move THEN rotate (usually what you want)
transforms:
  - translate: [10, 0, 0]
  - rotate: {axis: Z, angle: 90, origin: [0,0,0]}

# Rotate THEN move (different result!)
transforms:
  - rotate: {axis: Z, angle: 90, origin: [0,0,0]}
  - translate: [10, 0, 0]
```

---

## Quick Reference Card

### Basic Structure

```yaml
metadata:
  name: My Design

parameters:
  size: 100

parts:
  my_part:
    primitive: box
    size: [...]

operations:
  my_operation:
    type: boolean
    ...

export:
  default_part: final_part
```

### Primitives

```yaml
box:         size: [x, y, z]
cylinder:    radius: r, height: h
sphere:      radius: r
cone:        radius: r, height: h
```

### Operations

```yaml
# Boolean
type: boolean
operation: union | difference | intersection

# Pattern
type: pattern
pattern: linear | circular | grid

# Finishing
type: finishing
finish: fillet | chamfer
```

### Axes

```yaml
X  or  [1, 0, 0]
Y  or  [0, 1, 0]
Z  or  [0, 0, 1]
```

---

## Practice Exercises

Try building these on your own:

### Exercise 1: Simple Bracket

Create an L-shaped bracket (two boxes joined at 90 degrees).

**Hints:**
- Create two box parts
- Use `translate` to position the vertical part
- Use `boolean union` to join them

### Exercise 2: Grid of Holes

Create a plate with a 4x4 grid of evenly spaced holes.

**Hints:**
- Use `pattern: grid`
- `count_x: 4, count_y: 4`
- Subtract all 16 holes (hole_grid_0_0 through hole_grid_3_3)

### Exercise 3: Chamfered Box

Create a box with all edges chamfered (beveled).

**Hints:**
- Create a box
- Use `type: finishing, finish: chamfer`
- `edges: all`

---

## Real-World Example Walkthrough

Let's analyze one of the included examples: `rounded_mounting_plate.yaml`

### What It Creates

A professional 150x150mm mounting plate with:
- 6 bolt holes in a 100mm diameter circle (M6 size)
- Center hole (40mm diameter)
- Rounded top edges (2mm radius) for safety

### The Code Structure

```yaml
metadata:  # Documentation
  name: Rounded Mounting Plate with Filleted Edges
  ...

parameters:  # Configurable values
  plate_width: 150
  bolt_count: 6
  edge_fillet_radius: 2.0
  ...

parts:  # Basic building blocks
  plate:           # Main plate
    primitive: box
    ...

  bolt_hole:       # Hole template (will be patterned)
    primitive: cylinder
    ...

  center_hole:     # Center hole
    primitive: cylinder
    ...

operations:  # Combine and modify
  bolt_circle:     # Pattern: 6 holes in circle
    type: pattern
    pattern: circular
    ...

  plate_with_holes:  # Boolean: subtract holes
    type: boolean
    operation: difference
    ...

  finished_plate:  # Finishing: round edges
    type: finishing
    finish: fillet
    ...

export:  # Output
  default_part: plate_with_holes
```

### Why This Design Is Good

1. **Parametric**: Change any dimension easily
2. **Reusable**: Template for similar plates
3. **Professional**: Rounded edges prevent injuries
4. **Manufacturable**: Exports to STL for CNC or 3D printing

---

## Debugging Tips

### Enable Verbose Output

```bash
tiacad build examples/my_file.yaml --verbose
```

### Check Individual Parts

Export intermediate parts to see what's happening:

```yaml
export:
  default_part: intermediate_part  # Before the final operation
```

### Start Simple

Build complex models incrementally:
1. Create basic parts → export → verify
2. Add one operation → export → verify
3. Add next operation → export → verify
4. Continue until complete

### Read Error Messages

TiaCAD provides helpful errors:

```
Error: Part 'unknown_part' not found in operation 'my_operation'
Available parts: plate, hole, bracket
```

This tells you:
- What went wrong
- Where it happened
- What's actually available

---

## Next Steps

### Learn More

- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Complete language reference
- [EXAMPLES_GUIDE.md](EXAMPLES_GUIDE.md) - Detailed example walkthroughs
- [README.md](README.md) - Project overview and architecture

### Try the Examples

```bash
# Simple box
tiacad build examples/simple_box.yaml

# Guitar hanger (transforms)
tiacad build examples/simple_guitar_hanger.yaml

# Mounting plate (patterns)
tiacad build examples/mounting_plate_with_bolt_circle.yaml

# Rounded plate (finishing)
tiacad build examples/rounded_mounting_plate.yaml

# L-bracket (chamfer)
tiacad build examples/chamfered_bracket.yaml
```

### Build Real Projects

Use TiaCAD for:
- 3D printer parts
- CNC projects
- Prototyping
- Mechanical assemblies
- Enclosures and brackets
- Custom mounting hardware

### Get Help

- Review test files in `tiacad_core/tests/test_parser/` for usage examples
- Check session summaries in `/home/scottsen/src/tia/sessions/` for development history
- Read the comprehensive test suite for edge cases and patterns

---

## Congratulations!

You've learned:
- ✅ How to create YAML CAD files
- ✅ How to use parameters and expressions
- ✅ How to create holes with boolean operations
- ✅ How to make patterns (linear, circular, grid)
- ✅ How to add professional finishing (fillet, chamfer)

You're now ready to create professional parametric CAD models in YAML!

---

**Happy Modeling!** 🎨

---

**Version:** 0.2.0
**Last Updated:** 2025-10-25
**Status:** Phase 2 Complete
**Next:** Try the practice exercises or explore the real examples!
