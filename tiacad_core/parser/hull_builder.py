"""
HullBuilder - Execute convex hull operations on Part objects

Creates convex hull (shrink-wrap) around multiple parts to create
organic enclosures, smooth fairings, and structural connections.

Supported Operations:
- hull: Create convex hull around multiple input parts

Author: TIA
Version: 0.1.0-alpha (Phase 4A)
"""

import io
import logging
import os
import tempfile
from typing import Any, Dict, List, Tuple
import cadquery as cq
import numpy as np

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class HullBuilderError(TiaCADError):
    """Error during hull operations"""
    def __init__(self, message: str, operation_name: str = None):
        super().__init__(message)
        self.operation_name = operation_name


class HullBuilder:
    """
    Executes convex hull operations on Part objects.

    Creates convex hull around multiple parts, producing a shrink-wrapped
    geometry that encloses all inputs.

    Usage:
        builder = HullBuilder(part_registry, parameter_resolver)
        builder.execute_hull_operation('hull_enclosure', {
            'inputs': ['post1', 'post2', 'post3']
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver):
        self.registry = part_registry
        self.resolver = parameter_resolver

    def _validate_hull_inputs(self, name: str, resolved_spec: Dict[str, Any]) -> List[str]:
        """Validate the 'inputs' field and return the list of input part names."""
        if 'inputs' not in resolved_spec:
            raise HullBuilderError(
                f"Hull operation '{name}' missing required 'inputs' field",
                operation_name=name
            )
        input_names = resolved_spec['inputs']
        if not isinstance(input_names, list):
            raise HullBuilderError(
                f"Hull operation '{name}' inputs must be a list, got {type(input_names).__name__}",
                operation_name=name
            )
        if len(input_names) < 1:
            raise HullBuilderError(
                f"Hull operation '{name}' requires at least 1 input part",
                operation_name=name
            )
        return input_names

    def _resolve_input_parts(self, name: str, input_names: List[str]) -> List[Part]:
        """Look up each input part by name, raising if any is missing."""
        input_parts = []
        for input_name in input_names:
            if not self.registry.exists(input_name):
                available = ', '.join(self.registry.list_parts())
                raise HullBuilderError(
                    f"Hull operation '{name}' input part '{input_name}' not found. "
                    f"Available parts: {available}",
                    operation_name=name
                )
            input_parts.append(self.registry.get(input_name))
        return input_parts

    def _handle_single_input(self, name: str, input_name: str) -> None:
        """Handle single-input hull by cloning the input part unchanged."""
        if not self.registry.exists(input_name):
            raise HullBuilderError(
                f"Hull operation '{name}' input part '{input_name}' not found",
                operation_name=name
            )
        from .metadata_utils import copy_propagating_metadata
        input_part = self.registry.get(input_name)
        metadata = copy_propagating_metadata(
            source_metadata=input_part.metadata,
            target_metadata={'source': input_name, 'operation_type': 'hull'}
        )
        result_part = Part(
            name=name,
            geometry=input_part.geometry,
            metadata=metadata,
            current_position=input_part.current_position
        )
        self.registry.add(result_part)
        logger.info(f"Hull operation '{name}' with single input - returning input unchanged")

    def _collect_all_vertices(self, input_parts: List[Part]) -> List[Tuple]:
        """Extract and aggregate vertices from all input parts."""
        all_vertices = []
        for part in input_parts:
            vertices = self._extract_vertices(part.geometry)
            all_vertices.extend(vertices)
            logger.debug(f"Extracted {len(vertices)} vertices from {part.name}")
        logger.debug(f"Total vertices for hull computation: {len(all_vertices)}")
        return all_vertices

    def execute_hull_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a hull operation.

        Args:
            name: Name for the resulting part
            spec: Operation specification with 'inputs' list of part names

        Raises:
            HullBuilderError: If operation fails
        """
        resolved_spec = self.resolver.resolve(spec)
        input_names = self._validate_hull_inputs(name, resolved_spec)

        if len(input_names) == 1:
            self._handle_single_input(name, input_names[0])
            return

        input_parts = self._resolve_input_parts(name, input_names)
        logger.info(f"Computing hull of {len(input_parts)} parts: {input_names}")

        try:
            all_vertices = self._collect_all_vertices(input_parts)
            hull_geometry = self._compute_convex_hull(all_vertices)
            logger.info(f"Hull computation successful for '{name}'")
        except Exception as e:
            raise HullBuilderError(
                f"Failed to compute hull for operation '{name}': {str(e)}",
                operation_name=name
            ) from e

        from .metadata_utils import copy_propagating_metadata
        metadata = copy_propagating_metadata(
            source_metadata=input_parts[0].metadata,
            target_metadata={'sources': input_names, 'operation_type': 'hull'}
        )
        result_part = Part(
            name=name,
            geometry=hull_geometry,
            metadata=metadata,
            current_position=(0, 0, 0)
        )
        self.registry.add(result_part)
        logger.info(f"Created hull part '{name}' from {len(input_parts)} inputs")

    def _extract_vertices(self, geometry: cq.Workplane) -> List[Tuple[float, float, float]]:
        """
        Extract all vertices from a CadQuery geometry via tessellation.

        Args:
            geometry: CadQuery Workplane containing geometry

        Returns:
            List of (x, y, z) vertex tuples

        Raises:
            HullBuilderError: If vertex extraction fails
        """
        try:
            solid = geometry.val()
            vertices_tuple, _ = solid.tessellate(0.1)
            vertices = [(v.x, v.y, v.z) for v in vertices_tuple]

            if not vertices:
                raise HullBuilderError("No vertices found in geometry")

            logger.debug(f"Extracted {len(vertices)} tessellated vertices")
            return vertices

        except Exception as e:
            raise HullBuilderError(f"Failed to extract vertices: {str(e)}") from e

    def _compute_convex_hull(self, vertices: List[Tuple[float, float, float]]) -> cq.Workplane:
        """
        Compute convex hull from a list of vertices using scipy.

        Args:
            vertices: List of (x, y, z) vertex tuples

        Returns:
            CadQuery Workplane containing convex hull solid

        Raises:
            HullBuilderError: If hull computation fails
        """
        if len(vertices) < 4:
            raise HullBuilderError(
                f"Need at least 4 vertices for 3D convex hull, got {len(vertices)}"
            )

        try:
            from scipy.spatial import ConvexHull

            points = np.array(vertices)
            logger.debug(
                f"Point cloud stats - X: [{points[:,0].min():.2f}, {points[:,0].max():.2f}], "
                f"Y: [{points[:,1].min():.2f}, {points[:,1].max():.2f}], "
                f"Z: [{points[:,2].min():.2f}, {points[:,2].max():.2f}]"
            )

            if self._are_points_coplanar(points):
                logger.warning("Input points appear coplanar - hull may fail or produce 2D result")

            hull = ConvexHull(points)
            logger.debug(
                f"ConvexHull computed: {len(hull.vertices)} vertices, "
                f"{len(hull.simplices)} faces, volume: {hull.volume:.2f}"
            )
            return self._build_solid_from_hull(points, hull)

        except ImportError as e:
            raise HullBuilderError(
                "scipy is required for hull operations. Install with: pip install scipy"
            ) from e
        except Exception as e:
            raise HullBuilderError(f"Failed to compute convex hull: {str(e)}") from e

    def _are_points_coplanar(self, points: np.ndarray, tolerance: float = 1e-6) -> bool:
        """Check if all points lie in a single plane."""
        if len(points) < 4:
            return True

        p0, p1, p2 = points[0], points[1], points[2]
        v1, v2 = p1 - p0, p2 - p0
        normal = np.cross(v1, v2)

        if np.linalg.norm(normal) < tolerance:
            for i in range(3, len(points)):
                v2 = points[i] - p0
                normal = np.cross(v1, v2)
                if np.linalg.norm(normal) >= tolerance:
                    break
            else:
                return True

        normal = normal / np.linalg.norm(normal)
        return all(abs(np.dot(pt - p0, normal)) <= tolerance for pt in points[3:])

    def _trimesh_to_cq_workplane(self, mesh) -> cq.Workplane:
        """Export a trimesh mesh to STL and import into a CadQuery Workplane."""
        stl_buf = io.BytesIO()
        mesh.export(stl_buf, file_type='stl')
        stl_buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp.write(stl_buf.read())
            tmp_path = tmp.name

        try:
            try:
                result = cq.importers.importShape(cq.exporters.ExportTypes.STL, tmp_path)
                return cq.Workplane("XY").newObject([result])
            except RuntimeError as stl_error:
                if "Unsupported import type" in str(stl_error):
                    return None  # Signal fallback needed
                raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _build_solid_from_hull(self, points: np.ndarray, hull: Any) -> cq.Workplane:
        """
        Build a CadQuery solid from a scipy ConvexHull result.

        Tries trimesh-based STL round-trip first; falls back to direct face construction.

        Args:
            points: Original points array
            hull: scipy.spatial.ConvexHull result

        Returns:
            CadQuery Workplane containing solid

        Raises:
            HullBuilderError: If solid creation fails
        """
        try:
            import trimesh
            mesh = trimesh.Trimesh(vertices=points, faces=hull.simplices)
            mesh.fix_normals()
            result = self._trimesh_to_cq_workplane(mesh)
            if result is not None:
                return result
            return self._build_solid_from_hull_simple(points, hull)

        except ImportError:
            return self._build_solid_from_hull_simple(points, hull)
        except HullBuilderError:
            raise
        except Exception as e:
            raise HullBuilderError(
                f"Failed to build solid from convex hull: {str(e)}"
            ) from e

    def _build_solid_from_hull_simple(self, points: np.ndarray, hull: Any) -> cq.Workplane:
        """
        Fallback solid builder using CadQuery face/shell/solid construction.

        Args:
            points: Original points array
            hull: scipy.spatial.ConvexHull result

        Returns:
            CadQuery Workplane containing solid

        Raises:
            HullBuilderError: If solid creation fails
        """
        try:
            from cadquery import Solid, Face, Wire, Vector

            faces = []
            for simplex in hull.simplices:
                p0, p1, p2 = points[simplex[0]], points[simplex[1]], points[simplex[2]]
                v0 = Vector(p0[0], p0[1], p0[2])
                v1 = Vector(p1[0], p1[1], p1[2])
                v2 = Vector(p2[0], p2[1], p2[2])
                wire = Wire.makePolygon([v0, v1, v2, v0])
                faces.append(Face.makeFromWires(wire))

            shell = cq.Shell.makeShell(faces)
            solid = Solid.makeSolid(shell)
            return cq.Workplane("XY").newObject([solid])

        except Exception as e:
            raise HullBuilderError(
                f"Failed to build solid using simple method: {str(e)}"
            ) from e

    def __repr__(self) -> str:
        return f"HullBuilder(parts={len(self.registry)})"
