"""
Trust renderer for TiaCAD — multi-view colored renders for visual verification.

Renders each part in a distinct color with 6 viewpoints (2×3 grid):
  Row 0: Iso Front-Left, Iso Back-Right, Bottom (XY from below)
  Row 1: Front (XZ), Top (XY), Side (YZ)
Two isometrics cover both front-left and back-right blind spots. Bottom view
reveals underside features (standoffs, recesses). Produces a single composite
PNG you can inspect — or show to AI — and say "yep, that's right."

Usage:
    from tiacad_core.visual.trust_renderer import render_trust

    doc = TiaCADParser().parse_file("examples/trust/stacked_boxes.yaml")
    render_trust(doc, "trust_output/stacked_boxes.png")

Or from the CLI:
    python scripts/trust_render.py examples/trust/stacked_boxes.yaml
"""

import os
import io
import tempfile
from pathlib import Path
from typing import Optional

import pyvista as pv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Colorblind-friendly palette (high contrast, distinct at small size)
PART_PALETTE = [
    "#E63946",  # vivid red
    "#2196F3",  # vivid blue
    "#4CAF50",  # vivid green
    "#FF9800",  # vivid orange
    "#9C27B0",  # vivid purple
    "#00BCD4",  # vivid cyan
    "#FF5722",  # deep orange
    "#8BC34A",  # light green
    "#3F51B5",  # indigo
    "#F06292",  # pink
    "#795548",  # brown
    "#607D8B",  # blue-grey
]

# Camera positions: (label, position_vector, view_up, parallel_projection)
# position_vector is a direction — scaled to fit after reset_camera
# 6 panels in a 2×3 grid: two isometrics cover front-left and back-right blind spots;
# three orthographics lock in X/Y/Z planes; Bottom reveals underside features.
VIEWS = [
    ("Iso Front-Left",  ( 1.0, -1.2,  0.8), (0, 0, 1), False),  # row0 col0
    ("Iso Back-Right",  (-1.0,  1.2,  0.8), (0, 0, 1), False),  # row0 col1
    ("Bottom   (XY)",   ( 0.0,  0.0, -1.0), (0, 1, 0), True),   # row0 col2 — looking along +Z
    ("Front    (XZ)",   ( 0.0, -1.0,  0.0), (0, 0, 1), True),   # row1 col0 — looking along +Y
    ("Top      (XY)",   ( 0.0,  0.0,  1.0), (0, 1, 0), True),   # row1 col1 — looking along -Z
    ("Side     (YZ)",   ( 1.0,  0.0,  0.0), (0, 0, 1), True),   # row1 col2 — looking along -X
]
GRID_COLS = 3


def _hex_to_rgb_float(hex_color: str):
    """Convert '#RRGGBB' to (r, g, b) floats 0–1."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _part_color(metadata: dict, palette_index: int) -> tuple:
    """Return (r, g, b) float tuple for a part."""
    if "color" in metadata and metadata["color"]:
        rgba = metadata["color"]
        if isinstance(rgba, (tuple, list)) and len(rgba) >= 3:
            return tuple(float(v) for v in rgba[:3])
    return _hex_to_rgb_float(PART_PALETTE[palette_index % len(PART_PALETTE)])


def _geometry_to_pyvista(geometry) -> Optional[pv.PolyData]:
    """Export a CadQuery geometry to pyvista PolyData via STL."""
    try:
        if hasattr(geometry, "val"):
            solid = geometry.val()
        else:
            solid = geometry

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            tmp = f.name

        if hasattr(solid, "exportStl"):
            solid.exportStl(tmp)
        else:
            return None

        mesh = pv.read(tmp)
        os.unlink(tmp)

        if mesh.n_points == 0:
            return None
        # Compute normals for correct lighting — do NOT use smooth() as it moves
        # vertices and destroys flat faces (turns a box into a pillow shape).
        mesh = mesh.compute_normals(cell_normals=False, point_normals=True,
                                    split_vertices=True, auto_orient_normals=True)
        return mesh

    except Exception as e:
        print(f"    [warn] geometry export failed: {e}")
        return None


def _add_axes_widget(plotter: pv.Plotter):
    """Add a small XYZ axis indicator to the current subplot."""
    plotter.add_axes(
        xlabel="X", ylabel="Y", zlabel="Z",
        x_color="red", y_color="green", z_color="blue",
        line_width=3,
        shaft_length=0.6,
        tip_length=0.2,
        ambient=0.5,
    )


def render_trust(
    doc,
    output_path: str,
    title: Optional[str] = None,
    width: int = 1800,
    height: int = 1000,
) -> str:
    """
    Render a TiaCADDocument to a 4-panel trust PNG.

    Args:
        doc: Parsed TiaCADDocument
        output_path: Where to write the PNG
        title: Optional title shown in the legend panel
        width: Output image width in pixels
        height: Output image height in pixels

    Returns:
        Absolute path to the written PNG
    """
    pv.start_xvfb()

    # --- Collect parts ---
    part_names = doc.parts.list_parts()
    parts_data = []  # list of (name, pv.PolyData, (r,g,b))

    # Determine which parts are consumed as inputs to operations.
    # Consumed parts shouldn't be shown alongside their operation results —
    # that would render the original geometry on top of the boolean result.
    consumed = set()
    for op in (doc.operations or {}).values():
        # singular input fields (transform ops use 'input')
        for field in ("base", "tool", "input"):
            if field in op:
                consumed.add(op[field])
        # list input fields (boolean ops use 'subtract', 'inputs')
        for field in ("subtract", "inputs", "tools"):
            for name in op.get(field, []):
                consumed.add(name)

    # Visible = not a placeholder, not consumed as an intermediate input
    visible_names = [
        n for n in part_names
        if not n.startswith("_") and n not in consumed
    ]
    if not visible_names:
        visible_names = [n for n in part_names if not n.startswith("_")]

    print(f"  Parts: {visible_names}")

    for i, name in enumerate(visible_names):
        part = doc.parts.get(name)
        if part is None or part.geometry is None:
            continue
        mesh = _geometry_to_pyvista(part.geometry)
        if mesh is None:
            continue
        color = _part_color(part.metadata or {}, i)
        parts_data.append((name, mesh, color))
        print(f"    {name}: {mesh.n_points} pts, color={color}")

    if not parts_data:
        raise ValueError("No renderable geometry found in document")

    # --- Render 6 views (2×3 grid) ---
    n_rows = (len(VIEWS) + GRID_COLS - 1) // GRID_COLS
    plotter = pv.Plotter(
        shape=(n_rows, GRID_COLS),
        off_screen=True,
        window_size=[width, height],
    )
    plotter.set_background("white")

    # Compute scene bounds for camera placement
    all_bounds = np.array([m.bounds for _, m, _ in parts_data])
    scene_center = np.array([
        (all_bounds[:, 0].min() + all_bounds[:, 1].max()) / 2,
        (all_bounds[:, 2].min() + all_bounds[:, 3].max()) / 2,
        (all_bounds[:, 4].min() + all_bounds[:, 5].max()) / 2,
    ])
    scene_radius = max(
        all_bounds[:, 1].max() - all_bounds[:, 0].min(),
        all_bounds[:, 3].max() - all_bounds[:, 2].min(),
        all_bounds[:, 5].max() - all_bounds[:, 4].min(),
    ) * 1.5

    for idx, (view_label, pos_dir, view_up, parallel) in enumerate(VIEWS):
        row, col = divmod(idx, GRID_COLS)
        plotter.subplot(row, col)

        for name, mesh, color in parts_data:
            plotter.add_mesh(
                mesh,
                color=color,
                show_edges=True,
                edge_color="black",
                line_width=0.5,
                opacity=0.95,
                smooth_shading=False,
                specular=0.1,
                specular_power=10,
                ambient=0.4,
                diffuse=0.6,
            )

        _add_axes_widget(plotter)

        # Set camera via camera_position tuple — preserves position/focal/up atomically.
        # Do NOT call reset_camera() after this; it overrides all three values.
        d = np.array(pos_dir, dtype=float)
        d /= np.linalg.norm(d)
        cam_pos = scene_center + d * scene_radius * 2.5
        plotter.camera_position = [cam_pos.tolist(), scene_center.tolist(), list(view_up)]
        plotter.camera.parallel_projection = parallel
        if parallel:
            # For orthographic views, set parallel_scale to half the scene extent
            plotter.camera.parallel_scale = scene_radius * 0.6
        plotter.reset_camera_clipping_range()  # fix near/far planes only — does NOT move camera

        plotter.add_title(view_label, font_size=10, color="black")

    screenshot = plotter.screenshot(return_img=True)
    plotter.close()

    # --- Composite: render + legend strip ---
    render_img = Image.fromarray(screenshot)
    final_img = _add_legend(render_img, parts_data, title, width, height)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(out))
    return str(out.resolve())


def _add_legend(
    render_img: Image.Image,
    parts_data: list,
    title: Optional[str],
    width: int,
    height: int,
) -> Image.Image:
    """Overlay a legend strip on the right side of the render image."""
    LEGEND_W = 220
    final = Image.new("RGB", (width + LEGEND_W, height), color=(245, 245, 245))
    final.paste(render_img, (0, 0))

    draw = ImageDraw.Draw(final)
    x0 = width + 10
    y = 20

    # Title
    if title:
        draw.text((x0, y), title, fill=(30, 30, 30))
        y += 24
        draw.line([(x0, y), (x0 + LEGEND_W - 20, y)], fill=(180, 180, 180), width=1)
        y += 10

    draw.text((x0, y), "Parts", fill=(80, 80, 80))
    y += 20

    swatch = 16
    gap = 6
    for name, mesh, color in parts_data:
        r, g, b = (int(c * 255) for c in color)
        draw.rectangle([x0, y, x0 + swatch, y + swatch], fill=(r, g, b), outline=(0, 0, 0))
        label = name if len(name) <= 22 else name[:19] + "…"
        draw.text((x0 + swatch + gap, y + 2), label, fill=(30, 30, 30))
        y += swatch + gap

    y += 10
    draw.line([(x0, y), (x0 + LEGEND_W - 20, y)], fill=(180, 180, 180), width=1)
    y += 10
    draw.text((x0, y), "Axes", fill=(80, 80, 80))
    y += 18
    for axis_label, color in [("X", (200, 40, 40)), ("Y", (40, 160, 40)), ("Z", (40, 40, 200))]:
        draw.rectangle([x0, y, x0 + swatch, y + swatch], fill=color, outline=(0, 0, 0))
        draw.text((x0 + swatch + gap, y + 2), axis_label, fill=(30, 30, 30))
        y += swatch + gap

    return final
