"""
Appearance Builder - Handles color/material/appearance metadata for parts

Extracts appearance-related parsing logic from PartsBuilder to maintain
separation of concerns.
"""

import logging
from typing import Dict, Any, Optional

from .color_parser import ColorParser, ColorParseError

logger = logging.getLogger(__name__)


class AppearanceBuilder:
    """
    Builds appearance metadata (color, material, PBR properties) for parts.

    Separates appearance concerns from geometry building.
    """

    def __init__(self, color_parser: ColorParser):
        """
        Initialize appearance builder.

        Args:
            color_parser: ColorParser instance for parsing colors
        """
        self.color_parser = color_parser

    def build_appearance_metadata(
        self,
        spec: Dict[str, Any],
        part_name: str
    ) -> Dict[str, Any]:
        """
        Parse all appearance-related fields from part spec.

        Priority order (later overrides earlier):
        1. material (provides color + properties)
        2. color (just color)
        3. appearance (color + properties, most specific)

        Args:
            spec: Part specification dict (resolved parameters)
            part_name: Part name for error messages

        Returns:
            Metadata dict with optional keys:
            - 'color': RGBA tuple (r, g, b, a) in 0-1 range
            - 'material': Material name string
            - 'material_properties': Dict with finish, metalness, roughness, opacity

        Examples:
            >>> builder.build_appearance_metadata({'color': 'red'}, 'box1')
            {'color': (1.0, 0.0, 0.0, 1.0)}

            >>> builder.build_appearance_metadata({'material': 'aluminum'}, 'plate')
            {'material': 'aluminum', 'color': (0.75, 0.75, 0.75, 1.0), ...}
        """
        metadata = {}

        # Priority 1: Material (base color + properties)
        self._parse_material(spec, metadata, part_name)

        # Priority 2: Color (overrides material color)
        self._parse_color(spec, metadata, part_name)

        # Priority 3: Appearance (most specific, overrides all)
        self._parse_appearance(spec, metadata, part_name)

        return metadata

    def _parse_color(
        self,
        spec: Dict[str, Any],
        metadata: Dict[str, Any],
        part_name: str
    ) -> None:
        """
        Parse simple 'color' field.

        Modifies metadata in-place.
        """
        if 'color' not in spec:
            return

        try:
            color = self.color_parser.parse(spec['color'])
            metadata['color'] = color.to_rgba()
            logger.debug(f"Part '{part_name}' color: {color.to_hex()}")

        except ColorParseError as e:
            # Non-fatal: log warning but continue
            logger.warning(
                f"Failed to parse color for part '{part_name}': {e}"
            )

    def _parse_material(
        self,
        spec: Dict[str, Any],
        metadata: Dict[str, Any],
        part_name: str
    ) -> None:
        """
        Parse 'material' field from material library.

        Provides both color and PBR properties.
        Modifies metadata in-place.
        """
        if 'material' not in spec:
            return

        material_name = spec['material']

        try:
            # Get material from library
            material = self.color_parser.material_library.get(material_name)

            # Store material reference
            metadata['material'] = material_name

            # Extract color (RGBA)
            metadata['color'] = (*material.color, 1.0)

            # Extract PBR properties
            metadata['material_properties'] = {
                'finish': material.finish,
                'metalness': material.metalness,
                'roughness': material.roughness,
                'opacity': material.opacity,
            }

            logger.debug(f"Part '{part_name}' material: {material_name}")

        except ValueError as e:
            # Material not found
            logger.warning(
                f"Unknown material '{material_name}' for part '{part_name}': {e}"
            )

    def _parse_appearance(
        self,
        spec: Dict[str, Any],
        metadata: Dict[str, Any],
        part_name: str
    ) -> None:
        """
        Parse full 'appearance' specification.

        Supports:
        - color: Any color format
        - finish: matte, satin, glossy, metallic, etc.
        - metalness: 0-1
        - roughness: 0-1
        - opacity: 0-1

        Modifies metadata in-place.
        """
        if 'appearance' not in spec:
            return

        appearance = spec['appearance']

        # Parse color if present
        if 'color' in appearance:
            try:
                color = self.color_parser.parse(appearance['color'])
                metadata['color'] = color.to_rgba()

            except ColorParseError as e:
                logger.warning(
                    f"Failed to parse appearance color for part '{part_name}': {e}"
                )

        # Copy PBR properties
        pbr_properties = ['finish', 'metalness', 'roughness', 'opacity']
        for prop in pbr_properties:
            if prop in appearance:
                # Initialize material_properties if needed
                if 'material_properties' not in metadata:
                    metadata['material_properties'] = {}

                metadata['material_properties'][prop] = appearance[prop]

        if metadata.get('material_properties'):
            logger.debug(
                f"Part '{part_name}' appearance override: "
                f"{list(metadata['material_properties'].keys())}"
            )
