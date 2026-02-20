"""
Tests for GraphVisualizer - Graph export and statistics

Author: TIA
Version: 3.2.0
"""

import pytest
import tempfile
from pathlib import Path
from io import StringIO

from tiacad_core.dag.model_graph import ModelGraph, GraphNode, NodeType
from tiacad_core.dag.visualizer import GraphVisualizer


class TestGraphVisualizer:
    """Tests for GraphVisualizer class"""

    def test_dot_export_simple(self):
        """Test exporting simple graph to DOT format"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_dependency("part:base", "parameter:width")

        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_path = f.name

        try:
            GraphVisualizer.to_dot(graph, dot_path)

            # Read and verify content
            with open(dot_path, 'r') as f:
                content = f.read()

            assert 'digraph TiaCADDependencies' in content
            assert 'parameter:width' in content
            assert 'part:base' in content
            assert '->' in content  # Has edges
            assert 'lightblue' in content  # Parameter color
            assert 'lightgreen' in content  # Part color

        finally:
            Path(dot_path).unlink(missing_ok=True)

    def test_dot_export_with_filter(self):
        """Test filtering node types in DOT export"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("operation:final", NodeType.OPERATION, "final", {}))
        graph.add_dependency("part:base", "parameter:width")
        graph.add_dependency("operation:final", "part:base")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_path = f.name

        try:
            # Export only parameters and parts (no operations)
            GraphVisualizer.to_dot(
                graph,
                dot_path,
                filter_types={NodeType.PARAMETER, NodeType.PART}
            )

            with open(dot_path, 'r') as f:
                content = f.read()

            assert 'parameter:width' in content
            assert 'part:base' in content
            assert 'operation:final' not in content

        finally:
            Path(dot_path).unlink(missing_ok=True)

    def test_dot_export_with_invalid_highlight(self):
        """Test highlighting invalid nodes in DOT export"""
        graph = ModelGraph()

        # Add valid and invalid nodes
        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}, is_valid=True))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}, is_valid=False))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_path = f.name

        try:
            GraphVisualizer.to_dot(graph, dot_path, highlight_invalid=True)

            with open(dot_path, 'r') as f:
                content = f.read()

            # Invalid node should be highlighted in red
            assert 'lightcoral' in content

        finally:
            Path(dot_path).unlink(missing_ok=True)

    def test_dot_export_pattern_indicator(self):
        """Test that pattern operations show [pattern] label"""
        graph = ModelGraph()

        graph.add_node(GraphNode(
            "operation:repeated",
            NodeType.OPERATION,
            "repeated",
            {},
            is_pattern=True
        ))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_path = f.name

        try:
            GraphVisualizer.to_dot(graph, dot_path)

            with open(dot_path, 'r') as f:
                content = f.read()

            # Should show pattern indicator in label
            assert '[pattern]' in content or 'pattern' in content.lower()

        finally:
            Path(dot_path).unlink(missing_ok=True)

    def test_show_stats(self):
        """Test displaying graph statistics"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("parameter:height", NodeType.PARAMETER, "height", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("operation:final", NodeType.OPERATION, "final", {}))
        graph.add_dependency("part:base", "parameter:width")
        graph.add_dependency("operation:final", "part:base")

        # Capture output
        output = StringIO()
        GraphVisualizer.show_stats(graph, output=output)

        stats_text = output.getvalue()

        # Verify stats are present
        assert 'Dependency Graph' in stats_text
        assert 'Nodes: 4' in stats_text
        assert 'Parameter: 2' in stats_text  # Title-cased from node type
        assert 'Part: 1' in stats_text
        assert 'Operation: 1' in stats_text
        assert 'Edges: 2' in stats_text
        assert 'Max Depth:' in stats_text

    def test_show_stats_with_invalid(self):
        """Test stats showing invalid node count"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}, is_valid=True))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}, is_valid=False))

        output = StringIO()
        GraphVisualizer.show_stats(graph, output=output)

        stats_text = output.getvalue()

        assert 'Invalid: 1' in stats_text

    def test_show_node_details(self):
        """Test showing detailed node information"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("part:top", NodeType.PART, "top", {}))
        graph.add_dependency("part:base", "parameter:width")
        graph.add_dependency("part:top", "parameter:width")

        output = StringIO()
        GraphVisualizer.show_node_details(graph, "parameter:width", output=output)

        details = output.getvalue()

        assert 'parameter:width' in details
        assert 'Type: parameter' in details
        assert 'Dependents:' in details
        assert 'part:base' in details or 'part:top' in details

    def test_show_node_details_not_found(self):
        """Test showing details for nonexistent node"""
        graph = ModelGraph()

        output = StringIO()
        GraphVisualizer.show_node_details(graph, "parameter:nonexistent", output=output)

        details = output.getvalue()
        assert 'not found' in details

    def test_list_roots(self):
        """Test listing root nodes (no dependencies)"""
        graph = ModelGraph()

        # width has no dependencies (root)
        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        # height has no dependencies (root)
        graph.add_node(GraphNode("parameter:height", NodeType.PARAMETER, "height", {}))
        # base depends on width (not a root)
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_dependency("part:base", "parameter:width")

        output = StringIO()
        GraphVisualizer.list_roots(graph, output=output)

        roots_text = output.getvalue()

        assert 'Root Nodes' in roots_text
        assert 'parameter:width' in roots_text
        assert 'parameter:height' in roots_text
        assert 'part:base' not in roots_text  # Not a root

    def test_list_leaves(self):
        """Test listing leaf nodes (no dependents)"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:width", NodeType.PARAMETER, "width", {}))
        graph.add_node(GraphNode("part:base", NodeType.PART, "base", {}))
        graph.add_node(GraphNode("operation:final", NodeType.OPERATION, "final", {}))
        graph.add_dependency("part:base", "parameter:width")
        graph.add_dependency("operation:final", "part:base")

        output = StringIO()
        GraphVisualizer.list_leaves(graph, output=output)

        leaves_text = output.getvalue()

        assert 'Leaf Nodes' in leaves_text
        assert 'operation:final' in leaves_text  # Only leaf
        assert 'parameter:width' not in leaves_text  # Has dependents
        assert 'part:base' not in leaves_text  # Has dependents

    def test_empty_graph_stats(self):
        """Test stats on empty graph"""
        graph = ModelGraph()

        output = StringIO()
        GraphVisualizer.show_stats(graph, output=output)

        stats_text = output.getvalue()
        assert 'Nodes: 0' in stats_text
        assert 'Edges: 0' in stats_text

    def test_multiple_node_types_colors(self):
        """Test that all node types get proper colors in DOT"""
        graph = ModelGraph()

        graph.add_node(GraphNode("parameter:p", NodeType.PARAMETER, "p", {}))
        graph.add_node(GraphNode("sketch:s", NodeType.SKETCH, "s", {}))
        graph.add_node(GraphNode("part:pt", NodeType.PART, "pt", {}))
        graph.add_node(GraphNode("operation:op", NodeType.OPERATION, "op", {}))
        graph.add_node(GraphNode("reference:ref", NodeType.REFERENCE, "ref", {}))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_path = f.name

        try:
            GraphVisualizer.to_dot(graph, dot_path)

            with open(dot_path, 'r') as f:
                content = f.read()

            # Check that each color appears
            assert 'lightblue' in content  # parameter
            assert 'lightgreen' in content  # part
            assert 'lightyellow' in content  # operation
            assert 'lightpink' in content  # reference
            assert 'lavender' in content  # sketch

        finally:
            Path(dot_path).unlink(missing_ok=True)
