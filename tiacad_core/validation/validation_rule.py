"""
Base Validation Rule for TiaCAD Assembly Validator

Defines the abstract base class for all validation rules.
"""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
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
