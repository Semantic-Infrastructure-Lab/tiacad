"""Material-interval probing of a triangle mesh: where is it solid along a line, and how thick?

Backs `tiacad section`. Lines are cast with a VTK cell locator (no rtree needed); hits are
sorted along the line and paired (enter, exit) to give solid intervals. Thickness here is the
*axis-aligned* interval length, which is exact for walls, floors and skins that are
perpendicular to a scan axis (the usual box-style printed features) and over-reports for
oblique walls.
"""

import tempfile
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_AXES = "xyz"
_HIT_MERGE_TOL = 1e-6      # mm: hits closer than this along a line are one tangent/edge hit
_ROUND = 2                 # thickness rounding (0.01 mm) when grouping scan results


def _is_axis(name: str) -> bool:
    return len(name) == 1 and name in _AXES  # '' is a substring of every string


def part_to_mesh(part):
    """Export a CadQuery part to a trimesh via STL, stripping degenerate pole shards."""
    import trimesh

    from ..backend_support import require_cadquery_part
    from ..utils.mesh_repair import strip_degenerate_shards

    require_cadquery_part(part, "Section probing")
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        part.geometry.val().exportStl(str(tmp_path))
        mesh = trimesh.load(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)
    mesh, _ = strip_degenerate_shards(mesh)
    return mesh


def parse_plane_spec(spec: str) -> Tuple[int, float]:
    """'y=79.5' -> (1, 79.5). Raises ValueError on a malformed spec."""
    axis, sep, raw = spec.partition('=')
    axis = axis.strip().lower()
    if not sep or not _is_axis(axis):
        raise ValueError(f"Invalid plane '{spec}': expected AXIS=VALUE with AXIS one of x, y, z (e.g. y=79.5)")
    try:
        return _AXES.index(axis), float(raw)
    except ValueError:
        raise ValueError(f"Invalid plane '{spec}': '{raw}' is not a number") from None


def parse_line_spec(spec: str) -> Tuple[int, Dict[int, float]]:
    """'x@y=79.5,z=25.4' -> (0, {1: 79.5, 2: 25.4}): scan along X at those other coordinates."""
    along, sep, rest = spec.partition('@')
    along = along.strip().lower()
    if not sep or not _is_axis(along):
        raise ValueError(f"Invalid line '{spec}': expected AXIS@A=VALUE,B=VALUE (e.g. x@y=79.5,z=25.4)")
    axis = _AXES.index(along)
    fixed: Dict[int, float] = {}
    for chunk in rest.split(','):
        name, eq, raw = chunk.partition('=')
        name = name.strip().lower()
        try:
            if not eq or not _is_axis(name):
                raise ValueError
            fixed[_AXES.index(name)] = float(raw)
        except ValueError:
            raise ValueError(f"Invalid line '{spec}': bad coordinate '{chunk}'") from None
    if axis in fixed or set(fixed) | {axis} != {0, 1, 2}:
        raise ValueError(f"Invalid line '{spec}': give the two coordinates other than {along}")
    return axis, fixed


@dataclass
class ThicknessRow:
    thickness: float
    lines: int
    first_at: Tuple[float, float, float]


@dataclass
class SectionReport:
    axis: int
    value: float
    step: float
    # scan axis index -> rows sorted by thickness ascending
    scans: Dict[int, List[ThicknessRow]] = field(default_factory=OrderedDict)
    lines_cast: int = 0
    lines_hit: int = 0


class SurfaceProbe:
    """Casts lines against a mesh and returns solid intervals."""

    def __init__(self, mesh):
        import pyvista as pv
        import vtk

        self._vtk = vtk
        self._mesh = mesh
        self._locator = vtk.vtkStaticCellLocator()
        self._locator.SetDataSet(pv.wrap(mesh))
        self._locator.BuildLocator()

    @property
    def bounds(self):
        return self._mesh.bounds  # [[xmin,ymin,zmin],[xmax,ymax,zmax]]

    def intervals(self, axis: int, fixed: Dict[int, float]) -> List[Tuple[float, float]]:
        """Solid (enter, exit) coordinates along `axis` for the line through `fixed` coords."""
        lo, hi = float(self.bounds[0][axis]) - 1.0, float(self.bounds[1][axis]) + 1.0
        start, end = [0.0] * 3, [0.0] * 3
        for a, v in fixed.items():
            start[a] = end[a] = v
        start[axis], end[axis] = lo, hi

        points = self._vtk.vtkPoints()
        ids = self._vtk.vtkIdList()
        self._locator.IntersectWithLine(start, end, 1e-9, points, ids)
        hits = sorted(points.GetPoint(i)[axis] for i in range(points.GetNumberOfPoints()))
        merged: List[float] = []
        for h in hits:
            if not merged or h - merged[-1] > _HIT_MERGE_TOL:
                merged.append(h)
        if len(merged) % 2:
            merged = merged[:-1]  # a tangent graze left an unpaired hit; drop it rather than guess
        return [(merged[i], merged[i + 1]) for i in range(0, len(merged), 2)]


def _scan_positions(lo: float, hi: float, step: float) -> List[float]:
    n = max(int((hi - lo) / step), 1)
    return [lo + (i + 0.5) * (hi - lo) / n for i in range(n)]


def section_thicknesses(mesh, axis: int, value: float, step: float = 1.0) -> SectionReport:
    """Scan the plane `axis=value` along both in-plane axes and group solid thicknesses.

    For each in-plane axis A, lines parallel to A are cast every ``step`` mm across the
    other in-plane axis B; every solid interval's length is rounded to 0.01 mm and counted.
    """
    probe = SurfaceProbe(mesh)
    report = SectionReport(axis=axis, value=value, step=step)
    in_plane = [a for a in range(3) if a != axis]

    for scan_axis in in_plane:
        other = next(a for a in in_plane if a != scan_axis)
        groups: Dict[float, ThicknessRow] = {}
        for pos in _scan_positions(float(probe.bounds[0][other]), float(probe.bounds[1][other]), step):
            report.lines_cast += 1
            found = probe.intervals(scan_axis, {axis: value, other: pos})
            if found:
                report.lines_hit += 1
            for t0, t1 in found:
                key = round(t1 - t0, _ROUND)
                if key <= 0:
                    continue
                row = groups.get(key)
                if row is None:
                    at = [0.0] * 3
                    at[axis], at[other], at[scan_axis] = value, pos, (t0 + t1) / 2
                    groups[key] = ThicknessRow(key, 1, tuple(at))
                else:
                    row.lines += 1
        report.scans[scan_axis] = sorted(groups.values(), key=lambda r: r.thickness)
    return report


def probe_line(mesh, axis: int, fixed: Dict[int, float]) -> List[Tuple[float, float]]:
    return SurfaceProbe(mesh).intervals(axis, fixed)
