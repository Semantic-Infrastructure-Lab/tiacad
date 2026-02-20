"""
Core dependency graph for TiaCAD models

Uses NetworkX to track dependencies between parameters, parts, operations,
and references. Enables cycle detection and topological sorting.

Author: TIA
Version: 3.2.0
"""

import networkx as nx
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, List, Optional, Any
import time


class NodeType(Enum):
    """Types of nodes in the dependency graph"""
    PARAMETER = "parameter"    # parameters: section
    PART = "part"              # parts: primitives
    OPERATION = "operation"    # operations: results
    REFERENCE = "reference"    # references: spatial
    SKETCH = "sketch"          # sketches: section


@dataclass
class GraphNode:
    """
    Node in the dependency graph.

    Each node represents a named entity in the TiaCAD model that can
    depend on other nodes or be depended upon.

    Attributes:
        node_id: Unique identifier (e.g., "parameter:width", "part:base")
        node_type: Type of node
        name: Short name (e.g., "width", "base")
        spec: Original YAML specification
        hash_value: Content hash for change detection
        last_built: Timestamp of last successful build
        is_valid: Whether node's cached result is valid
        is_pattern: Whether this is a pattern operation (creates multiple parts)
        metadata: Additional node-specific data
    """
    node_id: str
    node_type: NodeType
    name: str
    spec: Dict[str, Any]
    hash_value: Optional[str] = None
    last_built: Optional[float] = None
    is_valid: bool = True
    is_pattern: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate node_id format"""
        if ':' not in self.node_id:
            raise ValueError(f"node_id must be in format 'type:name', got: {self.node_id}")

        expected_prefix = f"{self.node_type.value}:"
        if not self.node_id.startswith(expected_prefix):
            raise ValueError(
                f"node_id '{self.node_id}' doesn't match type '{self.node_type.value}'"
            )


class ModelGraph:
    """
    Dependency graph for TiaCAD models.

    Tracks dependencies between all entities in a TiaCAD model:
    - Parameters can depend on other parameters (via ${...} expressions)
    - Parts depend on parameters they reference
    - Operations depend on parts they transform
    - References depend on parts they position

    The graph is directed and acyclic (DAG). Cycles are detected and rejected.

    Example:
        >>> graph = ModelGraph()
        >>> graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {...}))
        >>> graph.add_node(GraphNode("part:base", NodeType.PART, "base", {...}))
        >>> graph.add_dependency("part:base", "parameter:width")  # base uses width
        >>> cycles = graph.detect_cycles()  # Should be empty
        >>> order = graph.topological_sort()  # ["parameter:width", "part:base"]
    """

    def __init__(self):
        """Initialize empty dependency graph"""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.valid_nodes: Set[str] = set()

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node to the graph.

        Args:
            node: GraphNode to add

        Raises:
            ValueError: If node with same ID already exists
        """
        if node.node_id in self.nodes:
            raise ValueError(f"Node '{node.node_id}' already exists in graph")

        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)

        if node.is_valid:
            self.valid_nodes.add(node.node_id)

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """
        Add a dependency edge.

        Creates an edge from dependency → dependent, meaning:
        - dependent USES dependency
        - dependency must be built BEFORE dependent
        - Changes to dependency invalidate dependent

        Args:
            dependent: Node that depends on another (e.g., "part:base")
            dependency: Node being depended upon (e.g., "parameter:width")

        Raises:
            ValueError: If either node doesn't exist
        """
        if dependent not in self.nodes:
            raise ValueError(f"Dependent node '{dependent}' not found in graph")
        if dependency not in self.nodes:
            raise ValueError(f"Dependency node '{dependency}' not found in graph")

        # Add edge: dependency → dependent
        # NetworkX convention: edge (a, b) means a → b
        self.graph.add_edge(dependency, dependent)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies.

        Returns:
            List of cycles found. Each cycle is a list of node IDs.
            Empty list if no cycles exist (valid DAG).

        Example:
            >>> cycles = graph.detect_cycles()
            >>> if cycles:
            ...     print(f"Cycle: {' -> '.join(cycles[0])}")
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            # NetworkX might raise for empty graphs
            return []

    def topological_sort(self, nodes: Optional[Set[str]] = None) -> List[str]:
        """
        Return nodes in build order (dependencies before dependents).

        Args:
            nodes: Optional subset of nodes to sort. If None, sorts all nodes.

        Returns:
            List of node IDs in topological order

        Raises:
            nx.NetworkXError: If graph has cycles (shouldn't happen if validated)
        """
        if nodes is None:
            # Sort all nodes
            return list(nx.topological_sort(self.graph))
        else:
            # Sort subset - need to preserve dependency relationships
            subgraph = self.graph.subgraph(nodes)
            return list(nx.topological_sort(subgraph))

    def get_dependencies(self, node_id: str) -> Set[str]:
        """
        Get direct dependencies of a node (what it depends on).

        Args:
            node_id: Node to query

        Returns:
            Set of node IDs this node directly depends on
        """
        if node_id not in self.nodes:
            return set()

        # Predecessors in NetworkX are nodes with edges pointing TO this node
        return set(self.graph.predecessors(node_id))

    def get_dependents(self, node_id: str) -> Set[str]:
        """
        Get direct dependents of a node (what depends on it).

        Args:
            node_id: Node to query

        Returns:
            Set of node IDs that directly depend on this node
        """
        if node_id not in self.nodes:
            return set()

        # Successors in NetworkX are nodes with edges coming FROM this node
        return set(self.graph.successors(node_id))

    def get_transitive_dependencies(self, node_id: str) -> Set[str]:
        """
        Get all upstream dependencies (transitive closure).

        Args:
            node_id: Node to query

        Returns:
            Set of all node IDs this node transitively depends on
        """
        if node_id not in self.nodes:
            return set()

        # nx.ancestors returns all nodes with paths TO this node
        return nx.ancestors(self.graph, node_id)

    def get_transitive_dependents(self, node_id: str) -> Set[str]:
        """
        Get all downstream nodes affected by this node (transitive closure).

        This is the key method for invalidation propagation:
        - If node X changes, all nodes in get_transitive_dependents(X) are invalidated

        Args:
            node_id: Node to query

        Returns:
            Set of all node IDs transitively affected by changes to this node
        """
        if node_id not in self.nodes:
            return set()

        # nx.descendants returns all nodes reachable FROM this node
        return nx.descendants(self.graph, node_id)

    def mark_invalid(self, node_id: str) -> None:
        """
        Mark a node as invalid (needs rebuild).

        Args:
            node_id: Node to invalidate
        """
        if node_id in self.nodes:
            self.nodes[node_id].is_valid = False
            self.valid_nodes.discard(node_id)

    def mark_valid(self, node_id: str, timestamp: Optional[float] = None) -> None:
        """
        Mark a node as valid (successfully built).

        Args:
            node_id: Node to mark valid
            timestamp: Optional build timestamp (defaults to now)
        """
        if node_id in self.nodes:
            self.nodes[node_id].is_valid = True
            self.nodes[node_id].last_built = timestamp or time.time()
            self.valid_nodes.add(node_id)

    def get_invalid_nodes(self) -> Set[str]:
        """Get all nodes marked as invalid"""
        return {nid for nid, node in self.nodes.items() if not node.is_valid}

    def get_node_count_by_type(self) -> Dict[NodeType, int]:
        """Get count of nodes by type"""
        counts = {node_type: 0 for node_type in NodeType}
        for node in self.nodes.values():
            counts[node.node_type] += 1
        return counts

    def get_max_depth(self) -> int:
        """
        Get maximum dependency depth (longest path in graph).

        Returns:
            Maximum depth, or 0 for empty graph
        """
        if not self.nodes:
            return 0

        try:
            # Find longest path using DAG longest path algorithm
            return nx.dag_longest_path_length(self.graph)
        except Exception:
            return 0

    def __len__(self) -> int:
        """Return number of nodes"""
        return len(self.nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if node exists"""
        return node_id in self.nodes

    def __repr__(self) -> str:
        """String representation"""
        return f"ModelGraph(nodes={len(self.nodes)}, edges={self.graph.number_of_edges()})"
