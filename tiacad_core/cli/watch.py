"""`tiacad watch` — rebuild a TiaCAD file on every change using IncrementalBuilder."""

import time
from pathlib import Path

from .output import Colors, print_error, print_info


def _resolve_watch_export_path(export_arg: str | None) -> Path | None:
    """Resolve and validate the optional watch auto-export path."""
    if not export_arg:
        return None

    export_path = Path(export_arg)
    ext = export_path.suffix.lower()
    if ext not in ('.stl', '.3mf', '.step'):
        print_error(f"Unsupported export format: {ext}  (use .stl, .3mf, or .step)")
        return None
    return export_path


def _format_watch_rebuild_line(result) -> str:
    """Format one watch rebuild status line."""
    ts = time.strftime("%H:%M:%S")
    tag = "initial" if result.is_initial else "changed"

    if result.ok:
        cache_str = (
            f"{result.rebuilt} rebuilt, {result.cached} cached"
            if result.cached > 0
            else f"{result.rebuilt} rebuilt"
        )
        export_str = (
            f"  → {Colors.CYAN}{Path(result.exported_path).name}{Colors.RESET}"
            if result.exported_path else ""
        )
        return (
            f"  {Colors.GRAY}[{ts}]{Colors.RESET}"
            f"  {tag:<9}"
            f"  {Colors.GREEN}✓{Colors.RESET}"
            f"  {result.rebuild_ms:>6.0f}ms"
            f"  {Colors.GRAY}{cache_str}{Colors.RESET}"
            f"{export_str}"
        )

    return (
        f"  {Colors.GRAY}[{ts}]{Colors.RESET}"
        f"  {tag:<9}"
        f"  {Colors.RED}✗{Colors.RESET}"
        f"  {Colors.RED}{result.error}{Colors.RESET}"
    )


def _print_watch_start(input_file: Path, export_path: Path | None) -> None:
    """Print watch startup information."""
    print_info(
        f"Watching {Colors.BOLD}{input_file.name}{Colors.RESET}"
        f"  (Ctrl+C to stop)"
    )
    print()
    if export_path:
        print_info(f"Auto-export → {Colors.CYAN}{export_path}{Colors.RESET}")


def _make_watch_rebuild_callback():
    """Create the CLI rebuild callback for watch mode."""
    def on_rebuild(result) -> None:
        print(_format_watch_rebuild_line(result))

    return on_rebuild


def cmd_watch(args):
    """
    Watch a TiaCAD YAML file for changes and rebuild on each modification.

    Uses IncrementalBuilder to reuse cached geometry between rebuilds —
    unchanged parts are served from cache rather than re-computed.

      tiacad watch examples/bracket.yaml
      # [14:32:01] initial   ✓  1842ms  1 rebuilt, 0 cached
      # [14:32:07] changed   ✓   112ms  1 rebuilt, 3 cached
    """
    from ..watcher import FileWatcher

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    export_path = _resolve_watch_export_path(args.export)
    if args.export and export_path is None:
        return 1

    _print_watch_start(input_file, export_path)
    on_rebuild = _make_watch_rebuild_callback()

    watcher = FileWatcher(input_file, on_rebuild=on_rebuild, export_path=export_path)
    try:
        watcher.start()
    except KeyboardInterrupt:
        pass

    print()
    print_info("Stopped.")
    return 0
