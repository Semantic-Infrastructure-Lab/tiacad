"""Main public parser entry points for TiaCAD YAML documents."""

import logging
import yaml
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..backend_support import require_cadquery_part
from ..part import PartRegistry
from .component_importer import ComponentImporter
from .parameter_resolver import ParameterResolver
from .yaml_with_lines import parse_yaml_with_lines, LineTracker
from .errors import TiaCADParserError
from .parse_pipeline import parse_tiacad_dict, normalize_yaml_aliases, extract_yaml_sections

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..dag import ModelGraph
    from ..geometry import GeometryBackend


def resolve_default_part_name(
    parts: PartRegistry,
    operations: Optional[Dict[str, Any]] = None,
    export_config: Optional[Dict[str, Any]] = None,
    explicit_part_name: Optional[str] = None,
) -> str:
    """Resolve the default/final part name used by export and assembly paths."""
    if explicit_part_name is not None:
        return explicit_part_name

    export_config = export_config or {}
    if export_config.get('default_part') is not None:
        return export_config['default_part']

    if operations:
        return list(operations.keys())[-1]

    part_names = parts.list_parts()
    if not part_names:
        raise TiaCADParserError("Document has no parts to assemble")
    return part_names[0]


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
                 export_config: Optional[Dict[str, Any]] = None,
                 line_tracker: Optional[LineTracker] = None,
                 yaml_string: Optional[str] = None,
                 file_path: Optional[str] = None,
                 graph: Optional['ModelGraph'] = None):
        """
        Initialize TiaCAD document.

        Args:
            metadata: Document metadata from YAML
            parameters: Resolved parameters
            parts: Registry with all parts (primitives + operations)
            operations: Optional operations spec for reference
            references: Optional spatial references dictionary (name -> spec)
            export_config: Optional export configuration (default_part, formats, etc.)
            line_tracker: Optional YAML line tracker for error reporting
            yaml_string: Optional original YAML string for error context
            file_path: Optional file path for error messages
            graph: Optional dependency graph (for incremental rebuilds)
        """
        self.metadata = metadata
        self.parameters = parameters
        self.parts = parts
        self.operations = operations or {}
        self.references = references or {}
        self.export_config = export_config or {}
        self.line_tracker = line_tracker
        self.yaml_string = yaml_string
        self.file_path = file_path
        self.graph = graph

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
            part_name: Part to export (if None, uses export config or last operation)

        Raises:
            TiaCADParserError: If export fails
        """
        try:
            part_name = resolve_default_part_name(
                self.parts, self.operations, self.export_config, part_name
            )
            part = self.parts.get(part_name)
            require_cadquery_part(part, "STL export")
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
            part_name: Part to export (if None, uses export config or last operation)

        Raises:
            TiaCADParserError: If export fails
        """
        try:
            part_name = resolve_default_part_name(
                self.parts, self.operations, self.export_config, part_name
            )
            part = self.parts.get(part_name)
            require_cadquery_part(part, "STEP export")
            part.geometry.val().exportStep(output_path)
            logger.info(f"Exported part '{part_name}' to {output_path}")
        except Exception as e:
            raise TiaCADParserError(
                f"Failed to export part '{part_name}' to STEP: {str(e)}"
            ) from e

    def export_3mf(self, output_path: str, part_name: Optional[str] = None):
        """
        Export parts to 3MF file with multi-material support.

        3MF is the modern standard for 3D printing, supporting:
        - Multi-color/multi-material parts
        - Material properties (from TiaCAD color system)
        - Assembly information
        - Metadata

        Unlike STL (single part) or STEP (CAD-focused), 3MF is perfect
        for multi-material 3D printing workflows.

        Args:
            output_path: Path to output .3mf file
            part_name: Part to export (if None, exports all parts)

        Raises:
            TiaCADParserError: If export fails

        Example:
            >>> doc = TiaCADParser.parse_file("multi_material.yaml")
            >>> doc.export_3mf("output.3mf")  # Export all parts
            >>> doc.export_3mf("output.3mf", "final_part")  # Export single part
            # Open in PrusaSlicer/BambuStudio with materials auto-assigned!
        """
        try:
            from ..exporters import export_3mf
            from ..part import PartRegistry

            # Determine which parts to export
            if part_name is not None:
                # Export single specified part
                temp_registry = PartRegistry()
                part = self.parts.get(part_name)
                temp_registry.add(part.clone(part_name))
                export_3mf(temp_registry, output_path, self.metadata)
                logger.info(f"Exported part '{part_name}' to {output_path}")
            else:
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

    def get_assembly(self, part_name: Optional[str] = None):
        """
        Get the final assembled geometry as a CadQuery Workplane.

        Returns the "final" part of the model — same priority as export_stl:
        1. Explicitly named part_name
        2. export_config default_part
        3. Last operation result (convention: final assembled result)
        4. First part if no operations

        Args:
            part_name: Specific part to return (optional)

        Returns:
            CadQuery Workplane object suitable for rendering or export

        Raises:
            TiaCADParserError: If no parts exist or named part not found
        """
        if not self.parts.list_parts():
            raise TiaCADParserError("Document has no parts to assemble")

        try:
            part_name = resolve_default_part_name(
                self.parts, self.operations, self.export_config, part_name
            )
            return self.parts.get(part_name).geometry
        except Exception as e:
            raise TiaCADParserError(
                f"Failed to get assembly part '{part_name}': {str(e)}"
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

    SUPPORTED_SCHEMA_VERSIONS = ["3.0"]

    @staticmethod
    def parse_file(
        file_path: str,
        validate_schema: bool = False,
        build_graph: bool = False,
        backend: Optional["GeometryBackend"] = None,
    ) -> TiaCADDocument:
        """
        Parse a TiaCAD YAML file.

        Args:
            file_path: Path to YAML file
            validate_schema: If True, validate against JSON schema before parsing
            build_graph: If True, build dependency graph (for DAG features)

        Returns:
            TiaCADDocument ready for export

        Raises:
            TiaCADParserError: If parsing fails
        """
        logger.info(f"Parsing TiaCAD file: {file_path}")

        # Load YAML with line tracking
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            build_graph=build_graph,
            line_tracker=line_tracker,
            yaml_string=yaml_string,
            backend=backend,
        )

    @staticmethod
    def parse_string(
        yaml_string: str,
        backend: Optional["GeometryBackend"] = None,
    ) -> TiaCADDocument:
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
        except (yaml.YAMLError, ValueError) as e:
            raise TiaCADParserError(f"Invalid YAML: {str(e)}")

        return TiaCADParser.parse_dict(
            yaml_data,
            line_tracker=line_tracker,
            yaml_string=yaml_string,
            backend=backend,
        )

    @staticmethod
    def _normalize_yaml_aliases(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize YAML aliases to canonical field names.

        Supports user-friendly aliases:
        - 'anchors:' -> 'references:' (v3.2+)

        Args:
            yaml_data: Parsed YAML data

        Returns:
            Normalized YAML data with canonical field names

        Raises:
            TiaCADParserError: If both alias and canonical names are present
        """
        return normalize_yaml_aliases(yaml_data)

    @staticmethod
    def _maybe_build_graph(yaml_data: Dict[str, Any], file_path: Optional[str], build_graph: bool):
        """Build dependency graph if requested; returns graph or None."""
        from .parse_pipeline import maybe_build_graph

        return maybe_build_graph(yaml_data, file_path, build_graph)

    @staticmethod
    def _resolve_color_palette(colors_palette: Dict, param_resolver: ParameterResolver) -> Dict:
        """Resolve parameter expressions in all palette color values."""
        from .parse_pipeline import resolve_color_palette

        return resolve_color_palette(colors_palette, param_resolver)

    @staticmethod
    def _build_sketches_from_spec(sketches_spec: Dict, param_resolver: ParameterResolver) -> Dict:
        """Build all sketches from YAML spec."""
        from .parse_pipeline import build_sketches_from_spec

        return build_sketches_from_spec(sketches_spec, param_resolver)

    @staticmethod
    def _resolve_references(references_spec: Dict, param_resolver: ParameterResolver) -> Dict:
        """Resolve parameter expressions in all spatial references."""
        from .parse_pipeline import resolve_references

        return resolve_references(references_spec, param_resolver)

    @staticmethod
    def _build_export_config(export_spec: Dict) -> Dict:
        """Build export configuration dict from YAML export section."""
        from .parse_pipeline import build_export_config

        return build_export_config(export_spec)

    @staticmethod
    def _extract_yaml_sections(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all top-level YAML sections into a named dict."""
        return extract_yaml_sections(yaml_data)

    @staticmethod
    def parse_dict(
        yaml_data: Dict[str, Any],
        file_path: Optional[str] = None,
        validate_schema: bool = False,
        build_graph: bool = False,
        line_tracker: Optional[LineTracker] = None,
        yaml_string: Optional[str] = None,
        backend: Optional["GeometryBackend"] = None,
    ) -> TiaCADDocument:
        """Parse TiaCAD data from a dict; returns TiaCADDocument or raises TiaCADParserError."""
        return parse_tiacad_dict(
            yaml_data,
            document_factory=TiaCADDocument,
            supported_schema_versions=TiaCADParser.SUPPORTED_SCHEMA_VERSIONS,
            load_imports=ComponentImporter.load_imports,
            file_path=file_path,
            validate_schema=validate_schema,
            build_graph=build_graph,
            line_tracker=line_tracker,
            yaml_string=yaml_string,
            backend=backend,
        )

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


# CLI invocation detection and deprecation warning
if __name__ == '__main__':
    import sys
    print("\n" + "=" * 70, file=sys.stderr)
    print("⚠️  WARNING: Direct parser module invocation is DEPRECATED", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(file=sys.stderr)
    print("You are using:", file=sys.stderr)
    print("  python -m tiacad_core.parser.tiacad_parser file.yaml", file=sys.stderr)
    print(file=sys.stderr)
    print("Please use the modern CLI instead:", file=sys.stderr)
    print("  tiacad build file.yaml", file=sys.stderr)
    print(file=sys.stderr)
    print("Benefits of the new CLI:", file=sys.stderr)
    print("  ✅ Defaults to modern 3MF format (not legacy STL)", file=sys.stderr)
    print("  ✅ Progress indicators and colored output", file=sys.stderr)
    print("  ✅ Better error messages with context", file=sys.stderr)
    print("  ✅ Multiple output formats: 3MF, STEP, STL", file=sys.stderr)
    print("  ✅ Validation and info subcommands", file=sys.stderr)
    print(file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("\nContinuing with legacy STL output...\n", file=sys.stderr)

    # Legacy behavior: parse and export to STL
    if len(sys.argv) < 2:
        print("Usage: python -m tiacad_core.parser.tiacad_parser <file.yaml>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        from pathlib import Path
        doc = TiaCADParser.parse_file(file_path)
        output_path = Path(file_path).stem + ".stl"
        doc.export_stl(output_path)
        print(f"✓ Exported to {output_path} (legacy STL format)", file=sys.stderr)
        print(f"\nTIP: Use 'tiacad build {file_path}' for modern 3MF output\n", file=sys.stderr)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
