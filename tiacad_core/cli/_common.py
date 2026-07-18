"""Helpers shared by 2+ CLI subcommands (part lookup, file globs, measurement)."""

from pathlib import Path

from .output import Colors, print_error, print_warning


def _resolve_file_list(patterns):
    """Expand a list of file paths / glob patterns into resolved Path objects."""
    files = []
    for pattern in patterns:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
        elif '*' in pattern or '?' in pattern:
            files.extend(Path('.').glob(pattern))
        else:
            print_warning(f"No files found matching: {pattern}")
    return files


def _print_file_errors(file: Path, errors) -> None:
    """Print validation errors for a single file."""
    print_error(f"{file}")
    for error in errors:
        print(f"  {Colors.RED}└─{Colors.RESET} {error}")


def _get_default_part_name(doc):
    """Pick the default/final part for single-part inspection commands."""
    if doc.operations:
        return list(doc.operations.keys())[-1]
    parts = doc.parts.list_parts()
    if not parts:
        return None
    return parts[0]


def _visible_parts(doc):
    """Return user-visible parts, excluding internal placeholders."""
    return [part_name for part_name in doc.parts.list_parts() if not part_name.startswith('_')]


def _get_part_display_type(part) -> str:
    """Return the best available type label for a part."""
    return (
        part.metadata.get('primitive_type')
        or part.metadata.get('operation_type')
        or part.metadata.get('source')
        or '?'
    )


def _measure_part_dimensions(part):
    """Measure a part and return width/height/depth/volume."""
    from ..testing.dimensions import get_dimensions

    dims = get_dimensions(part)
    return {
        'width': dims['width'],
        'height': dims['height'],
        'depth': dims['depth'],
        'volume': dims['volume'],
    }


def _pick_part_to_validate(args, doc) -> str:
    """Determine which part to validate: explicit arg, last operation, or first part."""
    if args.part:
        return args.part
    part_name = _get_default_part_name(doc)
    if part_name is None:
        print_error("No parts found in document")
        return None
    return part_name


def _format_parameter_summary(parameters: dict) -> str:
    """Format resolved parameters for compact CLI display."""
    pairs = [f"{Colors.CYAN}{key}{Colors.RESET}={value}" for key, value in parameters.items()]
    return "  " + "  ".join(pairs)
