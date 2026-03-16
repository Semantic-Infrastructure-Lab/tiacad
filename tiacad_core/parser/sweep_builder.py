"""
SweepBuilder - Execute sweep operations on 2D sketches

Creates 3D geometry by sweeping a 2D sketch profile along a path.
Useful for creating pipes, rails, and complex curved shapes.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import cadquery as cq
from cadquery import Wire, Edge

from ..part import Part, PartRegistry
from ..sketch import Sketch2D
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)


class SweepBuilderError(TiaCADError):
    """Error during sweep operation"""
    def __init__(self, message: str, operation_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class SweepBuilder:
    """
    Builds 3D geometry by sweeping 2D sketches along a path.

    Sweep creates complex curved shapes by moving a cross-section profile
    along a path curve.

    Usage:
        builder = SweepBuilder(registry, sketches, resolver, line_tracker)
        builder.execute_sweep_operation('pipe', {
            'profile': 'pipe_cross_section',
            'path': [[0,0,0], [10,0,0], [10,10,0], [10,10,10]]
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 sketches: Dict[str, Sketch2D],
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize sweep builder.

        Args:
            part_registry: Registry to add swept parts to
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

    def _validate_sweep_spec(
        self, name: str, resolved_spec: Dict[str, Any]
    ) -> Tuple[str, Optional[List], Optional[str]]:
        """Validate sweep spec and return (profile_name, path_points, path_sketch_name)."""
        profile_name = resolved_spec.get('profile')
        if not profile_name:
            line, col = self._get_line_info(['operations', name, 'profile'])
            raise SweepBuilderError(
                f"Sweep operation '{name}' missing required 'profile' field",
                operation_name=name, line=line, column=col
            )

        if profile_name not in self.sketches:
            line, col = self._get_line_info(['operations', name, 'profile'])
            available = ', '.join(self.sketches.keys())
            raise SweepBuilderError(
                f"Profile sketch '{profile_name}' not found for sweep operation '{name}'. "
                f"Available sketches: {available}",
                operation_name=name, line=line, column=col
            )

        path_points = resolved_spec.get('path')
        path_sketch_name = resolved_spec.get('path_sketch')

        if not path_points and not path_sketch_name:
            line, col = self._get_line_info(['operations', name])
            raise SweepBuilderError(
                f"Sweep operation '{name}' must have either 'path' or 'path_sketch'",
                operation_name=name, line=line, column=col
            )

        if path_points and path_sketch_name:
            line, col = self._get_line_info(['operations', name])
            raise SweepBuilderError(
                f"Sweep operation '{name}' cannot have both 'path' and 'path_sketch'",
                operation_name=name, line=line, column=col
            )

        if path_points:
            if not isinstance(path_points, list) or len(path_points) < 2:
                line, col = self._get_line_info(['operations', name, 'path'])
                raise SweepBuilderError(
                    "Sweep path must be a list of at least 2 points",
                    operation_name=name, line=line, column=col
                )
            for i, point in enumerate(path_points):
                if not isinstance(point, list) or len(point) != 3:
                    line, col = self._get_line_info(['operations', name, 'path', i])
                    raise SweepBuilderError(
                        f"Path point {i} must be [x, y, z], got {point}",
                        operation_name=name, line=line, column=col
                    )

        return profile_name, path_points, path_sketch_name

    def execute_sweep_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a sweep operation.

        Creates a 3D part by sweeping a 2D sketch profile along a path.

        Args:
            name: Result part name
            spec: Sweep specification with:
                - profile: Name of sketch to sweep (required)
                - path: List of 3D points defining path OR
                - path_sketch: Name of sketch defining path

        Raises:
            SweepBuilderError: If operation fails
        """
        try:
            resolved_spec = self.resolver.resolve(spec)
            profile_name, path_points, path_sketch_name = self._validate_sweep_spec(
                name, resolved_spec
            )
            profile_sketch = self.sketches[profile_name]

            logger.info(
                f"Sweeping profile '{profile_name}' along path "
                f"({'points' if path_points else 'sketch'})"
            )
            geometry = self._sweep_sketch(profile_sketch, path_points, path_sketch_name, name)

            part = Part(
                name=name,
                geometry=geometry,
                metadata={
                    'source': 'sweep',
                    'profile': profile_name,
                    'operation_type': 'sweep',
                    'path_type': 'points' if path_points else 'sketch'
                }
            )
            self.registry.add(part)
            logger.debug(f"Created swept part '{name}' from profile '{profile_name}'")

        except SweepBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise SweepBuilderError(
                f"Failed to execute sweep operation '{name}': {str(e)}",
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

    def _sweep_shape_solid(
        self, shape, sketch: Sketch2D, path_wire: Wire
    ) -> cq.Workplane:
        """Build a single shape on a workplane and sweep it along the path.

        Tries a direct polyline sweep first (preserves sharp corners).
        Falls back to a spline approximation if OCCT can't handle the path
        geometry (e.g. sharp 3D corners with non-planar direction changes).
        """
        wp = self._make_sketch_workplane(sketch)
        wp = shape.build(wp)
        try:
            return wp.sweep(path_wire)
        except Exception:
            # Sharp 3D corners can fail in OCCT; retry with a spline path
            pts = [v.Center() for v in path_wire.Vertices()]
            spline_wire = Wire.assembleEdges([Edge.makeSpline(pts)])
            wp2 = self._make_sketch_workplane(sketch)
            wp2 = shape.build(wp2)
            return wp2.sweep(spline_wire)

    def _sweep_sketch(self, profile_sketch: Sketch2D,
                      path_points: Optional[List[List[float]]],
                      path_sketch_name: Optional[str],
                      context: str) -> cq.Workplane:
        """
        Sweep a profile sketch along a path.

        Args:
            profile_sketch: Sketch2D profile to sweep
            path_points: List of 3D points defining path (if using points)
            path_sketch_name: Name of sketch defining path (if using sketch)
            context: Operation name for error messages

        Returns:
            CadQuery Workplane with swept 3D geometry

        Raises:
            SweepBuilderError: If sweep fails
        """
        try:
            if path_sketch_name:
                raise SweepBuilderError(
                    "Sweep with path_sketch not yet implemented. Use 'path' with points.",
                    operation_name=context
                )

            add_shapes = [s for s in profile_sketch.shapes if s.operation == 'add']
            subtract_shapes = [s for s in profile_sketch.shapes if s.operation == 'subtract']

            path_wire = Wire.makePolygon([cq.Vector(*pt) for pt in path_points])

            geometry = self._sweep_shape_solid(add_shapes[0], profile_sketch, path_wire)
            for shape in add_shapes[1:]:
                geometry = geometry.union(
                    self._sweep_shape_solid(shape, profile_sketch, path_wire)
                )
            for shape in subtract_shapes:
                geometry = geometry.cut(
                    self._sweep_shape_solid(shape, profile_sketch, path_wire)
                )

            logger.debug(
                f"Swept along path: {len(add_shapes)} add, {len(subtract_shapes)} subtract"
            )
            return geometry

        except Exception as e:
            raise SweepBuilderError(
                f"Failed to sweep profile '{profile_sketch.name}': {str(e)}",
                operation_name=context
            ) from e

    def __repr__(self) -> str:
        return (
            f"SweepBuilder("
            f"sketches={list(self.sketches.keys())}, "
            f"parts={list(self.registry.parts.keys())})"
        )
