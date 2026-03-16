"""
ComponentImporter - Local file import system for TiaCAD

Handles the `imports:` section in TiaCAD YAML files, allowing reuse of
parts from other YAML files with optional parameter overrides.

Import spec format:
  imports:
    - path: ./bracket.yaml      # required: path relative to current file
      as: bracket               # required: namespace prefix for imported parts
      parameters:               # optional: override parameters in imported file
        width: 75

After processing, parts from the imported file are available as:
  {namespace}.{part_name}   →   e.g. bracket.body, bracket.plate

Supports recursive imports (A imports B imports C).
Circular imports are detected and raise TiaCADParserError.
"""

import logging
from pathlib import Path
from typing import Dict, Any, FrozenSet, List

import yaml

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .yaml_with_lines import parse_yaml_with_lines

logger = logging.getLogger(__name__)


class ComponentImportError(TiaCADError):
    """Error during component import"""
    def __init__(self, message: str, path: str = None):
        super().__init__(message)
        self.path = path


class ComponentImporter:
    """
    Processes the `imports:` section of a TiaCAD YAML file.

    Usage (internal — called by TiaCADParser):
        registry = ComponentImporter.load_imports(
            imports_spec,
            base_dir='/path/to/current/file/dir',
            import_stack=frozenset()
        )
        # registry contains all imported parts, namespaced
    """

    @staticmethod
    def load_imports(
        imports_spec: List[Dict[str, Any]],
        base_dir: str,
        import_stack: FrozenSet[str] = frozenset()
    ) -> PartRegistry:
        """
        Process all imports and return a PartRegistry with namespaced parts.

        Args:
            imports_spec: List of import definitions from YAML
            base_dir: Directory of the importing file (for relative path resolution)
            import_stack: Set of absolute paths currently being imported (cycle detection)

        Returns:
            PartRegistry containing all imported parts under their namespace prefixes

        Raises:
            ComponentImportError: If an import fails, file not found, or circular import detected
        """
        registry = PartRegistry()
        base_path = Path(base_dir)

        for i, import_def in enumerate(imports_spec):
            ComponentImporter._validate_import_def(import_def, i)

            rel_path = import_def['path']
            namespace = import_def['as']
            param_overrides = import_def.get('parameters', {})

            abs_path = str((base_path / rel_path).resolve())

            if abs_path in import_stack:
                raise ComponentImportError(
                    f"Circular import detected: '{rel_path}' is already being imported.\n"
                    f"Import chain: {' → '.join(sorted(import_stack))} → {abs_path}",
                    path=abs_path
                )

            logger.info(f"Importing component '{namespace}' from {abs_path}")
            imported_parts = ComponentImporter._import_file(
                abs_path, namespace, param_overrides, import_stack
            )

            for part_name in imported_parts.list_parts():
                part = imported_parts.get(part_name)
                if registry.exists(part.name):
                    raise ComponentImportError(
                        f"Import conflict: part '{part.name}' already exists. "
                        f"Use a unique 'as:' namespace for each import.",
                        path=abs_path
                    )
                registry.add(part)
                logger.debug(f"Imported part '{part.name}'")

        return registry

    @staticmethod
    def _import_file(
        abs_path: str,
        namespace: str,
        param_overrides: Dict[str, Any],
        import_stack: FrozenSet[str]
    ) -> PartRegistry:
        """Load one component file and return its parts, namespaced."""
        # Deferred import to avoid circular dependency at module load time
        from .tiacad_parser import TiaCADParser, TiaCADParserError

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                yaml_string = f.read()
        except FileNotFoundError:
            raise ComponentImportError(
                f"Component file not found: '{abs_path}'",
                path=abs_path
            )
        except OSError as e:
            raise ComponentImportError(
                f"Failed to read component file '{abs_path}': {e}",
                path=abs_path
            )

        try:
            yaml_data, line_tracker = parse_yaml_with_lines(yaml_string, filename=abs_path)
        except (yaml.YAMLError, ValueError) as e:
            raise ComponentImportError(
                f"Invalid YAML in component '{abs_path}': {e}",
                path=abs_path
            )

        # Apply parameter overrides before parsing
        if param_overrides:
            yaml_data.setdefault('parameters', {})
            yaml_data['parameters'].update(param_overrides)
            logger.debug(f"Applied {len(param_overrides)} parameter overrides to '{abs_path}'")

        try:
            doc = TiaCADParser.parse_dict(
                yaml_data,
                file_path=abs_path,
                line_tracker=line_tracker,
                yaml_string=yaml_string,
                _import_stack=import_stack | {abs_path}
            )
        except TiaCADParserError as e:
            raise ComponentImportError(
                f"Failed to parse component '{abs_path}': {e}",
                path=abs_path
            ) from e

        # Namespace all parts: {namespace}.{original_name}
        namespaced = PartRegistry()
        for part_name in doc.parts.list_parts():
            part = doc.parts.get(part_name)
            namespaced_part = part.clone(f"{namespace}.{part_name}")
            namespaced.add(namespaced_part)

        logger.info(
            f"Imported {len(namespaced)} parts from '{abs_path}' as namespace '{namespace}'"
        )
        return namespaced

    @staticmethod
    def _validate_import_def(import_def: Dict[str, Any], index: int) -> None:
        """Validate a single import definition dict."""
        if not isinstance(import_def, dict):
            raise ComponentImportError(
                f"imports[{index}] must be a mapping, got {type(import_def).__name__}"
            )
        if 'path' not in import_def:
            raise ComponentImportError(
                f"imports[{index}] missing required field 'path'"
            )
        if 'as' not in import_def:
            raise ComponentImportError(
                f"imports[{index}] missing required field 'as' (namespace prefix)"
            )
        namespace = import_def['as']
        if not isinstance(namespace, str) or not namespace.isidentifier():
            raise ComponentImportError(
                f"imports[{index}] 'as' must be a valid identifier, got '{namespace}'"
            )
