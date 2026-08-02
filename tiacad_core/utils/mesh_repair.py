"""Post-tessellation STL mesh repair.

OCCT's mesher can leave a degenerate, zero-volume sliver triangle at a point
where a revolved/rotated surface pinches to a single point on its own axis
(a "pole") -- see KNOWN_LIMITATIONS.md #19. The B-Rep solid CadQuery/OCCT
builds is fully valid there (``Shape.isValid()`` is ``True``); only the STL
tessellation of that single point produces a tiny, non-watertight fragment
that ``trimesh`` reports as a separate disconnected "island". This module
strips exactly that kind of artifact so exported STL files are actually
watertight instead of relying on an advisory warning.
"""

from typing import Tuple


def strip_degenerate_shards(mesh, volume_ratio_threshold: float = 1e-6) -> Tuple[object, bool]:
    """
    Drop tiny non-watertight mesh fragments left over from tessellating a
    pole/pinch point, without touching legitimate multi-body geometry.

    A fragment is dropped only if it is BOTH non-watertight AND negligible
    in volume relative to the largest component in the mesh. A real
    disconnected solid in a multi-body assembly is watertight in its own
    right (each body is a closed shape) and is always kept regardless of
    its size, so this cannot silently eat a legitimately small part.

    Args:
        mesh: A ``trimesh.Trimesh`` (or compatible) mesh to inspect.
        volume_ratio_threshold: A fragment's volume must be at least this
            fraction of the largest component's volume to survive, unless
            it's watertight on its own.

    Returns:
        (mesh, changed) -- the original ``mesh`` object, unchanged, if
        nothing qualified for removal; otherwise a new merged mesh with the
        qualifying fragments dropped, and ``changed=True``.
    """
    import trimesh

    components = mesh.split(only_watertight=False)
    if len(components) <= 1:
        return mesh, False

    main_volume = max(abs(c.volume) for c in components)
    kept = [
        c for c in components
        if c.is_watertight or abs(c.volume) >= main_volume * volume_ratio_threshold
    ]
    if len(kept) == len(components):
        return mesh, False

    return trimesh.util.concatenate(kept), True
