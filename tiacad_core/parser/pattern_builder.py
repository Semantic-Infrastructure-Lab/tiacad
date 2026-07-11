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
import warnings
from typing import Any, Dict, List, Optional

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver
from .metadata_utils import copy_propagating_metadata

logger = logging.getLogger(__name__)


class PatternBuilderError(TiaCADError):
    """Error during pattern operations"""
    def __init__(self, message: str, operation_name: Optional[str] = None):
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

    # -------------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------------

    def _require(self, op_name: str, spec: Dict[str, Any], field: str, pattern_label: str) -> None:
        """Raise PatternBuilderError if a required field is missing from spec."""
        if field not in spec:
            raise PatternBuilderError(
                f"{pattern_label} pattern '{op_name}' missing '{field}' field",
                operation_name=op_name
            )

    def _get_input_part(self, op_name: str, spec: Dict[str, Any], pattern_label: str) -> tuple:
        """Validate and fetch the input part from the registry.

        Returns (input_name, input_part).
        """
        self._require(op_name, spec, 'input', pattern_label)
        input_name = spec['input']
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise PatternBuilderError(
                f"{pattern_label} pattern '{op_name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=op_name
            )
        return input_name, self.registry.get(input_name)

    def _make_and_register_part(
        self,
        part_name: str,
        geometry: Any,
        metadata: Dict[str, Any],
        position: Optional[tuple] = None,
        backend=None,
    ) -> 'Part':
        """Create a Part, add it to the registry, and return it."""
        part = Part(name=part_name, geometry=geometry, metadata=metadata,
                    current_position=position, backend=backend)
        self.registry.add(part)
        return part

    def _resolve_circular_axis(
        self,
        name: str,
        axis: Any,
    ) -> tuple[float, float, float]:
        """Resolve a circular-pattern axis spec into a concrete vector."""
        if isinstance(axis, str):
            axis_map = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
            if axis not in axis_map:
                raise PatternBuilderError(
                    f"Circular pattern '{name}' invalid axis '{axis}'. "
                    "Must be X, Y, Z, or [x,y,z]",
                    operation_name=name
                )
            return axis_map[axis]

        if isinstance(axis, list) and len(axis) == 3:
            return tuple(axis)

        raise PatternBuilderError(
            f"Circular pattern '{name}' invalid axis: {axis}. Must be X|Y|Z or [x,y,z]",
            operation_name=name
        )

    def _validate_circular_center(self, name: str, center: Any) -> tuple[float, float, float]:
        """Validate and normalize a circular-pattern center point."""
        if not isinstance(center, list) or len(center) != 3:
            raise PatternBuilderError(
                f"Circular pattern '{name}' center must be [x, y, z], got: {center}",
                operation_name=name
            )
        return tuple(center)

    def _circular_radial_offset(
        self,
        axis_vector: tuple[float, float, float],
        radius: Any,
    ) -> tuple[float, float, float] | None:
        """Return the radial offset vector used before circular rotation."""
        if radius is None:
            return None

        preferred_offsets = {
            (0, 0, 1): (radius, 0, 0),
            (0, 1, 0): (radius, 0, 0),
            (1, 0, 0): (0, radius, 0),
        }
        return preferred_offsets.get(axis_vector, (radius, 0, 0))

    def _translate_geometry(
        self,
        part: Part,
        geometry: Any,
        offset: tuple[float, float, float],
    ) -> Any:
        """Translate geometry through the part backend when available."""
        if part.backend is not None:
            return part.backend.translate(geometry, offset)
        return geometry.translate(offset)

    def _rotate_geometry(
        self,
        part: Part,
        geometry: Any,
        center: tuple[float, float, float],
        axis_vector: tuple[float, float, float],
        angle: float,
    ) -> Any:
        """Rotate geometry through the part backend when available."""
        axis_end = (
            center[0] + axis_vector[0],
            center[1] + axis_vector[1],
            center[2] + axis_vector[2],
        )
        if part.backend is not None:
            return part.backend.rotate(
                geometry,
                axis_start=center,
                axis_end=axis_end,
                angle=angle,
            )
        return geometry.rotate(
            axisStartPoint=center,
            axisEndPoint=axis_end,
            angleDegrees=angle,
        )

    def _build_circular_geometry(
        self,
        input_part: Part,
        center: tuple[float, float, float],
        axis_vector: tuple[float, float, float],
        angle: float,
        radial_offset: tuple[float, float, float] | None,
    ) -> Any:
        """Build the transformed geometry for one circular-pattern instance."""
        geometry = input_part.geometry
        if radial_offset is not None:
            geometry = self._translate_geometry(input_part, geometry, radial_offset)
        return self._rotate_geometry(input_part, geometry, center, axis_vector, angle)

    # -------------------------------------------------------------------------

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
        self._require(name, spec, 'count', 'Linear')
        self._require(name, spec, 'spacing', 'Linear')
        input_name, input_part = self._get_input_part(name, spec, 'Linear')

        count = spec['count']
        spacing = spec['spacing']
        start_offset = spec.get('start_offset', [0, 0, 0])

        # Backward compatibility: scalar 'spacing' + 'direction' → vector 'spacing'
        if 'direction' in spec and isinstance(spacing, (int, float)) and not isinstance(spacing, bool):
            warnings.warn(
                f"Linear pattern '{name}': scalar 'spacing' with 'direction' is "
                f"deprecated; use vector 'spacing: [dx, dy, dz]' instead. "
                f"See docs/developer/MIGRATION_GUIDE_V3.md.",
                DeprecationWarning,
                stacklevel=2,
            )
            axis = str(spec['direction']).upper()
            idx = {'X': 0, 'Y': 1, 'Z': 2}.get(axis)
            if idx is None:
                raise PatternBuilderError(
                    f"Linear pattern '{name}' has invalid direction "
                    f"{spec['direction']!r} (expected X, Y, or Z)",
                    operation_name=name,
                )
            vec = [0.0, 0.0, 0.0]
            vec[idx] = spacing
            spacing = vec

        if not isinstance(count, int) or count < 1:
            raise PatternBuilderError(
                f"Linear pattern '{name}' count must be integer >= 1, got: {count}",
                operation_name=name
            )
        if not isinstance(spacing, list) or len(spacing) != 3:
            raise PatternBuilderError(
                f"Linear pattern '{name}' spacing must be [dx, dy, dz], got: {spacing}",
                operation_name=name
            )
        if not isinstance(start_offset, list) or len(start_offset) != 3:
            raise PatternBuilderError(
                f"Linear pattern '{name}' start_offset must be [dx, dy, dz], got: {start_offset}",
                operation_name=name
            )

        parts = []
        for i in range(count):
            ox = start_offset[0] + spacing[0] * i
            oy = start_offset[1] + spacing[1] * i
            oz = start_offset[2] + spacing[2] * i
            if input_part.backend is not None:
                geometry = input_part.backend.translate(input_part.geometry, (ox, oy, oz))
            else:
                geometry = input_part.geometry.translate((ox, oy, oz))
            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'operation_type': 'pattern', 'pattern_type': 'linear',
                    'pattern_index': i, 'source': input_name,
                }
            )
            part = self._make_and_register_part(
                f"{name}_{i}", geometry, metadata, (ox, oy, oz), backend=input_part.backend
            )
            parts.append(part)
            logger.debug(f"Linear pattern: created {part.name} at ({ox}, {oy}, {oz})")

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
        self._require(name, spec, 'count', 'Circular')
        self._require(name, spec, 'axis', 'Circular')
        self._require(name, spec, 'center', 'Circular')
        input_name, input_part = self._get_input_part(name, spec, 'Circular')

        count = spec['count']
        axis = spec['axis']
        center = spec['center']
        start_angle = spec.get('start_angle', 0)
        end_angle = spec.get('end_angle', 360)
        radius = spec.get('radius', None)

        if not isinstance(count, int) or count < 1:
            raise PatternBuilderError(
                f"Circular pattern '{name}' count must be integer >= 1, got: {count}",
                operation_name=name
            )

        axis_vector = self._resolve_circular_axis(name, axis)
        center_point = self._validate_circular_center(name, center)

        angle_step = 0 if count == 1 else (end_angle - start_angle) / count
        radial_offset = self._circular_radial_offset(axis_vector, radius)

        parts = []
        for i in range(count):
            angle = start_angle + angle_step * i
            geometry = self._build_circular_geometry(
                input_part,
                center_point,
                axis_vector,
                angle,
                radial_offset,
            )
            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'operation_type': 'pattern', 'pattern_type': 'circular',
                    'pattern_index': i, 'source': input_name, 'angle': angle,
                }
            )
            part = self._make_and_register_part(
                f"{name}_{i}", geometry, metadata, backend=input_part.backend
            )
            parts.append(part)
            logger.debug(f"Circular pattern: created {part.name} at angle {angle}°")

        logger.info(f"Circular pattern: created {count} copies around {axis_vector}")
        return parts

    def _resolve_grid_count(self, name: str, spec: Dict[str, Any]) -> tuple:
        """Return (rows, cols), handling legacy count_x/count_y API."""
        if 'count' not in spec:
            if 'count_x' in spec and 'count_y' in spec:
                cx, cy = spec['count_x'], spec['count_y']
                spec['count'] = [cx, cy]
                logger.warning(
                    f"Grid pattern '{name}' uses deprecated 'count_x'/'count_y'. "
                    f"Use 'count: [{cx}, {cy}]'. Removed in v4.0."
                )
            else:
                raise PatternBuilderError(
                    f"Grid pattern '{name}' missing 'count' field. "
                    f"Use 'count: [rows, cols]' (or legacy 'count_x' and 'count_y')",
                    operation_name=name
                )
        count = spec['count']
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
        return rows, cols

    def _resolve_grid_spacing(self, name: str, spec: Dict[str, Any]) -> list:
        """Return [dx, dy, dz], handling legacy spacing_x/y/z API."""
        if 'spacing' not in spec:
            if 'spacing_x' in spec and 'spacing_y' in spec:
                sx, sy, sz = spec['spacing_x'], spec['spacing_y'], spec.get('spacing_z', 0)
                spec['spacing'] = [sx, sy, sz]
                logger.warning(
                    f"Grid pattern '{name}' uses deprecated 'spacing_x/y/z'. "
                    f"Use 'spacing: [{sx}, {sy}, {sz}]'. Removed in v4.0."
                )
            else:
                raise PatternBuilderError(
                    f"Grid pattern '{name}' missing 'spacing' field. "
                    f"Use 'spacing: [dx, dy, dz]' (or legacy 'spacing_x/y/z')",
                    operation_name=name
                )
        spacing = spec['spacing']
        if not isinstance(spacing, list) or len(spacing) != 3:
            raise PatternBuilderError(
                f"Grid pattern '{name}' spacing must be [dx, dy, dz], got: {spacing}",
                operation_name=name
            )
        return spacing

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
        self._require(name, spec, 'input', 'Grid')
        rows, cols = self._resolve_grid_count(name, spec)
        spacing = self._resolve_grid_spacing(name, spec)
        input_name, input_part = self._get_input_part(name, spec, 'Grid')

        start_offset = spec.get('start_offset', [0, 0, 0])
        center_grid = spec.get('center_grid', False)
        grid_offset_x = -(rows - 1) * spacing[0] / 2 if center_grid else 0
        grid_offset_y = -(cols - 1) * spacing[1] / 2 if center_grid else 0

        parts = []
        for row in range(rows):
            for col in range(cols):
                ox = start_offset[0] + grid_offset_x + row * spacing[0]
                oy = start_offset[1] + grid_offset_y + col * spacing[1]
                oz = start_offset[2] + spacing[2]
                if input_part.backend is not None:
                    geometry = input_part.backend.translate(input_part.geometry, (ox, oy, oz))
                else:
                    geometry = input_part.geometry.translate((ox, oy, oz))
                metadata = copy_propagating_metadata(
                    source_metadata=input_part.metadata,
                    target_metadata={
                        'operation_type': 'pattern', 'pattern_type': 'grid',
                        'grid_position': (row, col), 'source': input_name,
                    }
                )
                part = self._make_and_register_part(
                    f"{name}_{row}_{col}", geometry, metadata, (ox, oy, oz), backend=input_part.backend
                )
                parts.append(part)
                logger.debug(f"Grid pattern: created {part.name} at ({ox}, {oy}, {oz})")

        logger.info(f"Grid pattern: created {rows}x{cols} = {len(parts)} parts")
        return parts

    def __repr__(self) -> str:
        return f"PatternBuilder(parts={len(self.registry)}, resolver={self.resolver})"
