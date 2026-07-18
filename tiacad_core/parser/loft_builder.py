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
from .backend_utils import get_cadquery_backend

if TYPE_CHECKING:
    from .yaml_with_lines import LineTracker
    from ..geometry import GeometryBackend

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
                 line_tracker: Optional['LineTracker'] = None,
                 backend: Optional["GeometryBackend"] = None):
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
        self.backend = backend

    def _get_line_info(self, path: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get line and column info for a YAML path."""
        if self.line_tracker:
            line, col = self.line_tracker.get(path)
            return (line, col)
        return (None, None)

    def _validate_loft_spec(self, name: str, spec: Dict[str, Any]):
        """Validate loft spec. Returns (profiles, profile_names, ruled)."""
        def _err(field, msg, idx=None):
            path = ['operations', name, field] + ([idx] if idx is not None else [])
            line, col = self._get_line_info(path)
            raise LoftBuilderError(msg, operation_name=name, line=line, column=col)

        profile_names = spec.get('profiles')
        if not profile_names:
            _err('profiles', f"Loft operation '{name}' missing required 'profiles' field")
        if not isinstance(profile_names, list):
            _err('profiles', f"Loft profiles must be a list, got {type(profile_names).__name__}")
        if len(profile_names) < 2:
            _err('profiles', f"Loft operation '{name}' requires at least 2 profiles, got {len(profile_names)}")

        profiles = []
        for i, profile_name in enumerate(profile_names):
            if profile_name not in self.sketches:
                available = ', '.join(self.sketches.keys())
                _err('profiles', f"Profile sketch '{profile_name}' not found for loft operation '{name}'. "
                     f"Available sketches: {available}", idx=i)
            profiles.append(self.sketches[profile_name])

        ruled = spec.get('ruled', False)
        if not isinstance(ruled, bool):
            _err('ruled', f"Loft 'ruled' must be boolean, got {ruled}")

        return profiles, profile_names, ruled

    def execute_loft_operation(self, name: str, spec: Dict[str, Any]):
        """
        Execute a loft operation — creates 3D geometry by blending between multiple 2D sketch profiles.

        Args:
            name: Result part name
            spec: Loft spec (profiles required ≥2; ruled optional)

        Raises:
            LoftBuilderError: If operation fails
        """
        try:
            resolved_spec = self.resolver.resolve(spec)
            profiles, profile_names, ruled = self._validate_loft_spec(name, resolved_spec)

            logger.info(f"Lofting between {len(profiles)} profiles: {', '.join(profile_names)}")
            geometry = self._loft_sketches(profiles, ruled, name)
            self.registry.add(Part(name=name, geometry=geometry, metadata={
                'source': 'loft', 'profiles': profile_names, 'operation_type': 'loft', 'ruled': ruled
            }, backend=self.backend or get_cadquery_backend()))
            logger.debug(f"Created lofted part '{name}' from {len(profiles)} profiles")

        except LoftBuilderError:
            raise
        except Exception as e:
            line, col = self._get_line_info(['operations', name])
            raise LoftBuilderError(f"Failed to execute loft operation '{name}': {str(e)}",
                                    operation_name=name, line=line, column=col) from e

    def _get_plane_axes(self, base_plane: str, context: str):
        """Return (offset_idx, in_plane_idx) for the given plane. Raises on unsupported plane."""
        plane_axes = {'XY': (2, (0, 1)), 'XZ': (1, (0, 2)), 'YZ': (0, (1, 2))}
        if base_plane not in plane_axes:
            raise LoftBuilderError(f"Unsupported plane '{base_plane}'. Must be XY, XZ, or YZ",
                                    operation_name=context)
        return plane_axes[base_plane]

    def _position_profile_workplane(self, result_wp, profile, i: int,
                                    in_plane_idx, offset_idx, base_offset):
        """Create a positioned workplane for a loft profile. Returns (profile_wp, base_offset)."""
        in_plane_pos = (profile.origin[in_plane_idx[0]], profile.origin[in_plane_idx[1]])
        if i == 0:
            profile_wp = result_wp
            base_offset = profile.origin[offset_idx]
        else:
            profile_wp = result_wp.workplane(offset=profile.origin[offset_idx] - base_offset)
        if in_plane_pos != (0, 0):
            profile_wp = profile_wp.center(*in_plane_pos)
        return profile_wp, base_offset

    def _loft_sketches(self, profiles: List[Sketch2D], ruled: bool,
                       context: str) -> cq.Workplane:
        """Loft between multiple sketch profiles. All profiles must share the same base plane."""
        try:
            base_plane = profiles[0].plane
            if any(p.plane != base_plane for p in profiles):
                raise LoftBuilderError(
                    f"All profiles must use the same base plane. Found: {set(p.plane for p in profiles)}",
                    operation_name=context
                )

            offset_idx, in_plane_idx = self._get_plane_axes(base_plane, context)
            result_wp = cq.Workplane(base_plane)
            base_offset = 0.0

            for i, profile in enumerate(profiles):
                subtract_shapes = [s for s in profile.shapes if s.operation == 'subtract']
                if subtract_shapes:
                    logger.warning(f"Loft does not support subtract operations in profile '{profile.name}'. "
                                   f"Subtract shapes will be ignored.")

                add_shapes = [s for s in profile.shapes if s.operation == 'add']
                if not add_shapes:
                    raise LoftBuilderError(f"Profile '{profile.name}' has no additive shapes",
                                           operation_name=context)
                if len(add_shapes) > 1:
                    logger.warning(f"Profile '{profile.name}' has {len(add_shapes)} shapes. "
                                   f"Only first shape will be used for loft. "
                                   f"Consider creating a single combined shape.")

                profile_wp, base_offset = self._position_profile_workplane(
                    result_wp, profile, i, in_plane_idx, offset_idx, base_offset
                )
                result_wp = add_shapes[0].build(profile_wp)

            result = result_wp.loft(ruled=ruled)
            logger.debug(f"Lofted {len(profiles)} profiles ({'ruled' if ruled else 'smooth'})")
            return result

        except LoftBuilderError:
            raise
        except Exception as e:
            raise LoftBuilderError(f"Failed to loft profiles: {str(e)}", operation_name=context) from e

    def __repr__(self) -> str:
        return (
            f"LoftBuilder(parts={len(self.registry)}, "
            f"sketches={len(self.sketches)})"
        )
