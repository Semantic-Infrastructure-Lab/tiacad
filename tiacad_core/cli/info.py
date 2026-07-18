"""`tiacad info` — show metadata, parameters, parts, and operations for a file."""

import traceback
from pathlib import Path

from ._common import _get_part_display_type, _visible_parts
from .output import Colors, print_error, print_header


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


def cmd_info(args):
    """Show information about a TiaCAD file"""
    from ..parser.tiacad_parser import TiaCADParser

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
