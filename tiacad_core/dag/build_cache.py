"""
BuildCache — in-memory cache of built geometry, keyed by (node_id, content_hash).

CadQuery geometry objects are not picklable, so this is intentionally in-memory only.
The cache lives for the lifetime of a watch session. On cold start, everything rebuilds.

Future v2: persistent cache via STEP export/import (serialize geometry to disk).

Usage:
    cache = BuildCache()
    cache.put("operation:drill", "abc123", part_object)
    part = cache.get("operation:drill", "abc123")  # → Part or None
    cache.evict("operation:drill")
    cache.evict_many({"operation:drill", "part:base"})
    stats = cache.get_stats()
"""

from typing import Any, Optional, Set, Dict, Tuple


class BuildCache:
    """
    In-memory LRU-free cache keyed by (node_id, content_hash).

    Two separate keys are used intentionally:
    - node_id: identifies what was built ("operation:chamfer")
    - content_hash: the exact spec hash at build time

    If either changes, cache.get() returns None (miss).
    This means stale results are never returned — correctness over efficiency.
    """

    def __init__(self):
        # Maps node_id → (hash_value, built_object)
        self._store: Dict[str, Tuple[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, node_id: str, hash_value: str) -> Optional[Any]:
        """
        Return cached object if node_id+hash_value matches, else None.

        Args:
            node_id: Node identifier e.g. "operation:chamfer"
            hash_value: Content hash that was current when the object was built

        Returns:
            Cached object, or None on miss
        """
        entry = self._store.get(node_id)
        if entry is None:
            self._misses += 1
            return None
        stored_hash, obj = entry
        if stored_hash != hash_value:
            self._misses += 1
            return None
        self._hits += 1
        return obj

    def put(self, node_id: str, hash_value: str, obj: Any) -> None:
        """
        Store a built object.

        Args:
            node_id: Node identifier e.g. "operation:chamfer"
            hash_value: Content hash at build time
            obj: The built geometry / value to cache
        """
        self._store[node_id] = (hash_value, obj)

    def evict(self, node_id: str) -> bool:
        """
        Remove a single entry. Returns True if it existed.
        """
        if node_id in self._store:
            del self._store[node_id]
            return True
        return False

    def evict_many(self, node_ids: Set[str]) -> int:
        """
        Remove multiple entries. Returns count of entries actually removed.
        """
        removed = 0
        for node_id in node_ids:
            if self.evict(node_id):
                removed += 1
        return removed

    def has(self, node_id: str, hash_value: str) -> bool:
        """Return True if the exact (node_id, hash_value) pair is cached."""
        entry = self._store.get(node_id)
        return entry is not None and entry[0] == hash_value

    def clear(self) -> None:
        """Evict all entries and reset stats."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict:
        """
        Return cache performance stats.

        Returns:
            {
                "size": int,         # entries currently stored
                "hits": int,
                "misses": int,
                "hit_rate": float,   # hits / (hits + misses), or 1.0 if no lookups
            }
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 1.0
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._store
