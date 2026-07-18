"""`tiacad audit` — build multiple files and report dimensions/failures across all."""

import sys
import time
import traceback
from pathlib import Path

from ._common import _get_default_part_name, _measure_part_dimensions, _resolve_file_list
from .output import Colors, print_error, print_header, print_success


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
    from ..testing.dimensions import DimensionError

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


def _audit_one_file(input_file: Path, verbose: bool):
    """
    Build a single file and return a result dict for the audit table.
    Keys: name, status ('ok'/'fail'/'warn'), dims, volume, parts_count,
          final_part, error, elapsed.
    """
    from ..parser.tiacad_parser import TiaCADParser

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
    from ..parser.tiacad_parser import TiaCADParser
    from ..testing.contracts import write_contract_yaml

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
