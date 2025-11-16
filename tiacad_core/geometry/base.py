"""
Geometry Backend Interface

This module defines the abstract interface for geometry operations.
Different backends (CadQuery, Mock, FreeCAD, etc.) implement this interface.

Design Goals:
- Decouple TiaCAD logic from specific CAD kernel
- Enable fast unit testing with mock backend
- Support future alternative CAD kernels
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List


class GeometryBackend(ABC):
    """
    Abstract interface for CAD geometry operations.

    All geometry operations in TiaCAD go through this interface,
    allowing different implementations (real CAD kernels or fast mocks).
    """

    # ========================================================================
    # Primitive Creation
    # ========================================================================

    @abstractmethod
    def create_box(self, width: float, height: float, depth: float) -> Any:
        """
        Create a box primitive.

        Args:
            width: Box width (X dimension)
            height: Box height (Z dimension)
            depth: Box depth (Y dimension)

        Returns:
            Geometry object (type depends on backend)

        Examples:
            >>> backend = CadQueryBackend()
            >>> box = backend.create_box(10, 20, 30)
        """
        pass

    @abstractmethod
    def create_cylinder(self, radius: float, height: float) -> Any:
        """
        Create a cylinder primitive.

        Args:
            radius: Cylinder radius
            height: Cylinder height

        Returns:
            Geometry object

        Examples:
            >>> cylinder = backend.create_cylinder(5, 20)
        """
        pass

    @abstractmethod
    def create_sphere(self, radius: float) -> Any:
        """
        Create a sphere primitive.

        Args:
            radius: Sphere radius

        Returns:
            Geometry object

        Examples:
            >>> sphere = backend.create_sphere(10)
        """
        pass

    @abstractmethod
    def create_cone(self, radius1: float, radius2: float, height: float) -> Any:
        """
        Create a cone/frustum primitive.

        Args:
            radius1: Base radius (bottom)
            radius2: Top radius (top)
            height: Cone height

        Returns:
            Geometry object

        Examples:
            >>> cone = backend.create_cone(10, 5, 20)  # Frustum
            >>> pointed_cone = backend.create_cone(10, 0, 20)  # True cone
        """
        pass

    # ========================================================================
    # Boolean Operations
    # ========================================================================

    @abstractmethod
    def boolean_union(self, geom1: Any, geom2: Any) -> Any:
        """
        Union two geometries.

        Args:
            geom1: First geometry
            geom2: Second geometry

        Returns:
            Combined geometry

        Examples:
            >>> result = backend.boolean_union(box, cylinder)
        """
        pass

    @abstractmethod
    def boolean_difference(self, geom1: Any, geom2: Any) -> Any:
        """
        Subtract geom2 from geom1.

        Args:
            geom1: Base geometry
            geom2: Geometry to subtract

        Returns:
            Result geometry

        Examples:
            >>> result = backend.boolean_difference(box, hole)
        """
        pass

    @abstractmethod
    def boolean_intersection(self, geom1: Any, geom2: Any) -> Any:
        """
        Intersect two geometries.

        Args:
            geom1: First geometry
            geom2: Second geometry

        Returns:
            Intersection geometry

        Examples:
            >>> result = backend.boolean_intersection(box, sphere)
        """
        pass

    # ========================================================================
    # Transforms
    # ========================================================================

    @abstractmethod
    def translate(self, geom: Any, offset: Tuple[float, float, float]) -> Any:
        """
        Translate geometry by offset.

        Args:
            geom: Geometry to translate
            offset: (x, y, z) offset

        Returns:
            Translated geometry

        Examples:
            >>> moved = backend.translate(box, (10, 0, 0))
        """
        pass

    @abstractmethod
    def rotate(
        self,
        geom: Any,
        axis_start: Tuple[float, float, float],
        axis_end: Tuple[float, float, float],
        angle: float
    ) -> Any:
        """
        Rotate geometry around axis.

        Args:
            geom: Geometry to rotate
            axis_start: Axis start point (x, y, z)
            axis_end: Axis end point (x, y, z)
            angle: Rotation angle in degrees

        Returns:
            Rotated geometry

        Examples:
            >>> rotated = backend.rotate(
            ...     box,
            ...     axis_start=(0, 0, 0),
            ...     axis_end=(0, 0, 1),
            ...     angle=45
            ... )
        """
        pass

    @abstractmethod
    def scale(self, geom: Any, factor: float) -> Any:
        """
        Scale geometry uniformly.

        Args:
            geom: Geometry to scale
            factor: Scale factor (1.0 = no change)

        Returns:
            Scaled geometry

        Examples:
            >>> larger = backend.scale(box, 2.0)
        """
        pass

    # ========================================================================
    # Finishing Operations
    # ========================================================================

    @abstractmethod
    def fillet(self, geom: Any, radius: float, edge_selector: str = "|Z") -> Any:
        """
        Fillet (round) edges.

        Args:
            geom: Geometry to fillet
            radius: Fillet radius
            edge_selector: Which edges to fillet (e.g., "|Z")

        Returns:
            Filleted geometry

        Examples:
            >>> rounded = backend.fillet(box, radius=2.0)
        """
        pass

    @abstractmethod
    def chamfer(self, geom: Any, distance: float, edge_selector: str = "|Z") -> Any:
        """
        Chamfer (bevel) edges.

        Args:
            geom: Geometry to chamfer
            distance: Chamfer distance
            edge_selector: Which edges to chamfer

        Returns:
            Chamfered geometry

        Examples:
            >>> beveled = backend.chamfer(box, distance=1.5)
        """
        pass

    # ========================================================================
    # Queries
    # ========================================================================

    @abstractmethod
    def get_center(self, geom: Any) -> Tuple[float, float, float]:
        """
        Get geometric center.

        Args:
            geom: Geometry to query

        Returns:
            Center point (x, y, z)

        Examples:
            >>> center = backend.get_center(box)
            >>> x, y, z = center
        """
        pass

    @abstractmethod
    def get_bounding_box(self, geom: Any) -> Dict[str, Tuple[float, float, float]]:
        """
        Get bounding box.

        Args:
            geom: Geometry to query

        Returns:
            Dictionary with keys:
            - 'min': (xmin, ymin, zmin)
            - 'max': (xmax, ymax, zmax)
            - 'center': (x, y, z)

        Examples:
            >>> bbox = backend.get_bounding_box(box)
            >>> print(bbox['min'])
            (-5.0, -5.0, -5.0)
        """
        pass

    # ========================================================================
    # Selection (for features)
    # ========================================================================

    @abstractmethod
    def select_faces(self, geom: Any, selector: str) -> List[Any]:
        """
        Select faces by selector string.

        Args:
            geom: Geometry to query
            selector: Selector string (e.g., ">Z", "|X")

        Returns:
            List of face objects

        Examples:
            >>> top_faces = backend.select_faces(box, ">Z")
        """
        pass

    @abstractmethod
    def select_edges(self, geom: Any, selector: str) -> List[Any]:
        """
        Select edges by selector string.

        Args:
            geom: Geometry to query
            selector: Selector string

        Returns:
            List of edge objects

        Examples:
            >>> vertical_edges = backend.select_edges(box, "|Z")
        """
        pass

    # ========================================================================
    # Spatial Queries (for reference extraction)
    # ========================================================================

    @abstractmethod
    def get_face_center(self, face: Any) -> Tuple[float, float, float]:
        """
        Get the center point of a face.

        Args:
            face: Face object (from select_faces)

        Returns:
            Center point (x, y, z)

        Examples:
            >>> faces = backend.select_faces(box, ">Z")
            >>> center = backend.get_face_center(faces[0])
            >>> x, y, z = center
        """
        pass

    @abstractmethod
    def get_face_normal(self, face: Any) -> Tuple[float, float, float]:
        """
        Get the normal vector of a face.

        Args:
            face: Face object (from select_faces)

        Returns:
            Normal vector (nx, ny, nz) - normalized

        Examples:
            >>> faces = backend.select_faces(box, ">Z")
            >>> normal = backend.get_face_normal(faces[0])
            >>> # For top face, normal is (0, 0, 1)
        """
        pass

    @abstractmethod
    def get_edge_point(self, edge: Any, location: str) -> Tuple[float, float, float]:
        """
        Get a point on an edge.

        Args:
            edge: Edge object (from select_edges)
            location: One of 'start', 'end', 'midpoint'

        Returns:
            Point coordinates (x, y, z)

        Examples:
            >>> edges = backend.select_edges(box, "|Z")
            >>> midpoint = backend.get_edge_point(edges[0], "midpoint")
        """
        pass

    @abstractmethod
    def get_edge_tangent(self, edge: Any) -> Tuple[float, float, float]:
        """
        Get the tangent vector of an edge.

        For straight edges, this is the direction from start to end.
        For curves, this is the tangent at the midpoint.

        Args:
            edge: Edge object (from select_edges)

        Returns:
            Tangent vector (tx, ty, tz) - normalized

        Examples:
            >>> edges = backend.select_edges(box, "|Z")
            >>> tangent = backend.get_edge_tangent(edges[0])
        """
        pass

    # ========================================================================
    # Export (optional - may delegate to exporters)
    # ========================================================================

    def tessellate(self, geom: Any, tolerance: float = 0.1) -> Tuple[List, List]:
        """
        Convert geometry to triangle mesh.

        Args:
            geom: Geometry to tessellate
            tolerance: Tessellation tolerance

        Returns:
            Tuple of (vertices, triangles)

        Note:
            This is optional - backends may not support tessellation.
            Default implementation raises NotImplementedError.

        Examples:
            >>> vertices, triangles = backend.tessellate(box)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support tessellation"
        )
