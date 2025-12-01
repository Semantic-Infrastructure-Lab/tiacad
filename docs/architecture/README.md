# TiaCAD Architecture Documentation

System design, technical decisions, and architectural principles for TiaCAD.

---

## 🏗️ Architecture Documents

### Core Architecture

**[ARCHITECTURE_DECISION_V3.md](ARCHITECTURE_DECISION_V3.md)**

Major architectural decisions for TiaCAD v3.0:
- Reference-based spatial system
- Unified coordinate frame model
- Separation of concerns (parser, geometry, export)
- Design rationale and trade-offs

### Future: CGA Integration

**[CGA_V5_ARCHITECTURE_SPEC.md](CGA_V5_ARCHITECTURE_SPEC.md)**

Proposed v5.0 architecture with Conformal Geometric Algebra:
- CGA kernel design
- Unified geometric representation
- Constraint solving with CGA
- CAM integration (slicing, toolpaths)
- Implementation roadmap (40-80 weeks)

**Status:** Planning phase, comprehensive spec for future development

### Code Organization

**[CLEAN_ARCHITECTURE_PROPOSAL.md](CLEAN_ARCHITECTURE_PROPOSAL.md)**

Principles for clean, maintainable code organization:
- Separation of concerns
- Dependency management
- Testing boundaries
- Module responsibilities

### Component Design

**[SKETCH_ABSTRACTION_DESIGN.md](SKETCH_ABSTRACTION_DESIGN.md)**

Deep dive into sketch system design:
- 2D geometry in 3D space
- Sketch-to-solid operations
- Constraint handling
- Coordinate transformations

**[MENTAL_MODELS_AND_LANGUAGE.md](MENTAL_MODELS_AND_LANGUAGE.md)**

Conceptual framework and terminology:
- Core mental models (parts, sketches, operations)
- Language design principles
- User-facing vs. internal concepts
- Consistency guidelines

### Visual Documentation

**[diagrams/](diagrams/)**

Architecture diagrams and visualizations:
- Reference system diagrams
- Operation flow charts
- Coordinate frame illustrations
- Dependency graphs

---

## 🎯 Reading Guide

### For New Contributors

1. **Start:** [ARCHITECTURE_DECISION_V3.md](ARCHITECTURE_DECISION_V3.md)
   - Understand current v3 design
   - Learn key architectural patterns

2. **Deep Dive:** [SKETCH_ABSTRACTION_DESIGN.md](SKETCH_ABSTRACTION_DESIGN.md)
   - Core abstraction (sketches)
   - How 2D/3D geometry integrates

3. **Principles:** [CLEAN_ARCHITECTURE_PROPOSAL.md](CLEAN_ARCHITECTURE_PROPOSAL.md)
   - Code organization guidelines
   - Where to put new features

4. **Visuals:** [diagrams/](diagrams/)
   - See architectural concepts visually

### For System Designers

1. **Current State:** Architecture Decision + Sketch Design
2. **Future Vision:** [CGA_V5_ARCHITECTURE_SPEC.md](CGA_V5_ARCHITECTURE_SPEC.md)
3. **Conceptual:** [MENTAL_MODELS_AND_LANGUAGE.md](MENTAL_MODELS_AND_LANGUAGE.md)

### For Researchers

- **CGA Integration:** [CGA_V5_ARCHITECTURE_SPEC.md](CGA_V5_ARCHITECTURE_SPEC.md)
  - Full mathematical foundation
  - Constraint solving with geometric algebra
  - CAM applications
  - Implementation phases

---

## 🔑 Key Architectural Concepts

### Spatial Reference System

TiaCAD uses a **reference-based coordinate system**:
- Parts define local frames
- Operations reference geometry (faces, edges, vertices)
- Automatic anchor generation for easy composition
- Motor-based transformations (SE(3))

See: [ARCHITECTURE_DECISION_V3.md](ARCHITECTURE_DECISION_V3.md)

### Three-Layer Model

```
User Layer (YAML)
    ↓
IR Layer (Geometry objects, operations)
    ↓
Backend Layer (CadQuery/OCCT → BREP solids)
```

### Backend Abstraction

TiaCAD separates **analytic geometry** from **solid modeling**:
- Geometry layer: abstract geometric operations
- Backend layer: CadQuery/OCCT implementation
- Future: CGA analytic kernel (v5.0)

---

## 📊 Architecture Diagrams

Available in [diagrams/](diagrams/):
- Auto-reference visualization
- Local frame offsets
- Operation categories
- Reference-based vs. hierarchical approaches
- Reference chain dependencies

---

## 🚀 Evolution Timeline

| Version | Focus | Architecture |
|---------|-------|--------------|
| v1-v2 | Basic parametric CAD | Hierarchical transforms |
| **v3** (current) | Spatial references | Reference-based, unified frames |
| v4 | Constraints, assemblies | Extended reference system |
| v5 (planned) | CGA integration | Analytic kernel, advanced CAM |

---

## 🔗 Related Documentation

- **[Developer Docs](../developer/)** - Implementation details
- **[User Docs](../user/)** - User-facing features
- **[Code Structure](../developer/README.md)** - Module organization
