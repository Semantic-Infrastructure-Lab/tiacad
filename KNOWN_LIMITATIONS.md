# TiaCAD Known Limitations

**Version:** v3.1.2 (+32 commits)
**Last Updated:** 2026-03-16

This document honestly describes what TiaCAD **cannot do**, with practical workarounds.

---

## What TiaCAD CAN Do (For Context)

Before limitations, here's what works great:

✅ **Solid Math Foundations:**
- Full spatial references (position + orientation + tangent)
- Frame-based transformations (local coordinate systems)
- Auto-generated part references (box.face_top, cylinder.axis_z)
- Proper rotation math (Rodrigues formula, explicit origins)

✅ **Complete Primitives & Operations:**
- All primitives (box, cylinder, sphere, cone, polygon)
- Boolean ops (union, difference, intersection)
- Patterns (linear, polar, grid)
- Finishing (fillet, chamfer)
- Sketch ops (extrude, revolve, sweep, loft)
- Advanced ops (hull, gusset, text)

✅ **Component System:**
- Local file imports (`./bracket.yaml`)
- Bundled stdlib (`tiacad://std/hardware/m3_screw`)
- GitHub imports (`github:user/repo/path.yaml`, cached to `~/.tiacad/cache/github/`)
- Hardware stdlib: m3/m4/m5/m6 screws, m3 washer, m3 standoff, m3 nut, mounting bracket

✅ **Dependency Graph + Watch Mode:**
- Incremental rebuild — only recomputes parts that changed
- `tiacad watch model.yaml` — auto-rebuild on file save
- `tiacad watch model.yaml --export /tmp/model.stl` — auto-export on each rebuild
- Cycle detection at build time

✅ **Production Quality:**
- 1382 tests, 0 failing, 2 skipped, 1 xfailed
- 92%+ code coverage
- 3MF export with color/metadata
- Schema validation

---

## Current Limitations

### 1. No Constraint Solver (Manual Positioning Only)

**What's Missing:**
```yaml
# CAN'T DO THIS (yet):
constraints:
  - type: flush
    faces: [bracket.bottom, base.top]
  - type: coaxial
    axes: [shaft.axis, bearing.inner_axis]
  - type: offset
    distance: 5mm
    parts: [mount, surface]

# TiaCAD cannot automatically satisfy constraints
```

**Impact:**
- Assembly alignment requires manual calculations
- Cannot specify design intent declaratively
- No automatic mate/align/flush operations

**Workaround:**
```yaml
# Use spatial references for relative positioning
parts:
  bracket:
    primitive: box
    parameters: {width: 50, height: 10, depth: 50}

operations:
  position_bracket:
    type: transform
    input: bracket
    transforms:
      # Manual positioning to align with base
      - translate:
          to: base.face_top  # Use auto-generated reference
          offset: [0, 0, 5]  # Manual offset for clearance
```

**Best Practice:**
- Define logical anchor points in `references:` section
- Use descriptive names (`motor_mount_point` not `point_1`)
- Comment the intent ("5mm clearance for wiring")
- Test assembly fit with multiple parameter values

**Future:** Next major milestone — see ROADMAP.md. Target: Q4 2026.

---

### 2. Limited Export Formats

**What Works:**
- ✅ STL (widely supported)
- ✅ 3MF (with color and metadata)
- ✅ STEP (via CadQuery, basic)

**What's Missing:**
- ❌ DXF (2D laser cutting profiles)
- ❌ IGES (older CAD interchange)
- ❌ G-code (CNC toolpaths)
- ❌ SVG (2D projections)

**Impact:**
- Limited CAM integration
- No direct laser cutting export
- Manual conversion needed for some workflows

**Workaround:**
- Export STEP → import to FreeCAD → export to other formats
- Use external tools for CAM (Fusion360, FreeCAD Path)

**Future:** Community-driven — add if there's demand

---

### 3. CadQuery Coupling (Internal Issue)

**What It Means:**
- TiaCAD uses CadQuery as its geometry kernel
- ~90% of code calls CadQuery directly (backend abstraction exists but not enforced)
- Cannot easily swap to FreeCAD, build123d, or other kernels

**Impact:**
- Tied to CadQuery's capabilities and limitations
- Testing slower than with pure mock backend
- Cannot leverage alternative CAD kernels

**For Users:** This doesn't affect YAML usage — you won't notice it

**For Contributors:**
- New code should use `GeometryBackend` abstraction
- Gradual refactoring during feature work
- No plan to support multiple backends (maintenance burden)

**Decision:** Stay with CadQuery — it works well, no strong reason to change

---

### 4. GitHub Import: No Branch Override

**What's Missing:**
```yaml
# CAN'T specify branch (defaults to main):
imports:
  - github:user/repo@develop/path.yaml  # syntax not yet supported
```

**Workaround:** Only `main` branch is supported. Use local copies for non-main branches.

**Future:** Could add `github:user/repo@branch/file.yaml` syntax if there's demand.

---

### 5. Assembly Parts Not Auto-Positioned

**What It Means:**
- When using component imports in an assembly, parts float at their default origin
- No spatial placement without explicit transforms in the parent YAML

**Impact:**
- Visual demos may show parts interpenetrating or floating in space
- Functional geometry (volume, dimensions) is correct; visual assembly is not

**Workaround:**
```yaml
operations:
  place_screw:
    type: transform
    input: screw
    transforms:
      - translate: {to: bracket.hole_1}
```

**Future:** Constraint solver (next milestone) will address this.

---

## Test Health

**As of 2026-03-16:**
- 1382 passing
- 2 skipped (intentional — visual regression tests needing reference images)
- 0 failing
- 1 xfailed (expected failure, tracked)

---

## Best Practices for Working Within Limitations

### For Missing Constraints:
1. Use spatial references (`base.face_top`)
2. Create named anchors for assembly points
3. Comment design intent ("5mm clearance")
4. Validate fits with measurement tests

### For Limited Export:
1. Export STEP as CAD interchange format
2. Use FreeCAD for secondary format conversion
3. STL/3MF for direct printing

---

## How This Document Works

- **Updated:** On releases when capabilities change
- **Honest:** Real limitations, real workarounds
- **Practical:** Focus on "how to work around" not "why we can't"
- **Forward-looking:** Links to ROADMAP.md for future plans

**Not Listed:** Bugs (those go in GitHub issues), planned features (see ROADMAP.md)

---

**Feedback:** If a limitation blocks your work, file an issue with your use case. Real user needs guide priorities.
