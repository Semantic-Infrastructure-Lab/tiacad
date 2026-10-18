"""
PartsBuilder - Build Part objects from YAML primitive specifications

Handles creation of CadQuery geometry from primitive definitions and
wraps them in Part objects for the TiaCAD system.

Supported Primitives:
- box: Rectangular box with size [x, y, z]
- cylinder: Cylinder with radius and height
- sphere: Sphere with radius
- cone: Cone/frustum with two radii and height
- torus: Torus with major and minor radii
- text: 3D text with text, size, and height

Author: TIA
Version: 0.1.0-alpha
"""

import difflib
import logging
import warnings
from typing import Dict, Any, Optional
import cadquery as cq

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from ..geometry import GeometryBackend, CadQueryBackend, get_default_backend
from .parameter_resolver import ParameterResolver, parse_length
from .color_parser import ColorParser
from .appearance_builder import AppearanceBuilder

logger = logging.getLogger(__name__)


class PartsBuilderError(TiaCADError):
    """Error during parts building"""
    def __init__(self, message: str, part_name: Optional[str] = None):
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

    def __init__(
        self,
        parameter_resolver: ParameterResolver,
        color_parser: Optional[ColorParser] = None,
        backend: Optional[GeometryBackend] = None,
    ):
        """
        Initialize parts builder.

        Args:
            parameter_resolver: Resolver for ${...} expressions
            color_parser: Optional color parser for color/material support
            backend: Geometry backend for primitive creation and spatial queries
        """
        self.resolver = parameter_resolver
        self.color_parser = color_parser or ColorParser()
        self.appearance_builder = AppearanceBuilder(self.color_parser)
        self.backend = backend or get_default_backend()

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
        # Catch common misuse: 'position' is not valid — direct users to the right key
        if 'position' in spec:
            raise PartsBuilderError(
                f"Part '{name}' has unknown key 'position'. "
                f"Use 'origin: [x, y, z]' to set the part's build origin, "
                f"or use 'operations: transform' to move a part after creation.",
                part_name=name
            )

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
        elif primitive_type == 'polygon':
            geometry = self._build_polygon(name, resolved_spec)
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

    def _require_positive(self, name: str, primitive_label: str, **dims: Any) -> None:
        """
        Validate that each named dimension is a positive, finite number.

        Several primitives (box/cylinder/sphere/cone/torus) hand dimensions
        straight to the OCCT kernel, which raises an opaque, message-less
        `Standard_DomainError` on zero/negative input instead of a usable
        error. Catching it here produces a typed `PartsBuilderError` that
        actually names the offending parameter and value.

        Raises:
            PartsBuilderError: If any dimension is not a positive number.
        """
        for dim_name, value in dims.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise PartsBuilderError(
                    f"{primitive_label} '{name}' has invalid {dim_name}: {value!r} "
                    f"(must be a positive number)",
                    part_name=name
                )

    def _place_by_origin(self, name: str, label: str, shape: Any, origin: Any,
                         half_extents: tuple, point_reference: tuple,
                         default: str = 'center', base_offset: Optional[tuple] = None) -> Any:
        """
        Place a primitive according to its `origin:` value.

        Every primitive is built centered on (0, 0, 0) (polygon aside, see
        `_build_polygon`) and then moved so that a named reference point of its
        bounding box lands at the world origin. One vocabulary for all of them:

          center  -- bounding-box center at (0, 0, 0)
          base    -- bottom-center (middle of the z-min face) at (0, 0, 0)
          corner  -- bounding-box min corner at (0, 0, 0)
          [x,y,z] -- `point_reference` (box: min corner; cylinder/cone: bottom-center;
                     sphere/torus: center) at that world point. This generalizes the
                     primitive's own named mode instead of translating the centered shape
                     (confirmed against `examples/thingiverse_rebuilds/thing38359_wedge.yaml`,
                     KNOWN_LIMITATIONS.md #17).

        Anything else raises: an unknown or misspelled `origin` used to fall through
        to "centered" with no message.

        Args:
            half_extents: (hx, hy, hz) of the centered shape's bounding box
            point_reference: offset added to a literal `[x, y, z]` origin
            default: mode used when `origin` is absent (polygon is `base`)
            base_offset: shift that puts the base face at the origin; (0, 0, hz) unless
                the primitive's `axis:` points elsewhere
        """
        if origin is None:
            origin = default
        hx, hy, hz = half_extents
        if isinstance(origin, str):
            offsets = {'center': (0, 0, 0), 'base': base_offset or (0, 0, hz), 'corner': (hx, hy, hz)}
            if origin not in offsets:
                suggestion = difflib.get_close_matches(origin, offsets, n=1)
                hint = f" Did you mean '{suggestion[0]}'?" if suggestion else ""
                raise PartsBuilderError(
                    f"{label} '{name}' has unknown origin {origin!r}. Use 'center' "
                    f"(bounding-box center at 0,0,0), 'base' (bottom-center at 0,0,0), "
                    f"'corner' (min corner at 0,0,0) or [x, y, z].{hint}",
                    part_name=name
                )
            offset = offsets[origin]
        elif (isinstance(origin, (list, tuple)) and len(origin) == 3
              and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in origin)):
            offset = tuple(float(v) + r for v, r in zip(origin, point_reference))
        else:
            raise PartsBuilderError(
                f"{label} '{name}' has invalid origin {origin!r}. Use 'center', 'base', "
                f"'corner' or three numbers [x, y, z].",
                part_name=name
            )
        if tuple(float(v) for v in offset) == (0.0, 0.0, 0.0):
            return shape
        return self.backend.translate(shape, offset)

    def _build_box(self, name: str, spec: Dict[str, Any]) -> Any:
        """
        Build a box primitive.

        Args:
            name: Part name (for error messages)
            spec: Specification with `size: [x, y, z]` (extents along X, Y, Z in
                mm; a single number is a cube)

        Returns:
            CadQuery Workplane with box geometry

        Raises:
            PartsBuilderError: If size is missing, malformed or not positive
        """
        origin = spec.get('origin', 'center')
        x, y, z = self._box_size(name, spec)

        box = self.backend.create_box(x, y, z)
        return self._place_by_origin(name, 'Box', box, origin,
                                     (x / 2, y / 2, z / 2), (x / 2, y / 2, z / 2))

    def _box_size(self, name: str, spec: Dict[str, Any]) -> tuple:
        """Validate a box's `size:` and return (x, y, z) in mm."""
        legacy = [k for k in ('width', 'depth', 'height')
                  if k in spec or k in (spec.get('parameters') or {})]
        if legacy:
            raise PartsBuilderError(
                f"Box '{name}' uses {', '.join(legacy)}, which boxes no longer take; "
                f"write `size: [x, y, z]` (extents along X, Y, Z in mm; "
                f"width -> x, depth -> y, height -> z)",
                part_name=name
            )
        if 'size' not in spec:
            raise PartsBuilderError(
                f"Box '{name}' needs a size: write `size: [x, y, z]` "
                f"(extents along X, Y, Z in mm; a single number is a cube)",
                part_name=name
            )

        size = spec['size']
        if isinstance(size, (int, float, str)) and not isinstance(size, bool):
            size = [size, size, size]
        if not isinstance(size, (list, tuple)):
            raise PartsBuilderError(
                f"Box '{name}' has invalid size {size!r}: expected [x, y, z] "
                f"(or a single number for a cube)",
                part_name=name
            )
        if len(size) != 3:
            raise PartsBuilderError(
                f"Box '{name}' has invalid size {list(size)!r}: expected exactly 3 values [x, y, z], "
                f"got {len(size)}",
                part_name=name
            )

        values = tuple(parse_length(v) for v in size)
        for value in values:
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise PartsBuilderError(
                    f"Box '{name}' has invalid size {list(size)!r}: every value must be a "
                    f"positive number (got {value!r})",
                    part_name=name
                )
        return values

    # Cylinder, cone and polygon are built along Z and then turned onto `axis:`.
    # (rotation axis direction, angle in degrees) that carries +Z onto each axis.
    _AXIS_TURNS = {'X': ((0, 1, 0), 90), 'Y': ((1, 0, 0), -90)}

    def _axis_param(self, name: str, label: str, params: Dict[str, Any]) -> str:
        """Read and validate `axis:` (X, Y or Z, default Z)."""
        axis = params.get('axis', 'Z')
        if not isinstance(axis, str) or axis.upper() not in ('X', 'Y', 'Z'):
            raise PartsBuilderError(
                f"{label} '{name}' has invalid axis {axis!r}. Use X, Y or Z.",
                part_name=name
            )
        return axis.upper()

    def _length_param(self, name: str, label: str, params: Dict[str, Any]) -> Any:
        """
        Read the extent along the primitive's axis: `length`, or the deprecated
        `height`. Returns None when neither is given.
        """
        if 'length' in params and 'height' in params:
            raise PartsBuilderError(
                f"{label} '{name}' has both 'length' and 'height'; they mean the same "
                f"thing. Keep 'length'.",
                part_name=name
            )
        if 'height' in params:
            warnings.warn(
                f"{label} '{name}': 'height' is deprecated; use 'length' (the extent "
                f"along 'axis', default Z).",
                DeprecationWarning,
                stacklevel=3,
            )
            return params['height']
        return params.get('length')

    def _turn_to_axis(self, shape: Any, axis: str) -> Any:
        """Rotate a shape built along Z about the world origin so it lies along `axis`."""
        if axis == 'Z':
            return shape
        direction, angle = self._AXIS_TURNS[axis]
        return self.backend.rotate(shape, (0, 0, 0), direction, angle)

    @staticmethod
    def _axis_frame(axis: str, radius: float, half_length: float) -> tuple:
        """(half extents, base offset) of a centered round primitive lying along `axis`."""
        return {
            'X': ((half_length, radius, radius), (half_length, 0, 0)),
            'Y': ((radius, half_length, radius), (0, half_length, 0)),
            'Z': ((radius, radius, half_length), (0, 0, half_length)),
        }[axis]

    def _build_cylinder(self, name: str, spec: Dict[str, Any]) -> Any:
        """
        Build a cylinder primitive.

        Args:
            name: Part name
            spec: Specification with 'parameters' containing radius, length
                (extent along `axis`, default Z; `height` is a deprecated alias)

        Returns:
            CadQuery Workplane with cylinder geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        # Extract parameters (check 'parameters' key first, fall back to spec for backward compat)
        params = spec.get('parameters', spec)

        # Validate required parameters
        length = self._length_param(name, 'Cylinder', params)
        missing = [p for p in ('radius',) if p not in params] + (['length'] if length is None else [])
        if missing:
            raise PartsBuilderError(
                f"Cylinder '{name}' missing required parameters: {', '.join(missing)}",
                part_name=name
            )

        radius = params['radius']
        axis = self._axis_param(name, 'Cylinder', params)
        origin = spec.get('origin', 'center')

        self._require_positive(name, 'Cylinder', radius=radius, length=length)

        cylinder = self._turn_to_axis(self.backend.create_cylinder(radius, length), axis)
        half_extents, base_offset = self._axis_frame(axis, radius, length / 2)
        return self._place_by_origin(name, 'Cylinder', cylinder, origin,
                                     half_extents, base_offset, base_offset=base_offset)

    def _build_sphere(self, name: str, spec: Dict[str, Any]) -> Any:
        """
        Build a sphere primitive.

        Args:
            name: Part name
            spec: Specification with 'parameters' containing radius

        Returns:
            CadQuery Workplane with sphere geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        # Extract parameters (check 'parameters' key first, fall back to spec for backward compat)
        params = spec.get('parameters', spec)

        if 'radius' not in params:
            raise PartsBuilderError(
                f"Sphere '{name}' missing required parameter: radius",
                part_name=name
            )

        radius = params['radius']
        origin = spec.get('origin', 'center')

        self._require_positive(name, 'Sphere', radius=radius)

        sphere = self.backend.create_sphere(radius)
        return self._place_by_origin(name, 'Sphere', sphere, origin,
                                     (radius, radius, radius), (0, 0, 0))

    def _build_cone(self, name: str, spec: Dict[str, Any]) -> Any:
        """
        Build a cone/frustum primitive.

        Args:
            name: Part name
            spec: Specification with 'parameters' containing radius1, radius2, length
                (extent along `axis`, default Z; `height` is a deprecated alias).
                radius1 is the base end, radius2 the far end.

        Returns:
            CadQuery Workplane with cone geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        # Extract parameters (check 'parameters' key first, fall back to spec for backward compat)
        params = spec.get('parameters', spec)

        # Backward compatibility: deprecated radius_bottom/radius_top → radius1/radius2
        if 'radius_bottom' in params or 'radius_top' in params:
            warnings.warn(
                f"Cone '{name}': 'radius_bottom'/'radius_top' are deprecated; "
                f"use 'radius1' (base) and 'radius2' (top) instead. "
                f"See docs/developer/MIGRATION_GUIDE_V3.md.",
                DeprecationWarning,
                stacklevel=2,
            )
            params = dict(params)  # don't mutate the caller's spec
            if 'radius_bottom' in params:
                params.setdefault('radius1', params['radius_bottom'])
            if 'radius_top' in params:
                params.setdefault('radius2', params['radius_top'])

        # Validate required parameters
        length = self._length_param(name, 'Cone', params)
        missing = [p for p in ('radius1', 'radius2') if p not in params] + (['length'] if length is None else [])
        if missing:
            raise PartsBuilderError(
                f"Cone '{name}' missing required parameters: {', '.join(missing)}",
                part_name=name
            )

        radius1 = params['radius1']  # Base radius
        radius2 = params['radius2']  # Top radius
        axis = self._axis_param(name, 'Cone', params)
        origin = spec.get('origin', 'center')

        # radius1/radius2 may each be 0 (a true cone apex) but not negative,
        # and not both zero (that's a degenerate line, not a solid); height
        # must be strictly positive. See _require_positive's docstring for
        # why this is checked here rather than left to the OCCT kernel.
        for r_name, r_val in (('radius1', radius1), ('radius2', radius2)):
            if not isinstance(r_val, (int, float)) or isinstance(r_val, bool) or r_val < 0:
                raise PartsBuilderError(
                    f"Cone '{name}' has invalid {r_name}: {r_val!r} (must be >= 0)",
                    part_name=name
                )
        if radius1 == 0 and radius2 == 0:
            raise PartsBuilderError(
                f"Cone '{name}' has both radius1 and radius2 equal to 0 "
                f"(degenerate — not a solid)",
                part_name=name
            )
        self._require_positive(name, 'Cone', length=length)

        cone = self._turn_to_axis(self.backend.create_cone(radius1, radius2, length), axis)
        half_extents, base_offset = self._axis_frame(axis, max(radius1, radius2), length / 2)
        return self._place_by_origin(name, 'Cone', cone, origin,
                                     half_extents, base_offset, base_offset=base_offset)

    def _build_torus(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a torus primitive.

        Args:
            name: Part name
            spec: Specification with 'parameters' containing major_radius, minor_radius

        Returns:
            CadQuery Workplane with torus geometry

        Raises:
            PartsBuilderError: If required parameters missing
        """
        # Extract parameters (check 'parameters' key first, fall back to spec for backward compat)
        params = spec.get('parameters', spec)

        # Validate required parameters
        required = ['major_radius', 'minor_radius']
        missing = [p for p in required if p not in params]
        if missing:
            raise PartsBuilderError(
                f"Torus '{name}' missing required parameters: {', '.join(missing)}",
                part_name=name
            )

        self._require_cadquery_backend(name, 'torus')

        major_radius = params['major_radius']  # Distance from center to tube center
        minor_radius = params['minor_radius']  # Tube radius

        self._require_positive(name, 'Torus', major_radius=major_radius, minor_radius=minor_radius)
        if minor_radius >= major_radius:
            raise PartsBuilderError(
                f"Torus '{name}' has minor_radius ({minor_radius}) >= major_radius "
                f"({major_radius}) — the tube would self-intersect at the center",
                part_name=name
            )

        # Build the torus via the kernel's direct makeTorus primitive rather than
        # revolving a profile. The old `Workplane("XZ").center(R,0).circle(r)
        # .revolve(360, (0,0,0), (0,0,1))` idiom silently produced a *zero-volume*
        # degenerate solid on the OCP 7.9 / CadQuery 2.8 kernel (the revolve axis
        # lay in the profile plane) — the only torus test asserted `is not None`,
        # so it went unnoticed. makeTorus is exact and orientation-stable: the
        # donut lies flat on XY with its hole along +Z (bbox
        # 2(R+r) x 2(R+r) x 2r), the orientation the revolve was meant to produce.
        torus_solid = cq.Solid.makeTorus(major_radius, minor_radius)
        torus = cq.Workplane("XY").newObject([torus_solid])
        origin = spec.get('origin', 'center')
        reach = major_radius + minor_radius
        return self._place_by_origin(name, 'Torus', torus, origin,
                                     (reach, reach, minor_radius), (0, 0, 0))

    def _build_polygon(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """
        Build a regular polygon extruded into a prism.

        YAML parameters:
          sides:      number of sides (integer ≥ 3, required)
          diameter:   circumscribed circle diameter in mm (required)
          length:     extent along `axis` in mm (required; `height` is a deprecated alias)
          axis:       X, Y or Z (default Z); the prism's base sits on the plane through the origin
          circumscribed: true (default) = diameter is outer circle;
                         false = diameter is inner (inscribed) circle

        Examples:
          Hexagonal nut blank:
            primitive: polygon
            parameters: {sides: 6, diameter: 8, length: 4}

          Square post:
            primitive: polygon
            parameters: {sides: 4, diameter: 20, length: 50}
        """
        params = spec.get('parameters', spec)

        height = self._length_param(name, 'Polygon', params)
        missing = [p for p in ('sides', 'diameter') if p not in params] + (['length'] if height is None else [])
        if missing:
            raise PartsBuilderError(
                f"Polygon '{name}' missing required parameters: {', '.join(missing)}",
                part_name=name
            )

        self._require_cadquery_backend(name, 'polygon')

        sides = int(params['sides'])
        diameter = float(params['diameter'])
        height = float(height)
        axis = self._axis_param(name, 'Polygon', params)
        circumscribed = params.get('circumscribed', True)

        if sides < 3:
            raise PartsBuilderError(
                f"Polygon '{name}' must have at least 3 sides, got {sides}",
                part_name=name
            )
        if diameter <= 0:
            raise PartsBuilderError(
                f"Polygon '{name}' diameter must be positive, got {diameter}",
                part_name=name
            )
        if height <= 0:
            raise PartsBuilderError(
                f"Polygon '{name}' length must be positive, got {height}",
                part_name=name
            )

        # CadQuery's own `circumscribed` flag is inverted relative to this docstring's
        # (and conventional geometric) meaning: cq.Workplane.polygon(circumscribed=True)
        # puts the *given* diameter circle INSIDE the polygon (diameter = across-flats)
        # and circumscribed=False puts vertices ON the circle (diameter = tip-to-tip).
        # Invert here so TiaCAD's own contract — circumscribed: true = diameter is the
        # outer/tip-to-tip circle — actually holds. (Confirmed 2026-07-10: without this,
        # every stdlib hex nut (M3-M6) built ~15% oversized across-flats.)
        polygon = (
            cq.Workplane("XY")
            .polygon(sides, diameter, circumscribed=not circumscribed)
            .extrude(height)
        )
        # Built with its base face on the origin plane, so the reference for a literal
        # [x, y, z] is (0, 0, 0) and the centered shape's offsets are measured from the
        # base, not the middle.
        polygon = self._turn_to_axis(polygon, axis)
        bb = polygon.val().BoundingBox()
        along = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis]
        offsets = {'base': (0, 0, 0), 'center': tuple(-height / 2 * a for a in along),
                   'corner': (-bb.xmin, -bb.ymin, -bb.zmin)}
        origin = spec.get('origin', 'base')
        if isinstance(origin, str) and origin in offsets:
            offset = offsets[origin]
            return polygon if offset == (0, 0, 0) else self.backend.translate(polygon, offset)
        # unknown / [x, y, z]: reuse the shared validation and list handling
        return self._place_by_origin(name, 'Polygon', polygon, origin, (0, 0, 0), (0, 0, 0))

    _TEXT_VALID_STYLES = ['regular', 'bold', 'italic', 'bold-italic']
    _TEXT_VALID_HALIGN = ['left', 'center', 'right']
    _TEXT_VALID_VALIGN = ['top', 'center', 'baseline', 'bottom']

    def _validate_text_spec(self, name: str, spec: Dict[str, Any]) -> None:
        """Validate text primitive spec, raising PartsBuilderError on failure."""
        _req_labels = {'text': 'text', 'size': 'font size', 'height': 'extrusion height'}
        for req, label in _req_labels.items():
            if req not in spec:
                raise PartsBuilderError(
                    f"Text primitive '{name}' missing required '{req}' parameter ({label})",
                    part_name=name
                )
        text, size, height = spec['text'], spec['size'], spec['height']
        if not text or (isinstance(text, str) and not text.strip()):
            raise PartsBuilderError(f"Text primitive '{name}' has empty text string", part_name=name)
        if size <= 0:
            raise PartsBuilderError(f"Text primitive '{name}' size must be positive, got {size}", part_name=name)
        if height <= 0:
            raise PartsBuilderError(f"Text primitive '{name}' height must be positive, got {height}", part_name=name)
        if size < 1.0:
            logger.warning(f"Text primitive '{name}' has very small size {size}mm. Text may not render well. Consider size >= 1mm.")
        style = spec.get('style', 'regular')
        if style not in self._TEXT_VALID_STYLES:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid style '{style}'. Must be one of: {', '.join(self._TEXT_VALID_STYLES)}",
                part_name=name
            )
        halign = spec.get('halign', 'center')
        if halign not in self._TEXT_VALID_HALIGN:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid horizontal alignment '{halign}'. Must be one of: {', '.join(self._TEXT_VALID_HALIGN)}",
                part_name=name
            )
        valign = spec.get('valign', 'center')
        if valign not in self._TEXT_VALID_VALIGN:
            raise PartsBuilderError(
                f"Text primitive '{name}' has invalid vertical alignment '{valign}'. Must be one of: {', '.join(self._TEXT_VALID_VALIGN)}",
                part_name=name
            )
        spacing = spec.get('spacing', 1.0)
        if spacing <= 0:
            raise PartsBuilderError(f"Text primitive '{name}' spacing must be positive, got {spacing}", part_name=name)

    def _build_text(self, name: str, spec: Dict[str, Any]) -> cq.Workplane:
        """Build a 3D text primitive."""
        self._require_cadquery_backend(name, 'text')
        self._validate_text_spec(name, spec)
        text, size, height = spec['text'], spec['size'], spec['height']
        font = spec.get('font', 'Liberation Sans')
        style = spec.get('style', 'regular')
        halign = spec.get('halign', 'center')
        valign = spec.get('valign', 'center')
        font_path = spec.get('font_path', None)
        cq_kind = 'bold' if style == 'bold-italic' else style
        try:
            text_wp = cq.Workplane("XY").text(
                text, fontsize=size, distance=height,
                font=font, fontPath=font_path, kind=cq_kind,
                halign=halign, valign=valign
            )
            logger.debug(f"Built text primitive '{name}': text='{text}', size={size}, height={height}, font='{font}', style='{style}'")
            return text_wp
        except Exception as e:
            error_msg = str(e)
            if 'font' in error_msg.lower() or 'freetype' in error_msg.lower():
                raise PartsBuilderError(
                    f"Font error in text primitive '{name}': {error_msg}. "
                    f"Font '{font}' may not be available. Try 'Liberation Sans', 'Arial', or specify 'font_path' parameter.",
                    part_name=name
                )
            raise PartsBuilderError(f"Error creating text primitive '{name}': {error_msg}", part_name=name)

    def _require_cadquery_backend(self, name: str, primitive_type: str) -> None:
        """Fail clearly for primitives that still depend on CadQuery APIs."""
        if isinstance(self.backend, CadQueryBackend):
            return
        raise PartsBuilderError(
            f"Primitive '{primitive_type}' for part '{name}' still requires CadQueryBackend. "
            f"Supported through GeometryBackend today: box, cylinder, sphere, cone.",
            part_name=name,
        )

    def __repr__(self) -> str:
        return f"PartsBuilder(resolver={self.resolver})"
