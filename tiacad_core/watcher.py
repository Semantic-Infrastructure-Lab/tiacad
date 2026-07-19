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
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Set

import yaml

from .parser.component_importer import ComponentImporter

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
        self._watched_files: Set[Path] = {self.file_path}

    def _resolve_watch_paths(self) -> Set[Path]:
        """
        Return the root YAML file plus recursively imported local/stdlib files.

        GitHub imports are intentionally excluded because watch mode should track
        author-edited local files, not remote fetch targets.
        """
        visited: Set[Path] = set()

        def walk(path: Path) -> None:
            resolved = path.resolve()
            if resolved in visited or not resolved.exists():
                return

            visited.add(resolved)

            try:
                with open(resolved, encoding="utf-8") as fh:
                    yaml_data = yaml.safe_load(fh) or {}
            except yaml.YAMLError:
                # Temporary syntax errors should not break watch mode. Keep watching
                # the file that changed and let the normal rebuild path report errors.
                return

            for import_def in yaml_data.get("imports", []):
                if not isinstance(import_def, dict):
                    continue

                path_spec = import_def.get("path")
                if not path_spec or path_spec.startswith("github:"):
                    continue

                if path_spec.startswith("tiacad://std/"):
                    imported = Path(ComponentImporter._resolve_stdlib(path_spec))
                else:
                    imported = (resolved.parent / path_spec).resolve()

                if imported.exists():
                    walk(imported)

        walk(self.file_path)
        return visited

    def _refresh_watch_roots(self, observer, handler) -> None:
        """Resubscribe the observer to parent directories of all watched files."""
        watch_paths = self._resolve_watch_paths()
        if watch_paths == self._watched_files:
            return

        observer.unschedule_all()
        for parent in sorted({path.parent for path in watch_paths}):
            observer.schedule(handler, str(parent), recursive=False)

        self._watched_files = watch_paths

    def start(self) -> None:
        """
        Start watching. Performs an initial build immediately, then loops
        watching for file changes. Blocks until KeyboardInterrupt or stop().
        """
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        watcher = self
        pending = self._pending

        class _Handler(FileSystemEventHandler):
            @staticmethod
            def _queue_matching_file(event_path: str) -> None:
                if Path(event_path).resolve() in watcher._watched_files:
                    pending.set()

            @staticmethod
            def _matches(event_path: str) -> bool:
                return Path(event_path).resolve() in watcher._watched_files

            def on_modified(self, event):
                if not event.is_directory:
                    self._queue_matching_file(event.src_path)

            def on_created(self, event):
                # Atomic saves: editor writes a new file, renames over old one
                if not event.is_directory:
                    self.on_modified(event)

            def on_moved(self, event):
                if not event.is_directory and (
                    self._matches(event.src_path) or self._matches(event.dest_path)
                ):
                    pending.set()

        observer = Observer()
        handler = _Handler()
        self._watched_files = set()
        self._refresh_watch_roots(observer, handler)
        observer.start()

        try:
            self._rebuild(is_initial=True)
            self._refresh_watch_roots(observer, handler)
            while not self._stop.is_set():
                fired = self._pending.wait(timeout=0.5)
                if fired:
                    self._pending.clear()
                    time.sleep(self.debounce)   # wait for quiet period
                    self._pending.clear()        # discard events during sleep
                    self._rebuild(is_initial=False)
                    self._refresh_watch_roots(observer, handler)
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
        from .dag.incremental_builder import IncrementalBuilder
        from .parser.constraint_builder import ConstraintBuilder
        from .parser.operations_builder import OperationsBuilder
        from .parser.parse_pipeline import normalize_yaml_aliases, prepare_build_context
        from .parser.parts_builder import PartsBuilder
        from .parser.tiacad_parser import TiaCADDocument
        from .spatial_resolver import SpatialResolver
        t0 = time.monotonic()
        result = WatchBuildResult(is_initial=is_initial)

        try:
            # 1. Load and normalize YAML
            with open(self.file_path) as fh:
                yaml_data = yaml.safe_load(fh)
            yaml_data = normalize_yaml_aliases(yaml_data)
            context = prepare_build_context(
                yaml_data,
                load_imports=ComponentImporter.load_imports,
                file_path=str(self.file_path),
            )
            sections = context.sections

            # 2. Build fine-grained builders for IncrementalBuilder
            parts_builder = PartsBuilder(context.param_resolver, context.color_parser)
            ops_builder = OperationsBuilder(
                context.registry,
                context.param_resolver,
                context.sketches,
                context.spatial_resolver,
            )

            # 3. Incremental build — reuses unchanged geometry from _state
            inc_result = IncrementalBuilder().build(
                yaml_data=yaml_data,
                parts_spec=sections['parts'],
                operations_spec=sections['operations'],
                registry=context.registry,
                parts_builder=parts_builder,
                ops_builder=ops_builder,
                old_state=self._state,
            )

            self._state = inc_result.state

            # 4. Solve `constraints:` — IncrementalBuilder only knows about
            # parts/operations, not constraints (they aren't DAG edges yet,
            # see tt show TCAD-CON-5), so this step is not itself
            # incremental: every watched rebuild re-solves all constraints
            # from scratch against the just-rebuilt registry. Cheap relative
            # to a full re-parse, and correct — the alternative (skipping
            # this entirely, the prior behavior) silently left every
            # constrained part at its raw pre-constraint position in watch
            # mode while the same file built correctly outside watch mode.
            constraints_spec = sections.get('constraints', [])
            if constraints_spec:
                spatial_resolver = SpatialResolver(context.registry, context.resolved_references)
                ConstraintBuilder(context.registry, spatial_resolver).apply_constraints(constraints_spec)

            result.rebuild_ms = (time.monotonic() - t0) * 1000
            result.rebuilt = inc_result.stats.rebuilt
            result.cached = inc_result.stats.cached
            result.total_parts = len(
                [p for p in context.registry.list_parts() if not p.startswith('_')]
            )

            if self.export_path:
                doc = TiaCADDocument(
                    metadata=context.metadata,
                    parameters=context.resolved_params,
                    parts=context.registry,
                    operations=sections['operations'],
                    references=context.resolved_references,
                    export_config=context.export_config,
                    file_path=str(self.file_path),
                )
                self._export(doc, result)

        except Exception as exc:
            result.rebuild_ms = (time.monotonic() - t0) * 1000
            result.error = str(exc)
            logger.debug("Watch rebuild error", exc_info=True)

        self.on_rebuild(result)

    def _export(self, doc, result: WatchBuildResult) -> None:
        """Export the selected build result to self.export_path after a successful rebuild."""
        ext = self.export_path.suffix.lower()
        try:
            if ext == '.stl':
                doc.export_stl(str(self.export_path))
            elif ext == '.3mf':
                from .parser.tiacad_parser import resolve_default_part_name

                selected_part = resolve_default_part_name(
                    doc.parts, doc.operations, doc.export_config
                )
                doc.export_3mf(str(self.export_path), part_name=selected_part)
            elif ext == '.step':
                doc.export_step(str(self.export_path))
            else:
                logger.warning("Unsupported export format: %s", ext)
                return
            result.exported_path = str(self.export_path)
        except Exception as exc:
            logger.warning("Auto-export failed: %s", exc)
