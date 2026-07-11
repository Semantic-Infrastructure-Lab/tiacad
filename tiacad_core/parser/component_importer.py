"""
ComponentImporter - Import system for TiaCAD

Handles the `imports:` section in TiaCAD YAML files, allowing reuse of
parts from other YAML files with optional parameter overrides.

Supported path formats:
  imports:
    - path: ./bracket.yaml               # local file (relative to current file)
      as: bracket
    - path: tiacad://std/hardware/m3_screw   # bundled standard library
      as: screw
    - path: github:user/repo/component.yaml  # GitHub raw download (cached)
      as: hook
    - path: github:user/repo/component.yaml@dev  # optional @branch override
      as: hook_dev
      parameters:                        # optional: override parameters
        width: 75

After processing, parts from the imported file are available as:
  {namespace}.{part_name}   →   e.g. bracket.body, bracket.plate

Supports recursive imports (A imports B imports C).
Circular imports are detected and raise TiaCADParserError.

GitHub import details:
  - Fetches from https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}
  - Branch defaults to `main`; override with a trailing `@branch` on the spec
    (e.g. github:user/repo/file.yaml@dev). Branch names may contain slashes.
  - Cached to ~/.tiacad/cache/github/{user}/{repo}/{branch}/{path}
  - Cache is permanent; delete ~/.tiacad/cache/github/ to force refresh

Standard library details:
  - tiacad://std/hardware/m3_screw → tiacad_core/stdlib/hardware/m3_screw.yaml
  - Available: m3_screw, m4_screw, m5_screw, m6_bolt, m3_washer, m3_standoff
"""

import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, List, Optional

import yaml

from ..part import Part, PartRegistry
from ..utils.exceptions import TiaCADError
from .errors import TiaCADParserError
from .yaml_with_lines import parse_yaml_with_lines

# Bundled stdlib root: tiacad_core/stdlib/
_STDLIB_DIR = Path(__file__).parent.parent / "stdlib"

# GitHub download cache: ~/.tiacad/cache/github/
_GITHUB_CACHE_DIR = Path.home() / ".tiacad" / "cache" / "github"

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..geometry import GeometryBackend


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
        import_stack: FrozenSet[str] = frozenset(),
        backend: Optional["GeometryBackend"] = None,
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

            abs_path = ComponentImporter._resolve_path(rel_path, base_path)

            if abs_path in import_stack:
                raise ComponentImportError(
                    f"Circular import detected: '{rel_path}' is already being imported.\n"
                    f"Import chain: {' → '.join(sorted(import_stack))} → {abs_path}",
                    path=abs_path
                )

            logger.info(f"Importing component '{namespace}' from {abs_path}")
            imported_parts = ComponentImporter._import_file(
                abs_path,
                namespace,
                param_overrides,
                import_stack,
                backend=backend,
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
    def _resolve_path(path_spec: str, base_dir: Path) -> str:
        """
        Resolve a path spec to an absolute local filesystem path.

        Handles three URI schemes:
          - Local:   ./bracket.yaml or ../parts/bracket.yaml
          - Stdlib:  tiacad://std/hardware/m3_screw
          - GitHub:  github:user/repo/path/to/component.yaml
        """
        if path_spec.startswith("tiacad://std/"):
            return ComponentImporter._resolve_stdlib(path_spec)
        elif path_spec.startswith("github:"):
            return ComponentImporter._fetch_github(path_spec)
        else:
            return str((base_dir / path_spec).resolve())

    @staticmethod
    def _resolve_stdlib(uri: str) -> str:
        """
        Resolve tiacad://std/<subpath> to an absolute path in the bundled stdlib.

        Example:
            tiacad://std/hardware/m3_screw  →  .../tiacad_core/stdlib/hardware/m3_screw.yaml
        """
        # Strip scheme prefix
        subpath = uri[len("tiacad://std/"):]
        if not subpath:
            raise ComponentImportError(
                f"Invalid stdlib URI '{uri}': path is empty after 'tiacad://std/'"
            )

        # Add .yaml if not already present
        if not subpath.endswith(".yaml"):
            subpath += ".yaml"

        abs_path = _STDLIB_DIR / subpath
        if not abs_path.exists():
            # List available components in the same directory to help the user
            parent = abs_path.parent
            available = sorted(p.stem for p in parent.glob("*.yaml")) if parent.exists() else []
            hint = f" Available in {parent.name}/: {', '.join(available)}" if available else ""
            raise ComponentImportError(
                f"Standard library component not found: '{uri}'.{hint}",
                path=str(abs_path)
            )

        return str(abs_path)

    @staticmethod
    def _fetch_github(spec: str) -> str:
        """
        Fetch a GitHub component and cache it locally.

        Format: github:user/repo/path/to/component.yaml
                github:user/repo/path/to/component.yaml@branch   (branch override)
        URL:    https://raw.githubusercontent.com/user/repo/{branch}/path/to/component.yaml
        Cache:  ~/.tiacad/cache/github/user/repo/{branch}/path/to/component.yaml

        Defaults to the `main` branch when no `@branch` suffix is given. A
        branch name may itself contain slashes (e.g. `@feature/foo`). Cache is
        permanent — delete ~/.tiacad/cache/github/ to force a refresh.
        """
        # Strip scheme prefix: "user/repo/path/to/file.yaml[@branch]"
        remainder = spec[len("github:"):]
        parts = remainder.split("/", 2)
        if len(parts) < 3:
            raise ComponentImportError(
                f"Invalid GitHub import spec '{spec}': "
                f"expected 'github:user/repo/path/to/file.yaml[@branch]'"
            )
        user, repo, file_path = parts[0], parts[1], parts[2]

        # Optional '@branch' suffix (everything after the last '@'); the branch
        # may contain slashes, so split it off before touching the file path.
        file_path, at, branch = file_path.rpartition("@")
        if not at:
            file_path, branch = branch, "main"
        elif not branch:
            raise ComponentImportError(
                f"Invalid GitHub import spec '{spec}': empty branch after '@'"
            )

        if not file_path.endswith(".yaml"):
            file_path += ".yaml"

        url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
        cache_path = _GITHUB_CACHE_DIR / user / repo / branch / file_path

        if cache_path.exists():
            logger.info(f"GitHub cache hit: {spec} → {cache_path}")
            return str(cache_path)

        logger.info(f"Fetching GitHub component: {url}")
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(url, str(cache_path))
        except urllib.error.HTTPError as e:
            cache_path.unlink(missing_ok=True)
            raise ComponentImportError(
                f"Failed to fetch GitHub component '{spec}': HTTP {e.code} from {url}",
                path=str(cache_path)
            ) from e
        except urllib.error.URLError as e:
            cache_path.unlink(missing_ok=True)
            raise ComponentImportError(
                f"Failed to fetch GitHub component '{spec}': {e.reason}",
                path=str(cache_path)
            ) from e

        logger.info(f"Cached GitHub component: {spec} → {cache_path}")
        return str(cache_path)

    @staticmethod
    def _import_file(
        abs_path: str,
        namespace: str,
        param_overrides: Dict[str, Any],
        import_stack: FrozenSet[str],
        backend: Optional["GeometryBackend"] = None,
    ) -> PartRegistry:
        """Load one component file and return its parts, namespaced."""
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
            from .parse_pipeline import parse_tiacad_dict

            doc = parse_tiacad_dict(
                yaml_data,
                document_factory=_ImportedComponentDocument,
                supported_schema_versions=["3.0"],
                load_imports=ComponentImporter.load_imports,
                file_path=abs_path,
                line_tracker=line_tracker,
                yaml_string=yaml_string,
                import_stack=import_stack | {abs_path},
                backend=backend,
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


class _ImportedComponentDocument:
    """Minimal parse result for imported component files."""

    def __init__(self, parts: PartRegistry, **_kwargs):
        self.parts = parts
