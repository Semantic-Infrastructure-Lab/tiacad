# 🧭 Named Geometry References — the Missing “Spatial Language” in TiaCAD

---

## ❌ Current Situation

You **partially** have the beginnings of this in:

* `OperationsBuilder._apply_translate` and `_apply_rotate`, which use `PointResolver` and `named_points`.
* Some YAML patterns can refer to points via strings.

However, this is:

* **Limited to points only**, and
* **Purely positional**, not orientational — no notion of local axes or frames,
* **Ephemeral** — references don’t persist across parts or operations.

That means you can *translate or rotate relative to a named point*,
but you can’t say things like:

```yaml
align:
  part: "bracket"
  to_face: "base.mount_face"
  orientation: "normal"
  offset: 10
```

or

```yaml
mate:
  partA: "shaft"
  partB: "bearing"
  at: "shaft.axis"
  align_to: "bearing.hole_axis"
```

---

## 💡 Why It Matters

Adding **named geometric references** unlocks four major capabilities:

| Capability                | Description                                                                                                           |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Composability**         | Build higher-level assemblies without guessing coordinates — just refer to `face:left` or `point:center`.             |
| **Orientability**         | Define local coordinate systems — “axis of this hole”, “normal of that face” — for arbitrary rotations or alignments. |
| **Constraint Solving**    | Use named references as targets for `mate`, `align`, `flush`, or `offset` operations.                                 |
| **Clarity & Reusability** | YAML stays readable and declarative instead of coordinate-heavy and fragile.                                          |

---

## 🧠 Concept: “Named Feature Graph”

Each **Part** gains a lightweight registry of named geometric entities:

```python
part.named_points = {
  "center": (0, 0, 0),
  "top": (0, 0, 50)
}

part.named_axes = {
  "z_axis": ((0, 0, 0), (0, 0, 1))
}

part.named_faces = {
  "mount_face": FaceRef(normal=(0,0,1), origin=(0,0,50))
}
```

Each reference defines both **position** and **orientation**,
so operations can align or attach relative to those.

These references can come from:

* Explicit YAML declarations:

  ```yaml
  faces:
    mount: { selector: ">Z" }
    left: { selector: "<X" }
  points:
    base_center: { selector: "origin" }
  ```
* Or auto-generated (e.g. every primitive defines its canonical faces).

---

## 🧩 Implementation Pathway

### 1. **Extend GeometryBackend**

Add APIs for reference extraction:

```python
def get_named_points(self, geom) -> Dict[str, Tuple[float,float,float]]
def get_named_faces(self, geom) -> Dict[str, FaceReference]
def get_named_edges(self, geom) -> Dict[str, EdgeReference]
```

Each returns orientation and centroid data — can use CadQuery’s `faces()` / `edges()` with bounding boxes and normals.

---

### 2. **Enhance Part Metadata**

In `Part`, add:

```python
class Part:
    ...
    named_points: Dict[str, tuple]
    named_faces: Dict[str, FaceRef]
    named_axes: Dict[str, AxisRef]
```

Include these in YAML export so users can introspect or reference by name later.

---

### 3. **Upgrade PointResolver**

Replace with a unified **SpatialResolver**:

* Accepts inputs like `"part1:face:top"` or `"part1:axis:z_axis"`.
* Resolves to both position and orientation (as a local coordinate frame).
* Enables orientation-based transforms, e.g. “align X-axis of part A with Y-axis of part B.”

---

### 4. **Update OperationsBuilder**

Allow any transform, mate, or boolean operation to specify **reference-based** origins:

```yaml
rotate:
  around: "shaft.axis"
  by: 45
```

or:

```yaml
translate:
  to_face: "base.mount_face"
  align: "normal"
  offset: 5
```

---

### 5. **Optional — Orientation Math Layer**

Internally, define a small utility for 3D frames and transforms:

```python
class Frame:
    origin: np.array
    x: np.array
    y: np.array
    z: np.array
```

You can then easily compute relative transforms, alignments, and rotations.

Use `numpy` or `scipy.spatial.transform.Rotation` for these calculations.

---

## 🔧 Benefits

| Domain                  | What It Enables                                                |
| ----------------------- | -------------------------------------------------------------- |
| **Assemblies**          | Constraint-based mating (aligning faces, axes, edges)          |
| **Procedural modeling** | Build parts relative to others (no absolute coordinates)       |
| **Clarity**             | YAML reads like design intent (“mount bracket to top of base”) |
| **Future GUI**          | Picking and naming geometry interactively                      |

---

## 🚀 Summary: What to Add

| Gap                              | Current   | Needed                                |
| -------------------------------- | --------- | ------------------------------------- |
| Named points                     | ✅ Partial | Add persistence + orientations        |
| Named edges                      | ❌         | Extract via selector, store direction |
| Named faces                      | ❌         | Extract + store normal + origin       |
| Reference-based transforms       | ✅ Limited | Extend to full coordinate frame       |
| Cross-part spatial relationships | ❌         | Add `SpatialResolver` + constraints   |

---

## ✨ Outcome

With this system, TiaCAD graduates from a **“coordinate-based parametric generator”**
to a **“reference-based geometric modeler”** — a massive conceptual leap.

You’ll be able to express intent like:

```yaml
align:
  part: "gear"
  to_face: "motor_shaft.front"
  orientation: "coaxial"
  offset: 2
```

instead of:

```yaml
translate:
  offset: [0, 0, 42]
```

That difference — *intent vs coordinates* — is what distinguishes real CAD from mere 3D scripting.

