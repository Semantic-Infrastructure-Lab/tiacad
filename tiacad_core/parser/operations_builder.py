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
Version: 3.0.0-dev (Phase 2 - Parser Integration)
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import cadquery as cq

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

logger = logging.getLogger(__name__)


class OperationsBuilderError(TiaCADError):
    """Error during operations building or execution"""
    def __init__(self, message: str, operation_name: str = None):
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
                 sketches: Dict[str, Any] = None,
                 spatial_resolver: SpatialResolver = None):
        """
        Initialize operations builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
            sketches: Dictionary of sketches for extrude/revolve/sweep/loft (optional)
            spatial_resolver: SpatialResolver for reference resolution (optional)
        """
        self.registry = part_registry
        self.resolver = parameter_resolver
        self.sketches = sketches or {}
        self.spatial_resolver = spatial_resolver or SpatialResolver(part_registry, {})
        self.boolean_builder = BooleanBuilder(part_registry, parameter_resolver)
        self.pattern_builder = PatternBuilder(part_registry, parameter_resolver)
        self.finishing_builder = FinishingBuilder(part_registry, parameter_resolver)
        # Sketch-based operation builders (Phase 3)
        self.extrude_builder = ExtrudeBuilder(part_registry, self.sketches, parameter_resolver)
        self.revolve_builder = RevolveBuilder(part_registry, self.sketches, parameter_resolver)
        self.sweep_builder = SweepBuilder(part_registry, self.sketches, parameter_resolver)
        self.loft_builder = LoftBuilder(part_registry, self.sketches, parameter_resolver)
        self.hull_builder = HullBuilder(part_registry, parameter_resolver)
        self.text_builder = TextBuilder(part_registry, parameter_resolver)
        self.gusset_builder = GussetBuilder(part_registry, parameter_resolver)

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

        # Execute based on type
        if op_type == 'transform':
            self._execute_transform(name, resolved_spec)
        elif op_type == 'boolean':
            self.boolean_builder.execute_boolean_operation(name, resolved_spec)
        elif op_type == 'pattern':
            self.pattern_builder.execute_pattern_operation(name, resolved_spec)
        elif op_type == 'finishing':
            self.finishing_builder.execute_finishing_operation(name, resolved_spec)
        elif op_type == 'extrude':
            self.extrude_builder.execute_extrude_operation(name, resolved_spec)
        elif op_type == 'revolve':
            self.revolve_builder.execute_revolve_operation(name, resolved_spec)
        elif op_type == 'sweep':
            self.sweep_builder.execute_sweep_operation(name, resolved_spec)
        elif op_type == 'loft':
            self.loft_builder.execute_loft_operation(name, resolved_spec)
        elif op_type == 'hull':
            self.hull_builder.execute_hull_operation(name, resolved_spec)
        elif op_type == 'text':
            self.text_builder.execute_text_operation(name, resolved_spec)
        elif op_type == 'gusset':
            self.gusset_builder.execute_gusset_operation(name, resolved_spec)
        else:
            raise OperationsBuilderError(
                f"Unknown operation type '{op_type}' for operation '{name}'",
                operation_name=name
            )

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
        tracker = TransformTracker(input_part.geometry)

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
            current_position=tracker.current_position
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

    def _apply_rotate(self, tracker: TransformTracker, params: Dict[str, Any], context: str):
        """
        Apply rotate transform.

        Supports two modes:
        1. Traditional: axis (X/Y/Z or [x,y,z]) + origin (point)
        2. Frame-based: around (spatial reference with orientation)

        Traditional mode requires:
        - angle: degrees (or "Xrad" for radians)
        - axis: X|Y|Z or [x,y,z]
        - origin: point (rotation center)

        Frame-based mode requires:
        - angle: degrees (or "Xrad" for radians)
        - around: spatial reference (face, edge, or axis)
          - For faces: rotates around normal through face center
          - For edges: rotates around tangent
          - For axes: rotates around axis direction

        Args:
            tracker: TransformTracker to apply to
            params: Rotation parameters
            context: Context for error messages
        """
        if not isinstance(params, dict):
            raise OperationsBuilderError(
                f"Rotate parameters must be a dict, got: {params}",
                operation_name=context
            )

        # Validate required fields
        if 'angle' not in params:
            raise OperationsBuilderError(
                f"Rotate missing required 'angle' field",
                operation_name=context
            )

        # Parse angle
        angle = params['angle']
        if isinstance(angle, str) and angle.endswith('rad'):
            # Convert radians to degrees
            import math
            angle_rad = float(angle[:-3])
            angle_deg = math.degrees(angle_rad)
        else:
            angle_deg = float(angle)

        # Determine mode: traditional (axis + origin) or frame-based (around)
        if 'around' in params:
            # Frame-based rotation using spatial reference
            around_spec = params['around']

            # Resolve the spatial reference
            try:
                spatial_ref = self.spatial_resolver.resolve(around_spec)
            except Exception as e:
                raise OperationsBuilderError(
                    f"Failed to resolve 'around' reference '{around_spec}': {str(e)}",
                    operation_name=context
                ) from e

            # Validate that we got a reference with orientation
            if spatial_ref.orientation is None:
                raise OperationsBuilderError(
                    f"Frame-based rotation requires 'around' reference with orientation, "
                    f"but '{around_spec}' resolved to a point without orientation. "
                    f"Use a face, edge, or axis reference.",
                    operation_name=context
                )

            # Use orientation as rotation axis
            axis_vector = tuple(spatial_ref.orientation.tolist())
            # Use position as rotation origin
            origin_point = tuple(spatial_ref.position.tolist())

            logger.debug(f"Frame-based rotation around {around_spec}: axis={axis_vector}, origin={origin_point}")

        else:
            # Traditional rotation with explicit axis and origin
            if 'axis' not in params:
                raise OperationsBuilderError(
                    f"Rotate missing required 'axis' field (or use 'around' for frame-based rotation)",
                    operation_name=context
                )
            if 'origin' not in params:
                raise OperationsBuilderError(
                    f"Rotate missing required 'origin' field (or use 'around' for frame-based rotation)",
                    operation_name=context
                )

            # Parse axis
            axis = params['axis']
            if isinstance(axis, str):
                # Check if it's a named axis (X, Y, Z) or a spatial reference
                axis_map = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
                if axis in axis_map:
                    # Named axis
                    axis_vector = axis_map[axis]
                else:
                    # Try to resolve as spatial reference
                    try:
                        spatial_ref = self.spatial_resolver.resolve(axis)
                        if spatial_ref.orientation is None:
                            raise OperationsBuilderError(
                                f"Axis reference '{axis}' resolved to a point without orientation. "
                                f"Use a face, edge, or axis reference, or specify as 'around' parameter.",
                                operation_name=context
                            )
                        axis_vector = tuple(spatial_ref.orientation.tolist())
                        logger.debug(f"Resolved axis '{axis}' to orientation: {axis_vector}")
                    except Exception as e:
                        raise OperationsBuilderError(
                            f"Invalid axis '{axis}'. Must be X, Y, Z, [x,y,z], or a spatial reference.",
                            operation_name=context
                        ) from e
            elif isinstance(axis, list) and len(axis) == 3:
                axis_vector = tuple(axis)
            elif isinstance(axis, dict):
                # Inline spatial reference
                try:
                    spatial_ref = self.spatial_resolver.resolve(axis)
                    if spatial_ref.orientation is None:
                        raise OperationsBuilderError(
                            f"Axis reference resolved to a point without orientation",
                            operation_name=context
                        )
                    axis_vector = tuple(spatial_ref.orientation.tolist())
                except Exception as e:
                    raise OperationsBuilderError(
                        f"Failed to resolve axis reference: {str(e)}",
                        operation_name=context
                    ) from e
            else:
                raise OperationsBuilderError(
                    f"Invalid axis: {axis}. Must be X|Y|Z, [x,y,z], or a spatial reference",
                    operation_name=context
                )

            # Resolve origin point (supports named points, lists, dicts, dot notation)
            origin_spec = params['origin']
            origin_point = self._resolve_point(origin_spec, context)

        # Apply rotation
        tracker.apply_transform({
            'type': 'rotate',
            'angle': angle_deg,
            'axis': axis_vector,
            'origin': origin_point
        })
        logger.debug(f"Rotated {angle_deg}° around {axis_vector} at {origin_point}")

    def _apply_align_to_face(self, tracker: TransformTracker, params: Dict[str, Any], context: str):
        """
        Apply align_to_face transform.

        Aligns a part to a target face reference by:
        1. Rotating to match the face normal (orientation)
        2. Translating to the face position + optional offset along normal

        Supports:
        - face: face reference (string, dict, or SpatialRef)
        - orientation: how to align ('normal' aligns part's -Z to face normal)
        - offset: distance from face along normal (default: 0)

        Args:
            tracker: TransformTracker to apply to
            params: align_to_face parameters
            context: Context for error messages

        Example:
            align_to_face:
              face: base.top_face
              orientation: normal
              offset: 5
        """
        if not isinstance(params, dict):
            raise OperationsBuilderError(
                f"align_to_face parameters must be a dict, got: {params}",
                operation_name=context
            )

        # Validate required fields
        if 'face' not in params:
            raise OperationsBuilderError(
                f"align_to_face missing required 'face' field",
                operation_name=context
            )

        # Resolve face reference
        face_spec = params['face']
        try:
            face_ref = self.spatial_resolver.resolve(face_spec)
        except Exception as e:
            raise OperationsBuilderError(
                f"Failed to resolve face reference '{face_spec}': {str(e)}",
                operation_name=context
            ) from e

        # Validate that we got a face reference with orientation
        if face_ref.orientation is None:
            raise OperationsBuilderError(
                f"align_to_face requires a face reference with normal (orientation), "
                f"but '{face_spec}' resolved to a point without orientation",
                operation_name=context
            )

        # Get orientation mode (default: 'normal')
        orientation_mode = params.get('orientation', 'normal')
        if orientation_mode != 'normal':
            raise OperationsBuilderError(
                f"align_to_face currently only supports orientation='normal', got: {orientation_mode}",
                operation_name=context
            )

        # Get offset along normal (default: 0)
        offset_distance = float(params.get('offset', 0))

        # Step 1: Calculate rotation to align part's -Z axis to face normal
        # Face normal is the target direction
        target_normal = face_ref.orientation

        # Part's current -Z axis in world coordinates (before rotation)
        # Assuming part starts with -Z pointing down
        part_z_axis = np.array([0.0, 0.0, -1.0])

        # Calculate rotation axis and angle to align part_z_axis with target_normal
        # Using Rodrigues' rotation formula

        # Normalize vectors (should already be normalized, but be safe)
        v1 = part_z_axis / np.linalg.norm(part_z_axis)
        v2 = target_normal / np.linalg.norm(target_normal)

        # Calculate rotation axis (cross product)
        rotation_axis = np.cross(v1, v2)
        rotation_axis_length = np.linalg.norm(rotation_axis)

        # Check if vectors are parallel or anti-parallel
        if rotation_axis_length < 1e-10:
            # Vectors are parallel or anti-parallel
            dot_product = np.dot(v1, v2)
            if dot_product > 0.999:
                # Already aligned, no rotation needed
                rotation_angle_deg = 0.0
                rotation_axis = np.array([0.0, 0.0, 1.0])  # Arbitrary axis
            else:
                # Anti-parallel, rotate 180° around perpendicular axis
                # Choose a perpendicular axis
                if abs(v1[0]) < 0.9:
                    rotation_axis = np.cross(v1, np.array([1.0, 0.0, 0.0]))
                else:
                    rotation_axis = np.cross(v1, np.array([0.0, 1.0, 0.0]))
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
                rotation_angle_deg = 180.0
        else:
            # Normal case: calculate rotation angle
            rotation_axis = rotation_axis / rotation_axis_length

            # Calculate angle using dot product
            dot_product = np.dot(v1, v2)
            # Clamp to [-1, 1] to avoid numerical errors
            dot_product = np.clip(dot_product, -1.0, 1.0)
            rotation_angle_rad = np.arccos(dot_product)
            rotation_angle_deg = np.degrees(rotation_angle_rad)

        # Apply rotation around current position (part's center)
        if rotation_angle_deg > 1e-6:  # Only rotate if angle is significant
            tracker.apply_transform({
                'type': 'rotate',
                'angle': rotation_angle_deg,
                'axis': tuple(rotation_axis.tolist()),
                'origin': 'current'  # Rotate around current position
            })
            logger.debug(f"Rotated {rotation_angle_deg:.2f}° around {rotation_axis} to align with face normal")

        # Step 2: Translate to face position + offset along normal
        target_position = face_ref.position + (offset_distance * target_normal)

        current_pos = np.array(list(tracker.current_position))
        translation = target_position - current_pos

        tracker.apply_transform({
            'type': 'translate',
            'offset': list(translation)
        })
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
