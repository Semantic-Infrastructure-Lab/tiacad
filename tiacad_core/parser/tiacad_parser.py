"""
TiaCADParser - Main entry point for parsing TiaCAD YAML files

Orchestrates the complete parsing pipeline:
1. Load and validate YAML
2. Resolve parameters
3. Build parts from primitives
4. Execute operations
5. Return executable document

Author: TIA
Version: 0.1.0-alpha
"""

import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from ..part import PartRegistry
from ..utils.exceptions import TiaCADError
from ..spatial_resolver import SpatialResolver
from .parameter_resolver import ParameterResolver
from .parts_builder import PartsBuilder
from .operations_builder import OperationsBuilder
from .color_parser import ColorParser
from .schema_validator import SchemaValidator
from .yaml_with_lines import parse_yaml_with_lines, LineTracker, format_error

logger = logging.getLogger(__name__)


class TiaCADParserError(TiaCADError):
    """Error during YAML parsing"""
    def __init__(self, message: str, **kwargs):
        # Pass all keyword arguments to parent TiaCADError
        super().__init__(message, **kwargs)


class TiaCADDocument:
    """
    Executable TiaCAD document.

    Represents a parsed and built TiaCAD model ready for export.

    Attributes:
        metadata: Document metadata
        parameters: Resolved parameters
        parts: Registry of all parts
        final_geometry: Final combined geometry (if applicable)
    """

    def __init__(self,
                 metadata: Dict[str, Any],
                 parameters: Dict[str, Any],
                 parts: PartRegistry,
                 operations: Optional[Dict[str, Any]] = None,
                 references: Optional[Dict[str, Any]] = None,
                 line_tracker: Optional[LineTracker] = None,
                 yaml_string: Optional[str] = None,
                 file_path: Optional[str] = None):
        """
        Initialize TiaCAD document.

        Args:
            metadata: Document metadata from YAML
            parameters: Resolved parameters
            parts: Registry with all parts (primitives + operations)
            operations: Optional operations spec for reference
            references: Optional spatial references dictionary (name -> spec)
            line_tracker: Optional YAML line tracker for error reporting
            yaml_string: Optional original YAML string for error context
            file_path: Optional file path for error messages
        """
        self.metadata = metadata
        self.parameters = parameters
        self.parts = parts
        self.operations = operations or {}
        self.references = references or {}
        self.line_tracker = line_tracker
        self.yaml_string = yaml_string
        self.file_path = file_path

    def get_part(self, name: str):
        """
        Get a part by name.

        Args:
            name: Part name

        Returns:
            Part object with CadQuery geometry

        Raises:
            KeyError: If part doesn't exist
        """
        return self.parts.get(name)

    def export_stl(self, output_path: str, part_name: Optional[str] = None):
        """
        Export part to STL file.

        Args:
            output_path: Path to output STL file
            part_name: Part to export (if None, exports the last operation result)

        Raises:
            TiaCADParserError: If export fails
        """
        # Determine which part to export
        if part_name is None:
            # Get last part from operations (convention: final result)
            if self.operations:
                part_name = list(self.operations.keys())[-1]
            else:
                # No operations, export first part
                part_name = self.parts.list_parts()[0]

        try:
            part = self.parts.get(part_name)
            part.geometry.val().exportStl(output_path)
            logger.info(f"Exported part '{part_name}' to {output_path}")
        except Exception as e:
            raise TiaCADParserError(
                f"Failed to export part '{part_name}' to STL: {str(e)}"
            ) from e

    def export_step(self, output_path: str, part_name: Optional[str] = None):
        """
        Export part to STEP file.

        Args:
            output_path: Path to output STEP file
            part_name: Part to export (if None, exports the last operation result)

        Raises:
            TiaCADParserError: If export fails
        """
        if part_name is None:
            if self.operations:
                part_name = list(self.operations.keys())[-1]
            else:
                part_name = self.parts.list_parts()[0]

        try:
            part = self.parts.get(part_name)
            part.geometry.val().exportStep(output_path)
            logger.info(f"Exported part '{part_name}' to {output_path}")
        except Exception as e:
            raise TiaCADParserError(
                f"Failed to export part '{part_name}' to STEP: {str(e)}"
            ) from e

    def export_3mf(self, output_path: str):
        """
        Export all parts to 3MF file with multi-material support.

        3MF is the modern standard for 3D printing, supporting:
        - Multi-color/multi-material parts
        - Material properties (from TiaCAD color system)
        - Assembly information
        - Metadata

        Unlike STL (single part) or STEP (CAD-focused), 3MF is perfect
        for multi-material 3D printing workflows.

        Args:
            output_path: Path to output .3mf file

        Raises:
            TiaCADParserError: If export fails

        Example:
            >>> doc = TiaCADParser.parse_file("multi_material.yaml")
            >>> doc.export_3mf("output.3mf")
            # Open in PrusaSlicer/BambuStudio with materials auto-assigned!
        """
        try:
            from ..exporters import export_3mf

            # Export all parts with materials
            export_3mf(self.parts, output_path, self.metadata)

            logger.info(
                f"Exported {len(self.parts.list_parts())} parts to {output_path} (3MF)"
            )

        except ImportError as e:
            raise TiaCADParserError(
                "3MF export requires lib3mf. Install with: pip install lib3mf"
            ) from e
        except Exception as e:
            raise TiaCADParserError(
                f"Failed to export 3MF: {str(e)}"
            ) from e

    def __repr__(self) -> str:
        part_count = len(self.parts.list_parts())
        return f"TiaCADDocument(parts={part_count}, metadata={self.metadata.get('name', 'Unnamed')})"


class TiaCADParser:
    """
    Main parser for TiaCAD YAML files.

    Usage:
        # Parse from file
        doc = TiaCADParser.parse_file("model.yaml")

        # Export
        doc.export_stl("output.stl")

        # Access parts
        part = doc.get_part("my_part")
    """

    SUPPORTED_SCHEMA_VERSIONS = ["2.0"]

    @staticmethod
    def parse_file(file_path: str, validate_schema: bool = False) -> TiaCADDocument:
        """
        Parse a TiaCAD YAML file.

        Args:
            file_path: Path to YAML file
            validate_schema: If True, validate against JSON schema before parsing

        Returns:
            TiaCADDocument ready for export

        Raises:
            TiaCADParserError: If parsing fails
        """
        logger.info(f"Parsing TiaCAD file: {file_path}")

        # Load YAML with line tracking
        try:
            with open(file_path, 'r') as f:
                yaml_string = f.read()
            yaml_data, line_tracker = parse_yaml_with_lines(yaml_string, filename=file_path)
        except FileNotFoundError:
            raise TiaCADParserError(f"File not found: {file_path}", file_path=file_path)
        except yaml.YAMLError as e:
            raise TiaCADParserError(f"Invalid YAML: {str(e)}", file_path=file_path)
        except Exception as e:
            raise TiaCADParserError(f"Failed to load file: {str(e)}", file_path=file_path)

        # Parse the loaded YAML
        return TiaCADParser.parse_dict(
            yaml_data,
            file_path=file_path,
            validate_schema=validate_schema,
            line_tracker=line_tracker,
            yaml_string=yaml_string
        )

    @staticmethod
    def parse_string(yaml_string: str) -> TiaCADDocument:
        """
        Parse a TiaCAD YAML string.

        Args:
            yaml_string: YAML content as string

        Returns:
            TiaCADDocument ready for export

        Raises:
            TiaCADParserError: If parsing fails
        """
        try:
            yaml_data, line_tracker = parse_yaml_with_lines(yaml_string)
        except yaml.YAMLError as e:
            raise TiaCADParserError(f"Invalid YAML: {str(e)}")

        return TiaCADParser.parse_dict(
            yaml_data,
            line_tracker=line_tracker,
            yaml_string=yaml_string
        )

    @staticmethod
    def parse_dict(
        yaml_data: Dict[str, Any],
        file_path: Optional[str] = None,
        validate_schema: bool = False,
        line_tracker: Optional[LineTracker] = None,
        yaml_string: Optional[str] = None
    ) -> TiaCADDocument:
        """
        Parse TiaCAD data from dictionary.

        Args:
            yaml_data: Parsed YAML data
            file_path: Optional file path for error messages
            validate_schema: If True, validate against JSON schema before parsing
            line_tracker: Optional YAML line tracker for error reporting
            yaml_string: Optional original YAML string for error context

        Returns:
            TiaCADDocument ready for export

        Raises:
            TiaCADParserError: If parsing or validation fails
        """
        try:
            # Schema validation (if requested)
            if validate_schema:
                validator = SchemaValidator()
                errors = validator.validate(yaml_data)
                if errors:
                    error_msg = "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
                    raise TiaCADParserError(error_msg, file_path=file_path)

            # Validate schema version (optional but recommended)
            schema_version = yaml_data.get('schema_version', '2.0')
            if schema_version not in TiaCADParser.SUPPORTED_SCHEMA_VERSIONS:
                logger.warning(
                    f"Schema version '{schema_version}' not explicitly supported. "
                    f"Supported versions: {TiaCADParser.SUPPORTED_SCHEMA_VERSIONS}"
                )

            # Extract sections
            metadata = yaml_data.get('metadata', {})
            parameters = yaml_data.get('parameters', {})
            colors_palette = yaml_data.get('colors', {})
            materials_spec = yaml_data.get('materials', {})
            references_spec = yaml_data.get('references', {})
            parts_spec = yaml_data.get('parts', {})
            sketches_spec = yaml_data.get('sketches', {})
            operations_spec = yaml_data.get('operations', {})

            # Validate required sections
            if not parts_spec:
                raise TiaCADParserError(
                    "YAML must contain 'parts' section",
                    file_path=file_path
                )

            logger.info(f"Building model: {metadata.get('name', 'Unnamed')}")
            logger.debug(f"Parameters: {len(parameters)}, Parts: {len(parts_spec)}, Operations: {len(operations_spec)}, Colors: {len(colors_palette)}")

            # Phase 1: Resolve parameters
            param_resolver = ParameterResolver(parameters)
            resolved_params = param_resolver.resolve_all()
            logger.info(f"Resolved {len(resolved_params)} parameters")

            # Phase 1.5: Resolve color palette (may contain parameter references)
            resolved_palette = {}
            if colors_palette:
                for color_name, color_value in colors_palette.items():
                    resolved_palette[color_name] = param_resolver.resolve(color_value)
                logger.info(f"Loaded {len(resolved_palette)} palette colors")

            # Phase 1.6: Create color parser with resolved palette
            color_parser = ColorParser(palette=resolved_palette)
            if materials_spec:
                logger.info(f"Loaded {len(materials_spec)} custom materials")

            # Phase 1.7: Build sketches (for extrude/revolve/sweep/loft operations)
            sketches = {}
            if sketches_spec:
                from .sketch_builder import SketchBuilder
                sketch_builder = SketchBuilder(param_resolver)
                sketches = sketch_builder.build_sketches(sketches_spec)
                logger.info(f"Built {len(sketches)} sketches")

            # Phase 2: Build parts
            parts_builder = PartsBuilder(param_resolver, color_parser)
            registry = parts_builder.build_parts(parts_spec)
            logger.info(f"Built {len(parts_spec)} parts")

            # Phase 2.5: Parse spatial references (after parts, before operations)
            resolved_references = {}
            if references_spec:
                # Resolve parameter expressions in all references
                for ref_name, ref_spec in references_spec.items():
                    resolved_references[ref_name] = param_resolver.resolve(ref_spec)
                logger.info(f"Loaded {len(resolved_references)} references")

            # Create SpatialResolver
            spatial_resolver = SpatialResolver(registry, resolved_references)
            logger.info(f"Created SpatialResolver with {len(resolved_references)} references")

            # Phase 3: Execute operations (if any)
            if operations_spec:
                ops_builder = OperationsBuilder(registry, param_resolver, sketches, spatial_resolver)
                registry = ops_builder.execute_operations(operations_spec)
                logger.info(f"Executed {len(operations_spec)} operations")

            # Create document
            doc = TiaCADDocument(
                metadata=metadata,
                parameters=resolved_params,
                parts=registry,
                operations=operations_spec,
                references=resolved_references,
                line_tracker=line_tracker,
                yaml_string=yaml_string,
                file_path=file_path
            )

            logger.info(f"Successfully parsed TiaCAD document with {len(registry.list_parts())} total parts")
            return doc

        except TiaCADError:
            # Re-raise TiaCAD errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise TiaCADParserError(
                f"Unexpected error during parsing: {str(e)}",
                file_path=file_path
            ) from e

    @staticmethod
    def validate_file(file_path: str) -> tuple[bool, list[str]]:
        """
        Validate a TiaCAD YAML file without building geometry.

        Args:
            file_path: Path to YAML file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        try:
            # Try to parse
            TiaCADParser.parse_file(file_path)
            return (True, [])
        except TiaCADParserError as e:
            errors.append(str(e))
            return (False, errors)
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return (False, errors)


# Convenience function for quick usage
def parse(file_path: str) -> TiaCADDocument:
    """
    Quick parse function.

    Args:
        file_path: Path to TiaCAD YAML file

    Returns:
        TiaCADDocument

    Example:
        from tiacad_core.parser import parse
        doc = parse("model.yaml")
        doc.export_stl("output.stl")
    """
    return TiaCADParser.parse_file(file_path)
