"""
InvalidationTracker — computes which nodes need rebuilding between two graph snapshots.

Given an old graph and a new graph, determines the minimal dirty set: nodes whose
content changed directly, plus all transitive dependents of those changed nodes.

Usage:
    tracker = InvalidationTracker(old_graph)
    dirty = tracker.compute_dirty_set(new_graph)
    # dirty: Set[str] of node_ids that must be rebuilt
"""

from typing import Set, Optional
from .model_graph import ModelGraph


class InvalidationTracker:
    """
    Computes the dirty set between two graph snapshots.

    A node is dirty if:
    - Its hash_value changed (content changed)
    - It is new (added in new_graph, not in old_graph)
    - It was deleted from old_graph (callers must handle absent nodes)
    - Any of its (transitive) dependencies are dirty

    Deleted nodes from old_graph are returned in a separate set so callers
    can remove stale results from the build cache.
    """

    def __init__(self, old_graph: ModelGraph):
        self._old_graph = old_graph

    def compute_dirty_set(self, new_graph: ModelGraph) -> Set[str]:
        """
        Return the full set of node_ids that must be rebuilt.

        Steps:
        1. Find directly-changed nodes (hash mismatch, added)
        2. Expand via transitive dependents in new_graph
        3. Return union

        Args:
            new_graph: The graph built from the new/updated YAML

        Returns:
            Set of node_ids that need rebuilding (in new_graph)
        """
        directly_changed = self._find_directly_changed(new_graph)

        dirty: Set[str] = set(directly_changed)
        for node_id in directly_changed:
            if node_id in new_graph:
                dirty.update(new_graph.get_transitive_dependents(node_id))

        return dirty

    def compute_deleted_set(self, new_graph: ModelGraph) -> Set[str]:
        """
        Return node_ids present in old_graph but absent from new_graph.

        Useful for cache eviction — callers should remove these from BuildCache.
        """
        old_ids = set(self._old_graph.nodes.keys())
        new_ids = set(new_graph.nodes.keys())
        return old_ids - new_ids

    def _find_directly_changed(self, new_graph: ModelGraph) -> Set[str]:
        """
        Find nodes that changed directly (hash mismatch or newly added).
        """
        old_nodes = self._old_graph.nodes
        new_nodes = new_graph.nodes
        changed: Set[str] = set()

        for node_id, new_node in new_nodes.items():
            if node_id not in old_nodes:
                # New node — must build
                changed.add(node_id)
            else:
                old_node = old_nodes[node_id]
                if old_node.hash_value != new_node.hash_value:
                    # Content changed
                    changed.add(node_id)

        return changed

    def compute_full_report(self, new_graph: ModelGraph) -> dict:
        """
        Return a detailed change report for diagnostics / --show-deps output.

        Returns:
            {
                "added":    set of new node_ids,
                "deleted":  set of removed node_ids,
                "modified": set of node_ids with changed hashes,
                "dirty":    full dirty set (modified + added + transitive dependents),
                "clean":    node_ids in new_graph not in dirty set,
                "hit_rate": float (fraction of new_graph nodes that are clean),
            }
        """
        old_nodes = self._old_graph.nodes
        new_nodes = new_graph.nodes
        old_ids = set(old_nodes.keys())
        new_ids = set(new_nodes.keys())

        added = new_ids - old_ids
        deleted = old_ids - new_ids
        modified = {
            nid for nid in new_ids & old_ids
            if old_nodes[nid].hash_value != new_nodes[nid].hash_value
        }

        directly_changed = added | modified
        dirty: Set[str] = set(directly_changed)
        for node_id in directly_changed:
            dirty.update(new_graph.get_transitive_dependents(node_id))

        clean = new_ids - dirty
        hit_rate = len(clean) / len(new_ids) if new_ids else 1.0

        return {
            "added": added,
            "deleted": deleted,
            "modified": modified,
            "dirty": dirty,
            "clean": clean,
            "hit_rate": hit_rate,
        }
