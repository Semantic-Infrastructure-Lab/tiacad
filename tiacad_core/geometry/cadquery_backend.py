"""
CadQuery Backend Implementation

Wraps CadQuery operations to implement the GeometryBackend interface.
This is the production backend used for real CAD operations.
"""

import cadquery as cq
from typing import Tuple, Dict, Any, List

from .base import GeometryBackend


class CadQueryBackend(GeometryBackend):
    """
    CadQuery implementation of GeometryBackend.

    This backend wraps CadQuery Workplane operations to provide
    real CAD geometry processing.
    """

    def __init__(self):
        """Initialize CadQuery backend"""
        self.name = "CadQuery"
        self.version = cq.__version__ if hasattr(cq, '__version__') else "unknown"

    # ========================================================================
    # Primitive Creation
    # ========================================================================

    def create_box(self, width: float, height: float, depth: float) -> cq.Workplane:
        """Create a box using CadQuery"""
        return cq.Workplane("XY").box(width, depth, height)

    def create_cylinder(self, radius: float, height: float) -> cq.Workplane:
        """Create a cylinder using CadQuery"""
        return cq.Workplane("XY").cylinder(height, radius)

    def create_sphere(self, radius: float) -> cq.Workplane:
        """Create a sphere using CadQuery"""
        return cq.Workplane("XY").sphere(radius)

    def create_cone(self, radius1: float, radius2: float, height: float) -> cq.Workplane:
        """Create a cone/frustum using CadQuery"""
        # CadQuery doesn't have a direct cone primitive, use loft between circles
        if radius2 == 0:
            # True cone (pointed top)
            cone = (cq.Workplane("XY")
                    .circle(radius1)
                    .workplane(offset=height)
                    .circle(0.001)  # Very small circle at top (CadQuery doesn't like 0)
                    .loft())
        else:
            # Frustum (truncated cone)
            cone = (cq.Workplane("XY")
                    .circle(radius1)
                    .workplane(offset=height)
                    .circle(radius2)
                    .loft())
        # Center the cone vertically
        return cone.translate((0, 0, -height/2))

    # ========================================================================
    # Boolean Operations
    # ========================================================================

    def boolean_union(self, geom1: cq.Workplane, geom2: cq.Workplane) -> cq.Workplane:
        """Union two geometries using CadQuery"""
        return geom1.union(geom2)

    def boolean_difference(self, geom1: cq.Workplane, geom2: cq.Workplane) -> cq.Workplane:
        """Subtract geom2 from geom1 using CadQuery"""
        return geom1.cut(geom2)

    def boolean_intersection(self, geom1: cq.Workplane, geom2: cq.Workplane) -> cq.Workplane:
        """Intersect two geometries using CadQuery"""
        return geom1.intersect(geom2)

    # ========================================================================
    # Transforms
    # ========================================================================

    def translate(self, geom: cq.Workplane, offset: Tuple[float, float, float]) -> cq.Workplane:
        """Translate geometry using CadQuery"""
        return geom.translate(offset)

    def rotate(
        self,
        geom: cq.Workplane,
        axis_start: Tuple[float, float, float],
        axis_end: Tuple[float, float, float],
        angle: float
    ) -> cq.Workplane:
        """Rotate geometry using CadQuery"""
        return geom.rotate(
            axisStartPoint=axis_start,
            axisEndPoint=axis_end,
            angleDegrees=angle
        )

    def scale(self, geom: cq.Workplane, factor: float) -> cq.Workplane:
        """Scale geometry using CadQuery"""
        # CadQuery doesn't have direct scale, so we use transformGeometry
        # Note: This is a uniform scale
        from cadquery import Matrix
        scale_matrix = Matrix([
            [factor, 0, 0, 0],
            [0, factor, 0, 0],
            [0, 0, factor, 0],
            [0, 0, 0, 1]
        ])
        return geom.newObject([
            obj.transformGeometry(scale_matrix)
            for obj in geom.objects
        ])

    # ========================================================================
    # Finishing Operations
    # ========================================================================

    def fillet(self, geom: cq.Workplane, radius: float, edge_selector: str = "|Z") -> cq.Workplane:
        """Fillet edges using CadQuery"""
        return geom.edges(edge_selector).fillet(radius)

    def chamfer(self, geom: cq.Workplane, distance: float, edge_selector: str = "|Z") -> cq.Workplane:
        """Chamfer edges using CadQuery"""
        return geom.edges(edge_selector).chamfer(distance)

    # ========================================================================
    # Queries
    # ========================================================================

    def get_center(self, geom: cq.Workplane) -> Tuple[float, float, float]:
        """
        Get geometric center using CadQuery.

        Uses bounding box center as approximation.
        """
        try:
            bbox = geom.val().BoundingBox()
            if hasattr(bbox, 'center'):
                return (bbox.center.x, bbox.center.y, bbox.center.z)
            else:
                # Calculate from min/max
                return (
                    (bbox.xmin + bbox.xmax) / 2.0,
                    (bbox.ymin + bbox.ymax) / 2.0,
                    (bbox.zmin + bbox.zmax) / 2.0,
                )
        except (AttributeError, RuntimeError, TypeError):
            # Fallback to origin if bbox fails
            return (0.0, 0.0, 0.0)

    def get_bounding_box(self, geom: cq.Workplane) -> Dict[str, Tuple[float, float, float]]:
        """Get bounding box using CadQuery"""
        bbox = geom.val().BoundingBox()
        return {
            'min': (bbox.xmin, bbox.ymin, bbox.zmin),
            'max': (bbox.xmax, bbox.ymax, bbox.zmax),
            'center': self.get_center(geom),
        }

    # ========================================================================
    # Selection
    # ========================================================================

    def select_faces(self, geom: cq.Workplane, selector: str) -> List[Any]:
        """Select faces using CadQuery selector"""
        return geom.faces(selector).vals()

    def select_edges(self, geom: cq.Workplane, selector: str) -> List[Any]:
        """Select edges using CadQuery selector"""
        return geom.edges(selector).vals()

    # ========================================================================
    # Spatial Queries (for reference extraction)
    # ========================================================================

    def get_face_center(self, face: Any) -> Tuple[float, float, float]:
        """
        Get the center point of a face.

        Args:
            face: CadQuery Face object

        Returns:
            Center point (x, y, z)
        """
        try:
            # Try Center() method first (most accurate for planar faces)
            center_pt = face.Center()
            return (center_pt.x, center_pt.y, center_pt.z)
        except AttributeError:
            # Fallback to bounding box center
            bbox = face.BoundingBox()
            return (
                (bbox.xmin + bbox.xmax) / 2,
                (bbox.ymin + bbox.ymax) / 2,
                (bbox.zmin + bbox.zmax) / 2
            )

    def get_face_normal(self, face: Any) -> Tuple[float, float, float]:
        """
        Get the normal vector of a face.

        Args:
            face: CadQuery Face object

        Returns:
            Normal vector (nx, ny, nz) - normalized
        """
        # CadQuery faces have normalAt() method
        # Use center point for evaluation
        normal_vec = face.normalAt()
        return (normal_vec.x, normal_vec.y, normal_vec.z)

    def get_edge_point(self, edge: Any, location: str) -> Tuple[float, float, float]:
        """
        Get a point on an edge.

        Args:
            edge: CadQuery Edge object
            location: One of 'start', 'end', 'midpoint'

        Returns:
            Point coordinates (x, y, z)

        Raises:
            ValueError: If location is not valid
        """
        if location == 'start':
            pt = edge.startPoint()
            return (pt.x, pt.y, pt.z)
        elif location == 'end':
            pt = edge.endPoint()
            return (pt.x, pt.y, pt.z)
        elif location == 'midpoint':
            # Use bounding box center as approximation
            # (More accurate would be to evaluate curve at t=0.5)
            bbox = edge.BoundingBox()
            return (
                (bbox.xmin + bbox.xmax) / 2,
                (bbox.ymin + bbox.ymax) / 2,
                (bbox.zmin + bbox.zmax) / 2
            )
        else:
            raise ValueError(f"Invalid location '{location}'. Valid: start, end, midpoint")

    def get_edge_tangent(self, edge: Any) -> Tuple[float, float, float]:
        """
        Get the tangent vector of an edge.

        For straight edges, this is the direction from start to end.
        For curves, this is an approximation using start-to-end vector.

        Args:
            edge: CadQuery Edge object

        Returns:
            Tangent vector (tx, ty, tz) - normalized

        Raises:
            ValueError: If edge has zero length
        """
        # Get start and end points
        start_pt = edge.startPoint()
        end_pt = edge.endPoint()

        # Compute direction vector
        dx = end_pt.x - start_pt.x
        dy = end_pt.y - start_pt.y
        dz = end_pt.z - start_pt.z

        # Normalize
        length = (dx**2 + dy**2 + dz**2)**0.5
        if length < 1e-10:
            raise ValueError("Edge has zero length, cannot compute tangent")

        return (dx / length, dy / length, dz / length)

    # ========================================================================
    # Export/Tessellation
    # ========================================================================

    def tessellate(self, geom: cq.Workplane, tolerance: float = 0.1) -> Tuple[List, List]:
        """
        Tessellate geometry to triangle mesh using CadQuery.

        Returns:
            Tuple of (vertices, triangles)
            - vertices: List of vertex objects (with .x, .y, .z attributes)
            - triangles: List of triangle tuples (v0, v1, v2 indices)
        """
        shape = geom.val()
        vertices, triangles = shape.tessellate(tolerance)
        return vertices, triangles

    def __repr__(self) -> str:
        return f"CadQueryBackend(version={self.version})"
