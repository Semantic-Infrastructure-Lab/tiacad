# 🧭 TiaCAD YAML Specification — v2.0 Proposal

### *Enhancements for Named Geometry, Orientation, and Composability*

---

## 📜 1. Overview

TiaCAD YAML currently describes parts and operations using *absolute coordinates* and *flat primitives*.
This proposal introduces a structured, declarative extension that allows:

* **Named geometric references** (`points`, `faces`, `edges`, `axes`)
* **Orientation-aware transforms** (align, mate, attach, offset)
* **Reference-based relationships between parts**
* **Units, constraints, and reusable definitions**

These upgrades make TiaCAD YAML expressive enough for **parametric, constraint-based** modeling — without breaking existing files.

---

## 🧩 2. Versioning & Backward Compatibility

```yaml
schema_version: 2.0
```

* v1.x files remain valid.
* v2 adds optional new sections: `references`, `constraints`, `units`, `frames`.

---

## 📦 3. Core Additions

### 🧱 3.1 Named Geometry References

Each `part` can define *named points, edges, faces, and axes*.
These may be explicitly declared, derived via selectors, or auto-generated.

```yaml
parts:
  base_plate:
    primitive: box
    size: [100, 60, 10]
    references:
      points:
        center: { selector: "origin" }
        top_center: { selector: "face >Z", mode: "center" }
      faces:
        mount: { selector: ">Z" }
        bottom: { selector: "<Z" }
      axes:
        vertical: { from: [0,0,0], to: [0,0,1] }
```

#### **Rules:**

* Selectors match CadQuery-style face/edge filters.
* Each reference gets both:

  * **Position** (XYZ)
  * **Orientation** (local normal or axis vector)

> 💡 Every primitive automatically defines canonical references (e.g., `center`, `origin`, `axis_z`, `face_top`).

---

### 🧭 3.2 Orientation Frames

A frame defines a **local coordinate system** (origin + 3 orthogonal axes).

```yaml
frames:
  plate_frame:
    origin: base_plate:points:center
    z_axis: base_plate:axes:vertical
    x_axis: [1, 0, 0]
```

You can reference frames for transforms or assembly operations:

```yaml
operations:
  rotate:
    around: plate_frame
    by: 90
```

---

### 🔗 3.3 Reference-Based Transforms

Transforms now support **reference-based origins and alignments** in addition to numeric coordinates.

```yaml
operations:
  align_bracket:
    type: transform
    input: bracket
    transforms:
      - align:
          to_face: base_plate:faces:mount
          orientation: normal
          offset: 5
```

#### Valid keys:

| Key           | Meaning                                         |
| ------------- | ----------------------------------------------- |
| `to_point`    | Align part origin to another part’s named point |
| `to_face`     | Align part to a specific face                   |
| `to_axis`     | Align rotation axis to another’s                |
| `orientation` | Axis to align (`normal`, `x`, `y`, `z`)         |
| `offset`      | Distance offset along aligned axis              |

---

### 🧲 3.4 Mating & Constraints

Adds a declarative layer for **geometric relationships** between parts.

```yaml
constraints:
  mate_shaft_to_bearing:
    type: coaxial
    parts: [shaft, bearing]
    refs: [shaft:axes:z_axis, bearing:axes:z_axis]
    offset: 2

  align_mount_face:
    type: flush
    parts: [bracket, base_plate]
    refs: [bracket:faces:bottom, base_plate:faces:mount]
```

Constraint types:

| Type             | Description                                         |
| ---------------- | --------------------------------------------------- |
| `coaxial`        | Align two axes (e.g., shaft in bearing)             |
| `flush`          | Align faces with same orientation                   |
| `offset`         | Maintain distance between faces                     |
| `angle`          | Maintain angular relationship between faces or axes |
| `point_on_face`  | Place a point onto a target face                    |
| `point_distance` | Maintain distance between points                    |

These can be *solved* by a constraint solver (e.g., symbolic or numeric).

---

### 🧮 3.5 Units

Optional units can be added to all numeric values using SI or imperial notation.

```yaml
parameters:
  plate_width: 100 mm
  hole_diameter: 0.25 in
```

Internally handled by the [`pint`](https://pint.readthedocs.io/) library for consistent unit math.

---

### 🧠 3.6 Reusable Templates & Includes

Add the ability to reuse part or operation definitions.

```yaml
include:
  - ./common/bolts.yaml
  - ./templates/bracket.yaml
```

Template example:

```yaml
templates:
  hole_array:
    parameters: { count: 4, spacing: 20 }
    operations:
      pattern:
        input: hole
        type: linear
        direction: [1, 0, 0]
        count: ${count}
        spacing: ${spacing}
```

Then use it:

```yaml
use_template:
  from: hole_array
  with:
    count: 6
    spacing: 15
```

---

## 🧾 4. Full Example (YAML v2)

```yaml
schema_version: 2.0

parameters:
  thickness: 8 mm
  bolt_diameter: 5 mm
  plate_w: 100 mm
  plate_d: 60 mm

parts:
  base_plate:
    primitive: box
    size: [${plate_w}, ${plate_d}, ${thickness}]
    references:
      faces:
        top: { selector: ">Z" }
        bottom: { selector: "<Z" }
      points:
        center: { selector: "origin" }

  bolt_hole:
    primitive: cylinder
    radius: ${bolt_diameter / 2}
    height: ${thickness * 1.5}
    origin: base
    references:
      axes:
        axis: { from: [0,0,0], to: [0,0,1] }

constraints:
  mount_hole_center:
    type: point_on_face
    parts: [bolt_hole, base_plate]
    refs: [bolt_hole:points:base, base_plate:faces:top]
    offset: 0

  hole_alignment:
    type: flush
    parts: [bolt_hole, base_plate]
    refs: [bolt_hole:axes:axis, base_plate:axes:z_axis]

operations:
  cut_hole:
    type: boolean
    op: difference
    inputs: [base_plate, bolt_hole]
```

---

## 🔧 5. Implementation Notes

* `PointResolver` → becomes `SpatialResolver`, handling `part:entity_type:name` syntax.
* Add `Frame` and `Reference` dataclasses:

  ```python
  class FaceRef:
      origin: np.ndarray
      normal: np.ndarray
  class AxisRef:
      origin: np.ndarray
      direction: np.ndarray
  class Frame:
      origin, x, y, z: np.ndarray
  ```
* Update `OperationsBuilder` and `TransformTracker` to support frame-based transforms.
* Extend JSON Schema for YAML validation.

---

## 🚀 6. Benefits Summary

| Feature                | Enables                                   |
| ---------------------- | ----------------------------------------- |
| Named references       | Contextual modeling (“align to top face”) |
| Frames                 | Arbitrary local orientations              |
| Constraints            | Parametric assemblies                     |
| Units                  | Dimensional consistency                   |
| Templates/includes     | Scalable model composition                |
| Backward compatibility | Legacy YAML remains valid                 |

---

## ✅ 7. Next Steps (Recommended Implementation Order)

1. **Implement named references + frame extraction**
2. **Integrate `SpatialResolver` + frame-based transforms**
3. **Add constraints YAML schema & basic solver**
4. **Support units via `pint`**
5. **Introduce templates/includes loader**

