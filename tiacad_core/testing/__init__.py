"""
TiaCAD Testing Utilities

This module provides utilities for testing geometric correctness in TiaCAD.
Part of the Testing Confidence Plan (v3.1+).

Modules:
    measurements: Distance measurement, bounding box utilities
    orientation: Rotation angles, normal vectors, alignment (v3.1+)
    dimensions: Volume, surface area, feature detection (v3.1+)
    visual_regression: Visual testing framework (v3.2+)

Example:
    from tiacad_core.testing.measurements import measure_distance

    # Measure distance between two parts
    dist = measure_distance(box, cylinder,
                           ref1="face_top.center",
                           ref2="face_bottom.center")
    assert dist < 0.001  # Verify parts are touching

See also:
    docs/TESTING_CONFIDENCE_PLAN.md
    docs/TESTING_QUICK_REFERENCE.md
"""

from .measurements import (
    measure_distance,
    get_bounding_box_dimensions,
)

from .orientation import (
    get_orientation_angles,
    get_normal_vector,
    parts_aligned,
)

from .dimensions import (
    get_dimensions,
    get_volume,
    get_surface_area,
)

__all__ = [
    'measure_distance',
    'get_bounding_box_dimensions',
    'get_orientation_angles',
    'get_normal_vector',
    'parts_aligned',
    'get_dimensions',
    'get_volume',
    'get_surface_area',
]
