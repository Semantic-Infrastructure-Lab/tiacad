"""
Integration tests for text primitive.

Tests text primitives in real-world scenarios using the full TiaCAD parser.

Author: TIA
Version: 0.1.0-alpha (Phase 2)
Date: 2025-10-31
"""

import pytest
import tempfile
import os

from tiacad_core.parser.tiacad_parser import TiaCADParser


class TestTextPrimitiveBasicIntegration:
    """Basic integration tests for text primitives"""

    def test_simple_text_primitive_parsing(self):
        """Text primitive can be parsed from YAML"""
        yaml_content = """
parts:
  my_text:
    primitive: text
    text: "HELLO"
    size: 10
    height: 3
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc is not None
        part = doc.get_part('my_text')
        assert part is not None
        assert part.geometry is not None
        assert part.metadata['primitive_type'] == 'text'

    def test_text_primitive_with_all_parameters(self):
        """Text primitive with all parameters parses correctly"""
        yaml_content = """
parts:
  full_text:
    primitive: text
    text: "COMPLETE"
    size: 15
    height: 4
    font: "Liberation Sans"
    style: bold
    halign: center
    valign: center
    spacing: 1.2
"""
        doc = TiaCADParser.parse_string(yaml_content)

        part = doc.get_part('full_text')
        assert part is not None
        assert part.geometry is not None

    def test_text_primitive_with_parameters(self):
        """Text primitive with parameter substitution"""
        yaml_content = """
parameters:
  label: "PRODUCT"
  size: 12

parts:
  param_text:
    primitive: text
    text: "${label}"
    size: ${size}
    height: 3
"""
        doc = TiaCADParser.parse_string(yaml_content)

        part = doc.get_part('param_text')
        assert part is not None
        assert part.geometry is not None

    def test_text_primitive_with_color(self):
        """Text primitive with color"""
        yaml_content = """
parts:
  colored_text:
    primitive: text
    text: "COLOR"
    size: 10
    height: 3
    color: red
"""
        doc = TiaCADParser.parse_string(yaml_content)

        part = doc.get_part('colored_text')
        assert part is not None
        assert 'color' in part.metadata

    def test_text_primitive_with_material(self):
        """Text primitive with material"""
        yaml_content = """
materials:
  gold:
    color: "#FFD700"
    metallic: 0.9

parts:
  gold_text:
    primitive: text
    text: "GOLD"
    size: 10
    height: 3
    material: gold
"""
        doc = TiaCADParser.parse_string(yaml_content)

        part = doc.get_part('gold_text')
        assert part is not None
        assert 'material' in part.metadata

    def test_multiple_text_primitives(self):
        """Multiple text primitives in same document"""
        yaml_content = """
parts:
  text1:
    primitive: text
    text: "FIRST"
    size: 10
    height: 3

  text2:
    primitive: text
    text: "SECOND"
    size: 12
    height: 4

  text3:
    primitive: text
    text: "THIRD"
    size: 8
    height: 2
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('text1') is not None
        assert doc.get_part('text2') is not None
        assert doc.get_part('text3') is not None


class TestTextPrimitiveSTLExport:
    """Test STL export of text primitives"""

    def test_text_primitive_stl_export(self):
        """Text primitive can be exported to STL"""
        yaml_content = """
parts:
  export_text:
    primitive: text
    text: "EXPORT"
    size: 15
    height: 4
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('export_text')

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            doc.export_stl(temp_path, 'export_text')

            assert os.path.exists(temp_path)
            # File should be reasonable size
            size = os.path.getsize(temp_path)
            assert size > 5000, f"STL file too small: {size} bytes"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_text_primitive_unicode_stl_export(self):
        """Text primitive with Unicode can export to STL"""
        yaml_content = """
parts:
  unicode_text:
    primitive: text
    text: "TEST ✓"
    size: 12
    height: 3
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # May fail if font doesn't support Unicode, but should not crash
            doc.export_stl(temp_path, 'unicode_text')
            if os.path.exists(temp_path):
                assert os.path.getsize(temp_path) > 1000
        except Exception as e:
            # Only acceptable failure is font rendering
            if 'font' not in str(e).lower():
                raise
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestTextPrimitiveFontStyles:
    """Test text primitives with different fonts and styles"""

    def test_text_different_styles(self):
        """Text primitives with different styles"""
        yaml_content = """
parts:
  regular_text:
    primitive: text
    text: "REGULAR"
    size: 10
    height: 3
    style: regular

  bold_text:
    primitive: text
    text: "BOLD"
    size: 10
    height: 3
    style: bold

  italic_text:
    primitive: text
    text: "ITALIC"
    size: 10
    height: 3
    style: italic
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('regular_text') is not None
        assert doc.get_part('bold_text') is not None
        assert doc.get_part('italic_text') is not None

    def test_text_different_fonts(self):
        """Text primitives with different fonts"""
        yaml_content = """
parts:
  sans_text:
    primitive: text
    text: "SANS"
    size: 10
    height: 3
    font: "Liberation Sans"

  mono_text:
    primitive: text
    text: "MONO"
    size: 10
    height: 3
    font: "Liberation Mono"
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('sans_text') is not None
        assert doc.get_part('mono_text') is not None

    def test_text_different_alignments(self):
        """Text primitives with different alignments"""
        yaml_content = """
parts:
  left_text:
    primitive: text
    text: "LEFT"
    size: 10
    height: 3
    halign: left

  center_text:
    primitive: text
    text: "CENTER"
    size: 10
    height: 3
    halign: center

  right_text:
    primitive: text
    text: "RIGHT"
    size: 10
    height: 3
    halign: right
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('left_text') is not None
        assert doc.get_part('center_text') is not None
        assert doc.get_part('right_text') is not None


class TestTextPrimitiveRealWorldScenarios:
    """Real-world scenarios for text primitives"""

    def test_product_label(self):
        """Product label with parametric text"""
        yaml_content = """
parameters:
  product: "WIDGET PRO"
  version: "v2.5"

parts:
  base:
    primitive: box
    size: [100, 40, 3]

  product_name:
    primitive: text
    text: "${product}"
    size: 12
    height: 2

  version_label:
    primitive: text
    text: "${version}"
    size: 8
    height: 2
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('base') is not None
        assert doc.get_part('product_name') is not None
        assert doc.get_part('version_label') is not None

    def test_serial_number_plate(self):
        """Serial number plate with monospace font"""
        yaml_content = """
parameters:
  serial: "SN-2025-12345"
  date: "2025-10-31"

parts:
  plate:
    primitive: box
    size: [60, 30, 2]

  serial_text:
    primitive: text
    text: "${serial}"
    size: 6
    height: 1
    font: "Liberation Mono"

  date_text:
    primitive: text
    text: "${date}"
    size: 4
    height: 1
    font: "Liberation Mono"
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('plate') is not None
        assert doc.get_part('serial_text') is not None
        assert doc.get_part('date_text') is not None
