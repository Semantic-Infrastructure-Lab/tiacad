"""
TiaCAD Text Operations Builder

Implements text operations for engraving and embossing text on part faces.
"""

import cadquery as cq
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..part import Part, PartRegistry
from .parameter_resolver import ParameterResolver
from ..selector_resolver import SelectorResolver, FeatureType

logger = logging.getLogger(__name__)


class TextBuilderError(Exception):
    """Error during text operation building or execution"""

    def __init__(self, message: str, operation_name: str = None,
                 line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(message)
        self.operation_name = operation_name
        self.line = line
        self.column = column


class TextBuilder:
    """
    Builds text operations for engraving and embossing on part faces.

    Text operations allow you to:
    - Engrave text into a part face (negative depth)
    - Emboss text onto a part face (positive depth)

    The text is positioned on a selected face and can use all the same
    styling options as text primitives (font, style, alignment, etc.).

    Usage:
        builder = TextBuilder(part_registry, parameter_resolver)
        builder.execute_text_operation('serial_number', {
            'input': 'case_body',
            'text': 'S/N: 12345',
            'face': '>Z',
            'position': [10, 10],
            'size': 4,
            'depth': -0.5  # Negative = engrave
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize text builder.

        Args:
            part_registry: Registry of available parts
            parameter_resolver: Resolver for ${...} expressions
            line_tracker: Optional line tracker for enhanced error messages
        """
        self.registry = part_registry
        self.resolver = parameter_resolver
        self.line_tracker = line_tracker

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get line and column info for a YAML path."""
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def execute_text_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a text operation (engrave or emboss).

        Creates engraved or embossed text on a part face by:
        1. Selecting the target face
        2. Creating a workplane on that face
        3. Creating and positioning text geometry
        4. Boolean operation: union (emboss) or subtract (engrave)

        Args:
            name: Result part name
            spec: Text operation specification with:
                - input: Input part name (required)
                - text: Text content (required)
                - face: Face selector like '>Z', '|X' (required)
                - position: [x, y] position on face (required)
                - size: Font size in mm (required)
                - depth: Extrusion depth - positive=emboss, negative=engrave (required)
                - font: Font family (optional, default: "Liberation Sans")
                - style: Font style (optional, default: "regular")
                - halign: Horizontal alignment (optional, default: "left")
                - valign: Vertical alignment (optional, default: "baseline")
                - font_path: Custom font path (optional)
                - spacing: Character spacing multiplier (optional, default: 1.0)

        Raises:
            TextBuilderError: If operation fails
        """
        try:
            # Resolve parameters
            resolved_spec = self.resolver.resolve(spec)

            # Validate and get input part
            input_name = resolved_spec.get('input')
            if not input_name:
                line, col = self._get_line_info(['operations', name, 'input'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'input' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not self.registry.exists(input_name):
                line, col = self._get_line_info(['operations', name, 'input'])
                available = ', '.join(self.registry.list_parts())
                raise TextBuilderError(
                    f"Text operation '{name}' input part '{input_name}' not found. "
                    f"Available parts: {available}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            input_part = self.registry.get(input_name)

            # Validate required text field
            text_content = resolved_spec.get('text')
            if not text_content:
                line, col = self._get_line_info(['operations', name, 'text'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'text' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(text_content, str):
                line, col = self._get_line_info(['operations', name, 'text'])
                raise TextBuilderError(
                    f"Text operation '{name}' text must be a string, got: {type(text_content).__name__}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate face selector
            face_selector = resolved_spec.get('face')
            if not face_selector:
                line, col = self._get_line_info(['operations', name, 'face'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'face' field. "
                    f"Use face selector like '>Z', '<X', '|Y', etc.",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate position
            position = resolved_spec.get('position')
            if not position:
                line, col = self._get_line_info(['operations', name, 'position'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'position' field. "
                    f"Specify as [x, y] coordinates on the face.",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(position, list) or len(position) != 2:
                line, col = self._get_line_info(['operations', name, 'position'])
                raise TextBuilderError(
                    f"Text operation '{name}' position must be [x, y], got: {position}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate size
            size = resolved_spec.get('size')
            if size is None:
                line, col = self._get_line_info(['operations', name, 'size'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'size' field (font size in mm)",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(size, (int, float)) or size <= 0:
                line, col = self._get_line_info(['operations', name, 'size'])
                raise TextBuilderError(
                    f"Text operation '{name}' size must be a positive number, got: {size}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate depth
            depth = resolved_spec.get('depth')
            if depth is None:
                line, col = self._get_line_info(['operations', name, 'depth'])
                raise TextBuilderError(
                    f"Text operation '{name}' missing required 'depth' field "
                    f"(positive=emboss, negative=engrave)",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(depth, (int, float)) or depth == 0:
                line, col = self._get_line_info(['operations', name, 'depth'])
                raise TextBuilderError(
                    f"Text operation '{name}' depth must be non-zero number "
                    f"(positive=emboss, negative=engrave), got: {depth}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Get optional parameters with defaults
            font = resolved_spec.get('font', 'Liberation Sans')
            style = resolved_spec.get('style', 'regular')
            halign = resolved_spec.get('halign', 'left')
            valign = resolved_spec.get('valign', 'baseline')
            font_path = resolved_spec.get('font_path')
            spacing = resolved_spec.get('spacing', 1.0)

            # Validate style
            valid_styles = ['regular', 'bold', 'italic', 'bold-italic']
            if style not in valid_styles:
                line, col = self._get_line_info(['operations', name, 'style'])
                raise TextBuilderError(
                    f"Text operation '{name}' invalid style '{style}'. "
                    f"Valid styles: {', '.join(valid_styles)}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate alignment
            valid_halign = ['left', 'center', 'right']
            if halign not in valid_halign:
                line, col = self._get_line_info(['operations', name, 'halign'])
                raise TextBuilderError(
                    f"Text operation '{name}' invalid halign '{halign}'. "
                    f"Valid values: {', '.join(valid_halign)}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            valid_valign = ['top', 'center', 'baseline', 'bottom']
            if valign not in valid_valign:
                line, col = self._get_line_info(['operations', name, 'valign'])
                raise TextBuilderError(
                    f"Text operation '{name}' invalid valign '{valign}'. "
                    f"Valid values: {', '.join(valid_valign)}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Execute text operation
            operation_type = 'engrave' if depth < 0 else 'emboss'
            logger.info(
                f"Text operation '{name}': {operation_type} '{text_content}' "
                f"on face {face_selector} of '{input_name}'"
            )

            geometry = self._create_text_on_face(
                input_part=input_part,
                text_content=text_content,
                face_selector=face_selector,
                position=position,
                size=size,
                depth=depth,
                font=font,
                style=style,
                halign=halign,
                valign=valign,
                font_path=font_path,
                spacing=spacing,
                context=name
            )

            # Copy appearance metadata from input part
            from .metadata_utils import copy_propagating_metadata

            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'source': input_name,
                    'operation_type': 'text',
                    'text_operation': operation_type,
                    'text_content': text_content,
                    'face': face_selector,
                    'depth': depth
                }
            )

            # Create result part
            result_part = Part(
                name=name,
                geometry=geometry,
                metadata=metadata
            )

            # Add to registry
            self.registry.add(result_part)
            logger.debug(
                f"Created text operation '{name}': {operation_type} on '{input_name}'"
            )

        except TextBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise TextBuilderError(
                f"Failed to execute text operation '{name}': {str(e)}",
                operation_name=name,
                line=line,
                column=col
            ) from e

    def _create_text_geometry(self,
                            workplane: cq.Workplane,
                            text_content: str,
                            size: float,
                            abs_depth: float,
                            font: str,
                            font_path: Optional[str],
                            cq_font_style: str,
                            halign: str,
                            valign: str,
                            is_engrave: bool) -> cq.Workplane:
        """
        Create text geometry on a given workplane (DRY helper).

        Args:
            workplane: CadQuery workplane to create text on
            text_content: Text string
            size: Font size in mm
            abs_depth: Absolute extrusion depth
            font: Font family name
            font_path: Optional custom font path
            cq_font_style: CadQuery font style string
            halign: Horizontal alignment
            valign: Vertical alignment
            is_engrave: True for engraving (cut), False for embossing (union)

        Returns:
            Workplane with text geometry created and combined
        """
        text_kwargs = {
            'txt': text_content,
            'fontsize': size,
            'distance': abs_depth,
            'kind': cq_font_style,
            'halign': halign,
            'valign': valign,
            'combine': 'cut' if is_engrave else True  # Use 'cut' for engrave, True for emboss
        }

        if font_path:
            text_kwargs['fontPath'] = font_path
        else:
            text_kwargs['font'] = font

        return workplane.text(**text_kwargs)

    def _create_text_on_face(self,
                            input_part: Part,
                            text_content: str,
                            face_selector: str,
                            position: List[float],
                            size: float,
                            depth: float,
                            font: str,
                            style: str,
                            halign: str,
                            valign: str,
                            font_path: Optional[str],
                            spacing: float,
                            context: str) -> cq.Workplane:
        """
        Create text geometry on a selected face of the input part.

        Args:
            input_part: Part to add text to
            text_content: Text to create
            face_selector: Face selector string (e.g., '>Z')
            position: [x, y] position on face
            size: Font size in mm
            depth: Extrusion depth (positive=emboss, negative=engrave)
            font: Font family name
            style: Font style
            halign: Horizontal alignment
            valign: Vertical alignment
            font_path: Custom font file path
            spacing: Character spacing multiplier
            context: Operation name for error messages

        Returns:
            Modified geometry with text applied

        Raises:
            TextBuilderError: If text creation fails
        """
        try:
            # Select the face using SelectorResolver
            selector_resolver = SelectorResolver(input_part.geometry)
            faces = selector_resolver.resolve(face_selector, FeatureType.FACE)

            if not faces:
                raise TextBuilderError(
                    f"No faces found matching selector '{face_selector}' on part '{input_part.name}'",
                    operation_name=context
                )

            if len(faces) > 1:
                logger.warning(
                    f"Text operation '{context}': Face selector '{face_selector}' "
                    f"matched {len(faces)} faces, using first face"
                )

            # Map style names to CadQuery font style strings
            # Note: Not all fonts support all styles, especially 'bold italic'
            font_style_map = {
                'regular': 'regular',
                'bold': 'bold',
                'italic': 'italic',
                'bold-italic': 'bold'  # Fall back to 'bold' as 'bold italic' often unsupported
            }
            cq_font_style = font_style_map.get(style, 'regular')

            # Warn if bold-italic was requested
            if style == 'bold-italic':
                logger.warning(
                    f"Text operation '{context}': 'bold-italic' style not fully supported by CadQuery, "
                    f"using 'bold' instead. Font: {font}"
                )

            # Absolute depth for text extrusion
            abs_depth = abs(depth)

            # Create text geometry on the selected face using CadQuery's combine parameter
            # This approach avoids the "Bnd_Box is void" error that occurs with manual cut()
            try:
                # Get the coordinate system of the target face
                # Create a workplane on the target face
                face_wp = input_part.geometry.faces(face_selector).workplane()

                # Move to the specified position on the face
                if position[0] != 0 or position[1] != 0:
                    face_wp = face_wp.center(position[0], position[1])

                # Create text on the positioned workplane with automatic combine
                # Using combine='cut' for engrave or combine=True for emboss
                # This uses CadQuery's built-in boolean logic which handles geometry correctly
                is_engrave = depth < 0
                result = self._create_text_geometry(
                    workplane=face_wp,
                    text_content=text_content,
                    size=size,
                    abs_depth=abs_depth,
                    font=font,
                    font_path=font_path,
                    cq_font_style=cq_font_style,
                    halign=halign,
                    valign=valign,
                    is_engrave=is_engrave
                )

                operation_type = 'engrave' if is_engrave else 'emboss'
                logger.debug(f"{operation_type.capitalize()}ed text '{text_content}' with depth {depth}")

            except Exception as e:
                # Common error: font not found
                error_str = str(e).lower()
                if 'font' in error_str or 'fontconfig' in error_str:
                    raise TextBuilderError(
                        f"Text operation '{context}' font error: {str(e)}. "
                        f"Font '{font}' may not be available on this system. "
                        f"Try using 'Liberation Sans' or specify a custom font_path.",
                        operation_name=context
                    )
                else:
                    raise TextBuilderError(
                        f"Failed to create text geometry: {str(e)}",
                        operation_name=context
                    )

            return result

        except TextBuilderError:
            raise
        except Exception as e:
            raise TextBuilderError(
                f"Failed to create text on face: {str(e)}",
                operation_name=context
            ) from e

    def __repr__(self) -> str:
        return f"TextBuilder(parts={len(self.registry)}, resolver={self.resolver})"
