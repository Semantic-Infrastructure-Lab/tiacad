"""
ExtrudeBuilder - Execute extrude operations on 2D sketches

Creates 3D geometry by extruding 2D sketch profiles along a direction.
Supports tapered extrusions (draft angles) for manufacturability.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import cadquery as cq

from ..part import Part, PartRegistry
from ..sketch import Sketch2D, SketchError
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)


class ExtrudeBuilderError(TiaCADError):
    """Error during extrude operation"""
    def __init__(self, message: str, operation_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class ExtrudeBuilder:
    """
    Builds 3D geometry by extruding 2D sketches.

    Extrusion creates 3D solids by sweeping a 2D profile along a direction.
    Supports simple extrusion and tapered extrusion (draft angles).

    Usage:
        builder = ExtrudeBuilder(registry, sketches, resolver, line_tracker)
        builder.execute_extrude_operation('bracket', {
            'sketch': 'bracket_profile',
            'distance': 10,
            'direction': 'Z'
        })
    """

    # Default extrude directions for each plane
    DEFAULT_DIRECTIONS = {
        'XY': 'Z',  # XY plane extrudes along Z
        'XZ': 'Y',  # XZ plane extrudes along Y
        'YZ': 'X',  # YZ plane extrudes along X
    }

    def __init__(self,
                 part_registry: PartRegistry,
                 sketches: Dict[str, Sketch2D],
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize extrude builder.

        Args:
            part_registry: Registry to add extruded parts to
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

    def execute_extrude_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute an extrude operation.

        Creates a 3D part by extruding a 2D sketch profile.

        Args:
            name: Result part name
            spec: Extrude specification with:
                - sketch: Name of sketch to extrude (required)
                - distance: Extrusion distance (required)
                - direction: Extrude direction X|Y|Z (optional, auto-detected)
                - taper: Draft angle in degrees (optional, default: 0)

        Raises:
            ExtrudeBuilderError: If operation fails
        """
        try:
            # Resolve parameters
            resolved_spec = self.resolver.resolve(spec)

            # Validate and get sketch
            sketch_name = resolved_spec.get('sketch')
            if not sketch_name:
                line, col = self._get_line_info(['operations', name, 'sketch'])
                raise ExtrudeBuilderError(
                    f"Extrude operation '{name}' missing required 'sketch' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if sketch_name not in self.sketches:
                line, col = self._get_line_info(['operations', name, 'sketch'])
                available = ', '.join(self.sketches.keys())
                raise ExtrudeBuilderError(
                    f"Sketch '{sketch_name}' not found for extrude operation '{name}'. "
                    f"Available sketches: {available}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            sketch = self.sketches[sketch_name]

            # Validate and get distance
            distance = resolved_spec.get('distance')
            if distance is None:
                line, col = self._get_line_info(['operations', name, 'distance'])
                raise ExtrudeBuilderError(
                    f"Extrude operation '{name}' missing required 'distance' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(distance, (int, float)) or distance <= 0:
                line, col = self._get_line_info(['operations', name, 'distance'])
                raise ExtrudeBuilderError(
                    f"Extrude distance must be positive number, got {distance}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Get direction (default based on sketch plane)
            direction = resolved_spec.get('direction')
            if direction is None:
                direction = self._default_direction(sketch.plane)
                logger.debug(
                    f"Extrude '{name}': Auto-detected direction {direction} "
                    f"for {sketch.plane} plane"
                )
            else:
                direction = str(direction).upper()
                if direction not in ['X', 'Y', 'Z']:
                    line, col = self._get_line_info(['operations', name, 'direction'])
                    raise ExtrudeBuilderError(
                        f"Invalid extrude direction '{direction}'. Must be X, Y, or Z",
                        operation_name=name,
                        line=line,
                        column=col
                    )

            # Get taper angle (optional)
            taper = resolved_spec.get('taper', 0)
            if not isinstance(taper, (int, float)):
                line, col = self._get_line_info(['operations', name, 'taper'])
                raise ExtrudeBuilderError(
                    f"Taper angle must be a number, got {taper}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Build geometry
            logger.info(
                f"Extruding sketch '{sketch_name}' by {distance} in {direction} direction"
                + (f" with {taper}° taper" if taper != 0 else "")
            )

            geometry = self._extrude_sketch(sketch, distance, direction, taper, name)

            # Create part
            part = Part(
                name=name,
                geometry=geometry,
                metadata={
                    'source': 'extrude',
                    'sketch': sketch_name,
                    'operation_type': 'extrude',
                    'distance': distance,
                    'direction': direction,
                    'taper': taper
                }
            )

            # Add to registry
            self.registry.add(part)
            logger.debug(f"Created extruded part '{name}' from sketch '{sketch_name}'")

        except ExtrudeBuilderError:
            # Re-raise ExtrudeBuilderError as-is
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise ExtrudeBuilderError(
                f"Failed to execute extrude operation '{name}': {str(e)}",
                operation_name=name,
                line=line,
                column=col
            ) from e

    def _default_direction(self, plane: str) -> str:
        """
        Get default extrude direction for a sketch plane.

        Args:
            plane: Sketch plane (XY, XZ, or YZ)

        Returns:
            Default direction (X, Y, or Z)
        """
        return self.DEFAULT_DIRECTIONS.get(plane, 'Z')

    def _extrude_sketch(self, sketch: Sketch2D, distance: float,
                       direction: str, taper: float, context: str) -> cq.Workplane:
        """
        Extrude a sketch profile to create 3D geometry.

        Handles both simple extrusion and complex sketches with subtract operations.
        For sketches with holes/subtracts, extrudes additive and subtractive shapes
        separately, then performs boolean operations.

        Args:
            sketch: Sketch2D to extrude
            distance: Extrusion distance
            direction: Extrusion direction (X, Y, or Z)
            taper: Draft angle in degrees (0 = no taper)
            context: Operation name for error messages

        Returns:
            CadQuery Workplane with extruded 3D geometry

        Raises:
            ExtrudeBuilderError: If extrusion fails
        """
        try:
            # Check if requested direction matches plane normal
            expected_direction = self._default_direction(sketch.plane)
            if direction != expected_direction:
                logger.warning(
                    f"Extrude direction {direction} differs from sketch plane {sketch.plane} "
                    f"normal ({expected_direction}). This may produce unexpected results."
                )

            # Separate shapes by operation
            from ..sketch import Shape2D
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

            # Build and extrude first additive shape
            base_wp = add_shapes[0].build(base_wp)
            if taper == 0:
                geometry = base_wp.extrude(distance)
            else:
                geometry = base_wp.extrude(distance, taper=taper)

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
                if taper == 0:
                    shape_solid = shape_wp.extrude(distance)
                else:
                    shape_solid = shape_wp.extrude(distance, taper=taper)
                geometry = geometry.union(shape_solid)

            # Subtract shapes (make holes that go all the way through)
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
                # Extrude slightly longer to ensure clean cut through
                cut_solid = shape_wp.extrude(distance * 1.1)
                geometry = geometry.cut(cut_solid)

            logger.debug(
                f"Extruded {distance} units: {len(add_shapes)} add, "
                f"{len(subtract_shapes)} subtract"
                + (f", {taper}° taper" if taper != 0 else "")
            )

            return geometry

        except Exception as e:
            raise ExtrudeBuilderError(
                f"Failed to extrude sketch '{sketch.name}': {str(e)}",
                operation_name=context
            ) from e

    def __repr__(self) -> str:
        return (
            f"ExtrudeBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
