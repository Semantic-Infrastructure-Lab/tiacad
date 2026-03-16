"""
TiaCAD Command-Line Interface

Professional CLI for TiaCAD with subcommands, progress indicators, and color output.

Usage:
    tiacad build examples/plate.yaml --output plate.stl
    tiacad validate examples/*.yaml
    tiacad info examples/bracket.yaml

Author: TIA
Version: 3.1.1
"""

import argparse
import sys
import tempfile
import traceback
from pathlib import Path
import time

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

    @staticmethod
    def disable():
        """Disable colors for non-TTY output"""
        Colors.RESET = ''
        Colors.BOLD = ''
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.MAGENTA = ''
        Colors.CYAN = ''
        Colors.GRAY = ''


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}", file=sys.stderr)


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(message: str):
    """Print header message in bold"""
    print(f"{Colors.BOLD}{message}{Colors.RESET}")


class ProgressBar:
    """Simple progress bar for long operations"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()

    def update(self, n: int = 1):
        """Update progress by n steps"""
        self.current += n
        self._render()

    def _render(self):
        """Render the progress bar"""
        if not sys.stdout.isatty():
            return  # Don't show progress bar in non-TTY

        percent = (self.current / self.total) * 100
        filled = int(50 * self.current / self.total)
        bar = '█' * filled + '░' * (50 - filled)
        elapsed = time.time() - self.start_time

        print(f'\r{self.description}: |{bar}| {percent:.1f}% ({elapsed:.1f}s)', end='', flush=True)

        if self.current >= self.total:
            print()  # New line when done


def _show_dep_graph(args, doc, input_file: Path) -> None:
    """Print dependency graph output if --show-deps was requested."""
    if not (args.show_deps and doc.graph):
        return
    print()
    from .dag import GraphVisualizer
    if args.show_deps in ('text', 'both'):
        GraphVisualizer.show_stats(doc.graph)
    if args.show_deps in ('dot', 'both'):
        dot_path = input_file.stem + '_deps.dot'
        GraphVisualizer.to_dot(doc.graph, str(dot_path))
        print_success(f"Dependency graph written to: {Colors.CYAN}{dot_path}{Colors.RESET}")
        print_info(f"Generate image: dot -Tpng {dot_path} -o graph.png")
        print()


def cmd_build(args):
    """Build a TiaCAD YAML file to 3MF/STL/STEP (defaults to 3MF)"""
    from .parser.tiacad_parser import TiaCADParser

    input_file = Path(args.input)

    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    output_file = Path(args.output) if args.output else input_file.with_suffix('.3mf')
    output_ext = output_file.suffix.lower()
    if output_ext not in ['.stl', '.3mf', '.step']:
        print_error(f"Unsupported output format: {output_ext}")
        print_info("Supported formats: .stl, .3mf, .step")
        return 1

    doc = None
    try:
        build_graph = (args.show_deps is not None)
        print_info(f"Building {Colors.CYAN}{input_file}{Colors.RESET}")
        start_time = time.time()

        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema, build_graph=build_graph)

        parse_time = time.time() - start_time
        print_success(f"Parsed in {parse_time:.2f}s")

        _show_dep_graph(args, doc, input_file)

        print_info(f"Exporting to {Colors.CYAN}{output_file}{Colors.RESET}")
        export_start = time.time()

        if output_ext == '.stl':
            doc.export_stl(str(output_file), part_name=args.part)
        elif output_ext == '.3mf':
            doc.export_3mf(str(output_file), part_name=args.part)
        elif output_ext == '.step':
            doc.export_step(str(output_file), part_name=args.part)

        export_time = time.time() - export_start
        total_time = time.time() - start_time

        print_success(f"Exported in {export_time:.2f}s")
        print_success(f"Total time: {total_time:.2f}s")
        print_success(f"Output: {output_file}")

        if args.stats:
            print_header("\n📊 Statistics:")
            print(f"  Parts: {len(doc.parts.list_parts())}")
            print(f"  Parameters: {len(doc.parameters)}")
            print(f"  Operations: {len(doc.operations)}")

        return 0

    except Exception as e:
        print_error(f"Build failed: {str(e)}")

        if hasattr(e, 'with_context') and doc and hasattr(doc, 'yaml_string') and doc.yaml_string:
            print()
            print(e.with_context(doc.yaml_string))

        if args.verbose:
            print("\n" + Colors.GRAY + "Traceback:" + Colors.RESET)
            traceback.print_exc()

        return 1


def _resolve_file_list(patterns):
    """Expand a list of file paths / glob patterns into resolved Path objects."""
    files = []
    for pattern in patterns:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
        elif '*' in pattern or '?' in pattern:
            files.extend(Path('.').glob(pattern))
        else:
            print_warning(f"No files found matching: {pattern}")
    return files


def _print_file_errors(file: Path, errors) -> None:
    """Print validation errors for a single file."""
    print_error(f"{file}")
    for error in errors:
        print(f"  {Colors.RED}└─{Colors.RESET} {error}")


def cmd_validate(args):
    """Validate TiaCAD YAML files without building geometry"""
    from .parser.tiacad_parser import TiaCADParser

    files = _resolve_file_list(args.files)
    if not files:
        print_error("No files to validate")
        return 1

    print_header(f"Validating {len(files)} file(s)...")

    valid_count = 0
    invalid_count = 0

    for file in files:
        try:
            is_valid, errors = TiaCADParser.validate_file(str(file))
            if is_valid:
                print_success(f"{file}")
                valid_count += 1
            else:
                _print_file_errors(file, errors)
                invalid_count += 1
        except Exception as e:
            _print_file_errors(file, [str(e)])
            invalid_count += 1

    print()
    print_header("Summary:")
    print(f"  {Colors.GREEN}✓ Valid:{Colors.RESET} {valid_count}")
    if invalid_count > 0:
        print(f"  {Colors.RED}✗ Invalid:{Colors.RESET} {invalid_count}")
        return 1
    else:
        print_success("All files valid!")
        return 0


def cmd_info(args):
    """Show information about a TiaCAD file"""
    from .parser.tiacad_parser import TiaCADParser

    input_file = Path(args.input)

    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    try:
        doc = TiaCADParser.parse_file(str(input_file))

        print_header(f"\n📄 {input_file.name}")
        print()

        if doc.metadata:
            print_header("Metadata:")
            for key, value in doc.metadata.items():
                print(f"  {Colors.CYAN}{key}:{Colors.RESET} {value}")
            print()

        if doc.parameters:
            print_header(f"Parameters ({len(doc.parameters)}):")
            for name, value in doc.parameters.items():
                print(f"  {Colors.CYAN}{name}:{Colors.RESET} {value}")
            print()

        parts = doc.parts.list_parts()
        print_header(f"Parts ({len(parts)}):")
        for part_name in parts:
            part = doc.parts.get(part_name)
            prim_type = part.metadata.get('primitive_type', 'unknown')
            print(f"  {Colors.GREEN}•{Colors.RESET} {part_name} ({prim_type})")
        print()

        if doc.operations:
            print_header(f"Operations ({len(doc.operations)}):")
            for op_name, op_def in doc.operations.items():
                op_type = op_def.get('type', 'unknown')
                print(f"  {Colors.YELLOW}•{Colors.RESET} {op_name} ({op_type})")
            print()

        print_header("Statistics:")
        print(f"  Total parts: {len(parts)}")
        print(f"  Parameters: {len(doc.parameters)}")
        print(f"  Operations: {len(doc.operations)}")

        return 0

    except Exception as e:
        print_error(f"Failed to read file: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


def _pick_part_to_validate(args, doc) -> str:
    """Determine which part to validate: explicit arg, last operation, or first part."""
    if args.part:
        return args.part
    if doc.operations:
        return list(doc.operations.keys())[-1]
    parts = doc.parts.list_parts()
    if not parts:
        print_error("No parts found in document")
        return None
    return parts[0]


def _collect_geometry_issues(stats: dict, components, args) -> list:
    """Return a list of human-readable issue strings for the given mesh stats."""
    issues = []
    if stats['components'] > 1:
        issues.append(
            f"❌ {stats['components']} disconnected parts (expected 1 for printable model)"
        )
        if args.verbose:
            for i, comp in enumerate(components[:5]):
                issues.append(
                    f"   Component {i+1}: {len(comp.vertices)} vertices, {len(comp.faces)} faces"
                )
            if len(components) > 5:
                issues.append(f"   ... and {len(components) - 5} more")
    if not stats['watertight']:
        issues.append("❌ Mesh not watertight (will cause slicing errors)")
    if stats['volume'] <= 0:
        issues.append(f"❌ Invalid volume: {stats['volume']:.2f} mm³")
    if stats['vertices'] == 0:
        issues.append("❌ Empty mesh (no vertices)")
    if stats['faces'] == 0:
        issues.append("❌ No faces")
    return issues


def _print_geometry_outcome(stats: dict, issues: list, parse_time: float, export_time: float) -> int:
    """Print geometry stats table and outcome. Returns exit code."""
    print()
    print_header("📊 Geometry Analysis")
    print()
    print(f"  Vertices:    {stats['vertices']:,}")
    print(f"  Faces:       {stats['faces']:,}")
    print(f"  Volume:      {stats['volume']:.2f} mm³")
    print(f"  Watertight:  {'✅ Yes' if stats['watertight'] else '❌ No'}")
    print(f"  Components:  {stats['components']}")
    print()

    if not issues:
        print_success("✅ Geometry is valid and printable")
        print()
        print_info(f"Parse time:  {parse_time:.2f}s")
        print_info(f"Export time: {export_time:.2f}s")
        return 0
    else:
        print_error("❌ Geometry validation failed:")
        print()
        for issue in issues:
            print(f"  {issue}")
        print()
        print_warning("💡 Tip: For union operations, ensure parts actually overlap")
        print()
        return 1


def cmd_validate_geometry(args):
    """
    Validate geometry of built parts for 3D printing.

    Checks:
    - Single connected component (union operations actually merge)
    - Watertight meshes (no holes or gaps)
    - Positive volumes
    - No degenerate faces
    """
    from .parser.tiacad_parser import TiaCADParser

    try:
        import trimesh
    except ImportError:
        print_error("trimesh library required for geometry validation")
        print_info("Install with: pip install trimesh")
        return 1

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    print_info(f"Validating {Colors.CYAN}{input_file.name}{Colors.RESET}")
    print()

    try:
        start_time = time.time()
        doc = TiaCADParser.parse_file(str(input_file))
        parse_time = time.time() - start_time

        part_name = _pick_part_to_validate(args, doc)
        if part_name is None:
            return 1

        print_info(f"Validating part: {Colors.CYAN}{part_name}{Colors.RESET}")
        part = doc.parts.get(part_name)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            export_start = time.time()
            part.geometry.val().exportStl(str(tmp_path))
            export_time = time.time() - export_start

            mesh = trimesh.load(str(tmp_path))
            components = mesh.split(only_watertight=False)
            stats = {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'volume': mesh.volume,
                'watertight': mesh.is_watertight,
                'components': len(components),
            }
            issues = _collect_geometry_issues(stats, components, args)
            return _print_geometry_outcome(stats, issues, parse_time, export_time)

        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_check(args):
    """
    Build a TiaCAD file and report dimensions, volume, and validity for every part.

    No file output. Designed as a fast development loop tool:
      - Did my boolean subtract actually remove material?
      - Is this box really 80mm wide?
      - Did the revolve produce positive volume?
    """
    from .parser.tiacad_parser import TiaCADParser
    from .testing.dimensions import get_dimensions, DimensionError

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    print_header(f"\n📄 {input_file.name}")
    print()

    try:
        start_time = time.time()
        doc = TiaCADParser.parse_file(str(input_file))
        parse_time = time.time() - start_time

        if doc.parameters:
            print_header(f"Parameters ({len(doc.parameters)}):")
            pairs = [f"{Colors.CYAN}{k}{Colors.RESET}={v}" for k, v in doc.parameters.items()]
            # Wrap at ~80 chars
            line = "  "
            for p in pairs:
                line += p + "  "
            print(line.rstrip())
            print()

        # Identify the "final" part (last operation result)
        final_part_name = None
        if doc.operations:
            final_part_name = list(doc.operations.keys())[-1]

        parts = doc.parts.list_parts()
        if not parts:
            print_warning("No parts found in document")
            return 0

        # Column widths (exclude internal _ parts)
        visible_parts = [p for p in parts if not p.startswith('_')]
        max_name = max((len(p) for p in visible_parts), default=8)
        col_w = max(max_name, 8)

        print_header(f"Parts ({len(visible_parts)}):")
        print(f"  {'NAME':<{col_w}}  {'TYPE':<8}  {'W × H × D (mm)':<30}  VOLUME (mm³)")
        print(f"  {'─'*col_w}  {'─'*8}  {'─'*30}  {'─'*14}")

        errors = []
        build_start = time.time()

        for part_name in parts:
            if part_name.startswith('_'):
                continue  # skip internal placeholder parts
            part = doc.parts.get(part_name)
            prim_type = (
                part.metadata.get('primitive_type')
                or part.metadata.get('operation_type')
                or part.metadata.get('source')
                or '?'
            )
            is_final = part_name == final_part_name

            try:
                dims = get_dimensions(part)
                w, h, d = dims['width'], dims['height'], dims['depth']
                vol = dims['volume']
                dim_str = f"{w:.1f} × {h:.1f} × {d:.1f}"
                vol_str = f"{vol:>14,.1f}"

                star = f"{Colors.YELLOW}★{Colors.RESET}" if is_final else " "
                pad = ' ' * (col_w - len(part_name))
                if is_final:
                    name_col = f"{Colors.BOLD}{Colors.GREEN}{part_name}{Colors.RESET}"
                else:
                    name_col = f"{Colors.GREEN}{part_name}{Colors.RESET}"
                print(f"  {name_col}{pad}  {star} {Colors.GRAY}{prim_type:<8}{Colors.RESET}  {dim_str:<30}  {vol_str}")

            except DimensionError as e:
                errors.append((part_name, str(e)))
                star = "★" if is_final else " "
                pad = ' ' * (col_w - len(part_name))
                print(f"  {Colors.RED}{part_name}{Colors.RESET}{pad}  {star} {Colors.GRAY}{prim_type:<8}{Colors.RESET}  {Colors.RED}ERROR: {e}{Colors.RESET}")

        build_time = time.time() - build_start
        print()

        if errors:
            print_error(f"{len(errors)} part(s) failed measurement")
            for name, msg in errors:
                print(f"  {Colors.RED}└─ {name}:{Colors.RESET} {msg}")
            return 1
        else:
            n = len(visible_parts)
            print_success(
                f"All {n} part{'s' if n != 1 else ''} built  "
                f"(parse: {parse_time:.2f}s  build: {build_time:.2f}s)"
            )
            return 0

    except Exception as e:
        print_error(f"Check failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


def _audit_one_file(input_file: Path, verbose: bool):
    """
    Build a single file and return a result dict for the audit table.
    Keys: name, status ('ok'/'fail'/'warn'), dims, volume, parts_count,
          final_part, error, elapsed.
    """
    from .parser.tiacad_parser import TiaCADParser
    from .testing.dimensions import get_dimensions, DimensionError

    result = {
        'name': input_file.name,
        'status': 'ok',
        'dims': None,
        'volume': None,
        'parts_count': 0,
        'final_part': None,
        'issues': [],
        'error': None,
        'elapsed': 0.0,
    }

    try:
        t0 = time.time()
        doc = TiaCADParser.parse_file(str(input_file))

        parts = doc.parts.list_parts()
        result['parts_count'] = len(parts)

        # Pick final part
        final_name = None
        if doc.operations:
            final_name = list(doc.operations.keys())[-1]
        elif parts:
            final_name = parts[0]

        result['final_part'] = final_name

        if final_name:
            part = doc.parts.get(final_name)
            try:
                dims = get_dimensions(part)
                result['dims'] = (dims['width'], dims['height'], dims['depth'])
                result['volume'] = dims['volume']

                if dims['volume'] <= 0:
                    result['issues'].append(f"zero/negative volume: {dims['volume']:.1f}")
                    result['status'] = 'warn'

            except DimensionError as e:
                result['issues'].append(f"measure failed: {e}")
                result['status'] = 'warn'

        result['elapsed'] = time.time() - t0

    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
        if verbose:
            result['error'] += f"\n{traceback.format_exc()}"

    return result


def cmd_audit(args):
    """
    Audit multiple TiaCAD files: build each, report dimensions and volume of
    the final part, flag failures and anomalies.

    Designed for establishing ground truth across all examples:
      tiacad audit examples/*.yaml
    """
    files = _resolve_file_list(args.files)
    if not files:
        print_error("No files to audit")
        return 1

    # Sort for stable output
    files = sorted(files, key=lambda p: p.name)

    print_header(f"Auditing {len(files)} file(s)...\n")

    results = []
    total_start = time.time()

    for i, f in enumerate(files, 1):
        # Show progress on TTY
        if sys.stdout.isatty():
            print(f"\r  [{i}/{len(files)}] {f.name:<50}", end='', flush=True)
        result = _audit_one_file(f, verbose=args.verbose)
        results.append(result)

    if sys.stdout.isatty():
        print(f"\r{' ' * 60}\r", end='')  # clear progress line

    total_elapsed = time.time() - total_start

    # Column widths
    max_name = max(len(r['name']) for r in results)
    col_w = max(max_name, 12)

    # Header
    print(f"  {'FILE':<{col_w}}  {'PARTS':>5}  {'STATUS':<7}  {'DIMS W×H×D (mm)':<32}  {'VOLUME (mm³)':>14}  TIME")
    print(f"  {'─'*col_w}  {'─'*5}  {'─'*7}  {'─'*32}  {'─'*14}  {'─'*6}")

    ok_count = warn_count = fail_count = 0

    for r in results:
        name = r['name']
        parts_str = str(r['parts_count']) if r['parts_count'] else '-'
        elapsed_str = f"{r['elapsed']:.1f}s"

        if r['status'] == 'ok':
            ok_count += 1
            status_str = f"{Colors.GREEN}✓ OK   {Colors.RESET}"
        elif r['status'] == 'warn':
            warn_count += 1
            status_str = f"{Colors.YELLOW}⚠ WARN {Colors.RESET}"
        else:
            fail_count += 1
            status_str = f"{Colors.RED}✗ FAIL {Colors.RESET}"

        if r['dims']:
            w, h, d = r['dims']
            dims_str = f"{w:.1f} × {h:.1f} × {d:.1f}"
        elif r['error']:
            # Truncate error to fit column
            dims_str = r['error'][:30]
        else:
            dims_str = '-'

        vol_str = f"{r['volume']:>14,.1f}" if r['volume'] is not None else f"{'—':>14}"

        print(
            f"  {name:<{col_w}}  {parts_str:>5}  {status_str}  "
            f"{dims_str:<32}  {vol_str}  {elapsed_str}"
        )

        for issue in r['issues']:
            print(f"  {' '*(col_w+2)}  {Colors.YELLOW}└─ {issue}{Colors.RESET}")

    print()
    print_header("Summary:")
    print(f"  {Colors.GREEN}✓ OK:   {ok_count}{Colors.RESET}")
    if warn_count:
        print(f"  {Colors.YELLOW}⚠ WARN: {warn_count}{Colors.RESET}")
    if fail_count:
        print(f"  {Colors.RED}✗ FAIL: {fail_count}{Colors.RESET}")
    print(f"  Total: {len(files)} files  ({total_elapsed:.1f}s)")

    return 0 if fail_count == 0 else 1


def cmd_watch(args):
    """
    Watch a TiaCAD YAML file for changes and rebuild on each modification.

    Uses IncrementalBuilder to reuse cached geometry between rebuilds —
    unchanged parts are served from cache rather than re-computed.

      tiacad watch examples/bracket.yaml
      # [14:32:01] initial   ✓  1842ms  1 rebuilt, 0 cached
      # [14:32:07] changed   ✓   112ms  1 rebuilt, 3 cached
    """
    from .watcher import FileWatcher, WatchBuildResult

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    print_info(
        f"Watching {Colors.BOLD}{input_file.name}{Colors.RESET}"
        f"  (Ctrl+C to stop)"
    )
    print()

    def on_rebuild(result: WatchBuildResult) -> None:
        ts = time.strftime("%H:%M:%S")
        tag = "initial" if result.is_initial else "changed"
        if result.ok:
            cache_str = (
                f"{result.rebuilt} rebuilt, {result.cached} cached"
                if result.cached > 0
                else f"{result.rebuilt} rebuilt"
            )
            print(
                f"  {Colors.GRAY}[{ts}]{Colors.RESET}"
                f"  {tag:<9}"
                f"  {Colors.GREEN}✓{Colors.RESET}"
                f"  {result.rebuild_ms:>6.0f}ms"
                f"  {Colors.GRAY}{cache_str}{Colors.RESET}"
            )
        else:
            print(
                f"  {Colors.GRAY}[{ts}]{Colors.RESET}"
                f"  {tag:<9}"
                f"  {Colors.RED}✗{Colors.RESET}"
                f"  {Colors.RED}{result.error}{Colors.RESET}"
            )

    watcher = FileWatcher(input_file, on_rebuild=on_rebuild)
    try:
        watcher.start()
    except KeyboardInterrupt:
        pass

    print()
    print_info("Stopped.")
    return 0


def create_parser():
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        prog='tiacad',
        description='TiaCAD - Declarative Parametric CAD in YAML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tiacad build examples/plate.yaml                    # Outputs plate.3mf (modern format)
  tiacad build examples/plate.yaml -o plate.stl       # Force STL output
  tiacad build examples/bracket.yaml -o bracket.step  # CAD exchange format
  tiacad validate examples/*.yaml
  tiacad info examples/bracket.yaml

Note: 3MF is the recommended format for 3D printing (multi-material, compact, modern).
      STL is supported for legacy compatibility.

For more information: https://github.com/scottsen/tiacad
        """
    )

    parser.add_argument('--version', action='version', version='TiaCAD 3.1.1')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build a TiaCAD file to 3MF/STL/STEP (modern 3MF format recommended)')
    build_parser.add_argument('input', help='Input YAML file')
    build_parser.add_argument('-o', '--output', help='Output file (default: same name with .3mf extension - use .stl or .step to override)')
    build_parser.add_argument('-p', '--part', help='Specific part to export (default: last operation)')
    build_parser.add_argument('-s', '--stats', action='store_true', help='Show build statistics')
    build_parser.add_argument('--validate-schema', action='store_true', help='Enable JSON schema validation')
    build_parser.add_argument('--show-deps', choices=['text', 'dot', 'both'], help='Show dependency graph (text summary or Graphviz DOT)')
    build_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with traceback')
    build_parser.set_defaults(func=cmd_build)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate YAML files without building')
    validate_parser.add_argument('files', nargs='+', help='YAML file(s) to validate (supports glob patterns)')
    validate_parser.set_defaults(func=cmd_validate)

    # Info command
    info_parser = subparsers.add_parser('info', help='Show information about a TiaCAD file')
    info_parser.add_argument('input', help='Input YAML file')
    info_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    info_parser.set_defaults(func=cmd_info)

    # Validate-geometry command
    validate_geom_parser = subparsers.add_parser(
        'validate-geometry',
        help='Validate geometry is printable (checks for disconnected parts, watertightness)'
    )
    validate_geom_parser.add_argument('input', help='Input YAML file')
    validate_geom_parser.add_argument('-p', '--part', help='Specific part to validate (default: last operation)')
    validate_geom_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with component details')
    validate_geom_parser.set_defaults(func=cmd_validate_geometry)

    # Check command
    check_parser = subparsers.add_parser(
        'check',
        help='Build a file and report dimensions + volume for every part (no output file)'
    )
    check_parser.add_argument('input', help='Input YAML file')
    check_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with traceback on error')
    check_parser.set_defaults(func=cmd_check)

    # Audit command
    audit_parser = subparsers.add_parser(
        'audit',
        help='Audit multiple files: build each, report final-part dimensions and flag failures'
    )
    audit_parser.add_argument('files', nargs='+', help='YAML file(s) to audit (supports glob patterns)')
    audit_parser.add_argument('-v', '--verbose', action='store_true', help='Show full tracebacks on failure')
    audit_parser.set_defaults(func=cmd_audit)

    # Watch command
    watch_parser = subparsers.add_parser(
        'watch',
        help='Watch a file and rebuild on each save (incremental — reuses cached geometry)'
    )
    watch_parser.add_argument('input', help='Input YAML file to watch')
    watch_parser.set_defaults(func=cmd_watch)

    return parser


def main(argv=None):
    """Main entry point for CLI"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    if not args.command:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print()
        print_warning("Interrupted by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
