"""`tiacad section`: list where a part is solid along a plane's scan lines or one line."""

import json
import traceback
from pathlib import Path

from ._common import _echo_overrides, _parse_set_args, _pick_part_to_validate
from .output import Colors, print_error, print_header, print_info, print_warning


def _print_plane_report(report, part_name: str) -> None:
    axes = "XYZ"
    print_header(f"Section {axes[report.axis].lower()}={report.value:g}  (part {part_name}, scan step {report.step:g} mm)")
    print()
    print(f"  {report.lines_hit} of {report.lines_cast} scan lines cross material")
    for scan_axis, rows in report.scans.items():
        print()
        print(f"  Along {axes[scan_axis]} (solid interval lengths):")
        if not rows:
            print("    (no material)")
            continue
        print(f"    {'thickness mm':<14}{'lines':>7}   first seen at (x, y, z)")
        for row in rows:
            x, y, z = row.first_at
            print(f"    {row.thickness:<14.2f}{row.lines:>7}   ({x:.2f}, {y:.2f}, {z:.2f})")
    print()
    print_info("Axis-aligned interval lengths: exact for walls/floors perpendicular to a scan axis, over-reports oblique walls.")


def cmd_section(args):
    """Report material intervals / thicknesses of a part at a plane (--plane) or along one line (--line)."""
    from ..parser.tiacad_parser import TiaCADParser
    from ..validation.section_probe import (
        parse_line_spec, parse_plane_spec, part_to_mesh, probe_line, section_thicknesses,
    )

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1
    if bool(args.plane) == bool(args.line):
        print_error("Give exactly one of --plane AXIS=VALUE or --line AXIS@A=V,B=V")
        return 1
    if args.step <= 0:
        print_error("--step must be positive")
        return 1

    try:
        overrides = _parse_set_args(getattr(args, 'set', None))
        plane = parse_plane_spec(args.plane) if args.plane else None
        line = parse_line_spec(args.line) if args.line else None
        _echo_overrides(overrides)
        doc = TiaCADParser.parse_file(str(input_file), param_overrides=overrides)
        part_name = _pick_part_to_validate(args, doc)
        if part_name is None:
            return 1
        mesh = part_to_mesh(doc.parts.get(part_name))

        if plane:
            report = section_thicknesses(mesh, plane[0], plane[1], args.step)
            if report.lines_hit == 0:
                print_warning(f"Plane {args.plane} does not cut any material of '{part_name}'")
            if args.json:
                print(json.dumps({
                    'file': str(input_file), 'part': part_name, 'plane': args.plane, 'step': args.step,
                    'scans': {
                        "XYZ"[a]: [{'thickness': r.thickness, 'lines': r.lines, 'first_at': list(r.first_at)} for r in rows]
                        for a, rows in report.scans.items()
                    },
                }, indent=2, sort_keys=True))
            else:
                _print_plane_report(report, part_name)
            return 0 if report.lines_hit else 1

        axis, fixed = line
        intervals = probe_line(mesh, axis, fixed)
        if args.json:
            print(json.dumps({'file': str(input_file), 'part': part_name, 'line': args.line,
                              'intervals': [[a, b] for a, b in intervals]}, indent=2, sort_keys=True))
        else:
            print_header(f"Line {args.line}  (part {part_name})")
            print()
            if not intervals:
                print("  (no material along this line)")
            for t0, t1 in intervals:
                print(f"  solid {t0:.3f} -> {t1:.3f}   thickness {t1 - t0:.3f} mm")
            print()
        return 0 if intervals else 1
    except Exception as e:
        print_error(f"Section failed: {e}")
        if getattr(args, 'verbose', False):
            traceback.print_exc()
        return 1
