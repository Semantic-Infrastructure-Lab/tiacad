"""`tiacad debug` — build a machine-readable debug bundle for AI/debug workflows."""

import json
import traceback
from pathlib import Path

from .output import Colors, print_error, print_info, print_success, print_warning


def _resolve_debug_bundle_path(input_file: Path, bundle_arg: str | None) -> Path:
    """Resolve the bundle output directory for `tiacad debug`."""
    from ..debug_bundle import default_debug_bundle_dir

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
    from ..debug_bundle import create_debug_bundle

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
