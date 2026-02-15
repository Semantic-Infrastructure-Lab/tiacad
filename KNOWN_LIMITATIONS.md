# TiaCAD Known Limitations

**Version:** v3.1.2
**Last Updated:** 2026-02-15

This document honestly describes what TiaCAD **cannot do** as of v3.1.2, with practical workarounds.

---

## What TiaCAD CAN Do (For Context)

Before limitations, here's what works great:

✅ **Solid Math Foundations:**
- Full spatial references (position + orientation + tangent)
- Frame-based transformations (local coordinate systems)
- Auto-generated part references (box.face_top, cylinder.axis_z)
- Proper rotation math (Rodrigues formula, explicit origins)

✅ **Complete Primitives & Operations:**
- All primitives (box, cylinder, sphere, cone)
- Boolean ops (union, difference, intersection)
- Patterns (linear, polar, grid)
- Finishing (fillet, chamfer)
- Sketch ops (extrude, revolve, sweep, loft)
- Advanced ops (hull, gusset, text)

✅ **Production Quality:**
- 1125 comprehensive tests (94.4% passing)
- 92% code coverage
- 3MF export with color/metadata
- Schema validation

---

## Current Limitations

### 1. No Component/Module Import System

**What's Missing:**
```yaml
# ❌ CAN'T DO THIS (yet):
imports:
  - tiacad://std/hardware/m3_screw
  - github:user/repo/bracket.yaml
  - ./local_component.yaml

parts:
  screw:
    component: m3_screw  # Import from library
    parameters: {length: 20mm}
```

**Impact:**
- Cannot import standard parts (screws, nuts, bearings)
- No component sharing or reuse
- Copy-paste for common patterns

**Workaround:**
```yaml
# Use examples/ folder as template library
# Copy relevant YAML sections into your design
parts:
  screw:
    primitive: cylinder  # Model from primitives
    parameters: {radius: 1.5, height: 20}
  # ... manual screw threads not practical
```

**Best Practice:**
- Keep reusable patterns in `examples/` folder
- Use descriptive naming for copy-paste
- Create project-specific component libraries locally

**Future:** See ROADMAP.md - Component system under active consideration

---

### 2. No Dependency Graph (Full Rebuild on Changes)

**What's Missing:**
```yaml
parameters:
  screw_diameter: 3mm  # Change this value

# Currently: Rebuilds ENTIRE model
# Desired: Only parts depending on screw_diameter
```

**Impact:**
- Parameter changes require full model rebuild
- Slow iteration on complex models (>500 lines)
- No circular dependency detection at parse time

**Workaround:**
- Keep models under 200-300 lines for fast iteration
- Split complex assemblies into separate files
- Use parameters to centralize values
- Comment which parts depend on which parameters

**Best Practice:**
```yaml
parameters:
  # Base dimensions (affects: base, pillars, top_plate)
  base_width: 100
  base_depth: 80

  # Fasteners (affects: all mounting holes)
  screw_diameter: 3
  hole_clearance: 0.2
```

**Future:** See ROADMAP.md - DAG as alternative to component system

---

### 3. No Constraint Solver (Manual Positioning Only)

**What's Missing:**
```yaml
# ❌ CAN'T DO THIS (yet):
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

**Future:** See ROADMAP.md - Requires DAG first, then 16+ weeks for solver

---

### 4. No Live Preview/Watch Mode

**What's Missing:**
```bash
# ❌ CAN'T DO THIS (yet):
tiacad build model.yaml --watch
# Auto-rebuild on file save (like hot reload)
```

**Impact:**
- Manual rebuild after each edit
- Slower iteration cycle

**Workaround:**
```bash
# Use shell watch command
while true; do
  tiacad build model.yaml -o output.stl
  sleep 2
done

# Or use file watcher tools (entr, watchexec)
ls model.yaml | entr tiacad build model.yaml -o output.stl
```

**Best Practice:**
- Keep terminal and viewer (FreeCAD, PrusaSlicer) side-by-side
- Use incremental saves (model_v1.yaml, model_v2.yaml)
- Test small changes before full assembly

**Future:** Requires DAG for efficient incremental rebuilds

---

### 5. Limited Export Formats

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

**Future:** Community-driven - add if there's demand

---

### 6. CadQuery Coupling (Internal Issue)

**What It Means:**
- TiaCAD uses CadQuery as its geometry kernel
- ~90% of code calls CadQuery directly (backend abstraction exists but not enforced)
- Cannot easily swap to FreeCAD, build123d, or other kernels

**Impact:**
- Tied to CadQuery's capabilities and limitations
- Testing slower than with pure mock backend
- Cannot leverage alternative CAD kernels

**For Users:** This doesn't affect YAML usage - you won't notice it

**For Contributors:**
- New code should use `GeometryBackend` abstraction
- Gradual refactoring during feature work
- No plan to support multiple backends (maintenance burden)

**Decision:** Stay with CadQuery - it works well, no strong reason to change

---

## Test Health (Honest Status)

**As of 2026-02-15:**
- 1125 total tests
- 1062 passing (94.4%)
- 45 skipped (intentional)
- **17 failing (1.5%)** - actively being fixed:
  - 11 hull builder tests (CadQuery 2.7.0 STL import compatibility)
  - 6 visual regression tests (missing reference images, needs one-time generation)
- 1 xfailed (expected failure)

**Not "production-ready with 100% pass rate"** - we're honest about current state.

---

## Best Practices for Working Within Limitations

### For Missing Components:
1. Use `examples/` as template library
2. Create project-specific component collections
3. Document your patterns for reuse

### For Missing DAG:
1. Keep models modular (<300 lines per file)
2. Comment parameter dependencies clearly
3. Test with multiple parameter combinations

### For Missing Constraints:
1. Use spatial references (`base.face_top`)
2. Create named anchors for assembly points
3. Comment design intent ("5mm clearance")
4. Validate fits with measurement tests

### For Missing Imports:
1. Use YAML anchors for repetition within one file
2. Copy-paste is OK for now (document source)
3. Standardize naming conventions

---

## How This Document Works

- **Updated:** On releases when capabilities change
- **Honest:** Real limitations, real workarounds
- **Practical:** Focus on "how to work around" not "why we can't"
- **Forward-looking:** Links to ROADMAP.md for future plans

**Not Listed:** Bugs (those go in GitHub issues), planned features (see ROADMAP.md)

---

**Feedback:** If a limitation blocks your work, file an issue with your use case. Real user needs guide priorities.
