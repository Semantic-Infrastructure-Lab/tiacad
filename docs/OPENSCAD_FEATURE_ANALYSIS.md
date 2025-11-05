# OpenSCAD Feature Analysis for TiaCAD Enhancement

**Date**: 2025-10-31
**Session**: kinetic-abyss-1031
**Author**: TIA Analysis Team

## Executive Summary

This document analyzes OpenSCAD's features and capabilities to identify opportunities for enhancing TiaCAD. Through web research and comparative analysis, we've identified 10 high-value features that could significantly expand TiaCAD's capabilities while maintaining its declarative, YAML-based philosophy.

**Key Findings:**
- OpenSCAD has 8 critical features TiaCAD should adopt
- TiaCAD has 5 unique strengths to preserve and enhance
- Recommended implementation order prioritizes text operations, hull, and customizer GUI
- Total estimated development: 35-50 days for full feature parity

---

## Table of Contents

1. [Core Philosophy Comparison](#core-philosophy-comparison)
2. [Feature Comparison Matrix](#feature-comparison-matrix)
3. [Recommended Features to Port](#recommended-features-to-port)
4. [Implementation Roadmap](#implementation-roadmap)
5. [TiaCAD's Unique Strengths](#tiacads-unique-strengths)
6. [Technical Implementation Notes](#technical-implementation-notes)

---

## Core Philosophy Comparison

### OpenSCAD: Imperative Programming Model

**Characteristics:**
- Script-based approach resembling C/Java/Python syntax
- Functional programming philosophy with immutable variables
- Code-centric workflow: operations written as procedural functions
- CSG-first approach (Constructive Solid Geometry)
- Direct execution model where order of statements matters

**Example OpenSCAD Code:**
```openscad
cylinder(h=10, r=5);
translate([0, 0, 10])
  sphere(r=5);
difference() {
  cube([20, 20, 20]);
  cylinder(h=25, r=3);
}
```

**Strengths:**
- Familiar to programmers
- Powerful for algorithmic/generative design
- Loops and conditionals are natural
- Large existing codebase and community

**Weaknesses:**
- Steep learning curve for non-programmers
- Order-dependent (implicit state)
- Harder to version control (code vs. data)
- Limited IDE support
- Difficult to create parametric templates for end users

### TiaCAD: Declarative Data Model

**Characteristics:**
- YAML-based, data-driven design philosophy
- Clear separation between data (design) and execution (engine)
- Design-centric workflow: define what you want, not how to build it
- Explicit origin system (no implicit transformations)
- Graph-based execution model

**Example TiaCAD YAML:**
```yaml
parameters:
  height: 20
  radius: 5

parts:
  base:
    primitive: cylinder
    height: ${height}
    radius: ${radius}
    origin: center

  top:
    primitive: sphere
    radius: ${radius}
    origin: center

operations:
  assembly:
    type: transform
    input: top
    transforms:
      - translate: [0, 0, ${height}]
```

**Strengths:**
- Intuitive for designers and engineers
- Excellent version control (structured data)
- Easy to generate/modify programmatically
- Clear parameter system
- Self-documenting structure
- Easy to validate (JSON Schema)

**Weaknesses:**
- Less flexible for complex algorithmic designs
- Requires engine implementation for each feature
- YAML syntax can be verbose

### Philosophy Summary

**OpenSCAD** excels at **algorithmic design** - when you need loops, conditionals, and computational geometry.

**TiaCAD** excels at **parametric design** - when you need clear, maintainable, shareable designs with explicit parameters.

**Key Insight**: These are complementary approaches, not competitive. TiaCAD can learn specific features from OpenSCAD while maintaining its declarative advantage.

---

## Feature Comparison Matrix

| Feature | OpenSCAD | TiaCAD | Winner | Priority |
|---------|----------|--------|--------|----------|
| **Basic Primitives** | ✅ 2D + 3D | ✅ 3D (sketches for 2D) | Tie | - |
| **Boolean Operations** | ✅ union/diff/intersect | ✅ union/diff/intersect | Tie | - |
| **Linear Extrusion** | ✅ native | ✅ extrude | Tie | - |
| **Rotational Extrusion** | ✅ rotate_extrude | ✅ revolve | Tie | - |
| **Sweep Operations** | ❌ (via libraries) | ✅ native sweep | **TiaCAD** | - |
| **Loft Operations** | ❌ (limited) | ✅ native loft | **TiaCAD** | - |
| **Pattern Operations** | ❌ (manual loops) | ✅ linear/circular/grid | **TiaCAD** | - |
| **Fillet Operations** | ❌ (very limited) | ✅ full support | **TiaCAD** | - |
| **Chamfer Operations** | ❌ (manual) | ✅ full support | **TiaCAD** | - |
| **Materials System** | ❌ | ✅ full library | **TiaCAD** | - |
| **Multi-material Export** | ❌ | ✅ 3MF support | **TiaCAD** | - |
| **Advanced Color System** | ⚠️ basic | ✅ full HSL/RGB/named | **TiaCAD** | - |
| **Text/Engraving** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐⭐⭐ |
| **Minkowski Sum** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐⭐ |
| **Hull Operation** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐⭐ |
| **2D Offset** | ✅ offset() | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐ |
| **Shell/Hollow** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐ |
| **DXF Import** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐ |
| **SVG Import** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐ |
| **STL Import** | ✅ native | ❌ not implemented | **OpenSCAD** | ⭐⭐ |
| **Customizer GUI** | ✅ full support | ❌ not implemented | **OpenSCAD** | ⭐⭐⭐⭐⭐ |
| **Animation Support** | ✅ $t variable | ❌ not implemented | **OpenSCAD** | ⭐⭐ |

**Summary:**
- **TiaCAD wins**: 8 features (loft, sweep, patterns, fillets, chamfers, materials, multi-material, colors)
- **OpenSCAD wins**: 10 features (text, minkowski, hull, offset, shell, imports, customizer, animation)
- **Tie**: 5 features (basic operations both systems support well)

---

## Recommended Features to Port

### 1. Text/Engraving Operations ⭐⭐⭐⭐⭐

**Priority**: CRITICAL
**Estimated Effort**: 2-3 days
**Difficulty**: Low-Medium

#### Why This Feature?

Text operations are **essential** for real-world CAD:
- Product labels and branding
- Part numbers and identifiers
- Instructions and warnings
- Decorative engraving
- Accessibility labels (Braille, large print)

Every practical design eventually needs text. This is a fundamental gap in TiaCAD.

#### OpenSCAD Implementation

```openscad
// OpenSCAD text syntax
text("Made with Love",
     size=10,
     font="Liberation Sans:style=Bold",
     halign="center",
     valign="baseline");

// Extruded text
linear_extrude(height=2)
  text("DANGER", size=20);
```

#### Proposed TiaCAD Syntax

**Option A: Text as Sketch Shape**
```yaml
sketches:
  label_text:
    plane: XY
    origin: [0, 0, 0]
    shapes:
      - type: text
        text: "Made with TiaCAD"
        size: 10
        font: "Liberation Sans"
        style: "Bold"
        halign: center
        valign: baseline

operations:
  label_3d:
    type: extrude
    sketch: label_text
    distance: 2
    direction: Z
```

**Option B: Text as Operation**
```yaml
operations:
  engraved_label:
    type: text
    text: "${product_name} v${version}"
    position: [0, 0, 0]
    plane: XY
    size: 10
    height: 2  # Extrusion depth
    font: "Liberation Sans"
    style: "Bold"
    halign: center
    valign: baseline
```

**Option C: Text as Part Primitive**
```yaml
parts:
  warning_label:
    primitive: text
    text: "⚠ HIGH VOLTAGE ⚠"
    size: 8
    height: 1.5
    font: "Liberation Sans"
    origin: [0, 0, 0]
    plane: XY
```

**Recommendation**: Implement **Option A** (text as sketch shape) first for consistency with existing architecture, then add Option B as convenience syntax.

#### Implementation Details

**CadQuery Support:**
```python
# CadQuery has native text support
result = (
    cq.Workplane("XY")
    .text("Hello", 10, 2.0,
          font="Liberation Sans",
          fontPath="/usr/share/fonts/",
          halign="center",
          valign="center")
)
```

**Technical Tasks:**
1. Add `text` shape type to sketch parser
2. Map TiaCAD text params to CadQuery text() method
3. Handle font discovery (system fonts + custom fonts)
4. Support Unicode/international characters
5. Add font validation to schema
6. Create text operation tests
7. Document text capabilities and font requirements

**Font Handling:**
- System fonts: Auto-discover from standard paths
- Custom fonts: Support `font_path` parameter
- Fallback: Default to "Liberation Sans" (open source, widely available)
- Validation: Check font exists before rendering

**Parameters:**
- `text`: String (supports parameters: `"${part_name}"`)
- `size`: Font size in mm
- `font`: Font family name
- `style`: Regular, Bold, Italic, Bold Italic
- `halign`: left, center, right
- `valign`: baseline, bottom, center, top
- `spacing`: Character spacing multiplier (default: 1.0)

**Edge Cases:**
- Empty strings → error
- Missing fonts → fallback + warning
- Unicode characters → ensure UTF-8 encoding
- Very small text → minimum size warning

#### Examples

**Product Label:**
```yaml
parameters:
  product_name: "Widget Pro"
  model_number: "WP-2025"

sketches:
  label:
    plane: XY
    origin: [0, 0, 0]
    shapes:
      - type: text
        text: "${product_name}"
        size: 12
        font: "Liberation Sans"
        style: "Bold"
        halign: center
      - type: text
        text: "Model: ${model_number}"
        size: 6
        font: "Liberation Sans"
        halign: center

operations:
  label_plate:
    type: extrude
    sketch: label
    distance: 1
```

**Engraved Warning:**
```yaml
operations:
  warning:
    type: text
    text: "⚠ WARNING ⚠"
    position: [0, 0, 10]
    plane: XZ
    size: 8
    height: -0.5  # Negative = engrave into surface
    font: "Liberation Sans"
    style: "Bold"
    halign: center
```

---

### 2. Hull Operation ⭐⭐⭐⭐

**Priority**: HIGH
**Estimated Effort**: 3-5 days
**Difficulty**: Medium-High

#### Why This Feature?

Hull creates the **convex hull** around a set of shapes - essentially shrink-wrapping them. This enables:

- **Organic enclosures** around irregular components
- **Smooth fairings** for aerodynamics
- **Structural reinforcement** connecting multiple points
- **Boat hulls** and aircraft fuselages
- **Protective covers** that conform to complex shapes

Hull is a **unique capability** that distinguishes advanced CAD from basic modeling.

#### OpenSCAD Implementation

```openscad
// Hull around multiple objects
hull() {
  translate([0, 0, 0]) cylinder(h=1, r=5);
  translate([20, 0, 0]) cylinder(h=1, r=5);
  translate([10, 20, 0]) cylinder(h=1, r=5);
}
// Creates smooth triangular shape connecting the cylinders
```

#### Proposed TiaCAD Syntax

```yaml
parts:
  mounting_post_1:
    primitive: cylinder
    height: 10
    radius: 5
    origin: [0, 0, 0]

  mounting_post_2:
    primitive: cylinder
    height: 10
    radius: 5
    origin: [50, 0, 0]

  mounting_post_3:
    primitive: cylinder
    height: 10
    radius: 5
    origin: [25, 40, 0]

operations:
  enclosure_hull:
    type: hull
    inputs:
      - mounting_post_1
      - mounting_post_2
      - mounting_post_3

  # Optional: Hollow version
  enclosure_shell:
    type: boolean
    operation: difference
    base: enclosure_hull
    subtract:
      - interior_cavity
```

#### Implementation Details

**Challenge**: CadQuery doesn't have native hull operation.

**Solution Approaches:**

**Approach 1: scipy.spatial.ConvexHull (Recommended)**
```python
from scipy.spatial import ConvexHull
import cadquery as cq

def compute_hull(shapes):
    # 1. Extract vertices from all shapes
    vertices = []
    for shape in shapes:
        vertices.extend(extract_vertices(shape))

    # 2. Compute convex hull
    hull = ConvexHull(vertices)

    # 3. Build solid from hull faces
    faces = []
    for simplex in hull.simplices:
        face_vertices = [vertices[i] for i in simplex]
        faces.append(face_vertices)

    # 4. Create CadQuery solid from faces
    return cq.Solid.makeSolid(cq.Shell.makeShell(faces))
```

**Approach 2: Trimesh Library**
```python
import trimesh

def compute_hull_trimesh(shapes):
    # Convert CadQuery shapes to meshes
    meshes = [shape_to_trimesh(s) for s in shapes]

    # Concatenate all meshes
    combined = trimesh.util.concatenate(meshes)

    # Compute convex hull
    hull_mesh = combined.convex_hull

    # Convert back to CadQuery
    return trimesh_to_cadquery(hull_mesh)
```

**Approach 3: PyMesh (Most Robust)**
```python
import pymesh

def compute_hull_pymesh(shapes):
    mesh = combine_to_pymesh(shapes)
    hull = pymesh.convex_hull(mesh)
    return pymesh_to_cadquery(hull)
```

**Recommendation**: Start with **scipy approach** (pure Python, no extra deps), fall back to Trimesh if needed.

**Technical Tasks:**
1. Implement vertex extraction from CadQuery solids
2. Integrate scipy.spatial.ConvexHull
3. Build CadQuery solid from convex hull
4. Handle degenerate cases (coplanar points, etc.)
5. Optimize for performance (large vertex sets)
6. Add hull operation to operation parser
7. Create comprehensive tests
8. Document use cases and limitations

**Edge Cases:**
- Single input → return original shape
- Two inputs → create hull between them
- Coplanar points → return 2D hull (error? or extrude?)
- Empty inputs → error
- Very large meshes → performance warning

#### Use Cases & Examples

**Example 1: Organic Enclosure**
```yaml
# Enclosure around four mounting posts
operations:
  mounting_hull:
    type: hull
    inputs:
      - corner_post_1
      - corner_post_2
      - corner_post_3
      - corner_post_4
```

**Example 2: Aerodynamic Fairing**
```yaml
# Smooth fairing between cockpit and tail
operations:
  fuselage_fairing:
    type: hull
    inputs:
      - cockpit_section
      - tail_section
```

**Example 3: Cable Routing**
```yaml
# Smooth cable guide connecting waypoints
parts:
  waypoint_1:
    primitive: sphere
    radius: 2
    origin: [0, 0, 0]

  waypoint_2:
    primitive: sphere
    radius: 2
    origin: [20, 10, 5]

  waypoint_3:
    primitive: sphere
    radius: 2
    origin: [40, 5, 10]

operations:
  cable_guide:
    type: hull
    inputs:
      - waypoint_1
      - waypoint_2
      - waypoint_3
```

---

### 3. Customizer/Parameter GUI ⭐⭐⭐⭐⭐

**Priority**: CRITICAL (Game Changer)
**Estimated Effort**: 7-10 days
**Difficulty**: Medium

#### Why This Feature?

This is OpenSCAD's **killer feature** - the reason it's so popular on Thingiverse.

**Problem**: Most users aren't comfortable editing YAML/code, even for simple parameter changes.

**Solution**: Auto-generate a beautiful GUI from parameter definitions.

**Impact**:
- Makes TiaCAD accessible to **non-programmers**
- Enables **parametric template marketplace** (huge business opportunity!)
- **Real-time preview** shows changes instantly
- **Save presets** for different variants
- **Share designs** without requiring TiaCAD knowledge

#### OpenSCAD Implementation

OpenSCAD uses special comments to define UI controls:

```openscad
// Slider with range
height = 20; // [10:100]

// Dropdown menu
finish = "smooth"; // [smooth, textured, glossy]

// Checkbox
add_holes = true;

// Spinbox with step
radius = 5.5; // [0:0.5:20]
```

The Customizer window auto-generates sliders, dropdowns, checkboxes, etc.

#### Proposed TiaCAD Syntax

**Extended Parameter Syntax:**
```yaml
parameters:
  # Simple parameter (no UI metadata)
  depth: 10

  # Slider with range
  height:
    value: 20
    ui:
      type: slider
      min: 10
      max: 100
      step: 5
      description: "Overall bracket height"
      unit: mm

  # Dropdown selection
  finish_type:
    value: "smooth"
    ui:
      type: dropdown
      options:
        - value: "smooth"
          label: "Smooth Finish"
        - value: "textured"
          label: "Textured Surface"
        - value: "glossy"
          label: "Glossy Coating"
      description: "Surface finish selection"

  # Checkbox toggle
  add_mounting_holes:
    value: true
    ui:
      type: checkbox
      description: "Include mounting holes"

  # Spinbox for precise entry
  hole_diameter:
    value: 5.5
    ui:
      type: spinbox
      min: 3.0
      max: 10.0
      step: 0.5
      description: "Mounting hole diameter"
      unit: mm

  # Vector input
  mounting_position:
    value: [10, 10, 0]
    ui:
      type: vector
      description: "Position of mounting point"
      labels: ["X", "Y", "Z"]
      unit: mm

  # Color picker
  body_color:
    value: "#FF5733"
    ui:
      type: color
      description: "Body color"

  # Text input
  engraved_label:
    value: "Part 001"
    ui:
      type: text
      description: "Engraved label text"
      maxlength: 20

# Group parameters into tabs
ui:
  tabs:
    - name: "Dimensions"
      parameters:
        - height
        - depth
        - hole_diameter

    - name: "Features"
      parameters:
        - add_mounting_holes
        - mounting_position

    - name: "Appearance"
      parameters:
        - finish_type
        - body_color
        - engraved_label
```

#### Implementation Architecture

**Tech Stack:**
- **Backend**: FastAPI (async Python web framework)
- **Frontend**: Vue.js or React + Three.js for 3D preview
- **Communication**: WebSocket for real-time updates
- **Rendering**: Background worker queue for STL generation

**System Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                   Web Browser                       │
│  ┌─────────────────┐         ┌──────────────────┐  │
│  │  Parameter GUI  │         │  3D Preview      │  │
│  │  (Vue.js)       │────────▶│  (Three.js)      │  │
│  └─────────────────┘         └──────────────────┘  │
│         │                              ▲            │
│         │ WebSocket                    │            │
│         ▼                              │            │
└─────────────────────────────────────────────────────┘
          │                              │
          ▼                              │
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌──────────────────┐      ┌───────────────────┐   │
│  │  YAML Parser     │─────▶│  Parameter Meta   │   │
│  │  Extract params  │      │  Generate UI def  │   │
│  └──────────────────┘      └───────────────────┘   │
│                                     │               │
│  ┌──────────────────┐               │               │
│  │  Render Queue    │◀──────────────┘               │
│  │  (Celery/Redis)  │                               │
│  └──────────────────┘                               │
│         │                                            │
│         ▼                                            │
│  ┌──────────────────┐                               │
│  │  TiaCAD Engine   │                               │
│  │  YAML → STL      │                               │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

**User Flow:**
1. User uploads TiaCAD YAML file (or selects from gallery)
2. Backend parses YAML and extracts parameter metadata
3. Frontend renders UI controls based on metadata
4. User adjusts parameters via sliders/dropdowns/etc.
5. Frontend sends parameter values via WebSocket
6. Backend triggers render with new parameters
7. STL generated and preview updated
8. User downloads customized STL

**Features:**
- **Real-time preview**: Update 3D view as parameters change
- **Parameter presets**: Save/load favorite configurations
- **URL sharing**: Share customized designs via URL
- **Export options**: STL, 3MF, STEP (future)
- **Batch generation**: Generate multiple variants
- **Template gallery**: Browse community designs

#### Technical Tasks

**Phase 1: Core Backend (3 days)**
1. Parse YAML parameter metadata
2. Generate JSON UI definition
3. FastAPI endpoints for parameter updates
4. Render queue integration
5. WebSocket handling for real-time updates

**Phase 2: Frontend UI (3 days)**
1. Vue.js parameter form generator
2. Implement all UI control types
3. Parameter validation
4. Preset save/load
5. Responsive design

**Phase 3: 3D Preview (2 days)**
1. Three.js STL viewer
2. Camera controls (orbit, pan, zoom)
3. Lighting and materials
4. Loading states and progress

**Phase 4: Polish (2 days)**
1. Error handling and validation
2. Performance optimization
3. URL sharing
4. Template gallery
5. Documentation and examples

#### Example: Parametric Bracket Template

```yaml
schema_version: "2.0"

metadata:
  name: "Parametric Mounting Bracket"
  description: "Customizable bracket for electronics mounting"
  author: "TiaCAD Community"
  category: "Hardware"
  tags: ["bracket", "mounting", "customizable"]
  thumbnail: "bracket_preview.png"

parameters:
  # Dimensions tab
  bracket_width:
    value: 50
    ui:
      type: slider
      min: 20
      max: 200
      step: 5
      description: "Overall width of bracket"
      unit: mm

  bracket_height:
    value: 30
    ui:
      type: slider
      min: 10
      max: 100
      step: 5
      description: "Overall height of bracket"
      unit: mm

  bracket_thickness:
    value: 5
    ui:
      type: slider
      min: 2
      max: 10
      step: 1
      description: "Material thickness"
      unit: mm

  # Holes tab
  add_mounting_holes:
    value: true
    ui:
      type: checkbox
      description: "Include mounting holes"

  hole_diameter:
    value: 5.0
    ui:
      type: spinbox
      min: 2.0
      max: 20.0
      step: 0.5
      description: "Mounting hole diameter (M5 = 5.0mm)"
      unit: mm
      enabled_by: add_mounting_holes

  hole_pattern:
    value: "four_corner"
    ui:
      type: dropdown
      options:
        - value: "four_corner"
          label: "Four Corner Holes"
        - value: "bolt_circle"
          label: "Bolt Circle Pattern"
        - value: "linear"
          label: "Linear Array"
      description: "Hole arrangement pattern"
      enabled_by: add_mounting_holes

  # Finishing tab
  corner_radius:
    value: 3
    ui:
      type: slider
      min: 0
      max: 10
      step: 0.5
      description: "Corner rounding radius (0 = sharp)"
      unit: mm

  edge_chamfer:
    value: 1
    ui:
      type: slider
      min: 0
      max: 5
      step: 0.5
      description: "Edge chamfer size (0 = none)"
      unit: mm

  # Labeling tab
  add_label:
    value: true
    ui:
      type: checkbox
      description: "Add engraved label"

  label_text:
    value: "BRACKET-001"
    ui:
      type: text
      description: "Label text"
      maxlength: 20
      enabled_by: add_label

  label_size:
    value: 6
    ui:
      type: slider
      min: 4
      max: 12
      step: 1
      description: "Label text size"
      unit: mm
      enabled_by: add_label

ui:
  tabs:
    - name: "Dimensions"
      icon: "ruler"
      parameters:
        - bracket_width
        - bracket_height
        - bracket_thickness

    - name: "Holes"
      icon: "circle"
      parameters:
        - add_mounting_holes
        - hole_diameter
        - hole_pattern

    - name: "Finishing"
      icon: "wand"
      parameters:
        - corner_radius
        - edge_chamfer

    - name: "Labeling"
      icon: "text"
      parameters:
        - add_label
        - label_text
        - label_size

# ... rest of design definition ...
```

**User Experience:**
1. Visit https://tiacad.app/customize/parametric-bracket
2. See 3D preview of default bracket
3. Adjust sliders → preview updates in real-time
4. Click "Download STL" → get customized file
5. Click "Save Preset" → bookmark configuration
6. Click "Share" → get URL: https://tiacad.app/c/abc123

---

### 4. Minkowski Sum ⭐⭐⭐⭐

**Priority**: HIGH
**Estimated Effort**: 5-7 days
**Difficulty**: High

#### Why This Feature?

Minkowski sum "sweeps" one shape along the boundary of another, creating:
- **Uniform rounding** of complex shapes (sweep a sphere)
- **Offset/thickening** of thin structures
- **Organic transitions** and blending
- **Tool path simulation** (CNC/3D printing)

It's mathematically elegant and produces results difficult to achieve otherwise.

#### OpenSCAD Implementation

```openscad
// Round all edges by sweeping a sphere
minkowski() {
  cube([20, 20, 5]);
  sphere(r=2);
}
// Result: Cube with uniformly rounded edges

// Create offset version
minkowski() {
  import("complex_shape.stl");
  sphere(r=1);
}
// Result: Shape thickened by 1mm in all directions
```

#### Proposed TiaCAD Syntax

```yaml
operations:
  rounded_body:
    type: minkowski
    base: sharp_bracket
    sweep: rounding_sphere

parts:
  sharp_bracket:
    primitive: box
    size: [20, 20, 5]
    origin: center

  rounding_sphere:
    primitive: sphere
    radius: 2
    origin: center
```

**Simplified syntax for common case (sphere rounding):**
```yaml
operations:
  rounded_body:
    type: minkowski_round
    input: sharp_bracket
    radius: 2  # Sphere radius
```

#### Implementation Details

**Challenge**: CadQuery doesn't have native Minkowski sum.

**Solution Options:**

**Option 1: Mesh-Based (Recommended)**
```python
import trimesh
import numpy as np

def minkowski_sum(shape_a, shape_b):
    # Convert to meshes
    mesh_a = shape_to_trimesh(shape_a)
    mesh_b = shape_to_trimesh(shape_b)

    # Compute Minkowski sum
    # For each vertex in A, translate B to that vertex
    # Take convex hull of all resulting vertices
    vertices = []
    for v_a in mesh_a.vertices:
        for v_b in mesh_b.vertices:
            vertices.append(v_a + v_b)

    # Convex hull of all points
    hull = trimesh.convex.convex_hull(vertices)

    return trimesh_to_cadquery(hull)
```

**Option 2: PyMesh Library**
```python
import pymesh

def minkowski_pymesh(shape_a, shape_b):
    mesh_a = to_pymesh(shape_a)
    mesh_b = to_pymesh(shape_b)

    result = pymesh.minkowski_sum(mesh_a, mesh_b)

    return pymesh_to_cadquery(result)
```

**Option 3: Sphere Rounding Special Case**

For the common case of rounding with a sphere, use CadQuery's fillet operations:

```python
def minkowski_sphere_round(shape, radius):
    # Find all edges
    edges = shape.edges()

    # Apply uniform fillet
    result = shape.edges().fillet(radius)

    return result
```

**Recommendation**: Implement **Option 3** first (sphere rounding special case), then add general Minkowski via trimesh.

#### Use Cases & Examples

**Example 1: Uniform Rounding**
```yaml
# Sharp bracket with uniform rounding
operations:
  rounded_bracket:
    type: minkowski_round
    input: bracket_base
    radius: 2
```

**Example 2: Thickening Thin Structures**
```yaml
# Add thickness to thin shell
operations:
  thickened_shell:
    type: minkowski
    base: thin_lattice
    sweep: small_sphere
```

**Example 3: Organic Transitions**
```yaml
# Create organic blend between shapes
operations:
  organic_form:
    type: minkowski
    base: angular_structure
    sweep: smoothing_sphere
```

---

### 5. 2D Offset Operation ⭐⭐⭐

**Priority**: MEDIUM
**Estimated Effort**: 1 day
**Difficulty**: Low

#### Why This Feature?

2D offset expands or contracts 2D shapes - essential for:
- Creating **walls and borders**
- **Clearance gaps** around parts
- **Support structures**
- **Tool path generation** (CNC, laser cutting)
- **Inset/outset patterns**

#### OpenSCAD Implementation

```openscad
// Expand shape outward
offset(r=2) square([20, 20]);

// Contract shape inward
offset(r=-1) square([20, 20]);

// Chamfer instead of round
offset(r=2, chamfer=true) square([20, 20]);
```

#### Proposed TiaCAD Syntax

```yaml
sketches:
  base_outline:
    plane: XY
    shapes:
      - type: rectangle
        width: 50
        height: 30
        center: [0, 0]

  # Offset outward (expand)
  outer_wall:
    operation: offset
    source: base_outline
    distance: 3  # 3mm expansion
    mode: round  # round, square, or miter

  # Offset inward (contract)
  clearance:
    operation: offset
    source: base_outline
    distance: -1  # 1mm contraction
    mode: round

operations:
  # Extrude offset sketch
  wall:
    type: extrude
    sketch: outer_wall
    distance: 10
    direction: Z
```

#### Implementation Details

**Easy Win**: CadQuery has `.offset2D()` built-in!

```python
# CadQuery offset example
result = (
    cq.Workplane("XY")
    .rect(50, 30)
    .offset2D(3)  # Offset by 3mm
)
```

**Technical Tasks:**
1. Add `offset` sketch operation type
2. Parse offset parameters (source, distance, mode)
3. Map to CadQuery's offset2D()
4. Handle edge cases (self-intersecting paths)
5. Support offset modes (round, square, miter)
6. Add tests for various shapes
7. Document offset operation

**Parameters:**
- `source`: Source sketch name
- `distance`: Offset distance (positive = expand, negative = contract)
- `mode`: "round" (default), "square", or "miter"
- `closed`: Whether path is closed (default: auto-detect)

#### Examples

**Example 1: Create Wall with Clearance**
```yaml
sketches:
  component_outline:
    plane: XY
    shapes:
      - type: rectangle
        width: 40
        height: 25

  clearance_zone:
    operation: offset
    source: component_outline
    distance: 2  # 2mm clearance

  wall_outline:
    operation: offset
    source: clearance_zone
    distance: 3  # 3mm wall thickness

operations:
  enclosure_wall:
    type: extrude
    sketch: wall_outline
    distance: 15

  clearance_cavity:
    type: extrude
    sketch: clearance_zone
    distance: 20

  hollow_enclosure:
    type: boolean
    operation: difference
    base: enclosure_wall
    subtract: [clearance_cavity]
```

**Example 2: Inset Pattern**
```yaml
sketches:
  logo_outline:
    plane: XY
    shapes:
      - type: polygon
        points: [[...]]

  inset_border:
    operation: offset
    source: logo_outline
    distance: -2  # 2mm inset

operations:
  raised_logo:
    type: extrude
    sketch: logo_outline
    distance: 3

  border_recess:
    type: extrude
    sketch: inset_border
    distance: 1.5  # Half depth
```

---

### 6. DXF/SVG Import ⭐⭐⭐

**Priority**: MEDIUM
**Estimated Effort**: 4-5 days (2-3 days per format)
**Difficulty**: Medium

#### Why This Feature?

Import 2D paths from professional CAD and design tools:
- **Complex logos** and artwork from Illustrator/Inkscape
- **Technical drawings** from AutoCAD/LibreCAD
- **Laser-cut patterns** from existing libraries
- **Reuse existing designs** without manual recreation

This bridges TiaCAD with the broader CAD/design ecosystem.

#### OpenSCAD Implementation

```openscad
// Import DXF and extrude
linear_extrude(height=5)
  import("logo.dxf");

// Import SVG
linear_extrude(height=2)
  import("icon.svg");
```

#### Proposed TiaCAD Syntax

```yaml
sketches:
  company_logo:
    import:
      file: "assets/company_logo.dxf"
      format: dxf  # auto-detect if omitted
      layer: "outline"  # DXF layer to import (optional)
      scale: 2.0  # Scale factor
      origin: [0, 0]  # Import position
    plane: XY

  decorative_icon:
    import:
      file: "assets/icon.svg"
      format: svg
      scale: 1.5
    plane: XY

operations:
  logo_3d:
    type: extrude
    sketch: company_logo
    distance: 3
    direction: Z

  icon_engraving:
    type: extrude
    sketch: decorative_icon
    distance: -1  # Negative = engrave
    direction: Z
```

#### Implementation Details

**DXF Import:**

Library: `ezdxf` (pure Python DXF library)

```python
import ezdxf
import cadquery as cq

def import_dxf(file_path, layer=None):
    # Read DXF file
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    # Extract entities from specified layer
    entities = msp.query('*') if layer is None else msp.query(f'*[layer=="{layer}"]')

    # Convert to CadQuery wires/faces
    wires = []
    for entity in entities:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            wire = cq.Edge.makeLine(
                cq.Vector(start.x, start.y),
                cq.Vector(end.x, end.y)
            )
            wires.append(wire)

        elif entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            wire = cq.Wire.makeCircle(
                radius,
                cq.Vector(center.x, center.y, 0)
            )
            wires.append(wire)

        elif entity.dxftype() == 'ARC':
            # Convert arc to wire
            wire = convert_arc_to_wire(entity)
            wires.append(wire)

        elif entity.dxftype() == 'POLYLINE' or entity.dxftype() == 'LWPOLYLINE':
            # Convert polyline to wire
            points = [(p.x, p.y) for p in entity.get_points()]
            wire = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in points])
            wires.append(wire)

        elif entity.dxftype() == 'SPLINE':
            # Convert spline to wire (complex!)
            wire = convert_spline_to_wire(entity)
            wires.append(wire)

    # Combine wires into face(s)
    faces = wire_to_faces(wires)

    return faces
```

**SVG Import:**

Library: `svgpathtools`

```python
from svgpathtools import svg2paths
import cadquery as cq

def import_svg(file_path):
    # Parse SVG paths
    paths, attributes = svg2paths(file_path)

    wires = []
    for path in paths:
        # Convert SVG path segments to CadQuery edges
        edges = []
        for segment in path:
            if segment.__class__.__name__ == 'Line':
                edge = cq.Edge.makeLine(
                    cq.Vector(segment.start.real, segment.start.imag),
                    cq.Vector(segment.end.real, segment.end.imag)
                )
                edges.append(edge)

            elif segment.__class__.__name__ == 'CubicBezier':
                # Convert Bezier to BSpline
                edge = bezier_to_edge(segment)
                edges.append(edge)

            elif segment.__class__.__name__ == 'Arc':
                edge = arc_to_edge(segment)
                edges.append(edge)

        # Combine edges into wire
        wire = cq.Wire.assembleEdges(edges)
        wires.append(wire)

    # Convert wires to faces
    faces = wire_to_faces(wires)

    return faces
```

**Technical Tasks:**

**DXF Support (2-3 days):**
1. Install and test ezdxf library
2. Implement DXF entity parsers (LINE, CIRCLE, ARC, POLYLINE, SPLINE)
3. Convert DXF entities to CadQuery wires
4. Handle layers and selection
5. Add scaling and positioning
6. Create tests with sample DXF files
7. Document DXF import capabilities

**SVG Support (2-3 days):**
1. Install and test svgpathtools library
2. Implement SVG path parsers (lines, curves, arcs)
3. Convert SVG coordinates to CadQuery
4. Handle SVG transforms (scale, rotate, translate)
5. Support basic shapes (rect, circle, ellipse)
6. Create tests with sample SVG files
7. Document SVG import capabilities

**Edge Cases:**
- Invalid file paths → clear error message
- Unsupported entities → warning + skip
- Self-intersecting paths → attempt to fix or error
- Multiple disconnected paths → create multiple faces
- Text in DXF/SVG → convert to paths or skip (with warning)

#### Examples

**Example 1: Logo Engraving**
```yaml
sketches:
  logo:
    import:
      file: "assets/logo.svg"
      scale: 0.5
    plane: XY

parts:
  base_plate:
    primitive: box
    size: [100, 50, 5]
    origin: [0, 0, 0]

operations:
  logo_engraving:
    type: extrude
    sketch: logo
    distance: -1  # 1mm deep engraving
    direction: Z

  engraved_plate:
    type: boolean
    operation: difference
    base: base_plate
    subtract: [logo_engraving]
```

**Example 2: Technical Drawing Import**
```yaml
sketches:
  mounting_pattern:
    import:
      file: "drawings/mounting_holes.dxf"
      layer: "HOLES"  # Only import holes layer
      scale: 1.0
    plane: XY

operations:
  mounting_plate:
    type: extrude
    sketch: mounting_pattern
    distance: 10
```

---

### 7. Shell/Hollow Operation ⭐⭐⭐

**Priority**: MEDIUM
**Estimated Effort**: 2-3 days
**Difficulty**: Medium

#### Why This Feature?

Create hollow versions of solid parts:
- **Reduce material/weight** (3D printing, casting)
- **Create enclosures** with wall thickness
- **Thermal management** (hollow sections for cooling)
- **Cost reduction** (less material = lower cost)

#### OpenSCAD Implementation

OpenSCAD doesn't have native shell - users typically use `difference()`:

```openscad
// Manual hollow approach
difference() {
  sphere(r=20);
  sphere(r=18);  // 2mm wall
}
```

#### Proposed TiaCAD Syntax

```yaml
operations:
  hollow_sphere:
    type: shell
    input: solid_sphere
    thickness: 2  # Wall thickness
    faces: all  # Which faces to remove (all, or selector)
```

**Advanced: Selective Shelling**
```yaml
operations:
  hollow_box:
    type: shell
    input: solid_box
    thickness: 2
    faces:
      direction: "+Z"  # Remove top face only
```

#### Implementation Details

**Easy Win**: CadQuery has `.shell()` built-in!

```python
# CadQuery shell example
result = (
    cq.Workplane("XY")
    .box(20, 20, 20)
    .faces(">Z")  # Select top face
    .shell(2)  # 2mm wall thickness
)
```

**Technical Tasks:**
1. Add `shell` operation type to parser
2. Map TiaCAD params to CadQuery shell()
3. Implement face selection (all, direction-based, custom)
4. Handle edge cases (thickness too large, etc.)
5. Add tests for various shapes
6. Document shell operation

**Parameters:**
- `input`: Part to hollow
- `thickness`: Wall thickness (must be < minimum dimension)
- `faces`: Which faces to remove
  - `all`: Remove all faces (default)
  - `{direction: "+Z"}`: Remove faces in direction
  - `{selector: "..."}`: Custom face selector

#### Examples

**Example 1: Hollow Sphere**
```yaml
parts:
  solid_sphere:
    primitive: sphere
    radius: 20
    origin: center

operations:
  hollow_sphere:
    type: shell
    input: solid_sphere
    thickness: 2
    faces: all
```

**Example 2: Open-Top Box**
```yaml
parts:
  solid_box:
    primitive: box
    size: [50, 50, 30]
    origin: center

operations:
  container:
    type: shell
    input: solid_box
    thickness: 3
    faces:
      direction: "+Z"  # Remove top face only
```

---

### 8. STL Import ⭐⭐

**Priority**: LOW
**Estimated Effort**: 1 day
**Difficulty**: Low

#### Why This Feature?

Integrate existing STL models:
- **Combine** TiaCAD designs with downloaded models
- **Modify** existing parts
- **Remix** Thingiverse designs
- **Hybrid workflows** (scan → import → modify)

#### Proposed TiaCAD Syntax

```yaml
parts:
  imported_bracket:
    import:
      file: "models/standard_bracket.stl"
      scale: 1.0
      origin: [0, 0, 0]

operations:
  customized:
    type: boolean
    operation: union
    inputs:
      - imported_bracket
      - my_custom_extension
```

#### Implementation Details

CadQuery supports STL import via `importers`:

```python
import cadquery as cq

def import_stl(file_path):
    # CadQuery can import STL via OCCT
    shape = cq.importers.importShape(cq.exporters.ExportTypes.STL, file_path)
    return shape
```

**Technical Tasks:**
1. Add STL import support to part parser
2. Handle scaling and positioning
3. Validate STL file integrity
4. Add tests with sample STL files
5. Document STL import

---

### 9. Animation Support ⭐⭐

**Priority**: LOW (but cool!)
**Estimated Effort**: 3-5 days
**Difficulty**: Medium

#### Why This Feature?

Visualize motion and assemblies:
- **Demonstrate mechanisms** (gears, hinges, sliding parts)
- **Marketing materials** (rotating product shots)
- **Assembly instructions** (show how parts fit together)
- **Design validation** (check clearances during motion)

#### OpenSCAD Implementation

OpenSCAD has special variable `$t` that ranges from 0 to 1:

```openscad
// Rotation animation
rotate([0, 0, $t * 360])
  cube([10, 10, 10]);

// Translate animation
translate([$t * 50, 0, 0])
  sphere(r=5);
```

Generate animation: `openscad -o frame.png --animate 10 model.scad`

#### Proposed TiaCAD Syntax

```yaml
# Enable animation mode
animation:
  enabled: true
  frames: 60
  duration: 3  # seconds
  fps: 20

parameters:
  # Use $t variable (0.0 to 1.0)
  rotation_angle: "${$t * 360}"
  slider_position: "${$t * 50}"

operations:
  rotating_gear:
    type: transform
    input: gear
    transforms:
      - rotate:
          axis: Z
          angle: ${rotation_angle}
          origin: [0, 0, 0]

  sliding_part:
    type: transform
    input: slider
    transforms:
      - translate: [${slider_position}, 0, 0]
```

#### Implementation Details

**Technical Tasks:**
1. Add `animation` section to schema
2. Parse `$t` variable in parameter expressions
3. Render loop: iterate $t from 0 to 1
4. Generate frame images (PNG)
5. Compile frames to video (ffmpeg)
6. Add animation controls to Customizer GUI
7. Document animation syntax

**Output Options:**
- **Image sequence**: `frame_001.png`, `frame_002.png`, ...
- **Animated GIF**: `animation.gif`
- **Video**: `animation.mp4` (via ffmpeg)
- **Interactive**: Scrub timeline in web UI

#### Example

**Rotating Gear Animation:**
```yaml
animation:
  enabled: true
  frames: 360  # One degree per frame
  fps: 30

parameters:
  gear_rotation: "${$t * 360}"

operations:
  spinning_gear:
    type: transform
    input: gear
    transforms:
      - rotate:
          axis: Z
          angle: ${gear_rotation}
          origin: [0, 0, 0]
```

**Command Line:**
```bash
tiacad build gear_animation.yaml --animate --output animation.gif
# Generates 360-frame animated GIF
```

---

### 10. Variable-Radius Fillet ⭐⭐

**Priority**: LOW
**Estimated Effort**: 2-3 days
**Difficulty**: Medium

#### Why This Feature?

Create **organic transitions** with varying fillet radius along an edge:
- Aerodynamic shapes
- Ergonomic handles
- Artistic designs
- Natural-looking transitions

#### OpenSCAD Implementation

OpenSCAD doesn't support variable-radius fillets natively.

#### Proposed TiaCAD Syntax

```yaml
operations:
  organic_fillet:
    type: finishing
    finish: fillet
    input: base_part
    edges:
      selector: "..."
    radius_profile:
      - position: 0.0   # Start of edge (0-1)
        radius: 2.0
      - position: 0.5   # Midpoint
        radius: 5.0
      - position: 1.0   # End of edge
        radius: 2.0
```

#### Implementation Details

CadQuery doesn't have native variable-radius fillet. Would require:
1. Edge parameterization (0-1 along length)
2. Interpolate radius at sample points
3. Apply fillet with varying radius (complex OCCT operation)

**Recommendation**: Low priority - can be approximated with multiple fixed-radius fillets.

---

## Implementation Roadmap

### Phase 4A: Critical Missing Features (1-2 weeks)

**Goal**: Add essential operations that OpenSCAD has and TiaCAD needs.

#### Week 1: Text + Offset
1. **Text Operations** (3 days)
   - Day 1: Implement text as sketch shape type
   - Day 2: Font handling, validation, tests
   - Day 3: Documentation, examples, edge cases

2. **2D Offset** (1 day)
   - Morning: Implement offset sketch operation
   - Afternoon: Tests, documentation

3. **Shell/Hollow** (2 days)
   - Day 1: Implement shell operation, face selection
   - Day 2: Tests, examples, documentation

#### Week 2: Hull
4. **Hull Operation** (5 days)
   - Day 1: Research and design architecture
   - Day 2: Implement vertex extraction and hull computation
   - Day 3: CadQuery solid generation from hull
   - Day 4: Edge cases, optimization
   - Day 5: Tests, examples, documentation

**Deliverables:**
- Text operations fully functional
- 2D offset working for all shapes
- Shell operation for creating hollow parts
- Hull operation for convex hulls
- All features tested and documented
- Examples added to gallery

**Success Criteria:**
- 95%+ test coverage for new operations
- Documentation with 3+ examples each
- Integration tests with existing features
- Performance benchmarks

---

### Phase 4B: Import/Export Expansion (1-2 weeks)

**Goal**: Bridge TiaCAD with other CAD/design tools.

#### Week 3: 2D Imports
1. **DXF Import** (3 days)
   - Day 1: ezdxf integration, basic entities (LINE, CIRCLE, ARC)
   - Day 2: Complex entities (POLYLINE, SPLINE), layer support
   - Day 3: Tests, edge cases, documentation

2. **SVG Import** (2 days)
   - Day 1: svgpathtools integration, path conversion
   - Day 2: Tests, examples, documentation

#### Week 4: 3D Imports
3. **STL Import** (1 day)
   - Morning: Implement STL import
   - Afternoon: Tests, documentation

**Deliverables:**
- DXF import supporting common entities
- SVG import supporting paths and basic shapes
- STL import for existing models
- Import examples in documentation
- File validation and error handling

**Success Criteria:**
- Successfully import real-world DXF/SVG/STL files
- Clear error messages for unsupported features
- Examples showing import + modification workflows
- Integration with existing TiaCAD features

---

### Phase 4C: Advanced Operations (2-3 weeks)

**Goal**: Add mathematically sophisticated operations.

#### Week 5-6: Minkowski
1. **Minkowski Sum** (7 days)
   - Day 1-2: Research implementation approaches
   - Day 3-4: Implement sphere-rounding special case
   - Day 5-6: Implement general Minkowski (trimesh/pymesh)
   - Day 7: Tests, optimization, documentation

**Deliverables:**
- Minkowski sum operation (both special case and general)
- Performance optimization for large meshes
- Examples showing rounding and thickening
- Comprehensive tests

**Success Criteria:**
- Sphere rounding works for all shapes
- General Minkowski handles common cases
- Performance acceptable (< 5s for typical parts)
- Clear documentation of limitations

---

### Phase 5: Polish & UX (2-3 weeks)

**Goal**: Make TiaCAD accessible to non-programmers.

#### Week 7-9: Customizer GUI
1. **Backend** (3 days)
   - Day 1: Parameter metadata parsing, JSON UI generation
   - Day 2: FastAPI endpoints, WebSocket handling
   - Day 3: Render queue integration

2. **Frontend** (3 days)
   - Day 1: Vue.js parameter form generator
   - Day 2: All UI control types (slider, dropdown, etc.)
   - Day 3: Responsive design, validation

3. **3D Preview** (2 days)
   - Day 1: Three.js STL viewer, camera controls
   - Day 2: Lighting, materials, loading states

4. **Polish** (2 days)
   - Day 1: Error handling, optimization
   - Day 2: URL sharing, template gallery

**Deliverables:**
- Full-featured parameter customizer web UI
- Real-time 3D preview
- Preset save/load functionality
- URL sharing for designs
- Template gallery with examples

**Success Criteria:**
- Non-programmers can customize designs easily
- Preview updates in < 2s for typical parts
- Mobile-responsive interface
- At least 10 template designs in gallery

---

### Phase 6: Nice-to-Have (Future)

**Lower priority features for later:**

1. **Animation Support** (3-5 days)
   - $t variable support
   - Frame generation
   - GIF/MP4 export
   - Scrub timeline in GUI

2. **Variable-Radius Fillet** (2-3 days)
   - Edge parameterization
   - Radius interpolation
   - Complex OCCT operations

3. **STEP/IGES Export** (3-5 days)
   - Format conversion
   - Metadata preservation
   - CAM integration prep

4. **Advanced Text** (2-3 days)
   - Multi-line text
   - Text on curved surfaces
   - Font effects (outline, emboss)

**Total Estimated Effort**: 8-12 weeks for full OpenSCAD feature parity

---

## TiaCAD's Unique Strengths

While learning from OpenSCAD, **preserve what makes TiaCAD special:**

### 1. Declarative YAML Philosophy

**Strength**: Human-readable, version-control friendly, self-documenting.

```yaml
# TiaCAD: Clear intent
parameters:
  bracket_height: 20
  hole_diameter: 5

# vs OpenSCAD: Procedural code
bracket_height = 20;
hole_diameter = 5;
```

**Why It Matters:**
- Git diffs are meaningful
- Non-programmers can understand
- Easy to generate/modify programmatically
- Schema validation catches errors early

**Preserve**: Keep YAML as primary format. Consider OpenSCAD import/export as future feature.

---

### 2. Explicit Origins System

**Strength**: No ambiguity about where transformations happen.

```yaml
# TiaCAD: Explicit origin for every operation
operations:
  rotated_part:
    type: transform
    input: bracket
    transforms:
      - rotate:
          axis: Z
          angle: 45
          origin: [10, 10, 0]  # REQUIRED - crystal clear!
```

**vs OpenSCAD implicit transforms:**
```openscad
// OpenSCAD: Where does this rotate around?
translate([10, 10, 0])
  rotate([0, 0, 45])
    cube([20, 20, 5]);
// (Answer: depends on order and current position!)
```

**Why It Matters:**
- Eliminates "transform order confusion"
- Makes designs easier to understand
- Reduces debugging time
- Clearer mental model

**Preserve**: Never add implicit origins or "magic" defaults.

---

### 3. Advanced Sketch Operations

**Strength**: Loft, sweep, revolve are first-class operations.

```yaml
# TiaCAD: Native loft support
operations:
  smooth_transition:
    type: loft
    profiles:
      - square_base
      - circle_top
    ruled: false
```

**OpenSCAD**: Would require complex manual triangulation or external libraries.

**Why It Matters:**
- Enables organic forms
- Professional CAD capabilities
- Differentiates from basic tools

**Preserve**: Continue investing in advanced sketch operations. Consider:
- Boundary surfaces
- Guided sweeps (sweep along path with guide curves)
- N-sided patches

---

### 4. Pattern Operations

**Strength**: Linear, circular, and grid patterns built-in.

```yaml
# TiaCAD: Declarative patterns
operations:
  bolt_circle:
    type: pattern
    pattern: circular
    input: hole
    count: 6
    radius: 50
    axis: Z
    center: [0, 0, 0]
```

**OpenSCAD**: Manual for loops.

```openscad
// OpenSCAD: Manual loop
for (i = [0:5]) {
  rotate([0, 0, i * 60])
    translate([50, 0, 0])
      cylinder(h=10, r=2.5);
}
```

**Why It Matters:**
- Faster to write
- Clearer intent
- Less error-prone
- Easier to modify

**Preserve**: Keep pattern operations high-level. Consider adding:
- Path-based patterns (array along curve)
- Random/organic patterns
- Symmetry patterns

---

### 5. Comprehensive Materials System

**Strength**: Full material library with physical properties.

```yaml
# TiaCAD: Rich materials
materials:
  body:
    color: "#FF5733"
    name: "ABS Red"
    density: 1.04
    finish: "matte"

  insert:
    color: "#C0C0C0"
    name: "Brass Insert"
    density: 8.5
    finish: "metallic"
```

**OpenSCAD**: Basic colors only.

```openscad
// OpenSCAD: Just colors
color([1, 0.3, 0.2])
  cube([10, 10, 10]);
```

**Why It Matters:**
- Multi-material 3D printing (3MF export)
- Weight/cost calculations
- Realistic rendering
- Engineering analysis prep

**Preserve**: Continue developing materials system. Consider adding:
- Material database (common plastics, metals)
- Material property calculations (strength, flex)
- Manufacturing process metadata (print temp, etc.)

---

### 6. Test-Driven Development

**Strength**: 609 passing tests, high coverage, quality-first.

- Comprehensive test suite
- Continuous integration
- Regression prevention
- Confidence in refactoring

**OpenSCAD**: Community-driven, less formal testing.

**Why It Matters:**
- Production-ready reliability
- Safe to add features
- Professional codebase
- Maintainability

**Preserve**: Maintain test-first approach for all new features:
- Every feature requires tests
- Aim for 95%+ coverage
- Integration tests for complex workflows
- Performance benchmarks

---

### 7. Modern Architecture

**Strength**: Clean Python, CadQuery, modular design.

- Type hints throughout
- Clear abstractions
- Extensible architecture
- Modern Python idioms

**OpenSCAD**: C++ codebase, harder to extend.

**Why It Matters:**
- Easy to contribute
- Fast iteration
- Clear codebase
- Future-proof

**Preserve**: Maintain architectural principles:
- Separation of concerns
- Plugin architecture for extensions
- Clear APIs
- Comprehensive documentation

---

### 8. Schema Validation

**Strength**: JSON Schema validation catches errors early.

```yaml
# TiaCAD: Validates before building
tiacad validate design.yaml
# ❌ Error: Line 45: Invalid parameter type
#    Expected: number, Got: string
```

**OpenSCAD**: Errors at render time (or silent failures).

**Why It Matters:**
- Catch errors early
- Better error messages
- IDE auto-completion
- Self-documenting

**Preserve**: Extend schema as features grow:
- Schema for each operation type
- Parameter validation rules
- Unit checking (mm vs inches)
- Dependency validation

---

## Technical Implementation Notes

### Development Environment Setup

```bash
# Clone repo
git clone https://github.com/tia/tiacad.git
cd tiacad

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=tiacad_core --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Code Quality Tools

```bash
# Linting with ruff (fast)
ruff check .

# Comprehensive linting with pylint
pylint tiacad_core/

# Type checking with mypy
mypy tiacad_core/

# Format code
black tiacad_core/
```

### Testing Strategy

**Test Pyramid:**
1. **Unit Tests** (60%): Test individual functions/classes
2. **Integration Tests** (30%): Test operation combinations
3. **End-to-End Tests** (10%): Full YAML → STL pipeline

**Coverage Goals:**
- Core operations: 100%
- Parsers: 100%
- Utilities: 95%+
- CLI: 90%+
- Overall: 95%+

**Test Organization:**
```
tiacad_core/tests/
├── unit/
│   ├── test_parser.py
│   ├── test_point_resolver.py
│   ├── test_selector.py
│   └── ...
├── integration/
│   ├── test_boolean_operations.py
│   ├── test_pattern_operations.py
│   └── ...
└── e2e/
    ├── test_full_pipeline.py
    └── test_examples.py
```

### Performance Benchmarking

```python
# benchmarks/benchmark_operations.py
import pytest
import time

@pytest.mark.benchmark
def test_boolean_union_performance():
    start = time.time()

    # Run operation
    result = run_tiacad("complex_union.yaml")

    elapsed = time.time() - start

    # Assert performance target
    assert elapsed < 5.0, f"Union took {elapsed:.2f}s (target: <5s)"
```

**Performance Targets:**
- Simple operations (extrude, transform): < 0.5s
- Boolean operations: < 2s
- Pattern operations: < 3s
- Complex loft/sweep: < 5s
- Full complex part: < 10s

### Documentation Standards

**Every feature requires:**

1. **API Documentation** (docstrings)
```python
def hull(shapes: List[cq.Solid]) -> cq.Solid:
    """
    Compute convex hull around multiple shapes.

    Args:
        shapes: List of CadQuery solids to wrap

    Returns:
        CadQuery solid representing convex hull

    Raises:
        ValueError: If shapes list is empty
        GeometryError: If hull computation fails

    Example:
        >>> hull([box1, box2, box3])
        <cadquery.Solid object>
    """
```

2. **User Documentation** (markdown)
```markdown
## Hull Operation

Creates a convex hull around multiple parts...

### Syntax
...yaml example...

### Parameters
- `inputs`: List of parts to wrap

### Examples
...practical examples...

### Common Issues
...troubleshooting...
```

3. **Examples** (working YAML files)
```yaml
# examples/hull_enclosure.yaml
# Demonstrates hull operation for organic enclosure
...
```

4. **Tests** (pytest)
```python
def test_hull_basic():
    """Test hull around two boxes."""
    # Arrange, Act, Assert
```

---

## Conclusion

### Summary of Recommendations

**Immediate Priorities (Phase 4A):**
1. **Text Operations** - Critical missing feature, easy implementation
2. **Hull Operation** - Unique capability, differentiates TiaCAD
3. **2D Offset** - Quick win, high utility

**Medium-Term (Phase 4B-C):**
4. **DXF/SVG Import** - Integration with design ecosystem
5. **Minkowski Sum** - Advanced geometry capabilities
6. **Shell/Hollow** - Essential for real-world parts

**Long-Term (Phase 5):**
7. **Customizer GUI** - Game-changer for usability and adoption
8. **Animation Support** - Visualization and marketing
9. **STL Import** - Workflow flexibility

### Success Metrics

**Technical:**
- Test coverage remains > 95%
- Build time < 10s for complex parts
- Error messages clear and actionable
- Documentation comprehensive

**User Experience:**
- Non-programmers can use Customizer
- Example gallery has 20+ designs
- Common CAD tasks have clear examples
- Active community contributions

**Ecosystem:**
- Integration with major CAD tools (DXF/SVG import)
- Export to multiple formats (STL, 3MF, STEP)
- Template marketplace emerging
- Educational adoption

### Next Steps

1. **Review this document** with team
2. **Prioritize features** based on user feedback
3. **Create GitHub issues** for each feature
4. **Start with Text Operations** (quick win)
5. **Iterate based on feedback**

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
**Authors**: TIA Analysis Team
**Review Status**: Draft
**Next Review**: After Phase 4A completion
