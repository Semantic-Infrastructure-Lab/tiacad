---
title: "Case Study — Modeling a Dimensionally Accurate Egg"
type: analysis
beth_topics:
  - tiacad
  - sketch
  - revolve
  - validation
  - cli
  - case-study
---

# Case Study — Modeling a Dimensionally Accurate Egg

Building `examples/egg.yaml` (a biconic-profile revolve matching a real chicken
egg's length/diameter/asymmetry) surfaced four real friction points in the
sketch/revolve workflow, plus one false alarm (§1, corrected below — a
mistake in how I invoked the CLI, not a TiaCAD defect). None of the real
issues blocked the model from shipping — the final part is watertight,
dimensionally correct (44.0 × 44.0 × 58.0mm, 58,665mm³), and passes
`tiacad validate-geometry` — but each cost time that a diligent user wouldn't
expect to spend, and most of the failures were **silent**: nothing in
`tiacad build`, `tiacad validate`, or `tiacad render` flagged them.

---

## 1. ~~CLI entry point~~ — correction: this was my own mistake, not a TiaCAD bug

**Originally filed as `TCAD-BUG-1`; rejected on follow-up.** I guessed
`python -m tiacad_core.cli` (wrong module — `__main__.py` actually lives at
`tiacad_core/__main__.py`, one level up) and `poetry run tiacad` (this
project uses plain `setuptools`, not poetry) instead of reading
[CLI.md's Installation section](CLI.md#installation) first, which documents
exactly two zero-setup invocations:

```bash
./tiacad build examples/egg.yaml -o /tmp/egg.stl --stats   # works, no venv needed
python -m tiacad_core --help                                # also works
```

Both ran correctly against plain system `python3` with no `.venv` activation
and no `pip install -e .` — confirmed after the fact. `pip install tiacad` /
a registered `tiacad` console script is separately, correctly documented as
"Option 3: Install Package (**Future**)" — not yet supported, and not
claimed to be.

**Lesson for me, not for TiaCAD:** I skipped straight to guessing CLI
invocation syntax instead of running `reveal docs/developer/CLI.md --section
Installation` first, the same "reveal before you guess" discipline this
project's own `CLAUDE.md` calls for. No code change warranted here — leaving
this section in as an honest correction rather than deleting it, since a
false "the CLI is broken" claim would otherwise sit uncorrected in this doc.

---

## 2. Declared-but-unreferenced parameters are never flagged

`egg.yaml`'s first draft declared:

```yaml
parameters:
  length: 58
  max_diameter: 44
  blunt_fraction: 0.40
```

...as if the file were parametric. It wasn't — the sketch's `points:` list is
49 hardcoded literal coordinates, precomputed in a throwaway Python script,
because the sketch DSL has no way to express an ellipse arc (see §4 below).
Nothing in `length`/`max_diameter`/`blunt_fraction` is ever interpolated via
`${...}` anywhere in the file.

`tiacad validate` and `tiacad build --stats` both ran clean — `Parameters: 3`
is reported as a count, not cross-checked against usage. A user resizing this
"parametric" egg by editing `max_diameter: 44` → `50` would get **no error and
no effect** — the geometry wouldn't change at all, silently.

**Impact:** false confidence that a file is parametric when it isn't; this
class of bug is invisible until someone tries to actually reparametrize.

**Fixed** (`TCAD-BUG-2`, same session): a new `UnusedParametersRule` scans
the raw YAML source for `${...}` spans and warns on any declared parameter
that never appears in one — including correctly recognizing a parameter used
only from within another parameter's own formula as legitimately used, not
dead. See `KNOWN_LIMITATIONS.md` #21 for the full writeup. Running the new
rule against every committed example (not just this egg model) turned up
**8 pre-existing shipped files** with genuinely dead parameters — this wasn't
a hypothetical risk, it was already latent in the codebase.

---

## 3. A degenerate revolve apex produced a non-watertight STL with zero warning

The profile polygon's two tip points sat at exactly `r=0` (on the revolve
axis, at the egg's blunt and pointed ends). Revolving that profile 360° with
CadQuery/OCC produced a mesh with **4 broken faces and 2 open edge loops** at
the poles — confirmed only by loading the exported STL in `trimesh` directly:

```python
import trimesh
m = trimesh.load('/tmp/egg.stl')
m.is_watertight   # False
trimesh.repair.broken_faces(m)   # 4 faces
```

`tiacad build` reported success with no warning. `tiacad validate` (schema
validation) also passed clean — it doesn't build geometry. Only
`tiacad validate-geometry`, a separate command not run by default, would have
caught this (confirmed after the fact — it correctly reports
`Watertight: ✅ Yes` once fixed). The fix was moving both tip radii from
`0.0` to `0.02` (a 20-micron nudge), which fully resolved the degeneracy.

**Impact:** it is possible to `tiacad build` a non-manifold STL — silently —
whenever a revolve profile touches its own axis exactly at a tip. This is
exactly the kind of geometric defect a 3D-printing user would only discover
after a failed slice or print.

**Fixed** (`TCAD-BUG-3`, same session): `tiacad build` now runs a
best-effort `trimesh` watertightness check right after any `.stl` export and
prints an advisory warning (never a build failure) when the mesh isn't
manifold. See `KNOWN_LIMITATIONS.md` #19 for the full writeup and
`tiacad_core/tests/test_cli/test_cli_build.py`'s two new tests
(`test_build_stl_watertight_mesh_prints_no_warning`,
`test_build_stl_non_watertight_mesh_warns` — the latter using a minimal
3-point bicone repro, not the full egg model).

---

## 4. Sketch DSL has no arc/ellipse/spline primitive — see `KNOWN_LIMITATIONS.md` #18

`tiacad_core/sketch.py` implements exactly four `Shape2D` subclasses:
`Rectangle2D`, `Circle2D`, `Polygon2D` (straight line segments only), and
`Text2D`. There is no `Arc2D`, `Ellipse2D`, or `Spline2D`, even though the
underlying CadQuery/OCC backend natively supports all three (`cq.Workplane`
exposes `.ellipseArc()`, `.spline()`, `.threePointArc()`, etc.) — this is a
YAML-schema gap, not a backend limitation.

**Consequence for this model:** the egg's curved profile had to be
hand-faceted outside TiaCAD — a standalone Python script sampled
`r(z) = R·sqrt(1 - (z/h)²)` at 49 points per half and pasted the literal
floats into the YAML `points:` list (see §2 for the parametrization fallout).
There is also no `segments:`/`tolerance:` knob anywhere in the sketch or
revolve schema to control facet density — accuracy is entirely a function of
how many points a human (or AI) decides to precompute by hand.

Filed as a limitation (not just a bug) in
[KNOWN_LIMITATIONS.md](../../KNOWN_LIMITATIONS.md#18-sketch-dsl-has-no-arcellipsespline-primitive)
and tracked as `TCAD-DSL-1`.

---

## 5. The required placeholder part for sketch-only designs generates permanent spurious warnings

`YAML_REFERENCE.md` documents that `parts:` is "currently required even for
sketch-only designs," and prescribes a minimal placeholder (`_placeholder`, a
1×1×1 box, ignored on export) — exactly what `bottle_revolve.yaml`,
`duck_call_insert.yaml`, and this egg model all do. But that placeholder is
never exported or referenced by anything, so `tiacad debug`/`render`'s own
validator flags it twice, every time, in every sketch+revolve file:

```json
{"severity": "WARNING", "suggestion": "Add transform operation, export part, or remove if unused", ...}
{"severity": "WARNING", "suggestion": "Export this part, reference it from another operation, or remove it if it's dead work", ...}
```

`tiacad render`'s summary line (`Validation passed: 0 errors, 2 warnings,
0 info`) doesn't distinguish "2 warnings about a documented, harmless
workaround" from "2 warnings about your actual model" — both look identical
until you dig into `validation_report.json`. Confirmed this is exactly what
the 2 warnings on `egg.yaml` are: nothing about the egg geometry, purely the
placeholder.

**Impact:** every sketch-only model in the codebase (at least 3 committed
examples, likely more) carries permanent warning noise. A real new warning
introduced by a future edit would blend into the same "2 warnings" baseline
users learn to ignore.

**Fixed** (`TCAD-BUG-4`, same session): `UnusedPartsRule` and
`MissingPositionRule` now both skip leading-underscore part names — the
convention already in consistent use across 17 committed examples, not a new
one. `examples/egg.yaml` now reports `0 errors, 0 warnings, 0 info`. See
`KNOWN_LIMITATIONS.md` #20 for the full writeup, including the note that the
deeper fix — `parts:` shouldn't be required at all for sketch-only designs —
remains open and is a larger schema change than this session took on.

---

## What Went Right

- `tiacad render`'s 8-view trust check made it fast to visually confirm the
  final shape actually reads as an egg (rounder blunt end, tapered point,
  circular top/bottom cross-sections) once the geometry was fixed.
- `tiacad validate-geometry` gave a clean, decisive watertight/volume/vertex
  report once run — the tool exists and works, it just isn't in the default
  `build` path.
- The `revolve` operation itself, and the documented
  placeholder-part-for-sketch-only-designs pattern (from `bottle_revolve.yaml`
  and `duck_call_insert.yaml`), worked exactly as documented.

---

## The Principle

Three of four friction points here were **silent**: a fake-parametric file, a
non-manifold export, and a broken dev entry point all reported success. The
fourteenth-ish time this pattern shows up in `KNOWN_LIMITATIONS.md` (see
entries #8, #12, #14, #17 — all "silent/opaque failure" fixes) — TiaCAD's
recurring failure mode is not wrong geometry, it's **geometry that's wrong and
says nothing**. Each fix so far has been reactive, found by a human (or AI)
manually reaching for `trimesh` or noticing something felt off. The
recurring, compounding improvement is the same one
`CASE_STUDY_MOUNTING_HOLES.md` already named: move verification from
ad-hoc-and-human-triggered to automatic-and-every-build.
