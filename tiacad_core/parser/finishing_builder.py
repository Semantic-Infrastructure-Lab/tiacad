"""
FinishingBuilder - Execute finishing operations on Part objects

Handles finishing operations (fillet, chamfer) to add professional
finishing touches to parts.

Supported Operations:
- fillet: Round edges with specified radius
- chamfer: Bevel edges with specified length(s)
- Edge selection: Various selector strategies (all, direction, parallel, perpendicular)

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import logging
from typing import Dict, Any, List, Union, Optional
import cadquery as cq

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class FinishingBuilderError(TiaCADError):
    """Error during finishing operations"""
    def __init__(self, message: str, operation_name: str = None):
        super().__init__(message)
        self.operation_name = operation_name


class FinishingBuilder:
    """
    Executes finishing operations on Part objects.

    Finishing operations modify parts in-place by adding professional
    finishing touches like rounded (filleted) or beveled (chamfered) edges.

    Supports:
    - fillet: Round edges with specified radius
    - chamfer: Bevel edges with specified length(s)
    - Edge selection: various selector strategies

    Usage:
        builder = FinishingBuilder(part_registry, parameter_resolver)
        builder.execute_finishing_operation('finished_part', {
            'finish': 'fillet',
            'input': 'box_part',
            'radius': 2.0,
            'edges': 'all'
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver):
        """
        Initialize finishing builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
        """
        self.registry = part_registry
        self.resolver = parameter_resolver

    def execute_finishing_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a finishing operation and update part in registry.

        Note: Finishing operations modify the part in-place rather than
        creating a new part, as they are refinements of existing geometry.

        Args:
            name: Operation name (for error messages and tracking)
            spec: Operation specification with 'finish' field

        Raises:
            FinishingBuilderError: If operation fails
        """
        # Resolve parameters first
        resolved_spec = self.resolver.resolve(spec)

        # Validate finish field
        if 'finish' not in resolved_spec:
            raise FinishingBuilderError(
                f"Finishing operation '{name}' missing 'finish' field",
                operation_name=name
            )

        finish_type = resolved_spec['finish']

        # Execute based on finish type
        try:
            if finish_type == 'fillet':
                self._execute_fillet(name, resolved_spec)
            elif finish_type == 'chamfer':
                self._execute_chamfer(name, resolved_spec)
            else:
                raise FinishingBuilderError(
                    f"Unknown finishing operation '{finish_type}'. "
                    f"Supported: fillet, chamfer",
                    operation_name=name
                )

            logger.info(f"Finishing operation '{finish_type}' completed for '{name}'")

        except FinishingBuilderError:
            raise
        except Exception as e:
            raise FinishingBuilderError(
                f"Finishing operation '{finish_type}' failed for '{name}': {str(e)}",
                operation_name=name
            ) from e

    def _execute_fillet(self, name: str, spec: Dict[str, Any]):
        """
        Execute fillet operation - round edges.

        Args:
            name: Operation name (for error messages)
            spec: Specification with 'input', 'radius', and 'edges' fields

        Raises:
            FinishingBuilderError: If operation fails
        """
        # Validate required fields
        if 'input' not in spec:
            raise FinishingBuilderError(
                f"Fillet operation '{name}' missing 'input' field",
                operation_name=name
            )

        if 'radius' not in spec:
            raise FinishingBuilderError(
                f"Fillet operation '{name}' missing 'radius' field",
                operation_name=name
            )

        input_name = spec['input']
        radius = spec['radius']
        edges_spec = spec.get('edges', 'all')

        # Validate radius is numeric
        if not isinstance(radius, (int, float)):
            raise FinishingBuilderError(
                f"Fillet operation '{name}' radius must be a number, got: {type(radius).__name__}",
                operation_name=name
            )

        if radius <= 0:
            raise FinishingBuilderError(
                f"Fillet operation '{name}' radius must be positive, got: {radius}",
                operation_name=name
            )

        # Retrieve input part
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise FinishingBuilderError(
                f"Fillet operation '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        part = self.registry.get(input_name)

        # Build edge selector
        edge_selector = self._build_edge_selector(edges_spec, name)

        # Apply fillet
        try:
            if edge_selector is None:
                # Fillet all edges
                result = part.geometry.edges().fillet(radius)
            else:
                # Fillet selected edges
                result = part.geometry.edges(edge_selector).fillet(radius)

            # Update part geometry in-place
            part.geometry = result

            # Track finishing operation in metadata
            if 'finishing_ops' not in part.metadata:
                part.metadata['finishing_ops'] = []
            part.metadata['finishing_ops'].append({
                'type': 'fillet',
                'radius': radius,
                'edges': edges_spec
            })

            logger.debug(f"Fillet: applied radius={radius} to part '{input_name}'")

        except Exception as e:
            raise FinishingBuilderError(
                f"Fillet operation '{name}' failed applying fillet to '{input_name}': {str(e)}",
                operation_name=name
            ) from e

    def _execute_chamfer(self, name: str, spec: Dict[str, Any]):
        """
        Execute chamfer operation - bevel edges.

        Args:
            name: Operation name (for error messages)
            spec: Specification with 'input', 'length', optional 'length2', and 'edges' fields

        Raises:
            FinishingBuilderError: If operation fails
        """
        # Validate required fields
        if 'input' not in spec:
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' missing 'input' field",
                operation_name=name
            )

        if 'length' not in spec:
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' missing 'length' field",
                operation_name=name
            )

        input_name = spec['input']
        length = spec['length']
        length2 = spec.get('length2', None)
        edges_spec = spec.get('edges', 'all')

        # Validate length is numeric
        if not isinstance(length, (int, float)):
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' length must be a number, got: {type(length).__name__}",
                operation_name=name
            )

        if length <= 0:
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' length must be positive, got: {length}",
                operation_name=name
            )

        # Validate length2 if provided
        if length2 is not None:
            if not isinstance(length2, (int, float)):
                raise FinishingBuilderError(
                    f"Chamfer operation '{name}' length2 must be a number, got: {type(length2).__name__}",
                    operation_name=name
                )
            if length2 <= 0:
                raise FinishingBuilderError(
                    f"Chamfer operation '{name}' length2 must be positive, got: {length2}",
                    operation_name=name
                )

        # Retrieve input part
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' input part '{input_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        part = self.registry.get(input_name)

        # Build edge selector
        edge_selector = self._build_edge_selector(edges_spec, name)

        # Apply chamfer
        try:
            if edge_selector is None:
                # Chamfer all edges
                if length2 is None:
                    result = part.geometry.edges().chamfer(length)
                else:
                    result = part.geometry.edges().chamfer(length, length2)
            else:
                # Chamfer selected edges
                if length2 is None:
                    result = part.geometry.edges(edge_selector).chamfer(length)
                else:
                    result = part.geometry.edges(edge_selector).chamfer(length, length2)

            # Update part geometry in-place
            part.geometry = result

            # Track finishing operation in metadata
            if 'finishing_ops' not in part.metadata:
                part.metadata['finishing_ops'] = []

            op_info = {
                'type': 'chamfer',
                'length': length,
                'edges': edges_spec
            }
            if length2 is not None:
                op_info['length2'] = length2

            part.metadata['finishing_ops'].append(op_info)

            logger.debug(f"Chamfer: applied length={length} to part '{input_name}'")

        except Exception as e:
            raise FinishingBuilderError(
                f"Chamfer operation '{name}' failed applying chamfer to '{input_name}': {str(e)}",
                operation_name=name
            ) from e

    def _build_edge_selector(self, edges_spec: Union[str, Dict[str, Any]], operation_name: str) -> Optional[str]:
        """
        Build CadQuery edge selector from YAML specification.

        Args:
            edges_spec: Edge selection specification
            operation_name: Operation name (for error messages)

        Returns:
            CadQuery selector string or None (for all edges)

        Raises:
            FinishingBuilderError: If selector specification is invalid
        """
        # Case 1: "all" - select all edges
        if edges_spec == 'all':
            return None

        # Case 2: Dictionary with selector strategy
        if isinstance(edges_spec, dict):
            # Direction selector: edges aligned with direction
            if 'direction' in edges_spec:
                axis = self._normalize_axis(edges_spec['direction'], operation_name)
                return f">{axis}"

            # Parallel-to selector: edges parallel to direction
            elif 'parallel_to' in edges_spec:
                axis = self._normalize_axis(edges_spec['parallel_to'], operation_name)
                return f"|{axis}"

            # Perpendicular-to selector: edges perpendicular to direction
            elif 'perpendicular_to' in edges_spec:
                axis = self._normalize_axis(edges_spec['perpendicular_to'], operation_name)
                return f"#{axis}"

            # String selector: direct pass-through to CadQuery
            elif 'selector' in edges_spec:
                return edges_spec['selector']

            else:
                raise FinishingBuilderError(
                    f"Invalid edge selector specification for '{operation_name}'. "
                    f"Expected 'direction', 'parallel_to', 'perpendicular_to', or 'selector', "
                    f"got: {list(edges_spec.keys())}",
                    operation_name=operation_name
                )

        # Invalid specification
        raise FinishingBuilderError(
            f"Invalid edge selector specification for '{operation_name}'. "
            f"Expected 'all' or dict with selector strategy, got: {type(edges_spec).__name__}",
            operation_name=operation_name
        )

    def _normalize_axis(self, axis: Union[str, List[float]], operation_name: str) -> str:
        """
        Normalize axis specification to CadQuery axis string (X, Y, Z).

        Args:
            axis: Axis specification (string or vector)
            operation_name: Operation name (for error messages)

        Returns:
            CadQuery axis string ('X', 'Y', or 'Z')

        Raises:
            FinishingBuilderError: If axis specification is invalid
        """
        # String axis (X, Y, Z)
        if isinstance(axis, str):
            if axis in ['X', 'Y', 'Z']:
                return axis
            else:
                raise FinishingBuilderError(
                    f"Invalid axis '{axis}' in operation '{operation_name}'. "
                    f"Expected 'X', 'Y', or 'Z'",
                    operation_name=operation_name
                )

        # Vector axis [x, y, z]
        if isinstance(axis, (list, tuple)):
            if len(axis) != 3:
                raise FinishingBuilderError(
                    f"Invalid axis vector {axis} in operation '{operation_name}'. "
                    f"Expected 3 components [x, y, z]",
                    operation_name=operation_name
                )

            # Map standard unit vectors to axis strings
            if axis == [1, 0, 0] or axis == [1.0, 0.0, 0.0]:
                return 'X'
            elif axis == [0, 1, 0] or axis == [0.0, 1.0, 0.0]:
                return 'Y'
            elif axis == [0, 0, 1] or axis == [0.0, 0.0, 1.0]:
                return 'Z'
            else:
                raise FinishingBuilderError(
                    f"Unsupported axis vector {axis} in operation '{operation_name}'. "
                    f"Only standard unit vectors supported: [1,0,0], [0,1,0], [0,0,1]",
                    operation_name=operation_name
                )

        raise FinishingBuilderError(
            f"Invalid axis type in operation '{operation_name}'. "
            f"Expected string (X/Y/Z) or vector [x,y,z], got: {type(axis).__name__}",
            operation_name=operation_name
        )

    def __repr__(self) -> str:
        return f"FinishingBuilder(parts={len(self.registry)}, resolver={self.resolver})"
