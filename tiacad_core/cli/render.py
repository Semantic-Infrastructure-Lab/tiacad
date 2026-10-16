"""`tiacad render` — write the trust-render PNG for a file without a full debug bundle."""

import traceback
from pathlib import Path

from .output import Colors, print_error, print_info, print_success, print_warning


def _resolve_render_output_path(input_file: Path, output_arg: str | None, suffix: str = "_trust") -> Path:
    """Resolve the PNG output path for `tiacad render`."""
    return Path(output_arg).resolve() if output_arg else input_file.with_name(f"{input_file.stem}{suffix}.png").resolve()


def _render_section(args, input_file: Path) -> int:
    """Handle `tiacad render --section AXIS=VALUE`: write one capped cutaway PNG."""
    from ..parser.tiacad_parser import TiaCADParser
    from ..visual.trust_renderer import parse_section_spec, render_section

    try:
        axis, value = parse_section_spec(args.section)
        output_path = _resolve_render_output_path(input_file, args.output, suffix="_section")
        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema)
        written_path = render_section(doc, str(output_path), axis, value, title=input_file.stem)
        print_success(f"Section render written to {Colors.CYAN}{written_path}{Colors.RESET}")
        return 0
    except Exception as e:
        print_error(f"Render failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_render(args):
    """Render a file's trust-check PNG (8-view: iso/x-ray/orthographic) to disk."""
    from ..parser.tiacad_parser import TiaCADParser
    from ..validation.assembly_validator import AssemblyValidator
    from ..visual.trust_renderer import render_trust

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    if getattr(args, "section", None):
        return _render_section(args, input_file)

    output_path = _resolve_render_output_path(input_file, args.output)

    try:
        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema)
        report = AssemblyValidator().validate_document(doc)
        written_path = render_trust(
            doc, str(output_path), title=input_file.stem,
            issues=None if getattr(args, "no_markers", False) else report.issues,
        )
        print_success(f"Trust render written to {Colors.CYAN}{written_path}{Colors.RESET}")

        status = "passed" if report.passed else "failed"
        summary = (
            f"Validation {status}: {report.error_count} errors, "
            f"{report.warning_count} warnings, {report.info_count} info"
        )
        if report.passed:
            print_info(summary)
        else:
            print_warning(f"{summary} — see annotated markers in the render, or run `tiacad debug` for detail")

        return 0
    except Exception as e:
        print_error(f"Render failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1
