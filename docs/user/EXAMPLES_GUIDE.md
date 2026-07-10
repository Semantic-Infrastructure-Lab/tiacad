# TiaCAD Examples Guide

**Version:** 3.1.2
**Status:** Curated active example catalog

---

## Overview

This guide catalogs the active examples in the `examples/` directory, organized by difficulty and concept. Each example demonstrates specific TiaCAD features and builds foundational skills.

**Special cases to note:**
- `error_demo.yaml` is intentionally broken for error-handling tests
- `pipe_sweep.yaml` documents a known OCCT geometry limitation

---

## Quick Start

**New to TiaCAD?** Start here:
1. [simple_box.yaml](#simple_box) - Learn the basics (⭐)
2. [simple_extrude.yaml](#simple_extrude) - Sketch-based modeling (⭐)
3. [bracket_with_hole.yaml](#bracket_with_hole) - Boolean operations (⭐⭐)
4. [lego_brick_2x1.yaml](#lego_brick_2x1) - Parametric patterns (⭐⭐)

**Want to explore features?** Jump to:
- [By Difficulty](#examples-by-difficulty)
- [By Concept](#examples-by-concept)
- [By Feature](#examples-by-feature)

---

## Examples by Difficulty

### ⭐ Beginner (8 examples)

Simple primitives, basic operations, single parts. **Start here!**

| Example | Concepts | Status |
|---------|----------|--------|
| [simple_box.yaml](#simple_box) | Box primitive, minimal structure | ✅ |
| [simple_extrude.yaml](#simple_extrude) | Sketch extrusion basics | ✅ |
| [v3_simple_box.yaml](#v3_simple_box) | v3.0 syntax demo | ✅ |
| [simple_guitar_hanger.yaml](#simple_guitar_hanger) | Multiple parts, transforms | ✅ |
| [bottle_revolve.yaml](#bottle_revolve) | Revolve operation | ✅ |
| [hull_simple.yaml](#hull_simple) | Basic hull operation | ✅ |
| [text_primitive_simple.yaml](#text_primitive_simple) | 3D text basics | ✅ |
| [pipe_sweep_simple.yaml](#pipe_sweep_simple) | Simple sweep path | ✅ |

### ⭐⭐ Intermediate (26 examples)

Multiple parts, transforms, patterns, boolean operations, assemblies.

| Example | Concepts | Status |
|---------|----------|--------|
| [bracket_with_hole.yaml](#bracket_with_hole) | Boolean subtract, holes | ✅ |
| [chamfered_bracket.yaml](#chamfered_bracket) | Chamfer finishing | ✅ |
| [rounded_mounting_plate.yaml](#rounded_mounting_plate) | Fillet finishing | ✅ |
| [mounting_plate_with_bolt_circle.yaml](#mounting_plate_with_bolt_circle) | Circular patterns | ✅ |
| [guitar_hanger_with_holes.yaml](#guitar_hanger_with_holes) | Assembly with holes | ✅ |
| [guitar_hanger_named_points.yaml](#guitar_hanger_named_points) | Named references | ✅ |
| [v3_bracket_mount.yaml](#v3_bracket_mount) | v3.0 references system | ✅ |
| [anchors_demo.yaml](#anchors_demo) | Auto-generated anchors | ✅ |
| [references_demo.yaml](#references_demo) | Reference system | ✅ |
| [auto_references_box_stack.yaml](#auto_references_box_stack) | Auto-references stacking | ✅ |
| [auto_references_cylinder_assembly.yaml](#auto_references_cylinder_assembly) | Auto-references assembly | ✅ |
| [auto_references_rotation.yaml](#auto_references_rotation) | Auto-references rotation | ✅ |
| [auto_references_with_offsets.yaml](#auto_references_with_offsets) | Auto-references offsets | ✅ |
| [week5_align_to_face.yaml](#week5_align_to_face) | Face alignment | ✅ |
| [week5_assembly.yaml](#week5_assembly) | Multi-part assembly | ✅ |
| [week5_frame_based_rotation.yaml](#week5_frame_based_rotation) | Frame-based transforms | ✅ |
| [hull_enclosure.yaml](#hull_enclosure) | Hull for enclosures | ✅ |
| [transition_loft.yaml](#transition_loft) | Loft between shapes | ✅ |
| [color_demo.yaml](#color_demo) | Basic coloring | ✅ |
| [enhanced_metadata_demo.yaml](#enhanced_metadata_demo) | Metadata fields | ✅ |
| [formats_demo.yaml](#formats_demo) | Export formats | ✅ |
| [text_simple.yaml](#text_simple) | Text operations | ✅ |
| [text_label.yaml](#text_label) | Text labels | ✅ |
| [text_engraved.yaml](#text_engraved) | Text engraving | ✅ |
| [text_primitive_sign.yaml](#text_primitive_sign) | Text signage | ✅ |
| [text_primitive_styles.yaml](#text_primitive_styles) | Text styling | ✅ |

### ⭐⭐⭐ Advanced (10 examples)

Complex assemblies, parametric systems, multi-material, advanced features.

| Example | Concepts | Status |
|---------|----------|--------|
| [lego_brick_2x1.yaml](#lego_brick_2x1) | Parametric LEGO, patterns, standards | ✅ |
| [lego_brick_3x1.yaml](#lego_brick_3x1) | Extended LEGO patterns | ✅ |
| [awesome_guitar_hanger.yaml](#awesome_guitar_hanger) | Complete assembly, 400+ lines | ✅ |
| [multi_material_demo.yaml](#multi_material_demo) | Multiple materials | ✅ |
| [multi_material_enclosure.yaml](#multi_material_enclosure) | Complex multi-material | ✅ |
| [color_showcase.yaml](#color_showcase) | Advanced coloring, 300+ lines | ✅ |
| [text_operation_emboss_simple.yaml](#text_operation_emboss_simple) | Text embossing | ✅ |
| [text_operation_multi_face.yaml](#text_operation_multi_face) | Multi-face text | ✅ |
| [text_operation_product_label.yaml](#text_operation_product_label) | Product labeling | ✅ |
| [text_primitive_vs_sketch.yaml](#text_primitive_vs_sketch) | Text primitives comparison | ✅ |

### ⚠️ Special Cases (2 examples)

| Example | Purpose | Status |
|---------|---------|--------|
| [error_demo.yaml](#error_demo) | Error handling testing | ⚠️ Intentionally broken |
| [pipe_sweep.yaml](#pipe_sweep) | Sweep with hollow profile | ⚠️ OCCT limitation (use pipe_sweep_simple instead) |

---

## Examples by Concept

### Primitives
- **Box**: simple_box, v3_simple_box
- **Cylinder**: auto_references_cylinder_assembly
- **Cone**: (used in LEGO bricks)
- **Sphere**: (check color_showcase)

### Sketches & 2D
- **Basic extrusion**: simple_extrude, bracket_with_hole
- **Revolve**: bottle_revolve
- **Loft**: transition_loft
- **Sweep**: pipe_sweep_simple, pipe_sweep

### Boolean Operations
- **Union**: awesome_guitar_hanger (full assembly)
- **Subtract (holes)**: bracket_with_hole, guitar_hanger_with_holes
- **Hull**: hull_simple, hull_enclosure

### Patterns
- **Linear**: lego_brick_2x1, lego_brick_3x1, multi_material_enclosure
- **Circular**: mounting_plate_with_bolt_circle

### Finishing Operations
- **Fillet (rounded)**: rounded_mounting_plate
- **Chamfer (beveled)**: chamfered_bracket, lego_brick_2x1

### Positioning & References
- **Auto-references**: auto_references_box_stack, auto_references_cylinder_assembly, auto_references_rotation, auto_references_with_offsets
- **Named references**: guitar_hanger_named_points, references_demo
- **Anchors**: anchors_demo
- **Frame-based**: week5_frame_based_rotation

### Text & Labels
- **Primitives**: text_primitive_simple, text_primitive_sign, text_primitive_styles, text_primitive_vs_sketch
- **Operations**: text_operation_emboss_simple, text_operation_multi_face, text_operation_product_label
- **Engraving**: text_engraved, text_label, text_simple

### Materials & Colors
- **Basic**: color_demo
- **Multi-material**: multi_material_demo, multi_material_enclosure
- **Showcase**: color_showcase (300+ lines)

### Assemblies
- **Simple**: week5_assembly, auto_references_box_stack
- **Complex**: awesome_guitar_hanger (400+ lines), guitar_hanger_with_holes

### Metadata & Export
- **Metadata**: enhanced_metadata_demo
- **Export formats**: formats_demo

---

## Examples by Feature

### 🎯 Auto-Generated Anchors (v3.0)
Learn TiaCAD's powerful auto-reference system - no manual anchor definitions needed!

- auto_references_box_stack.yaml
- auto_references_cylinder_assembly.yaml
- auto_references_rotation.yaml
- auto_references_with_offsets.yaml
- anchors_demo.yaml

### 📐 Parametric Design
Examples with configurable parameters and ratios.

- lego_brick_2x1.yaml (LEGO standards)
- lego_brick_3x1.yaml (extended patterns)
- awesome_guitar_hanger.yaml (structural parameters)

### 🎨 Visual & Materials
Color, materials, and appearance.

- color_demo.yaml
- color_showcase.yaml
- multi_material_demo.yaml
- multi_material_enclosure.yaml

### 📝 Text & Typography
All text-related features.

**Primitives** (3D text objects):
- text_primitive_simple.yaml
- text_primitive_sign.yaml
- text_primitive_styles.yaml
- text_primitive_vs_sketch.yaml

**Operations** (text on surfaces):
- text_operation_emboss_simple.yaml
- text_operation_multi_face.yaml
- text_operation_product_label.yaml

**Styling**:
- text_engraved.yaml
- text_label.yaml
- text_simple.yaml

### 🔧 Practical Components
Real-world mechanical parts.

- mounting_plate_with_bolt_circle.yaml (standard mounting)
- rounded_mounting_plate.yaml (safety edges)
- bracket_with_hole.yaml (basic bracket)
- chamfered_bracket.yaml (finished bracket)
- v3_bracket_mount.yaml (v3.0 syntax)
- awesome_guitar_hanger.yaml (complete product)

---

## Detailed Example Walkthroughs

### <a name="simple_box"></a>simple_box.yaml ⭐

**Complexity:** Beginner
**Concepts:** Box primitive, minimal structure, parameters

**What it creates:** A simple 50×30×20mm box demonstrating the minimal YAML structure.

**Key concepts:**
- `metadata`: Optional documentation
- `parameters`: Reusable values
- `parts`: Define geometry (primitives or sketches)
- `export`: Specify output format

**Try it:**
```bash
tiacad build examples/simple_box.yaml
```

**Learning goals:**
- Understand YAML structure
- Learn about primitives
- See the basic workflow

---

### <a name="simple_extrude"></a>simple_extrude.yaml ⭐

**Complexity:** Beginner
**Concepts:** Sketch-based modeling, extrusion

**What it creates:** A simple extruded rectangle from a 2D sketch.

**Key concepts:**
- `sketches`: 2D profile definition
- `plane`: XY, XZ, or YZ
- `shapes`: Rectangle, circle, polygon
- `extrude`: Convert 2D → 3D

**Try it:**
```bash
tiacad build examples/simple_extrude.yaml
```

**Learning goals:**
- Understand sketch workflow
- Learn extrusion basics
- See sketch-to-3D conversion

---

### <a name="bracket_with_hole"></a>bracket_with_hole.yaml ⭐⭐

**Complexity:** Intermediate
**Concepts:** Boolean operations, holes, sketch subtract

**What it creates:** A 50×20×10mm bracket with a 5mm hole.

**Key concepts:**
- `sketches`: Multiple shapes in one sketch
- Boolean subtract with `operation: subtract`
- Positioning holes with offsets

**Try it:**
```bash
tiacad build examples/bracket_with_hole.yaml
```

**Learning goals:**
- Master boolean operations
- Learn hole-making patterns
- Understand sketch operations

**Design pattern:**
```yaml
sketches:
  profile:
    shapes:
      - type: rectangle  # Base shape
      - type: circle     # Hole
        operation: subtract  # Cut out
```

---

### <a name="lego_brick_2x1"></a>lego_brick_2x1.yaml ⭐⭐

**Complexity:** Intermediate (verging on Advanced)
**Concepts:** Parametric design, patterns, LEGO standards

**What it creates:** A fully parametric LEGO-compatible 2×1 brick with:
- 2 studs on top
- Hollow underside with support posts
- Chamfered stud tops
- Standard LEGO dimensions

**Key concepts:**
- Parametric ratios (LEGO standards)
- Linear patterns for stud arrays
- Multiple boolean operations
- Transform chains

**Try it:**
```bash
tiacad build examples/lego_brick_2x1.yaml
```

**Learning goals:**
- Advanced parametric design
- Pattern systems
- Real-world standards compliance
- Complex assemblies

**Why it's impressive:**
- 319 lines of parametric YAML
- Follows official LEGO dimensions
- Demonstrates pattern mastery
- Production-ready design

---

### <a name="awesome_guitar_hanger"></a>awesome_guitar_hanger.yaml ⭐⭐⭐

**Complexity:** Advanced
**Concepts:** Complete assembly, structural design, v3.0 auto-anchors

**What it creates:** A professional wall-mounted guitar hanger with:
- 120×70×15mm mounting plate
- Angled support beam with reinforcements
- Structural gussets
- Countersunk screw holes
- Ready for 3D printing

**Key concepts:**
- Auto-generated anchors (`beam.face_front`, `plate.face_top`)
- Boolean unions for complete assembly
- Structural reinforcements
- Optimized geometry

**Try it:**
```bash
tiacad build examples/awesome_guitar_hanger.yaml
```

**Learning goals:**
- Large-scale assembly design
- Structural engineering
- Auto-anchor mastery
- Production-ready modeling

**Why it's awesome:**
- 414 lines of well-documented YAML
- Real-world structural analysis
- Complete auto-anchor usage
- Print-ready output

---

## Learning Path

### 🌱 Start Here (Day 1)
1. simple_box.yaml - Understand structure
2. simple_extrude.yaml - Learn sketches
3. bracket_with_hole.yaml - Master booleans
4. simple_guitar_hanger.yaml - Multiple parts

### 🌿 Build Skills (Week 1)
5. mounting_plate_with_bolt_circle.yaml - Patterns
6. rounded_mounting_plate.yaml - Finishing
7. hull_simple.yaml - Hull operations
8. text_primitive_simple.yaml - Text basics

### 🌳 Advanced Techniques (Week 2)
9. auto_references_box_stack.yaml - Auto-anchors
10. lego_brick_2x1.yaml - Parametric design
11. multi_material_demo.yaml - Materials
12. awesome_guitar_hanger.yaml - Complete projects

---

## Common Use Cases

### 📦 Enclosures
- hull_enclosure.yaml - Convex hull wrapping
- multi_material_enclosure.yaml - Multi-part enclosures

### 🔩 Mounting Solutions
- mounting_plate_with_bolt_circle.yaml - Standard bolt patterns
- rounded_mounting_plate.yaml - Safe edges
- bracket_with_hole.yaml - Basic brackets
- chamfered_bracket.yaml - Finished brackets

### 🎸 Holders & Hangers
- simple_guitar_hanger.yaml - Basic concept
- guitar_hanger_with_holes.yaml - Wall mounting
- awesome_guitar_hanger.yaml - Production design

### 🧱 Parametric Components
- lego_brick_2x1.yaml - 2-stud brick
- lego_brick_3x1.yaml - 3-stud brick

---

## Tips for Using Examples

### 🔧 Modify Parameters
Most examples use `parameters:` section. Try changing values:

```yaml
parameters:
  width: 50   # Change to 100
  height: 20  # Change to 40
```

Then rebuild: `tiacad build examples/modified_example.yaml`

### 🎨 Mix and Match
Combine concepts from multiple examples:
- Take pattern from `lego_brick_2x1.yaml`
- Add finishing from `rounded_mounting_plate.yaml`
- Use auto-anchors from `auto_references_box_stack.yaml`

### 🧪 Learn from Tests
Many examples have corresponding tests in `tiacad_core/tests/`:
- test_auto_references.py
- test_integration_gusset.py
- test_visual_regression.py

---

## Known Issues

### ⚠️ pipe_sweep.yaml
**Status:** Known OCCT geometry limitation
**Issue:** Sweep operations fail with hollow profiles + cut operations on sharp corners
**Workaround:** Use `pipe_sweep_simple.yaml` instead, or avoid sharp-corner cuts on swept geometry
**Details:** See CHANGELOG.md "Known Limitations" section

### ⚠️ error_demo.yaml
**Status:** Intentionally broken (for error handling testing)
**Purpose:** Validates TiaCAD error reporting system
**Action:** Do not use as a template

---

## Next Steps

### 📚 Documentation
- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Complete syntax reference
- [TUTORIAL.md](TUTORIAL.md) - Step-by-step guide
- [GLOSSARY.md](GLOSSARY.md) - Terminology reference

### 🛠️ Developer Resources
- [MIGRATION_GUIDE_V3.md](../developer/MIGRATION_GUIDE_V3.md) - Upgrade guide
- [TESTING_GUIDE.md](../developer/TESTING_GUIDE.md) - Testing reference
- [TERMINOLOGY_GUIDE.md](../developer/TERMINOLOGY_GUIDE.md) - Canonical terms

### 🎯 Create Your Own
Start with a working example, modify parameters, then add your own features. The learning path above provides a natural progression from simple to complex designs.

---

## File Locations

**Examples directory:** `examples/`
**Build output:** `output/` (auto-created)
**Test references:** `tiacad_core/visual_references/`

---

**Status:** Active example guide
**Scope:** Includes working examples plus a small number of intentional or documented special cases
