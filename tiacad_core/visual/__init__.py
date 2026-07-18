"""
Visual debugging tools for TiaCAD

Canonical boundary vs. `tiacad_core.visualization`: this package (`visual`) is
the production rendering path — `trust_renderer.render_trust` is what
`tiacad debug`/`tiacad trust` and `debug_bundle.py` call for verification
renders. `tiacad_core.visualization.renderer.ModelRenderer` is a separate,
older multi-view renderer kept only for `scripts/render_demos.py` and
`scripts/render_grid_demos.py` — it is not wired into the CLI or debug bundle
and should not gain new production callers; extend `trust_renderer` instead.
"""

from .trust_renderer import render_trust

__all__ = [
    'render_trust',
]
