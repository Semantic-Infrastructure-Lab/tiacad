"""
Tests for ModelRenderer - 3D visualization to PNG

These tests generate visual output files that can be manually inspected
to verify rendering quality, colors, and materials.
"""

import pytest
from pathlib import Path
import cadquery as cq

from tiacad_core.part import Part, PartRegistry
from tiacad_core.visualization.renderer import (
    ModelRenderer,
    RenderError,
    render_part,
    render_assembly
)


class TestModelRendererInit:
    """Test renderer initialization"""

    def test_init_success(self):
        """Renderer should initialize with PyVista available"""
        try:
            renderer = ModelRenderer()
            assert renderer.pv is not None
            assert renderer.window_size == (1200, 900)
        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_init_custom_window_size(self):
        """Can specify custom window size"""
        try:
            renderer = ModelRenderer(window_size=(800, 600))
            assert renderer.window_size == (800, 600)
        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_camera_angles_defined(self):
        """Should have standard camera angles defined"""
        try:
            renderer = ModelRenderer()
            assert 'isometric' in renderer.CAMERA_ANGLES
            assert 'front' in renderer.CAMERA_ANGLES
            assert 'top' in renderer.CAMERA_ANGLES
            assert 'right' in renderer.CAMERA_ANGLES

            # Check angle structure
            iso = renderer.CAMERA_ANGLES['isometric']
            assert 'position' in iso
            assert 'focal_point' in iso
            assert 'viewup' in iso
            assert 'description' in iso

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise


class TestSinglePartRendering:
    """Test rendering individual parts"""

    @pytest.fixture
    def simple_box(self):
        """Create simple box part"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        return Part(name="test_box", geometry=geometry)

    @pytest.fixture
    def colored_box(self):
        """Create box with color"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        return Part(
            name="red_box",
            geometry=geometry,
            metadata={'color': (1.0, 0.0, 0.0, 1.0)}  # Red
        )

    @pytest.fixture
    def transparent_box(self):
        """Create transparent box"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        return Part(
            name="glass_box",
            geometry=geometry,
            metadata={'color': (0.0, 0.5, 1.0, 0.3)}  # Transparent blue
        )

    @pytest.fixture
    def cylinder(self):
        """Create cylinder"""
        geometry = cq.Workplane("XY").cylinder(20, 5)
        return Part(
            name="cylinder",
            geometry=geometry,
            metadata={'color': (0.0, 1.0, 0.0, 1.0)}  # Green
        )

    def test_render_simple_box(self, simple_box, tmp_path):
        """Render simple box without color"""
        output_path = tmp_path / "simple_box"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                simple_box,
                str(output_path),
                views=['isometric']
            )

            # Verify file created
            assert len(files) == 1
            assert Path(files[0]).exists()
            assert Path(files[0]).stat().st_size > 1000  # Non-trivial size

            print(f"\n✓ Rendered simple box to: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_colored_box(self, colored_box, tmp_path):
        """Render box with red color"""
        output_path = tmp_path / "colored_box"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                colored_box,
                str(output_path),
                views=['isometric', 'front']
            )

            # Verify both views created
            assert len(files) == 2
            for f in files:
                assert Path(f).exists()
                assert Path(f).stat().st_size > 1000

            print(f"\n✓ Rendered colored box:")
            for f in files:
                print(f"  - {f}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_transparent_box(self, transparent_box, tmp_path):
        """Render transparent box"""
        output_path = tmp_path / "transparent_box"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                transparent_box,
                str(output_path),
                views=['isometric']
            )

            assert len(files) == 1
            assert Path(files[0]).exists()

            print(f"\n✓ Rendered transparent box to: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_multiple_views(self, cylinder, tmp_path):
        """Render part from multiple angles"""
        output_path = tmp_path / "cylinder"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                cylinder,
                str(output_path),
                views=['isometric', 'front', 'top', 'right']
            )

            # Verify all 4 views created
            assert len(files) == 4
            for f in files:
                assert Path(f).exists()

            print(f"\n✓ Rendered cylinder from 4 angles:")
            for f in files:
                print(f"  - {Path(f).name}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_with_color_override(self, simple_box, tmp_path):
        """Override part color in render"""
        output_path = tmp_path / "override_color"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                simple_box,
                str(output_path),
                views=['isometric'],
                color=(1.0, 0.5, 0.0, 1.0)  # Orange
            )

            assert len(files) == 1
            assert Path(files[0]).exists()

            print(f"\n✓ Rendered with color override to: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_with_edges(self, colored_box, tmp_path):
        """Render with mesh edges visible"""
        output_path = tmp_path / "with_edges"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                colored_box,
                str(output_path),
                views=['isometric'],
                show_edges=True
            )

            assert len(files) == 1
            assert Path(files[0]).exists()

            print(f"\n✓ Rendered with edges to: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise


class TestAssemblyRendering:
    """Test rendering multi-part assemblies"""

    @pytest.fixture
    def simple_assembly(self):
        """Create simple 3-part assembly"""
        registry = PartRegistry()

        # Base plate (gray)
        base_geom = cq.Workplane("XY").box(100, 100, 5)
        base = Part(
            name="base",
            geometry=base_geom,
            metadata={'color': (0.5, 0.5, 0.5, 1.0)}
        )
        registry.add(base)

        # Body (blue)
        body_geom = cq.Workplane("XY").box(60, 60, 30)
        body = Part(
            name="body",
            geometry=body_geom,
            metadata={'color': (0.0, 0.4, 0.8, 1.0)}
        )
        registry.add(body)

        # Top (red)
        top_geom = cq.Workplane("XY").cylinder(10, 5)
        top = Part(
            name="top",
            geometry=top_geom,
            metadata={'color': (1.0, 0.0, 0.0, 1.0)}
        )
        registry.add(top)

        return registry

    def test_render_assembly_isometric(self, simple_assembly, tmp_path):
        """Render assembly from isometric view"""
        output_path = tmp_path / "assembly"

        try:
            renderer = ModelRenderer()
            files = renderer.render_assembly(
                simple_assembly,
                str(output_path),
                views=['isometric']
            )

            assert len(files) == 1
            assert Path(files[0]).exists()
            assert Path(files[0]).stat().st_size > 5000  # Larger for assembly

            print(f"\n✓ Rendered 3-part assembly to: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_assembly_multiple_views(self, simple_assembly, tmp_path):
        """Render assembly from multiple angles"""
        output_path = tmp_path / "assembly_multi"

        try:
            renderer = ModelRenderer()
            files = renderer.render_assembly(
                simple_assembly,
                str(output_path),
                views=['isometric', 'front', 'top']
            )

            assert len(files) == 3
            for f in files:
                assert Path(f).exists()

            print(f"\n✓ Rendered assembly from 3 angles:")
            for f in files:
                print(f"  - {Path(f).name}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_render_part_function(self, tmp_path):
        """Test render_part convenience function"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(
            name="convenience_test",
            geometry=geometry,
            metadata={'color': (1.0, 0.0, 1.0, 1.0)}  # Magenta
        )

        output_path = tmp_path / "convenience"

        try:
            files = render_part(
                part,
                str(output_path),
                views=['isometric']
            )

            assert len(files) == 1
            assert Path(files[0]).exists()

            print(f"\n✓ Convenience render_part() worked: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise

    def test_render_assembly_function(self, tmp_path):
        """Test render_assembly convenience function"""
        registry = PartRegistry()

        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(
            name="test",
            geometry=geometry,
            metadata={'color': (0.0, 1.0, 1.0, 1.0)}  # Cyan
        )
        registry.add(part)

        output_path = tmp_path / "convenience_asm"

        try:
            files = render_assembly(
                registry,
                str(output_path),
                views=['isometric']
            )

            assert len(files) == 1
            assert Path(files[0]).exists()

            print(f"\n✓ Convenience render_assembly() worked: {files[0]}")

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_view_name(self, tmp_path):
        """Invalid view name should be skipped with warning"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="test", geometry=geometry)

        output_path = tmp_path / "invalid_view"

        try:
            renderer = ModelRenderer()
            files = renderer.render_part(
                part,
                str(output_path),
                views=['isometric', 'invalid_view_name', 'front']
            )

            # Should render valid views only
            assert len(files) == 2  # isometric and front

        except RenderError as e:
            if "pyvista" in str(e).lower():
                pytest.skip("PyVista not installed")
            else:
                raise
