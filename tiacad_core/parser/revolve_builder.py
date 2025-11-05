"""
RevolveBuilder - Execute revolve operations on 2D sketches

Creates 3D geometry by revolving a 2D sketch profile around an axis.
Useful for creating cylindrical and rotational symmetric parts.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import cadquery as cq

from ..part import Part, PartRegistry
from ..sketch import Sketch2D
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)


class RevolveBuilderError(TiaCADError):
    """Error during revolve operation"""
    def __init__(self, message: str, operation_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class RevolveBuilder:
    """
    Builds 3D geometry by revolving 2D sketches around an axis.

    Revolution creates rotationally symmetric parts like bottles, cylinders,
    bowls, and other turned shapes.

    Usage:
        builder = RevolveBuilder(registry, sketches, resolver, line_tracker)
        builder.execute_revolve_operation('bottle', {
            'sketch': 'bottle_profile',
            'axis': 'Z',
            'angle': 360
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 sketches: Dict[str, Sketch2D],
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize revolve builder.

        Args:
            part_registry: Registry to add revolved parts to
            sketches: Dictionary of available sketches (name → Sketch2D)
            parameter_resolver: Resolver for ${...} parameter expressions
            line_tracker: Optional line tracker for enhanced error messages
        """
        self.registry = part_registry
        self.sketches = sketches
        self.resolver = parameter_resolver
        self.line_tracker = line_tracker

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get line and column info for a YAML path."""
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def execute_revolve_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a revolve operation.

        Creates a 3D part by revolving a 2D sketch profile around an axis.

        Args:
            name: Result part name
            spec: Revolve specification with:
                - sketch: Name of sketch to revolve (required)
                - axis: Rotation axis X|Y|Z (required)
                - angle: Rotation angle in degrees (default: 360)
                - origin: Point axis passes through (default: [0,0,0])

        Raises:
            RevolveBuilderError: If operation fails
        """
        try:
            # Resolve parameters
            resolved_spec = self.resolver.resolve(spec)

            # Validate and get sketch
            sketch_name = resolved_spec.get('sketch')
            if not sketch_name:
                line, col = self._get_line_info(['operations', name, 'sketch'])
                raise RevolveBuilderError(
                    f"Revolve operation '{name}' missing required 'sketch' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if sketch_name not in self.sketches:
                line, col = self._get_line_info(['operations', name, 'sketch'])
                available = ', '.join(self.sketches.keys())
                raise RevolveBuilderError(
                    f"Sketch '{sketch_name}' not found for revolve operation '{name}'. "
                    f"Available sketches: {available}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            sketch = self.sketches[sketch_name]

            # Validate and get axis
            axis = resolved_spec.get('axis')
            if not axis:
                line, col = self._get_line_info(['operations', name, 'axis'])
                raise RevolveBuilderError(
                    f"Revolve operation '{name}' missing required 'axis' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            axis = str(axis).upper()
            if axis not in ['X', 'Y', 'Z']:
                line, col = self._get_line_info(['operations', name, 'axis'])
                raise RevolveBuilderError(
                    f"Invalid revolve axis '{axis}'. Must be X, Y, or Z",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Get angle (default 360 for full revolution)
            angle = resolved_spec.get('angle', 360)
            if not isinstance(angle, (int, float)):
                line, col = self._get_line_info(['operations', name, 'angle'])
                raise RevolveBuilderError(
                    f"Revolve angle must be a number, got {angle}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Get origin point (axis passes through this point)
            origin = resolved_spec.get('origin', [0, 0, 0])
            if not isinstance(origin, list) or len(origin) != 3:
                line, col = self._get_line_info(['operations', name, 'origin'])
                raise RevolveBuilderError(
                    f"Revolve origin must be [x, y, z], got {origin}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Build geometry
            logger.info(
                f"Revolving sketch '{sketch_name}' {angle}° around {axis} axis"
            )

            geometry = self._revolve_sketch(sketch, axis, angle, origin, name)

            # Create part
            part = Part(
                name=name,
                geometry=geometry,
                metadata={
                    'source': 'revolve',
                    'sketch': sketch_name,
                    'operation_type': 'revolve',
                    'axis': axis,
                    'angle': angle,
                    'origin': origin
                }
            )

            # Add to registry
            self.registry.add(part)
            logger.debug(f"Created revolved part '{name}' from sketch '{sketch_name}'")

        except RevolveBuilderError:
            # Re-raise RevolveBuilderError as-is
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise RevolveBuilderError(
                f"Failed to execute revolve operation '{name}': {str(e)}",
                operation_name=name,
                line=line,
                column=col
            ) from e

    def _revolve_sketch(self, sketch: Sketch2D, axis: str, angle: float,
                       origin: List[float], context: str) -> cq.Workplane:
        """
        Revolve a sketch profile around an axis.

        Args:
            sketch: Sketch2D to revolve
            axis: Rotation axis (X, Y, or Z)
            angle: Rotation angle in degrees
            origin: Point the axis passes through
            context: Operation name for error messages

        Returns:
            CadQuery Workplane with revolved 3D geometry

        Raises:
            RevolveBuilderError: If revolution fails
        """
        try:
            # Separate shapes by operation
            add_shapes = [s for s in sketch.shapes if s.operation == 'add']
            subtract_shapes = [s for s in sketch.shapes if s.operation == 'subtract']

            # Build base geometry from additive shapes
            base_wp = cq.Workplane(sketch.plane)
            if sketch.origin != (0, 0, 0):
                if sketch.plane == 'XY':
                    base_wp = base_wp.center(sketch.origin[0], sketch.origin[1])
                elif sketch.plane == 'XZ':
                    base_wp = base_wp.center(sketch.origin[0], sketch.origin[2])
                elif sketch.plane == 'YZ':
                    base_wp = base_wp.center(sketch.origin[1], sketch.origin[2])

            # Build and revolve first additive shape
            base_wp = add_shapes[0].build(base_wp)

            # CadQuery revolve: axis is a tuple (x,y,z) representing axis direction
            axis_vector = self._get_axis_vector(axis)

            # Revolve around axis
            # Note: CadQuery's revolve uses the workplane's coordinate system
            geometry = base_wp.revolve(angle, axis_vector)

            # Union remaining additive shapes
            for shape in add_shapes[1:]:
                shape_wp = cq.Workplane(sketch.plane)
                if sketch.origin != (0, 0, 0):
                    if sketch.plane == 'XY':
                        shape_wp = shape_wp.center(sketch.origin[0], sketch.origin[1])
                    elif sketch.plane == 'XZ':
                        shape_wp = shape_wp.center(sketch.origin[0], sketch.origin[2])
                    elif sketch.plane == 'YZ':
                        shape_wp = shape_wp.center(sketch.origin[1], sketch.origin[2])
                shape_wp = shape.build(shape_wp)
                shape_solid = shape_wp.revolve(angle, axis_vector)
                geometry = geometry.union(shape_solid)

            # Subtract shapes (revolve holes)
            for shape in subtract_shapes:
                shape_wp = cq.Workplane(sketch.plane)
                if sketch.origin != (0, 0, 0):
                    if sketch.plane == 'XY':
                        shape_wp = shape_wp.center(sketch.origin[0], sketch.origin[1])
                    elif sketch.plane == 'XZ':
                        shape_wp = shape_wp.center(sketch.origin[0], sketch.origin[2])
                    elif sketch.plane == 'YZ':
                        shape_wp = shape_wp.center(sketch.origin[1], sketch.origin[2])
                shape_wp = shape.build(shape_wp)
                cut_solid = shape_wp.revolve(angle, axis_vector)
                geometry = geometry.cut(cut_solid)

            logger.debug(
                f"Revolved {angle}°: {len(add_shapes)} add, "
                f"{len(subtract_shapes)} subtract"
            )

            return geometry

        except Exception as e:
            raise RevolveBuilderError(
                f"Failed to revolve sketch '{sketch.name}': {str(e)}",
                operation_name=context
            ) from e

    def _get_axis_vector(self, axis: str) -> Tuple[float, float, float]:
        """
        Get axis vector for revolution.

        Args:
            axis: Axis name (X, Y, or Z)

        Returns:
            Axis vector tuple
        """
        axis_map = {
            'X': (1, 0, 0),
            'Y': (0, 1, 0),
            'Z': (0, 0, 1)
        }
        return axis_map[axis]

    def __repr__(self) -> str:
        return (
            f"RevolveBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
