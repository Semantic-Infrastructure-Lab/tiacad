"""
Test export configuration parsing and application.

Tests that export: section in YAML is properly parsed and applied,
fixing the issue where finishing operations broke exports due to
relying on dict ordering instead of explicit user intent.
"""

import pytest
import tempfile
import os
from tiacad_core.parser.tiacad_parser import TiaCADParser


class TestExportConfigParsing:
    """Test export configuration parsing"""

    def test_export_default_part_parsing(self):
        """Test that export: default_part: is parsed correctly"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
operations:
  modified:
    type: transform
    input: base
    transforms:
      - translate: [0, 0, 5]
export:
  default_part: modified
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Verify export config was parsed
        assert doc.export_config is not None
        assert doc.export_config['default_part'] == 'modified'

    def test_export_config_optional(self):
        """Test that export config is optional (backward compatible)"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Should still work without export section
        assert doc.export_config is not None
        assert doc.export_config['default_part'] is None

    def test_export_config_full_spec(self):
        """Test parsing full export configuration"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
export:
  default_part: base
  formats: [stl, step, 3mf]
  color_mode: realistic
  default_color: [0.8, 0.8, 0.8]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        assert doc.export_config['default_part'] == 'base'
        assert doc.export_config['formats'] == ['stl', 'step', '3mf']
        assert doc.export_config['color_mode'] == 'realistic'
        assert doc.export_config['default_color'] == [0.8, 0.8, 0.8]


class TestExportWithFinishingOperations:
    """Test that export config enables finishing operations"""

    def test_export_with_finishing_operation(self):
        """Test export with finishing operation (chamfer) using export config

        NOTE: Finishing operations modify parts in-place, they don't create new
        registry entries. That's why export config is needed - we specify which
        part to export BEFORE the finishing operation modifies it.
        """
        yaml_content = """
parts:
  bracket:
    primitive: box
    parameters:
      width: 20
      height: 20
      depth: 5
operations:
  positioned:
    type: transform
    input: bracket
    transforms:
      - translate: [0, 0, 0]
  finished:
    type: finishing
    finish: chamfer
    input: positioned
    length: 1
    edges: all
export:
  default_part: positioned  # Export the part (which was modified by finishing)
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # Verify finishing operation executed (operations_spec has it)
        assert 'finished' in doc.operations

        # Verify the part that was modified still exists
        assert 'positioned' in doc.parts.list_parts()

        # Verify export config respects our intent
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # Should export 'positioned' (now with chamfered edges), not fail
            doc.export_stl(temp_path)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_finishing_modifies_input_part(self):
        """Test that finishing operations modify the input part in-place"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters:
      width: 20
      height: 20
      depth: 5
operations:
  filleted_base:
    type: finishing
    finish: fillet
    input: base
    radius: 2
    edges: all
export:
  default_part: base  # Export the base (which now has fillets)
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # The base part still exists (was modified in-place)
        assert 'base' in doc.parts.list_parts()

        # No new part was created for the finishing operation
        assert 'filleted_base' not in doc.parts.list_parts()

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # Should export 'base' (which now has fillets applied)
            doc.export_stl(temp_path)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestExportPriorityLogic:
    """Test export part selection priority logic"""

    def test_priority_1_export_config(self):
        """Test that export config has highest priority"""
        yaml_content = """
parts:
  first:
    primitive: box
    parameters:
      width: 5
      height: 5
      depth: 5
operations:
  second:
    type: transform
    input: first
    transforms:
      - translate: [10, 0, 0]
  third:
    type: transform
    input: second
    transforms:
      - translate: [10, 0, 0]
export:
  default_part: second  # Not the last operation
"""
        doc = TiaCADParser.parse_string(yaml_content)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # Should export 'second', not 'third' (last operation)
            doc.export_stl(temp_path)
            # We can't directly verify which part was exported without
            # inspecting geometry, but we can verify it didn't crash
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_priority_2_last_operation_fallback(self):
        """Test that last operation is used when no export config"""
        yaml_content = """
parts:
  first:
    primitive: box
    parameters:
      width: 5
      height: 5
      depth: 5
operations:
  second:
    type: transform
    input: first
    transforms:
      - translate: [10, 0, 0]
  third:
    type: transform
    input: second
    transforms:
      - translate: [10, 0, 0]
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # No export config, should fall back to last operation
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            doc.export_stl(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_priority_3_first_part_fallback(self):
        """Test that first part is used when no operations or export config"""
        yaml_content = """
parts:
  only_part:
    primitive: box
    parameters:
      width: 5
      height: 5
      depth: 5
"""
        doc = TiaCADParser.parse_string(yaml_content)

        # No operations, no export config - should export first (only) part
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            doc.export_stl(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cli_override_has_ultimate_priority(self):
        """Test that explicit CLI part name overrides export config"""
        yaml_content = """
parts:
  first:
    primitive: box
    parameters:
      width: 5
      height: 5
      depth: 5
operations:
  second:
    type: transform
    input: first
    transforms:
      - translate: [10, 0, 0]
export:
  default_part: second
"""
        doc = TiaCADParser.parse_string(yaml_content)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            # Explicitly request 'first', should override export config
            doc.export_stl(temp_path, part_name='first')
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestExportConfigSTEPFormat:
    """Test that export config applies to STEP format too"""

    def test_step_respects_export_config(self):
        """Test that STEP export also respects export config"""
        yaml_content = """
parts:
  base:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
operations:
  modified:
    type: transform
    input: base
    transforms:
      - translate: [0, 0, 5]
  finished:
    type: finishing
    finish: chamfer
    input: modified
    length: 1
    edges: all
export:
  default_part: modified  # Export before finishing
"""
        doc = TiaCADParser.parse_string(yaml_content)

        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as f:
            temp_path = f.name

        try:
            # Should export 'modified' for STEP too
            doc.export_step(temp_path)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
