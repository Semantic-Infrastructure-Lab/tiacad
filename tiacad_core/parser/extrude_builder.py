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
from ..sketch import Sketch2D
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver
from tiacad_core.sketch import Text2D
from .backend_utils import get_cadquery_backend

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker
    from ..geometry import GeometryBackend

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
                 line_tracker: Optional['LineTracker'] = None,
                 backend: Optional["GeometryBackend"] = None):
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
        self.backend = backend

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get line and column info for a YAML path."""
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def _validate_extrude_spec(self, name: str, spec: Dict[str, Any]):
        """Validate extrude spec fields. Returns (sketch, sketch_name, distance, direction, taper)."""
        def _err(field, msg):
            line, col = self._get_line_info(['operations', name, field])
            raise ExtrudeBuilderError(msg, operation_name=name, line=line, column=col)

        sketch_name = spec.get('sketch')
        if not sketch_name:
            _err('sketch', f"Extrude operation '{name}' missing required 'sketch' field")
        if sketch_name not in self.sketches:
            available = ', '.join(self.sketches.keys())
            _err('sketch', f"Sketch '{sketch_name}' not found for extrude operation '{name}'. Available sketches: {available}")
        sketch = self.sketches[sketch_name]

        distance = spec.get('distance')
        if distance is None:
            _err('distance', f"Extrude operation '{name}' missing required 'distance' field")
        if not isinstance(distance, (int, float)) or distance <= 0:
            _err('distance', f"Extrude distance must be positive number, got {distance}")

        direction = spec.get('direction')
        if direction is None:
            direction = self._default_direction(sketch.plane)
            logger.debug(f"Extrude '{name}': Auto-detected direction {direction} for {sketch.plane} plane")
        else:
            direction = str(direction).upper()
            if direction not in ['X', 'Y', 'Z']:
                _err('direction', f"Invalid extrude direction '{direction}'. Must be X, Y, or Z")

        taper = spec.get('taper', 0)
        if not isinstance(taper, (int, float)):
            _err('taper', f"Taper angle must be a number, got {taper}")

        return sketch, sketch_name, distance, direction, taper

    def execute_extrude_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute an extrude operation — creates 3D geometry by extruding a 2D sketch profile.

        Args:
            name: Result part name
            spec: Extrude spec (sketch, distance required; direction, taper optional)

        Raises:
            ExtrudeBuilderError: If operation fails
        """
        try:
            resolved_spec = self.resolver.resolve(spec)
            sketch, sketch_name, distance, direction, taper = self._validate_extrude_spec(name, resolved_spec)

            logger.info(f"Extruding sketch '{sketch_name}' by {distance} in {direction} direction"
                        + (f" with {taper}° taper" if taper != 0 else ""))

            geometry = self._extrude_sketch(sketch, distance, direction, taper, name)
            self.registry.add(Part(name=name, geometry=geometry, metadata={
                'source': 'extrude', 'sketch': sketch_name, 'operation_type': 'extrude',
                'distance': distance, 'direction': direction, 'taper': taper
            }, backend=self.backend or get_cadquery_backend()))
            logger.debug(f"Created extruded part '{name}' from sketch '{sketch_name}'")

        except ExtrudeBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise ExtrudeBuilderError(f"Failed to execute extrude operation '{name}': {str(e)}",
                                       operation_name=name, line=line, column=col) from e

    def _default_direction(self, plane: str) -> str:
        """Get default extrude direction for a sketch plane."""
        return self.DEFAULT_DIRECTIONS.get(plane, 'Z')

    def _make_sketch_workplane(self, plane: str, origin) -> cq.Workplane:
        """Create a workplane for the given plane, centered at origin if non-zero."""
        wp = cq.Workplane(plane)
        if origin != (0, 0, 0):
            if plane == 'XY':
                wp = wp.center(origin[0], origin[1])
            elif plane == 'XZ':
                wp = wp.center(origin[0], origin[2])
            elif plane == 'YZ':
                wp = wp.center(origin[1], origin[2])
        return wp

    def _build_shape_solid(self, shape, workplane, distance: float,
                           taper: float, factor: float = 1.0):
        """Build a 3D solid from a shape on workplane. Handles Text2D and regular shapes."""
        dist = distance * factor
        if isinstance(shape, Text2D):
            return shape.build(workplane, extrusion_distance=dist)
        built_wp = shape.build(workplane)
        return built_wp.extrude(dist) if taper == 0 else built_wp.extrude(dist, taper=taper)

    def _extrude_sketch(self, sketch: Sketch2D, distance: float,
                        direction: str, taper: float, context: str) -> cq.Workplane:
        """
        Extrude a sketch profile to create 3D geometry.
        Handles add/subtract shapes separately via boolean union/cut.
        """
        try:
            expected = self._default_direction(sketch.plane)
            if direction != expected:
                logger.warning(f"Extrude direction {direction} differs from sketch plane "
                               f"{sketch.plane} normal ({expected}). This may produce unexpected results.")

            add_shapes = [s for s in sketch.shapes if s.operation == 'add']
            subtract_shapes = [s for s in sketch.shapes if s.operation == 'subtract']

            geometry = self._build_shape_solid(
                add_shapes[0], self._make_sketch_workplane(sketch.plane, sketch.origin), distance, taper
            )
            for shape in add_shapes[1:]:
                geometry = geometry.union(self._build_shape_solid(
                    shape, self._make_sketch_workplane(sketch.plane, sketch.origin), distance, taper
                ))
            for shape in subtract_shapes:
                geometry = geometry.cut(self._build_shape_solid(
                    shape, self._make_sketch_workplane(sketch.plane, sketch.origin), distance, taper, factor=1.1
                ))

            logger.debug(f"Extruded {distance} units: {len(add_shapes)} add, "
                         f"{len(subtract_shapes)} subtract"
                         + (f", {taper}° taper" if taper != 0 else ""))
            return geometry

        except Exception as e:
            raise ExtrudeBuilderError(f"Failed to extrude sketch '{sketch.name}': {str(e)}",
                                       operation_name=context) from e

    def __repr__(self) -> str:
        return (
            f"ExtrudeBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
