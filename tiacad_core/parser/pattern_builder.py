"""
PatternBuilder - Create arrays/patterns of Part objects

Handles pattern operations (linear, circular, grid) to create multiple
copies of parts with transformations.

Supported Patterns:
- linear: Repeat parts along a line with spacing
- circular: Rotate parts around an axis
- grid: 2D grid of parts

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import logging
from typing import Dict, Any, List

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class PatternBuilderError(TiaCADError):
    """Error during pattern operations"""
    def __init__(self, message: str, operation_name: str = None):
        super().__init__(message)
        self.operation_name = operation_name


class PatternBuilder:
    """
    Creates patterns (arrays) of Part objects.

    Supports:
    - linear: Repeat parts along a line
    - circular: Rotate parts around an axis
    - grid: 2D grid of parts

    Usage:
        builder = PatternBuilder(part_registry, parameter_resolver)
        parts = builder.execute_pattern_operation('hole_array', {
            'pattern': 'linear',
            'input': 'hole',
            'count': 5,
            'spacing': [20, 0, 0]
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver):
        """
        Initialize pattern builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
        """
        self.registry = part_registry
        self.resolver = parameter_resolver

    def execute_pattern_operation(self, name: str, spec: Dict[str, Any]) -> List[Part]:
        """
        Execute a pattern operation and add results to registry.

        Creates multiple copies of input part and adds them with indexed names.

        Args:
            name: Base name for pattern parts (will be suffixed with index)
            spec: Pattern specification with 'pattern' field

        Returns:
            List of created Part objects

        Raises:
            PatternBuilderError: If operation fails
        """
        # Resolve parameters first
        resolved_spec = self.resolver.resolve(spec)

        # Validate pattern field
        if 'pattern' not in resolved_spec:
            raise PatternBuilderError(
                f"Pattern operation '{name}' missing 'pattern' field",
                operation_name=name
            )

        pattern_type = resolved_spec['pattern']

        # Execute based on pattern type
        try:
            if pattern_type == 'linear':
                parts = self._execute_linear(name, resolved_spec)
            elif pattern_type == 'circular':
                parts = self._execute_circular(name, resolved_spec)
            elif pattern_type == 'grid':
                parts = self._execute_grid(name, resolved_spec)
            else:
                raise PatternBuilderError(
                    f"Unknown pattern type '{pattern_type}'. "
                    f"Supported: linear, circular, grid",
                    operation_name=name
                )

            logger.info(f"Pattern operation '{pattern_type}' created {len(parts)} parts")
            return parts

        except PatternBuilderError:
            raise
        except Exception as e:
            raise PatternBuilderError(
                f"Pattern operation '{pattern_type}' failed for '{name}': {str(e)}",
                operation_name=name
            ) from e

    def _execute_linear(self, name: str, spec: Dict[str, Any]) -> List[Part]:
        """
        Execute linear pattern - repeat parts along a line.

        Args:
            name: Base name for pattern parts
            spec: Specification with 'input', 'count', 'spacing' fields

        Returns:
            List of created Part objects

        Raises:
            PatternBuilderError: If inputs invalid or pattern fails
        """
        # Validate required fields
        if 'input' not in spec:
            raise PatternBuilderError(
                f"Linear pattern '{name}' missing 'input' field",
                operation_name=name
            )
        if 'count' not in spec:
            raise PatternBuilderError(
                f"Linear pattern '{name}' missing 'count' field",
                operation_name=name
            )
        if 'spacing' not in spec:
            raise PatternBuilderError(
                f"Linear pattern '{name}' missing 'spacing' field",
                operation_name=name
            )

        input_name = spec['input']
        count = spec['count']
        spacing = spec['spacing']
        start_offset = spec.get('start_offset', [0, 0, 0])

        # Validate count
        if not isinstance(count, int) or count < 1:
            raise PatternBuilderError(
                f"Linear pattern '{name}' count must be integer >= 1, got: {count}",
                operation_name=name
            )

        # Validate spacing
        if not isinstance(spacing, list) or len(spacing) != 3:
            raise PatternBuilderError(
                f"Linear pattern '{name}' spacing must be [dx, dy, dz], got: {spacing}",
                operation_name=name
            )

        # Validate start_offset
        if not isinstance(start_offset, list) or len(start_offset) != 3:
            raise PatternBuilderError(
                f"Linear pattern '{name}' start_offset must be [dx, dy, dz], got: {start_offset}",
                operation_name=name
            )

        # Get input part
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise PatternBuilderError(
                f"Linear pattern '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        input_part = self.registry.get(input_name)
        parts = []

        # Create copies
        for i in range(count):
            # Calculate offset for this copy
            offset_x = start_offset[0] + (spacing[0] * i)
            offset_y = start_offset[1] + (spacing[1] * i)
            offset_z = start_offset[2] + (spacing[2] * i)

            # Create transformed geometry
            geometry = input_part.geometry.translate((offset_x, offset_y, offset_z))

            # Copy appearance metadata (color, material, etc.) from input part
            from .metadata_utils import copy_propagating_metadata

            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'operation_type': 'pattern',
                    'pattern_type': 'linear',
                    'pattern_index': i,
                    'source': input_name
                }
            )

            # Create part
            part_name = f"{name}_{i}"
            part = Part(
                name=part_name,
                geometry=geometry,
                metadata=metadata,
                current_position=(offset_x, offset_y, offset_z)
            )

            # Add to registry
            self.registry.add(part)
            parts.append(part)
            logger.debug(f"Linear pattern: created {part_name} at ({offset_x}, {offset_y}, {offset_z})")

        logger.info(f"Linear pattern: created {count} copies with spacing {spacing}")
        return parts

    def _execute_circular(self, name: str, spec: Dict[str, Any]) -> List[Part]:
        """
        Execute circular pattern - rotate parts around axis.

        Args:
            name: Base name for pattern parts
            spec: Specification with 'input', 'count', 'axis', 'center' fields

        Returns:
            List of created Part objects

        Raises:
            PatternBuilderError: If inputs invalid or pattern fails
        """
        # Validate required fields
        if 'input' not in spec:
            raise PatternBuilderError(
                f"Circular pattern '{name}' missing 'input' field",
                operation_name=name
            )
        if 'count' not in spec:
            raise PatternBuilderError(
                f"Circular pattern '{name}' missing 'count' field",
                operation_name=name
            )
        if 'axis' not in spec:
            raise PatternBuilderError(
                f"Circular pattern '{name}' missing 'axis' field",
                operation_name=name
            )
        if 'center' not in spec:
            raise PatternBuilderError(
                f"Circular pattern '{name}' missing 'center' field",
                operation_name=name
            )

        input_name = spec['input']
        count = spec['count']
        axis = spec['axis']
        center = spec['center']
        start_angle = spec.get('start_angle', 0)
        end_angle = spec.get('end_angle', 360)
        radius = spec.get('radius', None)

        # Validate count
        if not isinstance(count, int) or count < 1:
            raise PatternBuilderError(
                f"Circular pattern '{name}' count must be integer >= 1, got: {count}",
                operation_name=name
            )

        # Parse axis
        if isinstance(axis, str):
            axis_map = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
            if axis not in axis_map:
                raise PatternBuilderError(
                    f"Circular pattern '{name}' invalid axis '{axis}'. Must be X, Y, Z, or [x,y,z]",
                    operation_name=name
                )
            axis_vector = axis_map[axis]
        elif isinstance(axis, list) and len(axis) == 3:
            axis_vector = tuple(axis)
        else:
            raise PatternBuilderError(
                f"Circular pattern '{name}' invalid axis: {axis}. Must be X|Y|Z or [x,y,z]",
                operation_name=name
            )

        # Validate center
        if not isinstance(center, list) or len(center) != 3:
            raise PatternBuilderError(
                f"Circular pattern '{name}' center must be [x, y, z], got: {center}",
                operation_name=name
            )

        # Get input part
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise PatternBuilderError(
                f"Circular pattern '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        input_part = self.registry.get(input_name)
        parts = []

        # Calculate angle step
        if count == 1:
            angle_step = 0
        else:
            angle_step = (end_angle - start_angle) / count

        # Create copies
        for i in range(count):
            # Calculate angle for this copy
            angle = start_angle + (angle_step * i)

            # Start with input geometry
            geometry = input_part.geometry

            # If radius specified, translate out first
            if radius is not None:
                # Determine radial direction based on axis
                if axis_vector == (0, 0, 1):  # Z axis
                    radial_offset = (radius, 0, 0)
                elif axis_vector == (0, 1, 0):  # Y axis
                    radial_offset = (radius, 0, 0)
                elif axis_vector == (1, 0, 0):  # X axis
                    radial_offset = (0, radius, 0)
                else:
                    # For custom axis, use X direction
                    radial_offset = (radius, 0, 0)

                geometry = geometry.translate(radial_offset)

            # Rotate around center
            # CadQuery rotate expects axis through origin, so we need to:
            # 1. Translate to center
            # 2. Rotate
            # 3. Already at center, no need to translate back
            center_tuple = tuple(center)
            geometry = geometry.rotate(
                axisStartPoint=center_tuple,
                axisEndPoint=(center[0] + axis_vector[0],
                              center[1] + axis_vector[1],
                              center[2] + axis_vector[2]),
                angleDegrees=angle
            )

            # Copy appearance metadata (color, material, etc.) from input part
            from .metadata_utils import copy_propagating_metadata

            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'operation_type': 'pattern',
                    'pattern_type': 'circular',
                    'pattern_index': i,
                    'source': input_name,
                    'angle': angle
                }
            )

            # Create part
            part_name = f"{name}_{i}"
            part = Part(
                name=part_name,
                geometry=geometry,
                metadata=metadata
            )

            # Add to registry
            self.registry.add(part)
            parts.append(part)
            logger.debug(f"Circular pattern: created {part_name} at angle {angle}°")

        logger.info(f"Circular pattern: created {count} copies around {axis_vector}")
        return parts

    def _execute_grid(self, name: str, spec: Dict[str, Any]) -> List[Part]:
        """
        Execute grid pattern - create 2D grid of parts.

        Args:
            name: Base name for pattern parts
            spec: Specification with 'input', 'count', 'spacing' fields

        Returns:
            List of created Part objects

        Raises:
            PatternBuilderError: If inputs invalid or pattern fails
        """
        # Validate required fields
        if 'input' not in spec:
            raise PatternBuilderError(
                f"Grid pattern '{name}' missing 'input' field",
                operation_name=name
            )

        # Handle count field with backward compatibility for legacy API
        if 'count' not in spec:
            # Try legacy API (count_x, count_y)
            if 'count_x' in spec and 'count_y' in spec:
                count_x = spec['count_x']
                count_y = spec['count_y']
                spec['count'] = [count_x, count_y]
                logger.warning(
                    f"Grid pattern '{name}' uses deprecated 'count_x' and 'count_y'. "
                    f"Please use 'count: [{count_x}, {count_y}]' instead. "
                    f"Legacy API will be removed in v4.0."
                )
            else:
                raise PatternBuilderError(
                    f"Grid pattern '{name}' missing 'count' field. "
                    f"Use 'count: [rows, cols]' (or legacy 'count_x' and 'count_y')",
                    operation_name=name
                )

        # Handle spacing field with backward compatibility for legacy API
        if 'spacing' not in spec:
            # Try legacy API (spacing_x, spacing_y, spacing_z)
            if 'spacing_x' in spec and 'spacing_y' in spec:
                spacing_x = spec['spacing_x']
                spacing_y = spec['spacing_y']
                spacing_z = spec.get('spacing_z', 0)
                spec['spacing'] = [spacing_x, spacing_y, spacing_z]
                logger.warning(
                    f"Grid pattern '{name}' uses deprecated 'spacing_x/y/z'. "
                    f"Please use 'spacing: [{spacing_x}, {spacing_y}, {spacing_z}]' instead. "
                    f"Legacy API will be removed in v4.0."
                )
            else:
                raise PatternBuilderError(
                    f"Grid pattern '{name}' missing 'spacing' field. "
                    f"Use 'spacing: [dx, dy, dz]' (or legacy 'spacing_x/y/z')",
                    operation_name=name
                )

        input_name = spec['input']
        count = spec['count']
        spacing = spec['spacing']
        start_offset = spec.get('start_offset', [0, 0, 0])
        center_grid = spec.get('center_grid', False)

        # Validate count
        if not isinstance(count, list) or len(count) != 2:
            raise PatternBuilderError(
                f"Grid pattern '{name}' count must be [rows, columns], got: {count}",
                operation_name=name
            )

        rows, cols = count
        if not isinstance(rows, int) or rows < 1:
            raise PatternBuilderError(
                f"Grid pattern '{name}' rows must be integer >= 1, got: {rows}",
                operation_name=name
            )
        if not isinstance(cols, int) or cols < 1:
            raise PatternBuilderError(
                f"Grid pattern '{name}' columns must be integer >= 1, got: {cols}",
                operation_name=name
            )

        # Validate spacing
        if not isinstance(spacing, list) or len(spacing) != 3:
            raise PatternBuilderError(
                f"Grid pattern '{name}' spacing must be [dx, dy, dz], got: {spacing}",
                operation_name=name
            )

        # Get input part
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise PatternBuilderError(
                f"Grid pattern '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        input_part = self.registry.get(input_name)
        parts = []

        # Calculate grid offset if centering
        grid_offset_x = 0
        grid_offset_y = 0
        if center_grid:
            grid_offset_x = -(rows - 1) * spacing[0] / 2
            grid_offset_y = -(cols - 1) * spacing[1] / 2

        # Create grid
        for row in range(rows):
            for col in range(cols):
                # Calculate position
                offset_x = start_offset[0] + grid_offset_x + (row * spacing[0])
                offset_y = start_offset[1] + grid_offset_y + (col * spacing[1])
                offset_z = start_offset[2] + spacing[2]

                # Create transformed geometry
                geometry = input_part.geometry.translate((offset_x, offset_y, offset_z))

                # Copy appearance metadata (color, material, etc.) from input part
                from .metadata_utils import copy_propagating_metadata

                metadata = copy_propagating_metadata(
                    source_metadata=input_part.metadata,
                    target_metadata={
                        'operation_type': 'pattern',
                        'pattern_type': 'grid',
                        'grid_position': (row, col),
                        'source': input_name
                    }
                )

                # Create part
                part_name = f"{name}_{row}_{col}"
                part = Part(
                    name=part_name,
                    geometry=geometry,
                    metadata=metadata,
                    current_position=(offset_x, offset_y, offset_z)
                )

                # Add to registry
                self.registry.add(part)
                parts.append(part)
                logger.debug(f"Grid pattern: created {part_name} at ({offset_x}, {offset_y}, {offset_z})")

        logger.info(f"Grid pattern: created {rows}x{cols} = {len(parts)} parts")
        return parts

    def __repr__(self) -> str:
        return f"PatternBuilder(parts={len(self.registry)}, resolver={self.resolver})"
