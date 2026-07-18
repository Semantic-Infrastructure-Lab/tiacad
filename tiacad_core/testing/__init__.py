"""
TiaCAD Testing Utilities

This module provides utilities for testing geometric correctness in TiaCAD.
Part of the Testing Confidence Plan (v3.1+).

Modules:
    measurements: Distance measurement, bounding box utilities
    orientation: Rotation angles, normal vectors, alignment (v3.1+)
    dimensions: Volume, surface area, feature detection (v3.1+)
    visual_regression: Visual testing framework (v3.1 Phase 2)

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
    docs/TESTING_GUIDE.md
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

from .geometry_summary import (
    summarize_part_geometry,
    summarize_part_registry,
    GeometrySummaryError,
)

from .golden_step import (
    topology_signature,
    topology_signature_from_step,
    check_against_golden_step,
    export_golden_step,
    TopologySignature,
    GoldenStepError,
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
    'summarize_part_geometry',
    'summarize_part_registry',
    'GeometrySummaryError',
    'topology_signature',
    'topology_signature_from_step',
    'check_against_golden_step',
    'export_golden_step',
    'TopologySignature',
    'GoldenStepError',
    'VisualRegressionTester',
    'VisualDiffResult',
    'RenderConfig',
    'pytest_visual_compare',
    'differential_check',
    'discover_eligible_trust_models',
    'DifferentialResult',
    'DifferentialError',
]


def __getattr__(name):
    """Lazily import heavy visual-regression / differential-testing helpers on demand."""
    if name in {
        'VisualRegressionTester',
        'VisualDiffResult',
        'RenderConfig',
        'pytest_visual_compare',
    }:
        from .visual_regression import (
            RenderConfig,
            VisualDiffResult,
            VisualRegressionTester,
            pytest_visual_compare,
        )

        exports = {
            'VisualRegressionTester': VisualRegressionTester,
            'VisualDiffResult': VisualDiffResult,
            'RenderConfig': RenderConfig,
            'pytest_visual_compare': pytest_visual_compare,
        }
        return exports[name]

    if name in {
        'differential_check',
        'discover_eligible_trust_models',
        'DifferentialResult',
        'DifferentialError',
    }:
        from .differential import (
            DifferentialError,
            DifferentialResult,
            differential_check,
            discover_eligible_trust_models,
        )

        exports = {
            'differential_check': differential_check,
            'discover_eligible_trust_models': discover_eligible_trust_models,
            'DifferentialResult': DifferentialResult,
            'DifferentialError': DifferentialError,
        }
        return exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
