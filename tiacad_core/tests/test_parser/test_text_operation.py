"""
Unit tests for text operations (engrave/emboss).

Tests TextBuilder functionality including:
- Basic text operation creation (engrave and emboss)
- Parameter validation
- Face selection
- Font and style options
- Alignment options
- Error handling
"""

import pytest
import cadquery as cq
from tiacad_core.parser.text_builder import TextBuilder, TextBuilderError
from tiacad_core.part import Part, PartRegistry
from tiacad_core.parser.parameter_resolver import ParameterResolver


# Fixtures

@pytest.fixture
def empty_registry():
    """Empty part registry"""
    return PartRegistry()


@pytest.fixture
def param_resolver():
    """Parameter resolver with no parameters"""
    return ParameterResolver({})


@pytest.fixture
def text_builder(empty_registry, param_resolver):
    """TextBuilder instance"""
    return TextBuilder(empty_registry, param_resolver)


@pytest.fixture
def box_part():
    """Simple box part for testing"""
    geometry = cq.Workplane("XY").box(20, 20, 10)
    return Part(name="test_box", geometry=geometry, metadata={})


@pytest.fixture
def registry_with_box(empty_registry, box_part):
    """Registry containing a test box"""
    empty_registry.add(box_part)
    return empty_registry


# Basic Creation Tests

def test_text_operation_engrave_basic(registry_with_box, param_resolver):
    """Test basic text engraving operation"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1  # Negative = engrave
    }

    builder.execute_text_operation('engraved_text', spec)

    # Check result exists
    assert registry_with_box.exists('engraved_text')
    result = registry_with_box.get('engraved_text')

    # Check metadata
    assert result.metadata['operation_type'] == 'text'
    assert result.metadata['text_operation'] == 'engrave'
    assert result.metadata['source'] == 'test_box'
    assert result.metadata['text_content'] == 'HELLO'


def test_text_operation_emboss_basic(registry_with_box, param_resolver):
    """Test basic text embossing operation"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': 1  # Positive = emboss
    }

    builder.execute_text_operation('embossed_text', spec)

    # Check result exists
    assert registry_with_box.exists('embossed_text')
    result = registry_with_box.get('embossed_text')

    # Check metadata
    assert result.metadata['operation_type'] == 'text'
    assert result.metadata['text_operation'] == 'emboss'
    assert result.metadata['depth'] == 1


def test_text_operation_with_parameters(registry_with_box):
    """Test text operation with parameter substitution"""
    param_resolver_with_params = ParameterResolver({'serial': '12345'})

    builder = TextBuilder(registry_with_box, param_resolver_with_params)

    spec = {
        'input': 'test_box',
        'text': 'S/N: ${serial}',
        'face': '>Z',
        'position': [0, 0],
        'size': 4,
        'depth': -0.5
    }

    builder.execute_text_operation('serial_number', spec)

    result = registry_with_box.get('serial_number')
    assert result.metadata['text_content'] == 'S/N: 12345'


# Validation Tests - Missing Required Parameters

def test_text_operation_missing_input(text_builder):
    """Test error when input parameter is missing"""
    spec = {
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        text_builder.execute_text_operation('test', spec)

    assert "missing required 'input' field" in str(exc_info.value)


def test_text_operation_missing_text(registry_with_box, param_resolver):
    """Test error when text parameter is missing"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "missing required 'text' field" in str(exc_info.value)


def test_text_operation_missing_face(registry_with_box, param_resolver):
    """Test error when face parameter is missing"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "missing required 'face' field" in str(exc_info.value)


def test_text_operation_missing_position(registry_with_box, param_resolver):
    """Test error when position parameter is missing"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "missing required 'position' field" in str(exc_info.value)


def test_text_operation_missing_size(registry_with_box, param_resolver):
    """Test error when size parameter is missing"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "missing required 'size' field" in str(exc_info.value)


def test_text_operation_missing_depth(registry_with_box, param_resolver):
    """Test error when depth parameter is missing"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "missing required 'depth' field" in str(exc_info.value)


# Validation Tests - Invalid Parameters

def test_text_operation_input_not_found(empty_registry, param_resolver):
    """Test error when input part doesn't exist"""
    builder = TextBuilder(empty_registry, param_resolver)

    spec = {
        'input': 'nonexistent',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "input part 'nonexistent' not found" in str(exc_info.value)


def test_text_operation_text_not_string(registry_with_box, param_resolver):
    """Test error when text is not a string"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 12345,  # Not a string
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "text must be a string" in str(exc_info.value)


def test_text_operation_invalid_position(registry_with_box, param_resolver):
    """Test error when position is not [x, y]"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0, 0],  # 3D instead of 2D
        'size': 5,
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "position must be [x, y]" in str(exc_info.value)


def test_text_operation_invalid_size(registry_with_box, param_resolver):
    """Test error when size is not positive"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': -5,  # Negative size
        'depth': -1
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "size must be a positive number" in str(exc_info.value)


def test_text_operation_zero_depth(registry_with_box, param_resolver):
    """Test error when depth is zero"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': 0  # Zero depth
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "depth must be non-zero" in str(exc_info.value)


def test_text_operation_invalid_style(registry_with_box, param_resolver):
    """Test error when style is invalid"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'style': 'invalid_style'
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "invalid style" in str(exc_info.value)


def test_text_operation_invalid_halign(registry_with_box, param_resolver):
    """Test error when halign is invalid"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'halign': 'invalid'
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "invalid halign" in str(exc_info.value)


def test_text_operation_invalid_valign(registry_with_box, param_resolver):
    """Test error when valign is invalid"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HELLO',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'valign': 'invalid'
    }

    with pytest.raises(TextBuilderError) as exc_info:
        builder.execute_text_operation('test', spec)

    assert "invalid valign" in str(exc_info.value)


# Font and Style Tests

def test_text_operation_bold_style(registry_with_box, param_resolver):
    """Test text operation with bold style"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'BOLD',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'style': 'bold'
    }

    builder.execute_text_operation('bold_text', spec)
    assert registry_with_box.exists('bold_text')


def test_text_operation_italic_style(registry_with_box, param_resolver):
    """Test text operation with italic style"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'ITALIC',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'style': 'italic'
    }

    builder.execute_text_operation('italic_text', spec)
    assert registry_with_box.exists('italic_text')


def test_text_operation_bold_italic_style(registry_with_box, param_resolver):
    """Test text operation with bold-italic style"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'BOLD ITALIC',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'style': 'bold-italic'
    }

    builder.execute_text_operation('bold_italic_text', spec)
    assert registry_with_box.exists('bold_italic_text')


def test_text_operation_custom_font(registry_with_box, param_resolver):
    """Test text operation with custom font"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'CUSTOM',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'font': 'Liberation Mono'
    }

    builder.execute_text_operation('custom_font', spec)
    assert registry_with_box.exists('custom_font')


# Alignment Tests

def test_text_operation_center_align(registry_with_box, param_resolver):
    """Test text operation with center alignment"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'CENTERED',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1,
        'halign': 'center',
        'valign': 'center'
    }

    builder.execute_text_operation('centered_text', spec)
    assert registry_with_box.exists('centered_text')


def test_text_operation_right_align(registry_with_box, param_resolver):
    """Test text operation with right alignment"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'RIGHT',
        'face': '>Z',
        'position': [10, 0],
        'size': 5,
        'depth': -1,
        'halign': 'right'
    }

    builder.execute_text_operation('right_text', spec)
    assert registry_with_box.exists('right_text')


# Face Selection Tests

def test_text_operation_on_different_faces(registry_with_box, param_resolver):
    """Test text operations on different faces"""
    builder = TextBuilder(registry_with_box, param_resolver)

    # Top face
    spec_top = {
        'input': 'test_box',
        'text': 'TOP',
        'face': '>Z',
        'position': [0, 0],
        'size': 3,
        'depth': -0.5
    }
    builder.execute_text_operation('top_text', spec_top)

    # Front face
    spec_front = {
        'input': 'test_box',
        'text': 'FRONT',
        'face': '>Y',
        'position': [0, 0],
        'size': 3,
        'depth': -0.5
    }
    builder.execute_text_operation('front_text', spec_front)

    # Right face
    spec_right = {
        'input': 'test_box',
        'text': 'RIGHT',
        'face': '>X',
        'position': [0, 0],
        'size': 3,
        'depth': -0.5
    }
    builder.execute_text_operation('right_text', spec_right)

    assert registry_with_box.exists('top_text')
    assert registry_with_box.exists('front_text')
    assert registry_with_box.exists('right_text')


# Depth Variation Tests

def test_text_operation_shallow_engrave(registry_with_box, param_resolver):
    """Test shallow engraving (small negative depth)"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'SHALLOW',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -0.2
    }

    builder.execute_text_operation('shallow', spec)
    result = registry_with_box.get('shallow')
    assert result.metadata['depth'] == -0.2


def test_text_operation_deep_engrave(registry_with_box, param_resolver):
    """Test deep engraving (large negative depth)"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'DEEP',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -2.0
    }

    builder.execute_text_operation('deep', spec)
    result = registry_with_box.get('deep')
    assert result.metadata['depth'] == -2.0


def test_text_operation_high_emboss(registry_with_box, param_resolver):
    """Test high embossing (large positive depth)"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'HIGH',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': 3.0
    }

    builder.execute_text_operation('high', spec)
    result = registry_with_box.get('high')
    assert result.metadata['depth'] == 3.0


# Unicode and Special Characters Tests

def test_text_operation_unicode(registry_with_box, param_resolver):
    """Test text operation with Unicode characters"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': '→ℓ←',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
    }

    builder.execute_text_operation('unicode_text', spec)
    result = registry_with_box.get('unicode_text')
    assert result.metadata['text_content'] == '→ℓ←'


def test_text_operation_multiline(registry_with_box, param_resolver):
    """Test text operation with multiline text"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'LINE1\nLINE2',
        'face': '>Z',
        'position': [0, 0],
        'size': 3,
        'depth': -0.5
    }

    builder.execute_text_operation('multiline', spec)
    assert registry_with_box.exists('multiline')


# Default Values Tests

def test_text_operation_default_font(registry_with_box, param_resolver):
    """Test that default font is used when not specified"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'DEFAULT',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
        # No font specified, should use default
    }

    builder.execute_text_operation('default_font', spec)
    assert registry_with_box.exists('default_font')


def test_text_operation_default_style(registry_with_box, param_resolver):
    """Test that default style (regular) is used when not specified"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'DEFAULT',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
        # No style specified, should use regular
    }

    builder.execute_text_operation('default_style', spec)
    assert registry_with_box.exists('default_style')


def test_text_operation_default_alignment(registry_with_box, param_resolver):
    """Test that default alignment is used when not specified"""
    builder = TextBuilder(registry_with_box, param_resolver)

    spec = {
        'input': 'test_box',
        'text': 'DEFAULT',
        'face': '>Z',
        'position': [0, 0],
        'size': 5,
        'depth': -1
        # No alignment specified, should use defaults (left, baseline)
    }

    builder.execute_text_operation('default_align', spec)
    assert registry_with_box.exists('default_align')
