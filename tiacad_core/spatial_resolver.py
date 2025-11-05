"""
Spatial Resolver - Unified reference resolution for TiaCAD v3.0

This module provides the SpatialResolver class that resolves reference
specifications (strings, dicts, lists) into SpatialRef objects.

The resolver handles:
- Absolute coordinates: [x, y, z] → SpatialRef(point)
- Named references: "mount_point" → lookup in references dict
- Dot notation: "part.face_top" → auto-generated part-local references
- Inline definitions: {type: face, part: x, selector: y} → extract from geometry
- Derived references: {from: ref, offset: [dx, dy, dz]} → offset in local frame

Philosophy: One unified resolver for all reference types. Clean, simple dispatch.
"""

from typing import Union, Dict, Any, Optional
import numpy as np
import logging

from tiacad_core.geometry.spatial_references import SpatialRef, Frame
from tiacad_core.part import PartRegistry

logger = logging.getLogger(__name__)


class SpatialResolverError(Exception):
    """Raised when spatial reference resolution fails"""
    pass


class SpatialResolver:
    """
    Resolves reference specifications to SpatialRef objects.

    Single responsibility: spec → SpatialRef
    Handles all reference types through clean dispatch.

    Args:
        registry: PartRegistry containing all parts
        references: Dict of user-defined references (name → spec)

    Example:
        resolver = SpatialResolver(part_registry, references_dict)

        # Resolve various specs
        ref1 = resolver.resolve([0, 0, 10])                    # Absolute point
        ref2 = resolver.resolve("mount_point")                 # Named reference
        ref3 = resolver.resolve("base.face_top")               # Part-local reference
        ref4 = resolver.resolve({type: "face", part: "base", selector: ">Z"})
    """

    def __init__(self, registry: PartRegistry, references: Optional[Dict[str, Any]] = None):
        """
        Initialize SpatialResolver.

        Args:
            registry: PartRegistry containing all parts
            references: Optional dict of user-defined references (name → spec)
        """
        self.registry = registry
        self.references = references or {}
        self._cache = {}  # Cache resolved references

    def resolve(self, spec: Union[str, dict, list, SpatialRef]) -> SpatialRef:
        """
        Resolve ANY reference spec to SpatialRef.

        Main dispatcher method - handles all input types.

        Args:
            spec: Reference specification:
                - List: [x, y, z] → simple point
                - String: "ref_name" or "part.ref_name"
                - Dict: {type: ..., part: ..., ...} → inline definition
                - SpatialRef: Already resolved, return as-is

        Returns:
            SpatialRef with position and optional orientation

        Raises:
            SpatialResolverError: If resolution fails

        Examples:
            # Absolute coordinates
            ref = resolver.resolve([10, 20, 30])

            # Named reference
            ref = resolver.resolve("mount_point")

            # Part-local auto-generated reference
            ref = resolver.resolve("base.face_top")

            # Inline face definition
            ref = resolver.resolve({
                "type": "face",
                "part": "base_plate",
                "selector": ">Z",
                "at": "center"
            })

            # Derived reference with offset
            ref = resolver.resolve({
                "type": "point",
                "from": "base.face_top",
                "offset": [10, 0, 5]
            })
        """
        # SpatialRef = already resolved, return as-is
        if isinstance(spec, SpatialRef):
            return spec

        # List = absolute point
        if isinstance(spec, list):
            if len(spec) != 3:
                raise SpatialResolverError(
                    f"Absolute coordinates must have exactly 3 values, got {len(spec)}"
                )
            try:
                return SpatialRef(
                    position=np.array([float(spec[0]), float(spec[1]), float(spec[2])]),
                    ref_type='point'
                )
            except (ValueError, TypeError) as e:
                raise SpatialResolverError(f"Invalid coordinate values: {e}")

        # String = reference name (dot notation or named)
        if isinstance(spec, str):
            return self._resolve_name(spec)

        # Dict = inline reference definition
        if isinstance(spec, dict):
            return self._resolve_dict(spec)

        raise SpatialResolverError(
            f"Invalid reference spec type: {type(spec)}. Expected list, string, dict, or SpatialRef."
        )

    def _resolve_name(self, name: str) -> SpatialRef:
        """
        Resolve named reference or dot notation.

        Handles:
        - Named references: "mount_point" → lookup in self.references
        - Dot notation: "part.ref_name" → part-local auto-generated references

        Uses caching to avoid redundant resolution.

        Args:
            name: Reference name (with or without dot notation)

        Returns:
            Resolved SpatialRef

        Raises:
            SpatialResolverError: If reference not found
        """
        # Check cache first
        if name in self._cache:
            logger.debug(f"Cache hit for reference '{name}'")
            return self._cache[name]

        # Check user-defined references
        if name in self.references:
            logger.debug(f"Resolving user-defined reference '{name}'")
            # Recursively resolve the spec (could be list, dict, or another string)
            result = self.resolve(self.references[name])
            self._cache[name] = result
            return result

        # Check part-local references (e.g., "base.face_top")
        if '.' in name:
            logger.debug(f"Resolving part-local reference '{name}'")
            part_name, ref_name = name.split('.', 1)

            # Check if part exists
            if not self.registry.exists(part_name):
                raise SpatialResolverError(
                    f"Part '{part_name}' not found in registry. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )

            part = self.registry.get(part_name)
            result = self._resolve_part_local(part, ref_name)
            self._cache[name] = result
            return result

        # Not found anywhere
        raise SpatialResolverError(
            f"Reference '{name}' not found. "
            f"Available named references: {', '.join(self.references.keys())}"
        )

    def _resolve_dict(self, spec: dict) -> SpatialRef:
        """
        Resolve inline reference definition.

        Handles different reference types:
        - point: Absolute or derived (with offset)
        - face: Extract from part geometry
        - edge: Extract from part geometry
        - axis: Defined by two points

        Args:
            spec: Dictionary with reference specification

        Returns:
            Resolved SpatialRef

        Raises:
            SpatialResolverError: If invalid specification
        """
        ref_type = spec.get('type', 'point')

        if ref_type == 'point':
            # Case 1: Absolute point
            if 'value' in spec:
                value = spec['value']
                if not isinstance(value, list) or len(value) != 3:
                    raise SpatialResolverError(
                        f"Point 'value' must be list of 3 coordinates, got: {value}"
                    )
                return SpatialRef(
                    position=np.array([float(value[0]), float(value[1]), float(value[2])]),
                    ref_type='point'
                )

            # Case 2: Offset from another reference
            elif 'from' in spec:
                if 'offset' not in spec:
                    raise SpatialResolverError(
                        "Derived reference must have both 'from' and 'offset' keys"
                    )

                # Resolve base reference (recursive)
                base = self.resolve(spec['from'])

                # Get offset
                offset = spec['offset']
                if not isinstance(offset, list) or len(offset) != 3:
                    raise SpatialResolverError(
                        f"Offset must be list of 3 values, got: {offset}"
                    )
                offset_arr = np.array([float(offset[0]), float(offset[1]), float(offset[2])])

                # Apply offset in base's local frame (if it has orientation)
                if base.orientation is not None:
                    frame = base.frame
                    world_offset = (
                        offset_arr[0] * frame.x_axis +
                        offset_arr[1] * frame.y_axis +
                        offset_arr[2] * frame.z_axis
                    )
                else:
                    # No orientation - offset in world coordinates
                    world_offset = offset_arr

                return SpatialRef(
                    position=base.position + world_offset,
                    orientation=None,  # Derived points don't inherit orientation
                    ref_type='point'
                )

            else:
                raise SpatialResolverError(
                    f"Point reference must have either 'value' or 'from'+'offset'. Got: {spec}"
                )

        elif ref_type == 'face':
            # Extract face reference from part geometry
            if 'part' not in spec or 'selector' not in spec:
                raise SpatialResolverError(
                    f"Face reference must have 'part' and 'selector'. Got: {spec}"
                )

            part_name = spec['part']
            if not self.registry.exists(part_name):
                raise SpatialResolverError(
                    f"Part '{part_name}' not found in registry. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )

            part = self.registry.get(part_name)
            selector = spec['selector']
            at = spec.get('at', 'center')  # Default to center

            return self._extract_face_ref(part, selector, at)

        elif ref_type == 'edge':
            # Extract edge reference from part geometry
            if 'part' not in spec or 'selector' not in spec:
                raise SpatialResolverError(
                    f"Edge reference must have 'part' and 'selector'. Got: {spec}"
                )

            part_name = spec['part']
            if not self.registry.exists(part_name):
                raise SpatialResolverError(
                    f"Part '{part_name}' not found in registry. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )

            part = self.registry.get(part_name)
            selector = spec['selector']
            at = spec.get('at', 'midpoint')  # Default to midpoint

            return self._extract_edge_ref(part, selector, at)

        elif ref_type == 'axis':
            # Axis defined by two points
            if 'from' not in spec or 'to' not in spec:
                raise SpatialResolverError(
                    f"Axis reference must have 'from' and 'to'. Got: {spec}"
                )

            # Resolve the two points
            from_spec = spec['from']
            to_spec = spec['to']

            # Handle both list and reference forms
            if isinstance(from_spec, list):
                from_pt = np.array([float(from_spec[0]), float(from_spec[1]), float(from_spec[2])])
            else:
                from_pt = self.resolve(from_spec).position

            if isinstance(to_spec, list):
                to_pt = np.array([float(to_spec[0]), float(to_spec[1]), float(to_spec[2])])
            else:
                to_pt = self.resolve(to_spec).position

            # Calculate direction
            direction = to_pt - from_pt
            length = np.linalg.norm(direction)
            if length < 1e-10:
                raise SpatialResolverError(
                    f"Axis 'from' and 'to' points are identical: {from_pt}"
                )
            direction = direction / length  # Normalize

            return SpatialRef(
                position=from_pt,
                orientation=direction,
                ref_type='axis'
            )

        else:
            raise SpatialResolverError(
                f"Unknown reference type: {ref_type}. "
                f"Valid types: point, face, edge, axis"
            )

    def _resolve_part_local(self, part, ref_name: str) -> SpatialRef:
        """
        Resolve auto-generated part-local references.

        Every part automatically provides these references:
        - 'center': Bounding box center
        - 'origin': Part origin (current position)
        - 'face_top', 'face_bottom', 'face_left', 'face_right', 'face_front', 'face_back'
        - 'axis_x', 'axis_y', 'axis_z'

        Args:
            part: Part object
            ref_name: Local reference name (e.g., 'face_top', 'center')

        Returns:
            Resolved SpatialRef

        Raises:
            SpatialResolverError: If reference name not recognized
        """
        if ref_name == 'center':
            # Bounding box center - use backend abstraction
            if part.backend is None:
                raise SpatialResolverError(
                    f"Part '{part.name}' has no backend - cannot get bounding box. "
                    "Parts must have a backend for spatial reference resolution."
                )
            bbox = part.backend.get_bounding_box(part.geometry)
            pos = np.array(bbox['center'])
            return SpatialRef(position=pos, ref_type='point')

        elif ref_name == 'origin':
            # Part's current position (origin)
            # Note: Part.current_position may not exist yet - use placeholder for now
            # TODO: Implement part.current_position tracking
            return SpatialRef(position=np.array([0.0, 0.0, 0.0]), ref_type='point')

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

            # Not a recognized face name
            raise SpatialResolverError(
                f"Unknown face reference: {ref_name}. "
                f"Valid faces: {', '.join(face_map.keys())}"
            )

        elif ref_name.startswith('axis_'):
            # Auto-generated axis references
            axis_map = {
                'axis_x': [1, 0, 0],
                'axis_y': [0, 1, 0],
                'axis_z': [0, 0, 1]
            }
            if ref_name in axis_map:
                direction = axis_map[ref_name]
                # Axis goes through part center
                center = self._resolve_part_local(part, 'center').position
                return SpatialRef(
                    position=center,
                    orientation=np.array(direction),
                    ref_type='axis'
                )

            # Not a recognized axis
            raise SpatialResolverError(
                f"Unknown axis reference: {ref_name}. "
                f"Valid axes: {', '.join(axis_map.keys())}"
            )

        else:
            raise SpatialResolverError(
                f"Unknown part-local reference: {ref_name}. "
                f"Valid references: center, origin, face_*, axis_*"
            )

    def _extract_face_ref(self, part, selector: str, at: str) -> SpatialRef:
        """
        Extract face reference from part geometry.

        Uses backend's face selection and spatial query methods.

        Args:
            part: Part object with geometry and backend
            selector: Face selector string (e.g., '>Z', '|X')
            at: Location on face ('center' for now, future: 'bounds_center', 'vertex_avg')

        Returns:
            SpatialRef with face position and normal

        Raises:
            SpatialResolverError: If face not found or extraction fails
        """
        try:
            # Require backend for spatial queries
            if part.backend is None:
                raise SpatialResolverError(
                    f"Part '{part.name}' has no backend - cannot extract face reference. "
                    "Parts must have a backend for spatial reference resolution."
                )

            # Select faces using backend
            faces = part.backend.select_faces(part.geometry, selector)

            if len(faces) == 0:
                raise SpatialResolverError(
                    f"Selector '{selector}' matched no faces on part '{part.name}'"
                )

            # Get first matching face
            face = faces[0]

            # Get face center using backend
            center_tuple = part.backend.get_face_center(face)
            center = np.array(center_tuple)

            # Get face normal using backend
            normal_tuple = part.backend.get_face_normal(face)
            normal = np.array(normal_tuple)

            # Normalize (should already be normalized, but just to be safe)
            normal_length = np.linalg.norm(normal)
            if normal_length > 1e-10:
                normal = normal / normal_length

            return SpatialRef(
                position=center,
                orientation=normal,
                ref_type='face'
            )

        except SpatialResolverError:
            raise
        except Exception as e:
            raise SpatialResolverError(
                f"Failed to extract face reference from part '{part.name}' "
                f"with selector '{selector}': {e}"
            )

    def _extract_edge_ref(self, part, selector: str, at: str) -> SpatialRef:
        """
        Extract edge reference from part geometry.

        Uses backend's edge selection and spatial query methods.

        Args:
            part: Part object with geometry and backend
            selector: Edge selector string (e.g., '|Z', '>X and >Y')
            at: Location on edge ('midpoint', 'start', 'end')

        Returns:
            SpatialRef with edge position and tangent

        Raises:
            SpatialResolverError: If edge not found or extraction fails
        """
        try:
            # Require backend for spatial queries
            if part.backend is None:
                raise SpatialResolverError(
                    f"Part '{part.name}' has no backend - cannot extract edge reference. "
                    "Parts must have a backend for spatial reference resolution."
                )

            # Select edges using backend
            edges = part.backend.select_edges(part.geometry, selector)

            if len(edges) == 0:
                raise SpatialResolverError(
                    f"Selector '{selector}' matched no edges on part '{part.name}'"
                )

            # Get first matching edge
            edge = edges[0]

            # Get position based on 'at' parameter using backend
            position_tuple = part.backend.get_edge_point(edge, at)
            position = np.array(position_tuple)

            # Get tangent using backend
            tangent_tuple = part.backend.get_edge_tangent(edge)
            tangent = np.array(tangent_tuple)

            # Normalize (should already be normalized, but just to be safe)
            tangent_length = np.linalg.norm(tangent)
            if tangent_length < 1e-10:
                raise SpatialResolverError(
                    f"Edge has zero length, cannot compute tangent"
                )
            tangent = tangent / tangent_length

            return SpatialRef(
                position=position,
                orientation=tangent,  # Tangent as primary orientation
                ref_type='edge'
            )

        except SpatialResolverError:
            raise
        except ValueError as e:
            # Convert backend ValueError to SpatialResolverError
            raise SpatialResolverError(
                f"Failed to extract edge reference from part '{part.name}' "
                f"with selector '{selector}': {e}"
            )
        except Exception as e:
            raise SpatialResolverError(
                f"Failed to extract edge reference from part '{part.name}' "
                f"with selector '{selector}': {e}"
            )

    def clear_cache(self):
        """Clear the resolution cache. Useful when parts or references change."""
        self._cache.clear()
        logger.debug("Spatial reference cache cleared")
