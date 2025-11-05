"""
PartsBuilder - Build Part objects from YAML primitive specifications

Handles creation of CadQuery geometry from primitive definitions and
wraps them in Part objects for the TiaCAD system.

Supported Primitives:
- box: Rectangular box with size [width, depth, height]
- cylinder: Cylinder with radius and height
- sphere: Sphere with radius
- cone: Cone/frustum with two radii and height
- torus: Torus with major and minor radii
- text: 3D text with text, size, and height

Author: TIA
Version: 0.1.0-alpha
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import cadquery as cq

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from ..geometry.cadquery_backend import CadQueryBackend
from .parameter_resolver import ParameterResolver
from .color_parser import ColorParser
from .appearance_builder import AppearanceBuilder

logger = logging.getLogger(__name__)


class PartsBuilderError(TiaCADError):
    """Error during parts building"""
    def __init__(self, message: str, part_name: str = None):
        super().__init__(message)
        self.part_name = part_name


class PartsBuilder:
    """
    Builds Part objects from YAML primitive specifications.

    Usage:
        builder = PartsBuilder(parameter_resolver)
        registry = builder.build_parts(yaml_data['parts'])
        plate = registry.get('plate')
    """

    def __init__(self, parameter_resolver: ParameterResolver, color_parser: Optional[ColorParser] = None):
        """
        Initialize parts builder.

        Args:
            parameter_resolver: Resolver for ${...} expressions
            color_parser: Optional color parser for color/material support
        """
        self.resolver = parameter_resolver
        self.color_parser = color_parser or ColorParser()
        self.appearance_builder = AppearanceBuilder(self.color_parser)
        self.backend = CadQueryBackend()  # Backend for spatial operations

    def build_parts(self, parts_spec: Dict[str, Dict]) -> PartRegistry:
        """
        Build all parts from YAML specification.

        Args:
            parts_spec: Dictionary of part_name → part_definition

        Returns:
            PartRegistry with all built parts

        Raises:
            PartsBuilderError: If part building fails
        """
        registry = PartRegistry()

        for part_name, part_def in parts_spec.items():
            try:
                logger.info(f"Building part '{part_name}'")
                part = self.build_part(part_name, part_def)
                registry.add(part)
                logger.debug(f"Part '{part_name}' built successfully")
            except Exception as e:
                raise PartsBuilderError(
                    f"Failed to build part '{part_name}': {str(e)}",
                    part_name=part_name
                ) from e

        logger.info(f"Built {len(parts_spec)} parts successfully")
        return registry

    def build_part(self, name: str, spec: Dict[str, Any]) -> Part:
        """
        Build a single part from specification.

        Args:
            name: Part name
            spec: Part specification dict with 'primitive' and parameters

        Returns:
            Built Part object

        Raises:
            PartsBuilderError: If spec is invalid or primitive unknown
        """
        # Validate spec has 'primitive' field
        if 'primitive' not in spec:
            raise PartsBuilderError(
                f"Part '{name}' missing 'primitive' field",
                part_name=name
            )

        primitive_type = spec['primitive']

        # Resolve parameters first
        resolved_spec = self.resolver.resolve(spec)

        # Build geometry based on primitive type
        if primitive_type == 'box':
            geometry = self._build_box(name, resolved_spec)
        elif primitive_type == 'cylinder':
            geometry = self._build_cylinder(name, resolved_spec)
        elif primitive_type == 'sphere':
            geometry = self._build_sphere(name, resolved_spec)
        elif primitive_type == 'cone':
            geometry = self._build_cone(name, resolved_spec)
        elif primitive_type == 'torus':
            geometry = self._build_torus(name, resolved_spec)
        elif primitive_type == 'text':
            geometry = self._build_text(name, resolved_spec)
        else:
            raise PartsBuilderError(
                f"Unknown primitive type '{primitive_type}' for part '{name}'",
                part_name=name
            )

        # Build metadata with primitive type
        metadata = {'primitive_type': primitive_type}

        # Parse appearance (color/material/properties) - delegated to AppearanceBuilder
        appearance_metadata = self.appearance_builder.build_appearance_metadata(
            resolved_spec,
            name
        )

        # Merge appearance metadata into part metadata
        metadata.update(appearance_metadata)

        # Create Part object with backend for spatial operations
        part = Part(
            name=name,
            geometry=geometry,
            metadata=metadata,
            backend=self.backend
        )

        return part

    def _build_box(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a box primitive.

        Args:
            name: Part name (for error messages)
            spec: Specification with 'size' [width, depth, height] and optional 'origin'

        Returns:
            CadQuery Workplane with box geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        if 'size' not in spec:
            raise PartsBuilderError(
                f"Box '{name}' missing required 'size' parameter",
                part_name=name
            )

        size = spec['size']
        if not isinstance(size, list) or len(size) != 3:
            raise PartsBuilderError(
                f"Box '{name}' size must be [width, depth, height], got: {size}",
                part_name=name
            )

        width, depth, height = size
        origin = spec.get('origin', 'center')

        # Create box at origin
        box = cq.Workplane("XY").box(width, depth, height, centered=(origin == 'center'))

        return box

    def _build_cylinder(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a cylinder primitive.

        Args:
            name: Part name
            spec: Specification with 'radius', 'height', and optional 'origin'

        Returns:
            CadQuery Workplane with cylinder geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        if 'radius' not in spec:
            raise PartsBuilderError(
                f"Cylinder '{name}' missing required 'radius' parameter",
                part_name=name
            )
        if 'height' not in spec:
            raise PartsBuilderError(
                f"Cylinder '{name}' missing required 'height' parameter",
                part_name=name
            )

        radius = spec['radius']
        height = spec['height']
        origin = spec.get('origin', 'center')

        # Create cylinder
        if origin == 'center':
            # Center at origin
            cylinder = cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, -height/2))
        else:  # origin == 'base'
            # Base at origin
            cylinder = cq.Workplane("XY").circle(radius).extrude(height)

        return cylinder

    def _build_sphere(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a sphere primitive.

        Args:
            name: Part name
            spec: Specification with 'radius'

        Returns:
            CadQuery Workplane with sphere geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        if 'radius' not in spec:
            raise PartsBuilderError(
                f"Sphere '{name}' missing required 'radius' parameter",
                part_name=name
            )

        radius = spec['radius']

        # Create sphere at origin (always centered)
        sphere = cq.Workplane("XY").sphere(radius)

        return sphere

    def _build_cone(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a cone/frustum primitive.

        Args:
            name: Part name
            spec: Specification with 'radius1' (base), 'radius2' (top), 'height'

        Returns:
            CadQuery Workplane with cone geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        if 'radius1' not in spec:
            raise PartsBuilderError(
                f"Cone '{name}' missing required 'radius1' parameter (base radius)",
                part_name=name
            )
        if 'radius2' not in spec:
            raise PartsBuilderError(
                f"Cone '{name}' missing required 'radius2' parameter (top radius)",
                part_name=name
            )
        if 'height' not in spec:
            raise PartsBuilderError(
                f"Cone '{name}' missing required 'height' parameter",
                part_name=name
            )

        radius1 = spec['radius1']  # Base radius
        radius2 = spec['radius2']  # Top radius
        height = spec['height']
        origin = spec.get('origin', 'center')

        # Create cone using loft between two circles
        # CadQuery doesn't have a direct cone primitive, so we use circle -> extrude with taper
        # Or use two circles and loft
        if radius2 == 0:
            # True cone (pointed top)
            # Use circle at base and point at top
            cone = (cq.Workplane("XY")
                    .circle(radius1)
                    .workplane(offset=height)
                    .circle(0.001)  # Very small circle at top (CadQuery doesn't like 0)
                    .loft())
        else:
            # Frustum (truncated cone)
            cone = (cq.Workplane("XY")
                    .circle(radius1)
                    .workplane(offset=height)
                    .circle(radius2)
                    .loft())

        # Adjust origin if needed
        if origin == 'center':
            cone = cone.translate((0, 0, -height/2))
        # else: origin == 'base', already at base

        return cone

    def _build_torus(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a torus primitive.

        Args:
            name: Part name
            spec: Specification with 'major_radius' and 'minor_radius'

        Returns:
            CadQuery Workplane with torus geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        if 'major_radius' not in spec:
            raise PartsBuilderError(
                f"Torus '{name}' missing required 'major_radius' parameter",
                part_name=name
            )
        if 'minor_radius' not in spec:
            raise PartsBuilderError(
                f"Torus '{name}' missing required 'minor_radius' parameter",
                part_name=name
            )

        major_radius = spec['major_radius']  # Distance from center to tube center
        minor_radius = spec['minor_radius']  # Tube radius

        # Create torus using revolve
        # Draw circle at (major_radius, 0) with radius minor_radius, then revolve around Z
        torus = (cq.Workplane("XZ")
                 .center(major_radius, 0)
                 .circle(minor_radius)
                 .revolve(360, (0, 0, 0), (0, 0, 1)))

        return torus

    def _build_text(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a 3D text primitive.

        Args:
            name: Part name
            spec: Specification with 'text', 'size', 'height' (required)
                  and optional 'font', 'style', 'halign', 'valign', 'font_path', 'spacing'

        Returns:
            CadQuery Workplane with 3D text geometry

        Raises:
            PartsBuilderError: If required parameters missing or invalid
        """
        # Validate required parameters
        if 'text' not in spec:
            raise PartsBuilderError(
                f"Text primitive '{name}' missing required 'text' parameter",
                part_name=name
            )
        if 'size' not in spec:
            raise PartsBuilderError(
                f"Text primitive '{name}' missing required 'size' parameter (font size)",
                part_name=name
            )
        if 'height' not in spec:
            raise PartsBuilderError(
                f"Text primitive '{name}' missing required 'height' parameter (extrusion height)",
                part_name=name
            )

        # Extract required parameters
        text = spec['text']
        size = spec['size']
        height = spec['height']

        # Validate text is not empty
        if not text or (isinstance(text, str) and not text.strip()):
            raise PartsBuilderError(
                f"Text primitive '{name}' has empty text string",
                part_name=name
            )

        # Validate numeric parameters
        if size <= 0:
            raise PartsBuilderError(
                f"Text primitive '{name}' size must be positive, got {size}",
                part_name=name
            )
        if height <= 0:
            raise PartsBuilderError(
                f"Text primitive '{name}' height must be positive, got {height}",
                part_name=name
            )

        # Warn about very small sizes
        if size < 1.0:
            logger.warning(
                f"Text primitive '{name}' has very small size {size}mm. "
                f"Text may not render well. Consider size >= 1mm."
            )

        # Extract optional parameters with defaults
        font = spec.get('font', 'Liberation Sans')
        style = spec.get('style', 'regular')
        halign = spec.get('halign', 'center')
        valign = spec.get('valign', 'center')
        font_path = spec.get('font_path', None)
        spacing = spec.get('spacing', 1.0)

        # Validate style
        valid_styles = ['regular', 'bold', 'italic', 'bold-italic']
        if style not in valid_styles:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid style '{style}'. "
                f"Must be one of: {', '.join(valid_styles)}",
                part_name=name
            )

        # Validate alignment
        valid_halign = ['left', 'center', 'right']
        if halign not in valid_halign:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid horizontal alignment '{halign}'. "
                f"Must be one of: {', '.join(valid_halign)}",
                part_name=name
            )

        valid_valign = ['top', 'center', 'baseline', 'bottom']
        if valign not in valid_valign:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid vertical alignment '{valign}'. "
                f"Must be one of: {', '.join(valid_valign)}",
                part_name=name
            )

        # Validate spacing
        if spacing <= 0:
            raise PartsBuilderError(
                f"Text primitive '{name}' spacing must be positive, got {spacing}",
                part_name=name
            )

        # Map style to CadQuery 'kind' parameter
        # CadQuery expects: 'regular', 'bold', 'italic'
        # For bold-italic, use 'bold' (CadQuery limitation)
        cq_kind = style
        if style == 'bold-italic':
            cq_kind = 'bold'

        # Create text on XY plane
        try:
            wp = cq.Workplane("XY")
            text_wp = wp.text(
                text,
                fontsize=size,
                distance=height,  # Full extrusion height (not placeholder like Text2D)
                font=font,
                fontPath=font_path,
                kind=cq_kind,
                halign=halign,
                valign=valign
            )

            logger.debug(
                f"Built text primitive '{name}': text='{text}', size={size}, "
                f"height={height}, font='{font}', style='{style}'"
            )

            return text_wp

        except Exception as e:
            # Provide helpful error for font issues
            error_msg = str(e)
            if 'font' in error_msg.lower() or 'freetype' in error_msg.lower():
                raise PartsBuilderError(
                    f"Font error in text primitive '{name}': {error_msg}. "
                    f"Font '{font}' may not be available. "
                    f"Try 'Liberation Sans', 'Arial', or specify 'font_path' parameter.",
                    part_name=name
                )
            raise PartsBuilderError(
                f"Error creating text primitive '{name}': {error_msg}",
                part_name=name
            )

    def __repr__(self) -> str:
        return f"PartsBuilder(resolver={self.resolver})"
