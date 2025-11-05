"""
Geometry Backend System

Provides abstraction layer between TiaCAD and CAD kernels.

Available Backends:
- CadQueryBackend: Production backend using CadQuery
- MockBackend: Fast backend for unit testing

Usage:
    # Production code
    from tiacad_core.geometry import CadQueryBackend
    backend = CadQueryBackend()
    box = backend.create_box(10, 10, 10)

    # Unit tests
    from tiacad_core.geometry import MockBackend
    backend = MockBackend()
    box = backend.create_box(10, 10, 10)  # 100x faster!

    # With Part
    from tiacad_core.part import Part
    part = Part("test", geometry=box, backend=backend)
"""

from .base import GeometryBackend
from .cadquery_backend import CadQueryBackend
from .mock_backend import MockBackend, MockGeometry

__all__ = [
    'GeometryBackend',
    'CadQueryBackend',
    'MockBackend',
    'MockGeometry',
]


# Default backend management
_default_backend = None


def get_default_backend() -> GeometryBackend:
    """
    Get or create default geometry backend.

    Returns:
        The default backend (CadQueryBackend by default)

    Examples:
        >>> backend = get_default_backend()
        >>> isinstance(backend, CadQueryBackend)
        True
    """
    global _default_backend
    if _default_backend is None:
        _default_backend = CadQueryBackend()
    return _default_backend


def set_default_backend(backend: GeometryBackend):
    """
    Set the default geometry backend.

    Useful for testing - set MockBackend as default for fast tests.

    Args:
        backend: Backend instance to use as default

    Examples:
        >>> # In test setup
        >>> set_default_backend(MockBackend())
        >>> # Now all Part creation uses mock backend
    """
    global _default_backend
    _default_backend = backend


def reset_default_backend():
    """
    Reset to default CadQuery backend.

    Useful in test teardown to ensure clean state.

    Examples:
        >>> set_default_backend(MockBackend())
        >>> # ... run tests ...
        >>> reset_default_backend()  # Back to CadQuery
    """
    global _default_backend
    _default_backend = CadQueryBackend()
