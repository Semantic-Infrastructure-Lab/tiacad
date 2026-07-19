"""
Base Validation Rule for TiaCAD Assembly Validator

Defines the abstract base class for all validation rules.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, TYPE_CHECKING
from .validation_constants import ValidationConstants

if TYPE_CHECKING:
    from .validation_types import ValidationIssue


class ValidationRule(ABC):
    """
    Abstract base class for validation rules.

    Each rule implements a specific validation check on a TiaCAD document.
    Rules are independent, testable, and composable.
    """

    def __init__(self, tolerance: float = ValidationConstants.DEFAULT_TOLERANCE):
        """
        Initialize validation rule.

        Args:
            tolerance: Distance tolerance for geometric checks (mm)
        """
        self.tolerance = tolerance
        self.constants = ValidationConstants

    @abstractmethod
    def check(self, document) -> List['ValidationIssue']:
        """
        Perform validation check on document.

        Args:
            document: TiaCADDocument instance to validate

        Returns:
            List of ValidationIssue objects found (empty if no issues)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable name of this validation rule."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """
        Return category of this validation rule.

        Categories: "connectivity", "geometry", "appearance", "parameters", "positioning"
        """
        pass

    # Helper methods available to all rules

    def _get_parts_dict(self, document) -> dict:
        """
        Get dictionary of all parts from document.

        Args:
            document: TiaCADDocument instance

        Returns:
            Dictionary mapping part names to Part objects
        """
        if hasattr(document.parts, '_parts'):
            return document.parts._parts
        elif hasattr(document.parts, 'list_parts'):
            return {name: document.parts.get(name) for name in document.parts.list_parts()}
        return {}

    def _get_bounding_box(self, geometry):
        """
        Get bounding box from a Part or geometry object.

        Handles:
        - Part objects with `get_bounds()` (backend-aware)
        - CadQuery Workplanes / Shapes
        - Mock geometries that expose BoundingBox()

        Args:
            geometry: Part or geometry object

        Returns:
            BoundingBox-like object with xmin/xmax/... and xlen/ylen/zlen

        Raises:
            AttributeError: If geometry doesn't support bounding box
        """
        if hasattr(geometry, 'get_bounds'):
            bounds = geometry.get_bounds()
            return _BoundsAdapter(bounds)
        if hasattr(geometry, 'val'):
            # CadQuery Workplane - get the shape
            return geometry.val().BoundingBox()
        else:
            # Direct shape
            return geometry.BoundingBox()

    def _bbox_center(self, bbox) -> Tuple[float, float, float]:
        """Calculate center point of a bounding box (for ValidationIssue.world_position)."""
        return (
            (bbox.xmin + bbox.xmax) / 2,
            (bbox.ymin + bbox.ymax) / 2,
            (bbox.zmin + bbox.zmax) / 2,
        )

    def _part_center(self, part) -> Optional[Tuple[float, float, float]]:
        """Best-effort world-position center for a part, for trust-render annotation."""
        try:
            return self._bbox_center(self._get_bounding_box(part))
        except Exception:
            return None

    def _get_operation_attr(self, operation, attr_name, default=None):
        """
        Get attribute from operation (handles both dict and object).

        Args:
            operation: Operation (dict or object)
            attr_name: Attribute name to get
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        if isinstance(operation, dict):
            return operation.get(attr_name, default)
        else:
            return getattr(operation, attr_name, default)

    def _get_all_parts(self, document) -> set:
        """Get set of all part names known to the document (primitives and operation results)."""
        if hasattr(document.parts, 'list_parts'):
            return set(document.parts.list_parts())
        return set()

    def _get_used_parts(self, document) -> set:
        """
        Get set of part/operation names referenced as an input by any operation.

        Operations are plain dicts in the parsed document, not objects, so this
        must go through `_get_operation_attr` rather than `hasattr`/`getattr`
        directly (those always miss on a dict and silently return nothing).
        """
        used_parts = set()

        operations = getattr(document, 'operations', None)
        if not operations:
            return used_parts

        for operation in operations.values():
            input_name = self._get_operation_attr(operation, 'input')
            if input_name:
                used_parts.add(input_name)

            base_name = self._get_operation_attr(operation, 'base')
            if base_name:
                used_parts.add(base_name)

            subtract_names = self._get_operation_attr(operation, 'subtract')
            if subtract_names:
                used_parts.update(subtract_names)

            input_names = self._get_operation_attr(operation, 'inputs')
            if input_names:
                used_parts.update(input_names)

        return used_parts

    def _get_exported_parts(self, document) -> set:
        """
        Get set of part names referenced by the document's export configuration.

        The live document attribute is `export_config` (a dict built by
        `build_export_config`), not `export` — `hasattr(document, 'export')`
        always misses.
        """
        exported_parts = set()

        export_config = getattr(document, 'export_config', None) or {}

        default_part = export_config.get('default_part')
        if default_part:
            exported_parts.add(default_part)

        for entry in export_config.get('parts', None) or []:
            name = entry.get('name') if isinstance(entry, dict) else entry
            if name:
                exported_parts.add(name)

        return exported_parts


class _BoundsAdapter:
    """Adapter that gives Part.get_bounds() dicts a BoundingBox-like surface."""

    def __init__(self, bounds: dict):
        min_corner = bounds['min']
        max_corner = bounds['max']
        self.xmin, self.ymin, self.zmin = min_corner
        self.xmax, self.ymax, self.zmax = max_corner
        self.xlen = self.xmax - self.xmin
        self.ylen = self.ymax - self.ymin
        self.zlen = self.zmax - self.zmin
