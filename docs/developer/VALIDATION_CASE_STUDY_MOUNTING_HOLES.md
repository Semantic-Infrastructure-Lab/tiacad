---
title: "Validation Case Study — The Mounting Holes That Weren't"
type: analysis
beth_topics:
  - tiacad
  - validation
  - correctness
  - boolean
  - trust-renderer
  - case-study
---

# Validation Case Study — The Mounting Holes That Weren't

A real defect found in a committed example (`examples/awesome_guitar_hanger.yaml`),
used here as the canonical worked example for the ideas in
[MODEL_VALIDATION.md](MODEL_VALIDATION.md) and [AI_DEBUG_WORKFLOW.md](AI_DEBUG_WORKFLOW.md).

**Note:** test counts below (1,599) are a point-in-time snapshot from when this
bug was found — the suite has since grown to 1,926 tests. The finding and
methodology are unaffected; don't read 1,599 as the current count.

**One-line summary:** the guitar hanger's four screw-hole cuts subtract from empty
air — the mounting plate ships with no holes, the `difference` operations remove
(almost) nothing, and **1,599 passing tests never noticed.**

---

## The Bug

The hanger is meant to bolt to a wall through two countersunk screw holes in the
mounting plate. The final part has none. The `difference` operation runs, but its
subtract tools do not intersect the plate, so no material is removed.

Measured evidence (all values in mm; the plate occupies `Z[-7.5, 7.5]`, `Y[-45, 45]`):

| Cutout | Built position | Plate overlap | Verdict |
|---|---|---|---|
| `left_screw_shaft` | `Z[16.5, 33.5]` | plate top is `Z=7.5` | ❌ floats 9 mm above the plate |
| `right_screw_shaft` | `Z[16.5, 33.5]` | same | ❌ misses the plate |
| `left_countersink` | `Y[65, 75]` | plate front is `Y=45` | ❌ 20–30 mm past the front edge |
| `right_countersink` | `Y[65, 75]` | same | ❌ floats off in space |

---

## Root Cause: An Axis-Mapping Mental-Model Error

TiaCAD's `box` primitive maps parameters to axes as **`width`→X, `height`→Z,
`depth`→Y**. The plate is defined:

```yaml
mounting_plate:
  primitive: box
  parameters:
    width:  '${plate_width}'      # 120 → X
    height: '${plate_thickness}'  # 15  → Z   (the thin thickness)
    depth:  '${plate_height}'     # 90  → Y
```

So the parameter *named* `plate_height` (90) becomes the plate's **Y** extent, and
`plate_thickness` (15) becomes the **Z** (thickness) extent. The plate is
`120(X) × 90(Y) × 15-thin(Z)`.

But the screw references were written as if the plate's 90 mm "height" ran **up the
Z axis**:

```yaml
left_screw_pos:
  from: mounting_plate.center
  offset: ['${-screw_spacing / 2}', 0, '${plate_height/2 - screw_offset_from_top}']
  #        [        -35          ,  0,               25                          ]
```

The vertical-position value **25** was placed in the **Z** slot — but Z is the
15 mm *thickness*, so the shaft (a Z-axis cylinder) lands at `Z[16.5, 33.5]`,
floating above the plate. The same error puts the countersinks at `Y[65, 75]`,
past the front edge (compounded by anchoring to `face_front`, a Y-face, which the
same confusion selected).

The tell: **a parameter named `_height` was routed to the Y axis, but every
consumer assumed it meant Z.** Naming implied one axis; the primitive assigned
another. Nothing checked that the screw actually reached the plate.

---

## The Fix

**Shafts (verified, applied):** swap the Y and Z offset components so the vertical value
positions the hole *along the plate face* (Y) and the through-axis (Z) stays
centered in the thickness:

```yaml
offset: ['${-screw_spacing / 2}', '${plate_height/2 - screw_offset_from_top}', 0]
#         [        -35          ,               25                          , 0 ]
```

Confirmed three independent ways:

- **Geometry:** shafts now span `Z[-8.5, 8.5]` → pierce the plate's `Z[-7.5, 7.5]`.
- **Volume:** final volume drops by **589 mm³ = exactly 2 × π·2.5²·15** — two clean
  through-holes, not a coincidence.
- **Render:** the X-Ray panel shows the shafts embedded *through* the plate instead
  of floating above it.

**Countersinks (verified, applied):** retarget from `mounting_plate.face_front` to
`mounting_plate.face_top` (a Z-face). Face anchors don't share one global X/Y/Z offset
convention — each face gets its own right-handed tangent frame from
`Frame.from_normal()` (`tiacad_core/spatial_references.py`), built as
`cross(normal, world_Z_or_X)`. For `face_top` that frame maps `offset[0]`→world Y,
`offset[1]`→−world X, `offset[2]`→world Z, so landing on the same X/Y as the shaft
while recessing into the surface takes:

```yaml
offset: ['${plate_height/2 - screw_offset_from_top}', '${-screw_spacing / 2}', '${-countersink_depth / 2}']
#         [               25                        ,         -35           ,             -1.5           ]
# (left; right flips the middle component's sign)
```

Confirmed with `Part.get_bounds()`: both countersinks now center on the same X/Y as
their shafts and span `Z[4, 8]`, straddling the plate's top surface at `Z=7.5`. Final
volume drops a further 412.4 mm³ (245,319.6 mm³ original → 244,318.2 mm³ fully fixed).

**Broader:** the plate lies flat (thin in Z) rather than standing vertical against a
wall — the same axis confusion likely affects the hanger's intended orientation.
That is a larger redesign, separate from the (now fixed) hole bug.

---

## How It Was Found — and What That Teaches

The causal chain, told honestly:

1. A **picture** (the per-component decomposed trust render) prompted the question
   "what are those nubs?" → then "can we see the mounting holes?"
2. **Numbers** (part bounding boxes) *proved* the bug: shaft `Z[16.5, 33.5]` vs
   plate `Z[-7.5, 7.5]`, no overlap.
3. A **volume delta** confirmed the fix with closed-form math.

Three lessons fall out, and they should shape how validation evolves:

### 1. Numbers were the oracle; the picture was only the trigger
The render did not *prove* anything — it created suspicion. The proof was numeric
(bounding-box overlap, volume delta). Reversing this order — trusting a render to
confirm correctness — is exactly what [MODEL_VALIDATION.md](MODEL_VALIDATION.md)
warns against.

### 2. Noticing an *absent* feature is the weakest possible oracle
A solid plate with no holes looks like a perfectly correct plate. Both the flat
single-color render *and* the decomposed render were reviewed without the missing
holes being noticed, until numbers were pulled. Human/AI visual review is good at
"this looks wrong" and bad at "something that should be here is missing." Do not
rely on it for presence/absence guarantees.

### 3. The whole bug class is auto-detectable — no picture, no per-model authoring
A `difference` that removes 0 mm³, or a `union` input that contributes 0 mm³, is
almost always a bug. TiaCAD already builds every part, so it can check this on
every model, in CI, with no contract to write. See "Boolean-effect assertions"
in [MODEL_VALIDATION.md](MODEL_VALIDATION.md#best-next-improvements) — the single
highest-ROI improvement, and the one that would have turned this lucky catch into a
CI failure nobody had to notice.

---

## Why 1,599 Tests Missed It

The example has geometric contracts (`test_correctness/test_example_contracts.py`,
`TestGuitarHanger*`), and they pass. They assert overall bounding dimensions and
volume *ranges* — not that the mounting holes exist or that each subtract tool
actually removes material. A boolean that silently left the solid untouched sits
comfortably inside a volume *range* check. This is the "correctness gap" and the
"boolean that silently failed" failure mode from
[TESTING_GUIDE.md](TESTING_GUIDE.md#correctness-gap--what-we-know), demonstrated on
a real committed model.

---

## The Principle

> Pictures generate suspicion. Numbers prove. The system should compute the numbers
> automatically, on every build, instead of waiting for a human to get suspicious.

We did the "numbers prove" step well, by hand, once we were suspicious. The
order-of-magnitude improvement is moving that from *ad-hoc and human-triggered* to
*automatic and every-build* — starting with boolean-effect assertions.
