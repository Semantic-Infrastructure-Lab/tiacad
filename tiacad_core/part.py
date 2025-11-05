"""
TiaCAD Part Representation

Solves Critical Gap #1: Internal Data Model

Design Decision: Start simple (Option A from assessment)
- Store CadQuery Workplane directly (or backend geometry)
- Add metadata dictionary for extensibility
- Track transforms for debugging/origin resolution

Phase 2 Enhancement:
- Support geometry backend injection
- Enable fast unit testing with MockBackend
- Maintain backward compatibility
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

# Avoid circular imports
if TYPE_CHECKING:
    from .geometry import GeometryBackend

from .utils.geometry import get_center as utils_get_center, get_bounding_box as utils_get_bounding_box


@dataclass
class Part:
    """Represents a geometric part in TiaCAD

    This is the core internal representation used during YAML processing.

    Design Philosophy:
    - Simple: Wraps geometry from any backend
    - Extensible: Metadata dict for future features
    - Debuggable: Track transform history
    - Testable: Support fast mock backend for unit tests

    Attributes:
        name: Part identifier (must be unique in assembly)
        geometry: Geometry object (CadQuery Workplane or MockGeometry)
        metadata: Flexible key-value storage for:
            - Attachment points (future)
            - Material properties (future)
            - Rendering hints (future)
            - Custom user data
        transform_history: List of transforms applied (for debugging/undo)
        current_position: Tracked position for "origin: current" support
        backend: Optional geometry backend (for backend-specific operations)
    """

    name: str
    geometry: Any  # CadQuery Workplane, MockGeometry, or other backend type
    metadata: Dict[str, Any] = field(default_factory=dict)
    transform_history: List[Dict[str, Any]] = field(default_factory=list)
    current_position: Optional[Tuple[float, float, float]] = None
    backend: Optional['GeometryBackend'] = None

    def __post_init__(self):
        """Initialize current_position to geometry center if not set"""
        if self.current_position is None:
            self.current_position = self._calculate_center()

    def _calculate_center(self) -> Tuple[float, float, float]:
        """Calculate geometric center of current geometry

        Returns:
            (x, y, z) tuple of center point

        Note:
            If backend is provided, uses backend.get_center().
            Otherwise falls back to utils function for backward compatibility.
        """
        if self.backend is not None:
            return self.backend.get_center(self.geometry)
        else:
            # Backward compatibility: use utils function
            return utils_get_center(self.geometry)

    def update_position(self, new_position: Tuple[float, float, float]):
        """Update tracked position after transform

        Args:
            new_position: New (x, y, z) position
        """
        self.current_position = new_position

    def add_transform(self, transform_type: str, params: Dict[str, Any]):
        """Record a transform in history

        Args:
            transform_type: Type of transform ("translate", "rotate", etc.)
            params: Transform parameters
        """
        self.transform_history.append({
            'type': transform_type,
            'params': params,
            'position_before': self.current_position,
        })

    def get_bounds(self) -> Dict[str, Tuple[float, float, float]]:
        """Get bounding box of geometry

        Returns:
            Dictionary with 'min', 'max', and 'center' tuples

        Note:
            If backend is provided, uses backend.get_bounding_box().
            Otherwise falls back to utils function for backward compatibility.
        """
        if self.backend is not None:
            return self.backend.get_bounding_box(self.geometry)
        else:
            # Backward compatibility: use utils function
            return utils_get_bounding_box(self.geometry)

    def get_center(self) -> Tuple[float, float, float]:
        """Get current geometric center

        Returns:
            (x, y, z) tuple of center point
        """
        return self._calculate_center()

    def clone(self, new_name: str) -> 'Part':
        """Create a copy of this part with a new name

        Args:
            new_name: Name for the cloned part

        Returns:
            New Part instance with copied geometry
        """
        # Geometry copy (works for both CadQuery and MockGeometry)
        new_geometry = self.geometry

        return Part(
            name=new_name,
            geometry=new_geometry,
            metadata=self.metadata.copy(),
            transform_history=self.transform_history.copy(),
            current_position=self.current_position,
            backend=self.backend,  # Preserve backend
        )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"Part(name='{self.name}', position={self.current_position}, transforms={len(self.transform_history)})"


class PartRegistry:
    """Registry for managing parts during build process

    Responsibilities:
    - Store all parts by name
    - Validate uniqueness
    - Support lookup and iteration
    """

    def __init__(self):
        self._parts: Dict[str, Part] = {}

    def add(self, part: Part):
        """Add a part to the registry

        Args:
            part: Part to add

        Raises:
            ValueError: If part name already exists
        """
        if part.name in self._parts:
            raise ValueError(f"Part '{part.name}' already exists in registry")
        self._parts[part.name] = part

    def get(self, name: str) -> Part:
        """Retrieve a part by name

        Args:
            name: Part name

        Returns:
            Part instance

        Raises:
            KeyError: If part doesn't exist
        """
        if name not in self._parts:
            available = ', '.join(self._parts.keys())
            raise KeyError(
                f"Part '{name}' not found.\n"
                f"Available parts: {available}"
            )
        return self._parts[name]

    def exists(self, name: str) -> bool:
        """Check if part exists

        Args:
            name: Part name

        Returns:
            True if part exists
        """
        return name in self._parts

    def list_parts(self) -> List[str]:
        """List all part names

        Returns:
            List of part names
        """
        return list(self._parts.keys())

    def clear(self):
        """Remove all parts from registry"""
        self._parts.clear()

    def __len__(self) -> int:
        """Number of parts in registry"""
        return len(self._parts)

    def __contains__(self, name: str) -> bool:
        """Support 'in' operator"""
        return self.exists(name)
