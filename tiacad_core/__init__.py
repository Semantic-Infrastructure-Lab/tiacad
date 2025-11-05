"""
TiaCAD Core - Implementation Classes

This package contains the core implementation classes for TiaCAD:
- Part: Internal representation of parts with position tracking
- SelectorResolver: Maps YAML selectors to CadQuery geometry
- TransformTracker: Tracks positions through transform sequences
- PointResolver: Resolves point expressions to coordinates (WIP)

Version: 0.1.0-alpha
Status: Phase 1 Implementation
"""

__version__ = "0.1.0-alpha"

from .part import Part, PartRegistry
from .selector_resolver import SelectorResolver
from .transform_tracker import TransformTracker
from .point_resolver import PointResolver
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
    'PointResolver',
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
