# TiaCAD Glossary

**Purpose**: This glossary defines TiaCAD-specific terminology and explains how it differs from traditional CAD tools and procedural modeling systems.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [TiaCAD vs Traditional CAD](#tiacad-vs-traditional-cad)
3. [TiaCAD vs Procedural Tools](#tiacad-vs-procedural-tools)
4. [Spatial Concepts](#spatial-concepts)
5. [Operation Types](#operation-types)
6. [Technical Terms](#technical-terms)

---

## Core Concepts

### Part

**What it means in TiaCAD**: A geometric object defined in the `parts:` section - can be a primitive (box, cylinder, sphere, cone) or an imported shape.

**What it is NOT**: In TiaCAD, "part" does NOT mean "final manufactured component" like in traditional manufacturing. It's simply a geometric shape that may be combined with others.

**Example**:
```yaml
parts:
  base:           # This is a "part" (a box primitive)
    primitive: box
    parameters: {width: 100, height: 20, depth: 50}
```

**Think of it as**: A LEGO brick - a building block that may be combined with others to create something larger.

**See also**: Shape, Element (these are clearer terms but not currently used in TiaCAD)

---

### Anchor (Reference Point)

**What it means in TiaCAD**: A spatial location with position and optional orientation, used to position parts relative to each other. Internally called `SpatialRef` or listed in the `references:` section.

**Why "anchor"?**: Like a ship's anchor marks a specific spot, spatial anchors mark positions where parts can be attached or positioned.

**Example**:
```yaml
references:
  mounting_point:        # This is an "anchor"
    type: point
    from: base.face_top
    offset: [0, 0, 5]
```

**Auto-generated anchors**: Every part automatically provides anchors:
- `{part}.center` - Center of bounding box
- `{part}.face_top` - Top face center
- `{part}.face_bottom` - Bottom face center
- `{part}.origin` - Part's origin point (0,0,0)

**Visual Guide**: See [auto-generated anchor Visualization](docs/diagrams/auto-generated anchor-visualization.md) for a complete visual reference.

**Think of it as**: Marking spots on a workbench with tape - "this is where the bracket goes"

**Traditional CAD equivalent**: Mate point, attachment point, reference geometry

---

### Reference-Based Composition

**What it means**: TiaCAD's core design philosophy where parts are independent and positioned using spatial anchors, rather than nested in hierarchical assemblies.

**Key characteristics**:
- Parts are peers (no parent-child relationships)
- Position is specified using anchors
- No implicit containment or ownership

**Example**:
```yaml
parts:
  base: [...]
  tower: [...]
    translate:
      to: base.face_top  # Reference to an anchor, not to "base" itself
```

**Think of it as**: Arranging furniture in a room using a floor plan with marked positions, rather than building nested boxes.

**Visual Guide**: See [Reference-Based vs Hierarchical](docs/diagrams/reference-based-vs-hierarchical.md) for a detailed comparison.

**Contrast**: Traditional CAD uses hierarchical assemblies (Assembly → Sub-assembly → Part)

---

### Operation

**What it means**: A transformation, modification, or combination applied to parts or sketches.

**Four categories**:
1. **Positioning operations** (transforms) - Move/rotate parts
2. **Shape modifications** (features) - Change geometry (fillet, chamfer)
3. **Combining operations** (booleans) - Merge or subtract parts
4. **Replication operations** (patterns) - Create multiple copies

**Visual Guide**: See [Operation Categories](docs/diagrams/operation-categories.md) for detailed examples and decision tree.

**Example**:
```yaml
operations:
  rounded_bracket:
    type: boolean
    operation: union
    base: bracket
    add: [reinforcement]
```

**Think of it as**: Instructions for what to do with the parts - like assembly instructions.

**See also**: [Operation Types](#operation-types) for detailed breakdown

---

### Parameter

**What it means**: A named value that can be used throughout the YAML file, supports mathematical expressions.

**Purpose**: Makes designs flexible and maintainable - change one value to update many dimensions.

**Example**:
```yaml
parameters:
  width: 100
  height: '${width / 2}'     # Expression (evaluated to 50)
  depth: '${width * 0.75}'   # Expression (evaluated to 75)

parts:
  box:
    primitive: box
    parameters:
      width: '${width}'       # References parameter
      height: '${height}'
      depth: '${depth}'
```

**Think of it as**: Variables in a spreadsheet - change the input cell and dependent cells update automatically.

**Traditional CAD equivalent**: Design parameters, dimensions, constraints

---

### Sketch

**What it means**: A 2D profile drawn on a plane, used as input for operations like extrude, revolve, sweep, or loft.

**Example**:
```yaml
sketches:
  bracket_profile:
    plane: XY
    origin: [0, 0, 0]
    shapes:
      - type: rectangle
        width: 50
        height: 20
```

**Think of it as**: Drawing on graph paper before cutting with scissors - the 2D outline before making it 3D.

**Traditional CAD equivalent**: Sketch, profile, section

---

## TiaCAD vs Traditional CAD

### Assembly (Traditional CAD) ↔ Document (TiaCAD)

| Traditional CAD | TiaCAD |
|-----------------|--------|
| Assembly file (.asm) | YAML file (.yaml) |
| Contains sub-assemblies and parts | Contains parts and references |
| Hierarchical structure | Flat structure with anchors |
| Parts "belong to" assemblies | All parts are independent |

**Example Traditional CAD (concept)**:
```
Assembly: GuitarHanger
├── Sub-Assembly: MountingSystem
│   ├── Part: BackPlate
│   └── Part: Bracket
└── Sub-Assembly: HookSystem
    ├── Part: LeftArm
    └── Part: RightArm
```

**Example TiaCAD**:
```yaml
parts:
  back_plate: [...]
  bracket: [...]
  left_arm: [...]
  right_arm: [...]
# All are peers - no hierarchy
```

---

### Mate (Traditional CAD) ↔ Translate to Anchor (TiaCAD)

| Traditional CAD | TiaCAD |
|-----------------|--------|
| Mate constraint | `translate: to: anchor` |
| "Mate face A to face B" | "Position at anchor" |
| Bidirectional relationship | Unidirectional reference |
| Can fail if over-constrained | Always well-defined |

**Traditional CAD concept**: "Mate the bracket's bottom face to the plate's top face"

**TiaCAD equivalent**:
```yaml
bracket:
  translate:
    to: plate.face_top  # Position bracket at plate's top face anchor
```

---

### Sub-Assembly (Traditional CAD) ↔ Named Reference (TiaCAD)

**Traditional CAD**: Group parts into sub-assemblies for organization

**TiaCAD**: Use named references to represent conceptual groups

```yaml
references:
  hook_system_position:    # Conceptual "sub-assembly" location
    type: point
    from: base.face_front
    offset: [0, 50, 0]

parts:
  left_arm:
    translate: hook_system_position
  right_arm:
    translate: hook_system_position
```

**Note**: TiaCAD doesn't have formal sub-assemblies, but named references can represent them conceptually.

---

## TiaCAD vs Procedural Tools

### OpenSCAD (Procedural) ↔ TiaCAD (Declarative)

| OpenSCAD | TiaCAD |
|----------|--------|
| Step-by-step instructions | Describe desired result |
| Execution order critical | Declaration order flexible |
| Imperative style | Declarative style |
| `translate([x,y,z])` | `translate: to: anchor` |
| Manual coordinate math | Auto-generated anchors |

**OpenSCAD Example** (procedural):
```openscad
// Step 1: Create base
cube([100, 50, 20], center=true);

// Step 2: Move up and create tower
translate([0, 0, 30])  // Manual calculation: 20/2 + 40/2
  cube([20, 20, 40], center=true);
```

**TiaCAD Equivalent** (declarative):
```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, depth: 50, height: 20}

  tower:
    primitive: box
    parameters: {width: 20, depth: 20, height: 40}
    translate:
      to: base.face_top  # No manual calculation!
```

---

### Execution Order

**OpenSCAD**: Order matters - operations execute sequentially

```openscad
translate([10, 0, 0])
  rotate([0, 0, 45])
    cube([10, 10, 10]);  // Different from rotate-then-translate!
```

**TiaCAD**: Declaration order *mostly* flexible, but transforms within a part are sequential

```yaml
parts:
  box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    transforms:
      - translate: [10, 0, 0]
      - rotate: {axis: Z, angle: 45}
      # Sequential: translate THEN rotate
```

---

## Spatial Concepts

### Face

**What it means**: A flat surface of a solid. In TiaCAD, faces can be selected and used as anchors.

**Face anchors** (auto-generated):
- `.face_top` - Top face (max Z)
- `.face_bottom` - Bottom face (min Z)
- `.face_left` - Left face (min X)
- `.face_right` - Right face (max X)
- `.face_front` - Front face (max Y)
- `.face_back` - Back face (min Y)

**Each face anchor includes**:
- Position: Center point of the face
- Normal: Vector pointing outward from the face

**Example**:
```yaml
pillar:
  translate:
    to: base.face_top  # Position at center of top face
```

**Think of it as**: The flat side of a box - each side is a face.

---

### Normal (Vector)

**What it means**: A vector pointing perpendicular (at 90°) to a surface, indicating its orientation.

**Why it matters**: Normals are used for intelligent positioning - when you place something on a face, it knows which way is "up" relative to that face.

**Example**:
- Top face of a box: normal = [0, 0, 1] (pointing up)
- Front face of a box: normal = [0, 1, 0] (pointing forward)

**Think of it as**: An arrow sticking out of a surface showing which way is "outward".

---

### Local Frame

**What it means**: Each anchor has its own local frame (X, Y, Z axes) oriented relative to the geometry.

**Why it matters**: Offsets are applied in the local frame, not world space.

**Example**:
```yaml
hook:
  translate:
    from: wall.face_front      # Face pointing in +Y direction
    offset: [0, 10, 0]         # 10 units in local Y (away from wall)
```

**Without local frames**: You'd need to calculate world space manually.

**Think of it as**: Each surface has its own "up", "forward", and "sideways" directions.

---

### Offset

**What it means**: An offset from an anchor position, specified in the anchor's local local frame.

**Format**: `[x, y, z]` where:
- x: left/right
- y: forward/back
- z: up/down
(Relative to the anchor's local frame)

**Example**:
```yaml
references:
  mounting_hole:
    from: plate.face_top
    offset: [15, 0, 5]  # 15 right, 0 forward, 5 up (in plate's local frame)
```

**Think of it as**: "From this spot, go 15mm right, 0mm forward, and 5mm up"

---

## Operation Types

TiaCAD operations fall into four categories, each with different purposes:

### 1. Positioning Operations (Transforms)

**What they do**: Change position or orientation WITHOUT modifying geometry.

**Operations**: `translate`, `rotate`, `align_to_face`

**Example**:
```yaml
tower:
  primitive: box
  parameters: {width: 20, height: 40, depth: 20}
  translate:
    to: base.face_top  # Positioning operation
```

**Think of it as**: Moving chess pieces on a board - the pieces don't change shape.

**Key insight**: These operations affect WHERE the part is, not WHAT it looks like.

---

### 2. Shape Modifications (Features)

**What they do**: Change the geometry itself - add or remove material.

**Operations**: `fillet`, `chamfer`, `extrude`, `revolve`, `sweep`, `loft`

**Example**:
```yaml
operations:
  rounded_box:
    type: fillet
    targets: [box]
    edges:
      selector: ">Z"
      mode: all
    radius: 2
```

**Think of it as**: Shaping clay - rounding edges, cutting profiles, etc.

**Key insight**: These operations affect WHAT the part looks like, not where it is.

---

### 3. Combining Operations (Booleans)

**What they do**: Create relationships between parts - merge, subtract, or find overlap.

**Operations**: `union` (combine), `difference` (subtract), `intersection` (overlap)

**Example**:
```yaml
operations:
  bracket_with_hole:
    type: boolean
    operation: difference
    base: bracket
    subtract: [hole]
```

**Think of it as**: Adding or removing material - like welding parts together or drilling holes.

**Key insight**: These operations create NEW geometry from existing parts.

---

### 4. Replication Operations (Patterns)

**What they do**: Create multiple copies of a part arranged in a pattern.

**Operations**: `linear_pattern` (line), `circular_pattern` (circle), `grid_pattern` (2D grid)

**Example**:
```yaml
operations:
  bolt_circle:
    type: pattern
    pattern: circular
    target: hole
    name: bolt_hole
    center: [0, 0, 0]
    axis: Z
    count: 8
```

**Think of it as**: Using a stamp or cookie cutter repeatedly.

**Key insight**: Pattern operations create named copies (`bolt_hole_0`, `bolt_hole_1`, etc.).

---

## Technical Terms

These terms appear in code, error messages, or advanced documentation:

### SpatialRef

**Technical term for**: Anchor / Reference Point

**What it is**: Internal data structure representing a position with optional orientation.

**Structure**:
```python
@dataclass
class SpatialRef:
    position: np.ndarray        # 3D coordinates [x, y, z]
    orientation: Optional[...]  # Normal vector (for faces)
    ref_type: str              # 'point', 'face', 'edge', 'axis'
```

**User-facing term**: "anchor" or "reference point"

**You'll see this**: In error messages, architecture docs, or code comments

---

### SpatialResolver

**What it is**: Internal system that resolves reference names to actual coordinates.

**What it does**:
- Converts `base.face_top` → 3D position + normal
- Handles reference chains (`ref_a` → `ref_b` → `ref_c`)
- Manages local frame transformations

**User-facing concept**: "The system that figures out where anchors are"

**You'll see this**: In error messages about reference resolution failures

---

### Geometry Backend

**What it is**: Abstraction layer between TiaCAD and the underlying CAD kernel (CadQuery).

**Why it exists**: Allows testing without full CAD system, potential future support for other kernels.

**Implementations**:
- `CadQueryBackend` - Real 3D geometry using CadQuery
- `MockBackend` - Fast testing without actual geometry

**User-facing concept**: "The 3D engine"

---

### Schema Validation

**What it is**: Automatic checking of YAML files against expected structure.

**What it does**:
- Validates required fields exist
- Checks data types (numbers vs strings)
- Ensures referenced parts exist
- Validates parameter expressions

**Example error**:
```
ValidationError: Unknown part reference 'tower' in operation 'place_tower'
```

**Think of it as**: Spell-checker for your YAML files - catches mistakes before building.

---

### Origin Mode

**What it is**: Specifies where a primitive's origin (0,0,0) is located relative to the shape.

**Options**:
- `center` - Origin at geometric center (default for box, sphere)
- `bottom` - Origin at bottom center (default for cylinder, cone)
- `corner` - Origin at corner (min X, min Y, min Z)

**Example**:
```yaml
box:
  primitive: box
  parameters: {width: 10, height: 10, depth: 10}
  origin: center  # Origin at center of box
```

**Why it matters**: Affects how transforms (rotate, translate) behave.

---

## Common Confusion Points

### "Part" vs "Primitive"

**Question**: Is there a difference?

**Answer**: In TiaCAD YAML, they're used interchangeably:
```yaml
parts:
  box1:
    primitive: box  # "primitive" specifies the type
```

**More precisely**:
- **Primitive**: The type (box, cylinder, sphere, cone)
- **Part**: The instance with specific parameters

**Think of it as**: "Primitive" = recipe, "Part" = the baked cake

---

### "Reference" vs "Anchor"

**Question**: Are these the same thing?

**Answer**: Yes! "Anchor" is the user-friendly term for what's technically called a "reference" or "SpatialRef" in code.

**Usage**:
- `references:` section in YAML (technical term)
- "spatial anchor" in documentation (user-friendly term)
- `SpatialRef` in code (internal term)

---

### "Operation" vs "Transform"

**Question**: What's the difference?

**Answer**:
- **Transform** is a specific TYPE of operation (translate, rotate)
- **Operation** is the broader category including transforms, booleans, patterns, features

**Analogy**:
- Operation = "action"
- Transform = "moving" (a specific type of action)

---

### auto-generated anchors vs Named References

**Question**: When do I use which?

**Answer**:

**auto-generated anchors** (use when):
- Simple positioning (put this on top of that)
- Common attachment points (face centers, part center)
- Don't need custom offsets

```yaml
tower:
  translate:
    to: base.face_top  # auto-generated anchor
```

**Named references** (use when):
- Complex positioning logic
- Need to reuse a reference point
- Multiple parts share the same anchor
- Custom offsets or calculations

```yaml
references:
  tower_position:
    from: base.face_top
    offset: [10, 0, 5]

tower_a:
  translate: tower_position

tower_b:
  translate: tower_position
```

---

## Quick Reference: Term Translations

| If you're looking for... | In TiaCAD, that's called... | Section in YAML |
|--------------------------|----------------------------|-----------------|
| Variables | Parameters | `parameters:` |
| Assembly | YAML Document | (whole file) |
| Sub-assembly | Named reference | `references:` |
| Mate / Constraint | Translate to anchor | `translate: to:` |
| Attachment point | Anchor / Reference | `references:` |
| Face center | auto-generated anchor | `.face_top` |
| Part center | auto-generated anchor | `.center` |
| Combine parts | Boolean union | `operations:` |
| Cut hole | Boolean difference | `operations:` |
| Round edge | Fillet | `operations:` |
| Copy in pattern | Pattern operation | `operations:` |
| 2D sketch | Sketch | `sketches:` |
| Extrude sketch | Extrude operation | `operations:` |

---

## Learning Path: Understanding TiaCAD's Model

1. **Start here**: Read "TiaCAD's Design Philosophy" in README.md
2. **Learn the basics**: Work through TUTORIAL.md
3. **Understand anchors**: Read AUTO_REFERENCES_GUIDE.md
4. **See examples**: Study examples/ directory
5. **Reference**: Use YAML_REFERENCE.md as needed
6. **Deep dive**: Read ARCHITECTURE_DECISION_V3.md (technical)

---

## Getting Help

**If you're confused about**:
- **A term**: Check this glossary
- **Syntax**: See YAML_REFERENCE.md
- **How to do something**: See TUTORIAL.md or EXAMPLES_GUIDE.md
- **Why something works this way**: See docs/ARCHITECTURE_DECISION_V3.md

**If you find missing or confusing terms**: Please contribute! This glossary is a living document.

---

**Last updated**: 2025-11-13
**Version**: 1.0
**See also**: [YAML_REFERENCE.md](YAML_REFERENCE.md), [AUTO_REFERENCES_GUIDE.md](AUTO_REFERENCES_GUIDE.md), [TUTORIAL.md](TUTORIAL.md)
