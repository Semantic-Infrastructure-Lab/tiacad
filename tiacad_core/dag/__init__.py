"""
Dependency graph (DAG) system for incremental rebuilds

This module provides dependency tracking, cycle detection, and incremental
rebuild capabilities for TiaCAD models.

Components:
- ModelGraph: Core dependency graph using NetworkX
- GraphBuilder: Extracts dependencies from YAML
- GraphVisualizer: Exports graphs for debugging
"""

from .model_graph import ModelGraph, NodeType, GraphNode
from .graph_builder import GraphBuilder
from .visualizer import GraphVisualizer

__all__ = [
    'ModelGraph',
    'NodeType',
    'GraphNode',
    'GraphBuilder',
    'GraphVisualizer',
]
