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
from typing import Dict, List, Tuple, Optional, Union
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

        Example:
            >>> doc = TiaCADParser.parse_file("assembly.yaml")
            >>> renderer = ModelRenderer()
            >>> paths = renderer.render_assembly(
            ...     doc.parts,
            ...     "output/assembly",
            ...     views=['isometric']
            ... )
        """
        try:
            output_files = []

            for view_name in views:
                if view_name not in self.CAMERA_ANGLES:
                    logger.warning(f"Unknown view '{view_name}', skipping")
                    continue

                # Create off-screen plotter
                plotter = self.pv.Plotter(
                    off_screen=True,
                    window_size=self.window_size
                )
                plotter.set_background(background)

                # Add all parts to scene
                all_bounds = []
                for part_name in parts_registry.list_parts():
                    part = parts_registry.get(part_name)

                    # Get color from metadata
                    color = part.metadata.get('color')

                    # Create mesh
                    mesh = self._part_to_mesh(part, color)
                    all_bounds.append(mesh.bounds)

                    # Add to plotter
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
                        plotter.add_mesh(
                            mesh,
                            color='lightgray',
                            show_edges=show_edges,
                            lighting=True
                        )

                # Calculate overall scene bounds
                if all_bounds:
                    all_bounds_array = np.array(all_bounds)
                    scene_bounds = [
                        all_bounds_array[:, 0].min(),  # x_min
                        all_bounds_array[:, 1].max(),  # x_max
                        all_bounds_array[:, 2].min(),  # y_min
                        all_bounds_array[:, 3].max(),  # y_max
                        all_bounds_array[:, 4].min(),  # z_min
                        all_bounds_array[:, 5].max()   # z_max
                    ]

                    size = max(
                        scene_bounds[1] - scene_bounds[0],
                        scene_bounds[3] - scene_bounds[2],
                        scene_bounds[5] - scene_bounds[4]
                    )
                    distance = size * 2.5

                    # Set camera
                    angle = self.CAMERA_ANGLES[view_name]
                    pos = np.array(angle['position'])
                    pos = pos / np.linalg.norm(pos) * distance

                    plotter.camera_position = [
                        pos.tolist(),
                        angle['focal_point'],
                        angle['viewup']
                    ]

                plotter.enable_anti_aliasing()

                # Save
                output_file = f"{output_path}_{view_name}.png"
                plotter.screenshot(output_file)
                plotter.close()

                output_files.append(output_file)
                logger.info(
                    f"Rendered assembly ({len(parts_registry.list_parts())} parts) "
                    f"{view_name} view to {output_file}"
                )

            return output_files

        except Exception as e:
            raise RenderError(f"Failed to render assembly: {str(e)}") from e

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
        """
        Render multiple views into a single grid image.

        Creates a composite image with multiple camera angles arranged in a grid,
        perfect for technical documentation and model verification.

        Args:
            parts_registry: PartRegistry with all parts
            output_path: Path for output composite image
            views: List of camera angles to render
            grid_size: Tuple of (columns, rows). Auto-calculated if None
            cell_size: Size of each cell in pixels (width, height)
            background: Background color
            show_labels: Whether to show view labels
            title: Optional title for the composite image
            show_edges: Whether to show mesh edges

        Returns:
            Path to generated composite image

        Example:
            >>> renderer = ModelRenderer()
            >>> renderer.render_grid(
            ...     doc.parts,
            ...     "output/model_sheet.png",
            ...     views=['isometric', 'front', 'top', 'right'],
            ...     title="Multi-Material Assembly"
            ... )
        """
        try:
            # Auto-calculate grid size if not provided
            if grid_size is None:
                num_views = len(views)
                # Try to make a roughly square grid
                cols = int(np.ceil(np.sqrt(num_views)))
                rows = int(np.ceil(num_views / cols))
                grid_size = (cols, rows)
            else:
                cols, rows = grid_size

            # Calculate composite image size
            title_height = 60 if title else 0
            label_height = 30 if show_labels else 0

            composite_width = cols * cell_size[0]
            composite_height = title_height + rows * (cell_size[1] + label_height)

            # Create composite image
            composite = Image.new('RGB', (composite_width, composite_height), 'white')
            draw = ImageDraw.Draw(composite)

            # Try to load a nice font, fallback to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()

            # Draw title if provided
            if title:
                # Center the title
                bbox = draw.textbbox((0, 0), title, font=title_font)
                text_width = bbox[2] - bbox[0]
                text_x = (composite_width - text_width) // 2
                draw.text((text_x, 15), title, fill='black', font=title_font)

            # Render each view to temporary file
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                for idx, view_name in enumerate(views):
                    if view_name not in self.CAMERA_ANGLES:
                        logger.warning(f"Unknown view '{view_name}', skipping")
                        continue

                    # Calculate grid position
                    col = idx % cols
                    row = idx // cols

                    # Skip if beyond grid bounds
                    if row >= rows:
                        break

                    # Render view to temporary file
                    temp_output = tmpdir_path / f"view_{idx}.png"

                    # Create off-screen plotter
                    plotter = self.pv.Plotter(
                        off_screen=True,
                        window_size=cell_size
                    )
                    plotter.set_background(background)

                    # Add all parts to scene
                    all_bounds = []
                    for part_name in parts_registry.list_parts():
                        part = parts_registry.get(part_name)
                        color = part.metadata.get('color')
                        mesh = self._part_to_mesh(part, color)
                        all_bounds.append(mesh.bounds)

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
                            plotter.add_mesh(
                                mesh,
                                color='lightgray',
                                show_edges=show_edges,
                                lighting=True
                            )

                    # Set camera for this view
                    if all_bounds:
                        all_bounds_array = np.array(all_bounds)
                        size = max(
                            all_bounds_array[:, 1].max() - all_bounds_array[:, 0].min(),
                            all_bounds_array[:, 3].max() - all_bounds_array[:, 2].min(),
                            all_bounds_array[:, 5].max() - all_bounds_array[:, 4].min()
                        )
                        distance = size * 2.5

                        angle = self.CAMERA_ANGLES[view_name]
                        pos = np.array(angle['position'])
                        pos = pos / np.linalg.norm(pos) * distance

                        plotter.camera_position = [
                            pos.tolist(),
                            angle['focal_point'],
                            angle['viewup']
                        ]

                    plotter.enable_anti_aliasing()
                    plotter.screenshot(str(temp_output))
                    plotter.close()

                    # Load rendered image and paste into composite
                    view_img = Image.open(temp_output)

                    # Calculate paste position
                    x_pos = col * cell_size[0]
                    y_pos = title_height + row * (cell_size[1] + label_height)

                    composite.paste(view_img, (x_pos, y_pos))

                    # Draw label if enabled
                    if show_labels:
                        label_text = view_name.title()
                        label_y = y_pos + cell_size[1] + 5

                        # Center label under image
                        bbox = draw.textbbox((0, 0), label_text, font=label_font)
                        text_width = bbox[2] - bbox[0]
                        label_x = x_pos + (cell_size[0] - text_width) // 2

                        draw.text((label_x, label_y), label_text, fill='black', font=label_font)

                    logger.debug(f"Added {view_name} view to grid at ({col}, {row})")

            # Save composite image
            composite.save(output_path)
            logger.info(
                f"Created grid composite ({cols}x{rows}) with {len(views)} views: {output_path}"
            )

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
