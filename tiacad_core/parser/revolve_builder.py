"""
RevolveBuilder - Execute revolve operations on 2D sketches

Creates 3D geometry by revolving a 2D sketch profile around an axis.
Useful for creating rotationally symmetric parts like cylinders, vases, and rings.

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
from .backend_utils import get_cadquery_backend

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker
    from ..geometry import GeometryBackend

logger = logging.getLogger(__name__)

_AXIS_VECTORS = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}


class RevolveBuilderError(TiaCADError):
    """Error during revolve operation"""
    def __init__(self, message: str, operation_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class RevolveBuilder:
    """
    Builds 3D geometry by revolving 2D sketches around an axis.

    Usage:
        builder = RevolveBuilder(registry, sketches, resolver, line_tracker)
        builder.execute_revolve_operation('vase', {
            'sketch': 'vase_profile',
            'axis': 'Z',
            'angle': 360
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 sketches: Dict[str, Sketch2D],
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None,
                 backend: Optional["GeometryBackend"] = None):
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

    def _validate_revolve_spec(
        self, name: str, resolved_spec: Dict[str, Any]
    ) -> Tuple[str, 'Sketch2D', str, float, List[float]]:
        """Validate revolve spec. Returns (sketch_name, sketch, axis, angle, origin)."""
        sketch_name = resolved_spec.get('sketch')
        if not sketch_name:
            line, col = self._get_line_info(['operations', name, 'sketch'])
            raise RevolveBuilderError(
                f"Revolve operation '{name}' missing required 'sketch' field",
                operation_name=name, line=line, column=col
            )

        if sketch_name not in self.sketches:
            line, col = self._get_line_info(['operations', name, 'sketch'])
            available = ', '.join(self.sketches.keys())
            raise RevolveBuilderError(
                f"Sketch '{sketch_name}' not found for revolve operation '{name}'. "
                f"Available sketches: {available}",
                operation_name=name, line=line, column=col
            )

        axis = resolved_spec.get('axis')
        if not axis:
            line, col = self._get_line_info(['operations', name, 'axis'])
            raise RevolveBuilderError(
                f"Revolve operation '{name}' missing required 'axis' field",
                operation_name=name, line=line, column=col
            )

        axis = str(axis).upper()
        if axis not in _AXIS_VECTORS:
            line, col = self._get_line_info(['operations', name, 'axis'])
            raise RevolveBuilderError(
                f"Invalid revolve axis '{axis}'. Must be X, Y, or Z",
                operation_name=name, line=line, column=col
            )

        angle = resolved_spec.get('angle', 360)
        if not isinstance(angle, (int, float)):
            line, col = self._get_line_info(['operations', name, 'angle'])
            raise RevolveBuilderError(
                f"Revolve angle must be a number, got {angle}",
                operation_name=name, line=line, column=col
            )

        origin = resolved_spec.get('origin', [0, 0, 0])
        if not isinstance(origin, list) or len(origin) != 3:
            line, col = self._get_line_info(['operations', name, 'origin'])
            raise RevolveBuilderError(
                f"Revolve origin must be [x, y, z], got {origin}",
                operation_name=name, line=line, column=col
            )

        return sketch_name, self.sketches[sketch_name], axis, angle, origin

    def execute_revolve_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a revolve operation.

        Creates a 3D part by revolving a 2D sketch profile around an axis.

        Args:
            name: Result part name
            spec: Revolve specification with sketch, axis, angle (default 360), origin (default [0,0,0])

        Raises:
            RevolveBuilderError: If operation fails
        """
        try:
            resolved_spec = self.resolver.resolve(spec)
            sketch_name, sketch, axis, angle, origin = self._validate_revolve_spec(
                name, resolved_spec
            )

            logger.info(f"Revolving sketch '{sketch_name}' {angle}° around {axis} axis")
            geometry = self._revolve_sketch(sketch, axis, angle, origin, name)

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
                },
                backend=self.backend or get_cadquery_backend(),
            )
            self.registry.add(part)
            logger.debug(f"Created revolved part '{name}' from sketch '{sketch_name}'")

        except RevolveBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise RevolveBuilderError(
                f"Failed to execute revolve operation '{name}': {str(e)}",
                operation_name=name, line=line, column=col
            ) from e

    def _make_sketch_workplane(self, sketch: Sketch2D) -> cq.Workplane:
        """Create a workplane for a sketch, applying origin offset if set."""
        wp = cq.Workplane(sketch.plane)
        if sketch.origin != (0, 0, 0):
            ox, oy, oz = sketch.origin
            offsets = {'XY': (ox, oy), 'XZ': (ox, oz), 'YZ': (oy, oz)}
            wp = wp.center(*offsets[sketch.plane])
        return wp

    def _revolve_shape_solid(
        self, shape, sketch: Sketch2D, angle: float,
        axis_start: cq.Vector, axis_end: cq.Vector
    ) -> cq.Workplane:
        """
        Build a 2D shape and revolve it using world-coordinate axis vectors.

        Uses Solid.revolve() with world coordinates instead of wp.revolve() to avoid
        axis-frame confusion: wp.revolve() interprets axis points relative to the
        workplane's current position (which may be shifted by shape.build()'s center()
        calls), whereas Solid.revolve() always uses world coordinates.
        """
        from cadquery.occ_impl.shapes import Solid as OccSolid
        wp = self._make_sketch_workplane(sketch)
        wp = shape.build(wp)
        wires = wp.ctx.pendingWires
        if not wires:
            raise RevolveBuilderError(
                f"No wires produced by sketch shape in sketch '{sketch.name}'",
                operation_name=sketch.name
            )
        face = cq.Face.makeFromWires(wires[0])
        solid = OccSolid.revolve(face, angle, axis_start, axis_end)
        return cq.Workplane(sketch.plane).newObject([solid])

    def _revolve_sketch(self, sketch: Sketch2D, axis: str, angle: float,
                        origin: List[float], context: str) -> cq.Workplane:
        """
        Revolve a sketch profile around an axis.

        Args:
            sketch: Sketch2D to revolve
            axis: Rotation axis (X, Y, or Z)
            angle: Rotation angle in degrees
            origin: Point the axis passes through (in world coordinates)
            context: Operation name for error messages

        Returns:
            CadQuery Workplane with revolved 3D geometry

        Raises:
            RevolveBuilderError: If revolution fails
        """
        try:
            add_shapes = [s for s in sketch.shapes if s.operation == 'add']
            subtract_shapes = [s for s in sketch.shapes if s.operation == 'subtract']
            ax, ay, az = _AXIS_VECTORS[axis]
            ox, oy, oz = origin
            axis_start = cq.Vector(ox, oy, oz)
            axis_end = cq.Vector(ox + ax, oy + ay, oz + az)

            geometry = self._revolve_shape_solid(add_shapes[0], sketch, angle, axis_start, axis_end)
            for shape in add_shapes[1:]:
                geometry = geometry.union(
                    self._revolve_shape_solid(shape, sketch, angle, axis_start, axis_end)
                )
            for shape in subtract_shapes:
                geometry = geometry.cut(
                    self._revolve_shape_solid(shape, sketch, angle, axis_start, axis_end)
                )

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

    def __repr__(self) -> str:
        return (
            f"RevolveBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
