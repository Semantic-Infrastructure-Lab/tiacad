"""
Dependency graph visualization and statistics

Exports graphs to Graphviz DOT format for debugging and provides
statistics about graph structure.

Author: TIA
Version: 3.2.0
"""

from typing import Optional, Set, TextIO
import sys

from .model_graph import ModelGraph, NodeType


class GraphVisualizer:
    """
    Export dependency graphs for debugging.

    Provides:
    - DOT format export (for Graphviz visualization)
    - Graph statistics (node counts, edge counts, depth)
    - Text-based summaries
    """

    # Color scheme for node types (Graphviz colors)
    NODE_COLORS = {
        NodeType.PARAMETER: 'lightblue',
        NodeType.PART: 'lightgreen',
        NodeType.OPERATION: 'lightyellow',
        NodeType.REFERENCE: 'lightpink',
        NodeType.SKETCH: 'lavender',
    }

    @staticmethod
    def to_dot(graph: ModelGraph,
               output_path: str,
               filter_types: Optional[Set[NodeType]] = None,
               highlight_invalid: bool = False) -> None:
        """
        Export graph to Graphviz DOT format.

        Generates a visual representation of the dependency graph that can be
        rendered with Graphviz:
            dot -Tpng graph.dot -o graph.png

        Args:
            graph: ModelGraph to export
            output_path: Path to write DOT file
            filter_types: Optional set of node types to include (filters others)
            highlight_invalid: If True, highlight invalid nodes in red

        Example:
            >>> GraphVisualizer.to_dot(graph, "deps.dot")
            >>> # Then run: dot -Tpng deps.dot -o deps.png
        """
        # Determine which nodes to include
        nodes_to_include = set(graph.graph.nodes())
        if filter_types:
            nodes_to_include = {
                nid for nid, node in graph.nodes.items()
                if node.node_type in filter_types
            }

        # Create subgraph if filtering
        if filter_types:
            subgraph = graph.graph.subgraph(nodes_to_include)
        else:
            subgraph = graph.graph

        # Write DOT file
        with open(output_path, 'w') as f:
            f.write('digraph TiaCADDependencies {\n')
            f.write('  rankdir=TB;\n')  # Top to bottom layout
            f.write('  node [shape=box, style=filled];\n')
            f.write('\n')

            # Write nodes with visual attributes
            for node_id in subgraph.nodes():
                if node_id not in graph.nodes:
                    continue

                node = graph.nodes[node_id]

                # Determine fill color
                if highlight_invalid and not node.is_valid:
                    fillcolor = 'lightcoral'
                else:
                    fillcolor = GraphVisualizer.NODE_COLORS.get(node.node_type, 'white')

                # Node label (show name only, not full ID)
                label = node.name

                # Add pattern indicator
                if node.is_pattern:
                    label = f"{label}\\n[pattern]"

                f.write(f'  "{node_id}" [label="{label}", fillcolor={fillcolor}];\n')

            f.write('\n')

            # Write edges
            for src, dst in subgraph.edges():
                f.write(f'  "{src}" -> "{dst}";\n')

            f.write('}\n')

    @staticmethod
    def show_stats(graph: ModelGraph, output: Optional[TextIO] = None) -> None:
        """
        Print graph statistics to console or file.

        Args:
            graph: ModelGraph to analyze
            output: Output stream (defaults to stdout)

        Example:
            >>> GraphVisualizer.show_stats(graph)
            📊 Dependency Graph
              Nodes: 42
                Parameters: 10
                Parts: 8
                Operations: 15
                ...
              Edges: 67
              Max Depth: 5
              Invalid: 0
        """
        if output is None:
            output = sys.stdout

        # Count nodes by type
        type_counts = graph.get_node_count_by_type()

        # Calculate statistics
        total_nodes = len(graph)
        total_edges = graph.graph.number_of_edges()
        max_depth = graph.get_max_depth()
        invalid_count = len(graph.get_invalid_nodes())

        # Print formatted output
        output.write("📊 Dependency Graph\n")
        output.write(f"\n  Nodes: {total_nodes}\n")

        for node_type in NodeType:
            count = type_counts[node_type]
            if count > 0:
                output.write(f"    {node_type.value.title()}: {count}\n")

        output.write(f"\n  Edges: {total_edges}\n")
        output.write(f"  Max Depth: {max_depth}\n")

        if invalid_count > 0:
            output.write(f"  Invalid: {invalid_count}\n")

        output.write("\n")

    @staticmethod
    def show_node_details(graph: ModelGraph,
                          node_id: str,
                          output: Optional[TextIO] = None) -> None:
        """
        Print detailed information about a specific node.

        Args:
            graph: ModelGraph to query
            node_id: Node to inspect
            output: Output stream (defaults to stdout)

        Example:
            >>> GraphVisualizer.show_node_details(graph, "parameter:width")
            📦 Node: parameter:width
              Type: parameter
              Valid: ✓
              Dependencies: (none)
              Dependents: part:base, part:top
        """
        if output is None:
            output = sys.stdout

        if node_id not in graph.nodes:
            output.write(f"❌ Node '{node_id}' not found\n")
            return

        node = graph.nodes[node_id]

        output.write(f"📦 Node: {node_id}\n")
        output.write(f"  Name: {node.name}\n")
        output.write(f"  Type: {node.node_type.value}\n")
        output.write(f"  Valid: {'✓' if node.is_valid else '✗'}\n")

        if node.is_pattern:
            output.write("  Pattern: yes\n")

        # Show dependencies
        deps = graph.get_dependencies(node_id)
        if deps:
            output.write(f"  Dependencies: {', '.join(sorted(deps))}\n")
        else:
            output.write("  Dependencies: (none)\n")

        # Show dependents
        dependents = graph.get_dependents(node_id)
        if dependents:
            output.write(f"  Dependents: {', '.join(sorted(dependents))}\n")
        else:
            output.write("  Dependents: (none)\n")

        # Show transitive counts
        trans_deps = graph.get_transitive_dependencies(node_id)
        trans_dependents = graph.get_transitive_dependents(node_id)

        if trans_deps:
            output.write(f"  Transitive Dependencies: {len(trans_deps)}\n")
        if trans_dependents:
            output.write(f"  Transitive Dependents: {len(trans_dependents)}\n")

        output.write("\n")

    @staticmethod
    def list_roots(graph: ModelGraph, output: Optional[TextIO] = None) -> None:
        """
        List root nodes (nodes with no dependencies).

        Args:
            graph: ModelGraph to analyze
            output: Output stream (defaults to stdout)
        """
        if output is None:
            output = sys.stdout

        roots = [nid for nid in graph.nodes if not graph.get_dependencies(nid)]

        if not roots:
            output.write("No root nodes found\n")
            return

        output.write(f"🌳 Root Nodes ({len(roots)}):\n")
        for root_id in sorted(roots):
            node = graph.nodes[root_id]
            output.write(f"  {root_id} ({node.node_type.value})\n")

        output.write("\n")

    @staticmethod
    def list_leaves(graph: ModelGraph, output: Optional[TextIO] = None) -> None:
        """
        List leaf nodes (nodes with no dependents).

        Args:
            graph: ModelGraph to analyze
            output: Output stream (defaults to stdout)
        """
        if output is None:
            output = sys.stdout

        leaves = [nid for nid in graph.nodes if not graph.get_dependents(nid)]

        if not leaves:
            output.write("No leaf nodes found\n")
            return

        output.write(f"🍃 Leaf Nodes ({len(leaves)}):\n")
        for leaf_id in sorted(leaves):
            node = graph.nodes[leaf_id]
            output.write(f"  {leaf_id} ({node.node_type.value})\n")

        output.write("\n")
