"""
Tests for ModelGraph - Core dependency graph data structure

Author: TIA
Version: 3.2.0
"""

import pytest
from tiacad_core.dag.model_graph import ModelGraph, GraphNode, NodeType


class TestGraphNode:
    """Tests for GraphNode dataclass"""

    def test_create_parameter_node(self):
        """Test creating a parameter node"""
        node = GraphNode(
            node_id="parameter:width",
            node_type=NodeType.PARAMETER,
            name="width",
            spec={'value': 100}
        )

        assert node.node_id == "parameter:width"
        assert node.node_type == NodeType.PARAMETER
        assert node.name == "width"
        assert node.spec == {'value': 100}
        assert node.is_valid
        assert not node.is_pattern

    def test_node_id_validation(self):
        """Test node_id format validation"""
        # Valid format
        node = GraphNode(
            node_id="part:base",
            node_type=NodeType.PART,
            name="base",
            spec={}
        )
        assert node.node_id == "part:base"

        # Invalid format - missing colon
        with pytest.raises(ValueError, match="must be in format 'type:name'"):
            GraphNode(
                node_id="invalidid",
                node_type=NodeType.PART,
                name="test",
                spec={}
            )

        # Invalid format - wrong prefix
        with pytest.raises(ValueError, match="doesn't match type"):
            GraphNode(
                node_id="wrong:test",
                node_type=NodeType.PARAMETER,
                name="test",
                spec={}
            )


class TestModelGraph:
    """Tests for ModelGraph class"""

    def test_empty_graph(self):
        """Test creating an empty graph"""
        graph = ModelGraph()

        assert len(graph) == 0
        assert graph.graph.number_of_edges() == 0
        assert len(graph.valid_nodes) == 0

    def test_add_node(self):
        """Test adding nodes to graph"""
        graph = ModelGraph()

        node1 = GraphNode("parameter:width", NodeType.PARAMETER, "width", {'value': 100})
        node2 = GraphNode("part:base", NodeType.PART, "base", {})

        graph.add_node(node1)
        graph.add_node(node2)

        assert len(graph) == 2
        assert "parameter:width" in graph
        assert "part:base" in graph
        assert len(graph.valid_nodes) == 2

    def test_duplicate_node_error(self):
        """Test that adding duplicate node raises error"""
        graph = ModelGraph()

        node1 = GraphNode("parameter:width", NodeType.PARAMETER, "width", {'value': 100})
        graph.add_node(node1)

        # Try to add again
        node2 = GraphNode("parameter:width", NodeType.PARAMETER, "width", {'value': 200})
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(node2)

    def test_add_dependency(self):
        """Test adding dependency edges"""
        graph = ModelGraph()

        # Add nodes
        param_node = GraphNode("parameter:width", NodeType.PARAMETER, "width", {})
        part_node = GraphNode("part:base", NodeType.PART, "base", {})

        graph.add_node(param_node)
        graph.add_node(part_node)

        # Add dependency: part uses width
        graph.add_dependency("part:base", "parameter:width")

        assert graph.graph.number_of_edges() == 1
        assert graph.graph.has_edge("parameter:width", "part:base")

    def test_dependency_nonexistent_node(self):
        """Test that adding dependency with nonexistent node raises error"""
        graph = ModelGraph()

        param_node = GraphNode("parameter:width", NodeType.PARAMETER, "width", {})
        graph.add_node(param_node)

        # Try to add dependency to nonexistent node
        with pytest.raises(ValueError, match="not found"):
            graph.add_dependency("part:nonexistent", "parameter:width")

        with pytest.raises(ValueError, match="not found"):
            graph.add_dependency("parameter:width", "parameter:nonexistent")

    def test_detect_cycles_none(self):
        """Test cycle detection on valid DAG"""
        graph = ModelGraph()

        # Create simple chain: param1 -> param2 -> part
        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("parameter:p2", "parameter:p1")
        graph.add_dependency("part:base", "parameter:p2")

        cycles = graph.detect_cycles()
        assert cycles == []

    def test_detect_cycles_simple(self):
        """Test cycle detection on graph with cycle"""
        graph = ModelGraph()

        # Create cycle: p1 -> p2 -> p1
        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))

        graph.add_dependency("parameter:p2", "parameter:p1")
        graph.add_dependency("parameter:p1", "parameter:p2")

        cycles = graph.detect_cycles()
        assert len(cycles) > 0
        assert len(cycles[0]) == 2  # Cycle involves 2 nodes

    def test_topological_sort(self):
        """Test topological sorting"""
        graph = ModelGraph()

        # Create: width -> height -> part
        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("parameter:height", NodeType.PARAMETER, "height", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("parameter:height", "parameter:width")
        graph.add_dependency("part:base", "parameter:height")

        order = graph.topological_sort()

        # Width should come before height, height before part
        width_idx = order.index("parameter:width")
        height_idx = order.index("parameter:height")
        part_idx = order.index("part:base")

        assert width_idx < height_idx < part_idx

    def test_get_dependencies(self):
        """Test getting direct dependencies"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:w", NodeType.PARAMETER, "w", {}))
        graph.add_node(GraphNode("parameter:h", NodeType.PARAMETER, "h", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("part:base", "parameter:w")
        graph.add_dependency("part:base", "parameter:h")

        deps = graph.get_dependencies("part:base")
        assert deps == {"parameter:w", "parameter:h"}

    def test_get_dependents(self):
        """Test getting direct dependents"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("part:top", NodeType.PART, "top", {}))

        graph.add_dependency("part:base", "parameter:width")
        graph.add_dependency("part:top", "parameter:width")

        dependents = graph.get_dependents("parameter:width")
        assert dependents == {"part:base", "part:top"}

    def test_transitive_dependencies(self):
        """Test transitive closure of dependencies"""
        graph = ModelGraph()

        # Chain: p1 -> p2 -> p3 -> part
        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))
        graph.add_node(GraphNode("parameter:p3", NodeType.PARAMETER, "p3", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("parameter:p2", "parameter:p1")
        graph.add_dependency("parameter:p3", "parameter:p2")
        graph.add_dependency("part:base", "parameter:p3")

        # part depends transitively on p3, p2, p1
        trans_deps = graph.get_transitive_dependencies("part:base")
        assert trans_deps == {"parameter:p1", "parameter:p2", "parameter:p3"}

    def test_transitive_dependents(self):
        """Test transitive closure of dependents (key for invalidation)"""
        graph = ModelGraph()

        # Chain: p1 -> p2 -> p3 -> part
        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))
        graph.add_node(GraphNode("parameter:p3", NodeType.PARAMETER, "p3", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("parameter:p2", "parameter:p1")
        graph.add_dependency("parameter:p3", "parameter:p2")
        graph.add_dependency("part:base", "parameter:p3")

        # If p1 changes, all downstream nodes are affected
        trans_dependents = graph.get_transitive_dependents("parameter:p1")
        assert trans_dependents == {"parameter:p2", "parameter:p3", "part:base"}

    def test_mark_invalid(self):
        """Test marking nodes invalid"""
        graph = ModelGraph()

        node = GraphNode("parameter:width", NodeType.PARAMETER, "width", {})
        graph.add_node(node)

        assert node.is_valid
        assert "parameter:width" in graph.valid_nodes

        graph.mark_invalid("parameter:width")

        assert not graph.nodes["parameter:width"].is_valid
        assert "parameter:width" not in graph.valid_nodes

    def test_mark_valid(self):
        """Test marking nodes valid"""
        graph = ModelGraph()

        node = GraphNode("parameter:width", NodeType.PARAMETER, "width", {}, is_valid=False)
        graph.add_node(node)

        assert not node.is_valid
        assert "parameter:width" not in graph.valid_nodes

        graph.mark_valid("parameter:width")

        assert graph.nodes["parameter:width"].is_valid
        assert "parameter:width" in graph.valid_nodes
        assert graph.nodes["parameter:width"].last_built is not None

    def test_get_invalid_nodes(self):
        """Test getting all invalid nodes"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}, is_valid=False))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}, is_valid=False))

        invalid = graph.get_invalid_nodes()
        assert invalid == {"parameter:p2", "part:base"}

    def test_get_node_count_by_type(self):
        """Test counting nodes by type"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("operation:final", NodeType.OPERATION, "final", {}))

        counts = graph.get_node_count_by_type()

        assert counts[NodeType.PARAMETER] == 2
        assert counts[NodeType.PART] == 1
        assert counts[NodeType.OPERATION] == 1
        assert counts[NodeType.REFERENCE] == 0
        assert counts[NodeType.SKETCH] == 0

    def test_get_max_depth(self):
        """Test calculating maximum dependency depth"""
        graph = ModelGraph()

        # Chain of depth 3: p1 -> p2 -> p3 -> part
        graph.add_node(GraphNode("parameter:p1", NodeType.PARAMETER, "p1", {}))
        graph.add_node(GraphNode("parameter:p2", NodeType.PARAMETER, "p2", {}))
        graph.add_node(GraphNode("parameter:p3", NodeType.PARAMETER, "p3", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))

        graph.add_dependency("parameter:p2", "parameter:p1")
        graph.add_dependency("parameter:p3", "parameter:p2")
        graph.add_dependency("part:base", "parameter:p3")

        depth = graph.get_max_depth()
        assert depth == 3

    def test_repr(self):
        """Test string representation"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_dependency("part:base", "parameter:width")

        repr_str = repr(graph)
        assert "ModelGraph" in repr_str
        assert "nodes=2" in repr_str
        assert "edges=1" in repr_str
