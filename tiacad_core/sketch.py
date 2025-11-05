"""
Sketch - 2D Profile System for TiaCAD

Provides 2D sketch functionality for creating profiles that can be extruded,
revolved, swept, or lofted into 3D geometry.

Supported Shapes:
- Rectangle: Basic rectangular profiles
- Circle: Circular profiles
- Polygon: Custom polygonal profiles from points
- Text: 2D text that can be extruded into 3D

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import List, Tuple, Optional
import cadquery as cq

from .utils.exceptions import TiaCADError

logger = logging.getLogger(__name__)


class SketchError(TiaCADError):
    """Error during sketch creation or manipulation"""
    def __init__(self, message: str, sketch_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.sketch_name = sketch_name


class Shape2D:
    """
    Base class for 2D shapes in a sketch.

    Attributes:
        shape_type: Type of shape (rectangle, circle, polygon)
        operation: Operation mode ('add' or 'subtract')
    """

    def __init__(self, shape_type: str, operation: str = 'add'):
        """
        Initialize 2D shape.

        Args:
            shape_type: Shape type identifier
            operation: 'add' to add material, 'subtract' to remove (default: 'add')
        """
        self.shape_type = shape_type
        self.operation = operation

        if operation not in ['add', 'subtract']:
            raise SketchError(
                f"Invalid operation '{operation}'. Must be 'add' or 'subtract'"
            )

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """
        Build this shape on the given workplane.

        Args:
            workplane: CadQuery workplane to build on

        Returns:
            Workplane with shape added

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement build()")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(operation={self.operation})"


class Rectangle2D(Shape2D):
    """
    2D Rectangle shape.

    Attributes:
        width: Rectangle width
        height: Rectangle height
        center: Center point in 2D sketch space [x, y]
        operation: 'add' or 'subtract'
    """

    def __init__(self, width: float, height: float,
                 center: Tuple[float, float] = (0, 0),
                 operation: str = 'add'):
        """
        Create a 2D rectangle.

        Args:
            width: Rectangle width
            height: Rectangle height
            center: Center point [x, y] (default: [0, 0])
            operation: 'add' or 'subtract' (default: 'add')
        """
        super().__init__('rectangle', operation)
        self.width = width
        self.height = height
        self.center = center

        if width <= 0:
            raise SketchError(f"Rectangle width must be positive, got {width}")
        if height <= 0:
            raise SketchError(f"Rectangle height must be positive, got {height}")

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """Build rectangle on workplane."""
        # Move to center point
        wp = workplane.workplane(offset=0)

        # CadQuery's rect() centers the rectangle at current position
        # So we need to move to the desired center first
        if self.center != (0, 0):
            wp = wp.center(self.center[0], self.center[1])

        # Create rectangle
        wp = wp.rect(self.width, self.height)

        logger.debug(
            f"Built rectangle {self.width}x{self.height} at {self.center}, "
            f"operation={self.operation}"
        )

        return wp

    def __repr__(self) -> str:
        return (
            f"Rectangle2D(width={self.width}, height={self.height}, "
            f"center={self.center}, operation={self.operation})"
        )


class Circle2D(Shape2D):
    """
    2D Circle shape.

    Attributes:
        radius: Circle radius
        center: Center point in 2D sketch space [x, y]
        operation: 'add' or 'subtract'
    """

    def __init__(self, radius: float,
                 center: Tuple[float, float] = (0, 0),
                 operation: str = 'add'):
        """
        Create a 2D circle.

        Args:
            radius: Circle radius
            center: Center point [x, y] (default: [0, 0])
            operation: 'add' or 'subtract' (default: 'add')
        """
        super().__init__('circle', operation)
        self.radius = radius
        self.center = center

        if radius <= 0:
            raise SketchError(f"Circle radius must be positive, got {radius}")

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """Build circle on workplane."""
        # Move to center point
        wp = workplane.workplane(offset=0)

        if self.center != (0, 0):
            wp = wp.center(self.center[0], self.center[1])

        # Create circle
        wp = wp.circle(self.radius)

        logger.debug(
            f"Built circle radius={self.radius} at {self.center}, "
            f"operation={self.operation}"
        )

        return wp

    def __repr__(self) -> str:
        return (
            f"Circle2D(radius={self.radius}, center={self.center}, "
            f"operation={self.operation})"
        )


class Polygon2D(Shape2D):
    """
    2D Polygon shape from points.

    Attributes:
        points: List of [x, y] points defining polygon
        closed: Whether to close the polygon (default: True)
        operation: 'add' or 'subtract'
    """

    def __init__(self, points: List[Tuple[float, float]],
                 closed: bool = True,
                 operation: str = 'add'):
        """
        Create a 2D polygon.

        Args:
            points: List of [x, y] points
            closed: Whether to close polygon (default: True)
            operation: 'add' or 'subtract' (default: 'add')
        """
        super().__init__('polygon', operation)
        self.points = points
        self.closed = closed

        if len(points) < 3:
            raise SketchError(
                f"Polygon must have at least 3 points, got {len(points)}"
            )

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """Build polygon on workplane."""
        wp = workplane.workplane(offset=0)

        # Create polyline
        wp = wp.polyline(self.points)

        # Close if needed
        if self.closed:
            wp = wp.close()

        logger.debug(
            f"Built polygon with {len(self.points)} points, "
            f"closed={self.closed}, operation={self.operation}"
        )

        return wp

    def __repr__(self) -> str:
        return (
            f"Polygon2D(points={len(self.points)}, closed={self.closed}, "
            f"operation={self.operation})"
        )


class Text2D(Shape2D):
    """
    2D Text shape for sketches.

    Creates text geometry that can be extruded into 3D. Text is positioned
    on the sketch plane and can be combined with other shapes.

    Attributes:
        text: The text string to render
        size: Font size (height in mm)
        font: Font family name
        font_path: Path to custom font file (optional)
        style: Font style ('regular', 'bold', 'italic', 'bold-italic')
        halign: Horizontal alignment ('left', 'center', 'right')
        valign: Vertical alignment ('top', 'center', 'baseline', 'bottom')
        position: Position in 2D sketch space [x, y]
        spacing: Character spacing multiplier (default: 1.0)
        operation: 'add' or 'subtract'
    """

    VALID_STYLES = ['regular', 'bold', 'italic', 'bold-italic']
    VALID_HALIGN = ['left', 'center', 'right']
    VALID_VALIGN = ['top', 'center', 'baseline', 'bottom']

    def __init__(self,
                 text: str,
                 size: float,
                 font: str = "Liberation Sans",
                 font_path: Optional[str] = None,
                 style: str = "regular",
                 halign: str = "left",
                 valign: str = "baseline",
                 position: Tuple[float, float] = (0, 0),
                 spacing: float = 1.0,
                 operation: str = 'add'):
        """
        Create a 2D text shape.

        Args:
            text: Text string to render
            size: Font size (height in mm)
            font: Font family name (default: "Liberation Sans")
            font_path: Path to custom font file (optional)
            style: Font style (default: "regular")
            halign: Horizontal alignment (default: "left")
            valign: Vertical alignment (default: "baseline")
            position: Center point [x, y] (default: [0, 0])
            spacing: Character spacing multiplier (default: 1.0)
            operation: 'add' or 'subtract' (default: 'add')

        Raises:
            SketchError: If parameters are invalid
        """
        super().__init__('text', operation)

        # Validate text
        if not text or not text.strip():
            raise SketchError("Text cannot be empty")

        # Validate Unicode
        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            raise SketchError(f"Invalid Unicode in text: {e}")

        self.text = text

        # Validate size
        if size <= 0:
            raise SketchError(f"Text size must be positive, got {size}")
        if size < 0.5:
            logger.warning(
                f"Text size {size}mm is very small and may not render well. "
                f"Consider using size >= 1mm"
            )
        self.size = size

        # Font settings
        self.font = font
        self.font_path = font_path

        # Validate style
        if style not in self.VALID_STYLES:
            raise SketchError(
                f"Invalid text style '{style}'. "
                f"Must be one of: {', '.join(self.VALID_STYLES)}"
            )
        self.style = style

        # Validate alignment
        if halign not in self.VALID_HALIGN:
            raise SketchError(
                f"Invalid horizontal alignment '{halign}'. "
                f"Must be one of: {', '.join(self.VALID_HALIGN)}"
            )
        if valign not in self.VALID_VALIGN:
            raise SketchError(
                f"Invalid vertical alignment '{valign}'. "
                f"Must be one of: {', '.join(self.VALID_VALIGN)}"
            )
        self.halign = halign
        self.valign = valign

        # Position and spacing
        self.position = position

        if spacing <= 0:
            raise SketchError(f"Text spacing must be positive, got {spacing}")
        self.spacing = spacing

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """
        Build text on workplane.

        Note: CadQuery's text() method creates 3D geometry immediately,
        not a 2D wire profile. This is handled specially by the extrude
        operation which will detect pre-extruded text shapes.

        Args:
            workplane: CadQuery workplane to build on

        Returns:
            Workplane with text shape
        """
        wp = workplane.workplane(offset=0)

        # Move to position if not at origin
        if self.position != (0, 0):
            wp = wp.center(self.position[0], self.position[1])

        # Map TiaCAD style names to CadQuery 'kind' parameter
        # CadQuery expects: 'regular', 'bold', 'italic'
        # For bold-italic, we'll use bold and handle with font name
        cq_kind = self.style
        if self.style == 'bold-italic':
            cq_kind = 'bold'  # CadQuery doesn't have bold-italic directly

        # Build text - creates 3D geometry
        # Use a minimal extrusion distance (0.1mm) as a placeholder
        # The actual extrusion will be handled by the extrude operation
        try:
            wp = wp.text(
                self.text,
                fontsize=self.size,
                distance=0.1,  # Minimal placeholder extrusion
                font=self.font,
                fontPath=self.font_path,
                kind=cq_kind,
                halign=self.halign,
                valign=self.valign
            )

            logger.debug(
                f"Built text '{self.text}' size={self.size} at {self.position}, "
                f"font={self.font}, style={self.style}, operation={self.operation}"
            )
        except Exception as e:
            # Provide helpful error for font issues
            error_msg = str(e)
            if 'font' in error_msg.lower() or 'freetype' in error_msg.lower():
                raise SketchError(
                    f"Font error rendering text '{self.text}': {error_msg}. "
                    f"Font '{self.font}' may not be available. "
                    f"Try 'Liberation Sans', 'Arial', or specify font_path."
                )
            raise SketchError(f"Error rendering text '{self.text}': {error_msg}")

        return wp

    def __repr__(self) -> str:
        return (
            f"Text2D(text='{self.text}', size={self.size}, font='{self.font}', "
            f"style='{self.style}', position={self.position}, operation={self.operation})"
        )


class Sketch2D:
    """
    2D Sketch containing multiple shapes.

    A sketch is a 2D profile on a coordinate plane (XY, XZ, or YZ) that can be
    used for extrude, revolve, sweep, or loft operations.

    Attributes:
        name: Sketch name
        plane: Coordinate plane ('XY', 'XZ', or 'YZ')
        origin: 3D origin point [x, y, z]
        shapes: List of Shape2D objects
        profile: CadQuery Workplane with combined 2D geometry (built on demand)
    """

    VALID_PLANES = ['XY', 'XZ', 'YZ']

    def __init__(self, name: str, plane: str, origin: Tuple[float, float, float],
                 shapes: List[Shape2D]):
        """
        Initialize 2D sketch.

        Args:
            name: Sketch identifier
            plane: Coordinate plane ('XY', 'XZ', 'YZ')
            origin: 3D origin point [x, y, z]
            shapes: List of Shape2D objects

        Raises:
            SketchError: If plane is invalid or shapes list is empty
        """
        self.name = name
        self.plane = plane.upper()
        self.origin = origin
        self.shapes = shapes
        self.profile = None

        # Validate plane
        if self.plane not in self.VALID_PLANES:
            raise SketchError(
                f"Invalid plane '{plane}'. Must be one of: {self.VALID_PLANES}",
                sketch_name=name
            )

        # Validate shapes
        if not shapes:
            raise SketchError(
                f"Sketch '{name}' must contain at least one shape",
                sketch_name=name
            )

        logger.info(
            f"Created sketch '{name}' on {plane} plane with {len(shapes)} shapes"
        )

    def build_profile(self) -> cq.Workplane:
        """
        Build the 2D profile - validates sketch structure.

        Note: Actual geometry building happens in the operation builder
        (e.g., ExtrudeBuilder) which handles both additive and subtractive
        shapes appropriately.

        Returns:
            Self (for method chaining)

        Raises:
            SketchError: If sketch validation fails
        """
        # Validate that sketch has at least one additive shape
        add_shapes = [s for s in self.shapes if s.operation == 'add']
        if not add_shapes:
            raise SketchError(
                f"Sketch '{self.name}' must have at least one 'add' shape",
                sketch_name=self.name
            )

        # Count shapes by type
        subtract_shapes = [s for s in self.shapes if s.operation == 'subtract']

        logger.info(
            f"Validated sketch '{self.name}': {len(add_shapes)} add, "
            f"{len(subtract_shapes)} subtract shapes"
        )

        # Mark as validated
        self.profile = self  # Marker that build_profile was called

        return self

    def __repr__(self) -> str:
        return (
            f"Sketch2D(name={self.name}, plane={self.plane}, "
            f"origin={self.origin}, shapes={len(self.shapes)})"
        )
