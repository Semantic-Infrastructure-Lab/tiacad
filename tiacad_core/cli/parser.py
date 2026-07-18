"""argparse wiring for the `tiacad` CLI: one subparser per command."""

import argparse

from .. import __version__
from .audit import cmd_audit
from .build import cmd_build
from .check import cmd_check
from .debug import cmd_debug
from .info import cmd_info
from .measure import cmd_measure
from .validate import cmd_validate
from .validate_geometry import cmd_validate_geometry
from .verify import cmd_verify
from .watch import cmd_watch


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

For more information: https://github.com/Semantic-Infrastructure-Lab/tiacad
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

    # Measure command
    measure_parser = subparsers.add_parser(
        'measure',
        help='Measure distance, angle, and coaxial alignment between two named spatial references'
    )
    measure_parser.add_argument('input', help='Input YAML file')
    measure_parser.add_argument('ref1', help="First reference spec, e.g. 'base.face_top'")
    measure_parser.add_argument('ref2', help="Second reference spec, e.g. 'bracket.center'")
    measure_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output with traceback on error')
    measure_parser.add_argument('--json', action='store_true', help='Print machine-readable result JSON to stdout')
    measure_parser.set_defaults(func=cmd_measure)

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
