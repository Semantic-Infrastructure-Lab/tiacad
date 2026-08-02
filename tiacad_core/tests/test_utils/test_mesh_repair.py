"""Tests for `strip_degenerate_shards` (tiacad_core/utils/mesh_repair.py).

Covers the fix for a revolve profile touching its own axis at a pole
(KNOWN_LIMITATIONS.md #19): OCCT's mesher leaves a degenerate, zero-volume
shard at the pinch point, which trimesh reports as a separate disconnected,
non-watertight "island" even though the B-Rep solid is valid.
"""

import numpy as np
import pytest
import trimesh

from tiacad_core.utils.mesh_repair import strip_degenerate_shards


def _box(extents=(10, 10, 10), translation=(0, 0, 0)):
    b = trimesh.creation.box(extents=extents)
    b.apply_translation(translation)
    return b


def _degenerate_shard(at=(0, 0, 20)):
    """A single zero-area triangle, disconnected from everything else --
    the exact shape of the pole-tessellation artifact this module targets."""
    verts = np.array(at) + np.array([[0, 0, 0], [1e-3, 0, 0], [0, 1e-3, 0]])
    return trimesh.Trimesh(vertices=verts, faces=[[0, 1, 2]], process=False)


def test_single_component_mesh_is_left_unchanged():
    mesh = _box()
    result, changed = strip_degenerate_shards(mesh)
    assert changed is False
    assert result is mesh


def test_degenerate_shard_is_stripped_and_main_body_becomes_watertight():
    box = _box()
    shard = _degenerate_shard()
    combined = trimesh.util.concatenate([box, shard])
    assert not combined.is_watertight
    assert len(combined.split(only_watertight=False)) == 2

    result, changed = strip_degenerate_shards(combined)

    assert changed is True
    assert result.is_watertight
    assert result.volume == pytest.approx(box.volume, rel=1e-6)


def test_two_legitimate_watertight_solids_are_both_kept():
    """A real multi-body assembly (two genuinely separate, watertight parts)
    must never be mistaken for a pole artifact, regardless of relative size."""
    big = _box(extents=(10, 10, 10))
    small = _box(extents=(0.5, 0.5, 0.5), translation=(100, 0, 0))
    combined = trimesh.util.concatenate([big, small])

    result, changed = strip_degenerate_shards(combined)

    assert changed is False
    assert result is combined
    assert len(result.split(only_watertight=False)) == 2


def test_large_non_watertight_fragment_above_threshold_is_kept():
    """A fragment that's non-watertight but not negligible in volume is a
    real defect, not a pole shard -- it must survive so the caller's
    watertight check still fires."""
    box = _box()
    open_box = trimesh.creation.box(extents=(5, 5, 5))
    open_box.apply_translation((50, 0, 0))
    broken = trimesh.Trimesh(vertices=open_box.vertices, faces=open_box.faces[:-2])
    combined = trimesh.util.concatenate([box, broken])

    result, changed = strip_degenerate_shards(combined)

    assert changed is False
    assert not result.is_watertight
