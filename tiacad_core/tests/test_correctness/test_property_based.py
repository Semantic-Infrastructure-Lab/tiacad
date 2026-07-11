"""
Property-Based Correctness Tests (Hypothesis)

Where the metamorphic suite (test_metamorphic.py) checks relationships over a
few hand-picked shapes, this suite checks the Tier-0/1 *analytic* oracles over
hundreds of machine-generated parameter values — the infinity of sizes a
hand-written test never reaches. Each primitive is built through the real
user-facing path (ParameterResolver -> PartsBuilder -> CadQueryBackend) and its
volume, bounding box, and (where the formula is clean) surface area are checked
against the closed-form analytic value. Transform-conservation and boolean
inclusion-exclusion are then asserted over generated inputs too.

See docs/developer/VALIDATION_STRENGTHENING.md section 4.2 and the Appendix
"analytic formulas" oracle kit. This is the suite that found the zero-volume
torus bug (a broken revolve on the OCP 7.9 kernel that `assert part is not None`
never noticed).

Determinism note: every test runs under `derandomize=True`, so Hypothesis
generates the *same* examples on every run — a failure reproduces exactly in CI
and locally, and the suite can't flake from run-to-run RNG. `deadline=None`
because OCCT solid construction is far slower and more variable than
Hypothesis's default per-example budget.

Author: TIA
"""

import math

import pytest
from hypothesis import given, settings, strategies as st

from tiacad_core.parser.parts_builder import PartsBuilder
from tiacad_core.parser.parameter_resolver import ParameterResolver
from tiacad_core.part import Part
from tiacad_core.geometry import CadQueryBackend
from tiacad_core.testing.dimensions import get_volume, get_surface_area

# 1% relative tolerance, matching REL_TOL in test_metamorphic.py. The kernel
# computes exact BREP volumes/areas, so the slack is for float noise and the
# tiny (0.001mm) apex circle the cone builder uses in place of a true point.
REL_TOL = 0.01

# OCCT solid construction is slow; keep example counts modest but meaningful.
# Primitive-formula tests build one solid per example; transform/boolean tests
# build several, so they get fewer.
PRIMITIVE_SETTINGS = settings(max_examples=30, deadline=None, derandomize=True)
COMPOUND_SETTINGS = settings(max_examples=15, deadline=None, derandomize=True)


# ---------------------------------------------------------------------------
# Build helpers — the real path a user's .tiacad file takes.
# ---------------------------------------------------------------------------
def _build(name, primitive, **params):
    resolver = ParameterResolver({})
    builder = PartsBuilder(resolver, backend=CadQueryBackend())
    spec = {name: {"primitive": primitive, "parameters": params}}
    return builder.build_parts(spec).get(name)


def _part(geometry):
    """Wrap a raw CadQuery geometry back into a Part for measurement."""
    return Part(name="tmp", geometry=geometry, backend=CadQueryBackend())


def _extents(part):
    """(x, y, z) bounding-box extents of a built part."""
    bb = part.geometry.val().BoundingBox()
    return bb.xlen, bb.ylen, bb.zlen


def _assert_close(actual, expected, rel_tol=REL_TOL, what=""):
    assert abs(actual - expected) < abs(expected) * rel_tol + 1e-9, (
        f"{what}: expected ~{expected:.5f}, got {actual:.5f} "
        f"(diff {abs(actual - expected):.5f}, tol {abs(expected) * rel_tol:.5f})"
    )


# Dimension strategies. Floors keep the kernel out of degenerate territory
# (sub-millimetre features, coincident faces); ceilings keep builds cheap.
dim = st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False)
radius = st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# Primitive analytic oracles (volume / bbox / surface area).
# ---------------------------------------------------------------------------
class TestBoxProperties:
    @given(w=dim, h=dim, d=dim)
    @PRIMITIVE_SETTINGS
    def test_box_volume(self, w, h, d):
        part = _build("box", "box", width=w, height=h, depth=d)
        _assert_close(get_volume(part), w * h * d, what="box volume")

    @given(w=dim, h=dim, d=dim)
    @PRIMITIVE_SETTINGS
    def test_box_bbox_axis_mapping(self, w, h, d):
        # create_box maps width->X, depth->Y, height->Z. This is exactly the
        # mapping that produced a real disconnected-components bug when it was
        # misunderstood (see VALIDATION_STRENGTHENING 4.1); pin it hard.
        x, y, z = _extents(_build("box", "box", width=w, height=h, depth=d))
        _assert_close(x, w, what="box x-extent (width)")
        _assert_close(y, d, what="box y-extent (depth)")
        _assert_close(z, h, what="box z-extent (height)")

    @given(w=dim, h=dim, d=dim)
    @PRIMITIVE_SETTINGS
    def test_box_surface_area(self, w, h, d):
        part = _build("box", "box", width=w, height=h, depth=d)
        expected = 2 * (w * h + w * d + h * d)
        _assert_close(get_surface_area(part), expected, what="box area")


class TestCylinderProperties:
    @given(r=radius, h=dim)
    @PRIMITIVE_SETTINGS
    def test_cylinder_volume(self, r, h):
        part = _build("cyl", "cylinder", radius=r, height=h)
        _assert_close(get_volume(part), math.pi * r**2 * h, what="cyl volume")

    @given(r=radius, h=dim)
    @PRIMITIVE_SETTINGS
    def test_cylinder_bbox(self, r, h):
        x, y, z = _extents(_build("cyl", "cylinder", radius=r, height=h))
        _assert_close(x, 2 * r, what="cyl x-extent")
        _assert_close(y, 2 * r, what="cyl y-extent")
        _assert_close(z, h, what="cyl z-extent")

    @given(r=radius, h=dim)
    @PRIMITIVE_SETTINGS
    def test_cylinder_surface_area(self, r, h):
        part = _build("cyl", "cylinder", radius=r, height=h)
        expected = 2 * math.pi * r * h + 2 * math.pi * r**2
        _assert_close(get_surface_area(part), expected, what="cyl area")


class TestSphereProperties:
    @given(r=radius)
    @PRIMITIVE_SETTINGS
    def test_sphere_volume(self, r):
        part = _build("sph", "sphere", radius=r)
        _assert_close(get_volume(part), 4 / 3 * math.pi * r**3, what="sphere volume")

    @given(r=radius)
    @PRIMITIVE_SETTINGS
    def test_sphere_bbox(self, r):
        x, y, z = _extents(_build("sph", "sphere", radius=r))
        for axis, ext in zip("xyz", (x, y, z)):
            _assert_close(ext, 2 * r, what=f"sphere {axis}-extent")

    @given(r=radius)
    @PRIMITIVE_SETTINGS
    def test_sphere_surface_area(self, r):
        part = _build("sph", "sphere", radius=r)
        _assert_close(get_surface_area(part), 4 * math.pi * r**2, what="sphere area")


class TestConeProperties:
    @given(r1=radius, h=dim)
    @PRIMITIVE_SETTINGS
    def test_true_cone_volume(self, r1, h):
        # radius2 == 0 takes the builder's dedicated pointed-apex branch.
        part = _build("cone", "cone", radius1=r1, radius2=0, height=h)
        expected = (1 / 3) * math.pi * r1**2 * h
        _assert_close(get_volume(part), expected, what="true-cone volume")

    # frac floors at 0.02 so the top radius stays well above the kernel's
    # ~1e-7 confusion tolerance — a sub-tolerance top circle isn't a cone the
    # loft can build, it's a degenerate input no real model would ask for.
    @given(r1=radius, h=dim, frac=st.floats(min_value=0.02, max_value=1.0))
    @PRIMITIVE_SETTINGS
    def test_frustum_volume(self, r1, h, frac):
        r2 = r1 * frac
        part = _build("cone", "cone", radius1=r1, radius2=r2, height=h)
        expected = (1 / 3) * math.pi * h * (r1**2 + r1 * r2 + r2**2)
        _assert_close(get_volume(part), expected, what="frustum volume")

    @given(r1=radius, h=dim, frac=st.floats(min_value=0.02, max_value=1.0))
    @PRIMITIVE_SETTINGS
    def test_cone_bbox(self, r1, h, frac):
        # Base radius r1 is the widest; top is smaller (frac <= 1), so the
        # widest xy extent is 2*r1 and the height extent is h.
        x, y, z = _extents(_build("cone", "cone", radius1=r1, radius2=r1 * frac, height=h))
        _assert_close(x, 2 * r1, what="cone x-extent")
        _assert_close(y, 2 * r1, what="cone y-extent")
        _assert_close(z, h, what="cone z-extent")


class TestTorusProperties:
    # minor < major keeps the tube from self-intersecting through the hole.
    @given(
        major=st.floats(min_value=5.0, max_value=50.0),
        minor_frac=st.floats(min_value=0.05, max_value=0.9),
    )
    @PRIMITIVE_SETTINGS
    def test_torus_volume(self, major, minor_frac):
        minor = major * minor_frac
        part = _build("torus", "torus", major_radius=major, minor_radius=minor)
        expected = 2 * math.pi**2 * major * minor**2  # Pappus
        _assert_close(get_volume(part), expected, what="torus volume")

    @given(
        major=st.floats(min_value=5.0, max_value=50.0),
        minor_frac=st.floats(min_value=0.05, max_value=0.9),
    )
    @PRIMITIVE_SETTINGS
    def test_torus_bbox(self, major, minor_frac):
        minor = major * minor_frac
        x, y, z = _extents(_build("torus", "torus", major_radius=major, minor_radius=minor))
        _assert_close(x, 2 * (major + minor), what="torus x-extent")
        _assert_close(y, 2 * (major + minor), what="torus y-extent")
        _assert_close(z, 2 * minor, what="torus z-extent (tube diameter)")


# ---------------------------------------------------------------------------
# Metamorphic properties over generated inputs (rigid transforms / scale).
# ---------------------------------------------------------------------------
class TestTransformConservation:
    @given(w=dim, h=dim, d=dim, dx=dim, dy=dim, dz=dim)
    @COMPOUND_SETTINGS
    def test_translate_preserves_volume(self, w, h, d, dx, dy, dz):
        backend = CadQueryBackend()
        base = _build("b", "box", width=w, height=h, depth=d)
        v0 = get_volume(base)
        moved = backend.translate(base.geometry, (dx, dy, dz))
        _assert_close(get_volume(_part(moved)), v0, rel_tol=1e-6, what="translate volume")

    @given(
        w=dim, h=dim, d=dim,
        angle=st.floats(min_value=1.0, max_value=359.0),
        ax=st.floats(min_value=-1.0, max_value=1.0),
        ay=st.floats(min_value=-1.0, max_value=1.0),
        az=st.floats(min_value=-1.0, max_value=1.0),
    )
    @COMPOUND_SETTINGS
    def test_rotate_preserves_volume(self, w, h, d, angle, ax, ay, az):
        # Skip near-zero axis vectors (no well-defined rotation axis).
        if math.sqrt(ax * ax + ay * ay + az * az) < 0.1:
            return
        backend = CadQueryBackend()
        base = _build("b", "box", width=w, height=h, depth=d)
        v0 = get_volume(base)
        rotated = backend.rotate(base.geometry, (0, 0, 0), (ax, ay, az), angle)
        _assert_close(get_volume(_part(rotated)), v0, rel_tol=1e-6, what="rotate volume")

    @given(
        w=dim, h=dim, d=dim,
        k=st.floats(min_value=0.2, max_value=3.0),
    )
    @COMPOUND_SETTINGS
    def test_uniform_scale_cubes_volume(self, w, h, d, k):
        backend = CadQueryBackend()
        base = _build("b", "box", width=w, height=h, depth=d)
        v0 = get_volume(base)
        scaled = backend.scale(base.geometry, k)
        _assert_close(get_volume(_part(scaled)), v0 * k**3, what="scale volume")


# ---------------------------------------------------------------------------
# Boolean algebra over generated pairs.
# ---------------------------------------------------------------------------
class TestBooleanInclusionExclusion:
    @given(
        s1=st.floats(min_value=5.0, max_value=40.0),
        s2=st.floats(min_value=5.0, max_value=40.0),
        ox=st.floats(min_value=-30.0, max_value=30.0),
        oy=st.floats(min_value=-30.0, max_value=30.0),
    )
    @COMPOUND_SETTINGS
    def test_inclusion_exclusion(self, s1, s2, ox, oy):
        # |A u B| + |A n B| = |A| + |B| for ANY two solids, overlapping or not.
        backend = CadQueryBackend()
        a = _build("a", "box", width=s1, height=s1, depth=s1)
        b_geo = backend.translate(
            _build("b", "box", width=s2, height=s2, depth=s2).geometry, (ox, oy, 0)
        )

        vol_a = get_volume(a)
        vol_b = get_volume(_part(b_geo))
        union = backend.boolean_union(a.geometry, b_geo)
        inter = backend.boolean_intersection(a.geometry, b_geo)

        vol_union = get_volume(_part(union))
        # Intersection may be empty (disjoint boxes) -> zero/empty volume.
        try:
            vol_inter = get_volume(_part(inter))
        except Exception:
            vol_inter = 0.0

        _assert_close(vol_union + vol_inter, vol_a + vol_b, what="inclusion-exclusion")
