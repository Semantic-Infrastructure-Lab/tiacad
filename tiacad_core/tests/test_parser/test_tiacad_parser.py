"""
Tests for TiaCADParser

Tests end-to-end parsing from YAML to TiaCADDocument.
"""

import pytest
import tempfile
import os
from pathlib import Path

from tiacad_core.parser.tiacad_parser import (
    TiaCADParser,
    TiaCADDocument,
    TiaCADParserError,
    parse
)


class TestBasicParsing:
    """Test basic parsing functionality"""

    def test_parse_simple_box(self):
        """Test parsing a simple box"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc is not None
        assert isinstance(doc, TiaCADDocument)
        assert doc.get_part('box') is not None

    def test_parse_with_parameters(self):
        """Test parsing with parameters"""
        yaml_content = """
parameters:
  width: 100
  height: 50

parts:
  box:
    primitive: box
    size: ['${width}', '${height}', 20]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.parameters['width'] == 100
        assert doc.parameters['height'] == 50
        assert doc.get_part('box') is not None

    def test_parse_with_metadata(self):
        """Test parsing with metadata"""
        yaml_content = """
metadata:
  name: Test Model
  version: "1.0"
  author: TIA

parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.metadata['name'] == 'Test Model'
        assert doc.metadata['version'] == '1.0'
        assert doc.metadata['author'] == 'TIA'


class TestWithOperations:
    """Test parsing with operations"""

    def test_parse_with_transform(self):
        """Test parsing with transform operation"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]

operations:
  box_moved:
    type: transform
    input: box
    transforms:
      - translate: [20, 0, 0]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('box') is not None
        assert doc.get_part('box_moved') is not None

    def test_parse_with_multiple_operations(self):
        """Test parsing with multiple operations"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]

operations:
  box1:
    type: transform
    input: box
    transforms:
      - translate: [20, 0, 0]

  box2:
    type: transform
    input: box
    transforms:
      - translate: [-20, 0, 0]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.get_part('box') is not None
        assert doc.get_part('box1') is not None
        assert doc.get_part('box2') is not None


class TestCompleteExample:
    """Test complete example with all features"""

    def test_parse_simplified_guitar_hanger(self):
        """Test parsing simplified guitar hanger"""
        yaml_content = """
metadata:
  name: Simple Guitar Hanger
  version: "1.0"

parameters:
  plate_w: 100
  plate_t: 12
  arm_spacing: 72
  arm_len: 70
  arm_tilt_deg: 10

parts:
  plate:
    primitive: box
    size: ['${plate_w}', '${plate_t}', 80]

  beam:
    primitive: box
    size: [32, 75, 24]

  arm:
    primitive: box
    size: [22, '${arm_len}', 16]

operations:
  left_arm:
    type: transform
    input: arm
    transforms:
      - translate:
          to: [0, 37.5, 0]
          offset: ['${-arm_spacing / 2}', '${arm_len / 2}', 0]
      - rotate:
          angle: '${arm_tilt_deg}'
          axis: X
          origin: [0, 37.5, 0]

  right_arm:
    type: transform
    input: arm
    transforms:
      - translate:
          to: [0, 37.5, 0]
          offset: ['${arm_spacing / 2}', '${arm_len / 2}', 0]
      - rotate:
          angle: '${arm_tilt_deg}'
          axis: X
          origin: [0, 37.5, 0]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Verify metadata
        assert doc.metadata['name'] == 'Simple Guitar Hanger'

        # Verify parameters resolved
        assert doc.parameters['plate_w'] == 100
        assert doc.parameters['arm_spacing'] == 72

        # Verify parts exist
        assert doc.get_part('plate') is not None
        assert doc.get_part('beam') is not None
        assert doc.get_part('arm') is not None
        assert doc.get_part('left_arm') is not None
        assert doc.get_part('right_arm') is not None

        # Verify arms are positioned differently
        left = doc.get_part('left_arm')
        right = doc.get_part('right_arm')
        assert left.current_position[0] < 0  # Left side
        assert right.current_position[0] > 0  # Right side


class TestFileOperations:
    """Test file-based parsing"""

    def test_parse_from_file(self):
        """Test parsing from actual file"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            doc = TiaCADParser.parse_file(temp_path)
            assert doc.get_part('box') is not None
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file"""
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_file("/nonexistent/file.yaml")

        assert 'not found' in str(exc_info.value).lower()


class TestExport:
    """Test export functionality"""

    def test_export_stl(self):
        """Test STL export"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            doc.export_stl(temp_path, 'box')
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_stl_default_part(self):
        """Test STL export with default part selection"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]

operations:
  box_moved:
    type: transform
    input: box
    transforms:
      - translate: [20, 0, 0]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # Export without specifying part - should export last operation
            doc.export_stl(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_step(self):
        """Test STEP export"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as f:
            temp_path = f.name

        try:
            doc.export_step(temp_path, 'box')
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestValidation:
    """Test validation functionality"""

    def test_validate_valid_file(self):
        """Test validating a valid file"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            is_valid, errors = TiaCADParser.validate_file(temp_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_yaml(self):
        """Test validating invalid YAML"""
        yaml_content = """
parts:
  box:
    primitive: invalid_primitive
    size: [10, 10, 10]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            is_valid, errors = TiaCADParser.validate_file(temp_path)
            assert not is_valid
            assert len(errors) > 0
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """Test error handling"""

    def test_missing_parts_section(self):
        """Test YAML without parts section"""
        yaml_content = """
metadata:
  name: Test
"""
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_string(yaml_content)

        assert 'parts' in str(exc_info.value).lower()

    def test_invalid_yaml_syntax(self):
        """Test invalid YAML syntax"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10
"""  # Missing closing bracket
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_string(yaml_content)

        assert 'yaml' in str(exc_info.value).lower()


class TestConvenienceFunction:
    """Test convenience parse() function"""

    def test_parse_convenience_function(self):
        """Test using parse() shortcut"""
        yaml_content = """
parts:
  box:
    primitive: box
    size: [10, 10, 10]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            doc = parse(temp_path)
            assert doc.get_part('box') is not None
        finally:
            os.unlink(temp_path)
