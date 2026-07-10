"""
GussetBuilder - Create structural gussets between parts

Creates triangular or wedge-shaped structural supports that connect
two parts or fill corners, eliminating manual rotation and positioning math.

Supported Modes:
- Manual points: Specify exact triangle vertices
- Auto-connect: Automatically connect two part faces (Phase 2)

Author: TIA (sunny-rainbow-1102)
Version: 0.1.0-alpha (Phase 1 - Manual Points MVP)
"""

import logging
from typing import Dict, Any, List, Tuple
import cadquery as cq
import numpy as np
from cadquery import Wire, Solid

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver
from ..selector_resolver import SelectorResolver
from .backend_utils import get_cadquery_backend

logger = logging.getLogger(__name__)


class GussetBuilderError(TiaCADError):
    """Error during gusset operations"""
    def __init__(self, message: str, operation_name: str = None):
        super().__init__(message)
        self.operation_name = operation_name


class GussetBuilder:
    """
    Creates structural gusset supports between parts.

    Phase 1 (MVP): Manual points mode - specify triangle vertices
    Phase 2 (Future): Auto-connect mode - connect two part faces

    Usage:
        builder = GussetBuilder(part_registry, parameter_resolver)

        # Manual points mode
        builder.execute_gusset_operation('corner_support', {
            'points': [[0,0,0], [50,0,0], [25,40,0]],
            'thickness': 8
        })

        # Auto-connect mode (Phase 2)
        builder.execute_gusset_operation('beam_support', {
            'connect': {
                'from': {'part': 'beam', 'face': '>Y'},
                'to': {'part': 'arm', 'face': '<Y'}
            },
            'thickness': 8
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver):
        """
        Initialize gusset builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
        """
        self.registry = part_registry
        self.resolver = parameter_resolver
        self.selector_resolver = SelectorResolver(part_registry)

    def execute_gusset_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a gusset operation.

        Args:
            name: Name for the resulting part
            spec: Operation specification with either 'points' or 'connect'

        Raises:
            GussetBuilderError: If operation fails

        Example specs:
            # Manual points
            {
                'points': [[0,0,0], [50,0,0], [25,40,0]],
                'thickness': 8
            }

            # Auto-connect (Phase 2)
            {
                'connect': {
                    'from': {'part': 'beam', 'face': '>Y'},
                    'to': {'part': 'arm', 'face': '<Y'}
                },
                'thickness': 8,
                'style': 'triangular'  # or 'curved', 'filleted'
            }
        """
        # Resolve parameters first
        resolved_spec = self.resolver.resolve(spec)

        # Validate required fields
        if 'thickness' not in resolved_spec:
            raise GussetBuilderError(
                f"Gusset operation '{name}' missing required 'thickness' field",
                operation_name=name
            )

        thickness = resolved_spec['thickness']

        # Validate thickness
        if not isinstance(thickness, (int, float)) or thickness <= 0:
            raise GussetBuilderError(
                f"Gusset operation '{name}' thickness must be positive number, got {thickness}",
                operation_name=name
            )

        # Determine mode and execute
        if 'points' in resolved_spec:
            geometry = self._execute_manual_points(name, resolved_spec)
        elif 'connect' in resolved_spec:
            geometry = self._execute_auto_connect(name, resolved_spec)
        else:
            raise GussetBuilderError(
                f"Gusset operation '{name}' must specify either 'points' or 'connect'",
                operation_name=name
            )

        # Create metadata

        metadata = {
            'operation_type': 'gusset',
            'thickness': thickness
        }

        if 'points' in resolved_spec:
            metadata['mode'] = 'manual_points'
            metadata['points'] = resolved_spec['points']
        else:
            metadata['mode'] = 'auto_connect'
            metadata['connect'] = resolved_spec['connect']

        # Create result part
        result_part = Part(
            name=name,
            geometry=geometry,
            metadata=metadata,
            current_position=(0, 0, 0),
            backend=get_cadquery_backend(),
        )

        # Add to registry
        self.registry.add(result_part)
        logger.info(f"Created gusset part '{name}' with thickness {thickness}mm")

    def _execute_manual_points(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Create gusset from manually specified points.

        Args:
            name: Operation name
            spec: Specification with 'points' and 'thickness'

        Returns:
            CadQuery Workplane containing gusset solid

        Raises:
            GussetBuilderError: If point specification is invalid
        """
        points = spec['points']
        thickness = spec['thickness']

        # Validate points
        if not isinstance(points, list):
            raise GussetBuilderError(
                f"Gusset '{name}' points must be a list, got {type(points).__name__}",
                operation_name=name
            )

        if len(points) != 3:
            raise GussetBuilderError(
                f"Gusset '{name}' requires exactly 3 points for triangular gusset, got {len(points)}",
                operation_name=name
            )

        # Convert points to tuples
        try:
            triangle_points = []
            for i, point in enumerate(points):
                if not isinstance(point, (list, tuple)) or len(point) != 3:
                    raise GussetBuilderError(
                        f"Gusset '{name}' point {i} must be [x,y,z] list, got {point}",
                        operation_name=name
                    )
                triangle_points.append(tuple(float(coord) for coord in point))
        except (ValueError, TypeError) as e:
            raise GussetBuilderError(
                f"Gusset '{name}' invalid point coordinates: {str(e)}",
                operation_name=name
            ) from e

        logger.debug(f"Creating triangular gusset with points: {triangle_points}")

        try:
            # Create the gusset geometry
            geometry = self._create_triangular_gusset(triangle_points, thickness)
            return geometry

        except Exception as e:
            raise GussetBuilderError(
                f"Failed to create gusset '{name}': {str(e)}",
                operation_name=name
            ) from e

    def _triangle_normal(
        self,
        p0: Tuple, p1: Tuple, p2: Tuple
    ) -> np.ndarray:
        """Return the unit normal vector for triangle (p0, p1, p2)."""
        v1 = np.array([p1[i] - p0[i] for i in range(3)])
        v2 = np.array([p2[i] - p0[i] for i in range(3)])
        normal = np.cross(v1, v2)
        length = np.linalg.norm(normal)
        if length < 1e-6:
            raise GussetBuilderError(
                "Gusset points are collinear (form a line, not a triangle)"
            )
        return normal / length

    def _offset_triangle(
        self,
        p0: Tuple, p1: Tuple, p2: Tuple,
        normal: np.ndarray, thickness: float
    ) -> Tuple:
        """Return three offset points translated by normal * thickness."""
        offset = normal * thickness
        return (
            tuple(p0[i] + offset[i] for i in range(3)),
            tuple(p1[i] + offset[i] for i in range(3)),
            tuple(p2[i] + offset[i] for i in range(3)),
        )

    def _loft_triangles(self, base: Tuple, top: Tuple) -> cq.Workplane:
        """Loft between two triangles (each a tuple of 3 points) to create a prism."""
        p0, p1, p2 = base
        q0, q1, q2 = top
        wire1 = Wire.makePolygon([cq.Vector(*p0), cq.Vector(*p1), cq.Vector(*p2), cq.Vector(*p0)])
        wire2 = Wire.makePolygon([cq.Vector(*q0), cq.Vector(*q1), cq.Vector(*q2), cq.Vector(*q0)])
        solid = Solid.makeLoft([wire1, wire2])
        return cq.Workplane("XY").newObject([solid])

    def _create_triangular_gusset(
        self,
        points: List[Tuple[float, float, float]],
        thickness: float
    ) -> cq.Workplane:
        """
        Create a triangular gusset solid from three points.

        Args:
            points: List of 3 (x,y,z) tuples defining triangle vertices
            thickness: Extrusion thickness (perpendicular to triangle plane)

        Returns:
            CadQuery Workplane with gusset solid
        """
        try:
            p0, p1, p2 = points
            normal = self._triangle_normal(p0, p1, p2)
            q0, q1, q2 = self._offset_triangle(p0, p1, p2, normal, thickness)
            result = self._loft_triangles((p0, p1, p2), (q0, q1, q2))
            logger.debug(f"Created triangular gusset: {thickness}mm thick")
            return result
        except GussetBuilderError:
            raise
        except Exception as e:
            raise GussetBuilderError(
                f"Failed to create triangular gusset geometry: {str(e)}"
            ) from e

    def _execute_auto_connect(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Create gusset by automatically connecting two part faces.

        Phase 2 implementation - auto-calculate triangle from face positions.

        Args:
            name: Operation name
            spec: Specification with 'connect' dict

        Returns:
            CadQuery Workplane containing gusset solid

        Raises:
            GussetBuilderError: Always (not implemented yet)
        """
        raise GussetBuilderError(
            f"Gusset '{name}': Auto-connect mode not yet implemented (Phase 2). "
            f"Use manual 'points' mode for now",
            operation_name=name
        )

    def __repr__(self) -> str:
        return f"GussetBuilder(parts={len(self.registry)})"
