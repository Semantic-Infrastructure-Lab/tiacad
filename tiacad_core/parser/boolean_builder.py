"""
BooleanBuilder - Execute boolean operations on Part objects

Handles boolean operations (union, difference, intersection) to create
complex geometries from simple parts.

Supported Operations:
- union: Combine multiple parts into one
- difference: Subtract parts from a base part
- intersection: Find common volume between parts

Author: TIA
Version: 0.1.0-alpha (Phase 2)
"""

import logging
import re
from typing import Dict, Any, List, Union
import cadquery as cq

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class BooleanBuilderError(TiaCADError):
    """Error during boolean operations"""
    def __init__(self, message: str, operation_name: str = None):
        super().__init__(message)
        self.operation_name = operation_name


class BooleanBuilder:
    """
    Executes boolean operations on Part objects.

    Supports:
    - union: Combine multiple parts
    - difference: Subtract parts from base
    - intersection: Find common volume

    Usage:
        builder = BooleanBuilder(part_registry, parameter_resolver)
        builder.execute_boolean_operation('result', {
            'operation': 'union',
            'inputs': ['part_a', 'part_b']
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver):
        """
        Initialize boolean builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
        """
        self.registry = part_registry
        self.resolver = parameter_resolver

    def _expand_str_item(self, item: str) -> List[str]:
        """Expand a string item: wildcard pattern or plain part name."""
        if '*' not in item:
            return [item]
        prefix = item.replace('*', '')
        matches = self._find_pattern_matches(prefix)
        if not matches:
            raise BooleanBuilderError(
                f"Pattern '{item}' matched no parts. "
                f"Available parts: {', '.join(self.registry.list_parts())}"
            )
        logger.debug(f"Expanded pattern '{item}' to {len(matches)} parts: {matches}")
        return matches

    def _expand_dict_item(self, item: Dict[str, Any]) -> List[str]:
        """Expand a dict item: {pattern:} or {range:} specification."""
        if 'pattern' in item:
            pattern_name = item['pattern']
            matches = self._find_pattern_matches(f"{pattern_name}_")
            if not matches:
                raise BooleanBuilderError(
                    f"Pattern '{pattern_name}' matched no parts. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )
            logger.debug(f"Expanded pattern '{pattern_name}' to {len(matches)} parts")
            return matches
        if 'range' in item:
            expanded = self._expand_range_spec(item['range'])
            logger.debug(f"Expanded range '{item['range']}' to {len(expanded)} parts")
            return expanded
        raise BooleanBuilderError(
            f"Invalid pattern dict: {item}. Expected 'pattern' or 'range' key"
        )

    def _expand_part_list(self, part_list: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """
        Expand pattern references in part list to concrete part names.

        Supports: plain names, wildcard strings ("bolt_*"), {"pattern": "name"},
        {"range": "name[0..5]"}, {"range": "name[*]"}.
        """
        expanded = []
        for item in part_list:
            if isinstance(item, str):
                expanded.extend(self._expand_str_item(item))
            elif isinstance(item, dict):
                expanded.extend(self._expand_dict_item(item))
            else:
                raise BooleanBuilderError(
                    f"Invalid part list item type: {type(item).__name__}. "
                    f"Expected str or dict"
                )
        return expanded

    def _find_pattern_matches(self, prefix: str) -> List[str]:
        """
        Find all parts matching a prefix pattern.

        Args:
            prefix: Pattern prefix (e.g., "bolt_circle_")

        Returns:
            List of matching part names, sorted numerically if possible
        """
        all_parts = self.registry.list_parts()
        matches = [p for p in all_parts if p.startswith(prefix)]

        # Try to sort numerically by suffix
        def sort_key(name):
            suffix = name[len(prefix):]
            try:
                return (0, int(suffix))  # Numeric suffix
            except ValueError:
                return (1, suffix)  # Non-numeric suffix (alphabetically)

        return sorted(matches, key=sort_key)

    def _expand_range_spec(self, range_spec: str) -> List[str]:
        """
        Expand range specification to part names.

        Supports:
        - "bolt_circle[0..5]" → bolt_circle_0, bolt_circle_1, ..., bolt_circle_5
        - "bolt_circle[*]" → all parts starting with bolt_circle_

        Args:
            range_spec: Range specification string

        Returns:
            List of part names in range

        Raises:
            BooleanBuilderError: If range syntax invalid or no matches
        """
        # Pattern: "name[start..end]" or "name[*]"
        match = re.match(r'^(.+?)\[(.+?)\]$', range_spec)
        if not match:
            raise BooleanBuilderError(
                f"Invalid range syntax: '{range_spec}'. "
                f"Expected 'name[start..end]' or 'name[*]'"
            )

        base_name = match.group(1)
        range_part = match.group(2)

        if range_part == '*':
            # Wildcard: all parts with this prefix
            matches = self._find_pattern_matches(f"{base_name}_")
            if not matches:
                raise BooleanBuilderError(
                    f"Range '{range_spec}' matched no parts. "
                    f"Available parts: {', '.join(self.registry.list_parts())}"
                )
            return matches

        else:
            # Numeric range: "0..5"
            range_match = re.match(r'^(\d+)\.\.(\d+)$', range_part)
            if not range_match:
                raise BooleanBuilderError(
                    f"Invalid range format: '{range_part}'. "
                    f"Expected 'start..end' (e.g., '0..5') or '*'"
                )

            start = int(range_match.group(1))
            end = int(range_match.group(2))

            if start > end:
                raise BooleanBuilderError(
                    f"Invalid range: start ({start}) > end ({end})"
                )

            # Generate part names and validate they exist
            part_names = []
            for i in range(start, end + 1):
                part_name = f"{base_name}_{i}"
                if not self.registry.exists(part_name):
                    raise BooleanBuilderError(
                        f"Range '{range_spec}' references non-existent part '{part_name}'. "
                        f"Available parts: {', '.join(self.registry.list_parts())}"
                    )
                part_names.append(part_name)

            return part_names

    def _find_source_part(self, operation: str, resolved_spec: Dict[str, Any]):
        """Find the source part for metadata inheritance based on operation type."""
        if operation in ('difference', 'intersection'):
            base_name = resolved_spec.get('base')
            if base_name and self.registry.exists(base_name):
                return self.registry.get(base_name)
        elif operation == 'union':
            inputs = resolved_spec.get('inputs', [])
            if inputs:
                first = inputs[0]
                if isinstance(first, str) and '*' not in first and self.registry.exists(first):
                    return self.registry.get(first)
        return None

    def execute_boolean_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a boolean operation and add result to registry.

        Args:
            name: New part name
            spec: Operation specification with 'operation' field

        Raises:
            BooleanBuilderError: If operation fails
        """
        resolved_spec = self.resolver.resolve(spec)

        if 'operation' not in resolved_spec:
            raise BooleanBuilderError(
                f"Boolean operation '{name}' missing 'operation' field",
                operation_name=name
            )

        operation = resolved_spec['operation']

        try:
            if operation == 'union':
                geometry = self._execute_union(name, resolved_spec)
            elif operation == 'difference':
                geometry = self._execute_difference(name, resolved_spec)
            elif operation == 'intersection':
                geometry = self._execute_intersection(name, resolved_spec)
            else:
                raise BooleanBuilderError(
                    f"Unknown boolean operation '{operation}'. "
                    f"Supported: union, difference, intersection",
                    operation_name=name
                )

            source_part = self._find_source_part(operation, resolved_spec)
            from .metadata_utils import copy_propagating_metadata
            metadata = copy_propagating_metadata(
                source_metadata=source_part.metadata if source_part else None,
                target_metadata={'operation_type': 'boolean', 'boolean_op': operation}
            )

            self.registry.add(Part(name=name, geometry=geometry, metadata=metadata))
            logger.info(f"Boolean operation '{operation}' created part '{name}'")

        except BooleanBuilderError:
            raise
        except Exception as e:
            raise BooleanBuilderError(
                f"Boolean operation '{operation}' failed for '{name}': {str(e)}",
                operation_name=name
            ) from e

    def _execute_union(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Execute union operation - combine multiple parts.

        Args:
            name: Operation name (for error messages)
            spec: Specification with 'inputs' field (list of part names)

        Returns:
            CadQuery Workplane with combined geometry

        Raises:
            BooleanBuilderError: If inputs invalid or union fails
        """
        # Validate inputs field
        if 'inputs' not in spec:
            raise BooleanBuilderError(
                f"Union operation '{name}' missing 'inputs' field",
                operation_name=name
            )

        inputs = spec['inputs']
        if not isinstance(inputs, list):
            raise BooleanBuilderError(
                f"Union operation '{name}' inputs must be a list, got: {type(inputs).__name__}",
                operation_name=name
            )

        # Expand pattern references to concrete part names BEFORE validation
        inputs = self._expand_part_list(inputs)

        if len(inputs) < 2:
            raise BooleanBuilderError(
                f"Union operation '{name}' requires at least 2 inputs, got {len(inputs)}",
                operation_name=name
            )

        # Retrieve all parts
        parts = []
        for input_name in inputs:
            if not self.registry.exists(input_name):
                available = ', '.join(self.registry.list_parts())
                raise BooleanBuilderError(
                    f"Union operation '{name}' input part '{input_name}' not found. "
                    f"Available parts: {available}",
                    operation_name=name
                )
            parts.append(self.registry.get(input_name))

        # Start with first part's geometry
        result = parts[0].geometry

        # Union remaining parts
        for i, part in enumerate(parts[1:], start=1):
            try:
                result = result.union(part.geometry)
                logger.debug(f"Union: combined part {i+1}/{len(parts)}")
            except Exception as e:
                raise BooleanBuilderError(
                    f"Union operation '{name}' failed combining part '{part.name}': {str(e)}",
                    operation_name=name
                ) from e

        logger.info(f"Union: successfully combined {len(parts)} parts")
        return result

    def _execute_difference(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Execute difference operation - subtract parts from base.

        Args:
            name: Operation name (for error messages)
            spec: Specification with 'base' and 'subtract' fields

        Returns:
            CadQuery Workplane with base minus subtracted parts

        Raises:
            BooleanBuilderError: If inputs invalid or difference fails
        """
        # Validate base field
        if 'base' not in spec:
            raise BooleanBuilderError(
                f"Difference operation '{name}' missing 'base' field",
                operation_name=name
            )

        # Validate subtract field
        if 'subtract' not in spec:
            raise BooleanBuilderError(
                f"Difference operation '{name}' missing 'subtract' field",
                operation_name=name
            )

        base_name = spec['base']
        subtract_list = spec['subtract']

        # Validate subtract is a list
        if not isinstance(subtract_list, list):
            raise BooleanBuilderError(
                f"Difference operation '{name}' subtract must be a list, "
                f"got: {type(subtract_list).__name__}",
                operation_name=name
            )

        # Expand pattern references to concrete part names BEFORE validation
        subtract_list = self._expand_part_list(subtract_list)

        if len(subtract_list) == 0:
            raise BooleanBuilderError(
                f"Difference operation '{name}' subtract list cannot be empty",
                operation_name=name
            )

        # Retrieve base part
        if not self.registry.exists(base_name):
            available = ', '.join(self.registry.list_parts())
            raise BooleanBuilderError(
                f"Difference operation '{name}' base part '{base_name}' not found. "
                f"Available parts: {available}",
                operation_name=name
            )

        base_part = self.registry.get(base_name)
        result = base_part.geometry

        # Subtract each part
        for i, subtract_name in enumerate(subtract_list):
            if not self.registry.exists(subtract_name):
                available = ', '.join(self.registry.list_parts())
                raise BooleanBuilderError(
                    f"Difference operation '{name}' subtract part '{subtract_name}' not found. "
                    f"Available parts: {available}",
                    operation_name=name
                )

            subtract_part = self.registry.get(subtract_name)

            try:
                result = result.cut(subtract_part.geometry)
                logger.debug(f"Difference: subtracted part {i+1}/{len(subtract_list)}")
            except Exception as e:
                raise BooleanBuilderError(
                    f"Difference operation '{name}' failed subtracting part '{subtract_name}': {str(e)}",
                    operation_name=name
                ) from e

        logger.info(f"Difference: subtracted {len(subtract_list)} parts from '{base_name}'")
        return result

    def _execute_intersection(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Execute intersection operation - find common volume.

        Args:
            name: Operation name (for error messages)
            spec: Specification with 'inputs' field (list of part names)

        Returns:
            CadQuery Workplane with intersection geometry

        Raises:
            BooleanBuilderError: If inputs invalid or intersection fails
        """
        # Validate inputs field
        if 'inputs' not in spec:
            raise BooleanBuilderError(
                f"Intersection operation '{name}' missing 'inputs' field",
                operation_name=name
            )

        inputs = spec['inputs']
        if not isinstance(inputs, list):
            raise BooleanBuilderError(
                f"Intersection operation '{name}' inputs must be a list, "
                f"got: {type(inputs).__name__}",
                operation_name=name
            )

        # Expand pattern references to concrete part names BEFORE validation
        inputs = self._expand_part_list(inputs)

        if len(inputs) < 2:
            raise BooleanBuilderError(
                f"Intersection operation '{name}' requires at least 2 inputs, got {len(inputs)}",
                operation_name=name
            )

        # Retrieve all parts
        parts = []
        for input_name in inputs:
            if not self.registry.exists(input_name):
                available = ', '.join(self.registry.list_parts())
                raise BooleanBuilderError(
                    f"Intersection operation '{name}' input part '{input_name}' not found. "
                    f"Available parts: {available}",
                    operation_name=name
                )
            parts.append(self.registry.get(input_name))

        # Start with first part's geometry
        result = parts[0].geometry

        # Intersect remaining parts
        for i, part in enumerate(parts[1:], start=1):
            try:
                result = result.intersect(part.geometry)
                logger.debug(f"Intersection: processed part {i+1}/{len(parts)}")
            except Exception as e:
                raise BooleanBuilderError(
                    f"Intersection operation '{name}' failed with part '{part.name}': {str(e)}",
                    operation_name=name
                ) from e

        logger.info(f"Intersection: found common volume of {len(parts)} parts")
        return result

    def __repr__(self) -> str:
        return f"BooleanBuilder(parts={len(self.registry)}, resolver={self.resolver})"
