
# 🧭 TiaCAD Gap & Opportunity Assessment

*(as of current tiacad_core architecture)*

---

## 🧩 1. Core Architecture Gaps

### 🔸 1.1 No Central Dependency Graph (Scene Tree)

**Current issue:**
TiaCAD executes YAML operations sequentially — once — with no memory of dependencies.
This prevents incremental recomputation, “update on change,” and assembly relationships.

**Impact:**

* Full rebuild required for every parameter tweak
* No true parametric modeling or constraint updates
* Hard to visualize feature lineage

**Solution:**
Implement a **Directed Acyclic Graph (DAG)** of dependencies between:

* Parameters → Sketches → Operations → Parts
* Each node stores results, metadata, and invalidation triggers

Use a lightweight graph engine (`networkx` or custom), and integrate into the `PartRegistry` or a new `ModelGraph` manager.
→ Enables *incremental updates, selective rebuilds, and real-time GUI editing*.

---

### 🔸 1.2 Tight CadQuery Coupling

**Current issue:**
Most builder logic directly calls `cq.Workplane` methods.
The `GeometryBackend` interface exists, but isn’t consistently used across builders.

**Impact:**

* Limits experimentation with alternate geometry engines
* Hinders integration with simulation or mesh-based systems

**Solution:**
Finish backend isolation by enforcing all builders to go through `GeometryBackend`.
Add optional backends:

* `FreeCADBackend` for feature completeness
* `TrimeshBackend` or `Open3DBackend` for mesh workflows
  → Provides kernel independence and modular testing.

---

### 🔸 1.3 No Persistent Model Format

**Current issue:**
Models are ephemeral — built from YAML and exported to `.stl` or `.3mf`, but can’t be reloaded.

**Impact:**

* No “save state” or project concept
* No interoperability with future GUIs or services

**Solution:**
Define a serialized **TiaCAD Model Format** (e.g. `*.tiacad.json`) capturing:

```json
{
  "parameters": {...},
  "parts": {...},
  "operations": {...},
  "dependencies": [...]
}
```

→ Allows session recovery, sharing, and future web/REST interfaces.

---

## 🧱 2. Geometry & CAD Functionality Gaps

| Feature Area            | Current State                                       | Problem / Gap                                    | Recommended Solution                                                                                                           |
| ----------------------- | --------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| **Sketching**           | Simple 2D profiles only                             | No constraint solver, no dimension relationships | Integrate a 2D constraint solver (`pysolvespace` or SymPy-based). Extend `SketchBuilder` to manage constraints and references. |
| **Feature Ops**         | Extrude, Revolve, Sweep, Loft partially implemented | No Shell, Offset, Mirror, or advanced booleans   | Add missing feature classes; mirror via transform + copy, shell via OCC’s `makeThickSolid`.                                    |
| **Assemblies**          | Parts can be referenced, no mate constraints        | No align/flush/offset logic                      | Introduce assembly constraints using a small geometric solver (PyBullet, OCC constraints, or linear algebra solver).           |
| **Finishing**           | Fillet/Chamfer basic                                | No variable-radius or blend surfaces             | Extend builder with radius maps; leverage OCC’s `makeFillet2D/3D`.                                                             |
| **Physical Properties** | None                                                | No volume, center of mass, or mass property calc | Use OCC functions: `Shape.massProperties()`, `BoundingBox()`, `InertiaTensor()`.                                               |
| **Import/Export**       | STL, 3MF only                                       | Missing STEP, IGES, DXF, GLTF                    | Add via `pythonOCC` or `assimp`; export meshes as glTF for web preview.                                                        |

---

## ⚙️ 3. Usability & User Experience Gaps

### 🔸 3.1 No Real-Time Feedback Loop

**Current issue:**
Workflow is static — write YAML → run → view STL.
No iterative feedback or error visualization.

**Solution:**
Add a **live CLI watcher** or **Qt/Browser preview**:

* Auto-reload on YAML file change
* Show tessellated result using `moderngl` or `pygfx`
* Stream errors in structured format

### 🔸 3.2 Limited CLI Output

**Current issue:**
Logs are developer-oriented only.

**Solution:**
Human-friendly summary:

```
✔ Loaded 4 parts
✔ Executed 8 operations (0.72s)
✔ Exported → output/assembly.3mf
```

Include timing, counts, and simple progress bars (`rich` library).

---

## 🧠 4. Data & Parametric Modeling Gaps

### 🔸 4.1 No Parametric Solver

**Problem:**
Parameters can be symbolic (`${...}`) but not interdependent.

**Solution:**
Implement a symbolic math layer (SymPy or CasADi) so parameters can depend on other values:

```yaml
parameters:
  hole_d: 5
  bolt_clearance: ${hole_d + 0.3}
```

→ Enables *true parametric models and dimension-driven edits*.

---

### 🔸 4.2 No Units or Dimensional Consistency

**Problem:**
All numeric values are unitless floats.

**Solution:**
Adopt a units library (`pint` or `unyt`) for explicit unit tracking:

```yaml
width: 100 mm
height: 4 in
```

→ Prevents silent unit mismatches.

---

## 🔧 5. Ecosystem & Integration Gaps

| Area                    | Current                 | Missing                          | Solution                                                            |
| ----------------------- | ----------------------- | -------------------------------- | ------------------------------------------------------------------- |
| **BOM / Metadata**      | Only YAML metadata      | No aggregation, no cost tracking | Collect metadata from `PartRegistry` → export as CSV/XLSX           |
| **Plugins**             | Monolithic architecture | Hard to extend                   | Implement plugin hooks: register new primitives, exporters, solvers |
| **API / Service Layer** | None                    | No way to call from web/app      | Expose `tiacad_core` as HTTP/REST or Python API service             |
| **Documentation**       | Partial docstrings      | No dev or user guide             | Generate docs via `mkdocs` or `pdoc`                                |

---

## 🎨 6. Visualization Gaps

### 🔸 6.1 Static Tessellation Only

**Problem:**
No GPU or interactive rendering, just tessellate → file.

**Solution:**
Add an optional **visualization layer**:

* `visualization/gpu_renderer.py` using `moderngl` or `pygfx`
* Render meshes with colors from `materials_library.py`
* Future-proof by supporting WebGPU or glTF output

---

### 🔸 6.2 Appearance Metadata Unused

**Problem:**
Color and material data exist but never influence rendering or exports.

**Solution:**
Integrate appearance metadata into tessellation/exporters:

* Include PBR data in glTF
* Add per-face color attributes

---

## 🔬 7. Quality & Tooling Gaps

| Area                  | Gap                          | Solution                                                |
| --------------------- | ---------------------------- | ------------------------------------------------------- |
| **Test Coverage**     | Uneven in builders (~60–70%) | Add integration tests for complex multi-operation YAMLs |
| **Schema Validation** | Mostly structural            | Add semantic validation (e.g., param consistency)       |
| **Error Reporting**   | Stack traces only            | Structured error objects (with source file + line info) |
| **Benchmarking**      | None                         | Add time-per-operation and memory profiling hooks       |

---

## 🌐 8. Strategic Platform Gaps

| Goal                                | Current Situation | Recommended Direction                                 |
| ----------------------------------- | ----------------- | ----------------------------------------------------- |
| **Persistent modeling environment** | Stateless CLI     | Add `ProjectManager` abstraction with history         |
| **Web / GUI integration**           | None              | Build minimal web viewer (FastAPI + WebGL)            |
| **Collaboration**                   | Local only        | Prepare for cloud model storage and shared param sets |
| **Licensing**                       | Not declared      | Choose Apache 2.0 or MIT for open ecosystem growth    |

---

## 🧭 Summary Table

| Category                   | Priority  | Description                      | Solution Keywords           |
| -------------------------- | --------- | -------------------------------- | --------------------------- |
| Core DAG architecture      | 🔥 High   | Enable incremental recomputation | `networkx`, `ModelGraph`    |
| Sketch & constraint solver | 🔥 High   | True parametric sketches         | `pysolvespace`, `sympy`     |
| Assembly constraints       | 🔥 High   | Align/mate relationships         | `pybullet`, OCC solver      |
| Visualization              | ⚡ Medium  | Real-time view / glTF export     | `moderngl`, `pygfx`, `gltf` |
| Parametric solver & units  | ⚡ Medium  | Symbolic parameters & units      | `sympy`, `pint`             |
| Export/Import              | ⚡ Medium  | STEP/DXF support                 | `pythonOCC`, `assimp`       |
| Metadata / BOM             | 🧩 Medium | Generate reports                 | `pandas`, CSV export        |
| Plugin & API layer         | 🔥 High   | Extensibility for community      | `entrypoints`, `FastAPI`    |
| Documentation & tests      | ⚡ Medium  | Completeness & reliability       | `mkdocs`, pytest            |

---

## 🧠 TL;DR — Strategic Focus

TiaCAD is **structurally sound** — its modular YAML → Builder → Geometry pipeline is a strong foundation.
To evolve from a “scripted CAD generator” into a **modern CAD platform**, it should focus on four axes:

1. **Recomputable Core:** add a dependency graph and parametric solver
2. **Smart Geometry:** constraint-based sketches and assemblies
3. **Interactive Feedback:** real-time viewer, GUI, live YAML reload
4. **Open Ecosystem:** plugins, project format, BOM, and service APIs

