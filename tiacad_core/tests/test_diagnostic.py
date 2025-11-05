"""
Diagnostic test to check for sys.modules pollution.
"""
import sys
import pytest


def test_cadquery_module_is_real():
    """Verify cadquery module is the real library, not a mock"""
    import cadquery as cq

    # Check it's not a Mock
    assert not str(type(cq)).startswith("<class 'unittest.mock")
    assert not str(type(cq)).startswith("<class 'mock.")

    # Check sys.modules has real cadquery
    cq_module = sys.modules.get('cadquery')
    assert cq_module is not None
    assert not str(type(cq_module)).startswith("<class 'unittest.mock")

    # Try to create something
    box = cq.Workplane("XY").box(10, 10, 10)
    assert box is not None

    # Try to get a shape
    shape = box.val()
    assert shape is not None

    # Try to tessellate
    vertices, triangles = shape.tessellate(0.1)
    assert len(vertices) > 0
    assert len(triangles) > 0

    print(f"CadQuery is real: {type(cq)}")
    print(f"Tessellation returned {len(vertices)} vertices, {len(triangles)} triangles")
