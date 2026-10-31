---
title: "Sticker drawer: status and next steps"
type: reference
beth_topics:
  - tiacad
  - sticker-drawer
  - sticker-tray
  - 3d-printing
  - print-cost
---

# Sticker drawer: status and next steps

Status as of 2026-10-30. The worked example is `sticker_tray.yaml`: single-sticker trays for a 15 in x 19.5 in drawer. Open work is tracked as TCAD-7 and TCAD-15 (`tt show TCAD-15`).

**The default in `sticker_tray.yaml` is now the 6 x 6 grid** (6 columns across, 6 trays per column, 36 trays). Layouts A and B are still available through `--set` overrides (table below); a plain `./tiacad build` builds the 6 x 6 tray.

## Drawer and layouts

Drawer: 15 in front-to-back (381 mm) by 19.5 in wide (495 mm). Drawer height is not recorded. Trays are 50.8 mm (2 in) tall. Gaps of 3 mm go between columns; trays in a column sit end to end.

| Layout | Overrides | Outside W x L (mm) | Interior W x L (mm) | Columns x per column | Total | Notes |
|---|---|---|---|---|---|---|
| 6 x 6 (default) | none (`tray_w` 78.5, `slot_l` 59.2, `wall` 2.0, `floor` 2.0) | 78.5 x 63.2 | 74.5 x 59.2 | 6 x 6 | 36 trays | 492 of 495 mm across, 379.2 of 381 mm deep. Interior is 2.93 x 2.33 in: only for stickers narrower than about 2.9 in |
| B | `--set tray_w=94 --set slot_l=90.6` | 94 x 94.6 at wall 2.0 | 90 x 90.6 | 5 x 4 | 20 trays | Holds stickers up to a 3.5 in (88.9 mm) diagonal. Wall 1.6 (the file's old default) printed flimsy |
| A | `--set tray_w=94 --set slot_l=71.6 --set wall=1.6 --set floor=1.2` | 94 x 74.8 | 90.8 x 71.6 | 5 x 5 | 25 trays | Judged not useful |

Tray length is `slot_l + 2 x wall`, so wall thickness spends drawer depth. The 6-per-column ceiling is 63.5 mm (381 / 6) with no gaps; layout B's ceiling is wall 2.3 mm (4 x 95.2 = 380.8 mm).

## Print history

| Print | Result |
|---|---|
| TRAYS_15MM (full size, 0.2 mm) | Floor only printed; cause never found |
| MINI_TRAYS (1/3 scale) | Fine |
| MID_TRAYS (2/3 scale, 1.2 mm walls, 0.28 mm, 5% rectilinear) | Looked good, walls thin, ramp felt wimpy |
| FULL_AB (wall 1.6, 0.28 mm, 10% gyroid, 4 perimeters) | Printed. Walls flimsy on every tray, some layer adhesion issues (Scott, 2026-10-19) |
| TRAYS_6X6_P1 (6 trays, wall 2.0, 0.20 mm, 5 perimeters, 10 bottom / 8 top, 215 C) | Printed 2026-10-26. All 6 trays good and sturdy, floor far stronger than needed, fine-hair stringing across the inside of each tray. Actual time matched the slicer estimate exactly (33 h 02 m 51 s, 331.4 g) (Scott, 2026-10-27) |
| TRAYS_6X6_P2 (6 trays, 6 bottom / 6 top, 5 perimeters, faster speeds, 210 C) | **Failed** (Scott, 2026-10-30): rat's nest partway up, and the walls were clearly flimsier than P1's even though the perimeter count (5) and geometry were identical. The 6/6 bottom/top cut itself was fine. Likely under-extrusion: P2's 60 mm/s inner perimeters and 70 mm/s infill run at about 5.3 and 6.2 mm3/s, at or above the one CR-6 SE flow test found (5 mm3/s at 100% extrusion, about 11 at under 90%; MakerShop review). A hypothesis, not proven; temperature (215 to 210 C) and speed changed together |
| TRAY_06_1X (ONE tray, 0.6 mm nozzle, 0.3 mm layers, 3 perimeters, 4 bottom / 4 top, P1 speeds and 215 C, flow cap 8 mm3/s) | On the SD card, not yet printed. Estimate 2 h 19 m, 48.7 g. Test of the 0.6 mm nozzle (see "Nozzle size" below) |

Layout A is not useful. The G-code headers on lenny confirm the printed MID_TRAYS was the 0.28 mm, 5% rectilinear slice (3h06m46s, 40.97 g); the 0.20 mm and 15% grid variants in `~/Downloads` were not the printed ones.

## Next steps

The 6 x 6 default (wall 2.0, floor 2.0) is built into the model and passes `./tiacad verify`; the tray golden is regenerated. Plate 1 (P1) has been printed and was good; plate 2 (P2) tried to trim the time and failed (see below).

1. **Print plates.** 6 trays fit one plate (2 x 3 inside the CR-6 SE's 234 x 234 mm travel). Slicer settings, changed from the earlier plates (SUNLU black PLA, 1.75 mm, 1 kg). The P1 column is what was printed; the P2 column is the trimmed slice that failed:

   | Setting | Earlier plates | 6 x 6 plate P1 (printed, good) | P2 (printed, failed) |
   |---|---|---|---|
   | Printer profile | Ender-3 stand-in | `Creality CR-6 SE (0.4 mm nozzle)` | same |
   | Layer height | 0.28 mm (MID, FULL_AB) | 0.20 mm | 0.20 mm (0.24 mm tested: only 1 h 12 m faster, more filament, skipped) |
   | Perimeters | 3 (MID) / 4 (FULL_AB) | 5 | 5 (4 saves only 55 min and 11.7 g per plate) |
   | Top / bottom layers | 4-6 / 3-4 | 8 (1.6 mm) / 10 (2.0 mm) | 6 (1.2 mm) / 6 (1.2 mm) |
   | Infill | 5% rectilinear / 10% gyroid | 10% gyroid | 10% gyroid, 70 mm/s |
   | Nozzle | 205 C (first layer 210) | 215 C (first layer 215) | 210 C (first layer 215), to cut stringing |
   | Fan | 100% (MID_TRAYS headers); 60% (FULL_AB header, checked on the card 2026-10-25) | 75%, off for the first 2 layers. This is more cooling than FULL_AB had, which is the opposite direction from the 30-40% suggested under "Fix layer adhesion" | same |
   | Perimeter / outer speed | 40 / 25 mm/s (MID); 60 (FULL_AB) | 40 / 25 mm/s | 60 inner / 35 outer and small perimeters; solid infill 60, top solid 40; travel 200 |
   | Seam | nearest | aligned | same |
   | Brim | none | none | none |

   Slice times (slicer estimate, 6 trays; P1's estimate matched the real print): P1 33 h 02 m / 331.4 g, 6/6 solid layers 29 h 07 m / 298.5 g, plus faster speeds 23 h 04 m, P2 23 h 05 m / 298.5 g. Raising acceleration from 500 to 1000 mm/s2 would save about 1 h 40 m more, but the CR-6 SE firmware limit is unchecked and higher acceleration may ring, so it is untried. Travel speed alone changes nothing because acceleration is the limit.

   To regenerate a slice, copy the config embedded in a G-code file (every line after `; prusaslicer_config = begin`, with the leading `; ` removed) to an `.ini`, then run the AppImage with `-g --load <ini> --duplicate 6` plus overrides such as `--bottom-solid-layers 6 --top-solid-layers 6 --temperature 210`. Use absolute paths; the AppImage ignores relative ones. The full P2 command is in `tt show TCAD-15` note #4.

   Slice on lenny with the AppImage (see the TIA memory `project_lenny_3d_printing_setup`); CR-6 SE is enabled by `model:CR6SE = 0.4` under `[vendor:Creality]` in `~/.config/PrusaSlicer/PrusaSlicer.ini`. Always grep the G-code header for `printer_settings_id`, `layer_height`, `perimeters`, and the top/bottom layer counts before copying to the card, and keep every coordinate inside 0-234 (no soft limits).
   **P2 failed (2026-10-30), so do not slice plates 2-6 from the P2 settings.** Keep P1's perimeter and wall speeds (inner 40, outer 25 mm/s) and 215 C. Only the 6 bottom / 6 top layer cut is known good. Keep volumetric flow (width x layer height x speed) at or below about 5 to 8 mm3/s on this printer.

   ### Nozzle size

   Slicer estimates for the 6-tray plate at P1's speeds (flow cap 8 mm3/s unless noted). The wall is 2.0 mm, so a nozzle that fits whole loops matters:

   | Nozzle | Layer | Wall loops | Time per plate | Flow demand (mm3/s) | Verdict |
   |---|---|---|---|---|---|
   | 0.4 (6/6 solid layers) | 0.20 | 5 | 29 h 07 m | 2 to 4 | baseline |
   | 0.6 | 0.30 | 3 x 0.66 = 1.98 mm | 13 h 53 m (15 h 04 m at a 6 cap) | 5 to 10 | picked: fits the wall, halves the time |
   | 0.8 | 0.40 | 2 (1.76 mm, 0.24 gap) | 7 h 50 m at a 15 cap, not reachable | 9 to 18 | exceeds the stock hotend |
   | 1.0 | 0.50 | 2 (2.2 mm) | 6 h 09 m at a 15 cap, not reachable | 14 to 28 | exceeds the stock hotend |

   All 36 trays at 0.6 mm: about 85 to 90 h. The 0.6 mm slice reuses the 0.4 mm CR-6 SE profile with only nozzle, width and layer overrides, so retraction and the start/end gcode are untuned. That the CR-6 SE takes the Creality M6 0.6 mm nozzle is unverified; swap, re-home and watch the first layers and about layer 7. To build it, use the regenerate recipe above with `--nozzle-diameter 0.6 --layer-height 0.3 --first-layer-height 0.3 --extrusion-width 0.66 --perimeter-extrusion-width 0.66 --external-perimeter-extrusion-width 0.63 --infill-extrusion-width 0.66 --solid-infill-extrusion-width 0.66 --top-infill-extrusion-width 0.6 --first-layer-extrusion-width 0.63 --perimeters 3 --bottom-solid-layers 4 --top-solid-layers 4 --filament-max-volumetric-speed 8 --duplicate 1`. Full notes: `tt show TCAD-15` notes 5 and 6.
2. **Cost check.** P1 estimated 1 d 9 h and 331 g per plate. P2 was estimated at 23 h 05 m and 299 g but failed, so its 139 h figure no longer stands (P1 settings: about 200 h and 2 kg; the 0.6 mm test points to about 85 to 90 h). Decide between home and online printing after the 0.6 mm single-tray test. After that test prints, check wall feel against P1, layer bonding, ramp stair-stepping, and any extruder skipping or gaps (which would mean the 8 mm3/s cap is too high).
3. The full `tiacad_core/tests/test_correctness` directory passed (589 tests) on 2026-10-25 after the 6 x 6 golden update. Local commits are not pushed.
4. Decide home versus online printing (below).

## Cost to print

### Geometry

| Part | Solid volume | Bounding box (mm) |
|---|---|---|
| 6 x 6 tray (default, wall 2.0, floor 2.0) | 79.2 cm3 | 78.5 x 63.2 x 50.8 |
| Tray A (wall 1.6, floor 1.2) | 115.6 cm3 | 94 x 74.8 x 50.8 |
| Tray B (wall 1.6, floor 1.2) | 172.1 cm3 | 94 x 93.8 x 50.8 |
| A + B pair (wall 1.6) | 287.7 cm3 | |

The A, B and pair rows and the online and home figures below are for the earlier wall 1.6 layouts; they have not been redone for the 6 x 6 tray.

### Online (JLC3DP)

Quoted by Scott: **PLA-C at about $20 per A + B pair was the cheapest** material tried, cheaper than SLA resin. I do not know the PLA-C spec, and I did not confirm that the $20 includes shipping. Search-based reference points, not quotes:

- MJF nylon (PA12) was listed at $0.275 per gram (August 2025), about $79 for the pair by weight.
- Per-tray prices were not read off the quote. By volume, A is about $8 and B about $12.
- Layout B (20 trays) would then be about $240 before shipping, duties and quantity discounts.

### Home

A pair is about 135 g of filament (a few dollars) plus about 9 hours of printer time. Printing 20 B trays at home is on the order of 90 hours.

### Open questions

- Does the JLC3DP price include shipping and import fees?
- What is PLA-C, and is it strong enough for daily handling?
- Re-quote after the wall change; thicker walls raise volume and weight.

## Related

- [YAML_REFERENCE.md](../../docs/user/YAML_REFERENCE.md) for the model syntax
- [MODEL_VALIDATION.md](../../docs/developer/MODEL_VALIDATION.md) for measure-plus-contract validation
- [VALIDATION_STRENGTHENING.md](../../docs/developer/VALIDATION_STRENGTHENING.md) for the `section` probe and contract relations
