"""
SketchBuilder - Build Sketch2D objects from YAML specifications

Parses sketch definitions from YAML and creates Sketch2D objects with Shape2D
components. Supports parameter resolution and line tracking for error messages.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING

from ..sketch import Sketch2D, Shape2D, Rectangle2D, Circle2D, Polygon2D, Text2D, SketchError
from .parameter_resolver import ParameterResolver

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)


class SketchBuilderError(SketchError):
    """Error during sketch building from YAML"""
    pass


class SketchBuilder:
    """
    Builds Sketch2D objects from YAML specifications.

    Similar to PartsBuilder, but creates 2D sketch profiles instead of 3D parts.
    Supports parameter resolution and enhanced error messages with line tracking.

    Usage:
        builder = SketchBuilder(param_resolver, line_tracker)
        sketches = builder.build_sketches(yaml_data['sketches'])
    """

    def __init__(self, parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize sketch builder.

        Args:
            parameter_resolver: Resolver for ${...} parameter expressions
            line_tracker: Optional line tracker for enhanced error messages
        """
        self.resolver = parameter_resolver
        self.line_tracker = line_tracker
        self.sketches: Dict[str, Sketch2D] = {}

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """
        Get line and column info for a YAML path.

        Args:
            path: YAML path as list (e.g., ['sketches', 'profile1', 'plane'])

        Returns:
            (line, column) tuple or (None, None) if not available
        """
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def build_sketches(self, sketches_spec: Dict[str, Dict]) -> Dict[str, Sketch2D]:
        """
        Build all sketches from YAML specification.

        Args:
            sketches_spec: Dictionary of sketch_name → sketch_definition

        Returns:
            Dictionary of sketch_name → Sketch2D object

        Raises:
            SketchBuilderError: If sketch building fails
        """
        for sketch_name, sketch_spec in sketches_spec.items():
            try:
                logger.info(f"Building sketch '{sketch_name}'")
                sketch = self.build_sketch(sketch_name, sketch_spec)
                self.sketches[sketch_name] = sketch
                logger.debug(f"Sketch '{sketch_name}' built successfully")
            except Exception as e:
                line, col = self._get_line_info(['sketches', sketch_name])
                raise SketchBuilderError(
                    f"Failed to build sketch '{sketch_name}': {str(e)}",
                    sketch_name=sketch_name,
                    line=line,
                    column=col
                ) from e

        logger.info(f"Built {len(self.sketches)} sketches successfully")
        return self.sketches

    def build_sketch(self, name: str, spec: Dict[str, Any]) -> Sketch2D:
        """
        Build a single Sketch2D from specification.

        Args:
            name: Sketch name
            spec: Sketch specification dict with 'plane', 'origin', 'shapes'

        Returns:
            Sketch2D object with built profile

        Raises:
            SketchBuilderError: If sketch spec is invalid
        """
        # Resolve parameters in spec
        resolved_spec = self.resolver.resolve(spec)

        # Extract sketch properties with defaults
        plane = resolved_spec.get('plane', 'XY')
        origin = resolved_spec.get('origin', [0, 0, 0])
        shapes_spec = resolved_spec.get('shapes', [])

        # Validate plane
        if not isinstance(plane, str) or plane.upper() not in ['XY', 'XZ', 'YZ']:
            line, col = self._get_line_info(['sketches', name, 'plane'])
            raise SketchBuilderError(
                f"Invalid plane '{plane}' for sketch '{name}'. "
                f"Must be XY, XZ, or YZ",
                sketch_name=name,
                line=line,
                column=col
            )

        # Validate origin
        if not isinstance(origin, list) or len(origin) != 3:
            line, col = self._get_line_info(['sketches', name, 'origin'])
            raise SketchBuilderError(
                f"Invalid origin '{origin}' for sketch '{name}'. "
                f"Must be [x, y, z]",
                sketch_name=name,
                line=line,
                column=col
            )

        # Validate shapes
        if not shapes_spec:
            line, col = self._get_line_info(['sketches', name, 'shapes'])
            raise SketchBuilderError(
                f"Sketch '{name}' must contain at least one shape",
                sketch_name=name,
                line=line,
                column=col
            )

        if not isinstance(shapes_spec, list):
            line, col = self._get_line_info(['sketches', name, 'shapes'])
            raise SketchBuilderError(
                f"Sketch '{name}' shapes must be a list",
                sketch_name=name,
                line=line,
                column=col
            )

        # Build shapes
        shapes = []
        for i, shape_spec in enumerate(shapes_spec):
            try:
                shape = self.build_shape(name, i, shape_spec)
                shapes.append(shape)
            except Exception as e:
                line, col = self._get_line_info(['sketches', name, 'shapes', i])
                raise SketchBuilderError(
                    f"Failed to build shape {i} in sketch '{name}': {str(e)}",
                    sketch_name=name,
                    line=line,
                    column=col
                ) from e

        # Create sketch
        sketch = Sketch2D(
            name=name,
            plane=plane,
            origin=tuple(origin),
            shapes=shapes
        )

        # Build the profile (combines all shapes)
        sketch.build_profile()

        logger.debug(
            f"Built sketch '{name}' on {plane} plane with {len(shapes)} shapes"
        )

        return sketch

    def build_shape(self, sketch_name: str, shape_index: int,
                    spec: Dict[str, Any]) -> Shape2D:
        """
        Build a Shape2D from specification.

        Args:
            sketch_name: Parent sketch name (for error messages)
            shape_index: Shape index in sketch (for error messages)
            spec: Shape specification dict

        Returns:
            Shape2D object (Rectangle2D, Circle2D, or Polygon2D)

        Raises:
            SketchBuilderError: If shape spec is invalid
        """
        # Get shape type
        if 'type' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'type']
            )
            raise SketchBuilderError(
                f"Shape {shape_index} in sketch '{sketch_name}' missing 'type' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        shape_type = spec['type']
        operation = spec.get('operation', 'add')

        # Validate operation
        if operation not in ['add', 'subtract']:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'operation']
            )
            raise SketchBuilderError(
                f"Invalid operation '{operation}' for shape {shape_index} "
                f"in sketch '{sketch_name}'. Must be 'add' or 'subtract'",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        # Build shape based on type
        try:
            if shape_type == 'rectangle':
                return self._build_rectangle(sketch_name, shape_index, spec, operation)
            elif shape_type == 'circle':
                return self._build_circle(sketch_name, shape_index, spec, operation)
            elif shape_type == 'polygon':
                return self._build_polygon(sketch_name, shape_index, spec, operation)
            elif shape_type == 'text':
                return self._build_text(sketch_name, shape_index, spec, operation)
            else:
                line, col = self._get_line_info(
                    ['sketches', sketch_name, 'shapes', shape_index, 'type']
                )
                raise SketchBuilderError(
                    f"Unknown shape type '{shape_type}' for shape {shape_index} "
                    f"in sketch '{sketch_name}'. "
                    f"Supported types: rectangle, circle, polygon, text",
                    sketch_name=sketch_name,
                    line=line,
                    column=col
                )
        except SketchBuilderError:
            # Re-raise SketchBuilderError as-is
            raise
        except Exception as e:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index]
            )
            raise SketchBuilderError(
                f"Error building {shape_type} shape {shape_index} "
                f"in sketch '{sketch_name}': {str(e)}",
                sketch_name=sketch_name,
                line=line,
                column=col
            ) from e

    def _build_rectangle(self, sketch_name: str, shape_index: int,
                        spec: Dict[str, Any], operation: str) -> Rectangle2D:
        """Build Rectangle2D from spec."""
        # Validate required fields
        if 'width' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'width']
            )
            raise SketchBuilderError(
                f"Rectangle shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'width' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        if 'height' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'height']
            )
            raise SketchBuilderError(
                f"Rectangle shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'height' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        width = spec['width']
        height = spec['height']
        center = spec.get('center', [0, 0])

        # Validate center
        if not isinstance(center, list) or len(center) != 2:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'center']
            )
            raise SketchBuilderError(
                f"Rectangle center must be [x, y], got {center}",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        return Rectangle2D(
            width=width,
            height=height,
            center=tuple(center),
            operation=operation
        )

    def _build_circle(self, sketch_name: str, shape_index: int,
                     spec: Dict[str, Any], operation: str) -> Circle2D:
        """Build Circle2D from spec."""
        # Validate required fields
        if 'radius' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'radius']
            )
            raise SketchBuilderError(
                f"Circle shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'radius' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        radius = spec['radius']
        center = spec.get('center', [0, 0])

        # Validate center
        if not isinstance(center, list) or len(center) != 2:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'center']
            )
            raise SketchBuilderError(
                f"Circle center must be [x, y], got {center}",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        return Circle2D(
            radius=radius,
            center=tuple(center),
            operation=operation
        )

    def _build_polygon(self, sketch_name: str, shape_index: int,
                      spec: Dict[str, Any], operation: str) -> Polygon2D:
        """Build Polygon2D from spec."""
        # Validate required fields
        if 'points' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'points']
            )
            raise SketchBuilderError(
                f"Polygon shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'points' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        points = spec['points']
        closed = spec.get('closed', True)

        # Validate points
        if not isinstance(points, list):
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'points']
            )
            raise SketchBuilderError(
                f"Polygon points must be a list, got {type(points).__name__}",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        # Convert points to tuples
        try:
            points_tuples = [tuple(p) for p in points]
        except Exception as e:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'points']
            )
            raise SketchBuilderError(
                f"Invalid polygon points format: {str(e)}",
                sketch_name=sketch_name,
                line=line,
                column=col
            ) from e

        return Polygon2D(
            points=points_tuples,
            closed=closed,
            operation=operation
        )

    def _build_text(self, sketch_name: str, shape_index: int,
                    spec: Dict[str, Any], operation: str) -> Text2D:
        """Build Text2D from spec."""
        # Validate required fields
        if 'text' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'text']
            )
            raise SketchBuilderError(
                f"Text shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'text' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        if 'size' not in spec:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'size']
            )
            raise SketchBuilderError(
                f"Text shape {shape_index} in sketch '{sketch_name}' "
                f"missing 'size' field",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        # Required parameters
        text = spec['text']
        size = spec['size']

        # Optional parameters with defaults
        font = spec.get('font', 'Liberation Sans')
        font_path = spec.get('font_path', None)
        style = spec.get('style', 'regular')
        halign = spec.get('halign', 'left')
        valign = spec.get('valign', 'baseline')
        position = spec.get('position', [0, 0])
        spacing = spec.get('spacing', 1.0)

        # Validate position
        if not isinstance(position, list) or len(position) != 2:
            line, col = self._get_line_info(
                ['sketches', sketch_name, 'shapes', shape_index, 'position']
            )
            raise SketchBuilderError(
                f"Text position must be [x, y], got {position}",
                sketch_name=sketch_name,
                line=line,
                column=col
            )

        return Text2D(
            text=text,
            size=size,
            font=font,
            font_path=font_path,
            style=style,
            halign=halign,
            valign=valign,
            position=tuple(position),
            spacing=spacing,
            operation=operation
        )

    def __repr__(self) -> str:
        return f"SketchBuilder(sketches={len(self.sketches)})"
