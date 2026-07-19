"""
Tests for Part/TransformTracker orientation tracking (TCAD-CON-2).

Regression coverage for the bug where `axis_x`/`axis_y`/`axis_z` part-local
spatial references always pointed along WORLD axes regardless of a part's
actual applied rotation. Fixed by tracking a cumulative `current_orientation`
rotation matrix on Part/TransformTracker and applying it in
SpatialResolver._resolve_part_local. Identified during TCAD-CON-1 constraint
solver scoping as a latent bug blocking constraint-driven rotations from
feeding correctly into other spatial references. See ROADMAP.md and
tt show TCAD-CON-2.
"""

import numpy as np
import pytest

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.spatial_resolver import SpatialResolver
from tiacad_core.transform_tracker import TransformTracker


def _approx_vec(v, expected, abs_tol=1e-6):
    assert v == pytest.approx(expected, abs=abs_tol)


class TestTransformTrackerOrientation:
    def test_unrotated_tracker_has_identity_orientation(self):
        tracker = TransformTracker(geometry=None, backend=_StubBackend())
        assert np.allclose(tracker.current_orientation, np.eye(3))

    def test_single_rotation_updates_orientation(self):
        tracker = TransformTracker(geometry=None, backend=_StubBackend())
        tracker.apply_transform({
            'type': 'rotate', 'angle': 90, 'axis': 'Z', 'origin': 'current'
        })
        # World X should now map to world Y
        rotated_x = tracker.current_orientation @ np.array([1.0, 0.0, 0.0])
        _approx_vec(rotated_x, [0.0, 1.0, 0.0])

    def test_translate_does_not_affect_orientation(self):
        tracker = TransformTracker(geometry=None, backend=_StubBackend())
        tracker.apply_transform({'type': 'translate', 'offset': [10, 0, 0]})
        assert np.allclose(tracker.current_orientation, np.eye(3))

    def test_composed_rotations_accumulate(self):
        tracker = TransformTracker(geometry=None, backend=_StubBackend())
        tracker.apply_transform({'type': 'rotate', 'angle': 90, 'axis': 'Z', 'origin': 'current'})
        tracker.apply_transform({'type': 'rotate', 'angle': 90, 'axis': 'X', 'origin': 'current'})
        # Two composed 90 degree rotations: X -> Y (first rotation), then
        # rotating about X leaves Y-derived vectors alone only for the axis
        # itself; verify via a known composition instead of guessing by hand.
        expected = TransformTracker._rotation_matrix(90, (1, 0, 0)) @ \
            TransformTracker._rotation_matrix(90, (0, 0, 1))
        assert np.allclose(tracker.current_orientation, expected)


class _StubBackend:
    """Minimal backend stub — enough for TransformTracker's position/rotate calls
    when geometry itself is irrelevant to the assertion (orientation only)."""

    def get_center(self, geometry):
        return (0.0, 0.0, 0.0)

    def translate(self, geometry, offset):
        return geometry

    def rotate(self, geometry, axis_start, axis_end, angle):
        return geometry


class TestPartLocalAxisReferencesReflectRotation:
    """End-to-end: build a real part via the YAML pipeline, rotate it, then
    verify its axis_x/axis_y part-local references follow the rotation."""

    def test_rotated_part_axis_x_follows_rotation(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
    rotate: {angle: 90, axis: Z, origin: [0, 0, 0]}
""")
        resolver = SpatialResolver(doc.parts, doc.references)
        ref_x = resolver.resolve('block.axis_x')
        ref_y = resolver.resolve('block.axis_y')

        _approx_vec(ref_x.orientation.tolist(), [0.0, 1.0, 0.0])
        _approx_vec(ref_y.orientation.tolist(), [-1.0, 0.0, 0.0])

    def test_unrotated_part_axis_x_is_world_x(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
""")
        resolver = SpatialResolver(doc.parts, doc.references)
        ref_x = resolver.resolve('block.axis_x')
        _approx_vec(ref_x.orientation.tolist(), [1.0, 0.0, 0.0])

    def test_rotation_via_transform_operation_also_updates_axis(self):
        doc = TiaCADParser.parse_string("""
parts:
  block:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center

operations:
  rotated_block:
    type: transform
    input: block
    transforms:
      - rotate: {angle: 90, axis: Z, origin: [0, 0, 0]}
""")
        resolver = SpatialResolver(doc.parts, doc.references)
        ref_x = resolver.resolve('rotated_block.axis_x')
        _approx_vec(ref_x.orientation.tolist(), [0.0, 1.0, 0.0])
