"""
Integration tests for gusset operation through full TIACAD pipeline

Tests the complete flow: YAML → Parser → Operations → Export

Author: TIA (sunny-rainbow-1102)
"""

import pytest
import tempfile
import os

from tiacad_core.parser.tiacad_parser import TiaCADParser, TiaCADParserError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Basic YAML Integration Tests
# ============================================================================

def test_gusset_simple_yaml_parse(temp_dir):
    """Test parsing YAML file with simple gusset operation."""
    yaml_content = """
metadata:
  name: Simple Gusset Test
  version: 1.0

parameters:
  thickness: 8

parts:
  base:
    primitive: box
    size: [50, 50, 10]

operations:
  support_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [30, 0, 0]
      - [15, 20, 0]
    thickness: ${thickness}

export:
  default_part: support_gusset
"""

    yaml_file = os.path.join(temp_dir, 'test_gusset.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Verify gusset was created (use .parts not .registry)
    assert result.parts.exists('support_gusset')
    gusset_part = result.parts.get('support_gusset')

    # Verify metadata
    assert gusset_part.metadata['operation_type'] == 'gusset'
    assert gusset_part.metadata['thickness'] == 8

    # Verify geometry is valid
    assert gusset_part.geometry.val().isValid()


def test_gusset_export_to_stl(temp_dir):
    """Test exporting gusset to STL file."""
    yaml_content = """
metadata:
  name: Gusset STL Export Test

parts:
  base:
    primitive: box
    size: [20, 20, 5]

operations:
  test_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [25, 0, 0]
      - [12.5, 18, 0]
    thickness: 6

export:
  default_part: test_gusset
"""

    yaml_file = os.path.join(temp_dir, 'gusset_export.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Export to STL (correct API: output_path, part_name)
    stl_file = os.path.join(temp_dir, 'test_gusset.stl')
    result.export_stl(stl_file, 'test_gusset')

    # Verify STL was created and has content
    assert os.path.exists(stl_file)
    assert os.path.getsize(stl_file) > 0


# ============================================================================
# Integration with Other Operations
# ============================================================================

def test_gusset_with_boolean_union(temp_dir):
    """Test gusset combined with boolean union operation."""
    yaml_content = """
metadata:
  name: Gusset + Boolean Test

parts:
  base_plate:
    primitive: box
    size: [60, 60, 8]
    origin: center

operations:
  corner_gusset:
    type: gusset
    points:
      - [20, 20, 0]
      - [30, 20, 0]
      - [25, 20, 15]
    thickness: 5

  reinforced_plate:
    type: boolean
    operation: union
    inputs:
      - base_plate
      - corner_gusset

export:
  default_part: reinforced_plate
"""

    yaml_file = os.path.join(temp_dir, 'gusset_boolean.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Verify union result exists and is valid
    assert result.parts.exists('reinforced_plate')
    union_part = result.parts.get('reinforced_plate')
    assert union_part.geometry.val().isValid()


def test_gusset_with_transform(temp_dir):
    """Test transforming a gusset (translate, rotate)."""
    yaml_content = """
metadata:
  name: Gusset Transform Test

parts:
  dummy:
    primitive: box
    size: [10, 10, 10]

operations:
  base_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [20, 0, 0]
      - [10, 15, 0]
    thickness: 4

  moved_gusset:
    type: transform
    input: base_gusset
    transforms:
      - translate: [50, 0, 0]
      - rotate:
          angle: 45
          axis: Z
          origin: [50, 0, 0]

export:
  default_part: moved_gusset
"""

    yaml_file = os.path.join(temp_dir, 'gusset_transform.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    assert result.parts.exists('moved_gusset')
    transformed = result.parts.get('moved_gusset')
    assert transformed.geometry.val().isValid()


def test_gusset_with_pattern(temp_dir):
    """Test creating pattern of gussets."""
    yaml_content = """
metadata:
  name: Gusset Pattern Test

parts:
  dummy:
    primitive: box
    size: [5, 5, 5]

operations:
  single_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [15, 0, 0]
      - [7.5, 12, 0]
    thickness: 3

  gusset_array:
    type: pattern
    pattern: linear
    input: single_gusset
    count: 4
    spacing: [30, 0, 0]

export:
  default_part: gusset_array
"""

    yaml_file = os.path.join(temp_dir, 'gusset_pattern.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Pattern operation creates individual parts (e.g., gusset_array_0, gusset_array_1, ...)
    # Check that at least one pattern result exists
    all_parts = result.parts.list_parts()
    pattern_parts = [p for p in all_parts if 'gusset_array' in p]
    assert len(pattern_parts) > 0


# ============================================================================
# Multiple Gussets
# ============================================================================

def test_multiple_gussets_in_assembly(temp_dir):
    """Test creating multiple gussets in one YAML file."""
    yaml_content = """
metadata:
  name: Multi-Gusset Assembly

parameters:
  gusset_thick: 6

parts:
  structure:
    primitive: box
    size: [100, 100, 10]

operations:
  gusset_1:
    type: gusset
    points:
      - [0, 0, 0]
      - [20, 0, 0]
      - [10, 0, 25]
    thickness: ${gusset_thick}

  gusset_2:
    type: gusset
    points:
      - [80, 0, 0]
      - [100, 0, 0]
      - [90, 0, 25]
    thickness: ${gusset_thick}

  full_assembly:
    type: boolean
    operation: union
    inputs:
      - structure
      - gusset_1
      - gusset_2

export:
  default_part: full_assembly
"""

    yaml_file = os.path.join(temp_dir, 'multi_gusset.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Verify all gussets exist
    for name in ['gusset_1', 'gusset_2']:
        assert result.parts.exists(name)
        gusset = result.parts.get(name)
        assert gusset.metadata['thickness'] == 6

    # Verify assembly
    assert result.parts.exists('full_assembly')


# ============================================================================
# Real-World Scenarios
# ============================================================================

def test_guitar_hanger_gussets_simple(temp_dir):
    """Integration test: Simplified guitar hanger with gusset supports."""
    # Using literal values to avoid YAML flow sequence issues
    yaml_content = """
metadata:
  name: Guitar Hanger with Gussets

parts:
  plate:
    primitive: box
    size: [100, 10, 90]
    origin: center

  beam:
    primitive: box
    size: [75, 10, 10]
    origin: center

  arm:
    primitive: box
    size: [30, 70, 10]
    origin: center

operations:
  left_arm:
    type: transform
    input: arm
    transforms:
      - translate: [-36, 72.5, 0]

  right_arm:
    type: transform
    input: arm
    transforms:
      - translate: [36, 72.5, 0]

  left_gusset:
    type: gusset
    points:
      - [-36, 20, 0]
      - [-36, 40, 0]
      - [-36, 30, 20]
    thickness: 8

  right_gusset:
    type: gusset
    points:
      - [36, 20, 0]
      - [36, 40, 0]
      - [36, 30, 20]
    thickness: 8

export:
  default_part: beam
"""

    yaml_file = os.path.join(temp_dir, 'guitar_hanger.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Verify all parts exist
    for part_name in ['plate', 'beam', 'left_arm', 'right_arm', 'left_gusset', 'right_gusset']:
        assert result.parts.exists(part_name)
        part = result.parts.get(part_name)
        assert part.geometry.val().isValid()

    # Verify gussets have correct metadata
    for gusset_name in ['left_gusset', 'right_gusset']:
        gusset = result.parts.get(gusset_name)
        assert gusset.metadata['operation_type'] == 'gusset'
        assert gusset.metadata['thickness'] == 8


def test_l_bracket_with_gusset(temp_dir):
    """Integration test: L-bracket with corner gusset."""
    yaml_content = """
metadata:
  name: L-Bracket with Gusset

parts:
  base_plate:
    primitive: box
    size: [80, 80, 6]
    origin: corner

  vertical_plate:
    primitive: box
    size: [80, 6, 60]
    origin: corner

operations:
  positioned_vertical:
    type: transform
    input: vertical_plate
    transforms:
      - translate: [0, 0, 6]

  corner_gusset:
    type: gusset
    points:
      - [0, 0, 6]
      - [40, 0, 6]
      - [0, 0, 46]
    thickness: 6

  l_bracket:
    type: boolean
    operation: union
    inputs:
      - base_plate
      - positioned_vertical
      - corner_gusset

export:
  default_part: l_bracket
"""

    yaml_file = os.path.join(temp_dir, 'l_bracket.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    assert result.parts.exists('l_bracket')
    bracket = result.parts.get('l_bracket')
    assert bracket.geometry.val().isValid()

    assert result.parts.exists('corner_gusset')
    gusset = result.parts.get('corner_gusset')
    assert gusset.metadata['thickness'] == 6


# ============================================================================
# Error Handling Integration
# ============================================================================

def test_gusset_yaml_error_missing_thickness(temp_dir):
    """Test that YAML parsing catches gusset errors properly."""
    yaml_content = """
metadata:
  name: Invalid Gusset Test

parts:
  dummy:
    primitive: box
    size: [10, 10, 10]

operations:
  bad_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [20, 0, 0]
      - [10, 15, 0]
    # Missing thickness!
"""

    yaml_file = os.path.join(temp_dir, 'bad_gusset.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()

    # Should raise error about missing thickness
    with pytest.raises(Exception) as exc_info:
        parser.parse_file(yaml_file)

    assert 'thickness' in str(exc_info.value).lower()


# ============================================================================
# Export Tests
# ============================================================================

def test_gusset_export_stl_file_size(temp_dir):
    """Test that gusset STL export produces reasonable file size."""
    yaml_content = """
metadata:
  name: STL Size Test

parts:
  dummy:
    primitive: box
    size: [10, 10, 10]

operations:
  test_gusset:
    type: gusset
    points:
      - [0, 0, 0]
      - [30, 0, 0]
      - [15, 25, 0]
    thickness: 8

export:
  default_part: test_gusset
"""

    yaml_file = os.path.join(temp_dir, 'stl_test.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    stl_file = os.path.join(temp_dir, 'gusset_test.stl')
    result.export_stl(stl_file, 'test_gusset')

    # STL should be > 100 bytes (has geometry)
    # and < 100KB (reasonable for simple gusset)
    file_size = os.path.getsize(stl_file)
    assert 100 < file_size < 100000


def test_gusset_export_multiple_parts(temp_dir):
    """Test exporting multiple gussets as separate STL files."""
    yaml_content = """
metadata:
  name: Multi-Part Export

parts:
  dummy:
    primitive: box
    size: [5, 5, 5]

operations:
  gusset_a:
    type: gusset
    points:
      - [0, 0, 0]
      - [20, 0, 0]
      - [10, 15, 0]
    thickness: 5

  gusset_b:
    type: gusset
    points:
      - [30, 0, 0]
      - [50, 0, 0]
      - [40, 15, 0]
    thickness: 5

export:
  default_part: gusset_a
"""

    yaml_file = os.path.join(temp_dir, 'multi_export.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()
    result = parser.parse_file(yaml_file)

    # Export both
    stl_a = os.path.join(temp_dir, 'gusset_a.stl')
    stl_b = os.path.join(temp_dir, 'gusset_b.stl')

    result.export_stl(stl_a, 'gusset_a')
    result.export_stl(stl_b, 'gusset_b')

    assert os.path.exists(stl_a)
    assert os.path.exists(stl_b)
    assert os.path.getsize(stl_a) > 0
    assert os.path.getsize(stl_b) > 0


# ============================================================================
# Performance Tests
# ============================================================================

def test_gusset_parse_performance(temp_dir):
    """Test that YAML with gussets parses in reasonable time."""
    import time

    yaml_content = """
metadata:
  name: Performance Test

parts:
  dummy:
    primitive: box
    size: [5, 5, 5]

operations:
  gusset_1:
    type: gusset
    points:
      - [0, 0, 0]
      - [25, 0, 0]
      - [12.5, 20, 0]
    thickness: 6

  gusset_2:
    type: gusset
    points:
      - [30, 0, 0]
      - [55, 0, 0]
      - [42.5, 20, 0]
    thickness: 6

  gusset_3:
    type: gusset
    points:
      - [60, 0, 0]
      - [85, 0, 0]
      - [72.5, 20, 0]
    thickness: 6
"""

    yaml_file = os.path.join(temp_dir, 'perf_test.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)

    parser = TiaCADParser()

    start = time.time()
    result = parser.parse_file(yaml_file)
    elapsed = time.time() - start

    # Should parse in under 2 seconds
    assert elapsed < 2.0

    # Verify all gussets created
    assert result.parts.exists('gusset_1')
    assert result.parts.exists('gusset_2')
    assert result.parts.exists('gusset_3')
