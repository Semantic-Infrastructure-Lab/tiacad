"""TiaCAD Visualization - 3D rendering to PNG images

Not the production rendering path — `tiacad debug`/`tiacad trust` and
`debug_bundle.py` use `tiacad_core.visual.trust_renderer.render_trust`
instead. This module (`ModelRenderer`) is kept for `scripts/render_demos.py`
and `scripts/render_grid_demos.py`; new verification-render work belongs in
`tiacad_core.visual.trust_renderer`, not here.
"""

from .renderer import ModelRenderer, render_part, render_assembly

__all__ = ['ModelRenderer', 'render_part', 'render_assembly']
