"""
Tests for TiaCADParser

Tests end-to-end parsing from YAML to TiaCADDocument.
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from tiacad_core.parser.tiacad_parser import (
    TiaCADParser,
    TiaCADDocument,
    TiaCADParserError,
    parse,
    resolve_default_part_name,
)
from tiacad_core.geometry import MockBackend
from tiacad_core.part import Part, PartRegistry


class TestBasicParsing:
    """Test basic parsing functionality"""

    def test_parse_simple_box(self):
        """Test parsing a simple box"""
        yaml_content = """
parts:
  box:
    primitive: box
    parameters:

      width: 10

      height: 10

      depth: 10
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
    parameters:

      width: '${width}'

      height: '${height}'

      depth: 20
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
    parameters:

      width: 10

      height: 10

      depth: 10
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.metadata['name'] == 'Test Model'
        assert doc.metadata['version'] == '1.0'
        assert doc.metadata['author'] == 'TIA'

    def test_parse_dict_honors_explicit_backend(self):
        """Test parsing with an explicitly supplied backend."""
        backend = MockBackend()

        doc = TiaCADParser.parse_dict(
            {
                'parts': {
                    'box': {
                        'primitive': 'box',
                        'parameters': {'width': 10, 'height': 10, 'depth': 10}
                    }
                }
            },
            backend=backend,
        )

        assert doc.get_part('box').backend is backend

    def test_numeric_schema_version_does_not_warn(self, caplog):
        """Numeric 3.0 is accepted because the JSON schema accepts both forms."""
        caplog.set_level("WARNING")

        TiaCADParser.parse_dict({
            'schema_version': 3.0,
            'parts': {
                'box': {
                    'primitive': 'box',
                    'parameters': {'width': 10, 'height': 10, 'depth': 10}
                }
            }
        })

        assert "not explicitly supported" not in caplog.text


class TestExportBoundaries:
    """Test export behavior around backend boundaries."""

    def test_export_stl_rejects_non_cadquery_backend(self, tmp_path):
        backend = MockBackend()
        registry = PartRegistry()
        registry.add(Part("mock_box", backend.create_box(10, 10, 10), backend=backend))
        doc = TiaCADDocument(metadata={}, parameters={}, parts=registry)

        with pytest.raises(TiaCADParserError) as exc_info:
            doc.export_stl(str(tmp_path / "bad.stl"), "mock_box")

        assert "cadquery-compatible part" in str(exc_info.value).lower()

    def test_export_3mf_single_part_builds_temp_registry(self, tmp_path):
        doc = TiaCADParser.parse_dict({
            'parts': {
                'box': {
                    'primitive': 'box',
                    'parameters': {'width': 10, 'height': 10, 'depth': 10}
                }
            }
        })

        captured = {}

        def fake_export(parts_registry, output_path, metadata):
            captured['parts'] = parts_registry.list_parts()
            captured['part'] = parts_registry.get('box')
            captured['output_path'] = output_path
            captured['metadata'] = metadata

        with patch('tiacad_core.exporters.export_3mf', side_effect=fake_export):
            doc.export_3mf(str(tmp_path / "single.3mf"), part_name='box')

        assert captured['parts'] == ['box']
        assert captured['part'].name == 'box'
        assert captured['part'].backend is doc.parts.get('box').backend

    def test_resolve_default_part_name_prefers_export_config(self):
        doc = TiaCADParser.parse_dict({
            'parts': {
                'base': {
                    'primitive': 'box',
                    'parameters': {'width': 10, 'height': 10, 'depth': 10}
                }
            },
            'operations': {
                'final': {
                    'type': 'transform',
                    'input': 'base',
                    'transforms': [{'translate': [5, 0, 0]}]
                }
            },
            'export': {
                'default_part': 'base'
            }
        })

        assert resolve_default_part_name(doc.parts, doc.operations, doc.export_config) == 'base'


class TestWithOperations:
    """Test parsing with operations"""

    def test_parse_with_transform(self):
        """Test parsing with transform operation"""
        yaml_content = """
parts:
  box:
    primitive: box
    parameters:

      width: 10

      height: 10

      depth: 10

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
    parameters:

      width: 10

      height: 10

      depth: 10

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

    def test_parse_text_engraved_example(self):
        """Text engraving example should parse without backend-compatibility errors."""
        doc = TiaCADParser.parse_file('examples/text_engraved.yaml')

        assert doc.get_part('final_sign') is not None

    def test_parse_text_label_example(self):
        """Text label example should parse without backend-compatibility errors."""
        doc = TiaCADParser.parse_file('examples/text_label.yaml')

        assert doc.get_part('final_label') is not None

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
    parameters:

      width: '${plate_w}'

      height: '${plate_t}'

      depth: 80

  beam:
    primitive: box
    parameters:

      width: 32

      height: 75

      depth: 24

  arm:
    primitive: box
    parameters:

      width: 22

      height: '${arm_len}'

      depth: 16

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
    parameters:

      width: 10

      height: 10

      depth: 10
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
    parameters:

      width: 10

      height: 10

      depth: 10
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
    parameters:

      width: 10

      height: 10

      depth: 10

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
    parameters:

      width: 10

      height: 10

      depth: 10
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


class TestConstraintsIntegration:
    """End-to-end constraints: -> parse -> export coverage through the exact
    entrypoint `tiacad build` uses (TiaCADParser.parse_file/parse_string ->
    doc.export_*), as distinct from test_dag/test_watcher.py's coverage of the
    same constraints through the separate `tiacad watch` incremental-rebuild
    path (TCAD-VAL-11) — the two pipelines apply constraints via independent
    code (parse_pipeline._apply_constraints vs watcher._rebuild's own call),
    and previously only the watch path had an end-to-end test."""

    def test_flush_and_offset_constraints_solve_through_full_pipeline(self):
        """Two constraints (flush, offset) on a three-part model, parsed via
        the standard (non-watch) pipeline, must both be reflected in the
        parts' final positions — not just accepted without error."""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  top:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center
  mount:
    primitive: box
    parameters: {width: 3, height: 3, depth: 3}
    origin: center

constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]
  - type: offset
    faces: [top.face_top, mount.face_bottom]
    distance: 2
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # flush: top sits directly on base's top face (base half-height 5 + top half-height 2.5)
        assert doc.get_part("top").get_center() == pytest.approx((0.0, 0.0, 7.5), abs=1e-6)
        # offset: mount sits 2mm above top's top face (top center 7.5 + top half-height 2.5
        # + offset 2 + mount half-height 1.5)
        assert doc.get_part("mount").get_center() == pytest.approx((0.0, 0.0, 13.5), abs=1e-6)

    def test_constrained_model_exports_correct_geometry(self, tmp_path):
        """The constraint solve must actually be baked into the exported mesh,
        not just the in-memory Part position — export through parse_file (what
        `tiacad build` calls) and check the STL reflects the constrained bbox."""
        input_path = tmp_path / "constrained.tiacad"
        input_path.write_text("""
parts:
  base:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  top:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center

constraints:
  - type: flush
    faces: [base.face_top, top.face_bottom]
""")
        doc = TiaCADParser.parse_file(str(input_path))

        output_path = tmp_path / "constrained.stl"
        doc.export_stl(str(output_path), "top")

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        import trimesh
        mesh = trimesh.load(str(output_path))
        # top is a 5mm cube flush-mated onto base's top face -> Z spans [5, 10]
        assert mesh.bounds[0][2] == pytest.approx(5.0, abs=0.05)
        assert mesh.bounds[1][2] == pytest.approx(10.0, abs=0.05)


class TestValidation:
    """Test validation functionality"""

    def test_validate_valid_file(self):
        """Test validating a valid file"""
        yaml_content = """
parts:
  box:
    primitive: box
    parameters:

      width: 10

      height: 10

      depth: 10
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
    parameters:

      width: 10

      height: 10

      depth: 10
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
    parameters: {width: 10, height: 10, depth: 10
"""  # Missing closing brace - invalid YAML
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
    parameters: {width: 10, height: 10, depth: 10}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            doc = parse(temp_path)
            assert doc.get_part('box') is not None
        finally:
            os.unlink(temp_path)


class TestYAMLAliasSupport:
    """Test YAML field alias support (v3.2+)"""

    def test_anchors_alias_for_references(self):
        """Test using 'anchors:' as alias for 'references:' (v3.2+)"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 10, depth: 100}

  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 50}
    translate:
      to: base.face_top

anchors:
  custom_point:
    type: point
    value: [50, 50, 30]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should successfully parse with 'anchors:' section
        assert doc is not None
        assert doc.get_part('base') is not None
        assert doc.get_part('pillar') is not None

        # The 'anchors:' section should be normalized to 'references:'
        assert 'custom_point' in doc.references

    def test_anchors_and_references_conflict(self):
        """Test error when both 'anchors:' and 'references:' are present"""
        yaml_content = """
parts:
  box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}

anchors:
  point1:
    type: point
    value: [0, 0, 0]

references:
  point2:
    type: point
    value: [10, 10, 10]
"""
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_string(yaml_content)

        error_msg = str(exc_info.value).lower()
        assert 'anchors' in error_msg and 'references' in error_msg
        assert 'both' in error_msg

    def test_references_still_works(self):
        """Test that canonical 'references:' still works (backward compatible)"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 10, depth: 100}

references:
  mounting_point:
    type: point
    value: [50, 50, 10]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should work with canonical 'references:' section
        assert doc is not None
        assert 'mounting_point' in doc.references
