# TiaCAD Evolution Roadmap

**Document Version:** 1.0
**Date:** 2025-11-02
**Status:** Strategic Planning
**Author:** TIA

---

## Executive Summary

TiaCAD is a **mature Phase 2** parametric CAD system with 806 tests and production-ready YAML-to-3D capabilities. This roadmap analyzes four strategic enhancement documents (notes1-4.md) and maps them to TiaCAD's current implementation, providing a **validated, prioritized evolution plan** toward becoming a constraint-based CAD platform.

**Current State: Phase 2 Complete** ✅
- Primitives (box, cylinder, sphere, cone, torus)
- Operations (transform, boolean, pattern, finishing, sketch ops)
- Named points system (NEW - Nov 2025)
- Multi-material 3MF export
- 806 comprehensive tests
- JSON Schema validation

**Target State: Phase 4 - Constraint-Based CAD** 🎯
- Named geometric references (faces, edges, axes)
- Orientation-aware transforms
- Declarative constraints (mate, align, flush)
- Dependency graph (DAG) for parametric updates
- True parametric modeling

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Strategic Analysis of Enhancement Proposals](#2-strategic-analysis-of-enhancement-proposals)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Validated Evolution Path](#4-validated-evolution-path)
5. [Implementation Plan](#5-implementation-plan)
6. [Risk Analysis](#6-risk-analysis)
7. [Success Metrics](#7-success-metrics)

---

## 1. Current State Assessment

### 1.1 What's Actually Implemented (Nov 2025)

**Core Architecture:**
```
YAML → Parser → Parts → Operations → Export
  ↓       ↓        ↓         ↓          ↓
Schema  Params  Registry  Transform  STL/3MF/STEP
```

**Components (All Production-Ready):**

| Component | Status | Tests | Features |
|-----------|--------|-------|----------|
| **PartRegistry** | ✅ Complete | 42 | Part storage, lookup, cloning |
| **PointResolver** | ✅ Complete | 36 | Named points, dot notation, offsets |
| **TransformTracker** | ✅ Complete | 21 | Position tracking, transform history |
| **SelectorResolver** | ✅ Complete | 22 | Face/edge selection (CadQuery) |
| **OperationsBuilder** | ✅ Complete | 147 | All operation types |
| **BooleanBuilder** | ✅ Complete | 32 | Union, difference, intersection |
| **PatternBuilder** | ✅ Complete | 43 | Linear, circular, grid patterns |
| **FinishingBuilder** | ✅ Complete | 29 | Fillet, chamfer |
| **SketchBuilder** | ✅ Complete | 55 | Rectangle, circle, polygon |
| **ExtrudeBuilder** | ✅ Complete | 34 | Extrude sketches |
| **RevolveBuilder** | ✅ Complete | 28 | Revolve sketches |
| **SweepBuilder** | ✅ Complete | 23 | Sweep along path |
| **LoftBuilder** | ✅ Complete | 19 | Loft between profiles |
| **HullBuilder** | ✅ Complete | 17 | Convex hull operations |
| **TextBuilder** | ✅ Complete | 45 | Text engraving/embossing |
| **GussetBuilder** | ✅ NEW | 14 | Triangular structural supports |
| **ColorParser** | ✅ Complete | 38 | RGB, hex, named colors, palettes |
| **ThreeMFExporter** | ✅ Complete | 23 | Multi-material 3D printing |
| **SchemaValidator** | ✅ Complete | 32 | IDE autocomplete, validation |

**Total: 806 tests across 19 major components**

### 1.2 Named Points System (NEW - Nov 2025)

**Implementation Status:** ✅ **PRODUCTION-READY**

```yaml
named_points:
  # 1. Absolute coordinates
  target: [10, 20, 30]

  # 2. Geometric references (dict notation)
  top_center:
    part: base
    face: ">Z"
    at: center

  # 3. Offsets from other named points
  offset_point:
    from: top_center
    offset: [0, 0, 5]

operations:
  move_part:
    type: transform
    input: part_name
    transforms:
      - translate: target  # ✨ Named point reference
```

**What Works:**
- ✅ Absolute coordinates with parameter expressions
- ✅ Geometric references (part.face.center)
- ✅ Cascading offsets (point can reference another named point)
- ✅ Used in translate/rotate operations
- ✅ Full parameter resolution support

**What's Missing:**
- ❌ Named **faces** (only points supported)
- ❌ Named **edges**
- ❌ Named **axes** (orientation data)
- ❌ Cross-part references in named_points section
- ❌ Orientation/normal information

### 1.3 GeometryBackend Architecture

**Status:** ✅ **INTERFACE COMPLETE, PARTIALLY ADOPTED**

```python
class GeometryBackend(ABC):
    # Primitives: create_box, create_cylinder, create_sphere
    # Booleans: union, difference, intersection
    # Transforms: translate, rotate, scale
    # Finishing: fillet, chamfer
    # Queries: get_center, get_bounding_box, select_faces/edges
```

**Current Reality:**
- ✅ Interface defined (`geometry/base.py`)
- ✅ CadQueryBackend implemented
- ✅ MockBackend for fast testing
- ⚠️ **Inconsistent adoption** - some builders still call CadQuery directly
- ⚠️ Parts use backend optionally (fallback to utils)

**Impact:**
- Backend abstraction exists but not fully enforced
- Most code still CadQuery-coupled
- Mock backend works for testing primitives, not full operations

---

## 2. Strategic Analysis of Enhancement Proposals

### 2.1 notes1.md - Gap Assessment

**Document Quality:** ✅ **EXCELLENT** - Comprehensive, accurate, well-prioritized

**Key Findings:**

| Gap Category | Priority | TiaCAD Reality Check |
|--------------|----------|----------------------|
| **Core DAG architecture** | 🔥 High | ❌ **NOT IMPLEMENTED** - Sequential execution only |
| **Sketch constraint solver** | 🔥 High | ❌ **NOT IMPLEMENTED** - No constraints |
| **Assembly constraints** | 🔥 High | ❌ **NOT IMPLEMENTED** - No mate/align logic |
| **Persistent model format** | ⚡ Medium | ❌ **NOT NEEDED** - YAML *is* the source |
| **Units system** | ⚡ Low | ❌ **NOT IMPLEMENTED** - Defer to v2.x |
| **Visualization** | ⚡ Medium | ✅ **PARTIAL** - Basic renderer exists |
| **Export/Import** | ⚡ Medium | ✅ **GOOD** - STL/STEP/3MF working |
| **CadQuery coupling** | ⚡ Medium | ⚠️ **VALID CONCERN** - Backend exists but not enforced |

**Strategic Verdict:**
- ✅ DAG is correctly identified as #1 priority
- ✅ Constraint solving is critical for Phase 4
- ❌ Persistent format is misguided (YAML already serves this)
- ✅ Units are correctly deprioritized
- ✅ Most gaps are valid and well-scoped

### 2.2 notes2.md - Named Geometry References

**Document Quality:** ✅ **EXCELLENT** - Directly addresses current limitation

**Status:** 🎉 **PARTIALLY IMPLEMENTED** (Named points done Nov 2025)

**What notes2.md Proposes:**
```yaml
# NOT YET POSSIBLE in TiaCAD
align:
  part: "bracket"
  to_face: "base.mount_face"
  orientation: "normal"
  offset: 10

mate:
  partA: "shaft"
  partB: "bearing"
  at: "shaft.axis"
  align_to: "bearing.hole_axis"
```

**Current TiaCAD Reality:**
```yaml
# WHAT WORKS TODAY ✅
named_points:
  mount_center:
    part: base
    face: ">Z"
    at: center

operations:
  move_bracket:
    type: transform
    input: bracket
    transforms:
      - translate: mount_center  # ✅ Works!
```

**Gap Analysis:**

| Feature | Proposed | Implemented | Gap |
|---------|----------|-------------|-----|
| Named **points** | ✅ | ✅ | **DONE** |
| Named **faces** | ✅ | ❌ | Need face storage with normal |
| Named **edges** | ✅ | ❌ | Need edge storage with direction |
| Named **axes** | ✅ | ❌ | Need axis origin + direction |
| Orientation data | ✅ | ❌ | Only position, no normal/direction |
| Frame-based transforms | ✅ | ❌ | No local coordinate systems |
| Mate constraints | ✅ | ❌ | No constraint solver |

**Strategic Verdict:**
- ✅ Correctly identified the limitation (points-only, no orientation)
- ✅ Proposed solution (SpatialResolver) is architecturally sound
- ✅ Frame concept is correct (matches SolidWorks/Fusion360)
- 🎯 **This is the natural Phase 3 evolution**

### 2.3 notes3.md - YAML v2.0 Proposal

**Document Quality:** ✅ **PROFESSIONAL-GRADE SPECIFICATION**

**Assessment:** Well-designed but **over-scoped** for current needs

**Proposed Additions:**

```yaml
schema_version: 2.0  # ⚠️ Already using "2.0" in current schema

# NEW: Named geometry (good!)
references:
  points: {...}
  faces: {...}
  axes: {...}

# NEW: Frames (good!)
frames:
  plate_frame:
    origin: base:points:center
    z_axis: base:axes:vertical

# NEW: Constraints (premature!)
constraints:
  mount_alignment:
    type: flush
    parts: [bracket, base]
    refs: [bracket:faces:bottom, base:faces:mount]

# NEW: Units (defer!)
units: mm
parameters:
  width: 100 mm

# NEW: Templates (good but defer!)
include:
  - ./common/bolts.yaml
```

**Reality Check:**

| Feature | Proposed Version | Current TiaCAD | Verdict |
|---------|------------------|----------------|---------|
| `schema_version: 2.0` | Bump to 2.1 | **Already 2.0** | ⚠️ Version conflict |
| `references:` | 2.0 | Not implemented | ✅ Add to current 2.0 |
| `frames:` | 2.0 | Not implemented | ✅ Add to 2.0 |
| `constraints:` | 2.0 | Not implemented | ⚠️ Needs DAG first |
| `units:` | 2.0 | Not implemented | ❌ Defer to 2.1+ |
| `include:` / `templates:` | 2.0 | Not implemented | ⚡ Nice-to-have |

**Strategic Verdict:**
- ✅ Excellent specification quality
- ⚠️ Proposes too many features at once
- ✅ `references` and `frames` should be added to current v2.0 YAML
- ❌ `constraints` require DAG foundation first
- ❌ `units` add complexity without clear ROI
- ⚡ `templates` are valuable but not critical path

### 2.4 notes4.md - v2.1 Addenda

**Document Quality:** ✅ **PRAGMATIC** - Correctly scopes evolution from v0.2.0

**Assessment:** Good incremental approach but **version confusion**

**Key Insight:**
> "What we've been discussing is the natural Phase 3 → Phase 4 evolution"

This is CORRECT. The proposals are evolutionary, not revolutionary.

**Implementation Checklist from notes4:**
```python
# Step 1: Add NamedReference types (geometry/base.py)
# Step 2: Upgrade PointResolver → SpatialResolver
# Step 3: Support reference-based origins (operations_builder.py)
# Step 4: Extend JSON Schema (tiacad-schema.json)
# Step 5: Validate undefined references (cli.py)
```

**Strategic Verdict:**
- ✅ Correct understanding that this extends current v2.0 (not a breaking change)
- ✅ Implementation order is sound
- ✅ Backward compatibility strategy is good
- ⚠️ Should call it v2.0 enhancement, not v2.1 (no schema version bump needed yet)

---

## 3. Architecture Deep Dive

### 3.1 Current Parser Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ TiaCADParser.parse_file("model.yaml")                       │
└─────────────────────────────────────────────────────────────┘
                           │
      ┌────────────────────┴────────────────────┐
      │  1. Load YAML with line tracking        │
      │  2. Schema validation (optional)        │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  3. Resolve parameters (${...})         │
      │     ParameterResolver                   │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  4. Resolve color palette               │
      │     ColorParser                         │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  5. Build sketches (if any)             │
      │     SketchBuilder                       │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  6. Build parts (primitives)            │
      │     PartsBuilder → PartRegistry         │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  7. Parse named_points (NEW!)           │
      │     PointResolver (iterative)           │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  8. Execute operations                  │
      │     OperationsBuilder                   │
      │      ├─ TransformTracker                │
      │      ├─ BooleanBuilder                  │
      │      ├─ PatternBuilder                  │
      │      ├─ FinishingBuilder                │
      │      ├─ ExtrudeBuilder                  │
      │      └─ ... (13 operation builders)     │
      └─────────────────────┬───────────────────┘
                            │
      ┌─────────────────────┴───────────────────┐
      │  9. Return TiaCADDocument               │
      │     → export_stl() / export_3mf()       │
      └─────────────────────────────────────────┘
```

**Key Observations:**
- ✅ Clean, linear pipeline (easy to understand)
- ✅ Good separation of concerns
- ❌ No dependency graph (must execute sequentially)
- ❌ No invalidation tracking (can't re-run partial builds)

### 3.2 PointResolver Current Implementation

**File:** `tiacad_core/point_resolver.py` (409 lines)

**Capabilities:**
```python
class PointResolver:
    def resolve(point_spec) -> (x, y, z):
        # Case 1: Absolute [x, y, z]
        # Case 2: Dict {from: ..., offset: [...]}
        # Case 3: Dict {part: ..., face: ..., at: ...}
        # Case 4: String (named point or dot notation)
```

**Example Resolutions:**
```python
# Absolute
resolve([10, 20, 30]) → (10, 20, 30)

# Named point
resolve("target") → lookup in named_points dict

# Geometric reference (dict)
resolve({part: "base", face: ">Z", at: "center"})
  → Select face → Get center → (x, y, z)

# Offset
resolve({from: "target", offset: [0, 0, 5]})
  → Resolve "target" → Add offset → (x, y, z)

# Dot notation (operations only, not in named_points)
resolve("base.face('>Z').center") → (x, y, z)
```

**Critical Limitation:**
- ✅ Returns position (x, y, z)
- ❌ **NO orientation data** (normal, direction, local axes)
- ❌ Cannot support `align_to_face` or `mate_axes` operations

**What's Needed for Phase 3:**
```python
# Current (Point-only)
def resolve(spec) -> Tuple[float, float, float]:
    return (x, y, z)

# Phase 3 (Spatial with orientation)
def resolve(spec) -> SpatialReference:
    return SpatialReference(
        position=(x, y, z),
        normal=(nx, ny, nz),      # For faces
        direction=(dx, dy, dz),   # For edges/axes
        frame=Frame(...)          # Local coordinate system
    )
```

### 3.3 GeometryBackend Adoption Status

**Interface:** `geometry/base.py` (349 lines, complete)

**Implementations:**
- ✅ `CadQueryBackend` - Full implementation
- ✅ `MockBackend` - Fast testing backend

**Adoption Status by Component:**

| Component | Backend Usage | Status |
|-----------|---------------|--------|
| `PartsBuilder` | ❌ Direct CadQuery | Not using backend |
| `BooleanBuilder` | ❌ Direct CadQuery | Not using backend |
| `PatternBuilder` | ❌ Direct CadQuery | Not using backend |
| `FinishingBuilder` | ❌ Direct CadQuery | Not using backend |
| `ExtrudeBuilder` | ❌ Direct CadQuery | Not using backend |
| `TransformTracker` | ❌ Direct CadQuery | Not using backend |
| `Part.get_center()` | ⚡ Optional | Fallback to utils |

**Why This Matters:**
- ⚠️ Backend exists but bypassed by most code
- ⚠️ Can't easily swap CAD kernels
- ⚠️ Testing still slow (not using MockBackend)

**Recommendation:**
- 🔧 Don't add new backends (FreeCAD, Trimesh) yet
- 🔧 **DO** enforce existing backend in all builders (Phase 3 refactor)
- 🔧 Keep CadQuery as the only real backend for now

---

## 4. Validated Evolution Path

### 4.1 What NOT to Do (Based on Analysis)

❌ **Don't pursue these from notes1-4:**

1. **Persistent `.tiacad.json` format** (notes1.md)
   - YAML is already the source format
   - JSON would be redundant
   - Users should edit YAML, not JSON
   - *Verdict:* Skip entirely

2. **Units system via `pint`** (notes1.md, notes3.md)
   - Adds complexity to every dimension
   - No clear user demand
   - Most CAD tools assume single unit (mm)
   - *Verdict:* Defer to post-1.0 (if at all)

3. **Multiple geometry backends** (notes1.md)
   - FreeCAD/Trimesh/Open3D add 3x testing burden
   - CadQuery works fine
   - No user complaints
   - *Verdict:* Defer until 1000+ users request it

4. **Immediate constraint solver** (notes3.md)
   - Requires DAG foundation first
   - Complex symbolic math
   - 8-12 week effort minimum
   - *Verdict:* Phase 4b, not Phase 3

5. **Schema version bump to 2.1** (notes4.md)
   - Already using v2.0
   - New features can extend v2.0
   - No breaking changes needed
   - *Verdict:* Stay on v2.0, extend it

### 4.2 What TO Do (Prioritized)

✅ **Pursue these enhancements:**

#### **Phase 3: Named Geometry & Orientation** (3-4 months)

**Goal:** Extend named_points to include faces/edges/axes with orientation data

**Deliverables:**
1. `SpatialReference` dataclass (position + orientation)
2. `SpatialResolver` (replaces `PointResolver`)
3. Named faces, edges, axes in YAML
4. Frame-based transforms
5. Updated examples and docs

**Impact:** Enables intent-based modeling ("align to face" vs raw coordinates)

#### **Phase 4a: Dependency Graph (DAG)** (6-8 weeks)

**Goal:** Track dependencies so parameter changes trigger selective rebuilds

**Deliverables:**
1. `ModelGraph` using `networkx`
2. Dependency tracking (params → sketches → parts → operations)
3. Invalidation propagation
4. Incremental rebuild logic

**Impact:** True parametric modeling (change parameter → instant update)

#### **Phase 4b: Explicit Constraints** (4-6 weeks)

**Goal:** Declarative constraints without automatic solving

**Deliverables:**
1. Constraint YAML schema
2. Manual constraint specification (user sets positions)
3. Constraint validation (detect conflicts)
4. Basic types: flush, offset, coaxial

**Impact:** Better design intent capture (but not automatic solving yet)

#### **Phase 5: Constraint Solver** (12-16 weeks)

**Goal:** Automatic constraint satisfaction

**Deliverables:**
1. Symbolic solver (SymPy for simple cases)
2. Numeric solver (scipy.optimize for assemblies)
3. Solver integration with DAG
4. Error reporting for unsolvable systems

**Impact:** Full constraint-based CAD (like SolidWorks/Fusion360)

### 4.3 Recommended Phase 3 Scope (Next Milestone)

**Theme:** "Reference-Based Modeling"

```yaml
# TODAY (Phase 2) ✅
named_points:
  target: [10, 20, 30]

operations:
  move:
    transforms:
      - translate: target  # ✅ Works

# PHASE 3 TARGET 🎯
geometry_references:
  points:
    target: [10, 20, 30]

  faces:
    mount_face:
      part: base
      selector: ">Z"
      # Stores: position + normal

  edges:
    top_edge:
      part: beam
      selector: "|Z and >X"
      # Stores: position + direction

  axes:
    rotation_axis:
      part: shaft
      from: [0, 0, 0]
      to: [0, 0, 100]
      # Stores: origin + direction

operations:
  align_bracket:
    type: transform
    input: bracket
    transforms:
      - align_to_face:
          face: mount_face
          orientation: normal
          offset: 5  # ✨ NEW capability
```

**Technical Implementation:**

1. **New Dataclasses** (`geometry/spatial_references.py`):
```python
@dataclass
class SpatialReference:
    position: Tuple[float, float, float]
    orientation: Optional[Tuple[float, float, float]] = None
    reference_type: str = "point"  # point, face, edge, axis

@dataclass
class Frame:
    origin: Tuple[float, float, float]
    x_axis: Tuple[float, float, float]
    y_axis: Tuple[float, float, float]
    z_axis: Tuple[float, float, float]
```

2. **Upgrade PointResolver** → `SpatialResolver`:
```python
class SpatialResolver:
    def resolve(spec) -> SpatialReference:
        # Returns position + orientation
        pass

    def resolve_face(part, selector) -> SpatialReference:
        # Returns face center + normal
        pass

    def resolve_edge(part, selector) -> SpatialReference:
        # Returns edge midpoint + direction
        pass
```

3. **Extend YAML Schema** (`tiacad-schema.json`):
```json
{
  "geometry_references": {
    "type": "object",
    "properties": {
      "points": {...},
      "faces": {...},
      "edges": {...},
      "axes": {...}
    }
  }
}
```

4. **Backward Compatibility**:
```yaml
# OLD (Phase 2) - Still works! ✅
named_points:
  target: [10, 20, 30]

# NEW (Phase 3) - Recommended
geometry_references:
  points:
    target: [10, 20, 30]
```

Parser checks for `geometry_references` first, falls back to `named_points`.

---

## 5. Implementation Plan

### 5.1 Phase 3: Named Geometry & Orientation

**Duration:** 12-16 weeks
**Complexity:** Medium
**Dependencies:** None (builds on Phase 2)

#### Week 1-2: Foundation
- [ ] Create `geometry/spatial_references.py`
  - `SpatialReference` dataclass
  - `Frame` dataclass
  - Helper functions for frame math
- [ ] Create `spatial_resolver.py` (extends `point_resolver.py`)
  - Preserve existing API
  - Add orientation support
- [ ] Write tests (target: 40+ tests)

#### Week 3-4: Face References
- [ ] Implement `resolve_face(part, selector)`
  - Use CadQuery face selection
  - Extract center + normal from face
- [ ] Add `faces:` section to YAML parser
- [ ] Update `OperationsBuilder` to use face references
- [ ] Create example: align bracket to mount face
- [ ] Write tests (target: 25+ tests)

#### Week 5-6: Edge References
- [ ] Implement `resolve_edge(part, selector)`
  - Use CadQuery edge selection
  - Extract midpoint + direction from edge
- [ ] Add `edges:` section to YAML parser
- [ ] Create example: align along edge
- [ ] Write tests (target: 25+ tests)

#### Week 7-8: Axis References
- [ ] Implement `resolve_axis(spec)`
  - Support `{from: [...], to: [...]}`
  - Extract origin + direction
- [ ] Add `axes:` section to YAML parser
- [ ] Create example: rotate around custom axis
- [ ] Write tests (target: 20+ tests)

#### Week 9-10: Frame-Based Transforms
- [ ] Implement `Frame` class with transform methods
- [ ] Add `frame:` parameter to rotate operations
- [ ] Add `align_to_face` operation
- [ ] Update `TransformTracker` for orientation tracking
- [ ] Write tests (target: 30+ tests)

#### Week 11-12: Integration & Docs
- [ ] Update JSON schema (`tiacad-schema.json`)
- [ ] Update YAML reference docs
- [ ] Create migration guide
- [ ] Convert 2-3 existing examples to use new features
- [ ] Performance testing (ensure no slowdown)

#### Week 13-14: Polish & Testing
- [ ] Full integration test suite
- [ ] Backward compatibility verification
- [ ] Error message improvements
- [ ] User guide updates
- [ ] Code review & refactor

#### Week 15-16: Release Preparation
- [ ] Beta testing with complex models
- [ ] Documentation review
- [ ] Example gallery (5+ new examples)
- [ ] Changelog and migration notes
- [ ] **Release: TiaCAD v2.0.1** (Phase 3 complete)

**Success Criteria:**
- ✅ 140+ new tests (total: 946+ tests)
- ✅ Backward compatibility maintained
- ✅ 5+ production-ready examples
- ✅ No performance regression

### 5.2 Phase 4a: Dependency Graph (DAG)

**Duration:** 6-8 weeks
**Complexity:** High
**Dependencies:** Phase 3 complete

#### Week 1-2: Design & Prototyping
- [ ] Design `ModelGraph` API
- [ ] Spike: `networkx` vs custom implementation
- [ ] Define node types (parameter, sketch, part, operation)
- [ ] Define edge types (depends_on, invalidates)
- [ ] Prototype with simple example

#### Week 3-4: Core DAG Implementation
- [ ] Create `model_graph.py`
  - `ModelGraph` class using `networkx`
  - `add_node()`, `add_edge()`, `get_dependencies()`
  - Cycle detection
  - Topological sort
- [ ] Write tests (target: 50+ tests)

#### Week 5-6: Parser Integration
- [ ] Update `TiaCADParser` to build DAG
  - Track parameter dependencies
  - Track part dependencies
  - Track operation dependencies
- [ ] Implement invalidation logic
- [ ] Add `rebuild_from_node()` method
- [ ] Write integration tests

#### Week 7-8: CLI Integration & Testing
- [ ] Add `--watch` mode (auto-rebuild on YAML change)
- [ ] Add `--show-deps` command (visualize graph)
- [ ] Performance optimization (cache nodes)
- [ ] Full integration testing
- [ ] **Release: TiaCAD v2.1.0** (DAG support)

**Success Criteria:**
- ✅ 50+ DAG-specific tests
- ✅ Incremental rebuild 10x faster than full rebuild
- ✅ Watch mode works with live reload

### 5.3 Phase 4b: Explicit Constraints

**Duration:** 4-6 weeks
**Complexity:** Medium
**Dependencies:** DAG complete

#### Week 1-2: Schema & Data Model
- [ ] Design constraint YAML schema
- [ ] Create `constraint.py` dataclasses
  - `FlushConstraint`, `CoaxialConstraint`, etc.
- [ ] Update JSON schema
- [ ] Write validation tests

#### Week 3-4: Constraint Parser
- [ ] Implement `ConstraintBuilder`
- [ ] Parse constraints from YAML
- [ ] Validate constraint references
- [ ] Detect conflicting constraints
- [ ] Write tests

#### Week 5-6: Constraint Application
- [ ] Add constraints to ModelGraph
- [ ] Manual constraint satisfaction (user provides positions)
- [ ] Constraint verification
- [ ] Example: assembly with manual constraints
- [ ] **Release: TiaCAD v2.2.0** (Constraint declarations)

**Success Criteria:**
- ✅ 30+ constraint tests
- ✅ Clear error messages for invalid constraints
- ✅ 3+ assembly examples

### 5.4 Phase 5: Constraint Solver

**Duration:** 12-16 weeks
**Complexity:** Very High
**Dependencies:** Explicit constraints complete

**Note:** This is a post-1.0 feature. Requires significant R&D.

**Approach:**
1. Start with 2D constraint solver (sketch constraints)
2. Symbolic solver (SymPy) for simple cases
3. Numeric solver (scipy.optimize) for complex assemblies
4. Integration with DAG for recomputation
5. Error handling for unsolvable systems

**Estimated Effort:** 3-4 months full-time

---

## 6. Risk Analysis

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking changes** | Medium | High | Strict backward compatibility testing |
| **Performance regression** | Medium | Medium | Benchmark suite, profiling |
| **DAG complexity** | High | High | Start simple, iterate |
| **Constraint solver difficulty** | High | Very High | Defer to Phase 5, extensive R&D |
| **CadQuery limitations** | Low | Medium | GeometryBackend allows future swap |

### 6.2 Scope Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Feature creep** | High | High | Stick to roadmap, resist temptations |
| **Units system pressure** | Medium | Low | Politely defer to v3.0+ |
| **Template system demands** | Low | Medium | Show workarounds (separate files) |
| **Multiple backend requests** | Low | Medium | Explain testing burden |

### 6.3 User Adoption Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Migration effort** | Low | Low | Backward compatible |
| **Documentation lag** | Medium | Medium | Docs as part of each phase |
| **Learning curve** | Medium | Medium | Examples, tutorials, migration guides |
| **Bug discovery** | Medium | Medium | Beta period, issue templates |

---

## 7. Success Metrics

### 7.1 Technical Metrics

**Phase 3 (Named Geometry):**
- ✅ Test coverage >95% (current: ~98%)
- ✅ Total tests: 946+ (current: 806)
- ✅ Zero performance regression
- ✅ 100% backward compatibility

**Phase 4a (DAG):**
- ✅ Incremental rebuild 10x faster
- ✅ Watch mode <100ms latency
- ✅ DAG visualization working

**Phase 4b (Constraints):**
- ✅ 30+ constraint tests
- ✅ Conflict detection working
- ✅ Clear error messages

### 7.2 User Experience Metrics

**Phase 3:**
- ✅ 5+ production examples using named geometry
- ✅ User guide updated
- ✅ IDE autocomplete for new features

**Phase 4:**
- ✅ Complex assembly example (10+ parts)
- ✅ Tutorial: "Parametric Design with TiaCAD"
- ✅ Community examples (if public)

### 7.3 Documentation Metrics

**Each Phase:**
- ✅ Updated YAML reference
- ✅ Migration guide
- ✅ Changelog
- ✅ 3+ working examples
- ✅ API documentation (if library use)

---

## 8. Recommendations Summary

### 8.1 Immediate Next Steps (This Week)

1. **Validate this roadmap** with stakeholders
2. **Archive notes1-4.md** as "analyzed and incorporated"
3. **Create GitHub issues** for Phase 3 tasks (if using issue tracking)
4. **Set up project board** (if desired)

### 8.2 Phase 3 Launch Checklist

- [ ] Create feature branch `feature/named-geometry`
- [ ] Set up test coverage tracking
- [ ] Create `geometry/spatial_references.py`
- [ ] Write first spike: `SpatialReference` dataclass
- [ ] Begin Week 1-2 tasks

### 8.3 Long-Term Strategic Guidance

**Do:**
- ✅ Focus on Phase 3 → 4a → 4b → 5 sequence
- ✅ Maintain strict backward compatibility
- ✅ Keep test coverage >95%
- ✅ Document everything as you go
- ✅ Enforce GeometryBackend usage in new code

**Don't:**
- ❌ Add units system
- ❌ Create persistent JSON format
- ❌ Implement multiple backends
- ❌ Rush constraint solver (needs DAG first)
- ❌ Bump schema version unnecessarily

**Defer to Post-1.0:**
- ⏳ Web viewer / GUI
- ⏳ BOM / metadata reports
- ⏳ Plugin system
- ⏳ REST API
- ⏳ Collaboration features

---

## 9. Conclusion

TiaCAD is in an **excellent position** to evolve from a mature Phase 2 parametric CAD system into a Phase 4 constraint-based platform. The enhancement proposals in notes1-4.md are largely sound, with the following strategic adjustments:

**Validated Enhancements:**
- ✅ Named geometry references (Phase 3) - **HIGH PRIORITY**
- ✅ Dependency graph (Phase 4a) - **CRITICAL for parametric**
- ✅ Explicit constraints (Phase 4b) - **GOOD intermediate step**
- ✅ Constraint solver (Phase 5) - **LONG-TERM goal**

**Rejected Enhancements:**
- ❌ Persistent JSON format (redundant with YAML)
- ❌ Units system (complexity without clear ROI)
- ❌ Multiple backends (testing burden)

**Deferred Enhancements:**
- ⏳ Templates/includes (nice-to-have)
- ⏳ Visualization improvements (Phase 5+)
- ⏳ Web/GUI (Phase 6+)

**Timeline:**
- **Phase 3:** 12-16 weeks (Named Geometry)
- **Phase 4a:** 6-8 weeks (DAG)
- **Phase 4b:** 4-6 weeks (Explicit Constraints)
- **Phase 5:** 12-16 weeks (Constraint Solver)

**Total to Full Constraint-Based CAD:** ~40-50 weeks (10-12 months)

This roadmap provides a **validated, prioritized, technically sound path forward** that builds on TiaCAD's strong Phase 2 foundation while avoiding common pitfalls (feature creep, premature optimization, breaking changes).

---

**Document Status:** ✅ **READY FOR EXECUTION**
**Next Action:** Review with team, then begin Phase 3 Week 1-2 tasks

---

*Generated: 2025-11-02*
*Roadmap Version: 1.0*
*TiaCAD Current Version: 2.0 (Phase 2 Complete)*
