"""Advisory 3D-print checks on a triangle mesh: build-volume fit, overhangs, wall thickness.

Pure mesh analysis (trimesh in, plain dataclasses out) behind `tiacad validate-geometry`.
Everything here is advisory: it reports what a slicer would care about, it never decides
that a model is invalid. Wall thickness is a *sampled* estimate (see ``min_wall_thickness``).
"""

import itertools
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

DEFAULT_OVERHANG_ANGLE = 45.0   # degrees from vertical; steeper-than-this faces need support
DEFAULT_MIN_WALL = 0.8          # mm; ~2 perimeters of a 0.4 mm nozzle
DEFAULT_WALL_SAMPLES = 20000
_BED_CONTACT_TOL = 1e-3         # mm above the lowest vertex that counts as "on the bed"
_FIT_EPS = 1e-6


def parse_bed_spec(spec: str) -> Tuple[float, float, float]:
    """'250x210x200' -> (250.0, 210.0, 200.0). Raises ValueError on anything else."""
    parts = spec.lower().replace(' ', '').split('x')
    try:
        dims = tuple(float(p) for p in parts)
    except ValueError:
        dims = ()
    if len(dims) != 3 or any(d <= 0 for d in dims):
        raise ValueError(f"--bed expects XxYxZ in mm with positive numbers, e.g. 250x210x200; got '{spec}'")
    return dims


@dataclass
class BedFit:
    fits: bool
    extents: Tuple[float, float, float]
    bed: Tuple[float, float, float]
    as_modeled: bool = False
    # model axes (indices into extents) assigned to bed X, Y, Z when it fits rotated
    axis_order: Optional[Tuple[int, int, int]] = None


@dataclass
class OverhangReport:
    angle: float
    area: float
    total_area: float

    @property
    def fraction(self) -> float:
        return self.area / self.total_area if self.total_area > 0 else 0.0


@dataclass
class WallReport:
    min_thickness: Optional[float]
    location: Optional[Tuple[float, float, float]]
    samples: int


def check_build_volume(mesh, bed: Tuple[float, float, float]) -> BedFit:
    """Does the mesh fit the bed as modeled, or in some axis-aligned orientation?"""
    extents = tuple(float(e) for e in mesh.extents)
    if all(extents[i] <= bed[i] + _FIT_EPS for i in range(3)):
        return BedFit(True, extents, bed, as_modeled=True, axis_order=(0, 1, 2))
    for order in itertools.permutations(range(3)):
        if all(extents[order[i]] <= bed[i] + _FIT_EPS for i in range(3)):
            return BedFit(True, extents, bed, as_modeled=False, axis_order=order)
    return BedFit(False, extents, bed)


def find_overhangs(mesh, angle: float = DEFAULT_OVERHANG_ANGLE) -> OverhangReport:
    """Area of downward faces overhanging more than ``angle`` degrees from vertical.

    +Z is up (the modeled orientation). A face with normal n overhangs by
    asin(-n_z) from the vertical; flat ceilings are 90 degrees. Faces resting on the
    bed (all vertices at the lowest Z) need no support and are excluded.
    """
    normals = mesh.face_normals
    areas = mesh.area_faces
    z_floor = mesh.bounds[0][2] + _BED_CONTACT_TOL
    on_bed = (mesh.triangles[:, :, 2] <= z_floor).all(axis=1)
    threshold = math.sin(math.radians(angle))
    needs_support = (-normals[:, 2] > threshold + _FIT_EPS) & ~on_bed
    return OverhangReport(angle=angle, area=float(areas[needs_support].sum()), total_area=float(areas.sum()))


def min_wall_thickness(mesh, samples: int = DEFAULT_WALL_SAMPLES, seed: int = 0) -> WallReport:
    """Estimate the thinnest wall by casting rays inward from sampled surface points.

    For each sample the ray runs against the surface normal; the distance to the first
    hit is the local thickness. This is a sampled estimate: a feature thinner than the
    sampling density can be missed, and it measures perpendicular thickness, so a thin
    sliver between non-parallel faces is under-reported near the edge. Rays that leave
    the mesh without a hit are ignored.
    """
    import pyvista as pv
    import trimesh
    import vtk

    points, face_idx = trimesh.sample.sample_surface(mesh, samples, seed=seed)
    normals = mesh.face_normals[face_idx]

    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(pv.wrap(mesh))
    locator.BuildLocator()

    reach = float(np.linalg.norm(mesh.extents)) + 1.0
    t, x, pcoords = vtk.mutable(0.0), [0.0] * 3, [0.0] * 3
    sub_id, cell_id = vtk.mutable(0), vtk.mutable(0)

    best: Optional[float] = None
    where: Optional[Tuple[float, float, float]] = None
    for p, n in zip(points, normals):
        start = p - n * 1e-3
        end = p - n * reach
        if locator.IntersectWithLine(start.tolist(), end.tolist(), 1e-6, t, x, pcoords, sub_id, cell_id):
            d = float(np.linalg.norm(np.array(x) - p))
            if best is None or d < best:
                best, where = d, (float(p[0]), float(p[1]), float(p[2]))
    return WallReport(min_thickness=best, location=where, samples=len(points))


def printability_warnings(
    mesh,
    bed: Optional[Tuple[float, float, float]] = None,
    min_wall: float = DEFAULT_MIN_WALL,
    overhang_angle: float = DEFAULT_OVERHANG_ANGLE,
) -> Tuple[List[str], List[str]]:
    """Return (info_lines, warning_lines) for the three checks."""
    info: List[str] = []
    warnings: List[str] = []

    if bed is not None:
        fit = check_build_volume(mesh, bed)
        ext = " x ".join(f"{e:.1f}" for e in fit.extents)
        bed_s = " x ".join(f"{b:g}" for b in fit.bed)
        if fit.fits and fit.as_modeled:
            info.append(f"Build volume: {ext} mm fits {bed_s} mm as modeled")
        elif fit.fits:
            axes = "XYZ"
            mapping = ", ".join(f"model {axes[a]}->bed {axes[i]}" for i, a in enumerate(fit.axis_order))
            warnings.append(f"Build volume: {ext} mm does not fit {bed_s} mm as modeled; fits rotated ({mapping})")
        else:
            warnings.append(f"Build volume: {ext} mm does not fit {bed_s} mm in any axis-aligned orientation")

    wall = min_wall_thickness(mesh)
    if wall.min_thickness is None:
        info.append("Wall thickness: no interior walls found by sampling")
    else:
        at = "(%.1f, %.1f, %.1f)" % wall.location
        line = (f"Wall thickness: thinnest sampled {wall.min_thickness:.2f} mm near {at} "
                f"({wall.samples:,} samples; estimate, thin features can be missed)")
        if wall.min_thickness < min_wall - _FIT_EPS:
            warnings.append(line + f" -- below {min_wall:g} mm")
        else:
            info.append(line)

    over = find_overhangs(mesh, overhang_angle)
    line = (f"Overhangs: {over.area:.1f} mm2 ({over.fraction * 100:.1f}% of surface) "
            f"steeper than {over.angle:g} deg from vertical, as modeled (+Z up)")
    (warnings if over.area > 0 else info).append(line + (" -- supports likely" if over.area > 0 else ""))
    return info, warnings
