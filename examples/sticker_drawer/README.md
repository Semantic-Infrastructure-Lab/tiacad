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

Status as of 2026-10-19. The worked example is `sticker_tray.yaml`: single-sticker trays for a 15 in x 19.5 in drawer. Open work is tracked as TCAD-7 (`tt show TCAD-7`).

## Drawer and layouts

Drawer: 15 in front-to-back (381 mm) by 19.5 in wide (495 mm). Drawer height is not recorded. Trays are 94 mm wide and 50.8 mm (2 in) tall, five columns across (488 of 495 mm with 3 mm gaps).

| Layout | `slot_l` | Per column | Tray length at wall 1.6 | Total | Notes |
|---|---|---|---|---|---|
| A | 71.6 | 5 | 74.8 mm | 25 trays | Judged not useful |
| B | 90.6 (`--set slot_l=90.6`) | 4 | 93.8 mm | 20 trays | Holds stickers up to a 3.5 in (88.9 mm) diagonal; the one to build |

Tray length is `slot_l + 2 x wall`, so wall thickness spends drawer depth. Layout B ceiling is wall 2.3 mm (4 x 95.2 = 380.8 mm, no gap); wall 2.0 mm leaves 2.6 mm of slack.

## Print history

| Print | Result |
|---|---|
| TRAYS_15MM (full size, 0.2 mm) | Floor only printed; cause never found |
| MINI_TRAYS (1/3 scale) | Fine |
| MID_TRAYS (2/3 scale, 1.2 mm walls, 0.28 mm, 5% rectilinear) | Looked good, walls thin, ramp felt wimpy |
| FULL_AB (wall 1.6, 0.28 mm, 10% gyroid, 4 perimeters) | Printed. Walls flimsy on every tray, some layer adhesion issues (Scott, 2026-10-19) |

Layout A is not useful; use the larger layout B next time.

## Next steps

1. Thicken walls. Recommended `wall: 2.0` for layout B (about 5 perimeter loops at a 0.4 mm nozzle). Then run `./tiacad verify`, regenerate the tray golden, and check the fit. Inspect the ramp and finger cutouts with `tiacad section`, since they are the likely weak spots; add material there instead of everywhere if possible.
2. Fix layer adhesion in the slicer, not the model. Our plate used 0.28 mm layers (about 70% of nozzle width), 60% fan and 60 mm/s perimeters. Try in this order: fan 30-40% on walls, nozzle +5-10 C, slower perimeters, 0.2 mm layers, dry filament. PETG bonds between layers better than PLA (general knowledge, untested here). The slicer profile is still an Ender-3 stand-in; a CR-6 SE profile is not installed.
3. Run the full `tiacad_core/tests/test_correctness` directory (about 10-12 min) before pushing. It has not been run since the wall 1.6 golden update, and the two local commits are not pushed.
4. Decide home versus online printing (below).

## Cost to print

### Geometry (wall 1.6)

| Part | Solid volume | Bounding box (mm) |
|---|---|---|
| Tray A | 115.6 cm3 | 94 x 74.8 x 50.8 |
| Tray B | 172.1 cm3 | 94 x 93.8 x 50.8 |
| A + B pair | 287.7 cm3 | |

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
