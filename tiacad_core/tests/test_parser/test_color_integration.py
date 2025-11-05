"""
Integration tests for color parsing in TiaCAD YAML files
"""

import pytest
from tiacad_core.parser.tiacad_parser import TiaCADParser


class TestColorIntegration:
    """Test color parsing through complete YAML → Part pipeline"""

    def test_simple_color(self):
        """Test simple inline color"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: red
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        # Should have color in metadata
        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        assert r == 1.0
        assert g == 0.0
        assert b == 0.0
        assert a == 1.0

    def test_hex_color(self):
        """Test hex color"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: "#0066CC"
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        assert r < 0.1
        assert 0.35 < g < 0.45
        assert 0.75 < b < 0.85

    def test_palette_reference(self):
        """Test color palette reference"""
        yaml_content = """
schema_version: "2.0"
colors:
  brand-blue: "#0066CC"
  brand-red: red

parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: brand-blue

  box2:
    primitive: box
    size: [5, 5, 5]
    color: brand-red
"""
        doc = TiaCADParser.parse_string(yaml_content)

        box1 = doc.get_part('box1')
        assert 'color' in box1.metadata
        r, g, b, a = box1.metadata['color']
        assert b > 0.7  # Should be blue

        box2 = doc.get_part('box2')
        assert 'color' in box2.metadata
        r, g, b, a = box2.metadata['color']
        assert r == 1.0  # Should be red

    def test_material_library(self):
        """Test material library reference"""
        yaml_content = """
schema_version: "2.0"
parts:
  plate:
    primitive: box
    size: [100, 100, 5]
    material: aluminum

  bracket:
    primitive: box
    size: [20, 20, 10]
    material: steel
"""
        doc = TiaCADParser.parse_string(yaml_content)

        plate = doc.get_part('plate')
        assert 'material' in plate.metadata
        assert plate.metadata['material'] == 'aluminum'
        assert 'color' in plate.metadata
        assert 'material_properties' in plate.metadata
        assert 'metalness' in plate.metadata['material_properties']

        bracket = doc.get_part('bracket')
        assert bracket.metadata['material'] == 'steel'

    def test_rgb_array(self):
        """Test RGB array color"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: [0.5, 0.6, 0.7]
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        assert r == 0.5
        assert g == 0.6
        assert b == 0.7
        assert a == 1.0

    def test_rgba_array_transparency(self):
        """Test RGBA array with transparency"""
        yaml_content = """
schema_version: "2.0"
parts:
  window:
    primitive: box
    size: [10, 10, 2]
    color: [0.0, 0.0, 1.0, 0.3]
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('window')

        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        assert b == 1.0
        assert a == 0.3

    def test_hsl_color(self):
        """Test HSL color object"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color:
      h: 240
      s: 100
      l: 50
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        # Should be blue (h=240)
        assert r < 0.1
        assert g < 0.1
        assert b > 0.9

    def test_appearance_specification(self):
        """Test full appearance specification"""
        yaml_content = """
schema_version: "2.0"
parts:
  custom_part:
    primitive: box
    size: [10, 10, 10]
    appearance:
      color: [0.8, 0.2, 0.2]
      finish: glossy
      metalness: 0.9
      roughness: 0.1
      opacity: 0.8
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('custom_part')

        assert 'color' in part.metadata
        r, g, b, a = part.metadata['color']
        assert r == 0.8
        assert g == 0.2
        assert b == 0.2

        assert 'material_properties' in part.metadata
        props = part.metadata['material_properties']
        assert props['finish'] == 'glossy'
        assert props['metalness'] == 0.9
        assert props['roughness'] == 0.1
        assert props['opacity'] == 0.8

    def test_multiple_parts_different_colors(self):
        """Test multiple parts with different color formats"""
        yaml_content = """
schema_version: "2.0"
colors:
  accent: "#FF6600"

parts:
  part1:
    primitive: box
    size: [10, 10, 10]
    color: red

  part2:
    primitive: cylinder
    radius: 5
    height: 20
    color: "#0066CC"

  part3:
    primitive: sphere
    radius: 8
    color: accent

  part4:
    primitive: box
    size: [5, 5, 5]
    material: aluminum

  part5:
    primitive: cylinder
    radius: 3
    height: 10
    color: [0.5, 0.5, 0.5]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # All parts should parse successfully
        assert doc.get_part('part1') is not None
        assert doc.get_part('part2') is not None
        assert doc.get_part('part3') is not None
        assert doc.get_part('part4') is not None
        assert doc.get_part('part5') is not None

        # Check each has color
        assert 'color' in doc.get_part('part1').metadata
        assert 'color' in doc.get_part('part2').metadata
        assert 'color' in doc.get_part('part3').metadata
        assert 'color' in doc.get_part('part4').metadata
        assert 'color' in doc.get_part('part5').metadata

    def test_no_color_specified(self):
        """Test part without color (should work, no color in metadata)"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        # Should build successfully
        assert part is not None
        # Color is optional
        # (Could be None or have a default - both are acceptable)

    def test_invalid_color_warning(self):
        """Test that invalid colors don't break parsing (just warn)"""
        yaml_content = """
schema_version: "2.0"
parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: invalid-color-name-xyz
"""
        # Should not raise exception (non-fatal error)
        doc = TiaCADParser.parse_string(yaml_content)
        part = doc.get_part('box1')

        # Part should still be built
        assert part is not None

    def test_color_with_parameters(self):
        """Test color with parameter substitution"""
        yaml_content = """
schema_version: "2.0"
parameters:
  primary_color: "#0066CC"

colors:
  theme: ${primary_color}

parts:
  box1:
    primitive: box
    size: [10, 10, 10]
    color: ${primary_color}

  box2:
    primitive: box
    size: [5, 5, 5]
    color: theme
"""
        doc = TiaCADParser.parse_string(yaml_content)

        box1 = doc.get_part('box1')
        box2 = doc.get_part('box2')

        # Both should have the same color
        assert 'color' in box1.metadata
        assert 'color' in box2.metadata

        # Should be the same blue color
        assert box1.metadata['color'] == box2.metadata['color']


class TestColorExamples:
    """Test the actual examples from the color system spec"""

    def test_example_simple_colors(self):
        """Test Example 1 from spec: Simple Colors"""
        yaml_content = """
schema_version: "2.0"
parts:
  cover:
    primitive: box
    size: [100, 80, 2]
    color: red

  frame:
    primitive: box
    size: [100, 80, 10]
    color: "#0066CC"

  detail:
    primitive: cylinder
    radius: 5
    height: 15
    color: [0.9, 0.7, 0.1]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should parse all three parts
        assert len(doc.parts.list_parts()) == 3
        assert doc.get_part('cover') is not None
        assert doc.get_part('frame') is not None
        assert doc.get_part('detail') is not None

    def test_example_material_presets(self):
        """Test Example 2 from spec: Material Presets"""
        yaml_content = """
schema_version: "2.0"
parts:
  bracket:
    primitive: box
    size: [50, 30, 5]
    material: aluminum

  shaft:
    primitive: cylinder
    radius: 8
    height: 100
    material: steel

  knob:
    primitive: sphere
    radius: 15
    material: abs-black
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should parse all three parts
        assert len(doc.parts.list_parts()) == 3

        # Check materials
        assert doc.get_part('bracket').metadata['material'] == 'aluminum'
        assert doc.get_part('shaft').metadata['material'] == 'steel'
        assert doc.get_part('knob').metadata['material'] == 'abs-black'

    def test_example_design_system(self):
        """Test Example 3 from spec: Design System"""
        yaml_content = """
schema_version: "2.0"
colors:
  brand-blue: "#0066CC"
  brand-orange: "#CC6600"
  frame-color: aluminum

parts:
  main_cover:
    primitive: box
    size: [120, 100, 3]
    color: brand-blue

  accent_strip:
    primitive: box
    size: [120, 10, 3]
    color: brand-orange

  mounting_bracket:
    primitive: box
    size: [30, 30, 5]
    color: frame-color
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should parse all parts
        assert len(doc.parts.list_parts()) == 3

        # All should have colors
        assert 'color' in doc.get_part('main_cover').metadata
        assert 'color' in doc.get_part('accent_strip').metadata
        assert 'color' in doc.get_part('mounting_bracket').metadata
