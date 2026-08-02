"""
Sketch - 2D Profile System for TiaCAD

Provides 2D sketch functionality for creating profiles that can be extruded,
revolved, swept, or lofted into 3D geometry.

Supported Shapes:
- Rectangle: Basic rectangular profiles
- Circle: Circular profiles
- Ellipse: Elliptical profiles
- Polygon: Custom polygonal profiles from points (straight edges only)
- Path: Custom profiles mixing straight lines and circular arcs
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
    def __init__(self, message: str, sketch_name: Optional[str] = None, **kwargs):
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


class Ellipse2D(Shape2D):
    """
    2D Ellipse shape.

    Direct analog of Circle2D for the non-circular case (elliptical holes,
    bosses, or as a building block for organic profiles) — see
    KNOWN_LIMITATIONS.md #18 / TCAD-DSL-1, which this closes for the
    standalone-shape case. For curves embedded within a larger profile (an
    ellipse *arc* as one edge of a multi-segment outline, as opposed to a
    complete closed ellipse), see Path2D below.

    Attributes:
        x_radius: Radius along the sketch plane's local X axis
        y_radius: Radius along the sketch plane's local Y axis
        center: Center point in 2D sketch space [x, y]
        rotation: Rotation of the ellipse's own axes, in degrees
        operation: 'add' or 'subtract'
    """

    def __init__(self, x_radius: float, y_radius: float,
                 center: Tuple[float, float] = (0, 0),
                 rotation: float = 0.0,
                 operation: str = 'add'):
        """
        Create a 2D ellipse.

        Args:
            x_radius: Radius along local X axis
            y_radius: Radius along local Y axis
            center: Center point [x, y] (default: [0, 0])
            rotation: Rotation in degrees (default: 0)
            operation: 'add' or 'subtract' (default: 'add')
        """
        super().__init__('ellipse', operation)
        self.x_radius = x_radius
        self.y_radius = y_radius
        self.center = center
        self.rotation = rotation

        if x_radius <= 0:
            raise SketchError(f"Ellipse x_radius must be positive, got {x_radius}")
        if y_radius <= 0:
            raise SketchError(f"Ellipse y_radius must be positive, got {y_radius}")

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """Build ellipse on workplane."""
        wp = workplane.workplane(offset=0)

        if self.center != (0, 0):
            wp = wp.center(self.center[0], self.center[1])

        wp = wp.ellipse(self.x_radius, self.y_radius, rotation_angle=self.rotation)

        logger.debug(
            f"Built ellipse x_radius={self.x_radius} y_radius={self.y_radius} "
            f"at {self.center}, rotation={self.rotation}, operation={self.operation}"
        )

        return wp

    def __repr__(self) -> str:
        return (
            f"Ellipse2D(x_radius={self.x_radius}, y_radius={self.y_radius}, "
            f"center={self.center}, rotation={self.rotation}, operation={self.operation})"
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


class Path2D(Shape2D):
    """
    2D Path shape built from a sequence of line/arc/ellipse_arc/spline
    segments — the general mechanism for profiles that mix straight edges
    with true curves, closing the "Sketch DSL has no arc/ellipse/spline
    primitive" gap (KNOWN_LIMITATIONS.md #18 / TCAD-DSL-1, TCAD-DSL-2).
    Where Polygon2D only connects points with straight lines, Path2D's
    segments can be:

    - ``{line: [x, y]}`` — straight line to (x, y)
    - ``{arc: {through: [x, y], to: [x, y]}}`` — circular arc from the
      current point, through one point, ending at another
    - ``{ellipse_arc: {x_radius, y_radius, angle1, angle2, rotation_angle:
      0.0, sense: 1}}`` — an elliptical arc from the current point, using
      OCCT's raw angle convention (angle1/angle2 in degrees measured from
      the ellipse's local +x axis, `sense=1` counter-clockwise). The
      recipe that produces a correct, tangent-continuous rounded cap (e.g.
      an egg/ellipsoid end) when revolved around an axis the profile
      touches: model each half as its own ellipse centered ON the axis,
      and use *quarter* arcs at the standard boundaries — bottom pole to
      equator is ``angle1=270, angle2=360``, equator to top pole is
      ``angle1=0, angle2=90`` — with `x_radius` (the shared equatorial
      radius) constant across both halves and `y_radius` set to each
      half's own length. This gives perpendicular tangents at both poles
      and a shared tangent direction at the equator automatically; no
      per-case root-finding needed.
    - ``{spline: {points: [[x, y], ...]}}`` — a spline from the current
      point, interpolated through the given points in order (current
      point is included as the spline's start automatically).

    All four were verified exact against analytic areas (semicircle,
    line+arc+line, and ellipse-arc profiles all matched pi*r^2/2-style
    references to within floating-point precision) and produce genuinely
    watertight, valid solids when extruded/revolved — *provided* the
    profile doesn't touch the revolve axis at a vertex. Revolve profiles
    that do touch the axis (egg/ellipsoid caps, bicones, ...) hit the
    pre-existing, already-accepted apex-tessellation artifact described in
    KNOWN_LIMITATIONS.md #19 (STL export produces a few disconnected mesh
    fragments at the pole despite a topologically valid solid) — this is
    not specific to `ellipse_arc`/`spline`; a pure `line`- or `arc`-only
    profile touching the axis exhibits the identical signature. `tiacad
    build` already warns on this (never fails); no new handling was added
    here.

    An earlier investigation session (2026-08-02) attempted `spline` and
    `ellipse_arc` and did not ship them, believing both hit new geometry
    defects specific to mixing curve types. Re-investigation (TCAD-DSL-2,
    same day) isolated the actual cause of the "non-watertight" result to
    the axis-touching apex artifact above (reproducible with plain
    lines/arcs, unrelated to spline/ellipse_arc), and found the "hard"
    angle1/angle2/sense derivation works correctly on the first
    straightforward attempt (see recipe above). Full detail in
    KNOWN_LIMITATIONS.md #18 and
    docs/developer/CASE_STUDY_MODELING_AN_EGG.md.

    Attributes:
        start: Starting point [x, y]
        segments: List of single-key segment dicts (see above)
        closed: Whether to close the path back to `start` (default: True)
        operation: 'add' or 'subtract'
    """

    SEGMENT_TYPES = ('line', 'arc', 'ellipse_arc', 'spline')

    def __init__(self, start: Tuple[float, float], segments: List[dict],
                 closed: bool = True,
                 operation: str = 'add'):
        """
        Create a 2D path.

        Args:
            start: Starting point [x, y]
            segments: List of single-key segment dicts
            closed: Whether to close the path (default: True)
            operation: 'add' or 'subtract' (default: 'add')
        """
        super().__init__('path', operation)
        self.start = start
        self.segments = segments
        self.closed = closed

        if not segments:
            raise SketchError("Path must have at least one segment")

        for i, seg in enumerate(segments):
            if not isinstance(seg, dict) or len(seg) != 1:
                raise SketchError(
                    f"Path segment {i} must be a single-key dict naming its "
                    f"type (one of {self.SEGMENT_TYPES}), got {seg!r}"
                )
            seg_type = next(iter(seg))
            if seg_type not in self.SEGMENT_TYPES:
                raise SketchError(
                    f"Path segment {i} has unknown type '{seg_type}'. "
                    f"Must be one of {self.SEGMENT_TYPES}"
                )

    def build(self, workplane: cq.Workplane) -> cq.Workplane:
        """Build path on workplane."""
        wp = workplane.workplane(offset=0)
        wp = wp.moveTo(self.start[0], self.start[1])

        for index, seg in enumerate(self.segments):
            seg_type, value = next(iter(seg.items()))
            wp = self._build_segment(wp, seg_type, value, index)

        if self.closed:
            wp = wp.close()

        logger.debug(
            f"Built path with {len(self.segments)} segments from {self.start}, "
            f"closed={self.closed}, operation={self.operation}"
        )

        return wp

    def _build_segment(self, wp: cq.Workplane, seg_type: str, value, index: int) -> cq.Workplane:
        """Apply a single path segment to the workplane, chaining from its current point."""
        try:
            if seg_type == 'line':
                return wp.lineTo(value[0], value[1])
            if seg_type == 'arc':
                through, to = value['through'], value['to']
                return wp.threePointArc((through[0], through[1]), (to[0], to[1]))
            if seg_type == 'ellipse_arc':
                return wp.ellipseArc(
                    x_radius=value['x_radius'],
                    y_radius=value['y_radius'],
                    angle1=value['angle1'],
                    angle2=value['angle2'],
                    rotation_angle=value.get('rotation_angle', 0.0),
                    sense=value.get('sense', 1),
                    startAtCurrent=True,
                )
            # seg_type == 'spline' -- the only remaining SEGMENT_TYPES member
            points = [(p[0], p[1]) for p in value['points']]
            return wp.spline(points, includeCurrent=True)
        except (KeyError, IndexError, TypeError) as e:
            raise SketchError(f"Invalid '{seg_type}' segment at index {index}: {e}") from e

    def __repr__(self) -> str:
        return (
            f"Path2D(start={self.start}, segments={len(self.segments)}, "
            f"closed={self.closed}, operation={self.operation})"
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

    def build(self, workplane: cq.Workplane, extrusion_distance: Optional[float] = None) -> cq.Workplane:
        """
        Build text on workplane.

        Note: CadQuery's text() method creates 3D geometry immediately,
        not a 2D wire profile. When used in an extrude operation, the
        extrusion_distance parameter should be provided to create text
        at the final height directly.

        Args:
            workplane: CadQuery workplane to build on
            extrusion_distance: Optional final extrusion distance (for extrude operations)
                              If None, uses 0.1mm placeholder

        Returns:
            Workplane with text shape (3D geometry)
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

        # Determine distance to use
        # If extrusion_distance is provided (from extrude operation), use it
        # Otherwise, use minimal placeholder (0.1mm) for standalone text
        distance = extrusion_distance if extrusion_distance is not None else 0.1

        # Build text - creates 3D geometry directly
        # CadQuery text() method always requires a distance parameter
        try:
            wp = wp.text(
                self.text,
                fontsize=self.size,
                distance=distance,
                font=self.font,
                fontPath=self.font_path,
                kind=cq_kind,
                halign=self.halign,
                valign=self.valign
            )

            logger.debug(
                f"Built text '{self.text}' size={self.size} at {self.position}, "
                f"distance={distance}, font={self.font}, style={self.style}, "
                f"operation={self.operation}"
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
