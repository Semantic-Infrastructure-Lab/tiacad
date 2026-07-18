"""
Visual debugging tools for TiaCAD

Tools for exporting and visualizing transform steps.

Canonical boundary vs. `tiacad_core.visualization`: this package (`visual`) is
the production rendering path — `trust_renderer.render_trust` is what
`tiacad debug`/`tiacad trust` and `debug_bundle.py` call for verification
renders. `tiacad_core.visualization.renderer.ModelRenderer` is a separate,
older multi-view renderer kept only for `scripts/render_demos.py` and
`scripts/render_grid_demos.py` — it is not wired into the CLI or debug bundle
and should not gain new production callers; extend `trust_renderer` instead.
`visual_debug.py`'s `export_transform_steps`/`compare_geometries`/
`debug_guitar_hanger_arm` are a standalone manual debug script (note the
`if __name__ == "__main__"` guard) with no callers elsewhere in the codebase —
treat as a worked example, not shared infrastructure.
"""

from .visual_debug import (
    export_transform_steps,
    compare_geometries,
    debug_guitar_hanger_arm,
)
from .trust_renderer import render_trust

__all__ = [
    'export_transform_steps',
    'compare_geometries',
    'debug_guitar_hanger_arm',
    'render_trust',
]
