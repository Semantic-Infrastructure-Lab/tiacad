Perfect — that gives me a *solid anchor point*.
Your `YAML_REFERENCE.md` v0.2.0 is clear, production-ready, and focuses on the **Phase 2 feature set** — primitives, transforms, booleans, patterns, and finishes — but it’s deliberately *flat*: no concept of orientation frames, references, or constraints yet.

What we’ve been discussing (named points/faces, frames, units, constraints, includes) is the **natural Phase 3 → Phase 4 evolution** of that same spec.

Here’s how we can extend what you have without breaking backward compatibility.

---

# 🧩 TiaCAD YAML v2.1 Proposed Addenda

*(to layer on top of your existing `YAML_REFERENCE.md` 0.2.0)*

---

## 1  New Top-Level Keys

| Key                          | Purpose                                        | Status        |
| ---------------------------- | ---------------------------------------------- | ------------- |
| `references:`                | Declare named points/faces/axes inside parts   | 🆕            |
| `frames:`                    | Define reusable coordinate systems             | 🆕            |
| `constraints:`               | Express mating & alignment rules between parts | 🆕            |
| `units:`                     | Specify default measurement units              | 🆕            |
| `include:` / `use_template:` | Modular file composition                       | 🆕 (optional) |

---

## 2  References — Named Geometry

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
      axes:
        vertical: { from: [0, 0, 0], to: [0, 0, 1] }
```

**Selector syntax** follows existing CadQuery strings.
Each reference resolves to:

```json
{ "origin": [x,y,z], "orientation": [nx,ny,nz] }
```

All primitives automatically expose canonical names:
`origin`, `center`, `face_top`, `face_bottom`, `axis_x/y/z`.

---

## 3  Frames — Local Coordinate Systems

```yaml
frames:
  plate_frame:
    origin: base_plate:points:center
    z_axis: base_plate:axes:vertical
    x_axis: [1, 0, 0]
```

Used anywhere an orientation is needed:

```yaml
operations:
  rotate_around_plate:
    type: transform
    input: arm
    transforms:
      - rotate:
          frame: plate_frame
          angle: 90
```

---

## 4  Reference-Based Transforms

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

**Valid keys:**
`to_point`, `to_face`, `to_axis`, `orientation`, `offset`.

---

## 5  Constraints — Declarative Mating

```yaml
constraints:
  mount_alignment:
    type: flush
    parts: [bracket, base_plate]
    refs: [bracket:faces:bottom, base_plate:faces:mount]

  shaft_in_bearing:
    type: coaxial
    parts: [shaft, bearing]
    refs: [shaft:axes:z, bearing:axes:z]
    offset: 2
```

| Type            | Description             |
| --------------- | ----------------------- |
| `flush`         | Make faces coplanar     |
| `coaxial`       | Align two axes          |
| `offset`        | Maintain distance       |
| `angle`         | Set angular relation    |
| `point_on_face` | Place a point on a face |

Future solver = symbolic (SymPy) or numeric (pybullet).

---

## 6  Units

```yaml
units: mm     # default
parameters:
  width: 100 mm
  bolt_dia: 0.25 in
```

Handled via `pint`.
Mixed units resolve to the declared system automatically.

---

## 7  Includes / Templates

```yaml
include:
  - ./common/bolts.yaml

use_template:
  from: bolt_array
  with:
    count: 6
    spacing: 15
```

Encourages modular libraries of parametric features.

---

## 8  Validation & Schema Notes

* Extend JSON Schema to recognise new sections (`references`, `constraints`, etc.).
* Add a `schema_version: 2.1` header.
* Older files remain valid.

---

## 9  Example — Reference-Aware Mount Plate

```yaml
schema_version: 2.1
units: mm

parts:
  plate:
    primitive: box
    size: [100, 60, 8]
    references:
      faces:
        top: { selector: ">Z" }
        bottom: { selector: "<Z" }
      points:
        center: { selector: "origin" }

  hole:
    primitive: cylinder
    radius: 3
    height: 12
    references:
      axes:
        axis: { from:[0,0,0], to:[0,0,1] }

constraints:
  hole_to_plate:
    type: point_on_face
    parts: [hole, plate]
    refs: [hole:points:base, plate:faces:top]
  hole_axis_align:
    type: flush
    parts: [hole, plate]
    refs: [hole:axes:axis, plate:axes:z]

operations:
  cut_hole:
    type: boolean
    operation: difference
    base: plate
    subtract: [hole]
```

---

## 10  Implementation Checklist

| Step | Module                     | Action                                                    |
| ---- | -------------------------- | --------------------------------------------------------- |
| 1    | `geometry/base.py`         | Add `NamedReference` types (PointRef, FaceRef, AxisRef)   |
| 2    | `parser/point_resolver.py` | Upgrade → `spatial_resolver.py` to parse `part:type:name` |
| 3    | `operations_builder.py`    | Support reference-based origins & frames                  |
| 4    | `schema_validator.py`      | Extend JSON Schema for new sections                       |
| 5    | `cli.py` / `validate`      | Warn on undefined reference names                         |

---

## 11  Backward Compatibility

* All existing 0.2.0 YAMLs → still valid.
* New features are **opt-in**.
* `schema_version` or presence of `references` section activates v2 parsing.

---

## 12  Phase 3 Goal

Once implemented, users will be able to describe *intent-driven, constraint-aware* designs:

```yaml
align:
  part: "arm"
  to_face: "base_plate:faces:mount"
  orientation: "normal"
  offset: 10
```

instead of raw coordinates — achieving human-readable, mechanically meaningful YAML.

---

Would you like me to turn this draft into a proper **`YAML_REFERENCE_v2.1.md`** file (with the same formatting style, tables, and example density as your current 0.2.0 doc)?
That way you’ll have both versions side-by-side in `docs/` (`YAML_REFERENCE.md` → v0.2.0, `YAML_REFERENCE_v2.1.md` → proposed Phase 3).

