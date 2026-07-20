"""
Trust renderer for TiaCAD — multi-view colored renders for visual verification.

Renders each part in a distinct color with 8 viewpoints (2×4 grid):
  Row 0: Iso front (shaded + edges), Iso rear (shaded + edges), X-Ray, Top (XY)
  Row 1: Front (XZ), Rear (XZ), Side (YZ), Bottom (XY)

The two isometrics view from opposite diagonals so no side face is hidden from
both — a part mirrored to the wrong side or a feature on a back face shows up in
at least one view, instead of passing review unseen.

Feature edges replace the old cell-count threshold — draws only real geometric
boundaries (dihedral angle > 40°), so boxes get clean outlines and curved
surfaces get rim/silhouette edges without tessellation noise.

Orthographic panels show bounding-box dimensions so you can immediately verify
"yes, this is 100×80×12mm" without guessing from visual scale.

X-Ray panel renders geometry transparent so internal features, standoffs, and
boolean cuts are visible through the shell.

Composite decomposition: when the final part is a union of several components
(a printable assembly fused into one solid), the renderer walks the operation
DAG and draws each additive component in its own color, with subtracted parts
shown as translucent-red voids in the X-Ray panel. Otherwise a flat single-color
solid would hide whether the parts are actually connected or correctly placed.
Metadata colors are ignored for these components — assembly parts often share one
color, which would defeat the decomposition.

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
from typing import List, Optional, Tuple

import pyvista as pv
import numpy as np
import vtk
from PIL import Image, ImageDraw
from ..backend_support import tessellate_part
from ..validation.validation_types import Severity, ValidationIssue

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
# 8 panels in a 2×4 grid. The two isometrics view from opposite diagonals
# (front-right-top and back-left-top) so no side face is hidden from both — a
# part mirrored to the wrong side or a feature on a back face is visible in at
# least one. X-Ray reveals internal/occluded features at the front angle.
#
# Row 0 (spatial): Iso front | Iso rear | X-Ray | Top
# Row 1 (orthographic + dims): Front | Rear | Side | Bottom
VIEWS = [
    ("Iso (front)",   ( 1.0, -1.2,  0.8), (0, 0, 1), False, "shaded"),  # row0 col0
    ("Iso (rear)",    (-1.0,  1.2,  0.8), (0, 0, 1), False, "shaded"),  # row0 col1
    ("X-Ray",         ( 1.0, -1.2,  0.8), (0, 0, 1), False, "xray"),    # row0 col2
    ("Top      (XY)", ( 0.0,  0.0,  1.0), (0, 1, 0), True,  "ortho"),   # row0 col3
    ("Front    (XZ)", ( 0.0, -1.0,  0.0), (0, 0, 1), True,  "ortho"),   # row1 col0
    ("Rear     (XZ)", ( 0.0,  1.0,  0.0), (0, 0, 1), True,  "ortho"),   # row1 col1
    ("Side     (YZ)", ( 1.0,  0.0,  0.0), (0, 0, 1), True,  "ortho"),   # row1 col2
    ("Bottom   (XY)", ( 0.0,  0.0, -1.0), (0, 1, 0), True,  "ortho"),   # row1 col3
]
GRID_COLS = 4

# Which two dimensions to display for each orthographic view
_ORTHO_DIMS = {
    "Top      (XY)":  ("X", "Y"),
    "Front    (XZ)":  ("X", "Z"),
    "Rear     (XZ)":  ("X", "Z"),
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
                if isinstance(name, dict):
                    if "pattern" in name:
                        prefix = f"{name['pattern']}_"
                        consumed.update(p for p in part_names if p.startswith(prefix))
                    # {"range": ...} entries reference already-consumed pattern
                    # instances by name elsewhere in the DAG; nothing new to mark.
                else:
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


def _collect_component_parts(doc) -> tuple[list, list]:
    """
    Walk the final part's operation DAG and split its source leaves into
    additive (union ingredients) and subtractive (difference cutouts).

    Each returned name is a part in the registry at its final position. Unions
    are flattened to their leaves; a difference sends its base down the current
    sign and its subtracted inputs down the flipped sign. Transforms, patterns,
    finishing ops, intersections, and primitives are opaque leaves — their
    registry geometry is what we draw.
    """
    from ..parser.tiacad_parser import resolve_default_part_name

    operations = doc.operations or {}
    try:
        root = resolve_default_part_name(doc.parts, operations, doc.export_config)
    except Exception:
        return [], []

    additive: list = []
    subtractive: list = []
    visited: set = set()

    def walk(name: str, is_additive: bool) -> None:
        if name in visited:
            return
        visited.add(name)
        op = operations.get(name)
        if op is None:
            (additive if is_additive else subtractive).append(name)
            return
        if op.get("type") == "boolean":
            operation = op.get("operation")
            if operation == "union":
                for inp in op.get("inputs", []):
                    walk(inp, is_additive)
                return
            if operation == "difference":
                base = op.get("base")
                if base:
                    walk(base, is_additive)
                for sub in op.get("subtract", []):
                    walk(sub, not is_additive)
                return
        # transform / pattern / finishing / intersection / unknown → opaque leaf
        (additive if is_additive else subtractive).append(name)

    walk(root, True)
    return additive, subtractive


def _build_component_data(doc, names: list, palette_offset: int = 0):
    """Build (name, mesh, color) tuples for named parts using distinct palette
    colors. Metadata colors are deliberately ignored — assembly parts frequently
    share one color, which would defeat the whole point of decomposition."""
    data = []
    for i, name in enumerate(names):
        if name not in doc.parts:
            continue
        part = doc.parts.get(name)
        if part is None or part.geometry is None:
            continue
        mesh = _part_to_pyvista(part)
        if mesh is None:
            continue
        color = _hex_to_rgb_float(PART_PALETTE[(palette_offset + i) % len(PART_PALETTE)])
        data.append((name, mesh, color))
    return data


def _collect_render_data(doc) -> tuple[list, list]:
    """
    Return (solids, voids) render tuples.

    When the final part is a single composite — a union/difference tree with more
    than one additive component — decompose it: each additive component gets a
    distinct color and each subtracted component becomes a translucent-red void
    (shown in the X-Ray panel), so part identity AND cutouts stay visible instead
    of collapsing into one flat-colored solid. Otherwise fall back to plain
    visible-part rendering (already-separate multi-part scenes, single primitives).
    """
    visible = _collect_visible_part_names(doc)
    if len(visible) == 1 and visible[0] in (doc.operations or {}):
        additive, subtractive = _collect_component_parts(doc)
        if len(additive) > 1:
            solids = _build_component_data(doc, additive)
            if len(solids) > 1:
                voids = _build_component_data(doc, subtractive)
                return solids, voids
    return _collect_parts_data(doc), []


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


_VOID_COLOR = (0.85, 0.15, 0.15)  # translucent red for subtracted (cutout) parts


def _add_view_meshes(plotter: pv.Plotter, parts_data, voids_data, mode: str) -> None:
    """Add all part meshes to the current subplot using the requested mode.

    Subtracted parts (voids) are drawn only in the X-Ray panel: they sit inside
    the solid components, so opaque panels would occlude them anyway — X-Ray is
    exactly where a cutout should read.
    """
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
                opacity=1.0,
                smooth_shading=False,
                specular=0.3,
                specular_power=20,
                ambient=0.15,
                diffuse=0.85,
            )
            _add_feature_edges(plotter, mesh, color=(0, 0, 0), line_width=1.5)

    if mode == "xray":
        for _name, mesh, _color in voids_data:
            plotter.add_mesh(
                mesh,
                color=_VOID_COLOR,
                opacity=0.35,
                show_edges=False,
                smooth_shading=False,
                ambient=0.5,
                diffuse=0.5,
            )
            _add_feature_edges(plotter, mesh, color=(0.5, 0.0, 0.0), line_width=1.2)


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


def _render_view(plotter: pv.Plotter, idx: int, parts_data, voids_data, metrics: SceneMetrics) -> None:
    """Render one configured trust-render view into the plotter grid."""
    view_label, pos_dir, view_up, parallel, mode = VIEWS[idx]
    row, col = divmod(idx, GRID_COLS)
    plotter.subplot(row, col)

    _add_view_meshes(plotter, parts_data, voids_data, mode)
    _add_axes_widget(plotter)
    _maybe_add_view_labels(plotter, parts_data, mode)
    _maybe_add_dimension_overlay(plotter, view_label, mode, metrics)
    _set_view_camera(plotter, pos_dir, view_up, parallel, metrics)
    plotter.add_title(view_label, font_size=10, color="black")


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


_ISSUE_MARKER_COLOR = {
    Severity.ERROR: (230, 57, 70),      # vivid red
    Severity.WARNING: (255, 152, 0),    # vivid orange
    Severity.INFO: (33, 150, 243),      # vivid blue
}
_ISSUE_MARKER_RADIUS = 10


def _subplot_pixel_rect(renderer, width: int, height: int) -> tuple:
    """Return (x0, y0, x1, y1) pixel rect for a subplot, top-left image origin."""
    vxmin, vymin, vxmax, vymax = renderer.GetViewport()
    x0, x1 = vxmin * width, vxmax * width
    # VTK viewports are bottom-left origin; flip to top-left for image coords.
    y0, y1 = height - vymax * height, height - vymin * height
    return x0, y0, x1, y1


def _project_world_to_pixel(renderer, point: Tuple[float, float, float], height: int) -> Tuple[int, int]:
    """Project a 3D world point through one subplot's active camera to an image pixel."""
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()
    coord.SetValue(*point)
    display_x, display_y = coord.GetComputedDisplayValue(renderer)
    return display_x, height - display_y


def _draw_issue_marker(draw: ImageDraw.ImageDraw, px: float, py: float, color: tuple) -> None:
    """Draw a crosshair-circle marker pointing at one validation issue's location."""
    r = _ISSUE_MARKER_RADIUS
    draw.ellipse([px - r, py - r, px + r, py + r], outline=color, width=3)
    draw.line([px - r - 5, py, px - r + 3, py], fill=color, width=2)
    draw.line([px + r - 3, py, px + r + 5, py], fill=color, width=2)
    draw.line([px, py - r - 5, px, py - r + 3], fill=color, width=2)
    draw.line([px, py + r - 3, px, py + r + 5], fill=color, width=2)


def _annotate_issues(
    render_img: Image.Image,
    plotter: pv.Plotter,
    issues: Optional[List[ValidationIssue]],
    width: int,
    height: int,
) -> None:
    """Mark each located validation issue on every panel, in that panel's own view. Mutates render_img in place."""
    located = [issue for issue in (issues or []) if issue.world_position is not None]
    if not located:
        return

    draw = ImageDraw.Draw(render_img)
    for renderer in plotter.renderers:
        x0, y0, x1, y1 = _subplot_pixel_rect(renderer, width, height)
        for issue in located:
            px, py = _project_world_to_pixel(renderer, issue.world_position, height)
            if x0 <= px <= x1 and y0 <= py <= y1:
                color = _ISSUE_MARKER_COLOR.get(issue.severity, (150, 150, 150))
                _draw_issue_marker(draw, px, py, color)


def render_trust(
    doc,
    output_path: str,
    title: Optional[str] = None,
    width: int = 2200,
    height: int = 1000,
    issues: Optional[List[ValidationIssue]] = None,
) -> str:
    """
    Render a TiaCADDocument to an 8-panel trust PNG.

    Panels:
      Row 0: Iso front (shaded+edges) | Iso rear (shaded+edges) | X-Ray | Top (XY)
      Row 1: Front (XZ) +dims | Rear (XZ) +dims | Side (YZ) +dims | Bottom (XY)

    A composite final part (multiple components fused by union) is decomposed so
    each component renders in a distinct color, with subtracted parts shown as
    translucent-red voids in the X-Ray panel. See `_collect_render_data`.

    Args:
        doc: Parsed TiaCADDocument
        output_path: Where to write the PNG
        title: Optional title shown in the legend panel
        width: Output image width in pixels
        height: Output image height in pixels
        issues: Optional validation issues to annotate directly on the render.
            Only issues with a `world_position` are drawn; each is projected
            through every panel's own camera, so it lands in the correct spot
            in each view (isometric, ortho, X-ray) rather than one fixed panel.

    Returns:
        Absolute path to the written PNG
    """
    _maybe_start_xvfb()
    parts_data, voids_data = _collect_render_data(doc)

    if not parts_data:
        raise ValueError("No renderable geometry found in document")

    metrics = _compute_scene_metrics(parts_data, doc.parameters)
    description = ((doc.metadata or {}).get("description") or "").strip()
    plotter = _create_plotter(width, height)
    for idx in range(len(VIEWS)):
        _render_view(plotter, idx, parts_data, voids_data, metrics)
    screenshot = plotter.screenshot(return_img=True)
    render_img = Image.fromarray(screenshot)
    _annotate_issues(render_img, plotter, issues, width, height)
    plotter.close()
    final_img = _add_legend(render_img, parts_data, voids_data, title, description, width, height)

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


def _draw_voids_legend(draw: ImageDraw.ImageDraw, x0: int, y: int, voids_data: list,
                       swatch: int, gap: int, legend_width: int) -> int:
    """Draw the cutouts (subtracted parts) legend block and return next y."""
    if not voids_data:
        return y
    y += 10
    y = _draw_legend_separator(draw, x0, y, legend_width)
    draw.text((x0, y), "Cutouts (X-Ray)", fill=(80, 80, 80))
    y += 18
    r, g, b = (int(c * 255) for c in _VOID_COLOR)
    max_label = 22
    for name, _mesh, _color in voids_data:
        draw.rectangle([x0, y, x0 + swatch, y + swatch], fill=(r, g, b), outline=(0, 0, 0))
        label = name if len(name) <= max_label else name[:max_label - 1] + "…"
        draw.text((x0 + swatch + gap, y + 1), label, fill=(30, 30, 30))
        y += swatch + gap
    return y


def _add_legend(
    render_img: Image.Image,
    parts_data: list,
    voids_data: list,
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
    y = _draw_voids_legend(draw, x0, y, voids_data, swatch, gap, legend_width)
    y = _draw_axes_legend(draw, x0, y, swatch, gap, legend_width)
    _draw_description_legend(draw, x0, y, description, legend_width, height)

    return final
