"""
Tests for tiacad_core/watcher.py — Phase 4: Watch Mode.

Two categories:
  - Unit tests (mocked _rebuild): fast, test event-loop logic only.
  - Integration tests (real builds): verify end-to-end watcher behaviour
    with a real simple YAML file.
"""

import threading
import time
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from tiacad_core.watcher import FileWatcher, WatchBuildResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SIMPLE_YAML = """\
metadata:
  name: watcher_test
parts:
  base:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 5
"""

_TWO_PART_YAML = """\
metadata:
  name: watcher_two_parts
parts:
  base:
    primitive: box
    parameters:
      width: 20
      height: 20
      depth: 5
  peg:
    primitive: cylinder
    parameters:
      radius: 2
      height: 8
"""


def _collect_results(watcher: FileWatcher, stop_after: int, timeout: float = 30) -> List[WatchBuildResult]:
    """Drive watcher in a background thread; return results list after stop_after events."""
    results: List[WatchBuildResult] = []
    done = threading.Event()
    original_on_rebuild = watcher.on_rebuild

    def collecting_on_rebuild(r: WatchBuildResult) -> None:
        original_on_rebuild(r)
        results.append(r)
        if len(results) >= stop_after:
            done.set()
            watcher.stop()

    watcher.on_rebuild = collecting_on_rebuild

    t = threading.Thread(target=watcher.start, daemon=True)
    t.start()
    done.wait(timeout=timeout)
    watcher.stop()
    t.join(timeout=5)
    return results


# ---------------------------------------------------------------------------
# WatchBuildResult
# ---------------------------------------------------------------------------

class TestWatchBuildResult:
    def test_ok_when_no_error(self):
        r = WatchBuildResult(rebuild_ms=100, rebuilt=2)
        assert r.ok is True

    def test_not_ok_when_error(self):
        r = WatchBuildResult(rebuild_ms=10, error="something broke")
        assert r.ok is False

    def test_defaults(self):
        r = WatchBuildResult()
        assert r.rebuild_ms == 0.0
        assert r.rebuilt == 0
        assert r.cached == 0
        assert r.total_parts == 0
        assert r.error is None
        assert r.is_initial is False


# ---------------------------------------------------------------------------
# Unit tests — mock _rebuild so tests run in milliseconds
# ---------------------------------------------------------------------------

class TestFileWatcherEventLoop:
    """Test watcher event-loop behaviour using a mocked _rebuild."""

    def _make_mock_rebuild(self, rebuilt=1, cached=0, total_parts=1, error=None):
        def fake_rebuild(self_watcher, is_initial=False):
            r = WatchBuildResult(
                rebuild_ms=1.0,
                rebuilt=rebuilt,
                cached=cached,
                total_parts=total_parts,
                error=error,
                is_initial=is_initial,
            )
            self_watcher.on_rebuild(r)
        return fake_rebuild

    def test_initial_build_fires_immediately(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(_SIMPLE_YAML)

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.02)
        with patch.object(FileWatcher, '_rebuild', self._make_mock_rebuild()):
            watcher_results = _collect_results(watcher, stop_after=1, timeout=5)

        assert len(watcher_results) >= 1
        assert watcher_results[0].is_initial is True

    def test_file_change_triggers_second_rebuild(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(_SIMPLE_YAML)

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.02)

        rebuild_calls = []
        original = self._make_mock_rebuild()

        def tracking_rebuild(self_w, is_initial=False):
            rebuild_calls.append(is_initial)
            original(self_w, is_initial=is_initial)

        done = threading.Event()
        def on_rebuild(r):
            results.append(r)
            if len(results) >= 2:
                done.set()
                watcher.stop()

        watcher.on_rebuild = on_rebuild

        with patch.object(FileWatcher, '_rebuild', tracking_rebuild):
            t = threading.Thread(target=watcher.start, daemon=True)
            t.start()

            # Wait for initial build, then touch the file
            time.sleep(0.2)
            f.write_text(_TWO_PART_YAML)
            f.touch()

            done.wait(timeout=10)
            watcher.stop()
            t.join(timeout=5)

        assert len(results) >= 2
        assert results[0].is_initial is True
        assert results[1].is_initial is False

    def test_rapid_saves_debounced_to_single_rebuild(self, tmp_path):
        """Multiple rapid events within debounce window → only one rebuild."""
        f = tmp_path / "test.yaml"
        f.write_text(_SIMPLE_YAML)

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.15)

        done = threading.Event()
        rebuild_after_initial = [0]

        original = self._make_mock_rebuild()
        def tracking_rebuild(self_w, is_initial=False):
            original(self_w, is_initial=is_initial)
            if not is_initial:
                rebuild_after_initial[0] += 1
                if rebuild_after_initial[0] >= 1:
                    done.set()
                    watcher.stop()

        watcher.on_rebuild = results.append

        with patch.object(FileWatcher, '_rebuild', tracking_rebuild):
            t = threading.Thread(target=watcher.start, daemon=True)
            t.start()

            time.sleep(0.2)  # wait for initial

            # Fire 5 rapid events — should debounce to 1 rebuild
            for _ in range(5):
                f.touch()
                time.sleep(0.02)

            done.wait(timeout=10)
            watcher.stop()
            t.join(timeout=5)

        # Should have exactly 1 rebuild after initial (debounced)
        assert rebuild_after_initial[0] == 1

    def test_stop_terminates_loop(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(_SIMPLE_YAML)

        watcher = FileWatcher(f, on_rebuild=lambda r: None, debounce=0.02)
        stopped = threading.Event()

        def run():
            watcher.start()
            stopped.set()

        with patch.object(FileWatcher, '_rebuild', self._make_mock_rebuild()):
            t = threading.Thread(target=run, daemon=True)
            t.start()
            time.sleep(0.3)
            watcher.stop()
            stopped.wait(timeout=10)

        assert stopped.is_set(), "watcher.stop() did not terminate the loop"

    def test_error_in_rebuild_reported_not_raised(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(_SIMPLE_YAML)

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.02)
        with patch.object(FileWatcher, '_rebuild',
                          self._make_mock_rebuild(error="parse failure")):
            _collect_results(watcher, stop_after=1, timeout=5)

        assert results[0].ok is False
        assert "parse failure" in results[0].error


# ---------------------------------------------------------------------------
# Integration tests — real CAD builds (slower)
# ---------------------------------------------------------------------------

class TestFileWatcherIntegration:
    """End-to-end tests with real TiaCAD builds. Marked 'slow' for CI filtering."""

    @pytest.mark.slow
    def test_initial_build_produces_correct_stats(self, tmp_path):
        f = tmp_path / "watch_int.yaml"
        f.write_text(_SIMPLE_YAML)

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.05)
        results = _collect_results(watcher, stop_after=1, timeout=60)

        assert results, "no result received"
        r = results[0]
        assert r.ok, f"build failed: {r.error}"
        assert r.is_initial
        assert r.rebuild_ms > 0
        assert r.total_parts >= 1
        assert r.rebuilt >= 1

    @pytest.mark.slow
    def test_second_build_hits_cache(self, tmp_path):
        """After identical re-save, cached > 0 (IncrementalBuilder reuses geometry)."""
        f = tmp_path / "watch_cache.yaml"
        f.write_text(_SIMPLE_YAML)

        all_results: List[WatchBuildResult] = []
        done = threading.Event()

        def on_rebuild(r: WatchBuildResult) -> None:
            all_results.append(r)
            if len(all_results) == 1 and r.ok:
                # Trigger change with identical content — all parts should cache
                f.write_text(_SIMPLE_YAML)
                f.touch()
            if len(all_results) >= 2:
                done.set()

        watcher = FileWatcher(f, on_rebuild=on_rebuild, debounce=0.05)
        t = threading.Thread(target=watcher.start, daemon=True)
        t.start()
        done.wait(timeout=120)
        watcher.stop()
        t.join(timeout=5)

        assert len(all_results) >= 2
        assert all_results[0].ok
        assert all_results[1].ok
        # Same content → all nodes are clean → everything from cache
        assert all_results[1].cached > 0

    @pytest.mark.slow
    def test_syntax_error_reported_gracefully(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("not: valid: yaml:\n  - [broken")

        results = []
        watcher = FileWatcher(f, on_rebuild=results.append, debounce=0.05)
        results = _collect_results(watcher, stop_after=1, timeout=30)

        assert results
        assert not results[0].ok
        assert results[0].error
