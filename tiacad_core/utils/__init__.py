"""
TiaCAD Utility Modules

Shared utility functions used across TiaCAD components.
"""

from .geometry import get_center, get_bounding_box
from .exceptions import (
    TiaCADError,
    GeometryError,
    InvalidGeometryError,
    TransformError,
    SelectorError,
    PointResolutionError,
)

__all__ = [
    # Geometry utilities
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
