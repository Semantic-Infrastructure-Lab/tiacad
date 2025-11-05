"""
Integration tests for text operations.

Tests full YAML → Parser → STL pipeline with text operations.
"""

import pytest
import tempfile
import os
from pathlib import Path

from tiacad_core.parser.tiacad_parser import TiaCADParser


# Test Data

YAML_ENGRAVE_SIMPLE = """
schema_version: 2.0

parameters:
  box_size: 30

parts:
  base_box:
    primitive: box
    size:
      - ${box_size}
      - ${box_size}
      - 10
    color: silver

operations:
  serial_number:
    type: text
    input: base_box
    text: "S/N: 12345"
    face: ">Z"
    position: [0, 0]
    size: 4
    depth: -0.5
"""

YAML_EMBOSS_SIMPLE = """
schema_version: 2.0

parts:
  plate:
    primitive: box
    size: [40, 20, 3]

operations:
  label:
    type: text
    input: plate
    text: "PRODUCT"
    face: ">Z"
    position: [0, 0]
    size: 5
    depth: 1.0
"""

YAML_MULTIPLE_FACES = """
schema_version: 2.0

parts:
  cube:
    primitive: box
    size: [20, 20, 20]

operations:
  top_label:
    type: text
    input: cube
    text: "TOP"
    face: ">Z"
    position: [0, 0]
    size: 4
    depth: -0.5

  front_label:
    type: text
    input: top_label
    text: "FRONT"
    face: ">Y"
    position: [0, 0]
    size: 4
    depth: -0.5

  right_label:
    type: text
    input: front_label
    text: "RIGHT"
    face: ">X"
    position: [0, 0]
    size: 4
    depth: -0.5
"""

YAML_WITH_STYLES = """
schema_version: 2.0

parts:
  panel:
    primitive: box
    size: [50, 30, 5]

operations:
  title:
    type: text
    input: panel
    text: "WARNING"
    face: ">Z"
    position: [0, 8]
    size: 6
    depth: -0.8
    style: bold
    halign: center

  subtitle:
    type: text
    input: title
    text: "High Voltage"
    face: ">Z"
    position: [0, -5]
    size: 4
    depth: -0.6
    style: italic
    halign: center
"""

YAML_ENGRAVE_WITH_BOOLEAN = """
schema_version: 2.0

parts:
  main_body:
    primitive: box
    size: [30, 30, 10]

  hole:
    primitive: cylinder
    radius: 5
    height: 15

operations:
  body_with_hole:
    type: boolean
    operation: difference
    base: main_body
    subtract: [hole]

  engraved_label:
    type: text
    input: body_with_hole
    text: "MODEL X"
    face: ">Z"
    position: [10, 10]
    size: 3
    depth: -0.5
"""

YAML_PARAMETRIC_TEXT = """
schema_version: 2.0

parameters:
  product_name: "Widget Pro"
  version: "2.5"
  plate_width: 60

parts:
  name_plate:
    primitive: box
    size:
      - ${plate_width}
      - 20
      - 3

operations:
  product_label:
    type: text
    input: name_plate
    text: "${product_name} v${version}"
    face: ">Z"
    position: [0, 0]
    size: 5
    depth: 1.0
    halign: center
    valign: center
"""


# Integration Tests

def test_engrave_simple_integration():
    """Test simple engraving operation through full parser"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_ENGRAVE_SIMPLE)

    # Check result structure
    assert result.parts is not None
    assert len(result.parts) > 0

    # Should have base_box and serial_number (result of operation)
    part_names = result.parts.list_parts()
    assert 'base_box' in part_names
    assert 'serial_number' in part_names

    # Check serial_number metadata
    serial_part = result.parts.get('serial_number')
    assert serial_part.metadata['operation_type'] == 'text'
    assert serial_part.metadata['text_operation'] == 'engrave'


def test_emboss_simple_integration():
    """Test simple embossing operation through full parser"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_EMBOSS_SIMPLE)

    part_names = result.parts.list_parts()
    assert 'plate' in part_names
    assert 'label' in part_names

    # Check label metadata
    label_part = result.parts.get('label')
    assert label_part.metadata['operation_type'] == 'text'
    assert label_part.metadata['text_operation'] == 'emboss'


def test_multiple_faces_integration():
    """Test text on multiple faces through full parser"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_MULTIPLE_FACES)

    part_names = result.parts.list_parts()
    assert 'cube' in part_names
    assert 'top_label' in part_names
    assert 'front_label' in part_names
    assert 'right_label' in part_names

    # All text operations should be engrave
    for part_name in part_names:
        if 'label' in part_name:
            part = result.parts.get(part_name)
            assert part.metadata['operation_type'] == 'text'
            assert part.metadata['text_operation'] == 'engrave'


def test_styles_integration():
    """Test text with different styles through full parser"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_WITH_STYLES)

    part_names = result.parts.list_parts()
    assert 'panel' in part_names
    assert 'title' in part_names
    assert 'subtitle' in part_names

    # Check both text operations executed
    title = result.parts.get('title')
    subtitle = result.parts.get('subtitle')

    assert title.metadata['text_content'] == 'WARNING'
    assert subtitle.metadata['text_content'] == 'High Voltage'


def test_engrave_with_boolean_integration():
    """Test text operation combined with boolean operation"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_ENGRAVE_WITH_BOOLEAN)

    part_names = result.parts.list_parts()
    assert 'main_body' in part_names
    assert 'hole' in part_names
    assert 'body_with_hole' in part_names
    assert 'engraved_label' in part_names

    # Check final part has text
    label = result.parts.get('engraved_label')
    assert label.metadata['operation_type'] == 'text'


def test_parametric_text_integration():
    """Test text operation with parameter substitution"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_PARAMETRIC_TEXT)

    part_names = result.parts.list_parts()
    assert 'name_plate' in part_names
    assert 'product_label' in part_names

    # Check parameter substitution worked
    label = result.parts.get('product_label')
    assert label.metadata['text_content'] == 'Widget Pro v2.5'


def test_stl_export_engrave():
    """Test STL export of engraved text"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_ENGRAVE_SIMPLE)

    # Get the final part (serial_number)
    serial_part = result.parts.get('serial_number')

    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
        temp_path = f.name

    try:
        # Export STL
        serial_part.geometry.val().exportStl(temp_path)

        # Verify file exists and has content
        assert os.path.exists(temp_path)
        file_size = os.path.getsize(temp_path)
        assert file_size > 0, "STL file is empty"
        assert file_size > 500, f"STL file seems too small ({file_size} bytes)"

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stl_export_emboss():
    """Test STL export of embossed text"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_EMBOSS_SIMPLE)

    # Get the final part (label)
    label_part = result.parts.get('label')

    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
        temp_path = f.name

    try:
        # Export STL
        label_part.geometry.val().exportStl(temp_path)

        # Verify file exists and has content
        assert os.path.exists(temp_path)
        file_size = os.path.getsize(temp_path)
        assert file_size > 0, "STL file is empty"
        assert file_size > 500, f"STL file seems too small ({file_size} bytes)"

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stl_export_multiple_faces():
    """Test STL export with text on multiple faces"""
    parser = TiaCADParser()
    result = parser.parse_string(YAML_MULTIPLE_FACES)

    # Get the final part (right_label)
    final_part = result.parts.get('right_label')

    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
        temp_path = f.name

    try:
        # Export STL
        final_part.geometry.val().exportStl(temp_path)

        # Verify file exists and has content
        assert os.path.exists(temp_path)
        file_size = os.path.getsize(temp_path)
        assert file_size > 0, "STL file is empty"
        # Should be larger than single text operation (multiple faces)
        assert file_size > 500, f"STL file seems too small ({file_size} bytes)"

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Error Handling Tests

def test_invalid_face_selector_integration():
    """Test error handling for invalid face selector"""
    yaml_invalid = """
schema_version: 2.0

parts:
  box:
    primitive: box
    size: [20, 20, 10]

operations:
  bad_text:
    type: text
    input: box
    text: "FAIL"
    face: "INVALID"
    position: [0, 0]
    size: 5
    depth: -1
"""

    parser = TiaCADParser()
    with pytest.raises(Exception) as exc_info:
        parser.parse_string(yaml_invalid)

    # Should fail with selector error
    assert 'selector' in str(exc_info.value).lower() or 'face' in str(exc_info.value).lower()


def test_missing_input_part_integration():
    """Test error handling when input part doesn't exist"""
    yaml_missing = """
schema_version: 2.0

parts:
  box:
    primitive: box
    size: [20, 20, 10]

operations:
  bad_text:
    type: text
    input: nonexistent
    text: "FAIL"
    face: ">Z"
    position: [0, 0]
    size: 5
    depth: -1
"""

    parser = TiaCADParser()
    with pytest.raises(Exception) as exc_info:
        parser.parse_string(yaml_missing)

    assert 'nonexistent' in str(exc_info.value) or 'not found' in str(exc_info.value).lower()


# Real-World Scenario Tests

def test_product_label_scenario():
    """Test real-world product label scenario"""
    yaml_product = """
schema_version: 2.0

parameters:
  model: "PRO-X1000"
  serial: "SN2024-001"

parts:
  back_plate:
    primitive: box
    size: [80, 50, 3]
    color: black

operations:
  model_label:
    type: text
    input: back_plate
    text: "Model: ${model}"
    face: ">Z"
    position: [0, 15]
    size: 5
    depth: -0.6
    style: bold
    halign: center

  serial_label:
    type: text
    input: model_label
    text: "Serial: ${serial}"
    face: ">Z"
    position: [0, -15]
    size: 4
    depth: -0.5
    halign: center
"""

    parser = TiaCADParser()
    result = parser.parse_string(yaml_product)

    # Should have back_plate, model_label, and serial_label
    part_names = result.parts.list_parts()
    assert 'back_plate' in part_names
    assert 'model_label' in part_names
    assert 'serial_label' in part_names

    # Check parameter substitution
    serial_part = result.parts.get('serial_label')
    assert 'SN2024-001' in serial_part.metadata['text_content']


def test_warning_sign_scenario():
    """Test real-world warning sign scenario"""
    yaml_warning = """
schema_version: 2.0

parts:
  sign_base:
    primitive: box
    size: [100, 100, 5]
    color: yellow

  border:
    primitive: box
    size: [95, 95, 6]

operations:
  sign_with_border:
    type: boolean
    operation: difference
    base: sign_base
    subtract: [border]

  warning_text:
    type: text
    input: sign_with_border
    text: "CAUTION"
    face: ">Z"
    position: [0, 20]
    size: 12
    depth: 1.5
    style: bold
    halign: center

  detail_text:
    type: text
    input: warning_text
    text: "Electrical Hazard"
    face: ">Z"
    position: [0, -20]
    size: 6
    depth: 1.0
    halign: center
"""

    parser = TiaCADParser()
    result = parser.parse_string(yaml_warning)

    # Check all parts created
    part_names = result.parts.list_parts()
    assert 'sign_base' in part_names
    assert 'border' in part_names
    assert 'sign_with_border' in part_names
    assert 'warning_text' in part_names
    assert 'detail_text' in part_names

    # Final part should have both texts
    final_part = result.parts.get('detail_text')
    assert final_part.metadata['operation_type'] == 'text'
