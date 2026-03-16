"""
3D Model Renderer for TiaCAD

Renders CadQuery models to PNG images using PyVista for visual validation.
Supports:
- Multiple camera angles (isometric, front, top, side)
- Material colors and transparency
- Multi-part assemblies
- Grid layouts for comparisons
"""

import logging
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile

logger = logging.getLogger(__name__)


class RenderError(Exception):
    """Error during rendering"""
    pass


class ModelRenderer:
    """
    Render TiaCAD models to PNG images using PyVista.

    Provides visual validation of 3D models with proper material colors,
    transparency, and multiple viewing angles.
    """

    # Standard camera angles for 3D visualization
    CAMERA_ANGLES = {
        'isometric': {
            'position': (1, 1, 1),
            'focal_point': (0, 0, 0),
            'viewup': (0, 0, 1),
            'description': 'Isometric view (3D perspective)'
        },
        'front': {
            'position': (0, -1, 0),
            'focal_point': (0, 0, 0),
            'viewup': (0, 0, 1),
            'description': 'Front view (looking along Y axis)'
        },
        'back': {
            'position': (0, 1, 0),
            'focal_point': (0, 0, 0),
            'viewup': (0, 0, 1),
            'description': 'Back view'
        },
        'top': {
            'position': (0, 0, 1),
            'focal_point': (0, 0, 0),
            'viewup': (0, 1, 0),
            'description': 'Top view (looking down Z axis)'
        },
        'bottom': {
            'position': (0, 0, -1),
            'focal_point': (0, 0, 0),
            'viewup': (0, 1, 0),
            'description': 'Bottom view'
        },
        'left': {
            'position': (-1, 0, 0),
            'focal_point': (0, 0, 0),
            'viewup': (0, 0, 1),
            'description': 'Left side view (looking along X axis)'
        },
        'right': {
            'position': (1, 0, 0),
            'focal_point': (0, 0, 0),
            'viewup': (0, 0, 1),
            'description': 'Right side view'
        }
    }

    def __init__(self, window_size: Tuple[int, int] = (1200, 900)):
        """
        Initialize renderer.

        Args:
            window_size: Tuple of (width, height) for render window
        """
        self.window_size = window_size
        self._check_pyvista()

    def _check_pyvista(self):
        """Check if PyVista is available"""
        try:
            import pyvista as pv
            self.pv = pv
            logger.debug(f"PyVista {pv.__version__} loaded successfully")
        except ImportError as e:
            raise RenderError(
                "PyVista not installed. Install with: pip install pyvista"
            ) from e

    def _part_to_mesh(self, part, color: Optional[Tuple[float, float, float, float]] = None):
        """
        Convert TiaCAD Part to PyVista mesh.

        Args:
            part: Part object with CadQuery geometry
            color: Optional RGBA color tuple (0.0-1.0 range)

        Returns:
            PyVista PolyData mesh
        """
        try:
            # Get CadQuery shape and tessellate
            shape = part.geometry.val()
            vertices, triangles = shape.tessellate(0.1)

            # Convert to numpy arrays
            verts = np.array([[v.x, v.y, v.z] for v in vertices])

            # PyVista faces format: [n_points, p0, p1, p2, n_points, p0, p1, p2, ...]
            faces = []
            for tri in triangles:
                faces.extend([3, tri[0], tri[1], tri[2]])
            faces = np.array(faces)

            # Create PyVista mesh
            mesh = self.pv.PolyData(verts, faces)

            logger.debug(
                f"Created mesh for '{part.name}': "
                f"{len(verts)} vertices, {len(triangles)} triangles"
            )

            return mesh

        except Exception as e:
            raise RenderError(
                f"Failed to create mesh for part '{part.name}': {str(e)}"
            ) from e

    def render_part(
        self,
        part,
        output_path: str,
        views: List[str] = ['isometric', 'front', 'top', 'right'],
        color: Optional[Tuple[float, float, float, float]] = None,
        background: str = 'white',
        show_edges: bool = True
    ) -> List[str]:
        """
        Render a single part from multiple camera angles.

        Args:
            part: Part object to render
            output_path: Base path for output files (without extension)
            views: List of camera angles to render
            color: Optional RGBA color tuple (overrides part metadata)
            background: Background color name or RGB tuple
            show_edges: Whether to show mesh edges

        Returns:
            List of generated file paths

        Example:
            >>> renderer = ModelRenderer()
            >>> paths = renderer.render_part(
            ...     part,
            ...     "output/box",
            ...     views=['isometric', 'front'],
            ...     color=(1.0, 0.0, 0.0, 1.0)
            ... )
            >>> # Creates: output/box_isometric.png, output/box_front.png
        """
        try:
            # Use part metadata color if not provided
            if color is None and 'color' in part.metadata:
                color = part.metadata['color']

            # Create mesh
            mesh = self._part_to_mesh(part, color)

            # Generate renders for each view
            output_files = []
            for view_name in views:
                if view_name not in self.CAMERA_ANGLES:
                    logger.warning(f"Unknown view '{view_name}', skipping")
                    continue

                output_file = f"{output_path}_{view_name}.png"
                self._render_mesh(
                    mesh,
                    output_file,
                    view_name,
                    color,
                    background,
                    show_edges
                )
                output_files.append(output_file)
                logger.info(f"Rendered {view_name} view to {output_file}")

            return output_files

        except Exception as e:
            raise RenderError(
                f"Failed to render part '{part.name}': {str(e)}"
            ) from e

    def _render_mesh(
        self,
        mesh,
        output_file: str,
        view_name: str,
        color: Optional[Tuple[float, float, float, float]],
        background: str,
        show_edges: bool
    ):
        """Internal method to render a mesh with specific camera angle"""

        # Create off-screen plotter
        plotter = self.pv.Plotter(
            off_screen=True,
            window_size=self.window_size
        )

        # Set background
        plotter.set_background(background)

        # Add mesh with material properties
        if color:
            r, g, b, a = color
            plotter.add_mesh(
                mesh,
                color=[r, g, b],
                opacity=a,
                show_edges=show_edges,
                edge_color='gray' if show_edges else None,
                lighting=True,
                specular=0.5,
                specular_power=15,
                ambient=0.2,
                diffuse=0.8
            )
        else:
            # Default gray material
            plotter.add_mesh(
                mesh,
                color='lightgray',
                show_edges=show_edges,
                edge_color='gray' if show_edges else None,
                lighting=True
            )

        # Set camera position for this view
        angle = self.CAMERA_ANGLES[view_name]

        # Calculate camera distance based on model bounds
        bounds = mesh.bounds
        size = max(
            bounds[1] - bounds[0],  # x
            bounds[3] - bounds[2],  # y
            bounds[5] - bounds[4]   # z
        )
        distance = size * 2.5  # Camera distance multiplier

        # Normalize position vector and scale by distance
        pos = np.array(angle['position'])
        pos = pos / np.linalg.norm(pos) * distance

        plotter.camera_position = [
            pos.tolist(),
            angle['focal_point'],
            angle['viewup']
        ]

        # Enable anti-aliasing for smoother edges
        plotter.enable_anti_aliasing()

        # Render and save
        plotter.screenshot(output_file)
        plotter.close()

    def _build_assembly_plotter(self, parts_registry, view_name: str,
                                window_size: Tuple[int, int], background: str,
                                show_edges: bool):
        """Create a configured plotter with all assembly parts and camera set for view_name."""
        plotter = self.pv.Plotter(off_screen=True, window_size=window_size)
        plotter.set_background(background)

        all_bounds = []
        for part_name in parts_registry.list_parts():
            part = parts_registry.get(part_name)
            color = part.metadata.get('color')
            mesh = self._part_to_mesh(part, color)
            all_bounds.append(mesh.bounds)
            if color:
                r, g, b, a = color
                plotter.add_mesh(mesh, color=[r, g, b], opacity=a,
                                 show_edges=show_edges,
                                 edge_color='gray' if show_edges else None,
                                 lighting=True, specular=0.5, specular_power=15,
                                 ambient=0.2, diffuse=0.8)
            else:
                plotter.add_mesh(mesh, color='lightgray', show_edges=show_edges, lighting=True)

        if all_bounds:
            arr = np.array(all_bounds)
            size = max(arr[:, 1].max() - arr[:, 0].min(),
                       arr[:, 3].max() - arr[:, 2].min(),
                       arr[:, 5].max() - arr[:, 4].min())
            angle = self.CAMERA_ANGLES[view_name]
            pos = np.array(angle['position'])
            pos = pos / np.linalg.norm(pos) * (size * 2.5)
            plotter.camera_position = [pos.tolist(), angle['focal_point'], angle['viewup']]

        plotter.enable_anti_aliasing()
        return plotter

    def _calculate_grid_layout(self, views: List[str], grid_size: Optional[Tuple[int, int]],
                                cell_size: Tuple[int, int], title: Optional[str],
                                show_labels: bool) -> Tuple[int, int, int, int, int, int]:
        """Compute grid dimensions and composite image size. Returns (cols, rows, width, height, title_h, label_h)."""
        if grid_size is None:
            cols = int(np.ceil(np.sqrt(len(views))))
            rows = int(np.ceil(len(views) / cols))
        else:
            cols, rows = grid_size
        title_h = 60 if title else 0
        label_h = 30 if show_labels else 0
        return cols, rows, cols * cell_size[0], title_h + rows * (cell_size[1] + label_h), title_h, label_h

    def _load_fonts(self):
        """Load DejaVu fonts, falling back to PIL default."""
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except Exception:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        return title_font, label_font

    def _paste_view_cell(self, composite, draw, view_img, col: int, row: int,
                         cell_size: Tuple[int, int], title_h: int, label_h: int,
                         view_name: str, show_labels: bool, label_font):
        """Paste a rendered view into the composite and optionally draw its label."""
        x = col * cell_size[0]
        y = title_h + row * (cell_size[1] + label_h)
        composite.paste(view_img, (x, y))
        if show_labels:
            label_text = view_name.title()
            bbox = draw.textbbox((0, 0), label_text, font=label_font)
            label_x = x + (cell_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((label_x, y + cell_size[1] + 5), label_text, fill='black', font=label_font)

    def render_assembly(
        self,
        parts_registry,
        output_path: str,
        views: List[str] = ['isometric', 'front', 'top'],
        background: str = 'white',
        show_edges: bool = False
    ) -> List[str]:
        """
        Render entire assembly with all parts and materials.

        Args:
            parts_registry: PartRegistry with all parts
            output_path: Base path for output files
            views: List of camera angles to render
            background: Background color
            show_edges: Whether to show mesh edges

        Returns:
            List of generated file paths
        """
        try:
            output_files = []
            for view_name in views:
                if view_name not in self.CAMERA_ANGLES:
                    logger.warning(f"Unknown view '{view_name}', skipping")
                    continue
                output_file = f"{output_path}_{view_name}.png"
                plotter = self._build_assembly_plotter(parts_registry, view_name,
                                                       self.window_size, background, show_edges)
                plotter.screenshot(output_file)
                plotter.close()
                output_files.append(output_file)
                logger.info(f"Rendered assembly ({len(parts_registry.list_parts())} parts) "
                            f"{view_name} view to {output_file}")
            return output_files
        except Exception as e:
            raise RenderError(f"Failed to render assembly: {str(e)}") from e

    def _render_views_into_composite(self, composite, draw, parts_registry, views,
                                     cols: int, rows: int, cell_size: Tuple[int, int],
                                     background: str, show_edges: bool,
                                     title_h: int, label_h: int, show_labels: bool, label_font) -> None:
        """Render each view into a temp PNG and paste it into the composite grid image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for idx, view_name in enumerate(views):
                if view_name not in self.CAMERA_ANGLES:
                    logger.warning(f"Unknown view '{view_name}', skipping")
                    continue
                col, row = idx % cols, idx // cols
                if row >= rows:
                    break
                temp_output = Path(tmpdir) / f"view_{idx}.png"
                plotter = self._build_assembly_plotter(parts_registry, view_name,
                                                       cell_size, background, show_edges)
                plotter.screenshot(str(temp_output))
                plotter.close()
                self._paste_view_cell(composite, draw, Image.open(temp_output),
                                      col, row, cell_size, title_h, label_h,
                                      view_name, show_labels, label_font)
                logger.debug(f"Added {view_name} view to grid at ({col}, {row})")

    def render_grid(
        self,
        parts_registry,
        output_path: str,
        views: List[str] = ['isometric', 'front', 'top', 'right'],
        grid_size: Optional[Tuple[int, int]] = None,
        cell_size: Tuple[int, int] = (600, 450),
        background: str = 'white',
        show_labels: bool = True,
        title: Optional[str] = None,
        show_edges: bool = False
    ) -> str:
        """Render multiple views into a single grid composite image."""
        try:
            cols, rows, comp_w, comp_h, title_h, label_h = \
                self._calculate_grid_layout(views, grid_size, cell_size, title, show_labels)
            composite = Image.new('RGB', (comp_w, comp_h), 'white')
            draw = ImageDraw.Draw(composite)
            title_font, label_font = self._load_fonts()
            if title:
                bbox = draw.textbbox((0, 0), title, font=title_font)
                draw.text(((comp_w - (bbox[2] - bbox[0])) // 2, 15), title, fill='black', font=title_font)
            self._render_views_into_composite(composite, draw, parts_registry, views,
                                              cols, rows, cell_size, background, show_edges,
                                              title_h, label_h, show_labels, label_font)
            composite.save(output_path)
            logger.info(f"Created grid composite ({cols}x{rows}) with {len(views)} views: {output_path}")
            return output_path
        except Exception as e:
            raise RenderError(f"Failed to create grid composite: {str(e)}") from e


# Convenience functions

def render_part(
    part,
    output_path: str,
    views: List[str] = ['isometric', 'front', 'top', 'right'],
    **kwargs
) -> List[str]:
    """
    Convenience function to render a single part.

    Args:
        part: Part object to render
        output_path: Base path for output files
        views: List of camera angles
        **kwargs: Additional arguments passed to ModelRenderer.render_part()

    Returns:
        List of generated file paths
    """
    renderer = ModelRenderer()
    return renderer.render_part(part, output_path, views=views, **kwargs)


def render_assembly(
    parts_registry,
    output_path: str,
    views: List[str] = ['isometric', 'front', 'top'],
    **kwargs
) -> List[str]:
    """
    Convenience function to render an assembly.

    Args:
        parts_registry: PartRegistry with all parts
        output_path: Base path for output files
        views: List of camera angles
        **kwargs: Additional arguments passed to ModelRenderer.render_assembly()

    Returns:
        List of generated file paths
    """
    renderer = ModelRenderer()
    return renderer.render_assembly(parts_registry, output_path, views=views, **kwargs)
