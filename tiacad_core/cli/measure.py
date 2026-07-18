"""`tiacad measure` — distance/angle/alignment between two named spatial references."""

import json
import traceback
from pathlib import Path

from .output import Colors, print_error, print_header, print_warning


def _print_measure_result(result: dict) -> None:
    print(f"  distance:  {result['distance']:.4f}")
    if 'angle_deg' in result:
        print(f"  angle:     {result['angle_deg']:.4f} deg")
        alignment = result['alignment']
        status = f"{Colors.GREEN}yes{Colors.RESET}" if alignment['aligned'] else f"{Colors.YELLOW}no{Colors.RESET}"
        print(f"  aligned:   {status}  (parallel={alignment['parallel']}, lateral_offset={alignment['lateral_offset']:.4f})")
    else:
        print_warning("angle/alignment skipped: one or both references have no orientation (bare point)")


def cmd_measure(args):
    """
    Measure distance, angle, and coaxial alignment between two named spatial
    references in a TiaCAD file (e.g. `base.face_top`, `bracket.center`).

    Angle and alignment are only reported when both references carry an
    orientation vector (faces, axes, edges) — a bare point has none.
    """
    from ..parser.tiacad_parser import TiaCADParser
    from ..spatial_resolver import SpatialResolver
    from ..testing.measurements import distance_between_refs, angle_between_refs, check_alignment

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    try:
        doc = TiaCADParser.parse_file(str(input_file))
        resolver = SpatialResolver(doc.parts, doc.references or {})
        ref1 = resolver.resolve(args.ref1)
        ref2 = resolver.resolve(args.ref2)
    except Exception as e:
        print_error(f"Failed to resolve references: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    result = {
        'ref1': args.ref1,
        'ref2': args.ref2,
        'distance': distance_between_refs(ref1, ref2),
    }
    if ref1.orientation is not None and ref2.orientation is not None:
        result['angle_deg'] = angle_between_refs(ref1, ref2)
        result['alignment'] = check_alignment(ref1, ref2)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_header(f"\n{args.ref1}  <->  {args.ref2}")
        _print_measure_result(result)

    return 0
