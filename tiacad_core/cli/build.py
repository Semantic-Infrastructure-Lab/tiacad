"""`tiacad build` — parse a TiaCAD YAML file and export it to STL/3MF/STEP."""

import time
import traceback
from pathlib import Path

from ._common import _echo_overrides, _override_tag, _parse_set_args
from .output import Colors, print_error, print_header, print_info, print_success, print_warning


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


def _resolve_build_output(input_file: Path, output_arg: str | None, tag: str = "") -> Path | None:
    """Resolve and validate the build output path (tag keeps a --set variant off the default file)."""
    output_file = Path(output_arg) if output_arg else input_file.with_name(f"{input_file.stem}{tag}.3mf")
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


def _check_stl_watertight(output_file: Path) -> None:
    """
    Best-effort post-export watertightness check for STL output.

    STL is the format most directly consumed by slicers, and a non-watertight
    mesh silently produces slicing errors or bad prints downstream with no
    signal from `tiacad build` itself (see KNOWN_LIMITATIONS.md #18 / TCAD-BUG-3
    — a revolve profile touching its own axis at a tip is a common way to
    trigger this). A pole-touching revolve is usually not a real defect: the
    B-Rep solid is valid, and OCCT's mesher just leaves a degenerate,
    zero-volume shard at the pinch point (KNOWN_LIMITATIONS.md #19), so this
    strips that kind of artifact via `strip_degenerate_shards` and re-exports
    the cleaned mesh before deciding whether to warn. This check is advisory
    only: never raises, never fails the build, and any import/read error is
    swallowed so a missing `trimesh` or an exotic mesh trimesh can't parse
    doesn't turn a successful build into a failure. `tiacad validate-geometry`
    remains the authoritative, detailed check (components, volume, vertex/face
    counts).
    """
    try:
        import trimesh
        from ..utils.mesh_repair import strip_degenerate_shards

        mesh = trimesh.load(str(output_file))
        if mesh.is_watertight:
            return

        cleaned, changed = strip_degenerate_shards(mesh)
        if changed:
            cleaned.export(str(output_file))
            mesh = cleaned

        if mesh.is_watertight:
            if changed:
                print_info(
                    "Removed degenerate pole-tessellation shard(s); re-exported "
                    "STL is watertight (KNOWN_LIMITATIONS.md #19)."
                )
            return

        print_warning(
            "Mesh is not watertight — may cause slicer errors or bad prints. "
            "Run `tiacad validate-geometry` for details."
        )
    except Exception:
        pass


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

    try:
        overrides = _parse_set_args(getattr(args, 'set', None))
    except ValueError as e:
        print_error(str(e))
        return 1

    output_file = _resolve_build_output(input_file, args.output, _override_tag(overrides))
    if output_file is None:
        return 1

    doc = None
    try:
        build_graph = (args.show_deps is not None)
        print_info(f"Building {Colors.CYAN}{input_file}{Colors.RESET}")
        _echo_overrides(overrides)
        start_time = time.time()

        doc = TiaCADParser.parse_file(str(input_file), validate_schema=args.validate_schema, build_graph=build_graph,
                                     param_overrides=overrides)
        parse_time = time.time() - start_time

        _show_dep_graph(args, doc, input_file)

        print_info(f"Exporting to {Colors.CYAN}{output_file}{Colors.RESET}")
        export_start = time.time()
        _export_document(doc, output_file, args.part)
        export_time = time.time() - export_start

        total_time = time.time() - start_time
        _print_build_success(output_file, parse_time, export_time, total_time)

        if output_file.suffix.lower() == '.stl':
            _check_stl_watertight(output_file)

        if args.stats:
            _print_build_stats(doc)

        return 0

    except Exception as e:
        _print_build_failure(e, doc, args.verbose)
        return 1
