"""`tiacad build` — parse a TiaCAD YAML file and export it to STL/3MF/STEP."""

import time
import traceback
from pathlib import Path

from .output import Colors, print_error, print_header, print_info, print_success


def _show_dep_graph(args, doc, input_file: Path) -> None:
    """Print dependency graph output if --show-deps was requested."""
    if not (args.show_deps and doc.graph):
        return
    print()
    from ..dag import GraphVisualizer
    if args.show_deps in ('text', 'both'):
        GraphVisualizer.show_stats(doc.graph)
    if args.show_deps in ('dot', 'both'):
        dot_path = input_file.stem + '_deps.dot'
        GraphVisualizer.to_dot(doc.graph, str(dot_path))
        print_success(f"Dependency graph written to: {Colors.CYAN}{dot_path}{Colors.RESET}")
        print_info(f"Generate image: dot -Tpng {dot_path} -o graph.png")
        print()


def _resolve_build_output(input_file: Path, output_arg: str | None) -> Path | None:
    """Resolve and validate the build output path."""
    output_file = Path(output_arg) if output_arg else input_file.with_suffix('.3mf')
    output_ext = output_file.suffix.lower()
    if output_ext not in ['.stl', '.3mf', '.step']:
        print_error(f"Unsupported output format: {output_ext}")
        print_info("Supported formats: .stl, .3mf, .step")
        return None
    return output_file


def _export_document(doc, output_file: Path, part_name: str | None) -> None:
    """Export a parsed document to the requested format."""
    output_ext = output_file.suffix.lower()
    if output_ext == '.stl':
        doc.export_stl(str(output_file), part_name=part_name)
    elif output_ext == '.3mf':
        doc.export_3mf(str(output_file), part_name=part_name)
    elif output_ext == '.step':
        doc.export_step(str(output_file), part_name=part_name)


def _print_build_stats(doc) -> None:
    """Print post-build document statistics."""
    print_header("\n📊 Statistics:")
    print(f"  Parts: {len(doc.parts.list_parts())}")
    print(f"  Parameters: {len(doc.parameters)}")
    print(f"  Operations: {len(doc.operations)}")


def _print_build_success(output_file: Path, parse_time: float, export_time: float, total_time: float) -> None:
    """Print a successful build summary."""
    print_success(f"Parsed in {parse_time:.2f}s")
    print_success(f"Exported in {export_time:.2f}s")
    print_success(f"Total time: {total_time:.2f}s")
    print_success(f"Output: {output_file}")


def _print_build_failure(error: Exception, doc, verbose: bool) -> None:
    """Print build failure output consistently."""
    print_error(f"Build failed: {str(error)}")

    if hasattr(error, 'with_context') and doc and hasattr(doc, 'yaml_string') and doc.yaml_string:
        print()
        print(error.with_context(doc.yaml_string))

    if verbose:
        print("\n" + Colors.GRAY + "Traceback:" + Colors.RESET)
        traceback.print_exc()


def cmd_build(args):
    """Build a TiaCAD YAML file to 3MF/STL/STEP (defaults to 3MF)"""
    from ..parser.tiacad_parser import TiaCADParser

    input_file = Path(args.input)

    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    output_file = _resolve_build_output(input_file, args.output)
    if output_file is None:
        return 1

    doc = None
    try:
        build_graph = (args.show_deps is not None)
        print_info(f"Building {Colors.CYAN}{input_file}{Colors.RESET}")
        start_time = time.time()

        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema, build_graph=build_graph)
        parse_time = time.time() - start_time

        _show_dep_graph(args, doc, input_file)

        print_info(f"Exporting to {Colors.CYAN}{output_file}{Colors.RESET}")
        export_start = time.time()
        _export_document(doc, output_file, args.part)
        export_time = time.time() - export_start

        total_time = time.time() - start_time
        _print_build_success(output_file, parse_time, export_time, total_time)

        if args.stats:
            _print_build_stats(doc)

        return 0

    except Exception as e:
        _print_build_failure(e, doc, args.verbose)
        return 1
