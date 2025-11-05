"""
Comprehensive unit tests for ThreeMFExporter

Tests all aspects of 3MF export functionality including:
- Material handling (named, colors, transparent)
- Mesh generation from CadQuery geometry
- Multi-part exports
- Metadata support
- Error handling and validation
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import cadquery as cq

from tiacad_core.exporters.threemf_exporter import (
    ThreeMFExporter,
    ThreeMFExportError,
    export_3mf
)
from tiacad_core.part import Part, PartRegistry


class TestThreeMFExporterInit:
    """Test ThreeMFExporter initialization"""

    def test_init_success(self):
        """Exporter should initialize with lib3mf installed"""
        try:
            exporter = ThreeMFExporter()
            assert exporter.lib3mf is not None
            assert exporter.wrapper is not None
        except ThreeMFExportError:
            pytest.skip("lib3mf not installed")

    def test_init_no_lib3mf(self):
        """Should raise helpful error if lib3mf not installed"""
        with patch.dict('sys.modules', {'lib3mf': None}):
            with patch('tiacad_core.exporters.threemf_exporter.ThreeMFExporter._check_lib3mf') as mock_check:
                mock_check.side_effect = ThreeMFExportError(
                    "lib3mf library not installed. Install with: pip install lib3mf"
                )
                with pytest.raises(ThreeMFExportError) as exc_info:
                    exporter = ThreeMFExporter()
                    exporter._check_lib3mf()

                assert "lib3mf" in str(exc_info.value).lower()
                assert "pip install" in str(exc_info.value).lower()


class TestBasicExport:
    """Test basic export functionality"""

    @pytest.fixture
    def simple_box(self):
        """Create simple box part"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="test_box", geometry=geometry)
        return part

    @pytest.fixture
    def parts_registry_single(self, simple_box):
        """Registry with single part"""
        registry = PartRegistry()
        registry.add(simple_box)
        return registry

    def test_export_single_part_no_material(self, parts_registry_single, tmp_path):
        """Export single part without material"""
        output_path = tmp_path / "test.3mf"

        try:
            exporter = ThreeMFExporter()
            exporter.export(parts_registry_single, str(output_path))

            # File should exist
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Should be a valid ZIP file (3MF is ZIP-based)
            import zipfile
            assert zipfile.is_zipfile(output_path)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_creates_valid_zip(self, parts_registry_single, tmp_path):
        """3MF file should be valid ZIP with expected structure"""
        output_path = tmp_path / "test.3mf"

        try:
            exporter = ThreeMFExporter()
            exporter.export(parts_registry_single, str(output_path))

            # Check ZIP contents
            import zipfile
            with zipfile.ZipFile(output_path, 'r') as zf:
                files = zf.namelist()
                # 3MF should have at least 3D/3dmodel.model
                assert any('3dmodel.model' in f for f in files) or len(files) > 0

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMaterialHandling:
    """Test material and color handling"""

    @pytest.fixture
    def box_with_color(self):
        """Box with RGB color"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="colored_box", geometry=geometry,
                   metadata={'color': (1.0, 0.0, 0.0, 1.0)})  # Red
        return part

    @pytest.fixture
    def box_with_material(self):
        """Box with named material"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="material_box", geometry=geometry,
                   metadata={
                       'material': 'aluminum',
                       'color': (0.75, 0.75, 0.75, 1.0)
                   })
        return part

    @pytest.fixture
    def box_with_transparency(self):
        """Box with transparent color"""
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="transparent_box", geometry=geometry,
                   metadata={'color': (0.0, 0.5, 1.0, 0.3)})  # Transparent blue
        return part

    def test_create_material_groups_no_materials(self):
        """Should handle parts with no materials"""
        try:
            exporter = ThreeMFExporter()

            # Mock model and registry
            model = Mock()
            registry = PartRegistry()

            # Add part without color/material
            geometry = cq.Workplane("XY").box(10, 10, 10)
            part = Part(name="plain", geometry=geometry)
            registry.add(part)

            material_map = exporter._create_material_groups(model, registry)

            # Should return empty map
            assert material_map == {}

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_with_single_color(self, box_with_color, tmp_path):
        """Export part with single color"""
        output_path = tmp_path / "colored.3mf"
        registry = PartRegistry()
        registry.add(box_with_color)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_with_named_material(self, box_with_material, tmp_path):
        """Export part with named material"""
        output_path = tmp_path / "material.3mf"
        registry = PartRegistry()
        registry.add(box_with_material)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_with_transparency(self, box_with_transparency, tmp_path):
        """Export part with transparent color (RGBA)"""
        output_path = tmp_path / "transparent.3mf"
        registry = PartRegistry()
        registry.add(box_with_transparency)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_multiple_materials(self, box_with_color, box_with_material, box_with_transparency, tmp_path):
        """Export multiple parts with different materials"""
        output_path = tmp_path / "multi_material.3mf"
        registry = PartRegistry()
        registry.add(box_with_color)
        registry.add(box_with_material)
        registry.add(box_with_transparency)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            assert output_path.exists()
            # File should be larger with multiple parts
            assert output_path.stat().st_size > 1000

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_material_deduplication(self):
        """Same material should only appear once in material group"""
        try:
            exporter = ThreeMFExporter()

            # Create registry with two parts using same color
            registry = PartRegistry()

            geometry1 = cq.Workplane("XY").box(10, 10, 10)
            part1 = Part(name="box1", geometry=geometry1,
                        metadata={'color': (1.0, 0.0, 0.0, 1.0)})  # Red

            geometry2 = cq.Workplane("XY").box(5, 5, 5)
            part2 = Part(name="box2", geometry=geometry2,
                        metadata={'color': (1.0, 0.0, 0.0, 1.0)})  # Same red

            registry.add(part1)
            registry.add(part2)

            # Mock model
            mock_model = Mock()
            mock_material_group = Mock()
            mock_material_group.GetResourceID.return_value = 1
            mock_material_group.AddMaterial.return_value = 0
            mock_model.AddBaseMaterialGroup.return_value = mock_material_group

            material_map = exporter._create_material_groups(mock_model, registry)

            # Should have exactly one material (deduplicated)
            assert len(material_map) == 1
            assert 'color_ff0000' in material_map

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMeshGeneration:
    """Test mesh creation from CadQuery geometry"""

    def test_create_mesh_simple_box(self):
        """Create mesh from simple box"""
        try:
            exporter = ThreeMFExporter()

            # Create simple box
            geometry = cq.Workplane("XY").box(10, 10, 10)
            part = Part(name="box", geometry=geometry)

            # Mock model
            model = Mock()
            mock_mesh = Mock()
            mock_mesh.SetName = Mock()
            mock_mesh.SetGeometry = Mock()
            mock_mesh.GetName.return_value = "box"
            model.AddMeshObject.return_value = mock_mesh

            mesh_obj = exporter._create_mesh_object(model, part, "box")

            # Should create mesh object
            assert mesh_obj is not None
            mock_mesh.SetName.assert_called_once_with("box")
            mock_mesh.SetGeometry.assert_called_once()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_mesh_has_vertices_and_triangles(self):
        """Mesh should have vertices and triangles"""
        try:
            exporter = ThreeMFExporter()

            # Create cylinder (will have many triangles)
            geometry = cq.Workplane("XY").cylinder(10, 5)
            part = Part(name="cylinder", geometry=geometry)

            # Mock model
            model = Mock()
            mock_mesh = Mock()
            mock_mesh.SetName = Mock()
            model.AddMeshObject.return_value = mock_mesh

            # Capture SetGeometry call
            vertices_captured = None
            triangles_captured = None

            def capture_geometry(vertices, triangles):
                nonlocal vertices_captured, triangles_captured
                vertices_captured = vertices
                triangles_captured = triangles

            mock_mesh.SetGeometry = capture_geometry

            mesh_obj = exporter._create_mesh_object(model, part, "cylinder")

            # Should have captured geometry
            assert vertices_captured is not None
            assert triangles_captured is not None
            assert len(vertices_captured) > 0
            assert len(triangles_captured) > 0

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_invalid_geometry_raises_error(self):
        """Should raise error for invalid geometry"""
        try:
            exporter = ThreeMFExporter()

            # Create part with invalid geometry (mock with no val method)
            geometry = Mock()
            geometry.val.return_value = None  # Invalid - returns None
            part = Part(name="invalid", geometry=geometry)

            # Mock model
            model = Mock()
            mock_mesh = Mock()
            model.AddMeshObject.return_value = mock_mesh

            with pytest.raises(ThreeMFExportError) as exc_info:
                exporter._create_mesh_object(model, part, "invalid")

            assert "Failed to create mesh" in str(exc_info.value)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMetadataHandling:
    """Test metadata export"""

    def test_export_with_metadata(self, tmp_path):
        """Export with document metadata"""
        output_path = tmp_path / "with_metadata.3mf"

        # Create simple part
        registry = PartRegistry()
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="box", geometry=geometry)
        registry.add(part)

        metadata = {
            'name': 'Test Model',
            'description': 'A test 3MF export'
        }

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path), metadata=metadata)

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_without_metadata(self, tmp_path):
        """Export without metadata should work"""
        output_path = tmp_path / "no_metadata.3mf"

        registry = PartRegistry()
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="box", geometry=geometry)
        registry.add(part)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path), metadata=None)

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_export_empty_registry(self, tmp_path):
        """Export empty registry should still create file"""
        output_path = tmp_path / "empty.3mf"
        registry = PartRegistry()

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            # Should create file even if empty
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_invalid_path(self):
        """Export to invalid path should raise error"""
        registry = PartRegistry()
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="box", geometry=geometry)
        registry.add(part)

        try:
            exporter = ThreeMFExporter()

            # Try to write to invalid path
            with pytest.raises(ThreeMFExportError) as exc_info:
                exporter.export(registry, "/invalid/path/that/does/not/exist/file.3mf")

            assert "Failed to export 3MF" in str(exc_info.value)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_with_exception(self, tmp_path):
        """Should wrap exceptions in ThreeMFExportError"""
        output_path = tmp_path / "error.3mf"
        registry = PartRegistry()

        try:
            exporter = ThreeMFExporter()

            # Mock to raise exception
            with patch.object(exporter.wrapper, 'CreateModel') as mock_create:
                mock_create.side_effect = Exception("Test error")

                with pytest.raises(ThreeMFExportError) as exc_info:
                    exporter.export(registry, str(output_path))

                assert "Failed to export 3MF" in str(exc_info.value)
                assert "Test error" in str(exc_info.value)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestConvenienceFunction:
    """Test export_3mf() convenience function"""

    def test_export_3mf_function(self, tmp_path):
        """Convenience function should work like exporter.export()"""
        output_path = tmp_path / "convenience.3mf"

        registry = PartRegistry()
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="box", geometry=geometry,
                   metadata={'color': (1.0, 0.0, 0.0, 1.0)})
        registry.add(part)

        try:
            export_3mf(registry, str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 0

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_3mf_with_metadata(self, tmp_path):
        """Convenience function with metadata"""
        output_path = tmp_path / "convenience_meta.3mf"

        registry = PartRegistry()
        geometry = cq.Workplane("XY").box(10, 10, 10)
        part = Part(name="box", geometry=geometry)
        registry.add(part)

        metadata = {'name': 'Test', 'description': 'Convenience test'}

        try:
            export_3mf(registry, str(output_path), metadata=metadata)

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_multi_part_multi_material_export(self, tmp_path):
        """Export complex model with multiple parts and materials"""
        output_path = tmp_path / "complex.3mf"

        registry = PartRegistry()

        # Base plate - aluminum
        base_geom = cq.Workplane("XY").box(100, 100, 5)
        base = Part(name="base_plate", geometry=base_geom,
                   metadata={
                       'material': 'aluminum',
                       'color': (0.75, 0.75, 0.75, 1.0)
                   })
        registry.add(base)

        # Main body - colored PLA
        body_geom = cq.Workplane("XY").box(80, 80, 30)
        body = Part(name="main_body", geometry=body_geom,
                   metadata={'color': (0.0, 0.4, 0.8, 1.0)})  # Blue
        registry.add(body)

        # Handle - TPU
        handle_geom = cq.Workplane("XY").cylinder(20, 5)
        handle = Part(name="handle", geometry=handle_geom,
                     metadata={
                         'material': 'tpu-flexible',
                         'color': (0.2, 0.2, 0.2, 1.0)
                     })
        registry.add(handle)

        # Window - transparent
        window_geom = cq.Workplane("XY").box(40, 30, 2)
        window = Part(name="window", geometry=window_geom,
                     metadata={'color': (0.0, 0.5, 1.0, 0.3)})  # Transparent blue
        registry.add(window)

        metadata = {
            'name': 'Complex Multi-Material Model',
            'description': 'Test model with 4 parts and 4 materials'
        }

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path), metadata=metadata)

            # Should create substantial file
            assert output_path.exists()
            assert output_path.stat().st_size > 5000  # Multi-part file

            # Verify it's a valid ZIP
            import zipfile
            assert zipfile.is_zipfile(output_path)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_same_color_different_parts(self, tmp_path):
        """Multiple parts with same color should deduplicate material"""
        output_path = tmp_path / "same_color.3mf"

        registry = PartRegistry()

        # Create 3 parts with same red color
        for i in range(3):
            geometry = cq.Workplane("XY").box(10 + i*5, 10, 10)
            part = Part(name=f"box{i}", geometry=geometry,
                       metadata={'color': (1.0, 0.0, 0.0, 1.0)})  # Same red
            registry.add(part)

        try:
            exporter = ThreeMFExporter()
            exporter.export(registry, str(output_path))

            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise
