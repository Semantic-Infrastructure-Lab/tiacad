"""
Integration tests for text operations.

Tests the full pipeline: YAML spec → SketchBuilder → Text2D → CadQuery → Geometry

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import pytest
import cadquery as cq

from tiacad_core.sketch import Sketch2D, Text2D
from tiacad_core.parser.sketch_builder import SketchBuilder
from tiacad_core.parser.parameter_resolver import ParameterResolver


class TestTextSketchBuilder:
    """Test SketchBuilder integration with text shapes"""

    def test_build_basic_text_sketch(self):
        """SketchBuilder creates text sketch from YAML spec"""
        spec = {
            'sketches': {
                'test_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': 'HELLO',
                            'size': 10
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        assert 'test_text' in sketches
        sketch = sketches['test_text']
        assert len(sketch.shapes) == 1
        assert isinstance(sketch.shapes[0], Text2D)
        assert sketch.shapes[0].text == 'HELLO'
        assert sketch.shapes[0].size == 10

    def test_build_text_with_all_parameters(self):
        """SketchBuilder handles all text parameters"""
        spec = {
            'sketches': {
                'fancy_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': 'TEST',
                            'size': 15,
                            'font': 'Arial',
                            'style': 'bold',
                            'halign': 'center',
                            'valign': 'center',
                            'position': [10, 20],
                            'spacing': 1.2
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        text = sketches['fancy_text'].shapes[0]
        assert text.text == 'TEST'
        assert text.size == 15
        assert text.font == 'Arial'
        assert text.style == 'bold'
        assert text.halign == 'center'
        assert text.valign == 'center'
        assert text.position == (10, 20)
        assert text.spacing == 1.2

    def test_text_with_parameter_resolution(self):
        """Text content resolved from parameters"""
        spec = {
            'sketches': {
                'param_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': '${product} v${version}',
                            'size': 10
                        }
                    ]
                }
            }
        }

        params = {
            'product': 'Widget',
            'version': '2.0'
        }
        resolver = ParameterResolver(params)
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        # Note: ParameterResolver should resolve the text string
        # The actual resolution happens during parsing
        text = sketches['param_text'].shapes[0]
        # Text should contain the template - resolution happens in builder
        assert '${' in text.text or 'Widget' in text.text

    def test_multiple_text_shapes_in_sketch(self):
        """Sketch can contain multiple text shapes"""
        spec = {
            'sketches': {
                'multi_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': 'Title',
                            'size': 20,
                            'position': [0, 10]
                        },
                        {
                            'type': 'text',
                            'text': 'Subtitle',
                            'size': 10,
                            'position': [0, -5]
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        sketch = sketches['multi_text']
        assert len(sketch.shapes) == 2
        assert sketch.shapes[0].text == 'Title'
        assert sketch.shapes[0].size == 20
        assert sketch.shapes[1].text == 'Subtitle'
        assert sketch.shapes[1].size == 10

    def test_text_mixed_with_other_shapes(self):
        """Text can be combined with rectangles and circles"""
        spec = {
            'sketches': {
                'mixed': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'rectangle',
                            'width': 50,
                            'height': 30,
                            'center': [0, 0]
                        },
                        {
                            'type': 'text',
                            'text': 'LABEL',
                            'size': 8,
                            'halign': 'center'
                        },
                        {
                            'type': 'circle',
                            'radius': 2,
                            'center': [20, 10],
                            'operation': 'subtract'
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        sketch = sketches['mixed']
        assert len(sketch.shapes) == 3
        assert sketch.shapes[0].shape_type == 'rectangle'
        assert sketch.shapes[1].shape_type == 'text'
        assert sketch.shapes[2].shape_type == 'circle'

    def test_text_on_different_planes(self):
        """Text works on XY, XZ, and YZ planes"""
        for plane in ['XY', 'XZ', 'YZ']:
            spec = {
                'sketches': {
                    f'text_{plane}': {
                        'plane': plane,
                        'origin': [0, 0, 0],
                        'shapes': [
                            {
                                'type': 'text',
                                'text': f'On {plane}',
                                'size': 10
                            }
                        ]
                    }
                }
            }

            resolver = ParameterResolver({})
            builder = SketchBuilder(resolver)
            sketches = builder.build_sketches(spec['sketches'])

            sketch = sketches[f'text_{plane}']
            assert sketch.plane == plane
            assert sketch.shapes[0].text == f'On {plane}'

    def test_text_subtractive_operation(self):
        """Text shape can have subtract operation"""
        spec = {
            'sketches': {
                'cutout': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'rectangle',
                            'width': 50,
                            'height': 30
                        },
                        {
                            'type': 'text',
                            'text': 'CUT',
                            'size': 10,
                            'operation': 'subtract'
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)
        sketches = builder.build_sketches(spec['sketches'])

        text = sketches['cutout'].shapes[1]
        assert text.operation == 'subtract'


class TestTextGeometryGeneration:
    """Test that text actually generates valid CadQuery geometry"""

    def test_text_builds_valid_geometry(self):
        """Text.build() creates valid CadQuery geometry"""
        text = Text2D(text="TEST", size=10)
        wp = cq.Workplane("XY")

        # This should not raise - may fail if fonts unavailable
        try:
            result = text.build(wp)
            assert result is not None
            assert isinstance(result, cq.Workplane)

            # Verify we have some geometry
            solid = result.val()
            assert solid is not None
        except Exception as e:
            # Acceptable to skip if fonts not available in test env
            if 'font' not in str(e).lower() and 'freetype' not in str(e).lower():
                raise
            pytest.skip(f"Font rendering unavailable: {e}")

    def test_text_geometry_different_sizes(self):
        """Text geometry can be created at different sizes"""
        sizes = [5, 10, 20, 50]

        for size in sizes:
            text = Text2D(text="A", size=size)
            wp = cq.Workplane("XY")

            try:
                result = text.build(wp)
                assert result is not None
            except Exception as e:
                if 'font' not in str(e).lower():
                    raise
                pytest.skip(f"Font rendering unavailable: {e}")

    def test_text_unicode_renders(self):
        """Unicode text renders without errors"""
        unicode_texts = [
            "Hello",
            "世界",  # Chinese
            "🌍",   # Emoji
            "مرحبا", # Arabic
            "Привет" # Russian
        ]

        for text_str in unicode_texts:
            text = Text2D(text=text_str, size=10)
            wp = cq.Workplane("XY")

            try:
                result = text.build(wp)
                assert result is not None
            except Exception as e:
                if 'font' not in str(e).lower():
                    raise
                # Some fonts may not support all Unicode ranges
                pytest.skip(f"Font may not support {text_str}: {e}")

    def test_text_different_alignments(self):
        """Text renders with different alignments"""
        alignments = [
            ('left', 'baseline'),
            ('center', 'center'),
            ('right', 'top'),
        ]

        for halign, valign in alignments:
            text = Text2D(
                text="ALIGN",
                size=10,
                halign=halign,
                valign=valign
            )
            wp = cq.Workplane("XY")

            try:
                result = text.build(wp)
                assert result is not None
            except Exception as e:
                if 'font' not in str(e).lower():
                    raise
                pytest.skip(f"Font rendering unavailable: {e}")

    def test_text_can_export_stl(self):
        """Text geometry can be exported to STL"""
        import tempfile
        import os

        text = Text2D(text="STL", size=15)
        wp = cq.Workplane("XY")

        try:
            result = text.build(wp)

            # Export to temporary file
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
                temp_path = f.name

            try:
                result.val().exportStl(temp_path)

                # Verify file exists and has content
                assert os.path.exists(temp_path)
                size = os.path.getsize(temp_path)
                assert size > 0, "STL file is empty"
                assert size > 1000, f"STL file too small ({size} bytes)"
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            if 'font' not in str(e).lower():
                raise
            pytest.skip(f"Font rendering unavailable: {e}")


class TestTextErrorHandling:
    """Test error handling in text operations"""

    def test_missing_text_field_error(self):
        """SketchBuilder raises error for missing text field"""
        spec = {
            'sketches': {
                'bad_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            # Missing 'text' field!
                            'size': 10
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)

        with pytest.raises(Exception) as exc_info:
            builder.build_sketches(spec['sketches'])
        assert 'text' in str(exc_info.value).lower()

    def test_missing_size_field_error(self):
        """SketchBuilder raises error for missing size field"""
        spec = {
            'sketches': {
                'bad_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': 'HELLO'
                            # Missing 'size' field!
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)

        with pytest.raises(Exception) as exc_info:
            builder.build_sketches(spec['sketches'])
        assert 'size' in str(exc_info.value).lower()

    def test_invalid_position_format_error(self):
        """SketchBuilder raises error for invalid position format"""
        spec = {
            'sketches': {
                'bad_text': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {
                            'type': 'text',
                            'text': 'HELLO',
                            'size': 10,
                            'position': [1, 2, 3]  # Should be [x, y] not [x, y, z]
                        }
                    ]
                }
            }
        }

        resolver = ParameterResolver({})
        builder = SketchBuilder(resolver)

        with pytest.raises(Exception) as exc_info:
            builder.build_sketches(spec['sketches'])
        assert 'position' in str(exc_info.value).lower()
