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
