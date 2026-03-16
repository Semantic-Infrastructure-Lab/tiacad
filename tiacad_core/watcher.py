"""
Phase 4 — Watch Mode

Watches a TiaCAD YAML file for changes and rebuilds incrementally,
reusing cached geometry from the prior build via IncrementalBuilder.

Usage:
    tiacad watch examples/bracket.yaml
    # [14:32:01] initial      ✓  1842ms  1 rebuilt, 0 cached
    # [14:32:07] changed      ✓   112ms  1 rebuilt, 3 cached
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, FrozenSet, Optional

logger = logging.getLogger(__name__)

# Debounce window: editors often emit 2-3 events per save (write, chmod, rename).
# 300ms quiet period ensures we only rebuild once.
_DEBOUNCE_SECONDS = 0.3


@dataclass
class WatchBuildResult:
    """Result from a single watch rebuild cycle."""
    rebuild_ms: float = 0.0
    rebuilt: int = 0
    cached: int = 0
    total_parts: int = 0
    error: Optional[str] = None
    is_initial: bool = False
    exported_path: Optional[str] = None   # set if --export succeeded

    @property
    def ok(self) -> bool:
        return self.error is None


class FileWatcher:
    """
    Watch a TiaCAD YAML file for changes and rebuild on modification.

    Uses watchdog for OS-level filesystem events. Debounces rapid saves.
    On each rebuild, calls on_rebuild(WatchBuildResult) with timing and
    cache statistics. Uses IncrementalBuilder to reuse unchanged geometry
    across consecutive rebuilds.

    Example::

        def on_rebuild(result):
            if result.ok:
                print(f"Done in {result.rebuild_ms:.0f}ms  "
                      f"({result.rebuilt} rebuilt, {result.cached} cached)")
            else:
                print(f"Error: {result.error}")

        watcher = FileWatcher(Path("examples/bracket.yaml"), on_rebuild)
        watcher.start()   # blocks until KeyboardInterrupt or stop()
    """

    def __init__(
        self,
        file_path: Path,
        on_rebuild: Callable[[WatchBuildResult], None],
        debounce: float = _DEBOUNCE_SECONDS,
        export_path: Optional[Path] = None,
    ) -> None:
        self.file_path = Path(file_path).resolve()
        self.on_rebuild = on_rebuild
        self.debounce = debounce
        self.export_path = Path(export_path) if export_path else None
        self._state = None          # IncrementalState from last successful build
        self._pending = threading.Event()
        self._stop = threading.Event()

    def start(self) -> None:
        """
        Start watching. Performs an initial build immediately, then loops
        watching for file changes. Blocks until KeyboardInterrupt or stop().
        """
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        target = self.file_path
        pending = self._pending

        class _Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and Path(event.src_path).resolve() == target:
                    pending.set()

            def on_created(self, event):
                # Atomic saves: editor writes a new file, renames over old one
                if not event.is_directory and Path(event.src_path).resolve() == target:
                    pending.set()

        observer = Observer()
        observer.schedule(_Handler(), str(self.file_path.parent), recursive=False)
        observer.start()

        try:
            self._rebuild(is_initial=True)
            while not self._stop.is_set():
                fired = self._pending.wait(timeout=0.5)
                if fired:
                    self._pending.clear()
                    time.sleep(self.debounce)   # wait for quiet period
                    self._pending.clear()        # discard events during sleep
                    self._rebuild(is_initial=False)
        finally:
            observer.stop()
            observer.join()

    def stop(self) -> None:
        """Signal the watch loop to stop."""
        self._stop.set()

    def _rebuild(self, is_initial: bool = False) -> None:
        """
        Rebuild the file. Uses IncrementalState from the previous build
        so unchanged parts are served from cache rather than re-computed.
        """
        import yaml

        from .dag.incremental_builder import IncrementalBuilder
        from .parser.color_parser import ColorParser
        from .parser.operations_builder import OperationsBuilder
        from .parser.parameter_resolver import ParameterResolver
        from .parser.parts_builder import PartsBuilder
        from .parser.tiacad_parser import TiaCADParser
        from .part import PartRegistry
        from .spatial_resolver import SpatialResolver

        t0 = time.monotonic()
        result = WatchBuildResult(is_initial=is_initial)

        try:
            # 1. Load and normalize YAML
            with open(self.file_path) as fh:
                yaml_data = yaml.safe_load(fh)
            yaml_data = TiaCADParser._normalize_yaml_aliases(yaml_data)

            s = TiaCADParser._extract_yaml_sections(yaml_data)

            # 2. Parameters → palette → color parser → sketches (no geometry yet)
            param_resolver = ParameterResolver(s['parameters'])
            resolved_palette = (
                TiaCADParser._resolve_color_palette(s['colors'], param_resolver)
                if s['colors'] else {}
            )
            color_parser = ColorParser(palette=resolved_palette)
            sketches = (
                TiaCADParser._build_sketches_from_spec(s['sketches'], param_resolver)
                if s['sketches'] else {}
            )

            # 3. Component imports → pre-populate registry
            registry = PartRegistry()
            if s['imports']:
                from .parser.component_importer import ComponentImporter
                base_dir = os.path.dirname(str(self.file_path))
                imported = ComponentImporter.load_imports(
                    s['imports'], base_dir, frozenset()
                )
                for name in imported.list_parts():
                    registry.add(imported.get(name))

            # 4. References + spatial resolver
            resolved_refs = (
                TiaCADParser._resolve_references(s['references'], param_resolver)
                if s['references'] else {}
            )
            spatial_resolver = SpatialResolver(registry, resolved_refs)

            # 5. Build fine-grained builders for IncrementalBuilder
            parts_builder = PartsBuilder(param_resolver, color_parser)
            ops_builder = OperationsBuilder(
                registry, param_resolver, sketches, spatial_resolver
            )

            # 6. Incremental build — reuses unchanged geometry from _state
            inc_result = IncrementalBuilder().build(
                yaml_data=yaml_data,
                parts_spec=s['parts'],
                operations_spec=s['operations'],
                registry=registry,
                parts_builder=parts_builder,
                ops_builder=ops_builder,
                old_state=self._state,
            )

            self._state = inc_result.state
            result.rebuild_ms = (time.monotonic() - t0) * 1000
            result.rebuilt = inc_result.stats.rebuilt
            result.cached = inc_result.stats.cached
            result.total_parts = len(
                [p for p in registry.list_parts() if not p.startswith('_')]
            )

            if self.export_path:
                self._export(registry, result)

        except Exception as exc:
            result.rebuild_ms = (time.monotonic() - t0) * 1000
            result.error = str(exc)
            logger.debug("Watch rebuild error", exc_info=True)

        self.on_rebuild(result)

    def _export(self, registry, result: WatchBuildResult) -> None:
        """Export the final built part to self.export_path after a successful rebuild."""
        parts = [p for p in registry.list_parts() if not p.startswith('_')]
        if not parts:
            return
        part = registry.get(parts[-1])
        ext = self.export_path.suffix.lower()
        try:
            if ext == '.stl':
                part.geometry.val().exportStl(str(self.export_path))
            elif ext == '.3mf':
                from .exporters.threemf_exporter import ThreeMFExporter
                ThreeMFExporter().export(registry, str(self.export_path))
            elif ext == '.step':
                part.geometry.val().exportStep(str(self.export_path))
            else:
                logger.warning("Unsupported export format: %s", ext)
                return
            result.exported_path = str(self.export_path)
        except Exception as exc:
            logger.warning("Auto-export failed: %s", exc)
