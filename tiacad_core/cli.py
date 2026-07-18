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
import json
import sys
import tempfile
import traceback
from pathlib import Path
import time

from . import __version__

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


def _resolve_build_output(input_file: Path, output_arg: str | None) -> Path | None:
    """Resolve and validate the build output path."""
    output_file = Path(output_arg) if output_arg else input_file.with_suffix('.3mf')
    output_ext = output_file.suffix.lower()
    if output_ext not in ['.stl', '.3mf', '.step']:
        print_error(f"Unsupported output format: {output_ext}")
        print_info("Supported formats: .stl, .3mf, .step")
        return None
    return output_file


def _export_document(doc, output_file: Path, part_name: str | None) -> None:
    """Export a parsed document to the requested format."""
    output_ext = output_file.suffix.lower()
    if output_ext == '.stl':
        doc.export_stl(str(output_file), part_name=part_name)
    elif output_ext == '.3mf':
        doc.export_3mf(str(output_file), part_name=part_name)
    elif output_ext == '.step':
        doc.export_step(str(output_file), part_name=part_name)


def _print_build_stats(doc) -> None:
    """Print post-build document statistics."""
    print_header("\n📊 Statistics:")
    print(f"  Parts: {len(doc.parts.list_parts())}")
    print(f"  Parameters: {len(doc.parameters)}")
    print(f"  Operations: {len(doc.operations)}")


def _print_build_success(output_file: Path, parse_time: float, export_time: float, total_time: float) -> None:
    """Print a successful build summary."""
    print_success(f"Parsed in {parse_time:.2f}s")
    print_success(f"Exported in {export_time:.2f}s")
    print_success(f"Total time: {total_time:.2f}s")
    print_success(f"Output: {output_file}")


def _print_build_failure(error: Exception, doc, verbose: bool) -> None:
    """Print build failure output consistently."""
    print_error(f"Build failed: {str(error)}")

    if hasattr(error, 'with_context') and doc and hasattr(doc, 'yaml_string') and doc.yaml_string:
        print()
        print(error.with_context(doc.yaml_string))

    if verbose:
        print("\n" + Colors.GRAY + "Traceback:" + Colors.RESET)
        traceback.print_exc()


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


def cmd_build(args):
    """Build a TiaCAD YAML file to 3MF/STL/STEP (defaults to 3MF)"""
    from .parser.tiacad_parser import TiaCADParser

    input_file = Path(args.input)

    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    output_file = _resolve_build_output(input_file, args.output)
    if output_file is None:
        return 1

    doc = None
    try:
        build_graph = (args.show_deps is not None)
        print_info(f"Building {Colors.CYAN}{input_file}{Colors.RESET}")
        start_time = time.time()

        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema, build_graph=build_graph)
        parse_time = time.time() - start_time

        _show_dep_graph(args, doc, input_file)

        print_info(f"Exporting to {Colors.CYAN}{output_file}{Colors.RESET}")
        export_start = time.time()
        _export_document(doc, output_file, args.part)
        export_time = time.time() - export_start

        total_time = time.time() - start_time
        _print_build_success(output_file, parse_time, export_time, total_time)

        if args.stats:
            _print_build_stats(doc)

        return 0

    except Exception as e:
        _print_build_failure(e, doc, args.verbose)
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
        _print_info_report(input_file, doc)
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
    part_name = _get_default_part_name(doc)
    if part_name is None:
        print_error("No parts found in document")
        return None
    return part_name


def _get_default_part_name(doc):
    """Pick the default/final part for single-part inspection commands."""
    if doc.operations:
        return list(doc.operations.keys())[-1]
    parts = doc.parts.list_parts()
    if not parts:
        return None
    return parts[0]


def _visible_parts(doc):
    """Return user-visible parts, excluding internal placeholders."""
    return [part_name for part_name in doc.parts.list_parts() if not part_name.startswith('_')]


def _print_key_value_section(title: str, items) -> None:
    """Print a simple key/value section when items are present."""
    if not items:
        return
    print_header(title)
    for key, value in items:
        print(f"  {Colors.CYAN}{key}:{Colors.RESET} {value}")
    print()


def _print_part_section(doc) -> list[str]:
    """Print the parts section and return the visible part names."""
    parts = _visible_parts(doc)
    print_header(f"Parts ({len(parts)}):")
    for part_name in parts:
        part = doc.parts.get(part_name)
        print(
            f"  {Colors.GREEN}•{Colors.RESET} "
            f"{part_name} ({_get_part_display_type(part)})"
        )
    print()
    return parts


def _print_operation_section(doc) -> None:
    """Print the operations section when operations are present."""
    if not doc.operations:
        return
    print_header(f"Operations ({len(doc.operations)}):")
    for op_name, op_def in doc.operations.items():
        op_type = op_def.get('type', 'unknown')
        print(f"  {Colors.YELLOW}•{Colors.RESET} {op_name} ({op_type})")
    print()


def _print_info_statistics(doc, visible_part_names: list[str]) -> None:
    """Print aggregate info statistics for a parsed document."""
    print_header("Statistics:")
    print(f"  Total parts: {len(visible_part_names)}")
    print(f"  Parameters: {len(doc.parameters)}")
    print(f"  Operations: {len(doc.operations)}")


def _print_info_report(input_file: Path, doc) -> None:
    """Print the full `tiacad info` report for a parsed document."""
    print_header(f"\n📄 {input_file.name}")
    print()
    _print_key_value_section("Metadata:", doc.metadata.items())
    _print_key_value_section(
        f"Parameters ({len(doc.parameters)}):",
        doc.parameters.items(),
    )
    visible_part_names = _print_part_section(doc)
    _print_operation_section(doc)
    _print_info_statistics(doc, visible_part_names)


def _format_parameter_summary(parameters: dict) -> str:
    """Format resolved parameters for compact CLI display."""
    pairs = [f"{Colors.CYAN}{key}{Colors.RESET}={value}" for key, value in parameters.items()]
    return "  " + "  ".join(pairs)


def _get_part_display_type(part) -> str:
    """Return the best available type label for a part."""
    return (
        part.metadata.get('primitive_type')
        or part.metadata.get('operation_type')
        or part.metadata.get('source')
        or '?'
    )


def _measure_part_dimensions(part):
    """Measure a part and return width/height/depth/volume."""
    from .testing.dimensions import get_dimensions

    dims = get_dimensions(part)
    return {
        'width': dims['width'],
        'height': dims['height'],
        'depth': dims['depth'],
        'volume': dims['volume'],
    }


def _build_check_rows(doc):
    """Collect per-part rows for `tiacad check`."""
    from .testing.dimensions import DimensionError

    final_part_name = _get_default_part_name(doc)
    rows = []
    errors = []

    for part_name in _visible_parts(doc):
        part = doc.parts.get(part_name)
        row = {
            'name': part_name,
            'type': _get_part_display_type(part),
            'is_final': part_name == final_part_name,
            'measurement': None,
            'error': None,
        }

        try:
            row['measurement'] = _measure_part_dimensions(part)
        except DimensionError as e:
            row['error'] = str(e)
            errors.append((part_name, str(e)))

        rows.append(row)

    return rows, errors


def _print_check_rows(rows) -> None:
    """Print the per-part table for `tiacad check`."""
    col_w = max((len(row['name']) for row in rows), default=8)
    col_w = max(col_w, 8)

    print_header(f"Parts ({len(rows)}):")
    print(f"  {'NAME':<{col_w}}  {'TYPE':<8}  {'W × H × D (mm)':<30}  VOLUME (mm³)")
    print(f"  {'─'*col_w}  {'─'*8}  {'─'*30}  {'─'*14}")

    for row in rows:
        star = f"{Colors.YELLOW}★{Colors.RESET}" if row['is_final'] else " "
        pad = ' ' * (col_w - len(row['name']))
        if row['is_final']:
            name_col = f"{Colors.BOLD}{Colors.GREEN}{row['name']}{Colors.RESET}"
        else:
            name_col = f"{Colors.GREEN}{row['name']}{Colors.RESET}"

        if row['error']:
            print(
                f"  {Colors.RED}{row['name']}{Colors.RESET}{pad}  "
                f"{star} {Colors.GRAY}{row['type']:<8}{Colors.RESET}  "
                f"{Colors.RED}ERROR: {row['error']}{Colors.RESET}"
            )
            continue

        measurement = row['measurement']
        dim_str = (
            f"{measurement['width']:.1f} × "
            f"{measurement['height']:.1f} × "
            f"{measurement['depth']:.1f}"
        )
        vol_str = f"{measurement['volume']:>14,.1f}"
        print(
            f"  {name_col}{pad}  {star} {Colors.GRAY}{row['type']:<8}{Colors.RESET}  "
            f"{dim_str:<30}  {vol_str}"
        )


def _empty_audit_result(input_file: Path) -> dict:
    """Create a default audit result record."""
    return {
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


def _measure_audit_final_part(doc, result: dict) -> None:
    """Populate audit measurements and warnings for the final/default part."""
    from .testing.dimensions import DimensionError

    final_name = _get_default_part_name(doc)
    result['final_part'] = final_name

    if final_name is None:
        return

    part = doc.parts.get(final_name)
    try:
        measurement = _measure_part_dimensions(part)
        result['dims'] = (
            measurement['width'],
            measurement['height'],
            measurement['depth'],
        )
        result['volume'] = measurement['volume']
        if measurement['volume'] <= 0:
            result['issues'].append(f"zero/negative volume: {measurement['volume']:.1f}")
            result['status'] = 'warn'
    except DimensionError as e:
        result['issues'].append(f"measure failed: {e}")
        result['status'] = 'warn'


def _format_audit_dims(result: dict) -> str:
    """Format the audit dimensions/error column."""
    if result['dims']:
        width, height, depth = result['dims']
        return f"{width:.1f} × {height:.1f} × {depth:.1f}"
    if result['error']:
        return result['error'][:30]
    return '-'


def _format_audit_status(status: str) -> str:
    """Format a colored audit status label."""
    if status == 'ok':
        return f"{Colors.GREEN}✓ OK   {Colors.RESET}"
    if status == 'warn':
        return f"{Colors.YELLOW}⚠ WARN {Colors.RESET}"
    return f"{Colors.RED}✗ FAIL {Colors.RESET}"


def _print_audit_results(results) -> tuple[int, int, int]:
    """Print the audit table and return ok/warn/fail counts."""
    col_w = max((len(result['name']) for result in results), default=12)
    col_w = max(col_w, 12)

    print(f"  {'FILE':<{col_w}}  {'PARTS':>5}  {'STATUS':<7}  {'DIMS W×H×D (mm)':<32}  {'VOLUME (mm³)':>14}  TIME")
    print(f"  {'─'*col_w}  {'─'*5}  {'─'*7}  {'─'*32}  {'─'*14}  {'─'*6}")

    ok_count = warn_count = fail_count = 0
    for result in results:
        if result['status'] == 'ok':
            ok_count += 1
        elif result['status'] == 'warn':
            warn_count += 1
        else:
            fail_count += 1

        parts_str = str(result['parts_count']) if result['parts_count'] else '-'
        elapsed_str = f"{result['elapsed']:.1f}s"
        vol_str = f"{result['volume']:>14,.1f}" if result['volume'] is not None else f"{'—':>14}"

        print(
            f"  {result['name']:<{col_w}}  {parts_str:>5}  {_format_audit_status(result['status'])}  "
            f"{_format_audit_dims(result):<32}  {vol_str}  {elapsed_str}"
        )

        for issue in result['issues']:
            print(f"  {' '*(col_w+2)}  {Colors.YELLOW}└─ {issue}{Colors.RESET}")

    return ok_count, warn_count, fail_count


def _print_audit_summary(ok_count: int, warn_count: int, fail_count: int, total_files: int, total_elapsed: float) -> None:
    """Print the audit summary block."""
    print()
    print_header("Summary:")
    print(f"  {Colors.GREEN}✓ OK:   {ok_count}{Colors.RESET}")
    if warn_count:
        print(f"  {Colors.YELLOW}⚠ WARN: {warn_count}{Colors.RESET}")
    if fail_count:
        print(f"  {Colors.RED}✗ FAIL: {fail_count}{Colors.RESET}")
    print(f"  Total: {total_files} files  ({total_elapsed:.1f}s)")


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
    from .backend_support import require_cadquery_part
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
        require_cadquery_part(part, "Geometry validation")

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

    With --contract: also check the file's embedded expect: block (if any)
    against the actual built geometry (see docs/developer/VALIDATION_STRENGTHENING.md
    section 4.1).
    """
    from .parser.tiacad_parser import TiaCADParser

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

        if getattr(args, 'contract', False):
            from .testing.contracts import ContractError, check_contract
            print()
            try:
                result = check_contract(doc)
            except ContractError as e:
                print_error(f"Contract check: {e}")
                return 1
            if result.ok:
                print_success(result.summary())
            else:
                print_error(result.summary())
                return 1

        if doc.parameters:
            print_header(f"Parameters ({len(doc.parameters)}):")
            print(_format_parameter_summary(doc.parameters))
            print()

        rows, errors = _build_check_rows(doc)
        if not rows:
            print_warning("No parts found in document")
            return 0

        build_start = time.time()
        _print_check_rows(rows)

        build_time = time.time() - build_start
        print()

        if errors:
            print_error(f"{len(errors)} part(s) failed measurement")
            for name, msg in errors:
                print(f"  {Colors.RED}└─ {name}:{Colors.RESET} {msg}")
            return 1
        else:
            n = len(rows)
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


def cmd_verify(args):
    """
    Evaluate a model's embedded expect: contract and report the result.

    Single-purpose sibling of `check --contract`: no part-by-part dimension
    table, just the contract verdict — a concise console summary plus,
    with --json, a machine-readable result for CI/tooling consumption.
    Implements docs/developer/MODEL_VALIDATION.md "Best Next Improvements" #3.
    """
    from .parser.tiacad_parser import TiaCADParser
    from .testing.contracts import ContractError, check_contract

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    try:
        doc = TiaCADParser.parse_file(str(input_file))
        result = check_contract(doc)
    except ContractError as e:
        print_error(f"{input_file.name}: {e}")
        if args.json:
            print(json.dumps({'file': str(input_file), 'error': str(e)}, indent=2, sort_keys=True))
        return 1
    except Exception as e:
        print_error(f"Verify failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    if result.ok:
        print_success(result.summary())
    else:
        print_error(result.summary())

    if args.json:
        print(json.dumps({
            'file': str(input_file),
            'ok': result.ok,
            'part_name': result.part_name,
            'violations': [
                {'check': v.check, 'message': v.message} for v in result.violations
            ],
        }, indent=2, sort_keys=True))

    return 0 if result.ok else 1


def _audit_one_file(input_file: Path, verbose: bool):
    """
    Build a single file and return a result dict for the audit table.
    Keys: name, status ('ok'/'fail'/'warn'), dims, volume, parts_count,
          final_part, error, elapsed.
    """
    from .parser.tiacad_parser import TiaCADParser

    result = _empty_audit_result(input_file)

    try:
        t0 = time.time()
        doc = TiaCADParser.parse_file(str(input_file))
        result['parts_count'] = len(doc.parts.list_parts())
        _measure_audit_final_part(doc, result)
        result['elapsed'] = time.time() - t0

    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
        if verbose:
            result['error'] += f"\n{traceback.format_exc()}"

    return result


def _cmd_audit_write_contract(files, verbose: bool) -> int:
    """Seed an expect: block per file from its current build (for --write-contract)."""
    from .parser.tiacad_parser import TiaCADParser
    from .testing.contracts import write_contract_yaml

    fail_count = 0
    for f in files:
        print_header(f"\n📄 {f.name}")
        try:
            doc = TiaCADParser.parse_file(str(f))
            print(write_contract_yaml(doc))
        except Exception as e:
            fail_count += 1
            print_error(f"Failed to build: {e}")
            if verbose:
                traceback.print_exc()

    print()
    if fail_count:
        print_error(f"{fail_count}/{len(files)} file(s) failed to build")
        return 1
    print_success(f"Seeded contracts for {len(files)} file(s) — review before pasting into the model file")
    return 0


def cmd_audit(args):
    """
    Audit multiple TiaCAD files: build each, report dimensions and volume of
    the final part, flag failures and anomalies.

    Designed for establishing ground truth across all examples:
      tiacad audit examples/*.yaml

    With --write-contract: instead of the audit table, seed an expect:
    YAML block from each file's current build for a human to review and
    paste into the file (see docs/developer/VALIDATION_STRENGTHENING.md
    section 4.1). Does not modify any file.
    """
    files = _resolve_file_list(args.files)
    if not files:
        print_error("No files to audit")
        return 1

    # Sort for stable output
    files = sorted(files, key=lambda p: p.name)

    if getattr(args, 'write_contract', False):
        return _cmd_audit_write_contract(files, args.verbose)

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
    ok_count, warn_count, fail_count = _print_audit_results(results)
    _print_audit_summary(ok_count, warn_count, fail_count, len(files), total_elapsed)

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
    from .watcher import FileWatcher

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


def _resolve_debug_bundle_path(input_file: Path, bundle_arg: str | None) -> Path:
    """Resolve the bundle output directory for `tiacad debug`."""
    from .debug_bundle import default_debug_bundle_dir

    return Path(bundle_arg).resolve() if bundle_arg else default_debug_bundle_dir(input_file).resolve()


def _print_debug_bundle_summary(manifest: dict, bundle_dir: Path) -> None:
    """Print a concise human summary for a completed debug bundle."""
    summary = manifest['summary']
    print_success(f"Debug bundle written to {bundle_dir}")
    print_info(
        f"Parts: {summary['parts_total']} total, "
        f"{summary['visible_parts_total']} visible, "
        f"{summary['operations_total']} operations"
    )
    print_info(f"Default part: {summary['default_part'] or '-'}")

    validation = summary['validation']
    status = "passed" if validation['passed'] else "failed"
    print_info(
        "Validation "
        f"{status}: {validation['error_count']} errors, "
        f"{validation['warning_count']} warnings, "
        f"{validation['info_count']} info"
    )

    trust_output = manifest['outputs']['final_trust']
    if trust_output:
        print_info(f"Trust render: {Colors.CYAN}{trust_output}{Colors.RESET}")
    else:
        print_warning("Trust render unavailable; see trust_render_manifest.json")

    compare = summary.get('compare', {})
    if compare.get('enabled'):
        print_info(
            f"Compare: {compare['changed_parts_total']} changed parts, "
            f"{compare['changed_operations_total']} changed operations"
        )


def cmd_debug(args):
    """Build a machine-readable debug bundle for AI/debug workflows."""
    from .debug_bundle import create_debug_bundle

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    bundle_dir = _resolve_debug_bundle_path(input_file, args.bundle)

    try:
        manifest = create_debug_bundle(
            input_file,
            bundle_dir=bundle_dir,
            validate_schema=args.validate_schema,
            include_trust_render=not args.no_trust_render,
            compare_bundle_dir=args.compare,
        )
        _print_debug_bundle_summary(manifest, bundle_dir)
        if args.json:
            print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    except Exception as e:
        print_error(f"Debug bundle failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


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
  tiacad debug examples/bracket.yaml --bundle out/

Note: 3MF is the recommended format for 3D printing (multi-material, compact, modern).
      STL is supported for legacy compatibility.

For more information: https://github.com/scottsen/tiacad
        """
    )

    parser.add_argument('--version', action='version', version=f'TiaCAD {__version__}')
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
    check_parser.add_argument(
        '--contract', action='store_true',
        help="Also check the file's embedded expect: block against the built geometry"
    )
    check_parser.set_defaults(func=cmd_check)

    # Verify command
    verify_parser = subparsers.add_parser(
        'verify',
        help="Evaluate a model's embedded expect: contract (CI-friendly; see also 'check --contract')"
    )
    verify_parser.add_argument('input', help='Input YAML file')
    verify_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with traceback on error')
    verify_parser.add_argument('--json', action='store_true', help='Print machine-readable result JSON to stdout')
    verify_parser.set_defaults(func=cmd_verify)

    # Audit command
    audit_parser = subparsers.add_parser(
        'audit',
        help='Audit multiple files: build each, report final-part dimensions and flag failures'
    )
    audit_parser.add_argument('files', nargs='+', help='YAML file(s) to audit (supports glob patterns)')
    audit_parser.add_argument('-v', '--verbose', action='store_true', help='Show full tracebacks on failure')
    audit_parser.add_argument(
        '--write-contract', action='store_true',
        help='Seed an expect: block per file from its current build, for human review (does not modify files)'
    )
    audit_parser.set_defaults(func=cmd_audit)

    # Watch command
    watch_parser = subparsers.add_parser(
        'watch',
        help='Watch a file and rebuild on each save (incremental — reuses cached geometry)'
    )
    watch_parser.add_argument('input', help='Input YAML file to watch')
    watch_parser.add_argument(
        '--export', '-e', metavar='PATH',
        help='Auto-export final part to STL/3MF/STEP on each successful rebuild'
    )
    watch_parser.set_defaults(func=cmd_watch)

    # Debug command
    debug_parser = subparsers.add_parser(
        'debug',
        help='Build an AI/debug bundle with resolved model, summaries, validation, and trust render'
    )
    debug_parser.add_argument('input', help='Input YAML file')
    debug_parser.add_argument(
        '--bundle', '-b',
        help='Output directory for bundle artifacts (default: INPUT stem + .tiacad-debug)'
    )
    debug_parser.add_argument('--json', action='store_true', help='Print manifest JSON to stdout')
    debug_parser.add_argument('--validate-schema', action='store_true', help='Enable JSON schema validation')
    debug_parser.add_argument(
        '--no-trust-render',
        action='store_true',
        help='Skip trust-render generation in the debug bundle'
    )
    debug_parser.add_argument(
        '--compare',
        help='Compare against a previous debug bundle directory and emit compare_report.json'
    )
    debug_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with traceback')
    debug_parser.set_defaults(func=cmd_debug)

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
