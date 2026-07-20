"""
TiaCAD Command-Line Interface

Professional CLI for TiaCAD with subcommands, progress indicators, and color output.

Usage:
    tiacad build examples/plate.yaml --output plate.stl
    tiacad validate examples/*.yaml
    tiacad info examples/bracket.yaml

Author: TIA
Version: 3.1.1

Each subcommand lives in its own module (build.py, check.py, audit.py, ...);
this file only wires them into argparse (parser.py) and exposes `main`.
Names are re-exported here for backward compatibility with existing imports
and tests (`from tiacad_core.cli import cmd_build`, etc).
"""

import sys

from ._common import (
    _format_parameter_summary,
    _get_default_part_name,
    _get_part_display_type,
    _measure_part_dimensions,
    _pick_part_to_validate,
    _print_file_errors,
    _resolve_file_list,
    _visible_parts,
)
from .output import Colors, ProgressBar, print_error, print_header, print_info, print_success, print_warning
from .parser import create_parser

from .build import (
    _export_document,
    _print_build_failure,
    _print_build_stats,
    _print_build_success,
    _resolve_build_output,
    _show_dep_graph,
    cmd_build,
)
from .watch import (
    _format_watch_rebuild_line,
    _make_watch_rebuild_callback,
    _print_watch_start,
    _resolve_watch_export_path,
    cmd_watch,
)
from .validate import cmd_validate
from .info import (
    _print_info_report,
    _print_info_statistics,
    _print_key_value_section,
    _print_operation_section,
    _print_part_section,
    cmd_info,
)
from .check import _build_check_rows, _print_check_rows, cmd_check
from .validate_geometry import _collect_geometry_issues, _print_geometry_outcome, cmd_validate_geometry
from .measure import _print_measure_result, cmd_measure
from .verify import cmd_verify
from .audit import (
    _cmd_audit_write_contract,
    _empty_audit_result,
    _format_audit_dims,
    _format_audit_status,
    _measure_audit_final_part,
    _print_audit_results,
    _print_audit_summary,
    _audit_one_file,
    cmd_audit,
)
from .debug import _print_debug_bundle_summary, _resolve_debug_bundle_path, cmd_debug
from .render import _resolve_render_output_path, cmd_render

__all__ = [
    'Colors', 'ProgressBar',
    'print_success', 'print_error', 'print_warning', 'print_info', 'print_header',
    'create_parser', 'main',
    'cmd_build', 'cmd_validate', 'cmd_info', 'cmd_validate_geometry', 'cmd_check',
    'cmd_measure', 'cmd_verify', 'cmd_audit', 'cmd_watch', 'cmd_debug', 'cmd_render',
]


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
