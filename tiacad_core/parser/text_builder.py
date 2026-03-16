"""
TiaCAD Text Operations Builder

Implements text operations for engraving and embossing text on part faces.
"""

import cadquery as cq
import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING

from ..part import Part, PartRegistry
from .parameter_resolver import ParameterResolver
from ..selector_resolver import SelectorResolver, FeatureType
from .metadata_utils import copy_propagating_metadata

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

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

    def _validate_required_params(self, name: str, spec: Dict[str, Any]):
        """Validate required text op fields. Returns (input_name, input_part, text_content, face_selector, position, size, depth)."""
        def _err(field, msg):
            line, col = self._get_line_info(['operations', name, field])
            raise TextBuilderError(msg, operation_name=name, line=line, column=col)

        input_name = spec.get('input')
        if not input_name:
            _err('input', f"Text operation '{name}' missing required 'input' field")
        if not self.registry.exists(input_name):
            available = ', '.join(self.registry.list_parts())
            _err('input', f"Text operation '{name}' input part '{input_name}' not found. Available parts: {available}")
        input_part = self.registry.get(input_name)

        text_content = spec.get('text')
        if not text_content:
            _err('text', f"Text operation '{name}' missing required 'text' field")
        if not isinstance(text_content, str):
            _err('text', f"Text operation '{name}' text must be a string, got: {type(text_content).__name__}")

        face_selector = spec.get('face')
        if not face_selector:
            _err('face', f"Text operation '{name}' missing required 'face' field. Use face selector like '>Z', '<X', '|Y', etc.")

        position = spec.get('position')
        if not position:
            _err('position', f"Text operation '{name}' missing required 'position' field. Specify as [x, y] coordinates on the face.")
        if not isinstance(position, list) or len(position) != 2:
            _err('position', f"Text operation '{name}' position must be [x, y], got: {position}")

        size = spec.get('size')
        if size is None:
            _err('size', f"Text operation '{name}' missing required 'size' field (font size in mm)")
        if not isinstance(size, (int, float)) or size <= 0:
            _err('size', f"Text operation '{name}' size must be a positive number, got: {size}")

        depth = spec.get('depth')
        if depth is None:
            _err('depth', f"Text operation '{name}' missing required 'depth' field (positive=emboss, negative=engrave)")
        if not isinstance(depth, (int, float)) or depth == 0:
            _err('depth', f"Text operation '{name}' depth must be non-zero number (positive=emboss, negative=engrave), got: {depth}")

        return input_name, input_part, text_content, face_selector, position, size, depth

    def _validate_style_params(self, name: str, spec: Dict[str, Any]):
        """Extract and validate optional style/alignment params. Returns (font, style, halign, valign, font_path, spacing)."""
        def _err(field, msg):
            line, col = self._get_line_info(['operations', name, field])
            raise TextBuilderError(msg, operation_name=name, line=line, column=col)

        font = spec.get('font', 'Liberation Sans')
        style = spec.get('style', 'regular')
        halign = spec.get('halign', 'left')
        valign = spec.get('valign', 'baseline')
        font_path = spec.get('font_path')
        spacing = spec.get('spacing', 1.0)

        valid_styles = ['regular', 'bold', 'italic', 'bold-italic']
        if style not in valid_styles:
            _err('style', f"Text operation '{name}' invalid style '{style}'. Valid styles: {', '.join(valid_styles)}")

        valid_halign = ['left', 'center', 'right']
        if halign not in valid_halign:
            _err('halign', f"Text operation '{name}' invalid halign '{halign}'. Valid values: {', '.join(valid_halign)}")

        valid_valign = ['top', 'center', 'baseline', 'bottom']
        if valign not in valid_valign:
            _err('valign', f"Text operation '{name}' invalid valign '{valign}'. Valid values: {', '.join(valid_valign)}")

        return font, style, halign, valign, font_path, spacing

    def execute_text_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a text operation (engrave or emboss) on a part face.

        Args:
            name: Result part name
            spec: Text operation specification (input, text, face, position, size, depth required;
                  font, style, halign, valign, font_path, spacing optional)

        Raises:
            TextBuilderError: If operation fails
        """
        try:
            resolved_spec = self.resolver.resolve(spec)
            input_name, input_part, text_content, face_selector, position, size, depth = \
                self._validate_required_params(name, resolved_spec)
            font, style, halign, valign, font_path, spacing = \
                self._validate_style_params(name, resolved_spec)

            operation_type = 'engrave' if depth < 0 else 'emboss'
            logger.info(f"Text operation '{name}': {operation_type} '{text_content}' on face {face_selector} of '{input_name}'")

            geometry = self._create_text_on_face(
                input_part=input_part, text_content=text_content,
                face_selector=face_selector, position=position,
                size=size, depth=depth, font=font, style=style,
                halign=halign, valign=valign, font_path=font_path,
                spacing=spacing, context=name
            )

            metadata = copy_propagating_metadata(
                source_metadata=input_part.metadata,
                target_metadata={
                    'source': input_name, 'operation_type': 'text',
                    'text_operation': operation_type, 'text_content': text_content,
                    'face': face_selector, 'depth': depth
                }
            )
            self.registry.add(Part(name=name, geometry=geometry, metadata=metadata))
            logger.debug(f"Created text operation '{name}': {operation_type} on '{input_name}'")

        except TextBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise TextBuilderError(
                f"Failed to execute text operation '{name}': {str(e)}",
                operation_name=name, line=line, column=col
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

    def _select_face_for_text(self, input_part: Part, face_selector: str, context: str) -> None:
        """Validate face selector resolves to at least one face; warn on multiple matches."""
        faces = SelectorResolver(input_part.geometry).resolve(face_selector, FeatureType.FACE)
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

    def _map_cq_font_style(self, style: str, font: str, context: str) -> str:
        """Map TiaCAD style name to CadQuery font style string."""
        # bold-italic falls back to bold — CadQuery limitation
        cq_style = 'bold' if style == 'bold-italic' else style
        if style == 'bold-italic':
            logger.warning(
                f"Text operation '{context}': 'bold-italic' style not fully supported by CadQuery, "
                f"using 'bold' instead. Font: {font}"
            )
        return cq_style

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
        """Create text geometry on a selected face of the input part (emboss or engrave)."""
        try:
            self._select_face_for_text(input_part, face_selector, context)
            cq_font_style = self._map_cq_font_style(style, font, context)
            is_engrave = depth < 0

            face_wp = input_part.geometry.faces(face_selector).workplane()
            if position[0] != 0 or position[1] != 0:
                face_wp = face_wp.center(position[0], position[1])

            try:
                result = self._create_text_geometry(
                    workplane=face_wp,
                    text_content=text_content,
                    size=size,
                    abs_depth=abs(depth),
                    font=font,
                    font_path=font_path,
                    cq_font_style=cq_font_style,
                    halign=halign,
                    valign=valign,
                    is_engrave=is_engrave
                )
            except Exception as e:
                error_str = str(e).lower()
                if 'font' in error_str or 'fontconfig' in error_str:
                    raise TextBuilderError(
                        f"Text operation '{context}' font error: {str(e)}. "
                        f"Font '{font}' may not be available on this system. "
                        f"Try using 'Liberation Sans' or specify a custom font_path.",
                        operation_name=context
                    )
                raise TextBuilderError(f"Failed to create text geometry: {str(e)}", operation_name=context)

            logger.debug(f"{'Engraved' if is_engrave else 'Embossed'} text '{text_content}' with depth {depth}")
            return result

        except TextBuilderError:
            raise
        except Exception as e:
            raise TextBuilderError(f"Failed to create text on face: {str(e)}", operation_name=context) from e

    def __repr__(self) -> str:
        return f"TextBuilder(parts={len(self.registry)}, resolver={self.resolver})"
