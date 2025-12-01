# TiaCAD v5.0 Architecture Specification: Full CGA Integration

**Document Type:** Architecture Specification
**Version:** 5.0 Draft
**Date:** 2025-12-01
**Source:** ChatGPT architectural design conversation
**Status:** Planning / Design Phase

---

## Executive Summary

TiaCAD v5.0 represents a fundamental architectural shift: introducing **Conformal Geometric Algebra (CGA)** as the core mathematical foundation for all geometric operations. This document specifies a complete redesign that unifies analytic geometry, constraint solving, solid modeling (BREP), and CAM (slicing/toolpaths) under a single CGA kernel.

**Key Innovation:** Replace ad-hoc geometric primitives with mathematically rigorous CGA multivectors, enabling exact analytic operations (intersections, projections, distances, offsets) that currently require numerical approximation or BREP topology queries.

---

## 1. Goals & Scope

### What is TiaCAD + CGA?

> A declarative, parametric CAD system backed by a **Conformal Geometric Algebra (CGA)** kernel, capable of driving both **solid modeling (via BREP)** and **CAM (slicing/toolpaths)** from a unified analytic geometry core.

### Core Goals

1. **Unified Geometric Representation**
   - Points, lines, planes, circles, spheres, surfaces represented as CGA multivectors
   - Eliminates separate code paths for different primitive types

2. **Analytic CGA Operations**
   - Intersections (meet)
   - Spans (join)
   - Distance computations
   - Projections
   - Offsets (analytic where possible)
   - Envelope operations

3. **Native Constraint Support**
   - Incidence constraints (point-on-line, line-in-plane)
   - Distance constraints
   - Angle constraints
   - Tangency constraints
   - All expressed as CGA equations

4. **Parametric DAG**
   - Parameters → Geometry → Constraints → Solids
   - Efficient recomputation on parameter changes
   - Clear dependency tracking

5. **BREP Realization**
   - CGA provides exact geometry
   - OCCT/CadQuery realizes as B-rep solids
   - Maintains tolerance control

6. **CGA-Based CAM**
   - Slicing via CGA plane intersections
   - Toolpath offsets via CGA operations
   - Supports both FDM (3D printing) and CNC milling

---

## 2. High-Level Architecture

### Layer Stack (Top → Bottom)

```
┌─────────────────────────────────────────────────────┐
│  1. TiaCAD DSL (YAML / Config Files)                │
│     - Parts, assemblies, constraints, CAM jobs      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  2. Front-End & IR                                   │
│     - Parser → AST → IR                              │
│     - Geometry, transforms, constraints, CAM         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  3. Parametric DAG                                   │
│     - Nodes: params, expressions, CGA objects,       │
│       solids, toolpaths                              │
│     - Edges: dependency & recomputation order        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  4. CGA Analytic Kernel ⭐ NEW CORE                  │
│     - Multivector types (GA(4,1))                    │
│     - Semantic wrappers: Point/Line/Plane/Circle/    │
│       Sphere                                         │
│     - Motors for SE(3) transformations               │
│     - Core ops: meet, join, project, distance,       │
│       offset                                         │
└─────────────────────────────────────────────────────┘
         ↓                                    ↓
┌──────────────────────┐          ┌──────────────────────┐
│  5. Constraint Engine │          │  6. BREP Backend     │
│  - Works in CGA space │          │  - CadQuery/OCCT     │
│  - Residual equations │          │  - Solid realization │
│  - Numerical solver   │          │  - STEP/STL export   │
└──────────────────────┘          └──────────────────────┘
                        ↓
                ┌─────────────────┐
                │  7. CAM Engine  │
                │  - CGA slicing  │
                │  - CGA toolpaths│
                │  - G-code gen   │
                └─────────────────┘
```

### Key Architectural Principles

1. **CGA as Foundation:** All geometry internally represented as CGA multivectors
2. **Semantic Type Safety:** Wrap raw multivectors in typed classes (Point3, Line3, etc.)
3. **Lazy Evaluation:** DAG enables selective recomputation
4. **Clear Separation:** Analytic (CGA) vs. Approximate (BREP) operations
5. **Composability:** Operations compose via well-defined interfaces

---

## 3. CGA Kernel Specification

### 3.1 Algebra Choice

**Conformal Geometric Algebra (CGA) for 3D Euclidean space**

- **Algebra:** GA(4,1) - 5D conformal model
- **Basis:**
  - Euclidean basis: `e₁, e₂, e₃`
  - Null directions: `e₀` (origin), `e∞` (infinity)
  - Metric signature: `(4,1)` - four positive, one negative

**Why CGA?**
- Represents points, lines, planes, circles, spheres uniformly
- Rigid transformations (rotations + translations) → motors (single multivector)
- Intersections, projections, distances → simple algebraic operations
- No special cases for parallel/perpendicular/coincident geometry

### 3.2 Core Multivector Implementation

```python
class Multivector:
    """
    GA(4,1) multivector with 32 coefficients:
    - 1 scalar
    - 5 vectors (e₁, e₂, e₃, e₀, e∞)
    - 10 bivectors (e₁₂, e₁₃, e₂₃, e₁₀, ...)
    - 10 trivectors
    - 5 quadvectors
    - 1 pseudoscalar (e₁₂₃₀∞)
    """
    coeffs: np.ndarray  # shape (32,)

    # Fundamental operations
    def __add__(self, other: 'Multivector') -> 'Multivector': ...
    def __sub__(self, other: 'Multivector') -> 'Multivector': ...
    def __mul__(self, other: 'Multivector') -> 'Multivector':
        """Geometric product"""
        ...

    def wedge(self, other: 'Multivector') -> 'Multivector':
        """Outer product (∧) - creates higher-grade objects"""
        ...

    def inner(self, other: 'Multivector') -> 'Multivector':
        """Inner product (⋅) - contracts grades"""
        ...

    def dual(self) -> 'Multivector':
        """Hodge dual (*) - IPNS ↔ OPNS conversion"""
        ...

    def norm(self) -> float:
        """Magnitude in CGA metric"""
        ...

    def normalize(self) -> 'Multivector':
        """Unit multivector"""
        ...

    def grade(self, k: int) -> 'Multivector':
        """Extract k-vector part"""
        ...

    def reverse(self) -> 'Multivector':
        """Reverse (∼) - for motor inverse"""
        ...
```

### 3.3 Semantic Geometry Types

Type-safe wrappers over raw multivectors:

```python
class Point3:
    """
    Point in 3D as null vector in CGA:
    P(x) = x₁e₁ + x₂e₂ + x₃e₃ + ½(x·x)e∞ + e₀

    Invariant: P·P = 0 (null vector)
    Grade: 1 (vector)
    """
    mv: Multivector

    @classmethod
    def from_euclidean(cls, x: float, y: float, z: float) -> 'Point3':
        """Construct from Cartesian coordinates"""
        ...

    def to_euclidean(self) -> tuple[float, float, float]:
        """Extract (x, y, z) coordinates"""
        ...

class Line3:
    """
    Line in 3D as 3-blade (wedge of two points + e∞):
    L = P₁ ∧ P₂ ∧ e∞

    Represents: Line through P₁ and P₂
    Grade: 3 (trivector)
    """
    mv: Multivector

    @classmethod
    def from_points(cls, p1: Point3, p2: Point3) -> 'Line3':
        """Line through two points"""
        ...

    @classmethod
    def from_origin_direction(cls, origin: Point3, direction: np.ndarray) -> 'Line3':
        """Line from point and direction vector"""
        ...

class Plane3:
    """
    Plane in 3D as vector (IPNS) or 4-blade (OPNS):

    IPNS (point-normal form):
    π = n₁e₁ + n₂e₂ + n₃e₃ + d·e∞

    OPNS (three-point form):
    π = P₁ ∧ P₂ ∧ P₃ ∧ e∞

    Grade: 1 (IPNS) or 4 (OPNS)
    """
    mv: Multivector
    representation: Literal['IPNS', 'OPNS']

    @classmethod
    def from_point_normal(cls, point: Point3, normal: np.ndarray) -> 'Plane3':
        """IPNS representation"""
        ...

    @classmethod
    def from_points(cls, p1: Point3, p2: Point3, p3: Point3) -> 'Plane3':
        """OPNS representation"""
        ...

class Circle3:
    """
    Circle in 3D as 3-blade:
    C = P₁ ∧ P₂ ∧ P₃

    Three points define unique circle
    Grade: 3 (trivector)
    """
    mv: Multivector

    @classmethod
    def from_points(cls, p1: Point3, p2: Point3, p3: Point3) -> 'Circle3':
        ...

    @classmethod
    def from_center_normal_radius(cls, center: Point3,
                                   normal: np.ndarray,
                                   radius: float) -> 'Circle3':
        ...

class Sphere3:
    """
    Sphere in 3D as 4-blade:
    S = P₁ ∧ P₂ ∧ P₃ ∧ P₄

    Four points define unique sphere
    Grade: 4 (quadvector)
    """
    mv: Multivector

    @classmethod
    def from_center_radius(cls, center: Point3, radius: float) -> 'Sphere3':
        ...

class Motor3:
    """
    Conformal motor: combined rotation + translation

    M = exp(½ B) where B is bivector generator

    Properties:
    - M·M̃ = 1 (unit motor)
    - Transforms objects: X' = M·X·M̃

    Grade: 0 + 2 + 4 (scalar + bivector + quadvector)
    """
    mv: Multivector

    @classmethod
    def from_rotation(cls, axis: np.ndarray, angle: float) -> 'Motor3':
        """Pure rotation motor"""
        ...

    @classmethod
    def from_translation(cls, displacement: np.ndarray) -> 'Motor3':
        """Pure translation motor"""
        ...

    @classmethod
    def from_rotation_translation(cls, axis: np.ndarray, angle: float,
                                   displacement: np.ndarray) -> 'Motor3':
        """Combined transformation"""
        ...

    def inverse(self) -> 'Motor3':
        """M̃ (reverse)"""
        ...
```

### 3.4 Core CGA Operations

#### Meet (Intersection)

```python
def meet(a: Union[Line3, Plane3, Circle3, Sphere3],
         b: Union[Line3, Plane3, Circle3, Sphere3]) -> Union[Point3, Line3, Circle3]:
    """
    Intersection of geometric objects via outer product in dual space.

    Examples:
    - Line ∧ Plane → Point
    - Plane ∧ Plane → Line
    - Sphere ∧ Plane → Circle
    - Line ∧ Line → Point (if intersecting) or None

    Returns None if objects don't intersect.
    """
    result_mv = a.mv.dual().wedge(b.mv.dual()).dual()
    return _classify_blade(result_mv)
```

#### Join (Span)

```python
def join(objects: list[Point3 | Line3 | Plane3]) -> Union[Line3, Plane3, Circle3, Sphere3]:
    """
    Smallest object containing all inputs via wedge product.

    Examples:
    - join(P₁, P₂) → Line
    - join(P₁, P₂, P₃) → Plane or Circle
    - join(P₁, P₂, P₃, P₄) → Sphere
    """
    result = objects[0].mv
    for obj in objects[1:]:
        result = result.wedge(obj.mv)
    return _classify_blade(result)
```

#### Distance

```python
def distance(a: Union[Point3, Line3, Plane3],
             b: Union[Point3, Line3, Plane3]) -> float:
    """
    Conformal distance between objects.

    For points: Euclidean distance
    For point-line/plane: perpendicular distance
    For line-line: minimum distance
    """
    if isinstance(a, Point3) and isinstance(b, Point3):
        # -2(P₁·P₂) gives squared Euclidean distance
        return np.sqrt(-2.0 * a.mv.inner(b.mv).coeffs[0])

    elif isinstance(a, Point3) and isinstance(b, Plane3):
        # Point-plane distance
        return abs(a.mv.inner(b.mv).coeffs[0])

    # ... other cases
```

#### Projection

```python
def project(obj: Union[Point3, Line3],
            onto: Union[Line3, Plane3, Sphere3]) -> Union[Point3, Line3]:
    """
    Project object onto target.

    Examples:
    - project(Point, Plane) → Point (closest point on plane)
    - project(Point, Line) → Point (perpendicular foot)
    - project(Line, Plane) → Line (if line ∦ plane) or Point
    """
    # Use reflection formula:
    # projection(X, Y) = (X·Y)·Y⁻¹
    ...
```

#### Transformation

```python
def apply(motor: Motor3,
          obj: Union[Point3, Line3, Plane3, Circle3, Sphere3]) -> ...:
    """
    Apply motor transformation: X' = M·X·M̃

    Preserves:
    - Distances (isometry)
    - Angles
    - Incidence relations
    """
    m_tilde = motor.inverse()
    result_mv = motor.mv * obj.mv * m_tilde.mv
    return _restore_type(result_mv, type(obj))

def compose(m1: Motor3, m2: Motor3) -> Motor3:
    """
    Compose transformations: M = M₂·M₁
    (Apply M₁ first, then M₂)
    """
    return Motor3(m2.mv * m1.mv)
```

#### Offset (Analytic)

```python
def offset(obj: Union[Line3, Plane3, Circle3],
           distance: float) -> ...:
    """
    Analytic offset where possible.

    - Line: parallel line at distance
    - Plane: parallel plane at distance
    - Circle: concentric circle with radius ± distance
    - General curves: may require numerical approximation
    """
    if isinstance(obj, Plane3):
        # Translate plane along normal
        normal = _extract_normal(obj)
        translation = Motor3.from_translation(distance * normal)
        return apply(translation, obj)

    elif isinstance(obj, Circle3):
        center = _extract_center(obj)
        radius = _extract_radius(obj)
        new_radius = radius + distance
        return Circle3.from_center_normal_radius(
            center, _extract_normal(obj), new_radius
        )

    # ... other cases
```

---

## 4. Geometry Model on Top of CGA

### 4.1 Core Data Structures

```python
class SketchCurve:
    """
    2D curve embedded in 3D via sketch plane.
    Backed by CGA representation.
    """
    cga_object: Union[Line3, Circle3]
    sketch_coords: Optional[np.ndarray]  # 2D coordinates

class Sketch:
    """
    Collection of curves with constraints in a reference plane.
    """
    plane: Plane3  # Sketch plane in 3D
    curves: list[SketchCurve]
    constraints: list['Constraint']
    is_closed: bool

class Feature:
    """
    Construction operation on geometry.
    """
    feature_type: FeatureType  # Extrude, Revolve, Loft, Sweep
    input_sketch: Sketch
    params: dict[str, Any]

    def compute_cga_geometry(self) -> ...:
        """Generate intermediate CGA representation"""
        ...

class SolidRef:
    """
    Reference to BREP solid with CGA approximation.
    """
    brep_id: str
    cga_approx: Optional[Union[Sphere3, list[Plane3]]]  # Bounding geometry

class Frame3:
    """
    Local coordinate system.
    """
    origin: Point3
    orientation: Motor3  # From global frame

class Ref:
    """
    Named reference to geometry entity.
    """
    name: str
    frame: Frame3
    target: Union[Point3, Line3, Plane3, SolidRef]
```

### 4.2 Coordinate Frame Model

All geometry exists within frames:

- **Global Frame:** World coordinates
- **Part Frame:** Local to each part
- **Sketch Frame:** 2D embedded in 3D
- **Feature Frame:** Relative to parent geometry

Transformations between frames use `Motor3`.

```python
def transform_to_frame(obj: Union[Point3, Line3, ...],
                       from_frame: Frame3,
                       to_frame: Frame3) -> ...:
    """
    Transform object between coordinate frames.
    """
    # Compose: from_frame → global → to_frame
    to_global = from_frame.orientation
    from_global = to_frame.orientation.inverse()
    motor = compose(from_global, to_global)
    return apply(motor, obj)
```

---

## 5. DSL / YAML Surface

TiaCAD's YAML syntax stays largely the same, but internal implementation uses CGA.

### 5.1 Geometry Section

```yaml
geometry:
  frames:
    base:
      origin: [0, 0, 0]
      orientation:
        type: axis_angle
        axis: [0, 0, 1]
        angle: 0deg

  sketches:
    profile:
      frame: base
      curves:
        - type: line
          from: [0, 0]
          to: [100, 0]

        - type: arc
          center: [50, 20]
          radius: 20
          start_angle: 180deg
          end_angle: 0deg

  features:
    base_extrusion:
      type: extrude
      sketch: profile
      distance: 10
      direction: [0, 0, 1]  # Converts to Motor3 internally
```

**Internal Processing:**
1. Parse YAML → AST
2. Convert frames → `Frame3` with `Motor3`
3. Convert 2D sketch coords → `Point3` in sketch plane
4. Lines/arcs → `Line3`/`Circle3` via CGA constructors
5. Extrude direction → motor for sweep

### 5.2 Constraints Section

```yaml
constraints:
  # Point coincidence
  - type: coincident
    point: profile.curve[0].start
    target: base.origin

  # Perpendicularity
  - type: perpendicular
    curve_a: profile.curve[0]
    curve_b: profile.curve[1]

  # Distance constraint
  - type: distance
    point_a: profile.curve[0].end
    point_b: profile.curve[1].start
    value: 10.0

  # Tangency
  - type: tangency
    curve_a: profile.curve[1]
    curve_b: profile.curve[2]
```

Each compiles to CGA residual equations (see Section 6).

### 5.3 CAM Section

```yaml
cam:
  jobs:
    bracket_mill:
      type: cnc
      tool:
        shape: endmill
        diameter: 6
        flute_length: 20

      strategy:
        type: contour
        stepover: 2
        stepdown: 1

      stock:
        size: [120, 80, 20]

      part: base_extrusion

    bracket_print:
      type: fdm
      nozzle_diameter: 0.4
      layer_height: 0.2
      infill:
        type: gyroid
        density: 0.25
```

CAM engine uses:
- BREP solid for exact part shape
- CGA for slicing (plane intersections)
- CGA for toolpath offsets

---

## 6. Constraint System (CGA-Backed)

Each constraint type translates to **scalar residual equations** in CGA space.

### 6.1 Constraint Types → CGA Residuals

Let `P, Q` be `Point3`, `L` be `Line3`, `π` be `Plane3`, `C` be `Circle3`.

#### Coincident (Point-Point)

**Constraint:** Points `P` and `Q` are the same
**Residual:**
```
r = distance(P, Q) = 0
```

#### Point on Line

**Constraint:** Point `P` lies on line `L`
**Residual:**
```
r = ||P ∧ L|| = 0
```
(Wedge product vanishes if point is on line)

#### Point on Plane

**Constraint:** Point `P` lies on plane `π`
**Residual:**
```
r = P · π = 0
```
(Inner product with IPNS plane)

#### Distance Constraint

**Constraint:** Distance between `P` and `Q` equals `d`
**Residual:**
```
r = distance(P, Q) - d = 0
```

#### Perpendicular Lines

**Constraint:** Lines `L₁` and `L₂` are perpendicular
**Residual:**
```
r = L₁ · L₂ = 0
```
(Inner product of direction bivectors)

#### Parallel Lines

**Constraint:** Lines `L₁ ∥ L₂`
**Residual:**
```
r = ||L₁ ∧ L₂|| = 0
```
(Wedge vanishes for parallel directions)

#### Tangency (Circle to Line)

**Constraint:** Circle `C` tangent to line `L`
**Residual:**
```
r = distance(center(C), L) - radius(C) = 0
```

### 6.2 Constraint Solver

**Problem:** Given parameter vector `p ∈ ℝⁿ`, find `p*` such that all constraints are satisfied.

**Formulation:** Nonlinear least squares
```
minimize  ||r(p)||² = Σᵢ rᵢ(p)²
```

Where each `rᵢ` is a constraint residual.

**Solver:** Gauss-Newton or Levenberg-Marquardt

```python
class ConstraintSolver:
    """
    Numerical solver for CGA-based constraint systems.
    """

    def __init__(self, constraints: list[Constraint],
                 parameters: ParameterSet):
        self.constraints = constraints
        self.parameters = parameters

    def residual_vector(self, p: np.ndarray) -> np.ndarray:
        """
        Evaluate all constraint residuals at parameter values p.
        """
        residuals = []
        for constraint in self.constraints:
            r = constraint.evaluate_cga(p, self.parameters)
            residuals.append(r)
        return np.array(residuals)

    def jacobian(self, p: np.ndarray) -> np.ndarray:
        """
        Compute Jacobian matrix ∂r/∂p via automatic differentiation.
        """
        # Use JAX or manual symbolic differentiation of CGA operations
        ...

    def solve(self, initial_guess: np.ndarray,
              tol: float = 1e-6,
              max_iter: int = 100) -> SolverResult:
        """
        Gauss-Newton iteration:

        p_{k+1} = p_k - (J^T J)^{-1} J^T r(p_k)
        """
        p = initial_guess

        for iteration in range(max_iter):
            r = self.residual_vector(p)

            if np.linalg.norm(r) < tol:
                return SolverResult(success=True, p=p, residual=r)

            J = self.jacobian(p)
            delta = np.linalg.lstsq(J.T @ J, -J.T @ r, rcond=None)[0]
            p = p + delta

        return SolverResult(success=False, p=p, residual=r)
```

**Detection of Over/Under-Constrained Systems:**

- **Over-constrained:** `rank(J) < len(constraints)` → Inconsistent system
- **Under-constrained:** `rank(J) < len(parameters)` → Null-space DOFs

---

## 7. Parametric DAG & Recomputation

TiaCAD maintains a directed acyclic graph (DAG) of dependencies.

### 7.1 Node Types

```python
class DAGNode(ABC):
    node_id: str
    dependencies: list['DAGNode']
    dirty: bool

    @abstractmethod
    def recompute(self) -> None: ...

class ParameterNode(DAGNode):
    """Leaf node: user-defined scalar/vector parameter"""
    value: float | np.ndarray

class ExpressionNode(DAGNode):
    """Computed from other parameters"""
    expression: Callable

    def recompute(self):
        self.value = self.expression(*[d.value for d in self.dependencies])

class CGAObjectNode(DAGNode):
    """Point3, Line3, Plane3, Circle3, Sphere3, Motor3"""
    cga_object: Union[Point3, Line3, ...]

    def recompute(self):
        # Reconstruct CGA object from dependency values
        ...

class ConstraintNode(DAGNode):
    """Represents constraint equations"""
    constraint: Constraint

    def recompute(self):
        # Re-solve constraints if parameters changed
        ...

class FeatureNode(DAGNode):
    """Extrude, Loft, Revolve, Sweep"""
    feature: Feature

    def recompute(self):
        # Rebuild CGA intermediate geometry
        ...

class SolidNode(DAGNode):
    """BREP solid reference"""
    solid_ref: SolidRef

    def recompute(self):
        # Regenerate BREP solid via CadQuery
        ...

class CAMNode(DAGNode):
    """Slicing, toolpaths, G-code"""
    cam_job: CAMJob

    def recompute(self):
        # Recompute toolpaths from updated solid
        ...
```

### 7.2 Recomputation Algorithm

```python
def mark_dirty(node: DAGNode):
    """Recursively mark node and downstream dependencies as dirty"""
    if node.dirty:
        return  # Already marked

    node.dirty = True
    for dependent in node.dependents:  # Reverse edges
        mark_dirty(dependent)

def recompute_dag(root: DAGNode):
    """Topologically sorted recomputation"""
    sorted_nodes = topological_sort(root)

    for node in sorted_nodes:
        if node.dirty:
            node.recompute()
            node.dirty = False
```

**Example Flow:**
1. User changes parameter `width`
2. `mark_dirty(width_param)` → marks all downstream nodes dirty
3. `recompute_dag(root)` → rebuilds:
   - CGA points depending on `width`
   - Constraints referencing those points (re-solve)
   - Features using sketch geometry
   - BREP solids from features
   - CAM toolpaths from solids

---

## 8. BREP Integration (CadQuery / OCCT)

CGA provides **exact analytic geometry**. BREP provides **solid modeling** and **export**.

### 8.1 Why Keep BREP?

Even with CGA, BREP is essential for:

1. **Solid Modeling:** Booleans, fillets, chamfers, shells
2. **Tolerances:** B-rep handles approximation errors
3. **Meshing:** STL/3MF export requires triangulation
4. **CAD Interop:** STEP files are B-rep based
5. **Rendering:** Graphics engines expect meshes

### 8.2 Mapping CGA → CadQuery

```python
class CGAToCadQueryAdapter:
    """
    Convert CGA geometry to CadQuery operations.
    """

    def point_to_tuple(self, p: Point3) -> tuple[float, float, float]:
        return p.to_euclidean()

    def line_to_edge(self, line: Line3) -> cq.Edge:
        """Convert Line3 to CadQuery edge"""
        origin, direction = _line_to_origin_direction(line)
        p1 = origin
        p2 = origin + 100 * direction  # Arbitrary length
        return cq.Edge.makeLine(
            cq.Vector(*p1.to_euclidean()),
            cq.Vector(*p2.to_euclidean())
        )

    def circle_to_wire(self, circle: Circle3) -> cq.Wire:
        """Convert Circle3 to CadQuery wire"""
        center = _extract_center(circle)
        radius = _extract_radius(circle)
        normal = _extract_normal(circle)

        # Create workplane perpendicular to circle
        plane = cq.Plane(
            origin=cq.Vector(*center.to_euclidean()),
            normal=cq.Vector(*normal)
        )
        return cq.Workplane(plane).circle(radius).val()

    def motor_to_transform(self, motor: Motor3) -> cq.Matrix:
        """Convert Motor3 to CadQuery transformation matrix"""
        # Extract rotation matrix + translation vector
        rot_matrix = motor.to_rotation_matrix()
        translation = motor.to_translation_vector()

        return cq.Matrix([
            [rot_matrix[0,0], rot_matrix[0,1], rot_matrix[0,2], translation[0]],
            [rot_matrix[1,0], rot_matrix[1,1], rot_matrix[1,2], translation[1]],
            [rot_matrix[2,0], rot_matrix[2,1], rot_matrix[2,2], translation[2]],
            [0, 0, 0, 1]
        ])
```

### 8.3 Feature Realization

```python
class ExtrudeFeature(Feature):
    """
    Extrusion backed by CGA → realized as BREP solid.
    """

    def realize_brep(self, adapter: CGAToCadQueryAdapter) -> SolidRef:
        """
        Convert CGA sketch → CadQuery extrusion.
        """
        # Get sketch geometry
        sketch_wire = self._sketch_to_cadquery_wire(adapter)

        # Extrude
        workplane = cq.Workplane("XY").add(sketch_wire)
        solid = workplane.extrude(self.params["distance"])

        return SolidRef.from_cadquery(solid)

    def _sketch_to_cadquery_wire(self, adapter):
        edges = []
        for curve in self.input_sketch.curves:
            if isinstance(curve.cga_object, Line3):
                edges.append(adapter.line_to_edge(curve.cga_object))
            elif isinstance(curve.cga_object, Circle3):
                edges.append(adapter.circle_to_wire(curve.cga_object))

        return cq.Wire.assembleEdges(edges)
```

---

## 9. CAM (Slicing & Toolpaths) on CGA

CAM operations leverage CGA for **exact geometric computations** while using BREP for part representation.

### 9.1 FDM Slicing (3D Printing)

**Algorithm:**
1. Define slice planes: `π_k = Plane3(z = k·layer_height)`
2. Intersect part surface with planes: `slice_curves = part_surface ∧ π_k`
3. Offset curves for nozzle radius: `toolpath = offset(slice_curve, nozzle_radius/2)`
4. Generate infill geometry (gyroid, honeycomb) using CGA
5. Convert to G-code

```python
class FDMSlicer:
    def slice(self, solid: SolidRef, layer_height: float,
              nozzle_diameter: float) -> list[Toolpath]:
        """
        Slice solid into horizontal layers using CGA planes.
        """
        toolpaths = []

        # Get bounding box
        bbox = solid.get_bounding_box()
        z_min, z_max = bbox.z_range

        # Generate slice planes
        num_layers = int((z_max - z_min) / layer_height)

        for layer in range(num_layers):
            z = z_min + layer * layer_height
            plane = Plane3.from_point_normal(
                Point3.from_euclidean(0, 0, z),
                np.array([0, 0, 1])
            )

            # Intersect BREP with CGA plane
            slice_curves = self._intersect_brep_with_plane(solid, plane)

            # Offset for nozzle
            perimeter_paths = [
                offset(curve, -nozzle_diameter/2)
                for curve in slice_curves
            ]

            # Generate infill (using CGA)
            infill_paths = self._generate_infill_cga(slice_curves, plane)

            toolpaths.append(Toolpath(
                layer=layer,
                perimeter=perimeter_paths,
                infill=infill_paths
            ))

        return toolpaths

    def _intersect_brep_with_plane(self, solid, plane):
        """
        Convert BREP faces to CGA patches, intersect with plane.
        """
        # BREP → piecewise CGA surfaces
        # For each face:
        #   - Approximate as collection of triangles or NURBS patches
        #   - Convert to local CGA representation (planes, spheres)
        #   - Compute plane ∧ patch
        ...

    def _generate_infill_cga(self, boundary_curves, plane):
        """
        Generate infill pattern using CGA geometric operations.
        """
        # Gyroid: implicit surface function
        # Honeycomb: regular line patterns in plane
        # Compute intersections with boundary using CGA meet()
        ...
```

### 9.2 CNC Toolpaths

**Algorithm:**
1. Represent tool as CGA solid (sphere for ball mill, cylinder for endmill)
2. Compute swept volume: `V = ⋃_t Motor(t)·Tool`
3. Contact curves: `toolpath(t) = Tool(t) ∧ PartSurface`
4. Collision detection: `SweptVolume ∧ Fixture`
5. Generate G-code

```python
class CNCToolpathGenerator:
    def generate_contour_path(self, solid: SolidRef,
                              tool: ToolGeometry,
                              stepover: float) -> Toolpath:
        """
        Generate contour toolpath using CGA for offset calculations.
        """
        # Get top face
        top_face = solid.get_top_face()

        # Extract boundary curve
        boundary = self._extract_boundary_cga(top_face)

        # Generate offset curves
        paths = []
        offset_distance = tool.diameter / 2

        while boundary.has_area():
            # Offset inward
            toolpath_curve = offset(boundary, -offset_distance)
            paths.append(toolpath_curve)

            boundary = offset(boundary, -stepover)

        return Toolpath(strategy="contour", curves=paths)

    def check_collision(self, toolpath: Toolpath,
                        fixture: SolidRef) -> list[Collision]:
        """
        Use CGA to detect tool-fixture collisions.
        """
        collisions = []

        for t, tool_position in enumerate(toolpath.positions):
            # Transform tool geometry to current position
            tool_motor = Motor3.from_translation(tool_position)
            transformed_tool = apply(tool_motor, self.tool_geometry)

            # Check intersection with fixture
            intersection = meet(transformed_tool, fixture.cga_approx)

            if intersection is not None:
                collisions.append(Collision(time=t, location=tool_position))

        return collisions
```

---

## 10. Integration with Morphogen & Philbrick

### 10.1 Morphogen → TiaCAD

**Morphogen** generates scalar/vector fields (distance fields, reaction-diffusion patterns, stress distributions).

**Integration Points:**

1. **Level Sets → Geometry**
   ```python
   def morphogen_field_to_surface(field: MorphogenField,
                                   isovalue: float) -> list[Point3]:
       """Extract isosurface as point cloud, fit CGA primitives"""
       points = field.extract_isosurface(isovalue)

       # Fit geometric primitives (planes, spheres, cylinders)
       primitives = fit_cga_primitives(points)
       return primitives
   ```

2. **Parametric Coupling**
   ```python
   # Morphogen simulation result influences TiaCAD parameter
   stress_field = morphogen.run_fea(part)
   max_stress = stress_field.max()

   # Parametric thickening based on stress
   thickness_param.value = base_thickness + scale_factor * max_stress
   ```

3. **Topology Optimization**
   ```python
   # Morphogen optimizes material distribution
   density_field = morphogen.topology_optimize(part, constraints)

   # Convert to TiaCAD solid
   optimized_solid = field_to_brep(density_field, threshold=0.5)
   ```

### 10.2 Philbrick → TiaCAD

**Philbrick** is a modular synthesis hardware platform.

**Use Cases:**

1. **Front Panel Design**
   ```yaml
   # TiaCAD generates Philbrick front panels with precise alignment
   parts:
     front_panel:
       type: extrude
       sketch: panel_layout
       features:
         - type: pattern
           object: knob_hole
           positions: grid(5, 3)  # 5x3 grid of knob holes
   ```

2. **PCB Mounting Plates**
   ```python
   # CGA ensures precise alignment of mounting holes
   def generate_philbrick_mount(module_spec):
       # Module dimensions from spec
       holes = [
           Point3.from_euclidean(*pos)
           for pos in module_spec.mounting_holes
       ]

       # Generate mounting plate with exact hole positions
       plate = extrude(rectangle(module_spec.width, module_spec.height), 3)

       for hole_pos in holes:
           plate = boolean_subtract(plate, cylinder(hole_pos, radius=2.5))

       return plate
   ```

3. **Enclosure Generation**
   ```python
   # TiaCAD generates enclosures fitting Philbrick module dimensions
   enclosure = generate_enclosure(
       internal_clearance=module_spec.bounding_box,
       wall_thickness=3.0,
       ventilation_pattern="honeycomb"
   )
   ```

---

## 11. Implementation Phases

Full CGA support is a multi-phase effort spanning 40-80 weeks (roughly 1-2 years).

### Phase 1: CGA Kernel MVP (8-12 weeks)

**Goals:**
- Implement core `Multivector` class with GA(4,1) algebra
- All basic operations: add, multiply, wedge, inner, dual, norm
- Semantic types: `Point3`, `Line3`, `Plane3`, `Circle3`, `Sphere3`, `Motor3`
- Core operations: `meet`, `join`, `distance`, `project`, `apply`, `compose`

**Deliverables:**
- `cga/` Python package
- 100+ unit tests covering all operations
- Performance benchmarks

**Dependencies:** NumPy, pytest

**Risks:** Getting GA indexing/metric correct is tricky (use existing libraries like `clifford` for validation)

---

### Phase 2: Geometry Integration (6-10 weeks)

**Goals:**
- Integrate CGA types into TiaCAD core
- Map sketches → CGA objects
- Implement `Frame3` / `Motor3` coordinate system model
- Refactor existing geometry code to use CGA backend

**Deliverables:**
- TiaCAD can parse YAML and construct CGA representations
- Internal geometry model uses `Point3`/`Line3`/etc.
- Coordinate frame transformations via motors

**Dependencies:** Phase 1

**Risks:** Large refactor of existing codebase - requires careful migration

---

### Phase 3: Constraint System (10-16 weeks)

**Goals:**
- Define constraint types (coincident, distance, perpendicular, tangent, etc.)
- Implement CGA → residual equation compiler
- Build numerical solver (Gauss-Newton / Levenberg-Marquardt)
- Integrate into parametric DAG

**Deliverables:**
- Constraint solver library
- YAML syntax for constraints
- Example files demonstrating constraint-based design

**Dependencies:** Phase 2

**Risks:** Solver convergence issues, handling degenerate cases

---

### Phase 4: BREP Integration Refactor (6-8 weeks)

**Goals:**
- Refactor `Feature` classes to consume CGA geometry
- Implement `CGAToCadQueryAdapter`
- Ensure all existing TiaCAD features work with CGA backend
- Validate output matches v3.x behavior

**Deliverables:**
- All existing examples render identically
- New CGA-based feature implementations
- Regression test suite

**Dependencies:** Phase 2-3

**Risks:** Subtle differences in numeric precision may cause rendering discrepancies

---

### Phase 5: CAM Subsystem (10-20 weeks)

**Goals:**
- Implement FDM slicer using CGA plane intersections
- Implement CNC contour/pocket toolpaths using CGA offsets
- G-code generation
- Collision detection using CGA

**Deliverables:**
- `tiacad cam slice <file>` CLI command
- `tiacad cam mill <file>` CLI command
- Example FDM/CNC job files

**Dependencies:** Phase 4

**Risks:** CAM is complex domain - may need domain expertise

---

### Phase 6: Optimization & Polish (Ongoing)

**Goals:**
- Performance: sparse multivector representations, SIMD, caching
- Robustness: handle degenerate geometry, numerical stability
- Constraint types: expand to more advanced constraints
- CAM strategies: adaptive slicing, 5-axis milling, etc.

**Deliverables:**
- 10x performance improvements
- Production-ready CAM engine
- Comprehensive documentation

**Dependencies:** All previous phases

---

## 12. Success Metrics

How do we know v5.0 is successful?

### Technical Metrics

1. **Correctness:**
   - All existing v3.x examples render identically
   - CGA operations pass validation against known results
   - Constraint solver converges on standard benchmarks

2. **Performance:**
   - CGA operations < 1ms for simple geometry (points, lines, planes)
   - Constraint solving < 100ms for typical sketches (10-20 constraints)
   - Slicing throughput > 100 layers/second

3. **Capability:**
   - Support 20+ constraint types
   - FDM slicing matches commercial slicers (Cura, PrusaSlicer)
   - CNC toolpaths validated via simulation

### User Experience Metrics

1. **YAML API stability:** No breaking changes to v3.x syntax (or clear migration path)
2. **Error messages:** CGA constraint failures provide actionable feedback
3. **Documentation:** Complete tutorials demonstrating CGA-enabled features

---

## 13. Open Questions & Future Research

### 13.1 CGA Extensions

- **Dual Quaternions vs. Motors:** Are dual quaternions more efficient for SE(3)?
- **Higher-Dimensional CGA:** GA(5,1) or GA(4,2) for additional geometric primitives?
- **Quadric Surfaces:** Native CGA representation of ellipsoids, paraboloids, hyperboloids?

### 13.2 Constraint Solving

- **Global Optimization:** Current solver is local (Gauss-Newton). Explore global methods (genetic algorithms, simulated annealing)?
- **Symbolic Solving:** Can we symbolically solve certain constraint types exactly?
- **Incremental Solving:** Update solution when single parameter changes (warm-start)?

### 13.3 BREP-CGA Bidirectional Mapping

- **CGA → BREP** is clear (current plan)
- **BREP → CGA** is harder: How to extract analytic geometry from arbitrary NURBS surfaces?

### 13.4 Freeform Surfaces

- CGA handles analytic primitives (planes, spheres, cylinders)
- How to represent NURBS, subdivision surfaces, implicit surfaces in CGA?
- Possible approach: Piecewise CGA approximation

---

## 14. Related Work & References

### Conformal Geometric Algebra

- **Dorst, L., Fontijne, D., Mann, S.** (2007). *Geometric Algebra for Computer Science*. Morgan Kaufmann.
- **Hildenbrand, D.** (2013). *Foundations of Geometric Algebra Computing*. Springer.

### CAD & Geometric Modeling

- **Stroud, I.** (2006). *Boundary Representation Modelling Techniques*. Springer.
- **Piegl, L., Tiller, W.** (1997). *The NURBS Book*. Springer.

### Constraint Solving

- **Hoffmann, C. M., Lomonosov, A., Sitharam, M.** (2001). "Finding solvable subsets of constraint graphs." *CP 2001*.
- **Bettig, B., Hoffmann, C. M.** (2011). "Geometric constraint solving in parametric CAD." *J. Computing & Information Science in Engineering*.

### CAM & Toolpath Generation

- **Held, M.** (1991). *On the Computational Geometry of Pocket Machining*. Springer.
- **Lee, Y. S.** (2003). "Admissible tool orientation control of gouging avoidance for 5-axis complex surface machining." *CAD*.

---

## 15. Conclusion

TiaCAD v5.0 with full CGA integration represents a paradigm shift: **mathematical elegance meets practical CAD/CAM**.

**Core Benefits:**
1. **Unified Geometry:** One algebra for all primitives
2. **Exact Operations:** Analytic intersections, projections, distances
3. **Natural Constraints:** Geometric conditions → algebraic equations
4. **Cleaner Code:** Eliminate special cases, simplify logic
5. **CAM Integration:** Slicing and toolpaths use same geometric foundation

**Challenges:**
- Large refactor of existing codebase
- CGA has learning curve (both for developers and users)
- Performance optimization needed for production use
- BREP integration still required for solid modeling

**Timeline:** 40-80 weeks (1-2 years) for full implementation across 6 phases.

**Next Steps:**
1. Validate CGA approach with prototype (Phase 1 spike: 2-4 weeks)
2. Get stakeholder buy-in on architecture
3. Begin Phase 1 implementation

---

## Appendix A: CGA Cheat Sheet

| Concept | CGA Representation | Grade |
|---------|-------------------|-------|
| Point | Null vector `P = x₁e₁ + x₂e₂ + x₃e₃ + ½(x·x)e∞ + e₀` | 1 |
| Line | Trivector `L = P₁ ∧ P₂ ∧ e∞` | 3 |
| Plane (IPNS) | Vector `π = n₁e₁ + n₂e₂ + n₃e₃ + d·e∞` | 1 |
| Plane (OPNS) | Quadvector `π = P₁ ∧ P₂ ∧ P₃ ∧ e∞` | 4 |
| Circle | Trivector `C = P₁ ∧ P₂ ∧ P₃` | 3 |
| Sphere | Quadvector `S = P₁ ∧ P₂ ∧ P₃ ∧ P₄` | 4 |
| Motor | Even multivector `M = exp(½B)` | 0+2+4 |

| Operation | CGA Formula | Meaning |
|-----------|-------------|---------|
| Intersection | `A ∧* B` (dual meet) | Smallest object containing both |
| Span | `A ∧ B` (meet) | Largest object in both |
| Distance | `\|2(P₁·P₂)\|^{1/2}` | Euclidean distance |
| Transform | `M·X·M̃` | Apply motor M to object X |
| Reflect | `-π·X·π⁻¹` | Reflect X across plane π |

---

## Appendix B: Python Package Structure

```
tiacad_core/
├── cga/                      # NEW: CGA kernel
│   ├── __init__.py
│   ├── multivector.py       # Core Multivector class
│   ├── point.py             # Point3
│   ├── line.py              # Line3
│   ├── plane.py             # Plane3
│   ├── circle.py            # Circle3
│   ├── sphere.py            # Sphere3
│   ├── motor.py             # Motor3
│   ├── operations.py        # meet, join, distance, project, offset
│   └── utils.py             # CGA basis, metric, helpers
│
├── constraints/             # NEW: Constraint system
│   ├── __init__.py
│   ├── constraint.py        # Base Constraint class
│   ├── types.py             # Coincident, Distance, Perpendicular, etc.
│   ├── solver.py            # Gauss-Newton / LM solver
│   └── residuals.py         # CGA → scalar residual compilers
│
├── geometry/                # REFACTORED: Now CGA-backed
│   ├── sketch.py            # Sketch uses CGA
│   ├── feature.py           # Features consume CGA
│   ├── frame.py             # Frame3 with Motor3
│   ├── cadquery_adapter.py  # CGA → CadQuery mapping
│   └── ...
│
├── cam/                     # NEW: CAM subsystem
│   ├── __init__.py
│   ├── slicer.py            # FDM slicing
│   ├── toolpath.py          # CNC toolpath generation
│   ├── gcode.py             # G-code export
│   └── collision.py         # CGA-based collision detection
│
├── dag/                     # NEW: Parametric DAG
│   ├── __init__.py
│   ├── node.py              # DAGNode base class
│   ├── parameter.py         # ParameterNode
│   ├── expression.py        # ExpressionNode
│   ├── geometry.py          # CGAObjectNode
│   └── recompute.py         # Topological sort & recomputation
│
├── parser/                  # EXISTING: Extended for constraints
│   ├── constraint_builder.py  # NEW
│   └── ...
│
└── ... (existing modules)
```

---

**END OF SPECIFICATION**

---

## Document Metadata

- **Total Length:** ~12,000 words
- **Sections:** 15 main + 2 appendices
- **Estimated Reading Time:** 45-60 minutes
- **Implementation Complexity:** Very High
- **Dependencies:** NumPy, CadQuery, OCCT, JAX (for autodiff), pytest
- **License:** (To be determined - likely Apache 2.0 to match SIL ecosystem)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-01 | 1.0 | Initial draft from ChatGPT conversation |

---

**Questions? Feedback?**
Open an issue or discussion in the TiaCAD repository.
