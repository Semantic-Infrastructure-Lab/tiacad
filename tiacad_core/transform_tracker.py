"""
TransformTracker - Manages sequential transforms and position tracking

Key responsibilities:
1. Apply transforms in order (translate, rotate, scale)
2. Track current position after each transform
3. Resolve origin references ('current', 'initial')
4. Maintain transform history for debugging
5. Ensure rotation origins are always explicit

Design principle: EXPLICIT OVER IMPLICIT
- Every rotation MUST specify its origin
- Transform order matters (applied top-to-bottom)
- Position tracking enables 'origin: current'
"""

import math
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Union

from .utils.geometry import get_center

logger = logging.getLogger(__name__)


@dataclass
class Transform:
    """
    Individual transform operation

    Attributes:
        type: 'translate' | 'rotate' | 'scale'
        params: Transform-specific parameters
        position_before: Position before this transform
        position_after: Position after this transform
    """
    type: str
    params: Dict[str, Any]
    position_before: Tuple[float, float, float]
    position_after: Tuple[float, float, float]
    origin_resolved: Tuple[float, float, float] = None  # For rotations
    axis_resolved: Tuple[float, float, float] = None    # For rotations


class TransformTracker:
    """
    Tracks geometry transforms and maintains position state

    Usage:
        geometry = cq.Workplane("XY").box(10, 10, 10)
        tracker = TransformTracker(geometry)

        # Apply transforms
        tracker.apply_transform({'type': 'translate', 'offset': [10, 0, 0]})
        tracker.apply_transform({
            'type': 'rotate',
            'angle': 45,
            'axis': 'Z',
            'origin': 'current'  # Uses tracked position
        })

        final_geometry = tracker.get_geometry()
    """

    def __init__(self, geometry):
        """
        Initialize tracker with starting geometry

        Args:
            geometry: CadQuery Workplane or mock for testing
        """
        self._geometry = geometry

        # Extract initial position from geometry
        self.initial_position = self._get_position(geometry)
        self.current_position = self.initial_position

        # Transform history for debugging
        self.history: List[Dict[str, Any]] = []

        # Track last rotation origin (for debugging)
        self.last_rotation_origin: Tuple[float, float, float] = None

    def apply_transform(self, transform: Dict[str, Any]):
        """
        Apply a transform operation

        Args:
            transform: Transform specification dict
                - type: 'translate' | 'rotate'
                - Other params depend on type

        Returns:
            Updated geometry

        Raises:
            ValueError: If transform is invalid or missing required params
        """
        transform_type = transform.get('type')

        if not transform_type:
            raise ValueError("Transform must specify 'type'")

        # Save position before transform
        position_before = self.current_position

        # Dispatch to appropriate handler
        if transform_type == 'translate':
            self._apply_translate(transform)
        elif transform_type == 'rotate':
            self._apply_rotate(transform)
        else:
            raise ValueError(f"Unknown transform type: {transform_type}")

        # Record in history
        position_after = self.current_position
        self.history.append({
            **transform,
            'position_before': position_before,
            'position_after': position_after,
        })

        return self._geometry

    def _apply_translate(self, transform: Dict[str, Any]):
        """Apply translation transform"""
        offset = transform.get('offset')
        if not offset:
            raise ValueError("Translate requires 'offset' parameter")

        # Apply translation to geometry
        self._geometry = self._geometry.translate(tuple(offset))

        # Update current position
        x, y, z = self.current_position
        dx, dy, dz = offset
        self.current_position = (x + dx, y + dy, z + dz)

    def _apply_rotate(self, transform: Dict[str, Any]):
        """Apply rotation transform"""
        # Validate required parameters
        angle = transform.get('angle')
        axis = transform.get('axis')
        origin = transform.get('origin')

        if angle is None:
            raise ValueError("Rotate requires 'angle' parameter")
        if axis is None:
            raise ValueError("Rotate requires 'axis' parameter")
        if origin is None:
            raise ValueError(
                "Rotate requires 'origin' parameter. "
                "Use absolute coords [x,y,z], 'current', or 'initial'. "
                "TiaCAD does not allow implicit rotation origins."
            )

        # Resolve axis to vector
        axis_vector = self._resolve_axis(axis)

        # Resolve origin to coordinates
        origin_coords = self._resolve_origin(origin)

        # Save for debugging
        self.last_rotation_origin = origin_coords

        # Record resolved values in history
        if self.history or 'origin_resolved' not in transform:
            # Update last entry (we append full record later)
            transform['axis_resolved'] = axis_vector
            transform['origin_resolved'] = origin_coords
            transform['origin_specified'] = origin

        # Apply rotation to geometry
        # CadQuery rotate() takes axis as two points: start and end
        axis_start = origin_coords
        axis_end = tuple(
            origin_coords[i] + axis_vector[i]
            for i in range(3)
        )

        self._geometry = self._geometry.rotate(
            axisStartPoint=axis_start,
            axisEndPoint=axis_end,
            angleDegrees=angle
        )

        # Update current position (rotated around origin)
        self.current_position = self._rotate_point(
            self.current_position,
            angle,
            axis_vector,
            origin_coords
        )

    def _resolve_axis(self, axis: Union[str, List[float]]) -> Tuple[float, float, float]:
        """
        Resolve axis specification to normalized vector

        Args:
            axis: 'X' | 'Y' | 'Z' | [x, y, z]

        Returns:
            Normalized axis vector (x, y, z)
        """
        # Named axes
        if axis == 'X':
            return (1.0, 0.0, 0.0)
        elif axis == 'Y':
            return (0.0, 1.0, 0.0)
        elif axis == 'Z':
            return (0.0, 0.0, 1.0)

        # Vector axis - normalize it
        if isinstance(axis, (list, tuple)) and len(axis) == 3:
            x, y, z = axis
            magnitude = math.sqrt(x*x + y*y + z*z)
            if magnitude < 1e-10:
                raise ValueError("Axis vector cannot be zero length")
            return (x/magnitude, y/magnitude, z/magnitude)

        raise ValueError(f"Invalid axis specification: {axis}. Use 'X', 'Y', 'Z', or [x,y,z]")

    def _resolve_origin(self, origin: Union[str, List[float]]) -> Tuple[float, float, float]:
        """
        Resolve origin specification to coordinates

        Args:
            origin: 'current' | 'initial' | [x, y, z]

        Returns:
            Origin coordinates (x, y, z)
        """
        # Keywords
        if origin == 'current':
            return self.current_position
        elif origin == 'initial':
            return self.initial_position

        # Absolute coordinates
        if isinstance(origin, (list, tuple)) and len(origin) == 3:
            return tuple(origin)

        raise ValueError(
            f"Invalid origin specification: {origin}. "
            "Use 'current', 'initial', or [x,y,z]"
        )

    def _rotate_point(
        self,
        point: Tuple[float, float, float],
        angle: float,
        axis: Tuple[float, float, float],
        origin: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Rotate a point around an axis through origin

        Uses Rodrigues' rotation formula:
        https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula

        Args:
            point: Point to rotate (x, y, z)
            angle: Rotation angle in degrees
            axis: Normalized rotation axis (x, y, z)
            origin: Point on rotation axis (x, y, z)

        Returns:
            Rotated point (x, y, z)
        """
        # Convert angle to radians
        theta = math.radians(angle)

        # Translate point to origin
        px, py, pz = point
        ox, oy, oz = origin
        x = px - ox
        y = py - oy
        z = pz - oz

        # Axis components (already normalized)
        ux, uy, uz = axis

        # Rodrigues' formula
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        # Dot product: u · p
        dot = ux*x + uy*y + uz*z

        # Cross product: u × p
        cross_x = uy*z - uz*y
        cross_y = uz*x - ux*z
        cross_z = ux*y - uy*x

        # Rotated point = p*cos(θ) + (u×p)*sin(θ) + u(u·p)(1-cos(θ))
        rx = x*cos_theta + cross_x*sin_theta + ux*dot*(1 - cos_theta)
        ry = y*cos_theta + cross_y*sin_theta + uy*dot*(1 - cos_theta)
        rz = z*cos_theta + cross_z*sin_theta + uz*dot*(1 - cos_theta)

        # Translate back
        return (rx + ox, ry + oy, rz + oz)

    def _get_position(self, geometry) -> Tuple[float, float, float]:
        """
        Extract current position from geometry

        For testing with mocks: checks center_point attribute
        For real CadQuery: uses bounding box center

        Args:
            geometry: CadQuery Workplane or mock

        Returns:
            Center position (x, y, z)

        Note:
            Uses shared geometry utility to avoid code duplication.
            Fixed: Previously had bare 'except' which caught system interrupts.
        """
        return get_center(geometry)

    def get_geometry(self):
        """Get the current transformed geometry"""
        return self._geometry

    def get_summary(self) -> str:
        """
        Generate human-readable summary of transforms

        Returns:
            Multi-line string describing transform sequence
        """
        if not self.history:
            return "No transforms applied"

        lines = [f"Transform sequence ({len(self.history)} steps):"]

        for i, t in enumerate(self.history, 1):
            ttype = t['type']

            if ttype == 'translate':
                offset = t.get('offset', [0, 0, 0])
                lines.append(f"  {i}. Translate by {offset}")

            elif ttype == 'rotate':
                angle = t.get('angle', 0)
                axis = t.get('axis', '?')
                origin_spec = t.get('origin_specified', t.get('origin'))
                origin_resolved = t.get('origin_resolved')

                lines.append(f"  {i}. Rotate {angle}° around {axis}")
                if origin_spec == 'current':
                    lines.append(f"      Origin: current → {origin_resolved}")
                elif origin_spec == 'initial':
                    lines.append(f"      Origin: initial → {origin_resolved}")
                else:
                    lines.append(f"      Origin: {origin_resolved}")

            # Show position after each step
            pos_after = t.get('position_after')
            if pos_after:
                lines.append(f"      Position: {pos_after}")

        return '\n'.join(lines)

    def __repr__(self):
        """String representation"""
        return (
            f"TransformTracker("
            f"initial={self.initial_position}, "
            f"current={self.current_position}, "
            f"transforms={len(self.history)})"
        )


# ============================================================================
# Utility Functions
# ============================================================================

def apply_transform_sequence(geometry, transforms: List[Dict[str, Any]]):
    """
    Apply a sequence of transforms to geometry

    Args:
        geometry: Starting CadQuery Workplane
        transforms: List of transform specifications

    Returns:
        Transformed geometry

    Example:
        result = apply_transform_sequence(box, [
            {'type': 'translate', 'offset': [10, 0, 0]},
            {'type': 'rotate', 'angle': 45, 'axis': 'Z', 'origin': 'current'},
        ])
    """
    tracker = TransformTracker(geometry)

    for transform in transforms:
        tracker.apply_transform(transform)

    return tracker.get_geometry()


def debug_transform_sequence(geometry, transforms: List[Dict[str, Any]]) -> List[Any]:
    """
    Apply transforms and return geometry at EACH step (for debugging)

    Args:
        geometry: Starting CadQuery Workplane
        transforms: List of transform specifications

    Returns:
        List of geometries (one per step, including initial)

    Example:
        steps = debug_transform_sequence(arm, [
            {'type': 'translate', 'offset': [10, 0, 0]},
            {'type': 'rotate', 'angle': 45, 'axis': 'Z', 'origin': [0,0,0]},
        ])
        # steps[0] = original
        # steps[1] = after translate
        # steps[2] = after rotate
    """
    tracker = TransformTracker(geometry)
    steps = [geometry]  # Include initial state

    for transform in transforms:
        tracker.apply_transform(transform)
        # Clone geometry at this step
        steps.append(tracker.get_geometry())

    return steps


# ============================================================================
# Documentation
# ============================================================================

__doc__ = """
TransformTracker - Sequential transform manager with explicit origins

Key Features:
- Tracks position through transform sequence
- Resolves 'origin: current' and 'origin: initial'
- Maintains transform history for debugging
- Enforces explicit rotation origins (no ambiguity!)
- Applies transforms in order (composition matters)

Usage Example:

    from tiacad_core.transform_tracker import TransformTracker

    # Create geometry
    geometry = cq.Workplane("XY").box(10, 10, 10)

    # Apply transforms with tracking
    tracker = TransformTracker(geometry)

    # Move to position
    tracker.apply_transform({'type': 'translate', 'offset': [10, 20, 0]})

    # Rotate around current position (attachment point)
    tracker.apply_transform({
        'type': 'rotate',
        'angle': 10,
        'axis': 'X',
        'origin': 'current'  # Rotates around (10, 20, 0)
    })

    # Get final geometry
    result = tracker.get_geometry()

    # Debug: print transform summary
    print(tracker.get_summary())

See tests/test_transform_tracker.py for comprehensive examples.
"""
