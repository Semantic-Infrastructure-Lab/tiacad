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

Status as of 2026-10-25. The worked example is `sticker_tray.yaml`: single-sticker trays for a 15 in x 19.5 in drawer. Open work is tracked as TCAD-7 and TCAD-15 (`tt show TCAD-15`).

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

Layout A is not useful. The G-code headers on lenny confirm the printed MID_TRAYS was the 0.28 mm, 5% rectilinear slice (3h06m46s, 40.97 g); the 0.20 mm and 15% grid variants in `~/Downloads` were not the printed ones.

## Next steps

The 6 x 6 default (wall 2.0, floor 2.0) is built into the model and passes `./tiacad verify`; the tray golden is regenerated. Nothing has been printed at this size yet.

1. **Print test plate.** 6 trays fit one plate (2 x 3 inside the CR-6 SE's 234 x 234 mm travel). Planned slicer settings, changed from the earlier plates (SUNLU black PLA, 1.75 mm, 1 kg):

   | Setting | Earlier plates | 6 x 6 test plate |
   |---|---|---|
   | Printer profile | Ender-3 stand-in | `Creality CR-6 SE (0.4 mm nozzle)` |
   | Layer height | 0.28 mm (MID, FULL_AB) | 0.20 mm |
   | Perimeters | 3 (MID) / 4 (FULL_AB) | 5 |
   | Top / bottom layers | 4-6 / 3-4 | 8 (1.6 mm) / 10 (2.0 mm) |
   | Infill | 5% rectilinear / 10% gyroid | 10% gyroid |
   | Nozzle | 205 C (first layer 210) | 215 C (first layer 215) |
   | Fan | 100% (MID_TRAYS headers); 60% (FULL_AB header, checked on the card 2026-10-25) | 75%, off for the first 2 layers. This is more cooling than FULL_AB had, which is the opposite direction from the 30-40% suggested under "Fix layer adhesion" |
   | Perimeter / outer speed | 40 / 25 mm/s (MID); 60 (FULL_AB) | 40 / 25 mm/s |
   | Seam | nearest | aligned |
   | Brim | none | none |

   Slice on lenny with the AppImage (see the TIA memory `project_lenny_3d_printing_setup`); CR-6 SE is enabled by `model:CR6SE = 0.4` under `[vendor:Creality]` in `~/.config/PrusaSlicer/PrusaSlicer.ini`. Always grep the G-code header for `printer_settings_id`, `layer_height`, `perimeters`, and the top/bottom layer counts before copying to the card, and keep every coordinate inside 0-234 (no soft limits).
2. **Cost check.** The first 6-tray slice at these settings estimates 1 d 9 h and 331 g for the plate, so all 36 trays would be 6 plates and about 200 h and 2 kg. Decide whether to trim (fewer perimeters or solid layers, 0.24 mm layers) or go online before printing everything.
3. Run the full `tiacad_core/tests/test_correctness` directory (about 10-12 min) before pushing. It has not been run since the wall 1.6 golden update, and the local commits are not pushed.
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
