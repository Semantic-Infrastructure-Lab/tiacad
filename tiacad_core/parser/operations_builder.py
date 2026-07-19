"""
OperationsBuilder - Build and execute operations from YAML specifications

Handles transformation and boolean operations on Part objects using the existing
TransformTracker, SpatialResolver, and BooleanBuilder components.

Phase 1 Implementation:
- Transform operations (translate, rotate)
- Sequential execution
- Part position tracking

Phase 2 Implementation:
- Boolean operations (union, difference, intersection)
- Pattern operations (linear, circular, grid)
- Finishing operations (fillet, chamfer)

Phase 3 Implementation (v3.0):
- Unified spatial references with SpatialResolver
- Orientation-aware transforms
- Reference-based positioning

Author: TIA
Version: 3.1.1
"""

import logging
import math
import warnings
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
import numpy as np

from ..part import Part, PartRegistry
from ..transform_tracker import TransformTracker
from ..spatial_resolver import SpatialResolver
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver
from .boolean_builder import BooleanBuilder
from .pattern_builder import PatternBuilder
from .finishing_builder import FinishingBuilder
from .extrude_builder import ExtrudeBuilder
from .revolve_builder import RevolveBuilder
from .sweep_builder import SweepBuilder
from .loft_builder import LoftBuilder
from .hull_builder import HullBuilder
from .text_builder import TextBuilder
from .gusset_builder import GussetBuilder

if TYPE_CHECKING:
    from ..geometry import GeometryBackend

logger = logging.getLogger(__name__)


class OperationsBuilderError(TiaCADError):
    """Error during operations building or execution"""
    def __init__(self, message: str, operation_name: Optional[str] = None):
        super().__init__(message)
        self.operation_name = operation_name


class OperationsBuilder:
    """
    Builds and executes operations from YAML specifications.

    Supported Operations:
    - transform: Move and rotate parts (translate, rotate)
    - boolean: Combine parts (union, difference, intersection)
    - pattern: Create arrays of parts (linear, circular, grid)
    - finishing: Apply finishing touches (fillet, chamfer)
    - extrude: Extrude sketches to create 3D geometry
    - revolve: Revolve sketches around an axis
    - sweep: Sweep sketches along a path
    - loft: Loft between multiple profiles
    - hull: Create convex hull around multiple parts
    - text: Engrave or emboss text on part faces
    - gusset: Create structural triangular supports between parts

    Usage:
        builder = OperationsBuilder(registry, param_resolver)
        result_registry = builder.execute_operations(yaml_data['operations'])
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver,
                 sketches: Optional[Dict[str, Any]] = None,
                 spatial_resolver: Optional[SpatialResolver] = None,
                 backend: Optional["GeometryBackend"] = None):
        """
        Initialize operations builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
            sketches: Dictionary of sketches for extrude/revolve/sweep/loft (optional)
            spatial_resolver: SpatialResolver for reference resolution (optional)
            backend: CadQuery backend to stamp onto parts produced by sketch-based
                operations (extrude/revolve/sweep/loft/hull/text/gusset); falls back
                to the process-global default when not given
        """
        self.registry = part_registry
        self.resolver = parameter_resolver
        self.sketches = sketches or {}
        self.spatial_resolver = spatial_resolver or SpatialResolver(part_registry, {})
        self.boolean_builder = BooleanBuilder(part_registry, parameter_resolver)
        self.pattern_builder = PatternBuilder(part_registry, parameter_resolver)
        self.finishing_builder = FinishingBuilder(part_registry, parameter_resolver)
        # Sketch-based operation builders (Phase 3)
        self.extrude_builder = ExtrudeBuilder(part_registry, self.sketches, parameter_resolver, backend=backend)
        self.revolve_builder = RevolveBuilder(part_registry, self.sketches, parameter_resolver, backend=backend)
        self.sweep_builder = SweepBuilder(part_registry, self.sketches, parameter_resolver, backend=backend)
        self.loft_builder = LoftBuilder(part_registry, self.sketches, parameter_resolver, backend=backend)
        self.hull_builder = HullBuilder(part_registry, parameter_resolver, backend=backend)
        self.text_builder = TextBuilder(part_registry, parameter_resolver, backend=backend)
        self.gusset_builder = GussetBuilder(part_registry, parameter_resolver, backend=backend)

        # op_type -> handler(name, resolved_spec). Built once here rather than
        # dispatched via if/elif in execute_operation, so adding an operation
        # type is a one-line registration instead of another branch.
        self._op_dispatch = {
            'transform': self._execute_transform,
            'boolean': self.boolean_builder.execute_boolean_operation,
            'pattern': self.pattern_builder.execute_pattern_operation,
            'finishing': self.finishing_builder.execute_finishing_operation,
            'extrude': self.extrude_builder.execute_extrude_operation,
            'revolve': self.revolve_builder.execute_revolve_operation,
            'sweep': self.sweep_builder.execute_sweep_operation,
            'loft': self.loft_builder.execute_loft_operation,
            'hull': self.hull_builder.execute_hull_operation,
            'text': self.text_builder.execute_text_operation,
            'gusset': self.gusset_builder.execute_gusset_operation,
        }

    def execute_operations(self, operations_spec: Dict[str, Dict]) -> PartRegistry:
        """
        Execute all operations from YAML specification.

        Operations are executed in order, creating new parts in the registry.

        Args:
            operations_spec: Dictionary of operation_name → operation_definition

        Returns:
            Updated PartRegistry with operation results

        Raises:
            OperationsBuilderError: If operation execution fails
        """
        for op_name, op_def in operations_spec.items():
            try:
                logger.info(f"Executing operation '{op_name}'")
                self.execute_operation(op_name, op_def)
                logger.debug(f"Operation '{op_name}' completed successfully")
            except Exception as e:
                raise OperationsBuilderError(
                    f"Failed to execute operation '{op_name}': {str(e)}",
                    operation_name=op_name
                ) from e

        logger.info(f"Executed {len(operations_spec)} operations successfully")
        return self.registry

    def apply_inline_part_transforms(self, parts_spec: Dict[str, Dict]) -> None:
        """
        Apply each part's own inline `translate:`/`rotate:` spec (schema v3.0),
        in place, to the already-built part of the same name in the registry.

        This is distinct from `operations: type: transform`, which creates a new,
        separately-named part. Inline part-level translate/rotate re-positions the
        part itself — e.g. `left_pillar.translate: {to: platform.face_top, ...}` —
        using the same anchor-resolution machinery (TransformTracker +
        spatial_resolver) as the transform operation, so `platform.face_top` and
        other auto-generated/user references resolve identically either way.

        Must run after every part in `parts_spec` already exists in the registry
        (so any part may anchor to any sibling's auto-generated references) and
        before `operations_spec` executes (so operations see the final position).
        No-op for parts with neither key.

        Args:
            parts_spec: Dictionary of part_name → part_definition (the YAML `parts:` section)
        """
        for part_name, part_def in parts_spec.items():
            if not isinstance(part_def, dict):
                continue
            has_translate = 'translate' in part_def
            has_rotate = 'rotate' in part_def
            if not has_translate and not has_rotate:
                continue

            resolved = self.resolver.resolve(part_def)
            part = self.registry.get(part_name)
            tracker = TransformTracker(part.geometry, backend=part.backend)

            try:
                if has_translate:
                    for vec in self._as_translate_sequence(resolved['translate']):
                        self._apply_translate(tracker, vec, part_name)
                if has_rotate:
                    for rot in self._as_rotate_sequence(resolved['rotate']):
                        self._apply_rotate(tracker, rot, part_name)
            except Exception as e:
                raise OperationsBuilderError(
                    f"Inline translate/rotate failed for part '{part_name}': {str(e)}",
                    operation_name=part_name
                ) from e

            self.registry.replace(Part(
                name=part_name,
                geometry=tracker.get_geometry(),
                metadata=part.metadata,
                current_position=tracker.current_position,
                backend=part.backend,
            ))
            logger.debug(f"Applied inline translate/rotate to part '{part_name}'")

    @staticmethod
    def _as_translate_sequence(value) -> list:
        """Normalize a part-level `translate:` value into a list of one-or-more
        `_apply_translate`-compatible specs. Schema allows: a single spec (dict
        with `to:`, a [x,y,z] list, or a named-point string), or a *sequence* of
        [x,y,z] vectors applied in order (`[[dx1,dy1,dz1], [dx2,dy2,dz2], ...]`)."""
        if (
            isinstance(value, list)
            and value
            and all(isinstance(v, list) for v in value)
        ):
            return value
        return [value]

    @staticmethod
    def _as_rotate_sequence(value) -> list:
        """Normalize a part-level `rotate:` value into a list of one-or-more
        `_apply_rotate`-compatible specs (each a dict with angle + axis/around)."""
        if isinstance(value, list):
            return value
        return [value]

    def execute_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a single operation.

        Args:
            name: Operation name (becomes new part name)
            spec: Operation specification dict

        Raises:
            OperationsBuilderError: If spec is invalid or execution fails
        """
        # Resolve parameters
        resolved_spec = self.resolver.resolve(spec)

        # Get operation type
        if 'type' not in resolved_spec:
            raise OperationsBuilderError(
                f"Operation '{name}' missing 'type' field",
                operation_name=name
            )

        op_type = resolved_spec['type']

        handler = self._op_dispatch.get(op_type)
        if handler is None:
            raise OperationsBuilderError(
                f"Unknown operation type '{op_type}' for operation '{name}'",
                operation_name=name
            )
        handler(name, resolved_spec)

    def _execute_transform(self, name: str, spec: Dict[str, Any]):
        """
        Execute a transform operation.

        Applies a sequence of transforms to an input part.

        Args:
            name: New part name
            spec: Transform specification with 'input' and 'transforms'

        Raises:
            OperationsBuilderError: If transform fails
        """
        # Get input part
        if 'input' not in spec:
            raise OperationsBuilderError(
                f"Transform '{name}' missing 'input' field",
                operation_name=name
            )

        input_name = spec['input']
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise OperationsBuilderError(
                f"Transform '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        input_part = self.registry.get(input_name)

        # Get transforms list
        if 'transforms' not in spec:
            raise OperationsBuilderError(
                f"Transform '{name}' missing 'transforms' field",
                operation_name=name
            )

        transforms = spec['transforms']
        if not isinstance(transforms, list):
            raise OperationsBuilderError(
                f"Transform '{name}' transforms must be a list",
                operation_name=name
            )

        # Create tracker with initial geometry
        tracker = TransformTracker(input_part.geometry, backend=input_part.backend)

        # Apply each transform
        for i, transform in enumerate(transforms):
            try:
                self._apply_transform(tracker, transform, name)
            except Exception as e:
                raise OperationsBuilderError(
                    f"Transform '{name}' failed at step {i}: {str(e)}",
                    operation_name=name
                ) from e

        # Create new part with transformed geometry
        # Copy appearance metadata (color, material, etc.) from input part
        from .metadata_utils import copy_propagating_metadata

        metadata = copy_propagating_metadata(
            source_metadata=input_part.metadata,
            target_metadata={
                'source': input_name,
                'operation_type': 'transform'
            }
        )

        transformed_part = Part(
            name=name,
            geometry=tracker.get_geometry(),
            metadata=metadata,
            current_position=tracker.current_position,
            backend=input_part.backend,
        )

        # Add to registry
        self.registry.add(transformed_part)
        logger.debug(f"Created transformed part '{name}' from '{input_name}'")

    def _apply_transform(self, tracker: TransformTracker, transform: Dict[str, Any], context: str):
        """
        Apply a single transform to the tracker.

        Args:
            tracker: TransformTracker to apply transform to
            transform: Transform specification (dict with one key: translate/rotate/etc)
            context: Context name for error messages

        Raises:
            OperationsBuilderError: If transform is invalid
        """
        if not isinstance(transform, dict) or len(transform) != 1:
            raise OperationsBuilderError(
                f"Each transform must be a dict with exactly one key, got: {transform}",
                operation_name=context
            )

        transform_type = list(transform.keys())[0]
        transform_params = transform[transform_type]

        if transform_type == 'translate':
            self._apply_translate(tracker, transform_params, context)
        elif transform_type == 'rotate':
            self._apply_rotate(tracker, transform_params, context)
        elif transform_type == 'align_to_face':
            self._apply_align_to_face(tracker, transform_params, context)
        else:
            raise OperationsBuilderError(
                f"Unknown transform type '{transform_type}' in operation '{context}'",
                operation_name=context
            )

    def _apply_translate(self, tracker: TransformTracker, params, context: str):
        """
        Apply translate transform.

        Supports:
        - to: point (with optional offset)
        - offset: [dx, dy, dz]
        - named_point (string shorthand)

        Args:
            tracker: TransformTracker to apply to
            params: Translation parameters (dict, list, or string)
            context: Context for error messages
        """
        # Backward compatibility: {offset: [...]} wrapper without 'to' → bare list.
        # ('offset:' remains valid alongside 'to:', handled by Case 1 below.)
        if isinstance(params, dict) and 'offset' in params and 'to' not in params:
            warnings.warn(
                f"Translate ({context}): the 'offset:' wrapper without 'to:' is "
                f"deprecated; use 'translate: [x, y, z]' directly. "
                f"See docs/developer/MIGRATION_GUIDE_V3.md.",
                DeprecationWarning,
                stacklevel=2,
            )
            params = params['offset']

        # Case 1: translate with 'to' and optional 'offset'
        if isinstance(params, dict) and 'to' in params:
            # Resolve target point
            to_point_spec = params['to']
            target_point = self._resolve_point(to_point_spec, context)

            # Get offset if provided
            offset = params.get('offset', [0, 0, 0])
            if not isinstance(offset, list) or len(offset) != 3:
                raise OperationsBuilderError(
                    f"Translate offset must be [dx, dy, dz], got: {offset}",
                    operation_name=context
                )

            # Calculate final position: target + offset
            final_x = target_point[0] + offset[0]
            final_y = target_point[1] + offset[1]
            final_z = target_point[2] + offset[2]

            # Get current position
            current_pos = tracker.current_position

            # Calculate delta from current to final
            dx = final_x - current_pos[0]
            dy = final_y - current_pos[1]
            dz = final_z - current_pos[2]

            # Apply translation
            tracker.apply_transform({'type': 'translate', 'offset': [dx, dy, dz]})
            logger.debug(f"Translated to {target_point} + offset {offset} = ({final_x}, {final_y}, {final_z})")

        # Case 2: translate with offset [dx, dy, dz]
        elif isinstance(params, list) and len(params) == 3:
            # Direct offset (relative movement)
            tracker.apply_transform({'type': 'translate', 'offset': params})
            logger.debug(f"Translated by offset {params}")

        # Case 3: translate with named point (string shorthand)
        elif isinstance(params, str):
            # Resolve named point
            target_point = self._resolve_point(params, context)

            # Get current position
            current_pos = tracker.current_position

            # Calculate delta from current to target
            dx = target_point[0] - current_pos[0]
            dy = target_point[1] - current_pos[1]
            dz = target_point[2] - current_pos[2]

            # Apply translation
            tracker.apply_transform({'type': 'translate', 'offset': [dx, dy, dz]})
            logger.debug(f"Translated to named point '{params}' at {target_point}")

        else:
            raise OperationsBuilderError(
                f"Invalid translate parameters: {params}. Expected:\n"
                f"  - Dict with 'to:' and optional 'offset:'\n"
                f"  - List [x,y,z] for offset\n"
                f"  - String for named point",
                operation_name=context
            )

    def _parse_angle(self, angle_val, context: str) -> float:
        """Parse angle value — converts 'Xrad' strings to degrees, otherwise returns float."""
        if isinstance(angle_val, str) and angle_val.endswith('rad'):
            return math.degrees(float(angle_val[:-3]))
        return float(angle_val)

    def _resolve_axis_vector(self, axis, context: str) -> Tuple[float, float, float]:
        """Parse an axis spec (X/Y/Z string, [x,y,z] list, or spatial reference) to a 3-tuple."""
        axis_map = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
        if isinstance(axis, str):
            if axis in axis_map:
                return axis_map[axis]
            try:
                spatial_ref = self.spatial_resolver.resolve(axis)
                if spatial_ref.orientation is None:
                    raise OperationsBuilderError(
                        f"Axis reference '{axis}' resolved to a point without orientation. "
                        f"Use a face, edge, or axis reference, or specify as 'around' parameter.",
                        operation_name=context
                    )
                logger.debug(f"Resolved axis '{axis}' to orientation: {tuple(spatial_ref.orientation.tolist())}")
                return tuple(spatial_ref.orientation.tolist())
            except OperationsBuilderError:
                raise
            except Exception as e:
                raise OperationsBuilderError(
                    f"Invalid axis '{axis}'. Must be X, Y, Z, [x,y,z], or a spatial reference.",
                    operation_name=context
                ) from e
        if isinstance(axis, list) and len(axis) == 3:
            return tuple(axis)
        if isinstance(axis, dict):
            try:
                spatial_ref = self.spatial_resolver.resolve(axis)
                if spatial_ref.orientation is None:
                    raise OperationsBuilderError(
                        "Axis reference resolved to a point without orientation", operation_name=context
                    )
                return tuple(spatial_ref.orientation.tolist())
            except OperationsBuilderError:
                raise
            except Exception as e:
                raise OperationsBuilderError(
                    f"Failed to resolve axis reference: {str(e)}", operation_name=context
                ) from e
        raise OperationsBuilderError(
            f"Invalid axis: {axis}. Must be X|Y|Z, [x,y,z], or a spatial reference",
            operation_name=context
        )

    def _resolve_around_axis(self, around_spec, context: str):
        """Resolve a frame-based 'around' reference. Returns (axis_vector, origin_point)."""
        try:
            spatial_ref = self.spatial_resolver.resolve(around_spec)
        except Exception as e:
            raise OperationsBuilderError(
                f"Failed to resolve 'around' reference '{around_spec}': {str(e)}",
                operation_name=context
            ) from e
        if spatial_ref.orientation is None:
            raise OperationsBuilderError(
                f"Frame-based rotation requires 'around' reference with orientation, "
                f"but '{around_spec}' resolved to a point without orientation. "
                f"Use a face, edge, or axis reference.",
                operation_name=context
            )
        axis_vector = tuple(spatial_ref.orientation.tolist())
        origin_point = tuple(spatial_ref.position.tolist())
        logger.debug(f"Frame-based rotation around {around_spec}: axis={axis_vector}, origin={origin_point}")
        return axis_vector, origin_point

    def _apply_rotate(self, tracker: TransformTracker, params: Dict[str, Any], context: str):
        """
        Apply rotate transform. Supports two modes:
        - Frame-based: angle + around (spatial reference with orientation)
        - Traditional: angle + axis (X/Y/Z or [x,y,z]) + origin (rotation center)
        Angle may be degrees (float) or radians ("Xrad" string).
        """
        if not isinstance(params, dict):
            raise OperationsBuilderError(f"Rotate parameters must be a dict, got: {params}",
                                         operation_name=context)
        if 'angle' not in params:
            raise OperationsBuilderError("Rotate missing required 'angle' field", operation_name=context)

        angle_deg = self._parse_angle(params['angle'], context)

        if 'around' in params:
            axis_vector, origin_point = self._resolve_around_axis(params['around'], context)
        else:
            if 'axis' not in params:
                raise OperationsBuilderError(
                    "Rotate missing required 'axis' field (or use 'around' for frame-based rotation)",
                    operation_name=context
                )
            if 'origin' not in params:
                raise OperationsBuilderError(
                    "Rotate missing required 'origin' field (or use 'around' for frame-based rotation)",
                    operation_name=context
                )
            axis_vector = self._resolve_axis_vector(params['axis'], context)
            origin_point = self._resolve_point(params['origin'], context)

        tracker.apply_transform({'type': 'rotate', 'angle': angle_deg,
                                  'axis': axis_vector, 'origin': origin_point})
        logger.debug(f"Rotated {angle_deg}° around {axis_vector} at {origin_point}")

    @staticmethod
    def _calc_alignment_rotation(v1: np.ndarray, v2: np.ndarray) -> Tuple[np.ndarray, float]:
        """Return (rotation_axis, angle_degrees) to rotate unit vector v1 onto unit vector v2."""
        axis = np.cross(v1, v2)
        axis_len = np.linalg.norm(axis)
        if axis_len < 1e-10:
            dot = np.dot(v1, v2)
            if dot > 0.999:
                return np.array([0.0, 0.0, 1.0]), 0.0
            # Anti-parallel: pick a perpendicular axis for 180° rotation
            perp = np.array([1.0, 0.0, 0.0]) if abs(v1[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            ax = np.cross(v1, perp)
            return ax / np.linalg.norm(ax), 180.0
        return axis / axis_len, np.degrees(np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0)))

    def _apply_align_to_face(self, tracker: TransformTracker, params: Dict[str, Any], context: str):
        """
        Apply align_to_face transform: rotate part's -Z to face normal, then translate to face position.

        Params: face (required), orientation ('normal'), offset (default 0).
        """
        if not isinstance(params, dict):
            raise OperationsBuilderError(f"align_to_face parameters must be a dict, got: {params}", operation_name=context)
        if 'face' not in params:
            raise OperationsBuilderError("align_to_face missing required 'face' field", operation_name=context)

        face_spec = params['face']
        try:
            face_ref = self.spatial_resolver.resolve(face_spec)
        except Exception as e:
            raise OperationsBuilderError(f"Failed to resolve face reference '{face_spec}': {str(e)}", operation_name=context) from e

        if face_ref.orientation is None:
            raise OperationsBuilderError(
                f"align_to_face requires a face reference with normal (orientation), "
                f"but '{face_spec}' resolved to a point without orientation",
                operation_name=context
            )

        orientation_mode = params.get('orientation', 'normal')
        if orientation_mode != 'normal':
            raise OperationsBuilderError(
                f"align_to_face currently only supports orientation='normal', got: {orientation_mode}",
                operation_name=context
            )

        target_normal = face_ref.orientation
        offset_distance = float(params.get('offset', 0))

        # Step 1: Rotate part's -Z axis to align with face normal
        v1 = np.array([0.0, 0.0, -1.0])
        v2 = target_normal / np.linalg.norm(target_normal)
        rotation_axis, rotation_angle_deg = self._calc_alignment_rotation(v1, v2)
        if rotation_angle_deg > 1e-6:
            tracker.apply_transform({
                'type': 'rotate',
                'angle': rotation_angle_deg,
                'axis': tuple(rotation_axis.tolist()),
                'origin': 'current'
            })
            logger.debug(f"Rotated {rotation_angle_deg:.2f}° around {rotation_axis} to align with face normal")

        # Step 2: Translate to face position + offset along normal
        target_position = face_ref.position + (offset_distance * target_normal)
        translation = target_position - np.array(list(tracker.current_position))
        tracker.apply_transform({'type': 'translate', 'offset': list(translation)})
        logger.debug(f"Translated to face position {face_ref.position} + offset {offset_distance} along normal")

    def _resolve_point(self, point_spec: Any, context: str) -> Tuple[float, float, float]:
        """
        Resolve a point specification to coordinates.

        Uses SpatialResolver to handle various reference types and extracts
        position coordinates for backward compatibility with existing transform operations.

        Args:
            point_spec: Point specification (array, string, or dict)
            context: Context for error messages

        Returns:
            (x, y, z) tuple

        Raises:
            OperationsBuilderError: If point cannot be resolved
        """
        try:
            # Use SpatialResolver to get SpatialRef
            spatial_ref = self.spatial_resolver.resolve(point_spec)
            # Extract position as tuple for backward compatibility
            return tuple(spatial_ref.position)
        except Exception as e:
            raise OperationsBuilderError(
                f"Failed to resolve point '{point_spec}' in operation '{context}': {str(e)}",
                operation_name=context
            ) from e

    def __repr__(self) -> str:
        return f"OperationsBuilder(parts={len(self.registry)}, resolver={self.resolver})"
