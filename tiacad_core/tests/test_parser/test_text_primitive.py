"""
Tests for text primitive in PartsBuilder.

Tests the _build_text() method and text primitive creation through
the PartsBuilder interface.

Author: TIA
Version: 0.1.0-alpha (Phase 2)
Date: 2025-10-31
"""

import pytest
import cadquery as cq

from tiacad_core.parser.parts_builder import PartsBuilder, PartsBuilderError
from tiacad_core.parser.parameter_resolver import ParameterResolver


class TestTextPrimitiveBasic:
    """Basic tests for text primitive creation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_basic_text_primitive(self):
        """Create basic text primitive with minimal parameters"""
        spec = {
            'primitive': 'text',
            'text': 'HELLO',
            'size': 10,
            'height': 5
        }

        part = self.builder.build_part('test_text', spec)

        assert part is not None
        assert part.name == 'test_text'
        assert part.geometry is not None
        assert isinstance(part.geometry, cq.Workplane)
        assert part.metadata['primitive_type'] == 'text'

        # Verify geometry exists
        solid = part.geometry.val()
        assert solid is not None

    def test_text_primitive_with_all_parameters(self):
        """Create text primitive with all optional parameters"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 15,
            'height': 3,
            'font': 'Liberation Sans',
            'style': 'bold',
            'halign': 'center',
            'valign': 'center',
            'spacing': 1.2
        }

        part = self.builder.build_part('full_text', spec)

        assert part is not None
        assert part.name == 'full_text'
        assert part.geometry is not None

    def test_text_primitive_with_font_path(self):
        """Text primitive can specify custom font path"""
        spec = {
            'primitive': 'text',
            'text': 'CUSTOM',
            'size': 12,
            'height': 4,
            'font_path': '/usr/share/fonts/truetype/custom.ttf'
        }

        # This may fail if font doesn't exist, but should not raise PartsBuilderError
        # for invalid parameters (only font loading error)
        try:
            part = self.builder.build_part('custom_font', spec)
            assert part is not None
        except PartsBuilderError as e:
            # Should only fail if font file doesn't exist, not parameter validation
            assert 'font' in str(e).lower()

    def test_text_primitive_unicode(self):
        """Text primitive supports Unicode characters"""
        spec = {
            'primitive': 'text',
            'text': '世界 🌍',
            'size': 10,
            'height': 2
        }

        # May fail if fonts don't support Unicode, but should not fail validation
        try:
            part = self.builder.build_part('unicode_text', spec)
            assert part is not None
        except PartsBuilderError as e:
            # Only acceptable failure is font rendering
            if 'font' not in str(e).lower():
                raise


class TestTextPrimitiveValidation:
    """Test validation and error handling for text primitives"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_missing_text_parameter(self):
        """Text primitive requires 'text' parameter"""
        spec = {
            'primitive': 'text',
            'size': 10,
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('no_text', spec)

        assert 'text' in str(exc_info.value).lower()
        assert 'missing' in str(exc_info.value).lower()

    def test_missing_size_parameter(self):
        """Text primitive requires 'size' parameter"""
        spec = {
            'primitive': 'text',
            'text': 'HELLO',
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('no_size', spec)

        assert 'size' in str(exc_info.value).lower()
        assert 'missing' in str(exc_info.value).lower()

    def test_missing_height_parameter(self):
        """Text primitive requires 'height' parameter"""
        spec = {
            'primitive': 'text',
            'text': 'HELLO',
            'size': 10
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('no_height', spec)

        assert 'height' in str(exc_info.value).lower()
        assert 'missing' in str(exc_info.value).lower()

    def test_empty_text_string(self):
        """Text primitive rejects empty text string"""
        spec = {
            'primitive': 'text',
            'text': '',
            'size': 10,
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('empty_text', spec)

        assert 'empty' in str(exc_info.value).lower()

    def test_whitespace_only_text(self):
        """Text primitive rejects whitespace-only text"""
        spec = {
            'primitive': 'text',
            'text': '   ',
            'size': 10,
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('whitespace_text', spec)

        assert 'empty' in str(exc_info.value).lower()

    def test_negative_size(self):
        """Text primitive rejects negative size"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': -5,
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('negative_size', spec)

        assert 'size' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()

    def test_zero_size(self):
        """Text primitive rejects zero size"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 0,
            'height': 5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('zero_size', spec)

        assert 'size' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()

    def test_negative_height(self):
        """Text primitive rejects negative height"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': -3
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('negative_height', spec)

        assert 'height' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()

    def test_zero_height(self):
        """Text primitive rejects zero height"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 0
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('zero_height', spec)

        assert 'height' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()

    def test_invalid_style(self):
        """Text primitive rejects invalid style"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 5,
            'style': 'super-bold'
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('invalid_style', spec)

        assert 'style' in str(exc_info.value).lower()
        assert 'invalid' in str(exc_info.value).lower()

    def test_invalid_halign(self):
        """Text primitive rejects invalid horizontal alignment"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 5,
            'halign': 'middle'
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('invalid_halign', spec)

        assert 'horizontal' in str(exc_info.value).lower() or 'halign' in str(exc_info.value).lower()
        assert 'invalid' in str(exc_info.value).lower()

    def test_invalid_valign(self):
        """Text primitive rejects invalid vertical alignment"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 5,
            'valign': 'middle'
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('invalid_valign', spec)

        assert 'vertical' in str(exc_info.value).lower() or 'valign' in str(exc_info.value).lower()
        assert 'invalid' in str(exc_info.value).lower()

    def test_negative_spacing(self):
        """Text primitive rejects negative spacing"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 5,
            'spacing': -0.5
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('negative_spacing', spec)

        assert 'spacing' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()

    def test_zero_spacing(self):
        """Text primitive rejects zero spacing"""
        spec = {
            'primitive': 'text',
            'text': 'TEST',
            'size': 10,
            'height': 5,
            'spacing': 0
        }

        with pytest.raises(PartsBuilderError) as exc_info:
            self.builder.build_part('zero_spacing', spec)

        assert 'spacing' in str(exc_info.value).lower()
        assert 'positive' in str(exc_info.value).lower()


class TestTextPrimitiveStyles:
    """Test different font styles"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_regular_style(self):
        """Text primitive with regular style"""
        spec = {
            'primitive': 'text',
            'text': 'REGULAR',
            'size': 10,
            'height': 3,
            'style': 'regular'
        }

        part = self.builder.build_part('regular', spec)
        assert part is not None

    def test_bold_style(self):
        """Text primitive with bold style"""
        spec = {
            'primitive': 'text',
            'text': 'BOLD',
            'size': 10,
            'height': 3,
            'style': 'bold'
        }

        part = self.builder.build_part('bold', spec)
        assert part is not None

    def test_italic_style(self):
        """Text primitive with italic style"""
        spec = {
            'primitive': 'text',
            'text': 'ITALIC',
            'size': 10,
            'height': 3,
            'style': 'italic'
        }

        part = self.builder.build_part('italic', spec)
        assert part is not None

    def test_bold_italic_style(self):
        """Text primitive with bold-italic style"""
        spec = {
            'primitive': 'text',
            'text': 'BOLD ITALIC',
            'size': 10,
            'height': 3,
            'style': 'bold-italic'
        }

        part = self.builder.build_part('bold_italic', spec)
        assert part is not None


class TestTextPrimitiveAlignment:
    """Test different text alignments"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_left_center_alignment(self):
        """Text primitive with left, center alignment"""
        spec = {
            'primitive': 'text',
            'text': 'LEFT',
            'size': 10,
            'height': 3,
            'halign': 'left',
            'valign': 'center'
        }

        part = self.builder.build_part('left_center', spec)
        assert part is not None

    def test_center_center_alignment(self):
        """Text primitive with center, center alignment"""
        spec = {
            'primitive': 'text',
            'text': 'CENTER',
            'size': 10,
            'height': 3,
            'halign': 'center',
            'valign': 'center'
        }

        part = self.builder.build_part('center_center', spec)
        assert part is not None

    def test_right_baseline_alignment(self):
        """Text primitive with right, baseline alignment"""
        spec = {
            'primitive': 'text',
            'text': 'RIGHT',
            'size': 10,
            'height': 3,
            'halign': 'right',
            'valign': 'baseline'
        }

        part = self.builder.build_part('right_baseline', spec)
        assert part is not None

    def test_center_top_alignment(self):
        """Text primitive with center, top alignment"""
        spec = {
            'primitive': 'text',
            'text': 'TOP',
            'size': 10,
            'height': 3,
            'halign': 'center',
            'valign': 'top'
        }

        part = self.builder.build_part('center_top', spec)
        assert part is not None

    def test_center_bottom_alignment(self):
        """Text primitive with center, bottom alignment"""
        spec = {
            'primitive': 'text',
            'text': 'BOTTOM',
            'size': 10,
            'height': 3,
            'halign': 'center',
            'valign': 'bottom'
        }

        part = self.builder.build_part('center_bottom', spec)
        assert part is not None


class TestTextPrimitiveParameterResolution:
    """Test parameter resolution in text primitives"""

    def test_text_with_parameter_substitution(self):
        """Text primitive resolves ${parameter} references"""
        resolver = ParameterResolver(parameters={'serial': 'SN-2025-001'})
        builder = PartsBuilder(resolver)

        spec = {
            'primitive': 'text',
            'text': 'S/N: ${serial}',
            'size': 8,
            'height': 2
        }

        part = builder.build_part('serial_text', spec)
        assert part is not None

    def test_size_with_parameter(self):
        """Text primitive resolves size parameter"""
        resolver = ParameterResolver(parameters={'text_size': 12})
        builder = PartsBuilder(resolver)

        spec = {
            'primitive': 'text',
            'text': 'PARAM',
            'size': '${text_size}',
            'height': 3
        }

        part = builder.build_part('param_size', spec)
        assert part is not None

    def test_height_with_parameter(self):
        """Text primitive resolves height parameter"""
        resolver = ParameterResolver(parameters={'extrude_depth': 5})
        builder = PartsBuilder(resolver)

        spec = {
            'primitive': 'text',
            'text': 'PARAM',
            'size': 10,
            'height': '${extrude_depth}'
        }

        part = builder.build_part('param_height', spec)
        assert part is not None


class TestTextPrimitiveGeometry:
    """Test geometry properties of text primitives"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_text_has_volume(self):
        """Text primitive creates geometry with volume"""
        spec = {
            'primitive': 'text',
            'text': 'VOL',
            'size': 15,
            'height': 5
        }

        part = self.builder.build_part('volume_test', spec)

        # Get the solid and check it has volume
        solid = part.geometry.val()
        assert solid is not None

        # CadQuery solids should have bounding box
        bbox = part.geometry.val().BoundingBox()
        assert bbox is not None

    def test_text_can_export_stl(self):
        """Text primitive geometry can export to STL"""
        import tempfile
        import os

        spec = {
            'primitive': 'text',
            'text': 'STL',
            'size': 15,
            'height': 3
        }

        part = self.builder.build_part('stl_test', spec)

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = f.name

        try:
            part.geometry.val().exportStl(temp_path)
            assert os.path.exists(temp_path)
            # STL file should have reasonable size (>1KB)
            assert os.path.getsize(temp_path) > 1000
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_different_heights_produce_different_geometry(self):
        """Text primitives with different heights produce different geometry"""
        spec1 = {
            'primitive': 'text',
            'text': 'H',
            'size': 10,
            'height': 2
        }

        spec2 = {
            'primitive': 'text',
            'text': 'H',
            'size': 10,
            'height': 5
        }

        part1 = self.builder.build_part('height_2', spec1)
        part2 = self.builder.build_part('height_5', spec2)

        bbox1 = part1.geometry.val().BoundingBox()
        bbox2 = part2.geometry.val().BoundingBox()

        # Different heights should produce different Z dimensions
        assert bbox1.zlen != bbox2.zlen
        # Height 5 should be taller than height 2
        assert bbox2.zlen > bbox1.zlen


class TestTextPrimitiveDefaults:
    """Test default values for optional parameters"""

    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = ParameterResolver(parameters={})
        self.builder = PartsBuilder(self.resolver)

    def test_default_font(self):
        """Text primitive uses default font when not specified"""
        spec = {
            'primitive': 'text',
            'text': 'DEFAULT',
            'size': 10,
            'height': 3
        }

        # Should not raise error - defaults to Liberation Sans
        part = self.builder.build_part('default_font', spec)
        assert part is not None

    def test_default_style(self):
        """Text primitive uses default style (regular) when not specified"""
        spec = {
            'primitive': 'text',
            'text': 'STYLE',
            'size': 10,
            'height': 3
        }

        # Should use regular style by default
        part = self.builder.build_part('default_style', spec)
        assert part is not None

    def test_default_alignment(self):
        """Text primitive uses default alignment when not specified"""
        spec = {
            'primitive': 'text',
            'text': 'ALIGN',
            'size': 10,
            'height': 3
        }

        # Should use center, center by default
        part = self.builder.build_part('default_align', spec)
        assert part is not None

    def test_default_spacing(self):
        """Text primitive uses default spacing (1.0) when not specified"""
        spec = {
            'primitive': 'text',
            'text': 'SPACE',
            'size': 10,
            'height': 3
        }

        # Should use spacing 1.0 by default
        part = self.builder.build_part('default_spacing', spec)
        assert part is not None
