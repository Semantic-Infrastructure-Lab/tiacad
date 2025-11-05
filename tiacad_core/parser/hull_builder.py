"""
HullBuilder - Execute convex hull operations on Part objects

Creates convex hull (shrink-wrap) around multiple parts to create
organic enclosures, smooth fairings, and structural connections.

Supported Operations:
- hull: Create convex hull around multiple input parts

Author: TIA
Version: 0.1.0-alpha (Phase 4A)
"""

import logging
from typing import Dict, Any, List, Tuple
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
        """
        Initialize hull builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
        """
        self.registry = part_registry
        self.resolver = parameter_resolver

    def execute_hull_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a hull operation.

        Args:
            name: Name for the resulting part
            spec: Operation specification with 'inputs'

        Raises:
            HullBuilderError: If operation fails

        Example spec:
            {
                'inputs': ['mounting_post_1', 'mounting_post_2', 'mounting_post_3']
            }
        """
        # Resolve parameters first
        resolved_spec = self.resolver.resolve(spec)

        # Validate inputs field
        if 'inputs' not in resolved_spec:
            raise HullBuilderError(
                f"Hull operation '{name}' missing required 'inputs' field",
                operation_name=name
            )

        input_names = resolved_spec['inputs']

        # Validate inputs is a list
        if not isinstance(input_names, list):
            raise HullBuilderError(
                f"Hull operation '{name}' inputs must be a list, got {type(input_names).__name__}",
                operation_name=name
            )

        # Validate we have at least one input
        if len(input_names) < 1:
            raise HullBuilderError(
                f"Hull operation '{name}' requires at least 1 input part",
                operation_name=name
            )

        # Special case: single input returns the input unchanged
        if len(input_names) == 1:
            input_name = input_names[0]
            if not self.registry.exists(input_name):
                raise HullBuilderError(
                    f"Hull operation '{name}' input part '{input_name}' not found",
                    operation_name=name
                )

            input_part = self.registry.get(input_name)

            # Create copy with new name
            from .metadata_utils import copy_propagating_metadata

            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'source': input_name,
                    'operation_type': 'hull'
                }
            )

            result_part = Part(
                name=name,
                geometry=input_part.geometry,
                metadata=metadata,
                current_position=input_part.current_position
            )

            self.registry.add(result_part)
            logger.info(f"Hull operation '{name}' with single input - returning input unchanged")
            return

        # Get input parts
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

        logger.info(f"Computing hull of {len(input_parts)} parts: {input_names}")

        try:
            # Extract vertices from all input parts
            all_vertices = []
            for part in input_parts:
                vertices = self._extract_vertices(part.geometry)
                all_vertices.extend(vertices)
                logger.debug(f"Extracted {len(vertices)} vertices from {part.name}")

            logger.debug(f"Total vertices for hull computation: {len(all_vertices)}")

            # Compute convex hull
            hull_geometry = self._compute_convex_hull(all_vertices)

            logger.info(f"Hull computation successful for '{name}'")

        except Exception as e:
            raise HullBuilderError(
                f"Failed to compute hull for operation '{name}': {str(e)}",
                operation_name=name
            ) from e

        # Create metadata for result part
        from .metadata_utils import copy_propagating_metadata

        # Use first input's metadata as base
        metadata = copy_propagating_metadata(
            source_metadata=input_parts[0].metadata,
            target_metadata={
                'sources': input_names,
                'operation_type': 'hull'
            }
        )

        # Create result part
        result_part = Part(
            name=name,
            geometry=hull_geometry,
            metadata=metadata,
            current_position=(0, 0, 0)  # Hull creates new geometry at origin
        )

        # Add to registry
        self.registry.add(result_part)
        logger.info(f"Created hull part '{name}' from {len(input_parts)} inputs")

    def _extract_vertices(self, geometry: cq.Workplane) -> List[Tuple[float, float, float]]:
        """
        Extract all vertices from a CadQuery geometry.

        Uses tessellation to get a dense vertex set for smooth surfaces.

        Args:
            geometry: CadQuery Workplane containing geometry

        Returns:
            List of (x, y, z) vertex tuples

        Raises:
            HullBuilderError: If vertex extraction fails
        """
        try:
            # Get the solid from the workplane
            solid = geometry.val()

            # Use tessellation to get mesh vertices (better for curved surfaces)
            # This gives us a good sampling of points on the surface
            tolerance = 0.1
            vertices_tuple, triangles = solid.tessellate(tolerance)

            # Convert OCP vertices to Python tuples
            vertices = []
            for vert in vertices_tuple:
                # vertices_tuple contains vertex objects with x, y, z attributes
                vertices.append((vert.x, vert.y, vert.z))

            if not vertices:
                raise HullBuilderError("No vertices found in geometry")

            logger.debug(f"Extracted {len(vertices)} tessellated vertices")

            return vertices

        except Exception as e:
            raise HullBuilderError(
                f"Failed to extract vertices: {str(e)}"
            ) from e

    def _compute_convex_hull(self, vertices: List[Tuple[float, float, float]]) -> cq.Workplane:
        """
        Compute convex hull from list of vertices.

        Uses scipy.spatial.ConvexHull for computation, then builds
        CadQuery solid from the resulting faces.

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
            # Import scipy for convex hull computation
            from scipy.spatial import ConvexHull

            # Convert to numpy array
            points = np.array(vertices)

            # Log point distribution for debugging
            logger.debug(f"Point cloud stats - X: [{points[:,0].min():.2f}, {points[:,0].max():.2f}], "
                        f"Y: [{points[:,1].min():.2f}, {points[:,1].max():.2f}], "
                        f"Z: [{points[:,2].min():.2f}, {points[:,2].max():.2f}]")

            # Check if points are coplanar and warn (but try anyway)
            if self._are_points_coplanar(points):
                logger.warning(f"Input points appear coplanar - hull may fail or produce 2D result")

            # Compute convex hull (scipy will handle degenerate cases)
            # Note: ConvexHull will raise QhullError if points are truly degenerate
            hull = ConvexHull(points)

            logger.debug(f"ConvexHull computed: {len(hull.vertices)} vertices, "
                        f"{len(hull.simplices)} faces, "
                        f"volume: {hull.volume:.2f}")

            # Build CadQuery solid from hull
            return self._build_solid_from_hull(points, hull)

        except ImportError as e:
            raise HullBuilderError(
                "scipy is required for hull operations. Install with: pip install scipy"
            ) from e
        except Exception as e:
            raise HullBuilderError(
                f"Failed to compute convex hull: {str(e)}"
            ) from e

    def _are_points_coplanar(self, points: np.ndarray, tolerance: float = 1e-6) -> bool:
        """
        Check if points are coplanar (all lie in a plane).

        Args:
            points: Nx3 numpy array of points
            tolerance: Numerical tolerance for coplanarity check

        Returns:
            True if points are coplanar, False otherwise
        """
        if len(points) < 4:
            return True

        # Take first 3 non-collinear points to define a plane
        p0 = points[0]
        p1 = points[1]
        p2 = points[2]

        # Compute normal vector to plane
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)

        # If normal is zero, first 3 points are collinear - find another
        if np.linalg.norm(normal) < tolerance:
            for i in range(3, len(points)):
                p2 = points[i]
                v2 = p2 - p0
                normal = np.cross(v1, v2)
                if np.linalg.norm(normal) >= tolerance:
                    break
            else:
                # All points are collinear
                return True

        normal = normal / np.linalg.norm(normal)

        # Check if all points lie on this plane
        for point in points[3:]:
            distance = abs(np.dot(point - p0, normal))
            if distance > tolerance:
                return False

        return True

    def _build_solid_from_hull(self, points: np.ndarray, hull: Any) -> cq.Workplane:
        """
        Build a CadQuery solid from scipy ConvexHull result.

        Args:
            points: Original points array
            hull: scipy.spatial.ConvexHull result

        Returns:
            CadQuery Workplane containing solid

        Raises:
            HullBuilderError: If solid creation fails
        """
        try:
            # Use trimesh for a simpler approach
            import trimesh

            # Create a trimesh mesh from the convex hull
            # hull.vertices are the indices of points that form the convex hull
            # hull.simplices are the triangular faces (indices into points array)
            mesh = trimesh.Trimesh(vertices=points, faces=hull.simplices)

            # Ensure normals are consistent
            mesh.fix_normals()

            # Export to STL bytes
            import io
            stl_bytes = io.BytesIO()
            mesh.export(stl_bytes, file_type='stl')
            stl_bytes.seek(0)

            # Import the STL into CadQuery
            import tempfile
            import os

            # Write to temporary file
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
                tmp.write(stl_bytes.read())
                tmp_path = tmp.name

            try:
                # Import STL as CadQuery solid
                result = cq.importers.importShape(
                    cq.exporters.ExportTypes.STL,
                    tmp_path
                )

                # Wrap in Workplane
                return cq.Workplane("XY").newObject([result])

            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except ImportError:
            # Trimesh not available, try simpler approach with CadQuery primitives
            return self._build_solid_from_hull_simple(points, hull)
        except Exception as e:
            raise HullBuilderError(
                f"Failed to build solid from convex hull: {str(e)}"
            ) from e

    def _build_solid_from_hull_simple(self, points: np.ndarray, hull: Any) -> cq.Workplane:
        """
        Simpler approach using CadQuery's polyhedron-like construction.

        Args:
            points: Original points array
            hull: scipy.spatial.ConvexHull result

        Returns:
            CadQuery Workplane containing solid

        Raises:
            HullBuilderError: If solid creation fails
        """
        try:
            # Build shell from faces using CadQuery's solid construction
            import cadquery as cq
            from cadquery import Solid, Face, Wire, Vector

            # Create faces for each simplex
            faces = []
            for simplex in hull.simplices:
                # Get three vertices
                p0 = points[simplex[0]]
                p1 = points[simplex[1]]
                p2 = points[simplex[2]]

                # Create CadQuery vectors
                v0 = Vector(p0[0], p0[1], p0[2])
                v1 = Vector(p1[0], p1[1], p1[2])
                v2 = Vector(p2[0], p2[1], p2[2])

                # Create a wire (polygon) from the three points
                wire = Wire.makePolygon([v0, v1, v2, v0])

                # Create face from wire
                face = Face.makeFromWires(wire)
                faces.append(face)

            # Create shell from faces
            shell = cq.Shell.makeShell(faces)

            # Create solid from shell
            solid = Solid.makeSolid(shell)

            # Wrap in Workplane
            return cq.Workplane("XY").newObject([solid])

        except Exception as e:
            raise HullBuilderError(
                f"Failed to build solid using simple method: {str(e)}"
            ) from e

    def __repr__(self) -> str:
        return f"HullBuilder(parts={len(self.registry)})"
