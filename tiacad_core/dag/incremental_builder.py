"""
IncrementalBuilder — orchestrates incremental model rebuilds using the DAG.

Given an old IncrementalState (graph + cache) and new YAML data, rebuilds only
the nodes whose content changed or that depend on changed nodes.

Algorithm:
1. Build new ModelGraph from yaml_data
2. If no old_state → full build, cache everything
3. Compute dirty set via InvalidationTracker
4. Build parts: dirty → build fresh; clean → restore from cache
5. Execute operations in topological order: dirty → execute; clean → restore
6. Return IncrementalResult with new state (graph + cache)

Usage:
    # First build (no state)
    builder = IncrementalBuilder()
    result = builder.build(yaml_data, parts_spec, operations_spec,
                           registry, parts_builder, ops_builder)

    # Subsequent builds (incremental)
    result2 = builder.build(new_yaml_data, new_parts_spec, new_ops_spec,
                            new_registry, new_parts_builder, new_ops_builder,
                            old_state=result.state)

    # result.stats shows how many nodes were rebuilt vs cached
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set

from .model_graph import ModelGraph, NodeType
from .graph_builder import GraphBuilder
from .build_cache import BuildCache
from .invalidation_tracker import InvalidationTracker
from ..part import Part, PartRegistry

logger = logging.getLogger(__name__)


@dataclass
class IncrementalState:
    """
    Preserved between incremental rebuilds.

    Callers hold this and pass it back on the next build call.
    Contains the graph snapshot and geometry cache from the last successful build.
    """
    graph: ModelGraph
    cache: BuildCache


@dataclass
class BuildStats:
    """Per-build statistics for diagnostics."""
    rebuilt: int = 0
    cached: int = 0
    total_ms: float = 0.0

    @property
    def total(self) -> int:
        return self.rebuilt + self.cached

    @property
    def cache_hit_rate(self) -> float:
        return self.cached / self.total if self.total > 0 else 1.0

    def __repr__(self) -> str:
        return (
            f"BuildStats(rebuilt={self.rebuilt}, cached={self.cached}, "
            f"hit_rate={self.cache_hit_rate:.1%}, total_ms={self.total_ms:.1f})"
        )


@dataclass
class IncrementalResult:
    """Result of a single incremental (or full) build."""
    registry: PartRegistry
    graph: ModelGraph
    state: IncrementalState
    stats: BuildStats


class IncrementalBuilderError(Exception):
    pass


class IncrementalBuilder:
    """
    Orchestrates incremental builds using the DAG, InvalidationTracker, and BuildCache.

    This class is stateless — state is held in IncrementalState and passed by the caller.
    This makes it safe to reuse across sessions and easy to test.
    """

    def build(
        self,
        yaml_data: Dict[str, Any],
        parts_spec: Dict[str, Any],
        operations_spec: Dict[str, Any],
        registry: PartRegistry,
        parts_builder,
        ops_builder,
        old_state: Optional[IncrementalState] = None,
    ) -> IncrementalResult:
        """
        Build a TiaCAD model, reusing cached geometry where possible.

        Args:
            yaml_data: Full YAML data dict (for graph building)
            parts_spec: The 'parts' section of the YAML
            operations_spec: The 'operations' section of the YAML
            registry: Fresh PartRegistry to populate (shared with ops_builder)
            parts_builder: PartsBuilder instance (already configured with param_resolver)
            ops_builder: OperationsBuilder instance (initialized with the same registry)
            old_state: State from prior build, or None for full build

        Returns:
            IncrementalResult with populated registry, new graph, new state, and stats
        """
        t0 = time.monotonic()
        stats = BuildStats()

        # Step 1: Build new graph
        new_graph = GraphBuilder().build_graph(yaml_data)

        # Step 2: Compute dirty set
        if old_state is None:
            # Full build — everything is dirty
            dirty: Set[str] = set(new_graph.nodes.keys())
            cache = BuildCache()
        else:
            tracker = InvalidationTracker(old_state.graph)
            dirty = tracker.compute_dirty_set(new_graph)
            deleted = tracker.compute_deleted_set(new_graph)
            cache = old_state.cache
            cache.evict_many(deleted)
            logger.info(
                f"Incremental: {len(dirty)} dirty, {len(new_graph.nodes) - len(dirty)} cached, "
                f"{len(deleted)} deleted"
            )

        # Step 3: Build parts (dirty → build; clean → restore from cache)
        self._build_parts(
            parts_spec=parts_spec,
            new_graph=new_graph,
            dirty=dirty,
            cache=cache,
            registry=registry,
            parts_builder=parts_builder,
            stats=stats,
        )

        # Step 4: Execute operations in topological order
        if operations_spec:
            self._execute_operations(
                operations_spec=operations_spec,
                new_graph=new_graph,
                dirty=dirty,
                cache=cache,
                registry=registry,
                ops_builder=ops_builder,
                stats=stats,
            )

        stats.total_ms = (time.monotonic() - t0) * 1000
        new_state = IncrementalState(graph=new_graph, cache=cache)

        logger.info(f"Build complete: {stats}")
        return IncrementalResult(
            registry=registry,
            graph=new_graph,
            state=new_state,
            stats=stats,
        )

    def _build_parts(
        self,
        parts_spec: Dict[str, Any],
        new_graph: ModelGraph,
        dirty: Set[str],
        cache: BuildCache,
        registry: PartRegistry,
        parts_builder,
        stats: BuildStats,
    ) -> None:
        """Build or restore all parts."""
        for part_name, spec in parts_spec.items():
            node_id = f"part:{part_name}"
            hash_value = new_graph.nodes[node_id].hash_value if node_id in new_graph else None

            if node_id in dirty or hash_value is None:
                # Build fresh
                part = parts_builder.build_part(part_name, spec)
                registry.add(part)
                if hash_value:
                    cache.put(node_id, hash_value, part)
                stats.rebuilt += 1
                logger.debug(f"Built (fresh): {node_id}")
            else:
                # Restore from cache
                cached = cache.get(node_id, hash_value)
                if cached is not None:
                    registry.add(cached)
                    stats.cached += 1
                    logger.debug(f"Restored (cached): {node_id}")
                else:
                    # Cache miss despite being clean — rebuild
                    part = parts_builder.build_part(part_name, spec)
                    registry.add(part)
                    cache.put(node_id, hash_value, part)
                    stats.rebuilt += 1
                    logger.debug(f"Built (cache miss): {node_id}")

    def _execute_operations(
        self,
        operations_spec: Dict[str, Any],
        new_graph: ModelGraph,
        dirty: Set[str],
        cache: BuildCache,
        registry: PartRegistry,
        ops_builder,
        stats: BuildStats,
    ) -> None:
        """
        Execute or restore operations in topological order.

        Topological order ensures operation inputs are in the registry
        before downstream operations run.
        """
        # Get all operation node IDs that exist in the graph
        op_node_ids = {
            f"operation:{name}"
            for name in operations_spec
            if f"operation:{name}" in new_graph
        }

        # Sort in topological order (dependencies before dependents)
        try:
            topo_order = new_graph.topological_sort(op_node_ids)
        except Exception:
            # Fallback: use dict order if topo sort fails
            topo_order = [f"operation:{name}" for name in operations_spec]

        for node_id in topo_order:
            op_name = node_id.split(':', 1)[1]
            if op_name not in operations_spec:
                continue

            spec = operations_spec[op_name]
            hash_value = new_graph.nodes[node_id].hash_value if node_id in new_graph else None

            if node_id in dirty or hash_value is None:
                # Execute fresh
                ops_builder.execute_operation(op_name, spec)
                part = registry.get(op_name)
                if hash_value:
                    cache.put(node_id, hash_value, part)
                stats.rebuilt += 1
                logger.debug(f"Executed (fresh): {node_id}")
            else:
                # Restore from cache
                cached = cache.get(node_id, hash_value)
                if cached is not None:
                    registry.add(cached)
                    stats.cached += 1
                    logger.debug(f"Restored (cached): {node_id}")
                else:
                    # Cache miss — execute fresh
                    ops_builder.execute_operation(op_name, spec)
                    part = registry.get(op_name)
                    cache.put(node_id, hash_value, part)
                    stats.rebuilt += 1
                    logger.debug(f"Executed (cache miss): {node_id}")
