"""
Differential (kernel-vs-kernel) geometry testing (TCAD-VAL-2).

Every other oracle in the validation ladder -- analytic formulas, embedded
``expect:`` contracts, golden STEP topology, visual review -- still measures
CadQuery/OCCT's own output. None of them can catch a bug in the kernel's
volume/boolean computation itself, only bugs in how TiaCAD drives it.

This suite rebuilds each eligible trust model's final part independently
with `manifold3d` (a mesh-based CSG kernel with no code in common with
OCCT -- see tiacad_core/testing/differential.py's module docstring for why)
and asserts its volume/bbox agree with CadQuery's within a tolerance sized
for manifold3d's circular-segment discretization bias, not genuine kernel
disagreement.

Coverage is intentionally partial: only primitives + booleans + plain
translates have an independent manifold3d implementation, so most trust
models involving patterns/sketches/fillets/lofts/sweeps/revolves are
correctly reported ineligible rather than silently skipped -- see
test_eligibility_report below for the current list.
"""

from pathlib import Path

import pytest

from tiacad_core.testing.differential import (
    DEFAULT_BBOX_TOL,
    DEFAULT_VOLUME_TOL,
    differential_check,
    discover_eligible_trust_models,
)

PROJECT_ROOT = Path(__file__).parents[3]
TRUST_DIR = PROJECT_ROOT / "examples" / "trust"

_CLASSIFIED = discover_eligible_trust_models(str(TRUST_DIR))
ELIGIBLE_PATHS = [path for path, eligible, _ in _CLASSIFIED if eligible]


def test_eligibility_report():
    """Guards against silent coverage loss/gain going unnoticed in review.

    If this fails after adding a new trust model or changing an existing
    one's operations, update the expected sets below deliberately -- don't
    just paste in the new failure output.
    """
    eligible_names = {Path(p).name for p in ELIGIBLE_PATHS}
    ineligible = {Path(p).name: reason for p, eligible, reason in _CLASSIFIED if not eligible}

    expected_eligible = {
        "boolean_intersect.yaml", "boolean_subtract.yaml", "boolean_union.yaml",
        "box_basic.yaml", "cone_basic.yaml", "cylinder_basic.yaml",
        "cylinder_on_plate.yaml", "pcb_standoff_assembly.yaml", "side_by_side.yaml",
        "sphere_basic.yaml", "stacked_boxes.yaml", "three_part_assembly.yaml",
    }
    assert eligible_names == expected_eligible, (
        f"differential-eligible trust models changed: "
        f"gained {eligible_names - expected_eligible}, lost {expected_eligible - eligible_names}"
    )
    assert set(ineligible) == {
        "chamfer_basic.yaml", "circular_pattern.yaml", "fillet_basic.yaml",
        "hull_spheres.yaml", "linear_pattern.yaml", "loft_rect_to_circle.yaml",
        "revolve_180.yaml", "revolve_90.yaml", "revolve_basic.yaml",
        "revolve_x_axis.yaml", "revolve_y_axis.yaml", "sweep_basic.yaml",
    }


@pytest.mark.parametrize("model_path", ELIGIBLE_PATHS, ids=lambda p: Path(p).name)
def test_differential_volume_and_bbox_agree(model_path):
    result = differential_check(model_path)
    assert result.eligible, result.reason

    assert result.volume_diff_relative <= DEFAULT_VOLUME_TOL, (
        f"{Path(model_path).name}: CadQuery volume {result.volume_cadquery} vs "
        f"manifold3d volume {result.volume_manifold} "
        f"(relative diff {result.volume_diff_relative:.5f} > {DEFAULT_VOLUME_TOL})"
    )
    assert result.bbox_diff_max <= DEFAULT_BBOX_TOL, (
        f"{Path(model_path).name}: CadQuery bbox {result.bbox_cadquery} vs "
        f"manifold3d bbox {result.bbox_manifold} "
        f"(max diff {result.bbox_diff_max} > {DEFAULT_BBOX_TOL})"
    )
