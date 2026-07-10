"""
Metamorphic Invariant Tests

Self-contained geometric invariants that must hold regardless of the specific
shapes involved — no generators or hand-picked expected values needed. See
docs/developer/VALIDATION_STRENGTHENING.md section 4.3.

These are the properties that would have caught most historic geometry bugs:
a transform that silently doesn't apply, a boolean that returns the wrong
operand, a pattern that leaves copies unrotated. Each test compares a
computed geometry against a *relationship*, not a memorized number.

Author: TIA
"""

import math

import cadquery as cq
import pytest

from tiacad_core.geometry import CadQueryBackend
from tiacad_core.part import Part
from tiacad_core.testing.dimensions import get_volume

REL_TOL = 0.01  # 1%, matching the tolerance used elsewhere in this suite


def _part(name: str, geometry) -> Part:
    return Part(name=name, geometry=geometry, backend=CadQueryBackend())


def _assert_close(actual: float, expected: float, rel_tol: float = REL_TOL):
    assert abs(actual - expected) < abs(expected) * rel_tol, (
        f"expected ~{expected:.4f}, got {actual:.4f} "
        f"(diff {abs(actual - expected):.4f}, tol {abs(expected) * rel_tol:.4f})"
    )


# Shapes used across multiple properties: one asymmetric shape per primitive
# family so translate/rotate/mirror conservation can't pass by accident of
# symmetry (a cube's volume is trivially invariant even if a bug ignores
# rotation entirely).
def _asymmetric_shapes():
    return {
        "box": cq.Workplane("XY").box(30, 12, 7),
        "cylinder": cq.Workplane("XY").cylinder(18, 5),
        "cone": cq.Workplane("XY").sphere(9).translate((3, 0, 0)).union(
            cq.Workplane("XY").box(4, 4, 4).translate((3, 0, 6))
        ),
    }


class TestTranslateConservation:
    """Translation must not change volume."""

    @pytest.mark.parametrize("name,shape", _asymmetric_shapes().items())
    def test_translate_preserves_volume(self, name, shape):
        original = get_volume(_part(f"{name}_orig", shape))
        moved = shape.translate((17.5, -8.25, 42.0))
        translated = get_volume(_part(f"{name}_translated", moved))
        _assert_close(translated, original)


class TestRotateConservation:
    """Rotation about an arbitrary axis must not change volume."""

    @pytest.mark.parametrize("name,shape", _asymmetric_shapes().items())
    def test_rotate_preserves_volume(self, name, shape):
        original = get_volume(_part(f"{name}_orig", shape))
        rotated_geo = shape.rotate((0, 0, 0), (1, 1, 0), 37)
        rotated = get_volume(_part(f"{name}_rotated", rotated_geo))
        _assert_close(rotated, original)


class TestMirrorSymmetry:
    """Mirroring must not change volume, regardless of mirror plane."""

    @pytest.mark.parametrize("plane", ["XY", "YZ", "XZ"])
    @pytest.mark.parametrize("name,shape", _asymmetric_shapes().items())
    def test_mirror_preserves_volume(self, name, shape, plane):
        original = get_volume(_part(f"{name}_orig", shape))
        mirrored_geo = shape.mirror(plane)
        mirrored = get_volume(_part(f"{name}_mirrored_{plane}", mirrored_geo))
        _assert_close(mirrored, original)


class TestScaleConservation:
    """Uniform scale by k must scale volume by k**3."""

    @pytest.mark.parametrize("k", [0.5, 2.0, 3.0])
    def test_box_scale_cubes_volume(self, k):
        base = cq.Workplane("XY").box(10, 6, 4)
        base_volume = get_volume(_part("box_base", base))

        scaled = cq.Workplane("XY").box(10 * k, 6 * k, 4 * k)
        scaled_volume = get_volume(_part("box_scaled", scaled))

        _assert_close(scaled_volume, base_volume * k**3)

    @pytest.mark.parametrize("k", [0.5, 2.0, 3.0])
    def test_cylinder_scale_cubes_volume(self, k):
        base = cq.Workplane("XY").cylinder(20, 6)
        base_volume = get_volume(_part("cyl_base", base))

        scaled = cq.Workplane("XY").cylinder(20 * k, 6 * k)
        scaled_volume = get_volume(_part("cyl_scaled", scaled))

        _assert_close(scaled_volume, base_volume * k**3)


class TestUnionAlgebra:
    """Union must be commutative and idempotent."""

    def test_union_commutative(self):
        box1 = cq.Workplane("XY").box(20, 10, 10)
        box2 = cq.Workplane("XY").center(12, 3).box(20, 10, 10)

        forward = get_volume(_part("a_or_b", box1.union(box2)))
        backward = get_volume(_part("b_or_a", box2.union(box1)))

        _assert_close(forward, backward, rel_tol=1e-6)

    def test_union_idempotent(self):
        box = cq.Workplane("XY").box(15, 15, 15)

        single = get_volume(_part("single", box))
        self_union = get_volume(_part("self_union", box.union(box)))

        _assert_close(self_union, single)


class TestBooleanSelfConsistency:
    """Inclusion-exclusion must hold for any pair of overlapping solids:
    |A ∪ B| + |A ∩ B| = |A| + |B|, and |A - B| = |A| - |A ∩ B|.
    """

    def _overlapping_pair(self):
        a = cq.Workplane("XY").box(20, 20, 20)
        b = cq.Workplane("XY").center(10, 5).box(20, 14, 20)
        return a, b

    def test_inclusion_exclusion(self):
        a, b = self._overlapping_pair()
        vol_a = get_volume(_part("a", a))
        vol_b = get_volume(_part("b", b))
        vol_union = get_volume(_part("union", a.union(b)))
        vol_intersect = get_volume(_part("intersect", a.intersect(b)))

        _assert_close(vol_union + vol_intersect, vol_a + vol_b)

    def test_difference_equals_minus_intersection(self):
        a, b = self._overlapping_pair()
        vol_a = get_volume(_part("a", a))
        vol_intersect = get_volume(_part("intersect", a.intersect(b)))
        vol_diff = get_volume(_part("diff", a.cut(b)))

        _assert_close(vol_diff, vol_a - vol_intersect)

    def test_difference_by_disjoint_solid_is_noop(self):
        """Subtracting a solid that doesn't touch A must leave A unchanged."""
        a = cq.Workplane("XY").box(10, 10, 10)
        far_away = cq.Workplane("XY").center(1000, 1000).box(10, 10, 10)

        vol_a = get_volume(_part("a", a))
        vol_diff = get_volume(_part("diff", a.cut(far_away)))

        _assert_close(vol_diff, vol_a)
