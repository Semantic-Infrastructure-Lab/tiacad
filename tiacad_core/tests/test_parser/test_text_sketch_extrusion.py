"""
Tests for text sketch extrusion.

This module tests that text sketches can be extruded properly despite
CadQuery's text() method creating 3D geometry directly rather than 2D wires.
"""

import pytest
import cadquery as cq
from tiacad_core.sketch import Sketch2D, Text2D, Rectangle2D
from tiacad_core.parser.extrude_builder import ExtrudeBuilder
from tiacad_core.part import PartRegistry, Part
from tiacad_core.parser.parameter_resolver import ParameterResolver


class TestTextSketchExtrusion:
    """Test text sketch extrusion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PartRegistry()
        self.sketches = {}
        self.resolver = ParameterResolver({})
        self.builder = ExtrudeBuilder(
            part_registry=self.registry,
            sketches=self.sketches,
            parameter_resolver=self.resolver,
            line_tracker=None
        )

    def test_single_text_sketch_extrusion(self):
        """Test extruding a sketch containing single text shape."""
        # Create text sketch
        text_shape = Text2D(
            text="TEST",
            size=10,
            font="Liberation Sans",
            style="regular",
            halign="center",
            position=(0, 0)
        )
        sketch = Sketch2D(
            name="test_text",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[text_shape]
        )

        # Execute extrusion
        spec = {
            'sketch': 'test_text',
            'distance': 5.0,
            'direction': 'Z'
        }

        # Add sketch to builder's sketch dictionary
        self.sketches['test_text'] = sketch

        # Execute operation
        self.builder.execute_extrude_operation('text_extruded', spec)

        # Verify part was created
        assert self.registry.exists('text_extruded')
        part = self.registry.get('text_extruded')
        assert part is not None

        # Verify geometry was created (should have solids)
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Extruded text should create solid geometry"

    def test_multiple_text_shapes_in_sketch(self):
        """Test extruding a sketch with multiple text shapes."""
        # Create sketch with multiple text shapes
        text1 = Text2D(text="Line1", size=8, position=(0, 10))
        text2 = Text2D(text="Line2", size=8, position=(0, 0))
        text3 = Text2D(text="Line3", size=8, position=(0, -10))

        sketch = Sketch2D(
            name="multi_text",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[text1, text2, text3]
        )

        spec = {
            'sketch': 'multi_text',
            'distance': 3.0,
            'direction': 'Z'
        }

        self.sketches['multi_text'] = sketch
        self.builder.execute_extrude_operation('multi_text_extruded', spec)

        # Verify part was created
        assert self.registry.exists('multi_text_extruded')
        part = self.registry.get('multi_text_extruded')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Multiple text shapes should create solid geometry"

    def test_text_mixed_with_rectangle_sketch(self):
        """Test extruding a sketch with both text and rectangle shapes."""
        # Create sketch with text and rectangle
        rect = Rectangle2D(width=50, height=20, center=(0, 0), operation='add')
        text = Text2D(text="Label", size=8, halign="center", position=(0, 0))

        sketch = Sketch2D(
            name="mixed_sketch",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[rect, text]
        )

        spec = {
            'sketch': 'mixed_sketch',
            'distance': 4.0,
            'direction': 'Z'
        }

        self.sketches['mixed_sketch'] = sketch
        self.builder.execute_extrude_operation('mixed_extruded', spec)

        # Verify part was created
        assert self.registry.exists('mixed_extruded')
        part = self.registry.get('mixed_extruded')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Mixed sketch should create solid geometry"

    def test_text_sketch_different_extrusion_distances(self):
        """Test that text is created at the correct extrusion distance."""
        # Create text sketch
        text = Text2D(text="Test", size=10, position=(0, 0))
        sketch = Sketch2D(
            name="text_sketch",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[text]
        )

        self.sketches['text_sketch'] = sketch

        # Test different extrusion distances
        for distance in [1.0, 5.0, 10.0, 20.0]:
            name = f'text_extruded_{distance}'
            spec = {
                'sketch': 'text_sketch',
                'distance': distance,
                'direction': 'Z'
            }

            self.builder.execute_extrude_operation(name, spec)

            # Verify part was created
            assert self.registry.exists(name)
            part = self.registry.get(name)

            # Verify bounding box height matches extrusion distance (approximately)
            bbox = part.geometry.val().BoundingBox()
            height = bbox.zlen
            # Text height should be approximately the extrusion distance
            # (allowing for font size contribution)
            assert height >= distance, \
                f"Text height {height} should be at least extrusion distance {distance}"

    def test_text_sketch_subtract_operation(self):
        """Test text shapes with subtract operation in sketch."""
        # Create base rectangle
        rect = Rectangle2D(width=60, height=30, center=(0, 0), operation='add')

        # Create text shape with subtract operation (creates cutout)
        text = Text2D(
            text="CUT",
            size=12,
            halign="center",
            position=(0, 0),
            operation='subtract'
        )

        sketch = Sketch2D(
            name="cutout_sketch",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[rect, text]
        )

        spec = {
            'sketch': 'cutout_sketch',
            'distance': 3.0,
            'direction': 'Z'
        }

        self.sketches['cutout_sketch'] = sketch
        self.builder.execute_extrude_operation('cutout_extruded', spec)

        # Verify part was created
        assert self.registry.exists('cutout_extruded')
        part = self.registry.get('cutout_extruded')

        # Should have created geometry with text cut out
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Sketch with text cutout should create solid geometry"

    def test_text_sketch_xz_plane(self):
        """Test extruding text sketch on XZ plane."""
        text = Text2D(text="XZ", size=10, position=(0, 0))
        sketch = Sketch2D(
            name="xz_text",
            plane="XZ",
            origin=(0, 0, 0),
            shapes=[text]
        )

        spec = {
            'sketch': 'xz_text',
            'distance': 5.0,
            'direction': 'Y'
        }

        self.sketches['xz_text'] = sketch
        self.builder.execute_extrude_operation('xz_extruded', spec)

        assert self.registry.exists('xz_extruded')
        part = self.registry.get('xz_extruded')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "XZ plane text extrusion should work"

    def test_text_sketch_yz_plane(self):
        """Test extruding text sketch on YZ plane."""
        text = Text2D(text="YZ", size=10, position=(0, 0))
        sketch = Sketch2D(
            name="yz_text",
            plane="YZ",
            origin=(0, 0, 0),
            shapes=[text]
        )

        spec = {
            'sketch': 'yz_text',
            'distance': 5.0,
            'direction': 'X'
        }

        self.sketches['yz_text'] = sketch
        self.builder.execute_extrude_operation('yz_extruded', spec)

        assert self.registry.exists('yz_extruded')
        part = self.registry.get('yz_extruded')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "YZ plane text extrusion should work"

    def test_text2d_build_with_extrusion_distance(self):
        """Test that Text2D.build() accepts extrusion_distance parameter."""
        text = Text2D(text="Test", size=10, position=(0, 0))
        wp = cq.Workplane("XY")

        # Build with extrusion distance
        result_wp = text.build(wp, extrusion_distance=5.0)

        # Verify geometry was created
        assert result_wp is not None
        solids = result_wp.solids().vals()
        assert len(solids) > 0, "Text.build() should create solid geometry"

        # Check that height is approximately correct
        bbox = result_wp.val().BoundingBox()
        assert bbox.zlen >= 5.0, \
            f"Text height {bbox.zlen} should be at least extrusion distance 5.0"

    def test_text2d_build_without_extrusion_distance(self):
        """Test that Text2D.build() works without extrusion_distance (backward compat)."""
        text = Text2D(text="Test", size=10, position=(0, 0))
        wp = cq.Workplane("XY")

        # Build without extrusion distance (should use default 0.1)
        result_wp = text.build(wp)

        # Verify geometry was created
        assert result_wp is not None
        solids = result_wp.solids().vals()
        assert len(solids) > 0, "Text.build() should create solid geometry"

    def test_text_extrusion_with_taper(self):
        """Test that text extrusion with taper parameter works."""
        text = Text2D(text="TAPER", size=12, position=(0, 0))
        sketch = Sketch2D(
            name="taper_text",
            plane="XY",
            origin=(0, 0, 0),
            shapes=[text]
        )

        spec = {
            'sketch': 'taper_text',
            'distance': 10.0,
            'direction': 'Z',
            'taper': 5.0  # 5 degree taper
        }

        self.sketches['taper_text'] = sketch
        self.builder.execute_extrude_operation('tapered_text', spec)

        # Note: Text doesn't actually support taper in CadQuery text() method,
        # but we should handle it gracefully
        assert self.registry.exists('tapered_text')
        part = self.registry.get('tapered_text')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Tapered text extrusion should create geometry"

    def test_text_sketch_with_origin_offset(self):
        """Test text sketch extrusion with non-zero origin."""
        text = Text2D(text="OFFSET", size=10, position=(0, 0))
        sketch = Sketch2D(
            name="offset_text",
            plane="XY",
            origin=(10, 20, 5),  # Offset origin
            shapes=[text]
        )

        spec = {
            'sketch': 'offset_text',
            'distance': 5.0,
            'direction': 'Z'
        }

        self.sketches['offset_text'] = sketch
        self.builder.execute_extrude_operation('offset_extruded', spec)

        assert self.registry.exists('offset_extruded')
        part = self.registry.get('offset_extruded')
        solids = part.geometry.solids().vals()
        assert len(solids) > 0, "Text with offset origin should create geometry"

        # Verify the text was positioned at the offset origin
        bbox = part.geometry.val().BoundingBox()
        # Text should be offset from (0, 0, 0) - center should not be at origin
        text_center_x = (bbox.xmin + bbox.xmax) / 2
        # With origin at (10, 20, 5), text center should be shifted from zero
        assert text_center_x > 0, \
            f"Text with offset origin should be shifted: center X = {text_center_x}"
