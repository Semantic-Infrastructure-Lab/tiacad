"""`tiacad validate` — validate TiaCAD YAML files without building geometry."""

from ._common import _print_file_errors, _resolve_file_list
from .output import Colors, print_error, print_header, print_success


def cmd_validate(args):
    """Validate TiaCAD YAML files without building geometry"""
    from ..parser.tiacad_parser import TiaCADParser

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
