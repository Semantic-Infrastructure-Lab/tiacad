"""
Dependency graph (DAG) system for incremental rebuilds

This module provides dependency tracking, cycle detection, and incremental
rebuild capabilities for TiaCAD models.

Components:
- ModelGraph: Core dependency graph using NetworkX
- GraphBuilder: Extracts dependencies from YAML
- GraphVisualizer: Exports graphs for debugging
- InvalidationTracker: Computes dirty sets between graph snapshots
"""

from .model_graph import ModelGraph, NodeType, GraphNode
from .graph_builder import GraphBuilder
from .visualizer import GraphVisualizer
from .invalidation_tracker import InvalidationTracker
from .build_cache import BuildCache
from .incremental_builder import IncrementalBuilder, IncrementalState, IncrementalResult, BuildStats

__all__ = [
    'ModelGraph',
    'NodeType',
    'GraphNode',
    'GraphBuilder',
    'GraphVisualizer',
    'InvalidationTracker',
    'BuildCache',
    'IncrementalBuilder',
    'IncrementalState',
    'IncrementalResult',
    'BuildStats',
]
