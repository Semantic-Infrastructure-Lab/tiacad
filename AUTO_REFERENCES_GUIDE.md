# Auto-References Guide

## Overview

TiaCAD automatically generates **spatial references** (we call them **anchors**) for every part, making it easy to position and attach parts without manually calculating coordinates.

**Think of anchors as**: Marked spots on a workbench where things can be attached - like "top of the base plate" or "center of the cylinder". Every part automatically provides these attachment points.

**Why "anchors"?** Just like a ship's anchor marks a specific location, spatial anchors mark positions and orientations in 3D space where parts can be positioned.

**Key benefits**:
- **No manual coordinate math**: Instead of `translate: [50, 25, 10]`, use `translate: base.face_top`
- **Self-updating**: If the base changes size, anchors update automatically
- **Orientation-aware**: Anchors include direction information (surface normals) for intelligent positioning
- **Every part gets them**: All primitives (box, cylinder, sphere, cone) automatically provide standard anchors

**Visual Guide:** See [Auto-Reference Visualization](docs/diagrams/auto-reference-visualization.md) for a complete visual reference of all auto-generated anchors.

These auto-generated anchors are available for all primitive types.

## Canonical References by Primitive Type

Every part automatically provides the following references:

### Common References (All Primitives)

| Reference | Description | Type | Example Usage |
|-----------|-------------|------|---------------|
| `{part}.center` | Bounding box center | Point | `translate: {to: "base.center"}` |
| `{part}.origin` | Part origin (0,0,0) | Point | `rotate: {origin: "arm.origin"}` |
| `{part}.axis_x` | X-axis through center | Axis | `rotate: {axis: "shaft.axis_x"}` |
| `{part}.axis_y` | Y-axis through center | Axis | `rotate: {axis: "shaft.axis_y"}` |
| `{part}.axis_z` | Z-axis through center | Axis | `rotate: {axis: "shaft.axis_z"}` |

### Face References

Face references point to the center of each face with a normal vector pointing outward.

#### Box (All 6 Faces)

| Reference | Description | Normal Direction |
|-----------|-------------|------------------|
| `{part}.face_top` | Top face (+Z) | [0, 0, 1] |
| `{part}.face_bottom` | Bottom face (-Z) | [0, 0, -1] |
| `{part}.face_left` | Left face (-X) | [-1, 0, 0] |
| `{part}.face_right` | Right face (+X) | [1, 0, 0] |
| `{part}.face_front` | Front face (+Y) | [0, 1, 0] |
| `{part}.face_back` | Back face (-Y) | [0, -1, 0] |

**Example:**
```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 20, depth: 50}

  mount:
    primitive: box
    parameters: {width: 30, height: 10, depth: 30}
    translate:
      to: base.face_top  # Place on top of base
```

#### Cylinder (2 Faces)

| Reference | Description | Normal Direction |
|-----------|-------------|------------------|
| `{part}.face_top` | Top circular face | [0, 0, 1] |
| `{part}.face_bottom` | Bottom circular face | [0, 0, -1] |

**Example:**
```yaml
parts:
  shaft:
    primitive: cylinder
    parameters: {radius: 5, height: 50}

  cap:
    primitive: cylinder
    parameters: {radius: 7, height: 3}
    translate:
      to: shaft.face_top  # Place cap on top of shaft
```

#### Sphere (2 Points)

| Reference | Description | Normal Direction |
|-----------|-------------|------------------|
| `{part}.face_top` | Top point of sphere | [0, 0, 1] |
| `{part}.face_bottom` | Bottom point of sphere | [0, 0, -1] |

**Example:**
```yaml
parts:
  ball:
    primitive: sphere
    parameters: {radius: 15}

  stand:
    primitive: cylinder
    parameters: {radius: 5, height: 10}
    translate:
      to: ball.face_bottom  # Place stand under ball
```

## Using Auto-References

### Basic Translation

Move a part to align with another part's reference:

```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 20, depth: 50}

  tower:
    primitive: box
    parameters: {width: 20, height: 80, depth: 20}
    translate:
      to: base.face_top  # Tower base sits on base's top face
```

### With Offsets

Add an offset to an auto-reference:

```yaml
parts:
  platform:
    primitive: box
    parameters: {width: 100, height: 5, depth: 100}

  post:
    primitive: cylinder
    parameters: {radius: 3, height: 40}
    translate:
      to:
        from: platform.face_top
        offset: [0, 0, 5]  # 5 units above platform
```

### Rotation Around Auto-Axes

Rotate a part around an auto-generated axis:

```yaml
parts:
  base:
    primitive: box
    parameters: {width: 50, height: 10, depth: 50}

  arm:
    primitive: box
    parameters: {width: 60, height: 5, depth: 10}
    rotate:
      axis: base.axis_x  # Rotate around base's X-axis
      angle: 45
      origin: base.center
```

## Benefits

1. **No Manual Calculation**: Don't need to calculate face positions or centers
2. **Maintainable**: If base dimensions change, references update automatically
3. **Readable**: `base.face_top` is clearer than `[50, 50, 20]`
4. **Type-Safe**: Auto-references are validated at parse time

## Implementation Details

### Backend Abstraction

Auto-references use the geometry backend abstraction:
- `GeometryBackend.get_bounding_box()` - Returns min, max, and center
- `GeometryBackend.select_faces()` - Selects faces by direction
- `GeometryBackend.get_face_center()` - Gets face center point
- `GeometryBackend.get_face_normal()` - Gets face normal vector

This abstraction enables:
- Fast unit testing with `MockBackend`
- Real CAD operations with `CadQueryBackend`
- Future support for other CAD kernels

### Caching

Auto-references are cached by the `SpatialResolver` for performance. The cache is automatically invalidated when parts are modified.

## See Also

- [NAMED_POINTS_GUIDE.md](NAMED_POINTS_GUIDE.md) - For custom reference points
- [YAML_REFERENCE.md](YAML_REFERENCE.md) - Complete YAML syntax reference
- [examples/](examples/) - Example YAML files demonstrating auto-references
