"""
Dependency extraction from TiaCAD YAML

Builds a ModelGraph by analyzing YAML specifications and extracting
dependency relationships between parameters, parts, and operations.

Author: TIA
Version: 3.2.0
"""

import re
from typing import Dict, Any, Set, List
import hashlib
import json

from .model_graph import ModelGraph, GraphNode, NodeType
from ..utils.exceptions import TiaCADError


class GraphBuilderError(TiaCADError):
    """Error during graph construction"""
    pass


class GraphBuilder:
    """
    Builds dependency graph from TiaCAD YAML.

    Extracts three types of dependencies:
    1. Parameter → Parameter (via ${...} expressions)
    2. Part → Parameter (parts reference parameters)
    3. Operation → Part (operations transform parts)

    Example:
        >>> builder = GraphBuilder()
        >>> graph = builder.build_graph(yaml_data)
        >>> print(f"Built graph with {len(graph)} nodes")
    """

    # Regex pattern for ${param} and ${expr} references
    PARAM_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self):
        self.graph = ModelGraph()
        self.parameter_names: Set[str] = set()

    def build_graph(self, yaml_data: Dict[str, Any]) -> ModelGraph:
        """
        Convert YAML to dependency graph.

        Phase 1: Add all nodes (parameters, parts, operations)
        Phase 2: Extract dependencies (analyze ${...} references, inputs, etc.)
        Phase 3: Validate (detect cycles)

        Args:
            yaml_data: Parsed YAML dictionary

        Returns:
            ModelGraph with all dependencies

        Raises:
            GraphBuilderError: If circular dependencies detected
        """
        # Phase 1: Add all nodes
        self._add_parameter_nodes(yaml_data.get('parameters', {}))
        self._add_sketch_nodes(yaml_data.get('sketches', {}))
        self._add_part_nodes(yaml_data.get('parts', {}))
        self._add_operation_nodes(yaml_data.get('operations', {}))
        self._add_reference_nodes(yaml_data.get('references', {}))

        # Phase 2: Extract dependencies
        self._extract_parameter_dependencies(yaml_data.get('parameters', {}))
        self._extract_sketch_dependencies(yaml_data.get('sketches', {}))
        self._extract_part_dependencies(yaml_data.get('parts', {}))
        self._extract_operation_dependencies(yaml_data.get('operations', {}))
        self._extract_reference_dependencies(yaml_data.get('references', {}))

        # Phase 3: Validate
        cycles = self.graph.detect_cycles()
        if cycles:
            # Format cycle for error message
            cycle = cycles[0]  # Show first cycle
            cycle_str = ' -> '.join(cycle + [cycle[0]])
            raise GraphBuilderError(f"Circular dependency detected: {cycle_str}")

        return self.graph

    # =========================================================================
    # Phase 1: Add Nodes
    # =========================================================================

    def _add_parameter_nodes(self, parameters: Dict[str, Any]) -> None:
        """Add parameter nodes to graph"""
        for param_name, param_value in parameters.items():
            self.parameter_names.add(param_name)

            node = GraphNode(
                node_id=f"parameter:{param_name}",
                node_type=NodeType.PARAMETER,
                name=param_name,
                spec={'value': param_value},
                hash_value=self._hash_spec(param_value)
            )
            self.graph.add_node(node)

    def _add_sketch_nodes(self, sketches: Dict[str, Any]) -> None:
        """Add sketch nodes to graph"""
        for sketch_name, sketch_spec in sketches.items():
            node = GraphNode(
                node_id=f"sketch:{sketch_name}",
                node_type=NodeType.SKETCH,
                name=sketch_name,
                spec=sketch_spec,
                hash_value=self._hash_spec(sketch_spec)
            )
            self.graph.add_node(node)

    def _add_part_nodes(self, parts: Dict[str, Any]) -> None:
        """Add part (primitive) nodes to graph"""
        for part_name, part_spec in parts.items():
            node = GraphNode(
                node_id=f"part:{part_name}",
                node_type=NodeType.PART,
                name=part_name,
                spec=part_spec,
                hash_value=self._hash_spec(part_spec)
            )
            self.graph.add_node(node)

    def _add_operation_nodes(self, operations: Dict[str, Any]) -> None:
        """Add operation nodes to graph"""
        for op_name, op_spec in operations.items():
            # Check if this is a pattern operation
            is_pattern = op_spec.get('type') in ('pattern', 'circular', 'linear', 'grid')

            node = GraphNode(
                node_id=f"operation:{op_name}",
                node_type=NodeType.OPERATION,
                name=op_name,
                spec=op_spec,
                hash_value=self._hash_spec(op_spec),
                is_pattern=is_pattern
            )
            self.graph.add_node(node)

    def _add_reference_nodes(self, references: Dict[str, Any]) -> None:
        """Add reference nodes to graph"""
        for ref_name, ref_spec in references.items():
            node = GraphNode(
                node_id=f"reference:{ref_name}",
                node_type=NodeType.REFERENCE,
                name=ref_name,
                spec=ref_spec,
                hash_value=self._hash_spec(ref_spec)
            )
            self.graph.add_node(node)

    # =========================================================================
    # Phase 2: Extract Dependencies
    # =========================================================================

    def _extract_parameter_dependencies(self, parameters: Dict[str, Any]) -> None:
        """
        Extract parameter → parameter dependencies.

        Parameters can reference other parameters via ${...} expressions.
        Example: width: 100, area: ${width * width}
        Dependency: parameter:area → parameter:width
        """
        for param_name, param_value in parameters.items():
            dependent_id = f"parameter:{param_name}"

            # Find all parameter references in value
            refs = self._find_parameter_refs(param_value)

            for ref_param in refs:
                if ref_param in self.parameter_names and ref_param != param_name:
                    # Add dependency: area depends on width
                    self.graph.add_dependency(dependent_id, f"parameter:{ref_param}")

    def _extract_sketch_dependencies(self, sketches: Dict[str, Any]) -> None:
        """
        Extract sketch → parameter dependencies.

        Sketches can use parameters in constraints, dimensions, etc.
        """
        for sketch_name, sketch_spec in sketches.items():
            dependent_id = f"sketch:{sketch_name}"

            # Find parameter references in entire sketch spec
            refs = self._find_parameter_refs(sketch_spec)

            for ref_param in refs:
                if ref_param in self.parameter_names:
                    self.graph.add_dependency(dependent_id, f"parameter:{ref_param}")

    def _extract_part_dependencies(self, parts: Dict[str, Any]) -> None:
        """
        Extract part → parameter and part → sketch dependencies.

        Parts can reference:
        - Parameters (in dimensions, positions, etc.)
        - Sketches (for extrude, revolve base)
        """
        for part_name, part_spec in parts.items():
            dependent_id = f"part:{part_name}"

            # Find parameter references
            refs = self._find_parameter_refs(part_spec)
            for ref_param in refs:
                if ref_param in self.parameter_names:
                    self.graph.add_dependency(dependent_id, f"parameter:{ref_param}")

            # Check for sketch references
            if 'sketch' in part_spec:
                sketch_name = part_spec['sketch']
                sketch_id = f"sketch:{sketch_name}"
                if sketch_id in self.graph:
                    self.graph.add_dependency(dependent_id, sketch_id)

    def _extract_operation_dependencies(self, operations: Dict[str, Any]) -> None:
        """
        Extract operation → part and operation → parameter dependencies.

        Operations can reference:
        - Parts (as inputs, bases, tools)
        - Parameters (in transformation values)
        """
        for op_name, op_spec in operations.items():
            dependent_id = f"operation:{op_name}"
            op_type = op_spec.get('type', '')

            # Find parameter references
            refs = self._find_parameter_refs(op_spec)
            for ref_param in refs:
                if ref_param in self.parameter_names:
                    self.graph.add_dependency(dependent_id, f"parameter:{ref_param}")

            # Extract part dependencies based on operation type
            part_refs = self._extract_operation_part_refs(op_spec, op_type)

            for part_name in part_refs:
                # Part could be either a primitive or another operation
                part_id = f"part:{part_name}"
                operation_id = f"operation:{part_name}"

                if part_id in self.graph:
                    self.graph.add_dependency(dependent_id, part_id)
                elif operation_id in self.graph:
                    self.graph.add_dependency(dependent_id, operation_id)

    def _extract_reference_dependencies(self, references: Dict[str, Any]) -> None:
        """
        Extract reference → part and reference → parameter dependencies.

        References position parts in space and can use parameters.
        """
        for ref_name, ref_spec in references.items():
            dependent_id = f"reference:{ref_name}"

            # Find parameter references
            refs = self._find_parameter_refs(ref_spec)
            for ref_param in refs:
                if ref_param in self.parameter_names:
                    self.graph.add_dependency(dependent_id, f"parameter:{ref_param}")

            # Check for part reference
            if 'part' in ref_spec:
                part_name = ref_spec['part']
                part_id = f"part:{part_name}"
                operation_id = f"operation:{part_name}"

                if part_id in self.graph:
                    self.graph.add_dependency(dependent_id, part_id)
                elif operation_id in self.graph:
                    self.graph.add_dependency(dependent_id, operation_id)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_parameter_refs(self, obj: Any) -> Set[str]:
        """
        Recursively find ${param} references in any object.

        Supports strings, dicts, lists, and nested structures.

        Args:
            obj: Object to scan (can be str, dict, list, etc.)

        Returns:
            Set of parameter names referenced

        Example:
            >>> refs = builder._find_parameter_refs({'width': '${base_width}'})
            >>> print(refs)  # {'base_width'}
        """
        refs = set()

        def extract(value):
            if isinstance(value, str):
                # Find all ${...} patterns
                for expr in self.PARAM_PATTERN.findall(value):
                    # Extract identifiers from expression
                    # e.g., "${width * 2}" → ["width"]
                    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
                    refs.update(identifiers)

            elif isinstance(value, dict):
                for v in value.values():
                    extract(v)

            elif isinstance(value, list):
                for item in value:
                    extract(item)

        extract(obj)
        return refs

    def _extract_operation_part_refs(self, op_spec: Dict[str, Any], op_type: str) -> Set[str]:
        """
        Extract part names referenced by an operation.

        Different operation types reference parts differently:
        - fillet/chamfer: 'input'
        - boolean: 'inputs' list (union/difference/intersection)
        - union/subtract/intersect: 'base' + 'parts' list
        - mirror/transform: 'input'
        - pattern: 'input'

        Args:
            op_spec: Operation specification
            op_type: Operation type

        Returns:
            Set of part names referenced
        """
        part_refs = set()

        # Standard input field
        if 'input' in op_spec:
            part_refs.add(op_spec['input'])

        # Boolean operations with 'inputs' list (union/difference/intersection)
        if 'inputs' in op_spec and isinstance(op_spec['inputs'], list):
            part_refs.update(op_spec['inputs'])

        # Boolean operations (legacy/alternative syntax)
        if 'base' in op_spec:
            part_refs.add(op_spec['base'])

        if 'parts' in op_spec and isinstance(op_spec['parts'], list):
            part_refs.update(op_spec['parts'])

        # Subtract operation (can have 'subtract' list)
        if 'subtract' in op_spec and isinstance(op_spec['subtract'], list):
            part_refs.update(op_spec['subtract'])

        # Union operation (can have 'union' list)
        if 'union' in op_spec and isinstance(op_spec['union'], list):
            part_refs.update(op_spec['union'])

        # Tool reference (for some operations)
        if 'tool' in op_spec:
            part_refs.add(op_spec['tool'])

        return part_refs

    def _hash_spec(self, spec: Any) -> str:
        """
        Compute stable hash of a specification.

        Used for change detection in incremental builds.

        Args:
            spec: Specification to hash (any JSON-serializable object)

        Returns:
            16-character hex hash
        """
        # Convert to stable JSON string
        json_str = json.dumps(spec, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
