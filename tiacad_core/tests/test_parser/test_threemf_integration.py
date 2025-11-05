"""
Integration tests for 3MF export from TiaCAD YAML files

Tests the complete workflow:
1. Parse YAML file with TiaCADParser
2. Export to 3MF format
3. Validate output file structure
4. Verify material assignments
"""

import pytest
import tempfile
from pathlib import Path
import zipfile

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.exporters.threemf_exporter import ThreeMFExportError


class TestBasicYAMLTo3MF:
    """Test basic YAML to 3MF export workflow"""

    @pytest.fixture
    def simple_yaml(self, tmp_path):
        """Create simple YAML file"""
        yaml_path = tmp_path / "simple.yaml"
        yaml_content = """
schema_version: "2.0"

parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_simple_export(self, simple_yaml, tmp_path):
        """Parse YAML and export to 3MF"""
        output_path = tmp_path / "simple.3mf"

        try:
            # Parse YAML
            doc = TiaCADParser.parse_file(str(simple_yaml))

            # Export to 3MF
            doc.export_3mf(str(output_path))

            # Verify output
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Should be valid ZIP
            assert zipfile.is_zipfile(output_path)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_returns_path(self, simple_yaml, tmp_path):
        """export_3mf should return without error"""
        output_path = tmp_path / "output.3mf"

        try:
            doc = TiaCADParser.parse_file(str(simple_yaml))
            result = doc.export_3mf(str(output_path))

            # Should complete without error (returns None)
            assert result is None
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestColoredPartsExport:
    """Test exporting parts with colors"""

    @pytest.fixture
    def colored_yaml(self, tmp_path):
        """YAML with colored parts"""
        yaml_path = tmp_path / "colored.yaml"
        yaml_content = """
schema_version: "2.0"

colors:
  brand-blue: "#0066CC"
  bright-red: "#FF0000"

parts:
  red_box:
    primitive: box
    size: [10, 10, 10]
    color: bright-red

  blue_cylinder:
    primitive: cylinder
    radius: 5
    height: 20
    color: brand-blue

  green_sphere:
    primitive: sphere
    radius: 8
    color: [0.0, 1.0, 0.0]  # RGB green
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_export_colored_parts(self, colored_yaml, tmp_path):
        """Export parts with different colors"""
        output_path = tmp_path / "colored.3mf"

        try:
            doc = TiaCADParser.parse_file(str(colored_yaml))
            doc.export_3mf(str(output_path))

            # Should create file
            assert output_path.exists()

            # File should be substantial (3 parts with colors)
            assert output_path.stat().st_size > 1000

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_palette_colors_exported(self, colored_yaml, tmp_path):
        """Palette color references should be exported"""
        output_path = tmp_path / "palette.3mf"

        try:
            doc = TiaCADParser.parse_file(str(colored_yaml))

            # Verify palette colors are in parts metadata
            red_box = doc.parts.get("red_box")
            assert 'color' in red_box.metadata
            # Should be RGB tuple (1.0, 0.0, 0.0, 1.0)
            r, g, b, a = red_box.metadata['color']
            assert r == 1.0
            assert g == 0.0
            assert b == 0.0

            # Export
            doc.export_3mf(str(output_path))
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMaterialLibraryExport:
    """Test exporting parts with materials from library"""

    @pytest.fixture
    def material_yaml(self, tmp_path):
        """YAML with material library usage"""
        yaml_path = tmp_path / "materials.yaml"
        yaml_content = """
schema_version: "2.0"

parts:
  aluminum_base:
    primitive: box
    size: [100, 100, 5]
    material: aluminum

  plastic_body:
    primitive: box
    size: [80, 80, 30]
    material: pla-white

  rubber_handle:
    primitive: cylinder
    radius: 8
    height: 60
    material: tpu-flexible
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_export_material_parts(self, material_yaml, tmp_path):
        """Export parts with named materials"""
        output_path = tmp_path / "materials.3mf"

        try:
            doc = TiaCADParser.parse_file(str(material_yaml))
            doc.export_3mf(str(output_path))

            # Should create file with 3 materials
            assert output_path.exists()
            assert output_path.stat().st_size > 2000

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_materials_in_metadata(self, material_yaml, tmp_path):
        """Material names should be in part metadata"""
        try:
            doc = TiaCADParser.parse_file(str(material_yaml))

            # Check aluminum part
            aluminum = doc.parts.get("aluminum_base")
            assert 'material' in aluminum.metadata
            assert aluminum.metadata['material'] == 'aluminum'
            assert 'color' in aluminum.metadata  # Should have color from material

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestTransparentPartsExport:
    """Test exporting transparent parts (RGBA)"""

    @pytest.fixture
    def transparent_yaml(self, tmp_path):
        """YAML with transparent parts"""
        yaml_path = tmp_path / "transparent.yaml"
        yaml_content = """
schema_version: "2.0"

parts:
  window:
    primitive: box
    size: [40, 30, 2]
    color: [0.0, 0.5, 1.0, 0.3]  # Transparent blue

  opaque_frame:
    primitive: box
    size: [50, 40, 3]
    color: [0.2, 0.2, 0.2, 1.0]  # Opaque gray
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_export_transparent_parts(self, transparent_yaml, tmp_path):
        """Export parts with alpha channel"""
        output_path = tmp_path / "transparent.3mf"

        try:
            doc = TiaCADParser.parse_file(str(transparent_yaml))

            # Verify alpha in metadata
            window = doc.parts.get("window")
            r, g, b, a = window.metadata['color']
            assert a == 0.3  # Transparent

            # Export
            doc.export_3mf(str(output_path))
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMultiMaterialExport:
    """Test complex multi-material exports"""

    @pytest.fixture
    def multi_material_yaml(self, tmp_path):
        """Complex YAML with mixed materials and colors"""
        yaml_path = tmp_path / "multi_material.yaml"
        yaml_content = """
schema_version: "2.0"

colors:
  brand-blue: "#0066CC"

parts:
  base_plate:
    primitive: box
    size: [120, 100, 5]
    material: aluminum

  main_body:
    primitive: box
    size: [100, 80, 30]
    color: brand-blue

  handle:
    primitive: cylinder
    radius: 8
    height: 60
    material: tpu-flexible

  window:
    primitive: box
    size: [40, 30, 2]
    color: [0.0, 0.5, 1.0, 0.3]

  label:
    primitive: box
    size: [20, 10, 1]
    color: "#FFFF00"  # Yellow hex

  button:
    primitive: sphere
    radius: 3
    color: [1.0, 0.0, 0.0]  # Red RGB

  port:
    primitive: cylinder
    radius: 2
    height: 10
    material: pla-black
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_export_complex_multi_material(self, multi_material_yaml, tmp_path):
        """Export complex model with 7 parts and multiple material types"""
        output_path = tmp_path / "complex.3mf"

        try:
            doc = TiaCADParser.parse_file(str(multi_material_yaml))

            # Verify we have 7 parts
            assert len(doc.parts.list_parts()) == 7

            # Export
            doc.export_3mf(str(output_path))

            # Should create substantial file
            assert output_path.exists()
            assert output_path.stat().st_size > 5000

            # Verify ZIP structure
            with zipfile.ZipFile(output_path, 'r') as zf:
                files = zf.namelist()
                assert len(files) > 0

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_all_color_formats_supported(self, multi_material_yaml, tmp_path):
        """All color format types should export correctly"""
        try:
            doc = TiaCADParser.parse_file(str(multi_material_yaml))

            # Verify different color formats are parsed
            # Palette reference
            body = doc.parts.get("main_body")
            assert 'color' in body.metadata

            # Hex color
            label = doc.parts.get("label")
            r, g, b, a = label.metadata['color']
            assert r == 1.0 and g == 1.0 and b == 0.0  # Yellow

            # RGB array
            button = doc.parts.get("button")
            r, g, b, a = button.metadata['color']
            assert r == 1.0 and g == 0.0 and b == 0.0  # Red

            # RGBA with transparency
            window = doc.parts.get("window")
            r, g, b, a = window.metadata['color']
            assert a == 0.3  # Transparent

            # Export all
            doc.export_3mf(str(tmp_path / "all_formats.3mf"))

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestMetadataExport:
    """Test document metadata in 3MF export"""

    @pytest.fixture
    def yaml_with_metadata(self, tmp_path):
        """YAML with metadata"""
        yaml_path = tmp_path / "with_meta.yaml"
        yaml_content = """
schema_version: "2.0"

metadata:
  name: "Test Assembly"
  description: "Integration test for 3MF export"
  version: "1.0"

parts:
  part1:
    primitive: box
    size: [10, 10, 10]
"""
        yaml_path.write_text(yaml_content)
        return yaml_path

    def test_export_with_document_metadata(self, yaml_with_metadata, tmp_path):
        """Document metadata should be included in export"""
        output_path = tmp_path / "metadata.3mf"

        try:
            doc = TiaCADParser.parse_file(str(yaml_with_metadata))

            # Verify metadata parsed
            assert hasattr(doc, 'metadata')
            assert 'name' in doc.metadata
            assert doc.metadata['name'] == "Test Assembly"

            # Export
            doc.export_3mf(str(output_path))
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestExistingDemoFiles:
    """Test with actual demo files from prior session"""

    def test_color_demo_export(self, tmp_path):
        """Export color_demo.yaml if it exists"""
        demo_path = Path("/home/scottsen/src/tia/projects/tiacad/examples/color_demo.yaml")

        if not demo_path.exists():
            pytest.skip("color_demo.yaml not found")

        output_path = tmp_path / "color_demo.3mf"

        try:
            doc = TiaCADParser.parse_file(str(demo_path))
            doc.export_3mf(str(output_path))

            # Should create file
            assert output_path.exists()

            # Should be substantial (7 parts)
            assert output_path.stat().st_size > 10000

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_multi_material_demo_export(self, tmp_path):
        """Export multi_material_demo.yaml if it exists"""
        demo_path = Path("/home/scottsen/src/tia/projects/tiacad/examples/multi_material_demo.yaml")

        if not demo_path.exists():
            pytest.skip("multi_material_demo.yaml not found")

        output_path = tmp_path / "multi_material_demo.3mf"

        try:
            doc = TiaCADParser.parse_file(str(demo_path))
            doc.export_3mf(str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 10000

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_export_no_parts(self, tmp_path):
        """Export YAML with no parts should raise error"""
        from tiacad_core.parser.tiacad_parser import TiaCADParserError

        yaml_path = tmp_path / "empty.yaml"
        yaml_content = """
schema_version: "2.0"
parts: {}
"""
        yaml_path.write_text(yaml_content)

        # Parser should reject empty parts
        with pytest.raises(TiaCADParserError) as exc_info:
            doc = TiaCADParser.parse_file(str(yaml_path))

        assert "parts" in str(exc_info.value).lower()

    def test_export_parts_no_colors(self, tmp_path):
        """Export parts without any colors or materials"""
        yaml_path = tmp_path / "plain.yaml"
        yaml_content = """
schema_version: "2.0"

parts:
  box1:
    primitive: box
    size: [10, 10, 10]

  cylinder1:
    primitive: cylinder
    radius: 5
    height: 20
"""
        yaml_path.write_text(yaml_content)
        output_path = tmp_path / "plain.3mf"

        try:
            doc = TiaCADParser.parse_file(str(yaml_path))
            doc.export_3mf(str(output_path))

            # Should use default colors
            assert output_path.exists()

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_export_to_existing_file(self, tmp_path):
        """Exporting should overwrite existing file"""
        yaml_path = tmp_path / "test.yaml"
        yaml_content = """
schema_version: "2.0"
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        yaml_path.write_text(yaml_content)
        output_path = tmp_path / "overwrite.3mf"

        try:
            doc = TiaCADParser.parse_file(str(yaml_path))

            # Export first time
            doc.export_3mf(str(output_path))
            first_size = output_path.stat().st_size

            # Export second time (should overwrite)
            doc.export_3mf(str(output_path))
            second_size = output_path.stat().st_size

            # Should be same size (or very similar)
            assert abs(first_size - second_size) < 100

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise


class Test3MFValidation:
    """Validate 3MF file structure and contents"""

    def test_3mf_is_valid_zip(self, tmp_path):
        """3MF file should be valid ZIP archive"""
        yaml_path = tmp_path / "test.yaml"
        yaml_content = """
schema_version: "2.0"
parts:
  box:
    primitive: box
    size: [10, 10, 10]
    color: "#FF0000"
"""
        yaml_path.write_text(yaml_content)
        output_path = tmp_path / "valid.3mf"

        try:
            doc = TiaCADParser.parse_file(str(yaml_path))
            doc.export_3mf(str(output_path))

            # Should be valid ZIP
            assert zipfile.is_zipfile(output_path)

            # Should be able to open and list files
            with zipfile.ZipFile(output_path, 'r') as zf:
                files = zf.namelist()
                assert len(files) > 0

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise

    def test_3mf_file_extension(self, tmp_path):
        """Should accept .3mf extension"""
        yaml_path = tmp_path / "test.yaml"
        yaml_content = """
schema_version: "2.0"
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        yaml_path.write_text(yaml_content)

        # Test with .3mf extension
        output_3mf = tmp_path / "test.3mf"

        try:
            doc = TiaCADParser.parse_file(str(yaml_path))
            doc.export_3mf(str(output_3mf))

            assert output_3mf.exists()
            assert zipfile.is_zipfile(output_3mf)

        except ThreeMFExportError as e:
            if "lib3mf" in str(e).lower():
                pytest.skip("lib3mf not installed")
            else:
                raise
