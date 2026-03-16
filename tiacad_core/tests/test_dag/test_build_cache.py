"""
Tests for BuildCache — in-memory geometry cache keyed by (node_id, hash_value).
"""

import pytest
from tiacad_core.dag.build_cache import BuildCache


class TestBuildCacheBasics:

    def test_empty_cache_miss(self):
        cache = BuildCache()
        assert cache.get("operation:drill", "abc123") is None

    def test_put_and_get_hit(self):
        cache = BuildCache()
        obj = {"geometry": "some_cq_object"}
        cache.put("operation:drill", "abc123", obj)
        result = cache.get("operation:drill", "abc123")
        assert result is obj

    def test_wrong_hash_is_miss(self):
        cache = BuildCache()
        obj = {"geometry": "some_cq_object"}
        cache.put("operation:drill", "abc123", obj)
        assert cache.get("operation:drill", "differenthash") is None

    def test_wrong_node_id_is_miss(self):
        cache = BuildCache()
        obj = object()
        cache.put("operation:drill", "abc123", obj)
        assert cache.get("operation:chamfer", "abc123") is None

    def test_overwrite_entry(self):
        cache = BuildCache()
        old = {"v": 1}
        new = {"v": 2}
        cache.put("part:base", "hash1", old)
        cache.put("part:base", "hash2", new)
        assert cache.get("part:base", "hash1") is None
        assert cache.get("part:base", "hash2") is new

    def test_none_value_is_cacheable(self):
        """Cache should store None as a valid result (e.g. empty geometry)"""
        cache = BuildCache()
        cache.put("part:empty", "h1", None)
        # None stored — but get returns None on both hit AND miss
        # Use has() to distinguish
        assert cache.has("part:empty", "h1") is True
        assert cache.get("part:empty", "h1") is None


class TestBuildCacheEviction:

    def test_evict_existing(self):
        cache = BuildCache()
        cache.put("part:base", "h1", object())
        assert cache.evict("part:base") is True
        assert cache.get("part:base", "h1") is None

    def test_evict_missing_returns_false(self):
        cache = BuildCache()
        assert cache.evict("part:nonexistent") is False

    def test_evict_many(self):
        cache = BuildCache()
        cache.put("part:a", "h1", object())
        cache.put("part:b", "h2", object())
        cache.put("part:c", "h3", object())
        removed = cache.evict_many({"part:a", "part:b", "part:missing"})
        assert removed == 2
        assert "part:a" not in cache
        assert "part:b" not in cache
        assert "part:c" in cache

    def test_clear(self):
        cache = BuildCache()
        cache.put("part:a", "h1", object())
        cache.put("part:b", "h2", object())
        cache.clear()
        assert len(cache) == 0
        assert cache.get("part:a", "h1") is None


class TestBuildCacheStats:

    def test_initial_stats(self):
        cache = BuildCache()
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 1.0

    def test_hit_counted(self):
        cache = BuildCache()
        cache.put("op:x", "h", object())
        cache.get("op:x", "h")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 1.0

    def test_miss_counted(self):
        cache = BuildCache()
        cache.get("op:x", "h")
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.0

    def test_mixed_hit_rate(self):
        cache = BuildCache()
        cache.put("op:a", "h1", object())
        cache.get("op:a", "h1")   # hit
        cache.get("op:a", "h1")   # hit
        cache.get("op:b", "h2")   # miss
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert abs(stats["hit_rate"] - 2/3) < 1e-9

    def test_stats_reset_on_clear(self):
        cache = BuildCache()
        cache.put("op:a", "h1", object())
        cache.get("op:a", "h1")
        cache.clear()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_size_reflects_entries(self):
        cache = BuildCache()
        assert len(cache) == 0
        cache.put("a:x", "h1", object())
        cache.put("b:y", "h2", object())
        assert len(cache) == 2
        cache.evict("a:x")
        assert len(cache) == 1


class TestBuildCacheContains:

    def test_contains_node_id(self):
        cache = BuildCache()
        cache.put("part:base", "h1", object())
        assert "part:base" in cache
        assert "part:other" not in cache

    def test_has_exact_key(self):
        cache = BuildCache()
        cache.put("part:base", "h1", object())
        assert cache.has("part:base", "h1") is True
        assert cache.has("part:base", "h2") is False
        assert cache.has("part:other", "h1") is False
