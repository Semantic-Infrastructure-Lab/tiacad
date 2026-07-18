"""`tiacad validate-geometry` — check that built geometry is printable."""

import tempfile
import time
import traceback
from pathlib import Path

from ._common import _pick_part_to_validate
from .output import Colors, print_error, print_header, print_info, print_success, print_warning


def _collect_geometry_issues(stats: dict, components, args) -> list:
    """Return a list of human-readable issue strings for the given mesh stats."""
    issues = []
    if stats['components'] > 1:
        issues.append(
            f"❌ {stats['components']} disconnected parts (expected 1 for printable model)"
        )
        if args.verbose:
            for i, comp in enumerate(components[:5]):
                issues.append(
                    f"   Component {i+1}: {len(comp.vertices)} vertices, {len(comp.faces)} faces"
                )
            if len(components) > 5:
                issues.append(f"   ... and {len(components) - 5} more")
    if not stats['watertight']:
        issues.append("❌ Mesh not watertight (will cause slicing errors)")
    if stats['volume'] <= 0:
        issues.append(f"❌ Invalid volume: {stats['volume']:.2f} mm³")
    if stats['vertices'] == 0:
        issues.append("❌ Empty mesh (no vertices)")
    if stats['faces'] == 0:
        issues.append("❌ No faces")
    return issues


def _print_geometry_outcome(stats: dict, issues: list, parse_time: float, export_time: float) -> int:
    """Print geometry stats table and outcome. Returns exit code."""
    print()
    print_header("📊 Geometry Analysis")
    print()
    print(f"  Vertices:    {stats['vertices']:,}")
    print(f"  Faces:       {stats['faces']:,}")
    print(f"  Volume:      {stats['volume']:.2f} mm³")
    print(f"  Watertight:  {'✅ Yes' if stats['watertight'] else '❌ No'}")
    print(f"  Components:  {stats['components']}")
    print()

    if not issues:
        print_success("✅ Geometry is valid and printable")
        print()
        print_info(f"Parse time:  {parse_time:.2f}s")
        print_info(f"Export time: {export_time:.2f}s")
        return 0
    else:
        print_error("❌ Geometry validation failed:")
        print()
        for issue in issues:
            print(f"  {issue}")
        print()
        print_warning("💡 Tip: For union operations, ensure parts actually overlap")
        print()
        return 1


def cmd_validate_geometry(args):
    """
    Validate geometry of built parts for 3D printing.

    Checks:
    - Single connected component (union operations actually merge)
    - Watertight meshes (no holes or gaps)
    - Positive volumes
    - No degenerate faces
    """
    from ..backend_support import require_cadquery_part
    from ..parser.tiacad_parser import TiaCADParser

    try:
        import trimesh
    except ImportError:
        print_error("trimesh library required for geometry validation")
        print_info("Install with: pip install trimesh")
        return 1

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    print_info(f"Validating {Colors.CYAN}{input_file.name}{Colors.RESET}")
    print()

    try:
        start_time = time.time()
        doc = TiaCADParser.parse_file(str(input_file))
        parse_time = time.time() - start_time

        part_name = _pick_part_to_validate(args, doc)
        if part_name is None:
            return 1

        print_info(f"Validating part: {Colors.CYAN}{part_name}{Colors.RESET}")
        part = doc.parts.get(part_name)
        require_cadquery_part(part, "Geometry validation")

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            export_start = time.time()
            part.geometry.val().exportStl(str(tmp_path))
            export_time = time.time() - export_start

            mesh = trimesh.load(str(tmp_path))
            components = mesh.split(only_watertight=False)
            stats = {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'volume': mesh.volume,
                'watertight': mesh.is_watertight,
                'components': len(components),
            }
            issues = _collect_geometry_issues(stats, components, args)
            return _print_geometry_outcome(stats, issues, parse_time, export_time)

        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1
