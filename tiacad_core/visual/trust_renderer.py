"""
Trust renderer for TiaCAD — multi-view colored renders for visual verification.

Renders each part in a distinct color with 6 viewpoints (2×3 grid):
  Row 0: Iso (shaded + feature edges), X-Ray (transparent + edges), Top (XY)
  Row 1: Front (XZ), Side (YZ), Bottom (XY)

Feature edges replace the old cell-count threshold — draws only real geometric
boundaries (dihedral angle > 25°), so boxes get clean outlines and curved
surfaces get rim/silhouette edges without tessellation noise.

Orthographic panels show bounding-box dimensions so you can immediately verify
"yes, this is 100×80×12mm" without guessing from visual scale.

X-Ray panel renders geometry transparent so internal features, standoffs, and
boolean cuts are visible through the shell.

Usage:
    from tiacad_core.visual.trust_renderer import render_trust

    doc = TiaCADParser().parse_file("examples/trust/stacked_boxes.yaml")
    render_trust(doc, "trust_output/stacked_boxes.png")

Or from the CLI:
    python scripts/trust_render.py examples/trust/stacked_boxes.yaml
"""

import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pyvista as pv
import numpy as np
from PIL import Image, ImageDraw
from ..backend_support import tessellate_part

logger = logging.getLogger(__name__)


@dataclass
class SceneMetrics:
    """Derived scene metrics shared across trust-render views."""

    center: np.ndarray
    radius: float
    sizes: dict
    named_dims: dict

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

# Camera views: (label, position_direction, view_up, parallel_projection, mode)
# mode: "shaded" | "xray" | "ortho"
#
# Row 0: isometric shaded, x-ray (same angle, transparent), top-down ortho
# Row 1: three orthographic views with dimension overlays
VIEWS = [
    ("Iso (shaded)",  ( 1.0, -1.2,  0.8), (0, 0, 1), False, "shaded"),  # row0 col0
    ("X-Ray",         ( 1.0, -1.2,  0.8), (0, 0, 1), False, "xray"),    # row0 col1
    ("Top      (XY)", ( 0.0,  0.0,  1.0), (0, 1, 0), True,  "ortho"),   # row0 col2
    ("Front    (XZ)", ( 0.0, -1.0,  0.0), (0, 0, 1), True,  "ortho"),   # row1 col0
    ("Side     (YZ)", ( 1.0,  0.0,  0.0), (0, 0, 1), True,  "ortho"),   # row1 col1
    ("Bottom   (XY)", ( 0.0,  0.0, -1.0), (0, 1, 0), True,  "ortho"),   # row1 col2
]
GRID_COLS = 3

# Which two dimensions to display for each orthographic view
_ORTHO_DIMS = {
    "Top      (XY)":  ("X", "Y"),
    "Front    (XZ)":  ("X", "Z"),
    "Side     (YZ)":  ("Y", "Z"),
    "Bottom   (XY)":  ("X", "Y"),
}

# Angle threshold for feature edge extraction.
# 40° captures box edges (90°), cylinder rims, fillet boundaries, boolean cuts.
# 25° is too low — it catches the OCCT seam edge on revolved solids (a dihedral
# discontinuity at the 0°/360° boundary that appears as an artifact line).
# 40° skips the seam while still capturing all real geometric boundaries.
_FEATURE_ANGLE = 40.0

# Tolerance (mm) for matching scene extents to parameter values.
_DIM_MATCH_TOL = 0.5


def _find_named_dims(sizes: dict, parameters: dict) -> dict:
    """Back-map scene extents to parameter names for readable dimension labels.

    For each axis (X, Y, Z), searches the resolved parameters for a numeric
    value matching the extent within _DIM_MATCH_TOL.  Returns a dict mapping
    axis letter → label string (e.g. {"X": "plate_w", "Y": "plate_h", "Z": "Z"}).

    Falls back to the axis letter if no parameter matches.
    """
    named = {}
    for axis, val in sizes.items():
        best = None
        for pname, pval in (parameters or {}).items():
            if not isinstance(pval, (int, float)):
                continue
            if abs(float(pval) - val) <= _DIM_MATCH_TOL:
                # Prefer names that hint at the axis to break ties
                hints = {"X": ("width", "w", "x"), "Y": ("depth", "d", "y"),
                         "Z": ("height", "h", "z")}
                if best is None:
                    best = pname
                elif any(h in pname.lower() for h in hints.get(axis, ())):
                    best = pname
        named[axis] = best if best is not None else axis
    return named


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


def _part_to_pyvista(part) -> Optional[pv.PolyData]:
    """Convert a TiaCAD part to PyVista mesh data via backend tessellation."""
    try:
        vertices, triangles = tessellate_part(part, 0.1)
        if not vertices or not triangles:
            return None

        verts = np.array(vertices)
        faces = []
        for tri in triangles:
            faces.extend([3, tri[0], tri[1], tri[2]])
        mesh = pv.PolyData(verts, np.array(faces))

        if mesh.n_points == 0:
            return None
        # Compute normals for correct lighting — do NOT use smooth() as it moves
        # vertices and destroys flat faces (turns a box into a pillow shape).
        mesh = mesh.compute_normals(cell_normals=False, point_normals=True,
                                    split_vertices=True, auto_orient_normals=True)
        return mesh

    except Exception as e:
        logger.warning("Trust render mesh conversion failed for part '%s': %s", part.name, e)
        return None


def _maybe_start_xvfb() -> None:
    """Best-effort headless setup for environments that need Xvfb."""
    start_xvfb = getattr(pv, "start_xvfb", None)
    if start_xvfb is None:
        return
    try:
        start_xvfb()
    except Exception as exc:
        logger.debug("PyVista Xvfb startup skipped: %s", exc)


def _collect_visible_part_names(doc) -> list[str]:
    """Return visible part names for trust rendering."""
    part_names = doc.parts.list_parts()
    consumed = set()
    for op in (doc.operations or {}).values():
        for field in ("base", "tool", "input"):
            if field in op:
                consumed.add(op[field])
        for field in ("subtract", "inputs", "tools"):
            for name in op.get(field, []):
                consumed.add(name)

    visible_names = [
        name for name in part_names
        if not name.startswith("_") and name not in consumed
    ]
    if not visible_names:
        visible_names = [name for name in part_names if not name.startswith("_")]
    return visible_names


def _collect_parts_data(doc) -> list[tuple[str, pv.PolyData, tuple]]:
    """Collect visible part render data for trust rendering."""
    parts_data = []
    visible_names = _collect_visible_part_names(doc)
    logger.debug("Trust render parts: %s", visible_names)

    for index, name in enumerate(visible_names):
        part = doc.parts.get(name)
        if part is None or part.geometry is None:
            continue
        mesh = _part_to_pyvista(part)
        if mesh is None:
            continue
        color = _part_color(part.metadata or {}, index)
        parts_data.append((name, mesh, color))
        logger.debug("Trust render part '%s': %s points color=%s", name, mesh.n_points, color)

    return parts_data


def _compute_scene_metrics(parts_data, parameters: dict) -> SceneMetrics:
    """Compute scene bounds, extents, and dimension labels."""
    all_bounds = np.array([mesh.bounds for _, mesh, _ in parts_data])
    center = np.array([
        (all_bounds[:, 0].min() + all_bounds[:, 1].max()) / 2,
        (all_bounds[:, 2].min() + all_bounds[:, 3].max()) / 2,
        (all_bounds[:, 4].min() + all_bounds[:, 5].max()) / 2,
    ])
    sizes = {
        "X": all_bounds[:, 1].max() - all_bounds[:, 0].min(),
        "Y": all_bounds[:, 3].max() - all_bounds[:, 2].min(),
        "Z": all_bounds[:, 5].max() - all_bounds[:, 4].min(),
    }
    radius = max(sizes.values()) * 1.5
    named_dims = _find_named_dims(sizes, parameters)
    return SceneMetrics(center=center, radius=radius, sizes=sizes, named_dims=named_dims)


def _create_plotter(width: int, height: int) -> pv.Plotter:
    """Create the off-screen plotter for trust rendering."""
    n_rows = (len(VIEWS) + GRID_COLS - 1) // GRID_COLS
    plotter = pv.Plotter(
        shape=(n_rows, GRID_COLS),
        off_screen=True,
        window_size=[width, height],
    )
    plotter.set_background("white")
    return plotter


def _add_view_meshes(plotter: pv.Plotter, parts_data, mode: str) -> None:
    """Add all part meshes to the current subplot using the requested mode."""
    for _name, mesh, color in parts_data:
        if mode == "xray":
            plotter.add_mesh(
                mesh,
                color=color,
                opacity=0.15,
                show_edges=False,
                smooth_shading=False,
                ambient=0.4,
                diffuse=0.6,
            )
            dark = tuple(max(0.0, c - 0.3) for c in color)
            _add_feature_edges(plotter, mesh, color=dark, line_width=1.5)
        else:
            plotter.add_mesh(
                mesh,
                color=color,
                show_edges=False,
                opacity=0.97,
                smooth_shading=False,
                specular=0.3,
                specular_power=20,
                ambient=0.15,
                diffuse=0.85,
            )
            _add_feature_edges(plotter, mesh, color=(0, 0, 0), line_width=1.5)


def _maybe_add_view_labels(plotter: pv.Plotter, parts_data, mode: str) -> None:
    """Add part labels to the current subplot when useful."""
    if mode != "shaded" or not (1 < len(parts_data) <= 8):
        return

    centroids = np.array([mesh.center for _, mesh, _ in parts_data])
    labels = [name for name, _, _ in parts_data]
    plotter.add_point_labels(
        centroids, labels,
        font_size=8,
        text_color="black",
        bold=True,
        show_points=False,
        shape="rounded_rect",
        shape_color="white",
        shape_opacity=0.6,
        always_visible=True,
    )


def _maybe_add_dimension_overlay(plotter: pv.Plotter, view_label: str, mode: str, metrics: SceneMetrics) -> None:
    """Add orthographic dimension labels for the current subplot."""
    if mode != "ortho" or view_label not in _ORTHO_DIMS:
        return

    dim_a, dim_b = _ORTHO_DIMS[view_label]
    name_a, name_b = metrics.named_dims[dim_a], metrics.named_dims[dim_b]
    dim_text = f"{name_a}: {metrics.sizes[dim_a]:.1f}  {name_b}: {metrics.sizes[dim_b]:.1f}"
    plotter.add_text(dim_text, position="lower_left", font_size=8, color="black")


def _set_view_camera(plotter: pv.Plotter, pos_dir, view_up, parallel: bool, metrics: SceneMetrics) -> None:
    """Set camera state for one trust-render subplot."""
    direction = np.array(pos_dir, dtype=float)
    direction /= np.linalg.norm(direction)
    camera_position = metrics.center + direction * metrics.radius * 2.5
    plotter.camera_position = [
        camera_position.tolist(),
        metrics.center.tolist(),
        list(view_up),
    ]
    plotter.camera.parallel_projection = parallel
    if parallel:
        plotter.camera.parallel_scale = metrics.radius * 0.6
    plotter.reset_camera_clipping_range()


def _render_view(plotter: pv.Plotter, idx: int, parts_data, metrics: SceneMetrics) -> None:
    """Render one configured trust-render view into the plotter grid."""
    view_label, pos_dir, view_up, parallel, mode = VIEWS[idx]
    row, col = divmod(idx, GRID_COLS)
    plotter.subplot(row, col)

    _add_view_meshes(plotter, parts_data, mode)
    _add_axes_widget(plotter)
    _maybe_add_view_labels(plotter, parts_data, mode)
    _maybe_add_dimension_overlay(plotter, view_label, mode, metrics)
    _set_view_camera(plotter, pos_dir, view_up, parallel, metrics)
    plotter.add_title(view_label, font_size=10, color="black")


def _render_views(parts_data, metrics: SceneMetrics, width: int, height: int):
    """Render all configured trust-render subplots and return the screenshot array."""
    plotter = _create_plotter(width, height)
    for idx in range(len(VIEWS)):
        _render_view(plotter, idx, parts_data, metrics)
    screenshot = plotter.screenshot(return_img=True)
    plotter.close()
    return screenshot


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


def _add_feature_edges(plotter: pv.Plotter, mesh: pv.PolyData, color=(0, 0, 0),
                       line_width: float = 1.5):
    """Extract and add feature edges for a mesh (real geometric boundaries only)."""
    edges = mesh.extract_feature_edges(
        feature_angle=_FEATURE_ANGLE,
        boundary_edges=True,
        non_manifold_edges=False,
        manifold_edges=True,
    )
    if edges.n_points > 0:
        plotter.add_mesh(edges, color=color, line_width=line_width,
                         render_lines_as_tubes=False)


def render_trust(
    doc,
    output_path: str,
    title: Optional[str] = None,
    width: int = 1800,
    height: int = 1000,
) -> str:
    """
    Render a TiaCADDocument to a 6-panel trust PNG.

    Panels:
      Row 0: Iso shaded+edges | X-Ray transparent+edges | Top (XY)
      Row 1: Front (XZ) +dims | Side (YZ) +dims         | Bottom (XY)

    Args:
        doc: Parsed TiaCADDocument
        output_path: Where to write the PNG
        title: Optional title shown in the legend panel
        width: Output image width in pixels
        height: Output image height in pixels

    Returns:
        Absolute path to the written PNG
    """
    _maybe_start_xvfb()
    parts_data = _collect_parts_data(doc)

    if not parts_data:
        raise ValueError("No renderable geometry found in document")

    metrics = _compute_scene_metrics(parts_data, doc.parameters)
    description = ((doc.metadata or {}).get("description") or "").strip()
    screenshot = _render_views(parts_data, metrics, width, height)
    render_img = Image.fromarray(screenshot)
    final_img = _add_legend(render_img, parts_data, title, description, width, height)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(out))
    return str(out.resolve())


def _draw_legend_separator(draw: ImageDraw.ImageDraw, x0: int, y: int, legend_width: int) -> int:
    """Draw a horizontal separator line and return the next y position."""
    draw.line([(x0, y), (x0 + legend_width - 20, y)], fill=(180, 180, 180), width=1)
    return y + 10


def _draw_legend_title(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y: int,
    title: Optional[str],
    legend_width: int,
) -> int:
    """Draw the optional legend title and return the next y position."""
    if not title:
        return y

    draw.text((x0, y), title, fill=(30, 30, 30))
    y += 24
    return _draw_legend_separator(draw, x0, y, legend_width)


def _legend_part_layout(parts_data: list) -> tuple[int, int, int]:
    """Return swatch/gap/label layout for the parts legend."""
    many_parts = len(parts_data) > 12
    swatch = 10 if many_parts else 16
    gap = 3 if many_parts else 6
    max_label = 26 if many_parts else 22
    return swatch, gap, max_label


def _draw_parts_legend(draw: ImageDraw.ImageDraw, x0: int, y: int, parts_data: list) -> tuple[int, int, int]:
    """Draw the parts legend and return next y plus layout values."""
    draw.text((x0, y), "Parts", fill=(80, 80, 80))
    y += 20

    swatch, gap, max_label = _legend_part_layout(parts_data)
    for name, _mesh, color in parts_data:
        r, g, b = (int(c * 255) for c in color)
        draw.rectangle([x0, y, x0 + swatch, y + swatch], fill=(r, g, b), outline=(0, 0, 0))
        label = name if len(name) <= max_label else name[:max_label - 1] + "…"
        draw.text((x0 + swatch + gap, y + 1), label, fill=(30, 30, 30))
        y += swatch + gap

    return y, swatch, gap


def _draw_axes_legend(draw: ImageDraw.ImageDraw, x0: int, y: int, swatch: int, gap: int, legend_width: int) -> int:
    """Draw the axes legend block and return the next y position."""
    y += 10
    y = _draw_legend_separator(draw, x0, y, legend_width)
    draw.text((x0, y), "Axes", fill=(80, 80, 80))
    y += 18
    for axis_label, color in [("X", (200, 40, 40)), ("Y", (40, 160, 40)), ("Z", (40, 40, 200))]:
        draw.rectangle([x0, y, x0 + swatch, y + swatch], fill=color, outline=(0, 0, 0))
        draw.text((x0 + swatch + gap, y + 2), axis_label, fill=(30, 30, 30))
        y += swatch + gap
    return y


def _draw_description_legend(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y: int,
    description: str,
    legend_width: int,
    height: int,
) -> int:
    """Draw the optional trust-check description block and return the next y position."""
    if not description:
        return y

    y += 10
    y = _draw_legend_separator(draw, x0, y, legend_width)
    draw.text((x0, y), "Trust Check", fill=(80, 80, 80))
    y += 18
    for line in textwrap.wrap(description, width=32):
        if y + 12 > height:
            break
        draw.text((x0, y), line, fill=(50, 50, 50))
        y += 13
    return y


def _add_legend(
    render_img: Image.Image,
    parts_data: list,
    title: Optional[str],
    description: str,
    width: int,
    height: int,
) -> Image.Image:
    """Overlay a legend strip on the right side of the render image."""
    legend_width = 250
    final = Image.new("RGB", (width + legend_width, height), color=(245, 245, 245))
    final.paste(render_img, (0, 0))

    draw = ImageDraw.Draw(final)
    x0 = width + 10
    y = 20

    y = _draw_legend_title(draw, x0, y, title, legend_width)
    y, swatch, gap = _draw_parts_legend(draw, x0, y, parts_data)
    y = _draw_axes_legend(draw, x0, y, swatch, gap, legend_width)
    _draw_description_legend(draw, x0, y, description, legend_width, height)

    return final
