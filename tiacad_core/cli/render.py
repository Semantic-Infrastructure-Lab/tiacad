"""`tiacad render` — write the trust-render PNG for a file without a full debug bundle."""

import traceback
from pathlib import Path

from .output import Colors, print_error, print_info, print_success


def _resolve_render_output_path(input_file: Path, output_arg: str | None) -> Path:
    """Resolve the PNG output path for `tiacad render`."""
    return Path(output_arg).resolve() if output_arg else input_file.with_name(f"{input_file.stem}_trust.png").resolve()


def cmd_render(args):
    """Render a file's trust-check PNG (8-view: iso/x-ray/orthographic) to disk."""
    from ..parser.tiacad_parser import TiaCADParser
    from ..validation.assembly_validator import AssemblyValidator
    from ..visual.trust_renderer import render_trust

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    output_path = _resolve_render_output_path(input_file, args.output)

    try:
        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema)
        issues = AssemblyValidator().validate_document(doc).issues
        written_path = render_trust(doc, str(output_path), title=input_file.stem, issues=issues)
        print_success(f"Trust render written to {Colors.CYAN}{written_path}{Colors.RESET}")
        return 0
    except Exception as e:
        print_error(f"Render failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1
