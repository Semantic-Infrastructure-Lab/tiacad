# TiaCAD Clean Architecture v3.0
## Zero Legacy Constraints - Pure Design

**Philosophy:** Everything is a spatial reference. Positions, orientations, frames - all unified.

---

## 1. Core Spatial Model

### 1.1 Single Unified Reference Type

```python
from dataclasses import dataclass
from typing import Literal, Optional
import numpy as np

@dataclass
class SpatialRef:
    """Universal spatial reference - the ONLY geometry reference type"""

    # Position (always present)
    position: np.ndarray  # (3,) array

    # Orientation (optional - None for simple points)
    orientation: Optional[np.ndarray] = None  # (3,) normal/direction vector

    # Tangent (optional - for edges, defines local coordinate system)
    tangent: Optional[np.ndarray] = None  # (3,) tangent vector

    # Type hint for debugging/validation
    ref_type: Literal['point', 'face', 'edge', 'axis'] = 'point'

    @property
    def frame(self) -> 'Frame':
        """Generate a Frame from this reference"""
        if self.orientation is None:
            # Default to world Z-up frame at this position
            return Frame(origin=self.position)

        if self.tangent is None:
            # Have normal, construct arbitrary tangent
            return Frame.from_normal(self.position, self.orientation)

        # Have both - full frame definition
        return Frame.from_normal_tangent(self.position, self.orientation, self.tangent)


@dataclass
class Frame:
    """Local coordinate system - generated FROM SpatialRef, not separate"""

    origin: np.ndarray    # (3,)
    x_axis: np.ndarray    # (3,) normalized
    y_axis: np.ndarray    # (3,) normalized
    z_axis: np.ndarray    # (3,) normalized

    @classmethod
    def from_normal(cls, origin: np.ndarray, normal: np.ndarray) -> 'Frame':
        """Construct frame from origin + normal (auto-generate tangents)"""
        z = normal / np.linalg.norm(normal)

        # Choose arbitrary perpendicular
        if abs(z[2]) < 0.9:
            x = np.cross(z, [0, 0, 1])
        else:
            x = np.cross(z, [1, 0, 0])
        x = x / np.linalg.norm(x)

        y = np.cross(z, x)

        return cls(origin=origin, x_axis=x, y_axis=y, z_axis=z)

    @classmethod
    def from_normal_tangent(cls, origin: np.ndarray, normal: np.ndarray, tangent: np.ndarray) -> 'Frame':
        """Construct frame from origin + normal + tangent"""
        z = normal / np.linalg.norm(normal)
        x = tangent / np.linalg.norm(tangent)
        y = np.cross(z, x)
        return cls(origin=origin, x_axis=x, y_axis=y, z_axis=z)

    def to_transform_matrix(self) -> np.ndarray:
        """Return 4x4 homogeneous transformation matrix"""
        mat = np.eye(4)
        mat[:3, 0] = self.x_axis
        mat[:3, 1] = self.y_axis
        mat[:3, 2] = self.z_axis
        mat[:3, 3] = self.origin
        return mat
```

---

## 2. Clean YAML Syntax

### 2.1 Unified `references:` Section

**No more separate `named_points`, `named_faces`, etc. - just `references:`**

```yaml
schema_version: 3.0

references:
  # Simple point (no orientation)
  center:
    type: point
    value: [0, 0, 0]

  # Face reference (position + normal)
  top_face:
    type: face
    part: base_plate
    selector: ">Z"        # CadQuery selector
    at: center            # center | bounds_center | vertex_avg

  # Edge reference (position + tangent + normal)
  front_edge:
    type: edge
    part: base_plate
    selector: "|Z and >Y"
    at: midpoint          # midpoint | start | end

  # Axis reference (origin + direction)
  shaft_axis:
    type: axis
    from: [0, 0, 0]
    to: [0, 0, 100]

  # Derived reference (offset from another)
  mount_point:
    type: point
    from: top_face        # Reference another reference!
    offset: [10, 0, 5]    # In local frame of 'top_face'
```

### 2.2 Clean Transform Syntax

**Every transform can use ANY reference - no special cases**

```yaml
operations:
  align_bracket:
    type: transform
    input: bracket
    transforms:
      # Translate: move part origin to reference
      - translate:
          to: mount_point

      # Rotate: around reference's frame
      - rotate:
          angle: 90
          axis: Z              # Axis in reference's local frame
          around: top_face     # Use this reference's frame

      # Align: match orientations
      - align:
          this_ref: bracket.bottom_face
          to_ref: base_plate.top_face
          orientation: normal  # normal | reverse | tangent
          offset: 2            # Gap distance
```

### 2.3 Part-Local References (Auto-Generated)

**Every primitive automatically generates canonical references**

```python
# When you create a box:
parts:
  base:
    primitive: box
    size: [100, 60, 10]

# System auto-creates:
references:
  base.center:      # Center of bounding box
  base.origin:      # Part origin (bottom-center by default)
  base.face_top:    # Top face (>Z)
  base.face_bottom: # Bottom face (<Z)
  base.face_left:   # (-X)
  base.face_right:  # (+X)
  base.face_front:  # (+Y)
  base.face_back:   # (-Y)
  base.axis_x:      # X-axis through center
  base.axis_y:      # Y-axis through center
  base.axis_z:      # Z-axis through center
```

You can reference these immediately:

```yaml
operations:
  mount_arm:
    type: transform
    input: arm
    transforms:
      - translate:
          to: base.face_top  # Auto-generated reference!
```

---

## 3. Resolver Architecture

### 3.1 Single Resolver Class

```python
class SpatialResolver:
    """
    Resolves reference specifications to SpatialRef objects.

    Clean, single responsibility: spec → SpatialRef
    """

    def __init__(self, registry: PartRegistry, references: Dict[str, Any]):
        self.registry = registry
        self.references = references  # User-defined references
        self._cache = {}              # Resolved references

    def resolve(self, spec: Union[str, dict, list]) -> SpatialRef:
        """
        Resolve ANY reference spec to SpatialRef.

        Args:
            spec: Can be:
                - String: "ref_name" or "part.ref_name"
                - Dict: {type: face, part: x, selector: y}
                - List: [x, y, z] (simple point)

        Returns:
            SpatialRef with position + orientation
        """
        # List = absolute point
        if isinstance(spec, list):
            return SpatialRef(position=np.array(spec), ref_type='point')

        # String = reference name (dot notation)
        if isinstance(spec, str):
            return self._resolve_name(spec)

        # Dict = inline reference definition
        if isinstance(spec, dict):
            return self._resolve_dict(spec)

        raise ValueError(f"Invalid reference spec: {spec}")

    def _resolve_name(self, name: str) -> SpatialRef:
        """Resolve dot notation: 'part.ref' or 'ref'"""

        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Check user-defined references
        if name in self.references:
            result = self.resolve(self.references[name])
            self._cache[name] = result
            return result

        # Check part-local references (e.g., "base.face_top")
        if '.' in name:
            part_name, ref_name = name.split('.', 1)
            part = self.registry.get(part_name)
            result = self._resolve_part_local(part, ref_name)
            self._cache[name] = result
            return result

        raise ValueError(f"Reference not found: {name}")

    def _resolve_dict(self, spec: dict) -> SpatialRef:
        """Resolve inline reference definition"""

        ref_type = spec.get('type', 'point')

        if ref_type == 'point':
            if 'value' in spec:
                # Absolute point
                return SpatialRef(position=np.array(spec['value']), ref_type='point')
            elif 'from' in spec:
                # Offset from another reference
                base = self.resolve(spec['from'])
                offset = np.array(spec['offset'])

                # Apply offset in base's local frame
                if base.orientation is not None:
                    frame = base.frame
                    world_offset = (
                        offset[0] * frame.x_axis +
                        offset[1] * frame.y_axis +
                        offset[2] * frame.z_axis
                    )
                else:
                    # No orientation - offset in world coords
                    world_offset = offset

                return SpatialRef(
                    position=base.position + world_offset,
                    ref_type='point'
                )

        elif ref_type == 'face':
            part = self.registry.get(spec['part'])
            selector = spec['selector']
            at = spec.get('at', 'center')

            # Use GeometryBackend to extract face geometry
            return self._extract_face_ref(part, selector, at)

        elif ref_type == 'edge':
            part = self.registry.get(spec['part'])
            selector = spec['selector']
            at = spec.get('at', 'midpoint')

            return self._extract_edge_ref(part, selector, at)

        elif ref_type == 'axis':
            from_pt = np.array(spec['from'])
            to_pt = np.array(spec['to'])
            direction = to_pt - from_pt
            direction = direction / np.linalg.norm(direction)

            return SpatialRef(
                position=from_pt,
                orientation=direction,
                ref_type='axis'
            )

        raise ValueError(f"Unknown reference type: {ref_type}")

    def _resolve_part_local(self, part, ref_name: str) -> SpatialRef:
        """
        Resolve auto-generated part-local references.

        Examples: 'center', 'origin', 'face_top', 'axis_z'
        """
        if ref_name == 'center':
            # Bounding box center
            bbox = part.geometry.val().BoundingBox()
            pos = np.array([
                (bbox.xmin + bbox.xmax) / 2,
                (bbox.ymin + bbox.ymax) / 2,
                (bbox.zmin + bbox.zmax) / 2
            ])
            return SpatialRef(position=pos, ref_type='point')

        elif ref_name == 'origin':
            # Part's current position
            return SpatialRef(position=np.array(part.current_position), ref_type='point')

        elif ref_name.startswith('face_'):
            # Auto-generated face references
            face_map = {
                'face_top': '>Z',
                'face_bottom': '<Z',
                'face_left': '<X',
                'face_right': '>X',
                'face_front': '>Y',
                'face_back': '<Y'
            }
            selector = face_map.get(ref_name)
            if selector:
                return self._extract_face_ref(part, selector, 'center')

        elif ref_name.startswith('axis_'):
            # Auto-generated axis references
            axis_map = {
                'axis_x': ([1, 0, 0], 'X'),
                'axis_y': ([0, 1, 0], 'Y'),
                'axis_z': ([0, 0, 1], 'Z')
            }
            if ref_name in axis_map:
                direction, _ = axis_map[ref_name]
                center = self._resolve_part_local(part, 'center').position
                return SpatialRef(
                    position=center,
                    orientation=np.array(direction),
                    ref_type='axis'
                )

        raise ValueError(f"Unknown part-local reference: {ref_name}")

    def _extract_face_ref(self, part, selector: str, at: str) -> SpatialRef:
        """Extract face reference from part geometry"""
        # Use GeometryBackend
        backend = part.backend
        faces = backend.select_faces(part.geometry, selector)

        if not faces:
            raise ValueError(f"No faces matched selector '{selector}' on part {part.name}")

        face = faces[0]  # Take first match

        # Get face properties
        center = backend.get_face_center(face)
        normal = backend.get_face_normal(face)

        # For 'at' parameter (future: bounds_center, vertex_avg)
        # Currently just use geometric center

        return SpatialRef(
            position=np.array(center),
            orientation=np.array(normal),
            ref_type='face'
        )

    def _extract_edge_ref(self, part, selector: str, at: str) -> SpatialRef:
        """Extract edge reference from part geometry"""
        backend = part.backend
        edges = backend.select_edges(part.geometry, selector)

        if not edges:
            raise ValueError(f"No edges matched selector '{selector}' on part {part.name}")

        edge = edges[0]

        # Get edge properties
        if at == 'midpoint':
            position = backend.get_edge_midpoint(edge)
        elif at == 'start':
            position = backend.get_edge_start(edge)
        elif at == 'end':
            position = backend.get_edge_end(edge)
        else:
            raise ValueError(f"Unknown edge location: {at}")

        tangent = backend.get_edge_tangent(edge, at_param=0.5)

        # For edge normal, we'd need to query adjacent faces
        # For now, leave as None or compute from curve

        return SpatialRef(
            position=np.array(position),
            orientation=np.array(tangent),  # Tangent as primary direction
            ref_type='edge'
        )
```

---

## 4. GeometryBackend Extensions

**Add these methods to base.GeometryBackend:**

```python
class GeometryBackend(ABC):
    """Abstract interface for CAD operations"""

    # ... existing methods ...

    # NEW: Spatial query methods
    @abstractmethod
    def select_faces(self, geom, selector: str) -> List[Any]:
        """Select faces matching CadQuery-style selector"""
        pass

    @abstractmethod
    def select_edges(self, geom, selector: str) -> List[Any]:
        """Select edges matching CadQuery-style selector"""
        pass

    @abstractmethod
    def get_face_center(self, face) -> Tuple[float, float, float]:
        """Get geometric center of face"""
        pass

    @abstractmethod
    def get_face_normal(self, face) -> Tuple[float, float, float]:
        """Get face normal vector (outward-pointing)"""
        pass

    @abstractmethod
    def get_edge_midpoint(self, edge) -> Tuple[float, float, float]:
        """Get midpoint of edge"""
        pass

    @abstractmethod
    def get_edge_tangent(self, edge, at_param: float = 0.5) -> Tuple[float, float, float]:
        """Get tangent vector of edge at parameter t ∈ [0,1]"""
        pass
```

---

## 5. Benefits of Clean Design

### 5.1 Simplicity

| Old (Phase 2) | Clean (v3.0) |
|---------------|--------------|
| `PointResolver` returns `(x,y,z)` | `SpatialResolver` returns `SpatialRef` (position + orientation) |
| `named_points`, `named_faces`, etc. | Just `references:` |
| 4 different dict formats | 1 unified format |
| Separate Frame concept | Frames generated FROM references |
| Manual orientation math | Automatic frame computation |

### 5.2 Consistency

**Everything works the same way:**

```yaml
# Point
- translate: {to: my_ref}

# Face
- translate: {to: my_ref}

# Edge
- translate: {to: my_ref}

# Axis
- rotate: {around: my_ref, angle: 90}
```

No special cases, no "this only works with faces" - if it's a reference, it works everywhere.

### 5.3 Composability

```yaml
references:
  # Base reference
  mount_face:
    type: face
    part: base
    selector: ">Z"

  # Offset from face (in face's local frame!)
  bolt_hole_1:
    type: point
    from: mount_face
    offset: [20, 20, 0]  # 20mm right, 20mm forward in face frame

  # Offset from offset
  bolt_hole_2:
    type: point
    from: bolt_hole_1
    offset: [40, 0, 0]  # 40mm right from first hole
```

Unlimited nesting, all automatic.

---

## 6. Implementation Strategy

### Phase 1: Core (2 weeks)
1. Implement `SpatialRef` and `Frame` classes
2. Implement `SpatialResolver`
3. Add GeometryBackend methods
4. 60+ tests

### Phase 2: Integration (2 weeks)
1. Update parser to use `references:` section
2. Update OperationsBuilder to use SpatialResolver
3. Remove old PointResolver
4. 40+ tests

### Phase 3: Auto-References (1 week)
1. Implement part-local reference generation
2. Document canonical references per primitive
3. 30+ tests

### Phase 4: Polish (1 week)
1. Update YAML schema
2. Update documentation
3. Create 5+ examples
4. Migration guide (for external users)

**Total: 6 weeks to production**

---

## 7. Example: Before & After

### Before (Phase 2 - named_points only)

```yaml
named_points:
  beam_front_center:
    part: beam
    face: ">Y"
    at: center

  left_arm_attach:
    from: beam_front_center
    offset: [-25, 0, 0]  # World coordinates!

operations:
  left_arm:
    type: transform
    input: arm
    transforms:
      - translate: left_arm_attach  # Just position, no orientation
      - rotate:  # Manual angle calculation required
          angle: 15
          axis: X
          origin: left_arm_attach  # Have to repeat!
```

### After (v3.0 - unified references)

```yaml
references:
  beam_front:
    type: face
    part: beam
    selector: ">Y"

  left_arm_mount:
    type: point
    from: beam_front
    offset: [-25, 0, 0]  # In beam_front's LOCAL frame! Z = outward from face

operations:
  left_arm:
    type: transform
    input: arm
    transforms:
      - align:
          this_ref: arm.base_face
          to_ref: beam_front
          orientation: normal  # Auto-aligns arm perpendicular to beam!
          offset: 2  # 2mm gap
      - translate:
          to: left_arm_mount
```

**Cleaner, more intuitive, orientation-aware.**

---

## Status

**Document Status:** ✅ **READY FOR REVIEW**

**Recommendation:** Implement this as TiaCAD v3.0 - break compatibility, gain clarity.

**Timeline:** 6 weeks to production-ready
**Tests Required:** ~130 new tests
**Breaking Changes:** Yes - but worth it for long-term maintainability
