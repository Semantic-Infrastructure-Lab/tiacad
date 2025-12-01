"""
TiaCAD Core - Implementation Classes

This package contains the core implementation classes for TiaCAD:
- Part: Internal representation of parts with position tracking
- SelectorResolver: Maps YAML selectors to CadQuery geometry
- TransformTracker: Tracks positions through transform sequences
- SpatialResolver: Resolves spatial references (position + orientation)

Version: 3.1.1
Status: Production - Visual Regression Testing Complete
"""

__version__ = "3.1.1"

from .part import Part, PartRegistry
from .selector_resolver import SelectorResolver
from .transform_tracker import TransformTracker
from .spatial_resolver import SpatialResolver
from .utils import (
    get_center,
    get_bounding_box,
    TiaCADError,
    GeometryError,
    InvalidGeometryError,
    TransformError,
    SelectorError,
    PointResolutionError,
)

__all__ = [
    # Core components
    'Part',
    'PartRegistry',
    'SelectorResolver',
    'TransformTracker',
    'SpatialResolver',
    # Utilities
    'get_center',
    'get_bounding_box',
    # Exceptions
    'TiaCADError',
    'GeometryError',
    'InvalidGeometryError',
    'TransformError',
    'SelectorError',
    'PointResolutionError',
]
