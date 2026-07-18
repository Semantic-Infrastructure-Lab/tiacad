"""Shared parse pipeline used by the public parser and component imports."""

import logging
import os
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, FrozenSet, Optional

from ..spatial_resolver import SpatialResolver
from ..utils.exceptions import TiaCADError
from .color_parser import ColorParser
from .errors import TiaCADParserError
from .operations_builder import OperationsBuilder
from .parameter_resolver import ParameterResolver
from .parts_builder import PartsBuilder
from .schema_validator import SchemaValidator
from .yaml_with_lines import LineTracker

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..geometry import GeometryBackend


@dataclass
class PreparedBuildContext:
    """Shared parser/watch build-prep state before part/operation realization."""

    metadata: Dict[str, Any]
    sections: Dict[str, Any]
    param_resolver: ParameterResolver
    resolved_params: Dict[str, Any]
    registry: Any
    color_parser: ColorParser
    sketches: Dict[str, Any]
    resolved_references: Dict[str, Any]
    spatial_resolver: SpatialResolver
    export_config: Dict[str, Any]


def normalize_yaml_aliases(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize supported YAML aliases to canonical field names."""
    if 'anchors' in yaml_data:
        if 'references' in yaml_data:
            raise TiaCADParserError(
                "Cannot use both 'anchors:' and 'references:' sections. "
                "Use 'anchors:' (user-friendly) or 'references:' (canonical), not both."
            )
        yaml_data['references'] = yaml_data.pop('anchors')
        logger.debug("Normalized 'anchors:' to 'references:' (alias support)")

    return yaml_data


def maybe_build_graph(yaml_data: Dict[str, Any], file_path: Optional[str], build_graph: bool):
    """Build dependency graph if requested; returns graph or None."""
    if not build_graph:
        return None
    try:
        from ..dag import GraphBuilder
        graph = GraphBuilder().build_graph(yaml_data)
        logger.info(f"Built dependency graph with {len(graph)} nodes")
        return graph
    except ImportError:
        logger.warning("NetworkX not installed. Install with: pip install networkx>=3.0")
        return None
    except TiaCADError as e:
        raise TiaCADParserError(f"Dependency graph error: {str(e)}", file_path=file_path) from e


def resolve_color_palette(colors_palette: Dict, param_resolver: ParameterResolver) -> Dict:
    """Resolve parameter expressions in all palette color values."""
    resolved = {name: param_resolver.resolve(val) for name, val in colors_palette.items()}
    logger.info(f"Loaded {len(resolved)} palette colors")
    return resolved


def build_sketches_from_spec(sketches_spec: Dict, param_resolver: ParameterResolver) -> Dict:
    """Build all sketches from YAML spec."""
    from .sketch_builder import SketchBuilder

    sketches = SketchBuilder(param_resolver).build_sketches(sketches_spec)
    logger.info(f"Built {len(sketches)} sketches")
    return sketches


def resolve_references(references_spec: Dict, param_resolver: ParameterResolver) -> Dict:
    """Resolve parameter expressions in all spatial references."""
    resolved = {name: param_resolver.resolve(spec) for name, spec in references_spec.items()}
    logger.info(f"Loaded {len(resolved)} references")
    return resolved


def _normalize_legacy_export(export_spec):
    """Map the deprecated list-form export section to the current dict form.

    Old syntax was a list of ``{filename, parts}`` entries; the current form is
    ``{default_part, formats}``. Conversion is best-effort: the first entry's
    first part (or its filename stem) becomes ``default_part``, and file
    extensions across entries become ``formats``.
    """
    if not isinstance(export_spec, list):
        return export_spec

    warnings.warn(
        "Export list format is deprecated; use the dict form "
        "'export: {default_part: <name>, formats: [step, stl]}'. "
        "See docs/developer/MIGRATION_GUIDE_V3.md.",
        DeprecationWarning,
        stacklevel=2,
    )
    default_part = None
    formats: list = []
    for entry in export_spec:
        if not isinstance(entry, dict):
            continue
        parts = entry.get('parts')
        filename = entry.get('filename', '')
        if default_part is None:
            if parts:
                default_part = parts[0]
            elif filename:
                default_part = os.path.splitext(os.path.basename(filename))[0]
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext and ext not in formats:
            formats.append(ext)
    return {'default_part': default_part, 'formats': formats}


def build_export_config(export_spec: Dict) -> Dict:
    """Build export configuration dict from YAML export section."""
    export_spec = _normalize_legacy_export(export_spec)
    cfg = {
        'default_part': export_spec.get('default_part'),
        'formats': export_spec.get('formats', []),
        'color_mode': export_spec.get('color_mode', 'realistic'),
        'default_color': export_spec.get('default_color', [0.7, 0.7, 0.7]),
    }
    if cfg['default_part']:
        logger.info(f"Export config: default_part={cfg['default_part']}")
    return cfg


def extract_yaml_sections(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract all top-level YAML sections into a named dict."""
    return {
        'metadata': yaml_data.get('metadata', {}),
        'parameters': yaml_data.get('parameters', {}),
        'imports': yaml_data.get('imports', []),
        'colors': yaml_data.get('colors', {}),
        'materials': yaml_data.get('materials', {}),
        'references': yaml_data.get('references', {}),
        'parts': yaml_data.get('parts', {}),
        'sketches': yaml_data.get('sketches', {}),
        'operations': yaml_data.get('operations', {}),
        'export': yaml_data.get('export', {}),
        'expect': yaml_data.get('expect', {}),
    }


def prepare_build_context(
    yaml_data: Dict[str, Any],
    *,
    load_imports: Optional[Callable[..., Any]] = None,
    file_path: Optional[str] = None,
    import_stack: FrozenSet[str] = frozenset(),
    backend: Optional["GeometryBackend"] = None,
) -> PreparedBuildContext:
    """Prepare shared parser/watch build context before parts and operations execute."""
    sections = extract_yaml_sections(yaml_data)
    metadata = sections['metadata']
    parameters = sections['parameters']

    imported_registry = None
    if sections['imports']:
        if load_imports is None:
            raise TiaCADParserError(
                "Import handling is not configured for this parse path",
                file_path=file_path
            )
        base_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()
        imported_registry = load_imports(
            sections['imports'],
            base_dir,
            import_stack,
            backend=backend,
        )
        logger.info(
            f"Imported {len(imported_registry)} parts from {len(sections['imports'])} component(s)"
        )

    param_resolver = ParameterResolver(parameters)
    resolved_params = param_resolver.resolve_all()
    logger.info(f"Resolved {len(resolved_params)} parameters")

    resolved_palette = (
        resolve_color_palette(sections['colors'], param_resolver)
        if sections['colors'] else {}
    )
    color_parser = ColorParser(palette=resolved_palette)
    if sections['materials']:
        logger.info(f"Loaded {len(sections['materials'])} custom materials")

    sketches = (
        build_sketches_from_spec(sections['sketches'], param_resolver)
        if sections['sketches'] else {}
    )

    from ..part import PartRegistry
    registry = PartRegistry()
    if imported_registry:
        for part_name in imported_registry.list_parts():
            registry.add(imported_registry.get(part_name))
        logger.debug(f"Pre-populated registry with {len(imported_registry)} imported parts")

    resolved_references = (
        resolve_references(sections['references'], param_resolver)
        if sections['references'] else {}
    )
    spatial_resolver = SpatialResolver(registry, resolved_references)
    logger.info(f"Created SpatialResolver with {len(resolved_references)} references")

    export_config = build_export_config(sections['export'])

    return PreparedBuildContext(
        metadata=metadata,
        sections=sections,
        param_resolver=param_resolver,
        resolved_params=resolved_params,
        registry=registry,
        color_parser=color_parser,
        sketches=sketches,
        resolved_references=resolved_references,
        spatial_resolver=spatial_resolver,
        export_config=export_config,
    )


def _validate_and_extract_sections(
    yaml_data: Dict[str, Any],
    *,
    file_path: Optional[str],
    validate_schema: bool,
    supported_schema_versions: list[str],
    build_graph: bool,
):
    """Normalize aliases, validate schema/version, and extract YAML sections."""
    yaml_data = normalize_yaml_aliases(yaml_data)
    graph = maybe_build_graph(yaml_data, file_path, build_graph)

    if validate_schema:
        errors = SchemaValidator().validate(yaml_data)
        if errors:
            raise TiaCADParserError(
                "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors),
                file_path=file_path
            )

    schema_version = str(yaml_data.get('schema_version', '3.0'))
    if schema_version not in supported_schema_versions:
        logger.warning(
            f"Schema version '{schema_version}' not explicitly supported. "
            f"Supported versions: {supported_schema_versions}"
        )

    sections = extract_yaml_sections(yaml_data)
    if not sections['parts'] and not sections['imports']:
        raise TiaCADParserError("YAML must contain 'parts' section", file_path=file_path)

    metadata = sections['metadata']
    logger.info(f"Building model: {metadata.get('name', 'Unnamed')}")
    logger.debug(
        f"Parameters: {len(sections['parameters'])}, Parts: {len(sections['parts'])}, "
        f"Operations: {len(sections['operations'])}, Colors: {len(sections['colors'])}"
    )
    return sections, graph


def _build_parts_registry(
    parts_spec: Dict[str, Any],
    context: PreparedBuildContext,
    *,
    backend: Optional["GeometryBackend"],
):
    """Build parts from spec and merge in any parts already loaded from imports."""
    registry = PartsBuilder(
        context.param_resolver,
        context.color_parser,
        backend=backend,
    ).build_parts(parts_spec)
    logger.info(f"Built {len(parts_spec)} parts")

    for part_name in context.registry.list_parts():
        registry.add(context.registry.get(part_name))
    if len(context.registry.list_parts()) > 0:
        logger.debug(f"Merged {len(context.registry.list_parts())} imported parts into registry")

    return registry


def _apply_transforms_and_operations(
    registry,
    context: PreparedBuildContext,
    parts_spec: Dict[str, Any],
    operations_spec: Dict[str, Any],
):
    """Apply inline part transforms, then execute operations, in dependency order."""
    spatial_resolver = SpatialResolver(registry, context.resolved_references)

    # Apply each part's own inline translate:/rotate: (schema v3.0) in place,
    # before operations run, so operations see parts at their final position.
    # Runs after every part in parts_spec exists in `registry`, so a part may
    # anchor to any sibling's auto-generated references (e.g. base.face_top).
    OperationsBuilder(
        registry, context.param_resolver, context.sketches, spatial_resolver
    ).apply_inline_part_transforms(parts_spec)

    if operations_spec:
        registry = OperationsBuilder(
            registry, context.param_resolver, context.sketches, spatial_resolver
        ).execute_operations(operations_spec)
        logger.info(f"Executed {len(operations_spec)} operations")

    return registry


def parse_tiacad_dict(
    yaml_data: Dict[str, Any],
    *,
    document_factory: Callable[..., Any],
    supported_schema_versions: list[str],
    load_imports: Optional[Callable[..., Any]] = None,
    file_path: Optional[str] = None,
    validate_schema: bool = False,
    build_graph: bool = False,
    line_tracker: Optional[LineTracker] = None,
    yaml_string: Optional[str] = None,
    import_stack: FrozenSet[str] = frozenset(),
    backend: Optional["GeometryBackend"] = None,
):
    """Parse TiaCAD data from a dict and construct a document via the provided factory."""
    try:
        sections, graph = _validate_and_extract_sections(
            yaml_data,
            file_path=file_path,
            validate_schema=validate_schema,
            supported_schema_versions=supported_schema_versions,
            build_graph=build_graph,
        )
        parts_spec = sections['parts']
        operations_spec = sections['operations']

        context = prepare_build_context(
            yaml_data,
            load_imports=load_imports,
            file_path=file_path,
            import_stack=import_stack,
            backend=backend,
        )

        registry = _build_parts_registry(parts_spec, context, backend=backend)
        registry = _apply_transforms_and_operations(
            registry, context, parts_spec, operations_spec
        )

        doc = document_factory(
            metadata=sections['metadata'],
            parameters=context.resolved_params,
            parts=registry,
            operations=operations_spec,
            references=context.resolved_references,
            export_config=context.export_config,
            expect=sections['expect'],
            line_tracker=line_tracker,
            yaml_string=yaml_string,
            file_path=file_path,
            graph=graph,
        )

        logger.info(
            f"Successfully parsed TiaCAD document with {len(registry.list_parts())} total parts"
        )
        return doc

    except TiaCADError:
        raise
    except Exception as e:
        raise TiaCADParserError(
            f"Unexpected error during parsing: {str(e)}",
            file_path=file_path
        ) from e
