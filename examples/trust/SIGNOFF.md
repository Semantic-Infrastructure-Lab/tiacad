# TiaCAD Trust Gallery Sign-off

Auto-refreshed (contract/render columns) at commit `e78d3d7` by `scripts/trust_signoff.py`. The Reviewed/Reviewer/Note columns are hand-maintained — re-running the script never overwrites them; a new scenario appears as PENDING until someone actually looks at its render.

Render the gallery for review with:
```
python scripts/trust_render.py --gallery
```
then open `trust_output/gallery.html` (or the individual PNGs under `trust_output/`).

| Scenario | Contract | Reviewed | Reviewer | Note |
|---|---|---|---|---|
| `boolean_intersect` | PASS | 2026-07-18 | TIA (AI review) | Small cube in center, all 4 views square — matches description. |
| `boolean_subtract` | PASS | 2026-07-18 | TIA (AI review) | Centered round hole through plate, no offset — matches description. |
| `boolean_union` | PASS | 2026-07-18 | TIA (AI review) | Plus/cross shape in top view, solid (no notch) — matches description. |
| `box_basic` | PASS | 2026-07-18 | TIA (AI review) | Axis mapping and proportions correct (X widest, Z shortest). |
| `chamfer_basic` | PASS | 2026-07-18 | TIA (AI review) | All 12 edges show flat 45° bevels, octagonal top view — matches description. |
| `circular_pattern` | PASS | 2026-07-18 | TIA (AI review) | 6 evenly-spaced bolt holes + 1 center hole, correct 60° spacing. |
| `cone_basic` | PASS | 2026-07-18 | TIA (AI review) | Triangle profile, circular base, apex at top — matches description. |
| `cylinder_basic` | PASS | 2026-07-18 | TIA (AI review) | Taller-than-wide proportions, no flat edges — matches description. |
| `cylinder_on_plate` | no expect: block | 2026-07-18 | TIA (AI review) | Cylinder centered on plate, flush contact, no offset — matches description. Multi-part scene, no single-solid expect: target. |
| `fillet_basic` | PASS | 2026-07-18 | TIA (AI review) | All 12 edges smooth arcs, no sharp corners — matches description. |
| `hull_spheres` | PASS | 2026-07-18 | TIA (AI review) | Rounded triangular blob, no flat gaps between spheres — matches description. sphere_c's Y translate corrected to the equilateral-exact 34.641016151377544 (was 34, a placeholder). Render still shows faceted (non-smooth) shading — the "Input points appear coplanar" warning is inherent to all three sphere centers sharing Z=0, not the Y-precision issue, so it persists after the fix; cosmetic tessellation artifact, not a topology defect (watertight, 1 solid). |
| `linear_pattern` | no expect: block | 2026-07-18 | TIA (AI review) | 5 evenly-spaced, distinctly colored boxes in a row — matches description. Multi-instance pattern, no single mergeable part. |
| `loft_rect_to_circle` | PASS | 2026-07-18 | TIA (AI review) | Trapezoid profile, square-to-circle corner rounding visible — matches description. |
| `pcb_standoff_assembly` | no expect: block | 2026-07-18 | TIA (AI review) | **Bug found and fixed this session**: plate/PCB `height`/`depth` params were swapped, rendering as a vertical wall instead of a flat plate (see KNOWN_LIMITATIONS.md #13). Re-rendered after fix — now shows the documented 3-layer stack (plate → standoffs → PCB). Multi-part scene, no single-solid expect: target. |
| `revolve_180` | PASS | 2026-07-18 | TIA (AI review) | Half-cylinder, flat face on symmetry plane — matches description. |
| `revolve_90` | PASS | 2026-07-18 | TIA (AI review) | Quarter-cylinder wedge, two flat faces at 90° — matches description. |
| `revolve_basic` | PASS | 2026-07-18 | TIA (AI review) | Symmetric I-beam/spool silhouette — matches description. |
| `revolve_x_axis` | PASS | 2026-07-18 | TIA (AI review) | Cylinder lying on its side, axis along X — matches description. |
| `revolve_y_axis` | PASS | 2026-07-18 | TIA (AI review) | Cylinder standing on end, axis along Y — matches description. |
| `side_by_side` | no expect: block | 2026-07-18 | TIA (AI review) | Two equal boxes with visible 20mm gap, same height — matches description. Multi-part scene, no single-solid expect: target. |
| `sphere_basic` | PASS | 2026-07-18 | TIA (AI review) | All 4 views circular, no flat edges — matches description. |
| `stacked_boxes` | no expect: block | 2026-07-18 | TIA (AI review) | Flush step profile, no gap/overlap, blue centered inside red border — matches description. Multi-part scene, no single-solid expect: target. |
| `sweep_basic` | PASS | 2026-07-18 | TIA (AI review) | L-shaped pipe, 90° corner visible, consistent thickness — matches description. |
| `three_part_assembly` | no expect: block | 2026-07-18 | TIA (AI review) | Symmetric posts on plate ends, all 3 parts distinct colors — matches description. Multi-part scene, no single-solid expect: target. |
