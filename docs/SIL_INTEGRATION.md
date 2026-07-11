# TiaCAD & the Semantic Infrastructure Lab

**How TiaCAD Embodies SIL Principles and Integrates with the Semantic OS**

Version: 1.0
Last Updated: 2025-12-07

---

## Table of Contents

1. [TiaCAD's Role in SIL](#tiacads-role-in-sil)
2. [SIL Principles in Action](#sil-principles-in-action)
3. [Layer 2: Domain Module](#layer-2-domain-module)
4. [Integration Patterns](#integration-patterns)
5. [Progressive Disclosure in CAD](#progressive-disclosure-in-cad)
6. [Reference-Based Composition](#reference-based-composition)
7. [Future Vision](#future-vision)

---

## TiaCAD's Role in SIL

**TiaCAD** is a production component of the [Semantic Infrastructure Lab (SIL)](https://github.com/Semantic-Infrastructure-Lab/SIL) — building the semantic substrate for intelligent systems.

### Position in the Semantic OS

```
Semantic OS Architecture
├── Layer 1: Kernel (TIA orchestration, Beth knowledge mesh, Gemma provenance)
├── Layer 2: Domain Modules
│   ├── TiaCAD ← Geometric/CAD reasoning
│   ├── Pantheon (Semantic IR)
│   ├── Morphogen (Universal computation)
│   └── ...
├── Layer 3: Tools (reveal, Scout, etc.)
└── Layer 4: Interfaces (CLI, web, etc.)
```

**TiaCAD provides:**
- **Geometric reasoning** - Declarative 3D modeling
- **Parametric design** - Mathematical relationships in physical space
- **Spatial composition** - Reference-based assembly model
- **Verifiable CAD** - Deterministic, testable geometry generation

---

## SIL Principles in Action

TiaCAD exemplifies all core SIL principles. Here's how:

### Principle #1: Progressive Disclosure

> **"Orient → Navigate → Focus. Never show everything at once."**

**In TiaCAD:**

```yaml
# LEVEL 1: ORIENT - High-level structure
metadata:
  name: Guitar Hanger

parameters:
  hook_width: 50

parts:
  base_plate: ...
  hook: ...

operations:
  final_assembly: ...
```

**Progressive exploration:**
```bash
# LEVEL 1: ORIENT - See structure
reveal awesome_guitar_hanger.yaml
# Returns: metadata, parameters, parts, operations sections

# LEVEL 2: NAVIGATE - Explore specific section
reveal awesome_guitar_hanger.yaml --range 30-60
# Returns: Just the parts section

# LEVEL 3: FOCUS - Extract specific part
grep -A 20 "hook:" awesome_guitar_hanger.yaml
# Returns: Full hook definition
```

**v3.1 DAG System** (planned) will extend this:
```bash
# LEVEL 1: ORIENT - Dependency summary
tiacad build design.yaml --show-deps-summary
# Output: "23 parts, 45 operations, 12 parameters"

# LEVEL 2: NAVIGATE - Visual graph
tiacad build design.yaml --show-deps
# Output: Interactive dependency graph

# LEVEL 3: FOCUS - Track specific changes
tiacad build design.yaml --watch --param hook_width
# Output: Real-time rebuild on parameter change
```

---

### Principle #2: Composability First

> **"Build tools that do one thing well, then orchestrate them into workflows."**

**TiaCAD's Reference-Based Composition:**

Unlike traditional CAD (hierarchical parent-child assemblies), TiaCAD uses **spatial references** for composability:

```yaml
# Parts are PEERS, not nested
parts:
  base:
    primitive: box
    # No "children" - it's independent

  cap:
    primitive: cylinder
    # Not "inside" base - it's a peer

operations:
  # Composition via SPATIAL REFERENCES
  cap_positioned:
    type: transform
    input: cap
    transforms:
      - translate:
          to: base.face_top  # Reference, not parent-child
```

**Why this matters for SIL:**
- Parts are composable units (like functions)
- No hidden dependencies (explicit references)
- Can be tested independently
- Orchestrated by TIA, not embedded hierarchies

**Integration with other SIL tools:**
```bash
# TiaCAD generates geometry
tiacad build bracket.yaml > bracket.stl

# reveal explores structure
reveal bracket.yaml --outline

# Beth finds similar designs
tia beth explore "bracket mounting hole pattern"

# Scout reviews design quality
scout review-cad bracket.yaml
```

---

### Principle #3: Clarity

> **"Explicit is better than implicit. No hidden magic."**

**TiaCAD's explicit design:**

```yaml
# BAD (implicit, magical)
box:
  size: [10, 10, 10]  # Which dimension is which?

# GOOD (explicit, clear)
box:
  primitive: box
  parameters:
    width: 10   # X dimension
    height: 10  # Y dimension
    depth: 10   # Z dimension
  origin: center  # Explicit origin point
```

**All behavior is explicit:**
- ✅ Origins specified (`center`, `corner`)
- ✅ Transformations sequential (order matters, documented)
- ✅ References explicit (`base.face_top`, not magic positioning)
- ✅ Units in comments (millimeters default, stated)
- ✅ No defaults without documentation

---

### Principle #4: Simplicity

> **"Minimal essential complexity. Declarative over imperative."**

**Compare approaches:**

**Traditional CAD (Procedural - Complex):**
```python
# 30 lines of code
workplane = cq.Workplane("XY")
box = workplane.box(10, 10, 10)
box = box.translate((5, 5, 5))
box = box.rotate((0, 0, 0), (1, 0, 0), 45)
cylinder = cq.Workplane("XY").cylinder(5, 20)
# ... manual calculations for positioning
```

**TiaCAD (Declarative - Simple):**
```yaml
# 15 lines of YAML
parts:
  box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center

  cylinder:
    primitive: cylinder
    radius: 5
    height: 20
```

**Complexity lives in the right place:**
- Domain logic → YAML (declarative, readable)
- Implementation → Python (tested, hidden)
- User sees → Simple, clear intent

---

### Principle #5: Verifiability

> **"Can be validated, tested, and proven correct."**

**TiaCAD's verification strategy:**

```
Comprehensive Test Suite (see TEST_STATUS.json for current counts)
├── Unit Tests (per-builder validation)
├── Integration Tests (full YAML → STL pipeline)
├── Correctness Tests (dimensional accuracy, geometry validation)
├── Visual Regression Tests (rendering consistency)
└── Schema Validation (YAML structure verification)
```

**Deterministic geometry:**
- Same YAML → Same geometry (always)
- Reproducible builds
- Version-controlled designs
- Testable parameters

**Example correctness test:**
```python
def test_box_dimensions():
    """Verify box has exact specified dimensions"""
    model = parse_yaml("box: {width: 10, height: 20, depth: 30}")
    bbox = model.bounding_box()
    assert bbox.width == 10.0  # Exact match
    assert bbox.height == 20.0
    assert bbox.depth == 30.0
```

---

## Layer 2: Domain Module

**What makes TiaCAD a Domain Module?**

Domain modules in the Semantic OS provide **specialized reasoning** for specific problem spaces. TiaCAD handles the **geometric/spatial domain**.

### Core Capabilities

| Capability | Description | SIL Value |
|------------|-------------|-----------|
| **Geometric Reasoning** | 3D solid modeling, boolean operations | Physical world representation |
| **Parametric Design** | Mathematical relationships in space | Composable design patterns |
| **Spatial References** | Anchor-based positioning | Semantic composition |
| **Deterministic Output** | Reproducible geometry | Verifiable artifacts |

### Integration Points

**TiaCAD connects to SIL ecosystem via:**

1. **Input:** YAML (human & AI readable)
2. **Output:** 3MF/STEP/STL (standard formats)
3. **References:** Spatial anchors (composable)
4. **Metadata:** Semantic tags, provenance

**Future integrations:**
- **Pantheon:** Geometric IR representation
- **GenesiGraph:** Design lineage tracking
- **Scout:** Automated design review
- **Beth:** CAD pattern knowledge mesh

---

## Progressive Disclosure in CAD

**Traditional CAD Problem:**
- Open SolidWorks → 100+ toolbars, 1000+ features
- Feature tree shows EVERYTHING
- Overwhelming for beginners, cluttered for experts

**TiaCAD Solution:**
Progressive disclosure at multiple levels:

### File Level

```bash
# LEVEL 1: What files exist?
ls examples/
# Returns: List of example designs

# LEVEL 2: What's in this design?
reveal examples/guitar_hanger.yaml
# Returns: Structure (metadata, parameters, parts, operations)

# LEVEL 3: Show me the hook part
reveal examples/guitar_hanger.yaml --range 45-75
# Returns: Just the hook part definition
```

### Semantic Level

```yaml
# LEVEL 1: Overview (metadata)
metadata:
  name: Parametric Bracket
  description: L-bracket with mounting holes

# LEVEL 2: Configurable aspects (parameters)
parameters:
  width: 80
  hole_count: 4

# LEVEL 3: Implementation (parts + operations)
parts:
  base_plate: ...
  mounting_holes: ...
```

### Execution Level (v3.1 planned)

```bash
# LEVEL 1: Quick summary
tiacad build bracket.yaml --summary
# "Building bracket.yaml (4 parts, 8 operations)"

# LEVEL 2: Build process
tiacad build bracket.yaml --verbose
# Shows each operation as it executes

# LEVEL 3: Full dependency graph
tiacad build bracket.yaml --show-deps --verbose
# Visual graph + execution trace
```

---

## Reference-Based Composition

**Core Innovation:** Parts are **peers** with **spatial anchors**, not **children** in hierarchies.

### The Anchor Model

Every part automatically generates **anchors** (reference points):

```yaml
parts:
  base:
    primitive: box
    # Auto-generates anchors:
    #   base.face_top, base.face_bottom
    #   base.center, base.corner

  lid:
    primitive: box

operations:
  # Position lid using base's anchor
  lid_positioned:
    type: transform
    input: lid
    transforms:
      - translate:
          to: base.face_top  # Semantic reference
```

**vs Traditional CAD:**
```
Traditional (Parent-Child):
Assembly
└── Base (parent)
    └── Lid (child of Base)
        └── Handle (child of Lid)

TiaCAD (Peer References):
Parts: [Base, Lid, Handle]
References:
  - Lid → Base.face_top
  - Handle → Lid.face_front
```

**SIL Benefit:** Composability without coupling

---

## Integration Patterns

### Pattern 1: TiaCAD + reveal

**Use Case:** Explore design structure without loading CAD software

```bash
# Orient: What's in this design?
reveal guitar_hanger.yaml

# Navigate: Show parameters
reveal guitar_hanger.yaml --range 10-25

# Focus: Extract hook geometry
reveal guitar_hanger.yaml hook
```

**Result:** Fast, token-efficient design exploration

---

### Pattern 2: TiaCAD + Beth

**Use Case:** Find similar design patterns

```bash
# User asks: "How do I create a bolt circle pattern?"
tia beth explore "bolt circle pattern mounting"

# Beth returns:
# - mounting_plate_with_bolt_circle.yaml (example)
# - YAML_REFERENCE.md (pattern operation docs)
# - Past designs using circular patterns

# User then:
reveal examples/mounting_plate_with_bolt_circle.yaml --outline
```

**Result:** Semantic CAD pattern discovery

---

### Pattern 3: TiaCAD + Gemma (Future)

**Use Case:** Track design provenance

```yaml
metadata:
  name: Bracket V2
  provenance:
    based_on: bracket_v1.yaml
    changes: "Increased hole spacing from 40mm to 50mm"
    author: TIA
    created: 2025-12-07
```

**Gemma tracks:**
- Design lineage (v1 → v2 → v3)
- Parameter changes over time
- Who/what/when/why for each modification

**Result:** Verifiable design history

---

### Pattern 4: TiaCAD + Scout (Future)

**Use Case:** Automated design review

```bash
scout review-cad bracket.yaml

# Scout checks:
# - Structural integrity (wall thickness, stress points)
# - Manufacturability (draft angles, undercuts)
# - Standards compliance (hole sizes, tolerances)
# - Best practices (fillet radii, material efficiency)
```

**Result:** AI-powered design validation

---

## Future Vision

**Note (2026-07-11):** the quarter labels below predate `ROADMAP.md` becoming
the canonical planning doc. v3.1's Dependency Graph shipped as described
(Q1 2026). The Semantic Constraints work is retimed to **Q4 2026** in
`ROADMAP.md` (not Q2) — see that file for the current authoritative schedule.

### v3.1: Dependency Graph (Q1 2026)

**Progressive Disclosure for Dependencies:**

```bash
# LEVEL 1: Orient
tiacad build widget.yaml --deps-summary
# "23 parts, 45 operations, 12 parameters, 8 dependency chains"

# LEVEL 2: Navigate
tiacad build widget.yaml --show-deps
# Interactive graph: hover for details, click to focus

# LEVEL 3: Focus
tiacad build widget.yaml --watch --param width
# Live updates on width changes, show affected parts
```

**SIL Impact:** Demonstrates progressive disclosure for SEMANTIC structures (dependencies), not just syntactic ones.

---

### v3.2: Semantic Constraints (Q2 2026)

**Declarative constraints:**

```yaml
constraints:
  - type: flush
    parts: [base.face_top, lid.face_bottom]

  - type: coaxial
    axes: [shaft.axis_z, bearing.axis_z]

  - type: offset
    distance: 5
    from: base.edge_front
    to: panel.edge_back
```

**SIL Impact:** Semantic relationships, not just geometric ones.

---

### Long-term: Pantheon Integration

**Geometric IR:**

TiaCAD designs could be represented in Pantheon's semantic IR, enabling:
- Cross-domain reasoning (CAD + code + docs)
- Unified semantic search
- AI understanding of physical designs

```
Example: "Find all designs with similar mounting patterns"
→ Pantheon searches geometric IR
→ Returns CAD, code, and documentation
→ Unified semantic view
```

---

## Conclusion

**TiaCAD exemplifies SIL principles:**

1. ✅ **Progressive Disclosure** - Orient → Navigate → Focus at every level
2. ✅ **Composability** - Reference-based composition, peer parts
3. ✅ **Clarity** - Explicit YAML, no hidden behavior
4. ✅ **Simplicity** - Declarative over imperative
5. ✅ **Verifiability** - comprehensive test suite (see TEST_STATUS.json), deterministic geometry

**TiaCAD as Layer 2 Domain Module:**
- Specialized geometric reasoning
- Integrates with SIL ecosystem
- Foundation for future semantic CAD

**Vision:**
> **"CAD for the Semantic Age"** - Where designs are not just geometry, but semantic artifacts that can be reasoned about, composed, and verified.

---

**Links:**
- [SIL Manifesto](https://github.com/Semantic-Infrastructure-Lab/SIL/blob/main/docs/canonical/MANIFESTO.md)
- [SIL Design Principles](https://github.com/Semantic-Infrastructure-Lab/SIL/blob/main/docs/canonical/SIL_DESIGN_PRINCIPLES.md)
- [TiaCAD README](../README.md)
- [TiaCAD Architecture](architecture/ARCHITECTURE_DECISION_V3.md)

---

**Document Status:** ✅ Complete
**Audience:** SIL contributors, TiaCAD users, AI agents
**Maintenance:** Update with each major release
