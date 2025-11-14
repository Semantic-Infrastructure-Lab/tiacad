# TiaCAD Terminology Guide

**Purpose**: Canonical terminology decisions for TiaCAD documentation, code, and user communication.
**Status**: Official terminology standard for v3.2+
**Last Updated**: 2025-11-14
**Applies To**: All documentation, error messages, examples, and user-facing communication

---

## Purpose & Usage

This guide ensures **consistent terminology** across all TiaCAD materials. When writing documentation, error messages, or examples, consult this guide for the correct term to use.

**For Contributors**:
- Check this guide before writing documentation
- Use these terms in error messages and user-facing output
- PR reviews should verify terminology consistency

**For Users**:
- This guide explains why TiaCAD uses specific terms
- Understanding these terms helps you read the docs more effectively

---

## Terminology Decision Principles

Our terminology choices balance:
1. **Technical correctness** - Use mathematically/geometrically accurate terms
2. **Industry standards** - Follow CAD/3D graphics conventions where applicable
3. **Approachable clarity** - Avoid unnecessary jargon, but don't oversimplify
4. **Consistency** - One canonical term per concept

When in doubt: **Prefer clarity over brevity, but technical accuracy over colloquialism.**

---

## CATEGORY 1: Spatial Coordinate Systems

### Local Frame ✅

**Use**: "Local frame" or "part's local frame"
**Don't use**: "coordinate system", "local coordinates", "coordinate frame"
**Technical definition**: A coordinate frame consisting of an origin point and three orthogonal axes (X, Y, Z)

**Why "local frame"**:
- ✅ Technically correct (frame = origin + axes)
- ✅ Industry standard in robotics, 3D graphics, game engines
- ✅ Shorter and easier to say than "local coordinate system"
- ✅ Matches our `Frame` dataclass in code

**Usage in docs**:
- "Offsets are applied in the anchor's local frame"
- "Each face anchor has its own local frame with a normal vector pointing outward"

**Example**:
```yaml
# Offset is relative to base.face_top's local frame
tower:
  box: {width: 20, depth: 20, height: 100}
  translate: base.face_top
  offset: [0, 0, 5]  # 5 units up in the face's local frame
```

---

### World Space ✅

**Use**: "World space"
**Don't use**: "global coordinates", "world coordinates", "global space"
**Technical definition**: The single global coordinate system in which all parts exist

**Why "world space"**:
- ✅ Standard in 3D graphics, game engines, robotics
- ✅ Pairs naturally with "local frame" (world space vs local frame)
- ✅ Shorter than "global coordinate system"

**Usage in docs**:
- "The base part is positioned at the origin of world space"
- "Without local frames, you'd need to calculate positions in world space manually"

---

### Offset ✅

**Use**: "Offset"
**Don't use**: "displacement", "shift", "delta"
**Technical definition**: A vector displacement from an anchor's position, specified in the anchor's local frame

**Why "offset"**:
- ✅ Industry standard in CAD, CNC, manufacturing
- ✅ Clear meaning: additional distance from a base position
- ✅ Matches YAML syntax: `offset: [x, y, z]`

**Usage in docs**:
- "Add an offset to position the part 5mm above the anchor"
- "Offsets are specified in the anchor's local frame"

---

## CATEGORY 2: Geometry Terms

### Face ✅

**Use**: "Face"
**Don't use**: "surface" (when referring to solid geometry)
**Technical definition**: A bounded planar or curved region that forms part of a solid's boundary

**Why "face"**:
- ✅ Standard CAD terminology (SolidWorks, Fusion 360, FreeCAD, OpenSCAD)
- ✅ Precise: A face is a bounded surface of a solid
- ✅ Matches CadQuery's `.faces()` selector
- ❌ "Surface" is too generic and could mean unbounded mathematical surfaces

**Usage in docs**:
- "Select the top face of the base part"
- "The face anchor includes the face's center position and outward normal"
- "Auto-generated anchors include `.face_top`, `.face_bot`, etc."

**Note**: "Surface" can be used in colloquial explanations ("the flat surface of the base"), but use "face" in technical contexts.

---

### Normal ✅

**Use**: "Normal" or "normal vector"
**Don't use**: "direction" (when referring to the perpendicular vector)
**Technical definition**: A vector perpendicular to a face, pointing outward from the solid

**Why "normal"**:
- ✅ Mathematically correct term in geometry
- ✅ Standard in 3D graphics, CAD, physics
- ✅ Precise meaning: perpendicular vector

**Usage in docs**:
- "The face anchor includes a normal vector pointing outward"
- "The normal determines which way is 'up' for the face's local frame"

**Contrast with "orientation"**: Use "normal" for a single perpendicular vector. Use "orientation" for a complete 3D frame.

---

### Orientation ✅

**Use**: "Orientation"
**Don't use**: "direction" (when referring to a complete frame), "rotation"
**Technical definition**: The rotational state of a 3D frame, defined by three orthogonal axes

**Why "orientation"**:
- ✅ Standard term for 3D rotational state
- ✅ Distinguishes from position (translation)
- ✅ Encompasses all three axes, not just one direction

**Usage in docs**:
- "The anchor's orientation determines how offsets are interpreted"
- "Face anchors include both position and orientation"

**Note**: "Rotation" refers to the *process* of changing orientation. "Orientation" is the *state*.

---

### Edge ✅

**Use**: "Edge"
**Don't use**: "line", "curve" (when referring to solid geometry)
**Technical definition**: The boundary between two faces of a solid; can be straight or curved

**Why "edge"**:
- ✅ Standard CAD term
- ✅ Precise: An edge is part of solid geometry, bounded by vertices
- ✅ Matches CadQuery's `.edges()` selector

**Usage in docs**:
- "Select an edge to fillet"
- "Edges can be straight or curved (e.g., after a fillet operation)"

**Note**: Use "line" only for abstract geometric lines, not solid boundaries.

---

## CATEGORY 3: Positioning Concepts

### Position (noun) ✅

**Use**: "Position"
**Don't use**: "location" (in technical contexts)
**Technical definition**: The spatial coordinates of a point in 3D space

**Why "position"**:
- ✅ Standard in 3D graphics, robotics, physics
- ✅ Technical and precise
- ❌ "Location" is too geographic and vague

**Usage in docs**:
- "The anchor's position is at the center of the face"
- "Use anchors to define positions in 3D space"

---

### Translate (YAML keyword) ⚠️

**Use**: `translate:` in YAML (current v3.x)
**Document as**: "Position the part at an anchor"
**Future (v4.0)**: Will likely change to `place:` or `at:` (Phase 3.4)

**Why this is imperfect**:
- ✅ "Translate" is mathematically correct (spatial translation)
- ✅ Used in OpenGL, game engines, 3D graphics
- ❌ Reads like code/math, not design intent
- 🚨 **Breaking change** to rename - must wait for v4.0

**Usage in docs (v3.x)**:
- YAML: `translate: base.face_top`
- Docs: "The `translate` operation positions a part at an anchor"
- **Never say**: "translate moves a part" (implies relative motion, not absolute positioning)

**Documentation strategy**:
- In tutorials: "Use `translate` to position parts at anchors"
- In reference: "The `translate` keyword specifies the anchor to position the part at"

---

## CATEGORY 4: Reference/Anchor Terminology

### Anchor (user-facing) ✅

**Use**: "Anchor" in all user-facing documentation
**Don't use**: "Reference" (in user docs, though YAML accepts both)
**Technical definition**: A marked spatial position with orientation, used for positioning parts

**Why "anchor"**:
- ✅ User-friendly spatial metaphor ("anchor points on a workbench")
- ✅ Phase 1 decision to improve clarity
- ✅ Will become the only term in v4.0 (Phase 3.1)
- ✅ More intuitive than abstract "reference"

**Usage in docs**:
- "Position parts using anchors"
- "Every part has auto-generated anchors like `.face_top` and `.center`"
- "Define custom anchors in the `anchors:` section"

**YAML syntax (v3.2+)**:
Both `anchors:` and `references:` are valid in YAML files:
```yaml
# Both work - use whichever feels more natural
anchors:
  mount_point: base.face_top

references:
  mount_point: base.face_top
```

**Error messages**: Always use "anchor"
- ✅ "Anchor 'base.face_top' not found in part 'base'"
- ❌ "Reference 'base.face_top' not found"

---

### Auto-Generated Anchors ✅

**Use**: "Auto-generated anchors"
**Don't use**: "auto-references", "built-in anchors", "default anchors"
**Technical definition**: Anchors automatically created for each part (e.g., `.face_top`, `.center`, `.origin`)

**Why this term**:
- ✅ Clear and explicit: anchors that are automatically generated
- ✅ Contrasts with "named anchors" (user-defined)
- ❌ "Built-in" implies they're part of the language (they're per-part)
- ❌ "Auto-references" uses deprecated terminology

**Usage in docs**:
- "Every part has auto-generated anchors for faces, center, origin, and axes"
- "You can reference auto-generated anchors like `base.face_top`"

**List of auto-generated anchors**:
- `.center` - Geometric center of the part
- `.origin` - Origin point (0, 0, 0) in part's local frame
- `.face_top`, `.face_bot`, `.face_left`, `.face_right`, `.face_front`, `.face_back`
- `.axis_x`, `.axis_y`, `.axis_z`

---

### Named Anchors ✅

**Use**: "Named anchors" or "custom anchors"
**Don't use**: "user-defined references"
**Technical definition**: Anchors explicitly defined by the user in the `anchors:` section

**Usage in docs**:
- "Define named anchors for complex positioning"
- "Named anchors can combine auto-generated anchors with offsets"

**Example**:
```yaml
anchors:
  mount_point: base.face_top + [10, 10, 0]  # Named anchor
```

---

## CATEGORY 5: Operations

### Operation Categories ✅

**Use**: Friendly term + technical term in parentheses
**YAML type values**: Use technical terms

**The four categories**:

1. **Positioning Operations (Transforms)**
   - User-friendly: "Positioning"
   - Technical: "Transforms"
   - YAML: `type: transform`
   - Examples: `translate`, `rotate`, `align_to_face`

2. **Shape Modification Operations (Features)**
   - User-friendly: "Shape Modification" or "Features"
   - Technical: "Features"
   - YAML: `type: feature`
   - Examples: `fillet`, `chamfer`, `extrude`

3. **Combining Operations (Booleans)**
   - User-friendly: "Combining"
   - Technical: "Booleans"
   - YAML: `type: boolean`
   - Examples: `union`, `difference`, `intersection`

4. **Replication Operations (Patterns)**
   - User-friendly: "Replication"
   - Technical: "Patterns"
   - YAML: `type: pattern`
   - Examples: `linear_pattern`, `circular_pattern`, `grid_pattern`

**Usage in docs**:
- Section headers: "Positioning Operations (Transforms)"
- First reference: "Positioning operations (also called transforms) change the position or orientation of a part"
- Subsequent references: Can use either term
- YAML: Always use technical term for `type:` field

---

### Operation Recipients ✅

**Use**: Context-specific terms (don't unify)
**Why**: Different operations have different semantics

**Transform operations**: Use `input:`
```yaml
tower_positioned:
  type: transform
  input: tower
  transforms:
    - translate: base.face_top
```

**Boolean operations**: Use `base:` and `tools:` or `targets:`
```yaml
combined:
  type: boolean
  operation: union
  base: base_plate
  tools: [tower, bracket]
```

**Pattern operations**: Use `input:`
```yaml
bolts:
  type: pattern
  input: bolt
  pattern_type: circular
```

**Don't force unification**: Each operation type has appropriate terminology.

---

## CATEGORY 6: Structure & Organization

### Part vs Shape ⚠️

**Use (v3.x)**: "Part"
**Future (v4.0)**: "Shape" (Phase 3.1 planned rename)
**Technical definition**: An individual 3D solid or geometry defined in the `parts:` section

**Why "part" (v3.x)**:
- ✅ Standard in CAD and manufacturing
- ✅ Primary audience is engineering/CAD users
- ⚠️ Slight manufacturing bias (not ideal for art/education)

**Why "shape" (v4.0)**:
- ✅ More general term (works for art, education, organic forms)
- ✅ Less manufacturing-centric
- 🚨 Breaking change - requires v4.0 major version bump

**Usage in docs (v3.x)**:
- "Define parts in the `parts:` section"
- "Each part can be positioned using anchors"
- "This assembly has 5 parts"

**Transition note**: In v4.0, `parts:` will become `shapes:` (Phase 3.1)

---

### Assembly ✅

**Use**: "Assembly"
**Technical definition**: A model composed of multiple parts positioned relative to each other

**Usage in docs**:
- "This design creates an assembly with 3 parts"
- In metadata: `type: assembly`

**When to use**:
- For models with 2+ parts
- When emphasizing multi-part composition
- In `metadata.type` field

---

### Model ✅

**Use**: "Model"
**Technical definition**: The complete 3D geometry output from TiaCAD (single part or assembly)

**Usage in docs**:
- "Export your model as STL"
- "The model is generated from your design"
- "Preview the 3D model"

**When to use**:
- When referring to the 3D output/result
- When discussing export formats
- When talking about visualization

---

### Design ✅

**Use**: "Design"
**Technical definition**: The TiaCAD YAML file and its creative intent

**Usage in docs**:
- "This design defines a guitar hanger"
- "Your design files go in `designs/`"
- "Parametric design allows easy customization"

**When to use**:
- When referring to the YAML file
- When discussing creative/engineering intent
- When talking about the design process

**Distinction**:
- **Design** = the YAML file (input)
- **Model** = the 3D geometry (output)
- **Assembly** = a multi-part model

---

### Parameters ✅

**Use**: "Parameters" (noun), "parametric" (adjective)
**Don't use**: "parametrics" (not a word)
**Technical definition**: Named variables in the `parameters:` section that can be used in expressions

**Usage in docs**:
- "This design has 8 parameters"
- "TiaCAD is a parametric CAD system"
- "Parametric design enables easy customization"

**YAML section**: `parameters:`

---

## CATEGORY 7: Documentation Voice

### Tutorial Voice ✅

**Use**: Second person ("you")
**Don't use**: Third person ("the user"), role-specific terms ("the designer")

**Why "you"**:
- ✅ Direct and friendly
- ✅ Standard for tutorials and guides
- ✅ Encourages engagement

**Usage**:
- "You position parts using anchors"
- "You can define custom anchors"
- "Start by creating a `parts:` section"

**Apply to**: Tutorials, quickstarts, examples, getting started guides

---

### Reference Voice ✅

**Use**: Third person ("users") or passive voice
**Don't use**: Role-specific terms ("designers", "engineers")

**Why neutral voice**:
- ✅ Professional tone for reference documentation
- ✅ Doesn't assume user's role or background

**Usage**:
- "Users can define custom anchors in the `anchors:` section"
- "Parts are positioned using spatial anchors"
- "The `translate` operation positions a part at an anchor"

**Apply to**: Reference documentation, technical specs, API docs

---

### File Terminology ✅

**Use**: Context-dependent

**When discussing file format**: "YAML file"
- "TiaCAD uses YAML file format"
- "The YAML file contains your design"

**When discussing content**: "Design" or "design file"
- "Save your design as `guitar_hanger.yaml`"
- "Open the design file in your editor"

**When discussing technical parsing**: "TiaCAD file"
- "Parse the TiaCAD file"
- "The TiaCAD file schema defines valid structure"

---

## Quick Reference Table

| Concept | ✅ Use This | ❌ Don't Use | Context |
|---------|------------|-------------|---------|
| **Spatial** |
| Coordinate reference | Local frame | coordinate system, local coordinates | Always |
| Global space | World space | global coordinates | Always |
| Additional positioning | Offset | displacement, shift | Always |
| **Geometry** |
| Solid boundary | Face | surface | CAD terminology |
| Perpendicular vector | Normal | direction (for vectors) | Math/technical |
| 3D rotational state | Orientation | direction (for frames) | Technical |
| Solid boundary line | Edge | line, curve | CAD terminology |
| **Positioning** |
| Spatial coordinate | Position | location | Technical |
| YAML positioning | translate | — | v3.x keyword |
| Documentation | "position at anchor" | "translate to" | User-facing |
| **Anchors** |
| User term | Anchor | reference | User-facing |
| YAML section | `anchors:` or `references:` | — | Both valid |
| Per-part anchors | Auto-generated anchors | auto-references, built-in | Always |
| User-defined | Named anchors | user-defined references | Always |
| **Operations** |
| Category 1 | Positioning (Transforms) | — | Docs |
| Category 2 | Shape Modification (Features) | — | Docs |
| Category 3 | Combining (Booleans) | — | Docs |
| Category 4 | Replication (Patterns) | — | Docs |
| **Structure** |
| YAML entity | Part (v3.x) → Shape (v4.0) | object | YAML |
| Multiple parts | Assembly | — | Multi-part models |
| 3D output | Model | — | Export context |
| YAML file | Design | — | Creative intent |
| **Documentation** |
| Tutorial voice | You | user, designer, engineer | Tutorials |
| Reference voice | Users / passive voice | designer, engineer | Reference docs |

---

## Version Evolution

### v3.0 - v3.2 (Current)
- "Anchor" terminology introduced (Phase 1)
- YAML accepts both `anchors:` and `references:` (Phase 2.2)
- Documentation standardization (this guide)

### v4.0 (Planned - Phase 3)
- `parts:` → `shapes:` (breaking change)
- `references:` removed, only `anchors:` accepted (breaking change)
- `translate:` → `place:` or `at:` (breaking change, Phase 3.4)
- Operation categorization in YAML structure (Phase 3.2)

---

## Enforcement

### Documentation PRs
- All PRs must follow this terminology guide
- Reviewers should check for consistency
- Link to this guide in PR template

### Error Messages
- Must use "anchor" (not "reference")
- Should use technical terms from this guide
- Should suggest correct terminology if user makes mistake

### Code Comments
- Internal code can use technical terms (`Reference`, `Frame`, etc.)
- User-facing strings must follow this guide

---

## Updates

**When to update this guide**:
- Phase completions (Phase 3, Phase 4, etc.)
- Version releases (v4.0, v5.0, etc.)
- User feedback reveals confusion
- New concepts added to TiaCAD

**How to propose changes**:
1. Open an issue explaining the terminology problem
2. Propose the new term with rationale
3. Update this guide via PR
4. Update affected documentation

**Document owner**: TiaCAD Core Team
**Review cycle**: Quarterly or before major releases
**Next review**: Before v4.0 planning (2026-Q2)

---

**End of Terminology Guide**
