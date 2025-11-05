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
from typing import Dict, Any, List, Tuple, Optional
import cadquery as cq

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver
from ..point_resolver import PointResolver
from ..selector_resolver import SelectorResolver

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
        self.point_resolver = PointResolver(part_registry)
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
        from .metadata_utils import copy_propagating_metadata

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
            current_position=(0, 0, 0)
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

    def _create_triangular_gusset(
        self,
        points: List[Tuple[float, float, float]],
        thickness: float
    ) -> cq.Workplane:
        """
        Create a triangular gusset solid from three points.

        Strategy:
        1. Create triangle from three points
        2. Calculate extrusion direction (perpendicular to triangle)
        3. Extrude triangle to create wedge/gusset

        Args:
            points: List of 3 (x,y,z) tuples defining triangle vertices
            thickness: Extrusion thickness

        Returns:
            CadQuery Workplane with gusset solid
        """
        import numpy as np

        # Extract points
        p0, p1, p2 = points

        # Calculate two edge vectors
        v1 = np.array([p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]])
        v2 = np.array([p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]])

        # Calculate normal (perpendicular to triangle plane)
        normal = np.cross(v1, v2)
        normal_length = np.linalg.norm(normal)

        if normal_length < 1e-6:
            raise GussetBuilderError(
                "Gusset points are collinear (form a line, not a triangle)"
            )

        # Normalize
        normal = normal / normal_length

        # Create sketch on XY plane at Z=0, then transform
        # This is easier than trying to create sketches on arbitrary planes

        # Step 1: Create triangle wireframe in 3D space
        wp = cq.Workplane("XY")
        wire = wp.moveTo(p0[0], p0[1])
        wire = wire.lineTo(p1[0], p1[1])
        wire = wire.lineTo(p2[0], p2[1])
        wire = wire.close()

        # HACK: CadQuery 2D sketches assume XY plane
        # For arbitrary 3D triangles, we need to:
        # 1. Project to XY plane
        # 2. Create face
        # 3. Transform to actual 3D position
        # OR use polyhedron approach

        # For Phase 1 MVP, let's use simpler approach:
        # Create polyhedron (triangular prism) directly

        # Calculate offset points for other face
        offset = normal * thickness
        p0_offset = (p0[0] + offset[0], p0[1] + offset[1], p0[2] + offset[2])
        p1_offset = (p1[0] + offset[0], p1[1] + offset[1], p1[2] + offset[2])
        p2_offset = (p2[0] + offset[0], p2[1] + offset[1], p2[2] + offset[2])

        # Create loft between two triangular faces
        # This is more reliable than trying to sketch on arbitrary planes

        try:
            # Create first triangle
            face1 = (cq.Workplane("XY")
                    .polyline([p0, p1, p2])
                    .close()
                    .extrude(0.001))  # Tiny extrusion to create solid

            # Create second triangle
            face2 = (cq.Workplane("XY")
                    .polyline([p0_offset, p1_offset, p2_offset])
                    .close()
                    .extrude(0.001))

            # Alternative: Use box and boolean operations
            # More reliable for Phase 1

            # Actually, let's use the simplest approach: Loft
            # Create two wire triangles and loft between them

            # Reset - use makePolygon for robust 3D polyline
            from cadquery import Wire

            wire1 = Wire.makePolygon([
                cq.Vector(*p0),
                cq.Vector(*p1),
                cq.Vector(*p2),
                cq.Vector(*p0)
            ])

            wire2 = Wire.makePolygon([
                cq.Vector(*p0_offset),
                cq.Vector(*p1_offset),
                cq.Vector(*p2_offset),
                cq.Vector(*p0_offset)
            ])

            # Loft between wires (not faces!)
            from cadquery import Solid

            solid = Solid.makeLoft([wire1, wire2])

            # Wrap in Workplane
            result = cq.Workplane("XY").newObject([solid])

            logger.debug(f"Created triangular gusset: {thickness}mm thick")
            return result

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
