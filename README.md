---
project: tiacad
type: software
status: active
beth_topics:
- tiacad
- software
tags:
- cad
- yaml
- parametric-design
- 3d-modeling
- development
- code
---

# TiaCAD - Declarative Parametric CAD in YAML

**Version:** 3.1.2 (+maintenance commits)
**Status:** Stable, extensively tested, Apache 2.0 licensed
**Current:** v3.1.2 + examples/docs updates (see CHANGELOG.md for unreleased work)
**Released:** v3.0.0 on Nov 19, 2025 | v3.1.0 on Nov 11 | v3.1.1 on Nov 16 | v3.1.2 on Dec 2, 2025
**Breaking Changes:** None in v3.1.x (backward compatible)

> **v3.1.2 Status:** Stable and feature-complete for the current scope:
>
> **v3.0 Foundation:**
> - ✅ Unified `SpatialRef` dataclass (position + orientation)
> - ✅ `SpatialResolver` with comprehensive reference resolution
> - ✅ Auto-generated part-local references (e.g., `base.face_top`)
> - ✅ Local frame offsets for intelligent positioning
>
> **v3.1 Enhancements:**
> - ✅ Visual regression testing framework (50+ tests)
> - ✅ Complete cone primitive support across all backends
> - ✅ Accurate origin tracking after transforms
> - ✅ Full XZ/YZ plane support for loft operations
> - ✅ Comprehensive testing utilities
> - ✅ Terminology standardization and visual documentation
>
> See `RELEASE_NOTES_V3.md` for complete details and `docs/developer/MIGRATION_GUIDE_V3.md` for upgrade instructions.

---

## Part of the Semantic Infrastructure Lab

**TiaCAD** is a production component of the [Semantic Infrastructure Lab (SIL)](https://github.com/semantic-infrastructure-lab/sil) — building the semantic substrate for intelligent systems.

### Role in the Semantic OS

```
Semantic OS Architecture
├── Layer 1: Kernel (TIA orchestration, Beth knowledge, Gemma provenance)
├── Layer 2: Domain Modules
│   └── TiaCAD ← Geometric/CAD reasoning
├── Layer 3: Tools (reveal, Scout)
└── Layer 4: Interfaces
```

**TiaCAD provides:**
- **Geometric Reasoning** - Declarative 3D solid modeling
- **Parametric Design** - Mathematical relationships in physical space
- **Spatial Composition** - Reference-based assembly without hierarchies
- **Verifiable CAD** - Deterministic, testable geometry with broad automated coverage

### What Makes TiaCAD Unique in SIL

**CAD for the Semantic Age** - TiaCAD is not just another CAD tool. It's the first CAD system designed from the ground up as a **semantic artifact**.

**Key Innovation: Reference-Based Composition**

Traditional CAD uses hierarchical parent-child assemblies. TiaCAD uses **peer parts with spatial anchors**:

```yaml
# Parts are PEERS, not nested
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 5, depth: 100}

  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 50}

operations:
  # Composition via SPATIAL REFERENCES (not parent-child)
  pillar_positioned:
    type: transform
    input: pillar
    transforms:
      - translate:
          to: base.face_top  # Semantic anchor, auto-generated!
```

**Why this matters:**
- ✅ Parts are independently testable (no coupling)
- ✅ Explicit dependencies (no hidden hierarchies)
- ✅ Composable like functions (orchestrated by TIA, not embedded)
- ✅ Semantic, not just geometric

### SIL Principles in Action

TiaCAD exemplifies all core SIL principles through concrete implementations:

#### 1. Progressive Disclosure

**Orient → Navigate → Focus** at multiple levels:

```bash
# LEVEL 1: ORIENT - What designs exist?
ls examples/                    # See all available designs

# LEVEL 2: NAVIGATE - What's in this design?
reveal guitar_hanger.yaml       # Structure: metadata, parameters, parts, operations

# LEVEL 3: FOCUS - Show specific part
reveal guitar_hanger.yaml --range 45-75  # Just the hook definition
```

**Future** (v3.1 DAG): Progressive disclosure for *dependencies*:
```bash
tiacad build widget.yaml --deps-summary    # LEVEL 1: "23 parts, 45 ops"
tiacad build widget.yaml --show-deps       # LEVEL 2: Dependency graph
tiacad build widget.yaml --watch --param w # LEVEL 3: Live tracking
```

#### 2. Composability

Parts compose via references, not nesting:
- TiaCAD generates geometry
- `reveal` explores structure
- `tia beth` finds similar patterns
- `scout` reviews quality (future)

**All tools work together, not bundled in a monolith.**

#### 3. Clarity + Simplicity

Explicit YAML (not implicit magic) + Declarative (not procedural):
```yaml
# Explicit origins, parameters, references
box:
  primitive: box        # Explicit type
  parameters:
    width: 10          # Named dimensions
    height: 10         # (not [10,10,10])
    depth: 10
  origin: center       # Explicit origin
```

#### 4. Verifiability

Automated tests ensure correctness:
- Deterministic: Same YAML → Same geometry (always)
- Testable: Parameters, operations, dimensions verified
- Reproducible: Version-controlled designs

### Learn More

📖 **[Complete SIL Integration Guide](docs/SIL_INTEGRATION.md)** - Deep dive into:
- How TiaCAD embodies each SIL principle (with examples)
- Integration patterns (TiaCAD + reveal, TiaCAD + Beth, etc.)
- Future vision (semantic constraints, Pantheon integration)
- Why reference-based composition matters for AI systems

**Quick Links:**
[SIL Manifesto](https://github.com/semantic-infrastructure-lab/sil/blob/main/docs/canonical/MANIFESTO.md) • [Design Principles](https://github.com/semantic-infrastructure-lab/sil/blob/main/docs/canonical/SIL_DESIGN_PRINCIPLES.md) • [Project Index](https://github.com/semantic-infrastructure-lab/sil/blob/main/projects/PROJECT_INDEX.md)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full test suite
python3 -m pytest tiacad_core/tests/

# Generate coverage report
python3 -m pytest tiacad_core/tests/ --cov=tiacad_core --cov-report=html

# Try an example - create a smooth transition using loft
tiacad build examples/transition_loft.yaml

# See the generated 3MF file (modern format)
ls -lh *.3mf
```

**What You Get:**
- Declarative YAML syntax for 3D CAD
- Parameters with expressions (`${width * 2}`)
- Primitives (box, cylinder, sphere, cone)
- Sketch operations (extrude, revolve, sweep, loft)
- Boolean operations (union, difference, intersection)
- Pattern operations (linear, circular, grid)
- Finishing operations (fillet, chamfer)
- Schema validation with helpful error messages
- Automatic 3MF export (modern format) + STEP and STL support
- A CadQuery-first kernel boundary with a partially enforced `GeometryBackend` abstraction

---

## What is TiaCAD?

TiaCAD is a **declarative parametric CAD system** that lets you design 3D models using **YAML** instead of code. It's built on top of CadQuery and focuses on:

- **Readability**: YAML syntax anyone can understand
- **Explicit behavior**: No hidden defaults or magic
- **Composability**: Build complex assemblies from simple parts
- **Verifiability**: Comprehensive test coverage ensures correctness
- **Quality**: Professional code quality with extensive validation

### TiaCAD's Design Philosophy: Reference-Based Composition

**How is TiaCAD different?** Unlike traditional CAD (SolidWorks, Fusion 360) which uses hierarchical parent-child assemblies, TiaCAD uses a **reference-based composition model**:

**🎯 Key Concepts:**
- **Independent parts**: Parts aren't nested in assembly hierarchies - they're all peers
- **Spatial anchors**: Position parts using reference points (we call them "anchors")
- **Auto-generated references**: Every part automatically provides attachment points (`.face_top`, `.center`, etc.)
- **Declarative**: Describe what you want ("put this on top of that"), not step-by-step instructions
- **No parent-child relationships**: Parts reference *positions*, not other parts

**Think of it as marking spots on a workbench** where things go, rather than building nested folders of sub-assemblies.

**vs Traditional CAD:**

| Traditional CAD (SolidWorks) | TiaCAD (Reference-Based) |
|------------------------------|--------------------------|
| Hierarchical assemblies | Flat parts with anchors |
| Parent-child relationships | Independent parts |
| Mate constraints | Spatial references |
| Assembly → Sub-assembly → Part | Part → Part → Part (peers) |
| "Connect this to that" | "Position this at that anchor" |

**vs Procedural Tools (OpenSCAD):**

| OpenSCAD (Procedural) | TiaCAD (Declarative) |
|-----------------------|----------------------|
| Step-by-step instructions | Describe desired result |
| Execution order matters | Declaration order flexible |
| `translate([0,0,10]) cylinder(...)` | `translate: to: base.face_top` |
| Manual coordinate calculation | Auto-generated anchors |

**Why this matters:** Once you understand the reference-based model, positioning becomes intuitive: "place the cap on the pillar's top face" rather than calculating coordinates manually.

**Visual Guide:** See [Reference-Based vs Hierarchical](docs/architecture/diagrams/reference-based-vs-hierarchical.md) for a detailed visual comparison.

**See also:** [Glossary](docs/user/GLOSSARY.md) for term definitions, [Auto References Guide](docs/user/AUTO_REFERENCES_GUIDE.md) for anchor details.

---

### Example: Parametric Bottle (Revolve Operation)

```yaml
parameters:
  bottle_height: 100
  bottle_radius: 30
  neck_radius: 10

sketches:
  bottle_profile:
    plane: XZ
    origin: [0, 0, 0]
    shapes:
      - type: polygon
        points:
          - [0, 0]                              # Bottom center
          - ["${bottle_radius}", 0]              # Bottom edge
          - ["${bottle_radius}", 70]             # Body top
          - ["${neck_radius}", 80]               # Neck start
          - ["${neck_radius}", "${bottle_height}"] # Neck top
          - [0, "${bottle_height}"]              # Top center

operations:
  bottle:
    type: revolve
    sketch: bottle_profile
    axis: Z
    angle: 360
```

**Result:** Smooth bottle shape created by revolving a 2D profile around an axis.

### Example: Smooth Transition (Loft Operation)

```yaml
sketches:
  base_square:
    plane: XY
    origin: [0, 0, 0]
    shapes:
      - type: rectangle
        width: 40
        height: 40

  top_circle:
    plane: XY
    origin: [0, 0, 30]
    shapes:
      - type: circle
        radius: 15

operations:
  transition:
    type: loft
    profiles: [base_square, top_circle]
    ruled: false  # Smooth blending
```

**Result:** Organic transition from square base to circular top.

### Example: auto-generated anchors (New in v3.0!)

v3.0 introduces **auto-generated references** that eliminate manual coordinate calculations:

```yaml
parts:
  # Base platform
  platform:
    primitive: box
    parameters:
      width: 100
      height: 5
      depth: 100

  # Pillar automatically positioned on top
  pillar:
    primitive: cylinder
    parameters:
      radius: 5
      height: 50
    translate:
      to: platform.face_top  # Auto-generated reference!

  # Cap positioned with offset from pillar top
  cap:
    primitive: box
    parameters:
      width: 15
      height: 5
      depth: 15
    translate:
      to:
        from: pillar.face_top  # Auto-generated reference!
        offset: [0, 0, 2]      # 2 units above pillar
```

**Benefits:**
- No manual reference definitions needed
- `{part}.face_top`, `{part}.center`, `{part}.axis_z` auto-generated for every part
- Offsets follow local coordinate frames for intuitive positioning
- Full orientation support (normals, tangents) for intelligent placement

**See:** `examples/auto_references_box_stack.yaml` and `docs/developer/MIGRATION_GUIDE_V3.md`

---

## Project Structure

```
tiacad/
├── tiacad_core/
│   ├── Core Components
│   │   ├── part.py                    # Part representation (19 tests ✅)
│   │   ├── selector_resolver.py       # Selector resolution (31 tests ✅, 100% cov)
│   │   ├── transform_tracker.py       # Transform tracking (21 tests ✅)
│   │   ├── point_resolver.py          # Point resolution (36 tests ✅)
│   │   └── sketch.py                  # 2D sketch system (25 tests ✅)
│   │
│   ├── parser/                        # YAML Parser System (Phase 1-3)
│   │   ├── tiacad_parser.py           # Main parser (16 tests ✅)
│   │   ├── parameter_resolver.py      # Expression resolver (33 tests ✅)
│   │   ├── parts_builder.py           # Parts builder (22 tests ✅)
│   │   ├── operations_builder.py      # Operations dispatcher (15 tests ✅)
│   │   ├── boolean_builder.py         # Boolean ops (32 tests ✅)
│   │   ├── pattern_builder.py         # Pattern ops (40 tests ✅)
│   │   ├── finishing_builder.py       # Finishing ops (38 tests ✅)
│   │   ├── sketch_builder.py          # Sketch builder (Phase 3)
│   │   ├── extrude_builder.py         # Extrude operation (6 tests ✅)
│   │   ├── revolve_builder.py         # Revolve operation (4 tests ✅)
│   │   ├── sweep_builder.py           # Sweep operation (4 tests ✅)
│   │   ├── loft_builder.py            # Loft operation (6 tests ✅)
│   │   └── schema_validator.py        # YAML schema validation (114 tests ✅)
│   │
│   ├── validation/                    # Assembly validation
│   │   └── assembly_validator.py      # Part references (19 tests ✅)
│   │
│   ├── exporters/                     # 3D file export
│   │   └── threemf_exporter.py        # 3MF format (31 tests ✅)
│   │
│   ├── tests/                         # Comprehensive test suite (see TEST_STATUS.json) ✅
│   │   ├── test_parser/               # Parser tests (Phase 1-3)
│   │   ├── test_validation/           # Validation tests
│   │   ├── test_exporters/            # Export tests
│   │   └── test_*.py                  # Component tests
│   │
│   └── utils/                         # Utilities
│       ├── exceptions.py              # Error handling (19 tests ✅)
│       └── geometry.py                # Geometry utilities
│
├── examples/                          # Working YAML examples
│   ├── transition_loft.yaml           # Loft example (square→circle)
│   ├── rounded_mounting_plate.yaml    # Fillet example
│   ├── chamfered_bracket.yaml         # Chamfer example
│   └── ...
│
├── output/                            # Generated STL/3MF files
├── htmlcov/                           # Coverage report (see TEST_STATUS.json)
├── docs/                              # Comprehensive documentation
└── README.md                          # This file
```

---

## Core Components

### Phase 1: Foundation (100% Complete ✅)

**1. Part System (19 tests ✅)**
- CadQuery Workplane wrapper with position tracking
- Transform history for debugging
- Part registry for complex assemblies

**2. SelectorResolver (31 tests ✅, 100% coverage)**
- Face/edge selection (`">Z"`, `"|X"`)
- Combinators (and, or, not)
- Comprehensive test coverage
- Clear error messages

**3. TransformTracker (21 tests ✅)**
- Sequential transform application
- Rotation origin resolution
- Rodrigues rotation (exact, arbitrary axes)

**4. PointResolver (36 tests ✅)**
- Absolute coordinates: `[x, y, z]`
- Dot notation: `"part.face('>Z').center"`
- Offset expressions

**5. ParameterResolver (33 tests ✅)**
- Expression evaluation: `${width * 2}`
- Nested parameters
- Math operations (+, -, *, /, **, %)

**6. Sketch System (25 tests ✅)**
- 2D profile creation (rectangle, circle, polygon)
- Multiple shapes per sketch
- Parameter resolution in sketches

### Phase 2: Operations (100% Complete ✅)

**7. YAML Parser (16 tests ✅)**
- Complete YAML → STL/3MF pipeline
- Metadata, parameters, parts, sketches, operations, export
- End-to-end integration
- Schema validation

**8. PartsBuilder (22 tests ✅)**
- Primitives: box, cylinder, sphere, cone
- Origin modes: center, corner, custom
- Transform application

**9. BooleanBuilder (32 tests ✅)**
- Union: combine parts
- Difference: subtract parts
- Intersection: find overlap
- Multi-part operations

**10. PatternBuilder (40 tests ✅)**
- Linear patterns (1D, 2D, 3D)
- Circular patterns (bolt circles, gears)
- Grid patterns (arrays)
- Parameter expressions

**11. FinishingBuilder (38 tests ✅)**
- Fillet: round edges with radius
- Chamfer: bevel edges (uniform/asymmetric)
- Edge selection: direction, parallel, perpendicular
- Multiple operations per part

### Phase 3: Sketch Operations (100% Complete ✅)

**12. ExtrudeBuilder (6 tests ✅)**
- Extrude 2D sketches along direction
- Distance and both-directions support
- Draft angles for manufacturability
- Parameter expressions

**13. RevolveBuilder (4 tests ✅)**
- Revolve profiles around axis (X, Y, or Z)
- Full (360°) or partial angles
- Custom axis specification
- Rotationally symmetric parts

**14. SweepBuilder (4 tests ✅)**
- Sweep profile along path
- Straight and curved paths
- Complex pipe and rail shapes
- Path point arrays

**15. LoftBuilder (6 tests ✅)**
- Blend between multiple profiles
- Smooth or ruled surfaces
- Organic shape creation
- Multi-profile transitions

**16. SchemaValidator (114 tests ✅)**
- YAML schema validation against JSON schema
- Comprehensive error messages
- Field-level validation
- Type checking

**17. AssemblyValidator (19 tests ✅)**
- Part reference validation
- Circular dependency detection
- Missing part detection
- Operation validation

**18. 3MF Exporter (31 tests ✅)**
- 3D Manufacturing Format export
- Color and material preservation
- Multi-part assemblies
- Production-ready output

### v3.1: Testing Confidence

**19. Testing Utilities (71 tests ✅) - NEW in v3.1**
- Measurement utilities: distance, dimensions, bounding boxes
- Orientation utilities: rotation angles, normals, alignment
- Dimension utilities: volume, surface area calculations
- Full documentation with examples

**20. Correctness Tests**
- Attachment correctness
- Rotation correctness
- Dimensional accuracy
- Comprehensive verification of YAML → 3D translation

---

## Quality Assurance

### Test Coverage

For live pass/fail/skip/coverage counts, see the CI-generated
[`TEST_STATUS.json`](TEST_STATUS.json) — the counts below are a snapshot and
will drift; `TEST_STATUS.json` is the source of truth.

**Overall:** Broad automated coverage across the suite

**Includes:**
- Testing utility coverage for measurement, orientation, and dimension helpers
- Correctness coverage for attachment, rotation, and dimensional behavior

**By Component:**
- Selector resolution: 100% coverage ✨
- Exception handling: 100% coverage
- Part system: 99% coverage
- Sketch system: 95% coverage
- Parameter resolution: 95% coverage
- Boolean operations: 93% coverage
- Color parsing: 93% coverage

### Code Quality

**Tools Used:**
- **Ruff**: Modern Python linter for focused and CI-ready cleanup
- **Pylint**: Code quality analysis for deeper review when needed
- **pytest-cov**: Coverage analysis (see TEST_STATUS.json for the current overall %)
- **mypy-ready**: TYPE_CHECKING imports for type safety

**Quality Improvements:**
- Removed unused imports
- Fixed type hints (TYPE_CHECKING pattern)
- Enhanced error messages with context
- Consistent code style
- Comprehensive docstrings

### Testing Strategy

**Test Types:**
1. **Unit Tests**: Fast, isolated component tests
2. **Integration Tests**: Real CadQuery validation
3. **Error Case Tests**: Comprehensive error handling
4. **Regression Tests**: Prevent bugs from returning
5. **Real-World Examples**: Practical use case validation

---

## Development Roadmap

### Phase 1: Foundation (100% Complete ✅)
- [x] Part representation (19 tests)
- [x] Selector resolution (31 tests, 100% coverage)
- [x] Transform tracking (21 tests)
- [x] Point resolution (36 tests)
- [x] Parameter resolution (33 tests)
- [x] YAML parser (16 tests)

**Deliverable:** YAML → STL pipeline functional ✅

### Phase 2: Operations (100% Complete ✅)
- [x] Boolean operations (32 tests)
- [x] Pattern operations (40 tests)
- [x] Finishing operations (38 tests)
- [x] Parts builder (22 tests)
- [x] Operations integration (15 tests)
- [x] Real-world examples (6+ working)

**Deliverable:** Production-ready parametric CAD system ✅

### Phase 3: Sketch Operations (100% Complete ✅)
- [x] 2D sketch system (25 tests)
- [x] Extrude operation (6 tests)
- [x] Revolve operation (4 tests)
- [x] Sweep operation (4 tests)
- [x] Loft operation (6 tests)
- [x] Schema validation (114 tests)
- [x] Assembly validation (19 tests)
- [x] 3MF export (31 tests)
- [x] Quality improvements (609 total tests, 84% coverage — Phase 3 snapshot; see "What's Next?" below for current counts)

**Deliverable:** Complete CAD system with sketch-based modeling ✅

---

## What's Next?

**See [ROADMAP.md](ROADMAP.md) for detailed plans and priorities.**

**Current Status (Mar 2026):** Active development — Component System + DAG both complete

**Completed in Q1 2026:**
- ✅ **Component/Module System** — local, stdlib (`tiacad://std/...`), GitHub (`github:user/repo/...`) imports
- ✅ **Hardware stdlib** — m3/m4/m5/m6 screws, washer, standoff, nut, mounting bracket
- ✅ **Dependency Graph (DAG)** — incremental rebuild, watch mode, `--export` flag
- ✅ **`polygon` primitive** — regular N-sided prism (hex nuts, gears, etc.)

**Next Milestone (Q4 2026):** Constraint Solver — declarative assemblies ("make these flush")

---

## Known Limitations & Future Plans

**TiaCAD v3.1.2 has solid mathematical foundations and comprehensive features, but some capabilities remain unimplemented.**

📋 **For detailed limitations and workarounds:** See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)

🗺️ **For future plans and priorities:** See [ROADMAP.md](ROADMAP.md)

**Quick Summary:**

**Current Limitations:**
- No constraint solver (manual positioning only) — next milestone Q4 2026
- Limited export formats (STL/3MF/STEP; no DXF/G-code/SVG)
- STL/STEP export currently requires CadQuery-compatible parts; 3MF/visualization can use backend tessellation

**Recent Additions (Q1 2026):**
- ✅ Component imports: local, stdlib, GitHub
- ✅ Hardware stdlib (8 components)
- ✅ Incremental rebuild + watch mode
- ✅ `polygon` primitive

### Advanced Features (v4.0+)

**Constraints & Assemblies:**
- [ ] Attachment constraints (mate, align, coincide)
- [ ] Multi-part assemblies with relationships
- [ ] Named constraint patterns
- [ ] Assembly collision detection

**Advanced Operations:**
- [ ] Shell/offset operations
- [ ] Advanced fillets (variable radius, blend)
- [ ] Text/engraving
- [ ] Imported sketches (DXF, SVG)

**Export & Integration:**
- [ ] Additional formats (STEP, IGES, DXF)
- [ ] CAM integration (toolpaths, g-code)
- [ ] Bill of materials (BOM) generation
- [ ] Assembly instructions

### Phase 5: Tooling & Polish (Future)
- [ ] Web-based YAML editor
- [ ] Real-time 3D preview
- [ ] Error visualization
- [ ] Interactive documentation
- [ ] YAML auto-completion
- [ ] Template library

---

## Design Principles

### 1. Explicit Origins (No Magic)

**Problem:** Default rotation behavior causes confusion
**Solution:** REQUIRE explicit rotation origins in YAML

```yaml
# ❌ REJECTED - ambiguous behavior
- rotate: {angle: 45, axis: Z}

# ✅ ACCEPTED - explicit origin
- rotate: {angle: 45, axis: Z, origin: current}
- rotate: {angle: 45, axis: Z, origin: [0, 0, 0]}
- rotate: {angle: 45, axis: Z, origin: "beam.face('>Y').center"}
```

### 2. Sequential Transforms (Order Matters)

Transforms apply top-to-bottom. Order matters!

```yaml
# These produce DIFFERENT results:
transforms:
  - translate: [10, 0, 0]  # Move THEN rotate
  - rotate: {angle: 90, axis: Z, origin: [0,0,0]}

transforms:
  - rotate: {angle: 90, axis: Z, origin: [0,0,0]}  # Rotate THEN move
  - translate: [10, 0, 0]
```

### 3. Test-Driven Development

Every component has comprehensive tests:
- Unit tests with mocks (fast iteration)
- Integration tests with real CadQuery (validation)
- Error case coverage (robustness)
- Real-world use cases (practical verification)

**Result:** broad parser, geometry, correctness, validation, DAG, and visual coverage.

### 4. Quality First

- Code quality tools (ruff, pylint)
- Type safety (TYPE_CHECKING imports)
- Comprehensive error messages
- Clear documentation
- Professional code standards

---

## Documentation

### User Documentation

**Getting Started:**
- [docs/user/TUTORIAL.md](docs/user/TUTORIAL.md) - Step-by-step introduction
- [docs/user/GLOSSARY.md](docs/user/GLOSSARY.md) - Terminology and concepts
- [docs/user/EXAMPLES_GUIDE.md](docs/user/EXAMPLES_GUIDE.md) - Detailed example walkthroughs

**Reference:**
- [docs/user/YAML_REFERENCE.md](docs/user/YAML_REFERENCE.md) - Complete syntax reference
- [docs/user/AUTO_REFERENCES_GUIDE.md](docs/user/AUTO_REFERENCES_GUIDE.md) - Spatial anchors guide
- [docs/developer/CLI.md](docs/developer/CLI.md) - Command-line interface

**Migration:**
- [docs/developer/MIGRATION_GUIDE_V3.md](docs/developer/MIGRATION_GUIDE_V3.md) - Upgrading from v0.3.0
- [RELEASE_NOTES_V3.md](RELEASE_NOTES_V3.md) - What's new in v3.0

### Technical Documentation

**Architecture & Design:**
- [docs/architecture/ARCHITECTURE_DECISION_V3.md](docs/architecture/ARCHITECTURE_DECISION_V3.md) - v3.0 design rationale
- [docs/architecture/MENTAL_MODELS_AND_LANGUAGE.md](docs/architecture/MENTAL_MODELS_AND_LANGUAGE.md) - Language design exploration
- [docs/archive/SKETCH_ABSTRACTION_DESIGN.md](docs/archive/SKETCH_ABSTRACTION_DESIGN.md) - Sketch system design
- [docs/architecture/CLEAN_ARCHITECTURE_PROPOSAL.md](docs/architecture/CLEAN_ARCHITECTURE_PROPOSAL.md) - Architecture principles

**Testing:**
- [docs/developer/TESTING_GUIDE.md](docs/developer/TESTING_GUIDE.md) - Testing strategies
- [docs/developer/TESTING_QUICK_REFERENCE.md](docs/developer/TESTING_QUICK_REFERENCE.md) - Quick test commands
- [docs/developer/MODEL_VALIDATION.md](docs/developer/MODEL_VALIDATION.md) - Correctness evidence model for numeric, visual, and AI review
- [docs/developer/AI_DEBUG_WORKFLOW.md](docs/developer/AI_DEBUG_WORKFLOW.md) - Debug bundles and AI-assisted review workflow
- [docs/archive/TESTING_ROADMAP.md](docs/archive/TESTING_ROADMAP.md) - Historical test coverage plans

**Project Planning:**
- [docs/archive/TIACAD_EVOLUTION_ROADMAP.md](docs/archive/TIACAD_EVOLUTION_ROADMAP.md) - Overall project roadmap
- [docs/archive/KNOWN_ISSUES.md](docs/archive/KNOWN_ISSUES.md) - Historical known limitations and improvement plans
- [docs/archive/LANGUAGE_IMPROVEMENTS_STATUS.md](docs/archive/LANGUAGE_IMPROVEMENTS_STATUS.md) - Documentation improvement tracking
- [docs/archive/V3_IMPLEMENTATION_STATUS.md](docs/archive/V3_IMPLEMENTATION_STATUS.md) - Feature implementation status
- [docs/archive/CURRENT_STATUS.md](docs/archive/CURRENT_STATUS.md) - Historical project health snapshot

---

## Testing

### Run All Tests

```bash
# Run full test suite
pytest tiacad_core/tests/ -v

# Quick run
pytest tiacad_core/tests/ -q

# With coverage
pytest tiacad_core/tests/ --cov=tiacad_core --cov-report=html

# Coverage opens in browser
open htmlcov/index.html
```

### Run Specific Components

```bash
# Selector tests
pytest tiacad_core/tests/test_selector_resolver.py -v

# Sketch operation tests
pytest tiacad_core/tests/test_parser/test_sketch_operations.py -v

# Schema validation tests
pytest tiacad_core/tests/test_parser/test_schema_validation.py -v

# Boolean operation tests
pytest tiacad_core/tests/test_parser/test_boolean_builder.py -v

# Testing utilities
pytest tiacad_core/tests/test_testing/ -v

# Correctness tests
pytest tiacad_core/tests/test_correctness/ -v

# Run by category (requires pytest markers)
pytest -m attachment  # Attachment correctness tests
pytest -m rotation    # Rotation correctness tests
pytest -m dimensions  # Dimensional accuracy tests
```

### Code Quality Checks

```bash
# Run ruff on touched files or directories
ruff check tiacad_core/parser tiacad_core/tests/test_parser

# Run pylint (comprehensive analysis)
pylint tiacad_core/ --disable=C0103,C0114,C0115,C0116

# Type checking (if using mypy)
mypy tiacad_core/ --strict
```

---

## Current Status Summary

### Phase Completion

| Phase | Status | Validation Focus |
|-------|--------|------------------|
| Phase 1: Foundation | ✅ Complete | core part, selector, transform, parameter, and sketch behavior |
| Phase 2: Operations | ✅ Complete | parser, primitive builders, boolean/pattern/finishing behavior |
| Phase 3: Sketch Ops | ✅ Complete | extrude, revolve, sweep, loft, schema, assembly validation, export |
| v3.1: Testing Confidence | ✅ Complete | testing utilities, correctness contracts, visual regression |
| v3.1: Component+DAG | ✅ Complete | imports, stdlib components, dependency graph, watch mode |
| Current | ✅ Active | parser, correctness, DAG, validation, visual, and example coverage |

### Component Breakdown

| Component Area | Status | Notes |
|-----------|--------|-------|
| Core model types | ✅ | part, selector, transform, parameter, spatial reference behavior |
| Parser/build pipeline | ✅ | YAML parsing, parts, operations, imports, schema validation |
| Geometry operations | ✅ | primitives, booleans, patterns, finishing, sketch operations |
| Export and visualization | ✅ | STL/STEP/3MF surfaces, visual regression, trust rendering |
| Correctness contracts | ✅ | dimensions, volumes, attachment, rotation, example/trust contracts |
| Debug/review tooling | ✅ | `tiacad check`, `tiacad debug`, geometry summaries, validation reports |

### Real-World Examples

✅ Multiple working examples, all export to STL/3MF:

**Basic Examples:**
1. simple_box.yaml - Primitive shapes
2. simple_guitar_hanger.yaml - Transforms
3. guitar_hanger_with_holes.yaml - Boolean ops

**Pattern Examples:**
4. mounting_plate_with_bolt_circle.yaml - Circular patterns

**Finishing Examples:**
5. rounded_mounting_plate.yaml - Fillet edges
6. chamfered_bracket.yaml - Chamfer edges

**Sketch Operation Examples:**
7. transition_loft.yaml - Loft (square→circle)
8. bottle_revolve.yaml - Revolve profiles
9. pipe_sweep.yaml - Sweep along path

**What Works:**
- Complete YAML → STL/3MF pipeline ✅
- Parametric expressions ✅
- All primitives ✅
- All sketch operations ✅
- All boolean operations ✅
- All pattern types ✅
- Professional finishing ✅
- Schema validation ✅
- Comprehensive error messages ✅
- Production-ready quality ✅

---

## Contributing

This is an active development project with stable core components and production-ready quality.

**Quality Standards:**
- **Test First**: All features require comprehensive tests
- **Code Quality**: Pass focused lint checks for touched code; keep reducing repo-wide lint debt
- **Coverage**: Aim for >80% test coverage
- **Documentation**: Update README and docstrings

**Development Principles:**
- **Explicit Behavior**: No implicit defaults
- **Real Validation**: Test with real CadQuery
- **Error Messages**: Clear, helpful error messages
- **Type Safety**: Use proper type hints

---

## License

Apache 2.0 - see [LICENSE](LICENSE) for details

Copyright 2025 Semantic Infrastructure Lab Contributors

---

## Acknowledgments

Built with:
- **CadQuery**: Powerful parametric 3D CAD library
- **pytest**: Comprehensive testing framework
- **ruff**: Lightning-fast Python linter
- **pytest-cov**: Code coverage measurement

---

**Status:** Active project
**Quality:** Linting, coverage, correctness tests, and example validation are part of the current workflow
**Examples:** See `examples/` plus `docs/user/EXAMPLES_GUIDE.md` for current example coverage and special cases
