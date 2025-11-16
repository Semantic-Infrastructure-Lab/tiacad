"""
LoftBuilder - Execute loft operations on 2D sketches

Creates 3D geometry by blending between multiple 2D sketch profiles.
Useful for creating organic shapes and smooth transitions.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import cadquery as cq

from ..part import Part, PartRegistry
from ..sketch import Sketch2D
from ..utils.exceptions import TiaCADError
from .parameter_resolver import ParameterResolver

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)


class LoftBuilderError(TiaCADError):
    """Error during loft operation"""
    def __init__(self, message: str, operation_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class LoftBuilder:
    """
    Builds 3D geometry by lofting between multiple 2D sketches.

    Loft creates smooth transitions between different cross-section profiles,
    useful for organic shapes and complex transitions.

    Usage:
        builder = LoftBuilder(registry, sketches, resolver, line_tracker)
        builder.execute_loft_operation('wing', {
            'profiles': ['root_profile', 'tip_profile'],
            'ruled': False
        })
    """

    def __init__(self,
                 part_registry: PartRegistry,
                 sketches: Dict[str, Sketch2D],
                 parameter_resolver: ParameterResolver,
                 line_tracker: Optional['LineTracker'] = None):
        """
        Initialize loft builder.

        Args:
            part_registry: Registry to add lofted parts to
            sketches: Dictionary of available sketches (name → Sketch2D)
            parameter_resolver: Resolver for ${...} parameter expressions
            line_tracker: Optional line tracker for enhanced error messages
        """
        self.registry = part_registry
        self.sketches = sketches
        self.resolver = parameter_resolver
        self.line_tracker = line_tracker

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get line and column info for a YAML path."""
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def execute_loft_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a loft operation.

        Creates a 3D part by blending between multiple 2D sketch profiles.

        Args:
            name: Result part name
            spec: Loft specification with:
                - profiles: List of sketch names to loft between (required, ≥2)
                - ruled: Use ruled surface (straight lines) vs smooth (default: False)

        Raises:
            LoftBuilderError: If operation fails
        """
        try:
            # Resolve parameters
            resolved_spec = self.resolver.resolve(spec)

            # Validate and get profile sketches
            profile_names = resolved_spec.get('profiles')
            if not profile_names:
                line, col = self._get_line_info(['operations', name, 'profiles'])
                raise LoftBuilderError(
                    f"Loft operation '{name}' missing required 'profiles' field",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if not isinstance(profile_names, list):
                line, col = self._get_line_info(['operations', name, 'profiles'])
                raise LoftBuilderError(
                    f"Loft profiles must be a list, got {type(profile_names).__name__}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            if len(profile_names) < 2:
                line, col = self._get_line_info(['operations', name, 'profiles'])
                raise LoftBuilderError(
                    f"Loft operation '{name}' requires at least 2 profiles, got {len(profile_names)}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Validate all profiles exist
            profiles = []
            for i, profile_name in enumerate(profile_names):
                if profile_name not in self.sketches:
                    line, col = self._get_line_info(['operations', name, 'profiles', i])
                    available = ', '.join(self.sketches.keys())
                    raise LoftBuilderError(
                        f"Profile sketch '{profile_name}' not found for loft operation '{name}'. "
                        f"Available sketches: {available}",
                        operation_name=name,
                        line=line,
                        column=col
                    )
                profiles.append(self.sketches[profile_name])

            # Get ruled option (default False for smooth loft)
            ruled = resolved_spec.get('ruled', False)
            if not isinstance(ruled, bool):
                line, col = self._get_line_info(['operations', name, 'ruled'])
                raise LoftBuilderError(
                    f"Loft 'ruled' must be boolean, got {ruled}",
                    operation_name=name,
                    line=line,
                    column=col
                )

            # Build geometry
            logger.info(
                f"Lofting between {len(profiles)} profiles: {', '.join(profile_names)}"
            )

            geometry = self._loft_sketches(profiles, ruled, name)

            # Create part
            part = Part(
                name=name,
                geometry=geometry,
                metadata={
                    'source': 'loft',
                    'profiles': profile_names,
                    'operation_type': 'loft',
                    'ruled': ruled
                }
            )

            # Add to registry
            self.registry.add(part)
            logger.debug(f"Created lofted part '{name}' from {len(profiles)} profiles")

        except LoftBuilderError:
            # Re-raise LoftBuilderError as-is
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise LoftBuilderError(
                f"Failed to execute loft operation '{name}': {str(e)}",
                operation_name=name,
                line=line,
                column=col
            ) from e

    def _loft_sketches(self, profiles: List[Sketch2D], ruled: bool,
                      context: str) -> cq.Workplane:
        """
        Loft between multiple sketch profiles.

        Args:
            profiles: List of Sketch2D profiles to loft between
            ruled: Use ruled surface (straight) vs smooth blending
            context: Operation name for error messages

        Returns:
            CadQuery Workplane with lofted 3D geometry

        Raises:
            LoftBuilderError: If loft fails
        """
        try:
            # CadQuery's loft requires all profiles to be built on the same workplane
            # using .workplane(offset=...) to position them along the plane's normal

            # Start with base workplane and validate all profiles use same plane
            base_plane = profiles[0].plane
            if any(p.plane != base_plane for p in profiles):
                raise LoftBuilderError(
                    f"All profiles must use the same base plane. Found: {set(p.plane for p in profiles)}",
                    operation_name=context
                )

            result_wp = cq.Workplane(base_plane)

            # Determine offset direction and in-plane coordinates based on base plane
            # XY plane: offset in Z direction, in-plane is X,Y
            # XZ plane: offset in Y direction, in-plane is X,Z
            # YZ plane: offset in X direction, in-plane is Y,Z
            if base_plane == 'XY':
                offset_idx = 2  # Z
                in_plane_idx = (0, 1)  # X, Y
            elif base_plane == 'XZ':
                offset_idx = 1  # Y
                in_plane_idx = (0, 2)  # X, Z
            elif base_plane == 'YZ':
                offset_idx = 0  # X
                in_plane_idx = (1, 2)  # Y, Z
            else:
                raise LoftBuilderError(
                    f"Unsupported plane '{base_plane}'. Must be XY, XZ, or YZ",
                    operation_name=context
                )

            # Build each profile on the combined workplane
            for i, profile in enumerate(profiles):
                # Check for subtract shapes (not supported in loft)
                subtract_shapes = [s for s in profile.shapes if s.operation == 'subtract']
                if subtract_shapes:
                    logger.warning(
                        f"Loft does not support subtract operations in profile '{profile.name}'. "
                        f"Subtract shapes will be ignored."
                    )

                # Get additive shapes
                add_shapes = [s for s in profile.shapes if s.operation == 'add']
                if not add_shapes:
                    raise LoftBuilderError(
                        f"Profile '{profile.name}' has no additive shapes",
                        operation_name=context
                    )

                # For first profile, use base workplane
                # For subsequent profiles, create offset workplane
                if i == 0:
                    # First profile - position at its origin
                    profile_wp = result_wp
                    if profile.origin != (0, 0, 0):
                        in_plane_pos = (profile.origin[in_plane_idx[0]], profile.origin[in_plane_idx[1]])
                        if in_plane_pos != (0, 0):
                            profile_wp = profile_wp.center(in_plane_pos[0], in_plane_pos[1])
                    base_offset = profile.origin[offset_idx]  # Store base offset for subsequent profiles
                else:
                    # Subsequent profiles - calculate offset from first profile along normal direction
                    offset = profile.origin[offset_idx] - base_offset
                    profile_wp = result_wp.workplane(offset=offset)

                    # Apply in-plane positioning if needed
                    in_plane_pos = (profile.origin[in_plane_idx[0]], profile.origin[in_plane_idx[1]])
                    if in_plane_pos != (0, 0):
                        profile_wp = profile_wp.center(in_plane_pos[0], in_plane_pos[1])

                # Build the first shape on this workplane
                profile_wp = add_shapes[0].build(profile_wp)

                # If multiple add shapes, warn (only first will be used)
                if len(add_shapes) > 1:
                    logger.warning(
                        f"Profile '{profile.name}' has {len(add_shapes)} shapes. "
                        f"Only first shape will be used for loft. "
                        f"Consider creating a single combined shape."
                    )

                # Update result workplane with this profile
                result_wp = profile_wp

            # Now loft all the wires together
            result = result_wp.loft(ruled=ruled)

            logger.debug(
                f"Lofted {len(profiles)} profiles "
                f"({'ruled' if ruled else 'smooth'})"
            )

            return result

        except Exception as e:
            raise LoftBuilderError(
                f"Failed to loft profiles: {str(e)}",
                operation_name=context
            ) from e

    def __repr__(self) -> str:
        return (
            f"LoftBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
