# Mental Models and Language Design for TiaCAD

**Date**: November 2025
**Status**: Design Discussion
**Purpose**: Explore how users conceptualize modeling and composition, and how TiaCAD's language can better align with mental models

## Overview

This document explores different ways people think about 3D modeling and composition, analyzes TiaCAD's current terminology, and proposes language improvements to make the mental model easier to hold and translate into our YAML syntax.

## Common Mental Models for CAD Composition

### 1. Physical Assembly Model 🔧
**Mental image**: Parts on a workbench, screwing things together

- **Terms**: assembly, component, sub-assembly, mate, constraint
- **Strength**: Maps directly to real-world manufacturing processes
- **Challenge**: Implies fixed hierarchical relationships
- **Examples**: SolidWorks, traditional mechanical CAD

### 2. Scene Graph Model 🌳
**Mental image**: Tree of objects, transforms flow down branches

- **Terms**: node, parent/child, scene, hierarchy, transform propagation
- **Strength**: Clear parent-child relationships, familiar to programmers
- **Challenge**: Can feel arbitrary for non-nested objects
- **Examples**: 3D game engines (Unity, Unreal), 3D graphics tools (Blender)

### 3. Reference Frame Model 📐
**Mental image**: Coordinate systems attached to objects

- **Terms**: frame, local/world space, origin, basis vectors
- **Strength**: Mathematically precise and unambiguous
- **Challenge**: Requires strong spatial reasoning ability
- **Examples**: Robotics, aerospace engineering

### 4. Spatial Relationships Model 🎯
**Mental image**: Objects positioned relative to landmarks

- **Terms**: anchor point, relative to, offset from, aligned with
- **Strength**: Natural language descriptions ("put the hook 10mm above the backplate")
- **Challenge**: Can become complex with many relationships
- **Examples**: TiaCAD v3.0 (current model)

### 5. Recipe/Procedure Model 📝
**Mental image**: Step-by-step instructions

- **Terms**: step, operation, apply, result
- **Strength**: Matches how people describe processes verbally
- **Challenge**: Ordering dependencies can be opaque
- **Examples**: OpenSCAD, procedural modeling tools

## TiaCAD's Current Mental Model

TiaCAD uses a **hybrid reference-based composition model**:

### Key Characteristics
- **Parts are independent** – no explicit parent-child hierarchy
- **Relationships through spatial references** – parts reference positions/orientations, not each other
- **Declarative operations** – describe what you want, not how to compute it
- **Auto-generated references** – every part provides canonical attachment points
- **Local frame offsets** – offsets follow reference orientation

### What Makes TiaCAD Different
Unlike traditional CAD (SolidWorks, Fusion 360) which use **hierarchical assemblies**, TiaCAD uses **flat part collections with spatial references**. This is closer to how **scene graphs** work but without rigid parent-child constraints.

## Language Tensions & Ambiguities

### 1. "Part" Ambiguity

**Current usage**: "Part" = any geometric object (primitive, imported, or derived)

```yaml
parts:
  box1:              # Is this a "part"?
    type: box
    width: 10
```

**Mental confusion**: In manufacturing, "part" often implies a *final component* that gets assembled. Is `box1` a part, or is it a primitive shape that will *become part of* a part?

**Alternative terms**:
- `Shape` – emphasizes geometry, not manufacturing
- `Object` – generic, but clear
- `Solid` – CAD-specific terminology
- `Body` – used in some CAD systems
- `Element` – compositional terminology
- `Piece` – informal, approachable

**Recommendation**: Consider `shapes:` or `elements:` to reduce manufacturing connotation, or explicitly document what "Part" means in TiaCAD.

### 2. "SpatialRef" Technical Abstraction

**Current usage**: `SpatialRef` = position + orientation data structure

**Mental confusion**: Technical term doesn't map to intuitive spatial thinking. Users think "I want to attach this *here*" not "I want to reference this spatial ref."

**Alternative terms**:
- `Anchor` – nautical metaphor, implies fixed attachment point
- `Pin` – engineering drawing metaphor
- `Landmark` – navigation metaphor
- `Marker` – visual metaphor
- `Location` – simple, direct
- `ReferencePoint` – explicit but verbose

**Recommendation**: Use "anchor" in user-facing documentation and consider `anchors:` as YAML section name.

### 3. Implicit Composition Model

**Current**: YAML document implicitly represents a model/assembly

**Mental confusion**: What *is* the document? A model? A design? An assembly? A recipe?

**Current structure**:
```yaml
parts:
  [...]
operations:
  [...]
references:
  [...]
export:
  [...]
```

**Alternative approaches**:
```yaml
# Option A: Explicit model concept
model:
  name: guitar_hanger
  type: assembly

parts:
  [...]

# Option B: Explicit assembly concept
assembly:
  name: guitar_hanger
  components:
    [...]

# Option C: Design document concept
design:
  name: guitar_hanger
  description: "Wall-mounted guitar hanger"
  elements:
    [...]
```

**Recommendation**: Add optional top-level metadata section to make document purpose explicit.

### 4. "Operations" Category Too Broad

**Current**: Everything is an "operation"

**Mental models differ by operation type**:
- **Moving/rotating** = transforms (change position, not geometry)
- **Fillet/chamfer** = modifications or features (change geometry)
- **Boolean union** = combining or merging (relationships between parts)
- **Patterns** = replication or arrays (multiplying objects)

**Current (unified)**:
```yaml
operations:
  - transform: [...]
  - fillet: [...]
  - union: [...]
  - pattern: [...]
```

**Alternative (categorized)**:
```yaml
transforms:
  - move: [...]
  - rotate: [...]

features:
  - fillet: [...]
  - chamfer: [...]

combinations:
  - union: [...]
  - subtract: [...]

replications:
  - array: [...]
```

**Recommendation**: Consider categorizing operations in documentation and examples, even if YAML structure remains flat.

### 5. "References" Section Purpose

**Current**: `references:` defines custom spatial locations

**Mental model**: This is really about defining **attachment points** or **anchors** for later use

**Current syntax**:
```yaml
references:
  mounting_hole_top:
    part: bracket
    face: top
    offset: [5, 5, 0]
```

**Alternative language**:
```yaml
anchors:  # or: landmarks, markers, attachment_points
  mounting_hole_top:
    on: bracket        # vs "part"
    face: top
    offset: [5, 5, 0]
```

**Recommendation**: `anchors:` is more intuitive than `references:` for spatial positioning.

## Recommendations for Cognitive Clarity

### Strategy 1: Match Mental Model to Domain

Ask: *"Are users thinking about assembly (like LEGO), composition (like music), or construction (like building)?"*

**Assembly language**: component, mate, assemble, fit, attach
**Composition language**: element, compose, combine, arrange, layer
**Construction language**: build, add, place, join, modify

### Strategy 2: Consistent Spatial Metaphor

The `SpatialRef` system is powerful but abstract. Pick a consistent metaphor:

**Option A: "Anchor" metaphor**
```yaml
anchors:
  hook_position:
    at: backplate.face_front
    offset: [0, 0, 10]

attach:
  what: hook
  to: hook_position
```

**Option B: "Pin" metaphor** (like engineering drawings)
```yaml
pins:
  assembly_point_1: [...]

align:
  hook.center --> assembly_point_1
```

**Option C: "Landmark" metaphor**
```yaml
landmarks:
  where_hook_goes: [...]

place:
  hook: at where_hook_goes
```

### Strategy 3: Separate Concerns in Language

Consider whether these concepts should have distinct vocabulary:

1. **Geometric primitives** (box, cylinder) → `primitives:` or `shapes:`
2. **Imported parts** (STL files) → `imports:` or `external:`
3. **Derived geometry** (extrusions, booleans) → `features:` or `constructed:`
4. **Spatial references** → `anchors:`, `landmarks:`, `pins:`
5. **Positioning** → `place:`, `position:`, `locate:`
6. **Relationships** → `align:`, `attach:`, `mate:`

### Strategy 4: Make the Mental Model Explicit

Add a top-level concept that makes clear what the document represents:

```yaml
model:
  name: guitar_hanger
  description: "Wall-mounted guitar hanger"
  type: assembly  # or: part, mechanism, structure

shapes:
  [...]

anchors:
  [...]
```

## Guiding Questions for Future Language Design

### User Persona
1. Who is your primary user?
   - Engineers (familiar with CAD hierarchy)?
   - Makers (think about physical assembly)?
   - Programmers (comfortable with abstraction)?
   - Artists (visual/spatial thinkers)?

### Primary Mental Model
2. What's the core activity?
   - *Assembling* existing parts?
   - *Constructing* something from scratch?
   - *Composing* elements into a whole?
   - *Writing a recipe* that generates geometry?

### Relationship Model
3. What's the relationship between parts?
   - Are parts *contained* in assemblies (hierarchy)?
   - Are parts *referenced* by position (current TiaCAD)?
   - Are parts *constrained* to each other (parametric)?

### Document Purpose
4. What is the YAML document?
   - A *recipe* that generates a model?
   - A *description* of an assembly?
   - A *scene file* defining a 3D arrangement?
   - A *blueprint* for construction?

## Specific Recommendations for TiaCAD

### Short-term (clearer without breaking changes)
1. **Terminology in documentation**: Consistently refer to `SpatialRef` as "anchors" or "reference points" in user-facing docs
2. **Add glossary**: Define what "Part" means in TiaCAD vs traditional CAD
3. **Document mental model explicitly**: "TiaCAD uses reference-based composition, not hierarchical assembly"
4. **Operation categorization in docs**: Group operations by type in documentation even if YAML is flat

### Medium-term (aliases/ergonomics)
1. **Add YAML aliases**: Allow `anchors:` as alias for `references:`
2. **Add optional metadata section**:
   ```yaml
   model:
     name: guitar_hanger
     description: "Wall-mounted guitar hanger"
   ```
3. **Enhanced auto-references naming**: Consider more intuitive names
4. **Visual documentation**: Diagrams showing the reference-based mental model

### Long-term (potential v4.0 breaking changes)
1. **Rename `Part` → `Shape` or `Element`** to reduce manufacturing connotation
2. **Rename `references:` → `anchors:`** for intuitive spatial metaphor
3. **Categorize operations** into `transforms:`, `features:`, `combinations:`, `replications:`
4. **Make composition model explicit** with required top-level `model:` or `assembly:` block
5. **Consistent spatial language**: "place", "attach", "align" operations with anchor-based syntax

## Key Insight

**TiaCAD's reference-based, declarative model is actually more intuitive than traditional hierarchical CAD once users "get it"**, but the language could better telegraph what makes it different.

The biggest opportunity is making the **spatial reference system** more intuitive through metaphor (anchors, pins, landmarks) rather than technical terminology (SpatialRef, references).

## Next Steps

1. **User research**: Test terminology with target users
2. **Glossary creation**: Clear definitions for TiaCAD-specific terms
3. **Documentation update**: Rewrite tutorials with clearer mental model language
4. **Prototype v4.0 syntax**: Experiment with anchor-based language
5. **Migration path**: Plan how to evolve language while maintaining compatibility

## References

- `AUTO_REFERENCES_GUIDE.md` - Current auto-reference system
- `ARCHITECTURE_DECISION_V3.md` - v3.0 spatial reference design
- `YAML_REFERENCE.md` - Current syntax reference
- `tiacad_core/geometry/spatial_references.py` - Implementation of SpatialRef
- `tiacad_core/part.py` - Part abstraction

---

**Feedback Welcome**: This is a living document. Please contribute insights about how you think about modeling and what language resonates with you.
