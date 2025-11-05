"""
PointResolver - Resolve point expressions to 3D coordinates

Resolves various point specifications:
1. Absolute coordinates: [x, y, z]
2. Dot notation: "part_name.face('>Z').center"
3. Offset notation: {from: point, offset: [x, y, z]}

Usage:
    registry = PartRegistry()
    resolver = PointResolver(registry)

    # Absolute coordinates
    point = resolver.resolve([10, 20, 30])  # → (10, 20, 30)

    # Dot notation
    point = resolver.resolve("beam.face('>Z').center")  # → (x, y, z)

    # With offset
    point = resolver.resolve({
        'from': "beam.face('>Z').center",
        'offset': [0, 0, 5]
    })
"""

import re
import logging
from typing import Union, Tuple, Dict, List, Any
from .part import PartRegistry
from .utils.geometry import get_center

logger = logging.getLogger(__name__)


class PointResolverError(Exception):
    """Raised when point resolution fails"""
    pass


class PointResolver:
    """
    Resolves point expressions to 3D coordinates.

    Supports:
    - Absolute coordinates: [x, y, z]
    - Dot notation: "part.face('>Z').center"
    - Offset notation: {from: point, offset: [dx, dy, dz]}
    """

    def __init__(self, part_registry: PartRegistry, named_points: Dict[str, Tuple[float, float, float]] = None):
        """
        Initialize PointResolver with part registry and optional named points.

        Args:
            part_registry: Registry containing all parts
            named_points: Optional dictionary of named points (name -> (x,y,z))
        """
        self.registry = part_registry
        self.named_points = named_points or {}

    def resolve(self, point_spec: Union[List[float], str, Dict[str, Any]]) -> Tuple[float, float, float]:
        """
        Resolve a point specification to 3D coordinates.

        Args:
            point_spec: Point specification (list, string, or dict)

        Returns:
            Tuple of (x, y, z) coordinates

        Raises:
            PointResolverError: If resolution fails
        """
        # Case 1: Absolute coordinates [x, y, z]
        if isinstance(point_spec, list):
            return self._resolve_absolute(point_spec)

        # Case 2: Dictionary - could be offset or geometric reference
        if isinstance(point_spec, dict):
            # Check if it's an offset notation {from: ..., offset: [...]}
            if 'from' in point_spec and 'offset' in point_spec:
                return self._resolve_offset(point_spec)
            # Check if it's a geometric reference {part: ..., face/edge/vertex: ..., at: ...}
            elif 'part' in point_spec:
                return self._resolve_geometric_dict(point_spec)
            else:
                raise PointResolverError(
                    f"Invalid dict specification. Expected either:\n"
                    f"  - Offset: {{from: point, offset: [dx,dy,dz]}}\n"
                    f"  - Geometric: {{part: name, face/edge/vertex: selector, at: location}}\n"
                    f"Got: {point_spec}"
                )

        # Case 3: String - either named point or dot notation
        if isinstance(point_spec, str):
            # Check if it's a named point first (simple identifier, no dots or parentheses)
            if point_spec in self.named_points:
                logger.debug(f"Resolved named point '{point_spec}' to {self.named_points[point_spec]}")
                return self.named_points[point_spec]

            # Otherwise try dot notation "part.face('>Z').center"
            return self._resolve_dot_notation(point_spec)

        raise PointResolverError(
            f"Invalid point specification type: {type(point_spec)}. "
            f"Expected list, string, or dict."
        )

    def _resolve_absolute(self, coords: List[float]) -> Tuple[float, float, float]:
        """
        Resolve absolute coordinates.

        Args:
            coords: List of [x, y, z] coordinates

        Returns:
            Tuple of (x, y, z)

        Raises:
            PointResolverError: If not exactly 3 coordinates
        """
        if len(coords) != 3:
            raise PointResolverError(
                f"Absolute coordinates must have exactly 3 values, got {len(coords)}"
            )

        try:
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        except (ValueError, TypeError) as e:
            raise PointResolverError(f"Invalid coordinate values: {e}")

    def _resolve_offset(self, offset_spec: Dict[str, Any]) -> Tuple[float, float, float]:
        """
        Resolve offset notation {from: point, offset: [dx, dy, dz]}.

        Args:
            offset_spec: Dictionary with 'from' and 'offset' keys

        Returns:
            Tuple of (x, y, z) with offset applied

        Raises:
            PointResolverError: If invalid offset specification
        """
        if 'from' not in offset_spec:
            raise PointResolverError("Offset specification must have 'from' key")

        if 'offset' not in offset_spec:
            raise PointResolverError("Offset specification must have 'offset' key")

        # Resolve base point (recursive)
        base_point = self.resolve(offset_spec['from'])

        # Get offset
        offset = offset_spec['offset']
        if not isinstance(offset, list) or len(offset) != 3:
            raise PointResolverError(
                f"Offset must be list of 3 values, got: {offset}"
            )

        try:
            dx, dy, dz = float(offset[0]), float(offset[1]), float(offset[2])
        except (ValueError, TypeError) as e:
            raise PointResolverError(f"Invalid offset values: {e}")

        return (
            base_point[0] + dx,
            base_point[1] + dy,
            base_point[2] + dz
        )

    def _resolve_dot_notation(self, expression: str) -> Tuple[float, float, float]:
        """
        Resolve dot notation: "part_name.face('>Z').center"

        Format: part_name.feature(selector).location

        Args:
            expression: Dot notation string

        Returns:
            Tuple of (x, y, z) coordinates

        Raises:
            PointResolverError: If invalid expression or part not found
        """
        # Parse the expression
        parsed = self._parse_dot_notation(expression)

        # Get the part
        part_name = parsed['part']
        if not self.registry.exists(part_name):
            raise PointResolverError(
                f"Part '{part_name}' not found in registry. "
                f"Available parts: {', '.join(self.registry.list_parts())}"
            )

        part = self.registry.get(part_name)

        # Get the feature (face/edge/vertex)
        feature_type = parsed['feature']
        selector = parsed['selector']

        selected = self._select_feature(part.geometry, feature_type, selector)

        # Get the location (center/min/max/start/end)
        location = parsed['location']
        coords = self._get_location(selected, feature_type, location)

        return coords

    def _resolve_geometric_dict(self, spec: Dict[str, Any]) -> Tuple[float, float, float]:
        """
        Resolve geometric dictionary specification.

        Format: {part: name, face/edge/vertex: selector, at: location}
        Example: {part: "beam", face: ">Z", at: "center"}

        Args:
            spec: Dictionary with part, feature, and location

        Returns:
            Tuple of (x, y, z) coordinates

        Raises:
            PointResolverError: If invalid specification or part not found
        """
        # Get part name
        part_name = spec.get('part')
        if not part_name:
            raise PointResolverError("Geometric reference must have 'part' key")

        if not self.registry.exists(part_name):
            raise PointResolverError(
                f"Part '{part_name}' not found in registry. "
                f"Available parts: {', '.join(self.registry.list_parts())}"
            )

        part = self.registry.get(part_name)

        # Determine feature type and selector
        feature_type = None
        selector = None

        if 'face' in spec:
            feature_type = 'face'
            selector = spec['face']
        elif 'edge' in spec:
            feature_type = 'edge'
            selector = spec['edge']
        elif 'vertex' in spec:
            feature_type = 'vertex'
            selector = spec['vertex']
        else:
            raise PointResolverError(
                f"Geometric reference must have one of: 'face', 'edge', or 'vertex'. Got: {spec}"
            )

        # Get location
        location = spec.get('at', 'center')  # Default to center

        # Select feature and get location
        selected = self._select_feature(part.geometry, feature_type, selector)
        coords = self._get_location(selected, feature_type, location)

        return coords

    def _parse_dot_notation(self, expression: str) -> Dict[str, str]:
        """
        Parse dot notation expression.

        Format: part_name.feature(selector).location
        Example: "beam.face('>Z').center"

        Args:
            expression: Dot notation string

        Returns:
            Dict with keys: part, feature, selector, location

        Raises:
            PointResolverError: If invalid format
        """
        # Pattern: part_name.feature(selector).location
        pattern = r"^(\w+)\.(face|edge|vertex)\('([^']+)'\)\.(center|min|max|start|end)$"

        match = re.match(pattern, expression.strip())
        if not match:
            raise PointResolverError(
                f"Invalid dot notation: '{expression}'. "
                f"Expected format: part_name.feature('selector').location\n"
                f"Example: beam.face('>Z').center"
            )

        part_name, feature, selector, location = match.groups()

        return {
            'part': part_name,
            'feature': feature,
            'selector': selector,
            'location': location
        }

    def _select_feature(self, geometry, feature_type: str, selector: str):
        """
        Select feature from geometry using selector.

        Args:
            geometry: CadQuery Workplane
            feature_type: 'face', 'edge', or 'vertex'
            selector: Selector string (e.g., '>Z')

        Returns:
            Selected geometry (CadQuery Workplane)

        Raises:
            PointResolverError: If selection fails
        """
        try:
            if feature_type == 'face':
                # Use CadQuery directly - it returns a Workplane
                selected = geometry.faces(selector)
            elif feature_type == 'edge':
                selected = geometry.edges(selector)
            elif feature_type == 'vertex':
                selected = geometry.vertices(selector)
            else:
                raise PointResolverError(f"Unknown feature type: {feature_type}")

            # Check that something was selected
            if selected.size() == 0:
                raise PointResolverError(
                    f"Selector '{selector}' matched no {feature_type} features"
                )

            return selected
        except PointResolverError:
            raise
        except Exception as e:
            raise PointResolverError(f"Feature selection failed: {e}")

    def _get_location(self, selected, feature_type: str, location: str) -> Tuple[float, float, float]:
        """
        Get specific location from selected feature.

        Args:
            selected: Selected CadQuery geometry
            feature_type: Type of feature
            location: Location type (center/min/max/start/end)

        Returns:
            Tuple of (x, y, z) coordinates

        Raises:
            PointResolverError: If location extraction fails
        """
        try:
            if location == 'center':
                return self._get_center(selected)

            elif location == 'min':
                bbox = selected.val().BoundingBox()
                return (bbox.xmin, bbox.ymin, bbox.zmin)

            elif location == 'max':
                bbox = selected.val().BoundingBox()
                return (bbox.xmax, bbox.ymax, bbox.zmax)

            elif location == 'start':
                if feature_type != 'edge':
                    raise PointResolverError(
                        f"'.start' only valid for edges, not {feature_type}"
                    )
                point = selected.val().startPoint()
                return (point.x, point.y, point.z)

            elif location == 'end':
                if feature_type != 'edge':
                    raise PointResolverError(
                        f"'.end' only valid for edges, not {feature_type}"
                    )
                point = selected.val().endPoint()
                return (point.x, point.y, point.z)

            else:
                raise PointResolverError(f"Unknown location: {location}")

        except PointResolverError:
            raise
        except Exception as e:
            raise PointResolverError(f"Location extraction failed: {e}")

    def _get_center(self, selected) -> Tuple[float, float, float]:
        """
        Get center point of selected feature

        Note:
            Uses shared geometry utility to avoid code duplication.
            Handles both Center() method and bounding box fallback.
        """
        try:
            # Try CadQuery's Center() method first
            center = selected.val().Center()
            return (center.x, center.y, center.z)
        except AttributeError:
            # Fallback to shared utility (uses bounding box)
            logger.debug("Feature has no Center(), using bounding box")
            return get_center(selected)
