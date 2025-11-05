"""
TiaCAD Command-Line Interface

Professional CLI for TiaCAD with subcommands, progress indicators, and color output.

Usage:
    tiacad build examples/plate.yaml --output plate.stl
    tiacad validate examples/*.yaml
    tiacad info examples/bracket.yaml

Author: TIA
Version: 0.1.0 (QW4 Enhanced CLI)
"""

import argparse
import sys
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


def cmd_build(args):
    """Build a TiaCAD YAML file to 3MF/STL/STEP (defaults to 3MF)"""
    from .parser.tiacad_parser import TiaCADParser

    input_file = Path(args.input)

    # Validate input file exists
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Auto-generate output filename - default to 3MF (modern standard)
        output_file = input_file.with_suffix('.3mf')

    # Determine format from extension
    output_ext = output_file.suffix.lower()
    if output_ext not in ['.stl', '.3mf', '.step']:
        print_error(f"Unsupported output format: {output_ext}")
        print_info("Supported formats: .stl, .3mf, .step")
        return 1

    try:
        # Parse YAML
        print_info(f"Building {Colors.CYAN}{input_file}{Colors.RESET}")
        start_time = time.time()

        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema)

        parse_time = time.time() - start_time
        print_success(f"Parsed in {parse_time:.2f}s")

        # Export
        print_info(f"Exporting to {Colors.CYAN}{output_file}{Colors.RESET}")
        export_start = time.time()

        if output_ext == '.stl':
            doc.export_stl(str(output_file), part_name=args.part)
        elif output_ext == '.3mf':
            doc.export_3mf(str(output_file))
        elif output_ext == '.step':
            doc.export_step(str(output_file), part_name=args.part)

        export_time = time.time() - export_start
        total_time = time.time() - start_time

        print_success(f"Exported in {export_time:.2f}s")
        print_success(f"Total time: {total_time:.2f}s")
        print_success(f"Output: {output_file}")

        # Show statistics
        if args.stats:
            print_header("\n📊 Statistics:")
            print(f"  Parts: {len(doc.parts.list_parts())}")
            print(f"  Parameters: {len(doc.parameters)}")
            print(f"  Operations: {len(doc.operations)}")

        return 0

    except Exception as e:
        print_error(f"Build failed: {str(e)}")

        # Show enhanced error context if available
        if hasattr(e, 'with_context') and doc and hasattr(doc, 'yaml_string') and doc.yaml_string:
            print()
            print(e.with_context(doc.yaml_string))

        if args.verbose:
            import traceback
            print("\n" + Colors.GRAY + "Traceback:" + Colors.RESET)
            traceback.print_exc()

        return 1


def cmd_validate(args):
    """Validate TiaCAD YAML files without building geometry"""
    from .parser.tiacad_parser import TiaCADParser

    # Expand glob patterns
    files = []
    for pattern in args.files:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
        elif '*' in pattern or '?' in pattern:
            # Glob pattern
            files.extend(Path('.').glob(pattern))
        else:
            print_warning(f"No files found matching: {pattern}")

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
                print_error(f"{file}")
                for error in errors:
                    print(f"  {Colors.RED}└─{Colors.RESET} {error}")
                invalid_count += 1

        except Exception as e:
            print_error(f"{file}")
            print(f"  {Colors.RED}└─{Colors.RESET} {str(e)}")
            invalid_count += 1

    # Summary
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

        # Header
        print_header(f"\n📄 {input_file.name}")
        print()

        # Metadata
        if doc.metadata:
            print_header("Metadata:")
            for key, value in doc.metadata.items():
                print(f"  {Colors.CYAN}{key}:{Colors.RESET} {value}")
            print()

        # Parameters
        if doc.parameters:
            print_header(f"Parameters ({len(doc.parameters)}):")
            for name, value in doc.parameters.items():
                print(f"  {Colors.CYAN}{name}:{Colors.RESET} {value}")
            print()

        # Parts
        parts = doc.parts.list_parts()
        print_header(f"Parts ({len(parts)}):")
        for part_name in parts:
            part = doc.parts.get(part_name)
            prim_type = part.metadata.get('primitive_type', 'unknown')
            print(f"  {Colors.GREEN}•{Colors.RESET} {part_name} ({prim_type})")
        print()

        # Operations
        if doc.operations:
            print_header(f"Operations ({len(doc.operations)}):")
            for op_name, op_def in doc.operations.items():
                op_type = op_def.get('type', 'unknown')
                print(f"  {Colors.YELLOW}•{Colors.RESET} {op_name} ({op_type})")
            print()

        # Quick stats
        print_header("Statistics:")
        print(f"  Total parts: {len(parts)}")
        print(f"  Parameters: {len(doc.parameters)}")
        print(f"  Operations: {len(doc.operations)}")

        return 0

    except Exception as e:
        print_error(f"Failed to read file: {str(e)}")

        if args.verbose:
            import traceback
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

For more information: https://github.com/yourusername/tiacad
        """
    )

    parser.add_argument('--version', action='version', version='TiaCAD 0.1.0')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build a TiaCAD file to 3MF/STL/STEP (modern 3MF format recommended)')
    build_parser.add_argument('input', help='Input YAML file')
    build_parser.add_argument('-o', '--output', help='Output file (default: same name with .3mf extension - use .stl or .step to override)')
    build_parser.add_argument('-p', '--part', help='Specific part to export (default: last operation)')
    build_parser.add_argument('-s', '--stats', action='store_true', help='Show build statistics')
    build_parser.add_argument('--validate-schema', action='store_true', help='Enable JSON schema validation')
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

    return parser


def main(argv=None):
    """Main entry point for CLI"""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Run the command
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
