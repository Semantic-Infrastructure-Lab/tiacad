"""
Mock Backend Implementation

Fast, lightweight mock backend for unit testing.
No actual CAD operations - just tracks what would happen.

Benefits:
- 10-100x faster than real CadQuery
- No heavy dependencies
- Predictable, deterministic results
- Easy to verify test logic
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, List, Optional
from .base import GeometryBackend


@dataclass
class MockFace:
    """Mock face object for testing"""
    center: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    name: str = "MockFace"


@dataclass
class MockEdge:
    """Mock edge object for testing"""
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]
    name: str = "MockEdge"


@dataclass
class MockGeometry:
    """
    Lightweight mock geometry for testing.

    Instead of real CAD operations, this just tracks:
    - What shape it is
    - What parameters were used
    - Where it's located
    - What operations were applied

    This allows fast unit testing of TiaCAD logic without
    slow CAD kernel operations.
    """

    shape_type: str  # "box", "cylinder", "sphere", "union", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bounds: Optional[Dict[str, Tuple]] = None
    operation_history: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate reasonable bounds based on shape type"""
        if self.bounds is None:
            self.bounds = self._calculate_default_bounds()

    def _calculate_default_bounds(self) -> Dict[str, Tuple]:
        """Calculate reasonable bounding box for shape type"""
        if self.shape_type == 'box':
            w = self.parameters.get('width', 10)
            h = self.parameters.get('height', 10)
            d = self.parameters.get('depth', 10)
            return {
                'min': (-w/2, -d/2, -h/2),
                'max': (w/2, d/2, h/2),
                'center': self.center
            }

        elif self.shape_type == 'cylinder':
            r = self.parameters.get('radius', 5)
            h = self.parameters.get('height', 20)
            return {
                'min': (-r, -r, -h/2),
                'max': (r, r, h/2),
                'center': self.center
            }

        elif self.shape_type == 'sphere':
            r = self.parameters.get('radius', 10)
            return {
                'min': (-r, -r, -r),
                'max': (r, r, r),
                'center': self.center
            }

        else:
            # Default: unit box
            return {
                'min': (-0.5, -0.5, -0.5),
                'max': (0.5, 0.5, 0.5),
                'center': self.center
            }

    def with_center(self, new_center: Tuple[float, float, float]) -> 'MockGeometry':
        """Create copy with new center"""
        return MockGeometry(
            shape_type=self.shape_type,
            parameters=self.parameters.copy(),
            center=new_center,
            bounds=self._recalculate_bounds(new_center),
            operation_history=self.operation_history.copy()
        )

    def _recalculate_bounds(self, new_center: Tuple[float, float, float]) -> Dict:
        """Recalculate bounds for new center"""
        if self.bounds is None:
            return None

        old_center = self.center
        offset = tuple(new_center[i] - old_center[i] for i in range(3))

        old_min = self.bounds['min']
        old_max = self.bounds['max']

        return {
            'min': tuple(old_min[i] + offset[i] for i in range(3)),
            'max': tuple(old_max[i] + offset[i] for i in range(3)),
            'center': new_center
        }

    def add_operation(self, operation: str) -> 'MockGeometry':
        """Record an operation in history"""
        new_history = self.operation_history.copy()
        new_history.append(operation)
        return MockGeometry(
            shape_type=self.shape_type,
            parameters=self.parameters.copy(),
            center=self.center,
            bounds=self.bounds.copy() if self.bounds else None,
            operation_history=new_history
        )

    def __repr__(self) -> str:
        return f"MockGeometry(type={self.shape_type}, center={self.center}, ops={len(self.operation_history)})"


class MockBackend(GeometryBackend):
    """
    Fast mock backend for unit testing.

    This backend creates lightweight MockGeometry objects instead of
    real CAD geometry. Operations just update the mock state rather
    than performing actual CAD operations.

    Benefits:
    - 10-100x faster than CadQueryBackend
    - No CadQuery dependency needed
    - Deterministic, predictable behavior
    - Easy to test TiaCAD logic
    """

    def __init__(self):
        """Initialize mock backend"""
        self.name = "Mock"
        self.version = "1.0"
        self.operations_count = 0  # Track total operations

    # ========================================================================
    # Primitive Creation
    # ========================================================================

    def create_box(self, width: float, height: float, depth: float) -> MockGeometry:
        """Create mock box"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='box',
            parameters={'width': width, 'height': height, 'depth': depth}
        )

    def create_cylinder(self, radius: float, height: float) -> MockGeometry:
        """Create mock cylinder"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='cylinder',
            parameters={'radius': radius, 'height': height}
        )

    def create_sphere(self, radius: float) -> MockGeometry:
        """Create mock sphere"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='sphere',
            parameters={'radius': radius}
        )

    # ========================================================================
    # Boolean Operations
    # ========================================================================

    def boolean_union(self, geom1: MockGeometry, geom2: MockGeometry) -> MockGeometry:
        """Mock union - just record the operation"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='union',
            parameters={'operands': [geom1, geom2]},
            center=geom1.center,  # Use first geometry's center
            operation_history=geom1.operation_history + ['union']
        )

    def boolean_difference(self, geom1: MockGeometry, geom2: MockGeometry) -> MockGeometry:
        """Mock difference - just record the operation"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='difference',
            parameters={'base': geom1, 'subtract': geom2},
            center=geom1.center,
            operation_history=geom1.operation_history + ['difference']
        )

    def boolean_intersection(self, geom1: MockGeometry, geom2: MockGeometry) -> MockGeometry:
        """Mock intersection - just record the operation"""
        self.operations_count += 1
        return MockGeometry(
            shape_type='intersection',
            parameters={'operands': [geom1, geom2]},
            center=geom1.center,
            operation_history=geom1.operation_history + ['intersection']
        )

    # ========================================================================
    # Transforms
    # ========================================================================

    def translate(self, geom: MockGeometry, offset: Tuple[float, float, float]) -> MockGeometry:
        """Mock translate - just update center"""
        self.operations_count += 1
        new_center = tuple(geom.center[i] + offset[i] for i in range(3))
        return geom.with_center(new_center).add_operation(f'translate{offset}')

    def rotate(
        self,
        geom: MockGeometry,
        axis_start: Tuple[float, float, float],
        axis_end: Tuple[float, float, float],
        angle: float
    ) -> MockGeometry:
        """Mock rotate - just record operation (center unchanged for simple shapes)"""
        self.operations_count += 1
        return geom.add_operation(f'rotate({angle}°)')

    def scale(self, geom: MockGeometry, factor: float) -> MockGeometry:
        """Mock scale - multiply parameters"""
        self.operations_count += 1

        # Scale the parameters
        new_params = {}
        for key, value in geom.parameters.items():
            if isinstance(value, (int, float)):
                new_params[key] = value * factor
            else:
                new_params[key] = value

        return MockGeometry(
            shape_type=geom.shape_type,
            parameters=new_params,
            center=geom.center,
            operation_history=geom.operation_history + [f'scale({factor})']
        )

    # ========================================================================
    # Finishing Operations
    # ========================================================================

    def fillet(self, geom: MockGeometry, radius: float, edge_selector: str = "|Z") -> MockGeometry:
        """Mock fillet - just record operation"""
        self.operations_count += 1
        return geom.add_operation(f'fillet(r={radius}, edges={edge_selector})')

    def chamfer(self, geom: MockGeometry, distance: float, edge_selector: str = "|Z") -> MockGeometry:
        """Mock chamfer - just record operation"""
        self.operations_count += 1
        return geom.add_operation(f'chamfer(d={distance}, edges={edge_selector})')

    # ========================================================================
    # Queries
    # ========================================================================

    def get_center(self, geom: MockGeometry) -> Tuple[float, float, float]:
        """Get mock geometry center"""
        return geom.center

    def get_bounding_box(self, geom: MockGeometry) -> Dict[str, Tuple[float, float, float]]:
        """Get mock bounding box"""
        return geom.bounds

    # ========================================================================
    # Selection
    # ========================================================================

    def select_faces(self, geom: MockGeometry, selector: str) -> List[MockFace]:
        """Mock face selection - return mock face objects"""
        # For testing purposes, return mock faces based on selector
        # Parse selector to determine which face (e.g., ">Z" = top face)

        if geom.shape_type == 'box':
            # Get bounding box
            bbox = geom.bounds
            xmin, ymin, zmin = bbox['min']
            xmax, ymax, zmax = bbox['max']
            cx, cy, cz = bbox['center']

            # Define standard box faces based on selector
            if selector == '>Z':  # Top face
                return [MockFace(
                    center=(cx, cy, zmax),
                    normal=(0, 0, 1),
                    name=f"MockFace-{selector}"
                )]
            elif selector == '<Z':  # Bottom face
                return [MockFace(
                    center=(cx, cy, zmin),
                    normal=(0, 0, -1),
                    name=f"MockFace-{selector}"
                )]
            elif selector == '>X':  # Right face
                return [MockFace(
                    center=(xmax, cy, cz),
                    normal=(1, 0, 0),
                    name=f"MockFace-{selector}"
                )]
            elif selector == '<X':  # Left face
                return [MockFace(
                    center=(xmin, cy, cz),
                    normal=(-1, 0, 0),
                    name=f"MockFace-{selector}"
                )]
            elif selector == '>Y':  # Front face
                return [MockFace(
                    center=(cx, ymax, cz),
                    normal=(0, 1, 0),
                    name=f"MockFace-{selector}"
                )]
            elif selector == '<Y':  # Back face
                return [MockFace(
                    center=(cx, ymin, cz),
                    normal=(0, -1, 0),
                    name=f"MockFace-{selector}"
                )]

        # Default: return a generic face at center
        return [MockFace(
            center=geom.center,
            normal=(0, 0, 1),
            name=f"MockFace-{selector}"
        )]

    def select_edges(self, geom: MockGeometry, selector: str) -> List[MockEdge]:
        """Mock edge selection - return mock edge objects"""
        # For testing, return mock edges based on selector

        if geom.shape_type == 'box':
            bbox = geom.bounds
            xmin, ymin, zmin = bbox['min']
            xmax, ymax, zmax = bbox['max']

            # Define standard box edges based on selector
            if selector == '|Z':  # Vertical edges (parallel to Z)
                return [
                    MockEdge(start=(xmin, ymin, zmin), end=(xmin, ymin, zmax), name=f"MockEdge-{selector}-0"),
                    MockEdge(start=(xmax, ymin, zmin), end=(xmax, ymin, zmax), name=f"MockEdge-{selector}-1"),
                    MockEdge(start=(xmax, ymax, zmin), end=(xmax, ymax, zmax), name=f"MockEdge-{selector}-2"),
                    MockEdge(start=(xmin, ymax, zmin), end=(xmin, ymax, zmax), name=f"MockEdge-{selector}-3"),
                ]
            elif selector == '|X':  # Edges parallel to X
                return [
                    MockEdge(start=(xmin, ymin, zmin), end=(xmax, ymin, zmin), name=f"MockEdge-{selector}-0"),
                    MockEdge(start=(xmin, ymax, zmin), end=(xmax, ymax, zmin), name=f"MockEdge-{selector}-1"),
                ]

        # Default: return a generic edge
        cx, cy, cz = geom.center
        return [MockEdge(
            start=(cx - 1, cy, cz),
            end=(cx + 1, cy, cz),
            name=f"MockEdge-{selector}"
        )]

    # ========================================================================
    # Spatial Queries (for reference extraction)
    # ========================================================================

    def get_face_center(self, face: MockFace) -> Tuple[float, float, float]:
        """Get the center point of a mock face"""
        return face.center

    def get_face_normal(self, face: MockFace) -> Tuple[float, float, float]:
        """Get the normal vector of a mock face"""
        return face.normal

    def get_edge_point(self, edge: MockEdge, location: str) -> Tuple[float, float, float]:
        """
        Get a point on a mock edge.

        Args:
            edge: MockEdge object
            location: One of 'start', 'end', 'midpoint'

        Returns:
            Point coordinates (x, y, z)

        Raises:
            ValueError: If location is not valid
        """
        if location == 'start':
            return edge.start
        elif location == 'end':
            return edge.end
        elif location == 'midpoint':
            # Calculate midpoint
            sx, sy, sz = edge.start
            ex, ey, ez = edge.end
            return ((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2)
        else:
            raise ValueError(f"Invalid location '{location}'. Valid: start, end, midpoint")

    def get_edge_tangent(self, edge: MockEdge) -> Tuple[float, float, float]:
        """
        Get the tangent vector of a mock edge.

        Returns:
            Tangent vector (tx, ty, tz) - normalized

        Raises:
            ValueError: If edge has zero length
        """
        sx, sy, sz = edge.start
        ex, ey, ez = edge.end

        # Compute direction vector
        dx = ex - sx
        dy = ey - sy
        dz = ez - sz

        # Normalize
        length = (dx**2 + dy**2 + dz**2)**0.5
        if length < 1e-10:
            raise ValueError("Edge has zero length, cannot compute tangent")

        return (dx / length, dy / length, dz / length)

    # ========================================================================
    # Export/Tessellation
    # ========================================================================

    def tessellate(self, geom: MockGeometry, tolerance: float = 0.1) -> Tuple[List, List]:
        """
        Mock tessellation - return simple triangle mesh.

        For testing, returns a minimal valid mesh (triangulated box).
        """
        # Simple box mesh for testing
        vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),  # Bottom
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),      # Top
        ]
        triangles = [
            (0, 1, 2), (0, 2, 3),  # Bottom
            (4, 5, 6), (4, 6, 7),  # Top
            (0, 1, 5), (0, 5, 4),  # Sides...
            (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6),
            (3, 0, 4), (3, 4, 7),
        ]
        return vertices, triangles

    def __repr__(self) -> str:
        return f"MockBackend(operations={self.operations_count})"
