"""`tiacad check` — build a file and report dimensions/volume for every part."""

import traceback
import time
from pathlib import Path

from ._common import (
    _format_parameter_summary,
    _get_default_part_name,
    _get_part_display_type,
    _measure_part_dimensions,
    _visible_parts,
)
from .output import Colors, print_error, print_header, print_success, print_warning


def _build_check_rows(doc):
    """Collect per-part rows for `tiacad check`."""
    from ..testing.dimensions import DimensionError

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
    from ..parser.tiacad_parser import TiaCADParser

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
            from ..testing.contracts import ContractError, check_contract
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
