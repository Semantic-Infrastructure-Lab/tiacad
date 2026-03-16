"""
Tests for ComponentImporter — the `imports:` section in TiaCAD YAML.

Tests cover:
- Basic local file import
- Parameter overrides
- Multiple imports with distinct namespaces
- Imported parts available in operations
- Error cases: missing file, missing 'path', missing 'as', invalid namespace, circular imports
- Nested imports (A imports B imports C)
- Import-only design (no local `parts:` section)
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tiacad_core.parser.tiacad_parser import TiaCADParser, TiaCADParserError
from tiacad_core.parser.component_importer import (
    ComponentImporter, ComponentImportError, _STDLIB_DIR, _GITHUB_CACHE_DIR
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_yaml(directory: str, filename: str, content: str) -> str:
    """Write a YAML file to a temp directory and return its absolute path."""
    path = os.path.join(directory, filename)
    with open(path, 'w') as f:
        f.write(content)
    return path


SIMPLE_BOX_COMPONENT = """
metadata:
  name: Simple Box Component
parameters:
  width: 50
  height: 30
  depth: 20
parts:
  body:
    primitive: box
    parameters:
      width: '${width}'
      height: '${height}'
      depth: '${depth}'
"""

MULTI_PART_COMPONENT = """
parameters:
  radius: 10
  height: 40
parts:
  shaft:
    primitive: cylinder
    parameters:
      radius: '${radius}'
      height: '${height}'
  cap:
    primitive: cylinder
    parameters:
      radius: '${radius}'
      height: 5
"""


# ---------------------------------------------------------------------------
# Basic import
# ---------------------------------------------------------------------------

class TestBasicImport:

    def test_import_single_component(self, tmp_path):
        """Basic import — parts appear with namespace prefix."""
        write_yaml(str(tmp_path), 'box_comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = f"""
imports:
  - path: ./box_comp.yaml
    as: box_comp

parts:
  base:
    primitive: box
    parameters:
      width: 100
      height: 10
      depth: 100
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        assert doc.get_part('base') is not None
        assert doc.get_part('box_comp.body') is not None

    def test_imported_part_geometry_exists(self, tmp_path):
        """Imported part has geometry (not None)."""
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: comp

parts:
  anchor:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        part = doc.get_part('comp.body')
        assert part is not None
        assert part.geometry is not None

    def test_import_without_local_parts_raises(self, tmp_path):
        """Importing with no local parts and no imports still raises the usual error."""
        main_yaml = """
metadata:
  name: Missing Parts
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises(TiaCADParserError, match="parts"):
            TiaCADParser.parse_file(main_file)

    def test_imports_only_no_local_parts(self, tmp_path):
        """A design with only imports and no local `parts:` is valid."""
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: comp
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        assert doc.get_part('comp.body') is not None


# ---------------------------------------------------------------------------
# Parameter overrides
# ---------------------------------------------------------------------------

class TestParameterOverrides:

    def test_override_changes_geometry(self, tmp_path):
        """Parameter overrides propagate into the imported component."""
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: widget
    parameters:
      width: 200
      height: 100
      depth: 50

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        part = doc.get_part('widget.body')
        assert part is not None
        # Geometry should reflect the overridden dimensions (200 × 100 × 50)
        bounds = part.get_bounds()
        size_x = bounds['max'][0] - bounds['min'][0]
        assert abs(size_x - 200) < 1.0, f"Expected width ~200, got {size_x}"

    def test_partial_overrides_keep_defaults(self, tmp_path):
        """Overriding only some parameters leaves defaults for the rest."""
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: comp
    parameters:
      width: 80   # override; height and depth stay at 30, 20

parts:
  dummy:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        part = doc.get_part('comp.body')
        bounds = part.get_bounds()
        size_x = bounds['max'][0] - bounds['min'][0]
        assert abs(size_x - 80) < 1.0


# ---------------------------------------------------------------------------
# Multiple imports
# ---------------------------------------------------------------------------

class TestMultipleImports:

    def test_two_imports_distinct_namespaces(self, tmp_path):
        """Two components imported under different namespaces coexist."""
        write_yaml(str(tmp_path), 'box_comp.yaml', SIMPLE_BOX_COMPONENT)
        write_yaml(str(tmp_path), 'cyl_comp.yaml', MULTI_PART_COMPONENT)

        main_yaml = """
imports:
  - path: ./box_comp.yaml
    as: box_comp
  - path: ./cyl_comp.yaml
    as: cyl_comp

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        assert doc.get_part('box_comp.body') is not None
        assert doc.get_part('cyl_comp.shaft') is not None
        assert doc.get_part('cyl_comp.cap') is not None

    def test_same_file_two_namespaces(self, tmp_path):
        """Same component imported twice with different namespaces and parameters."""
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: small
    parameters:
      width: 10
      height: 10
      depth: 10
  - path: ./comp.yaml
    as: large
    parameters:
      width: 100
      height: 100
      depth: 100

parts:
  placeholder:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        doc = TiaCADParser.parse_file(main_file)

        small = doc.get_part('small.body')
        large = doc.get_part('large.body')
        assert small is not None and large is not None

        small_bounds = small.get_bounds()
        large_bounds = large.get_bounds()
        small_size = small_bounds['max'][0] - small_bounds['min'][0]
        large_size = large_bounds['max'][0] - large_bounds['min'][0]
        assert large_size > small_size


# ---------------------------------------------------------------------------
# Nested imports (A → B → C)
# ---------------------------------------------------------------------------

class TestNestedImports:

    def test_transitive_import(self, tmp_path):
        """Component B imports component C; A imports B → all parts visible."""
        write_yaml(str(tmp_path), 'c.yaml', SIMPLE_BOX_COMPONENT)

        b_yaml = """
imports:
  - path: ./c.yaml
    as: c_comp

parts:
  b_part:
    primitive: cylinder
    parameters:
      radius: 5
      height: 20
"""
        write_yaml(str(tmp_path), 'b.yaml', b_yaml)

        a_yaml = """
imports:
  - path: ./b.yaml
    as: b_comp

parts:
  a_part:
    primitive: box
    parameters:
      width: 50
      height: 50
      depth: 50
"""
        a_file = write_yaml(str(tmp_path), 'a.yaml', a_yaml)
        doc = TiaCADParser.parse_file(a_file)

        # A's own part
        assert doc.get_part('a_part') is not None
        # B's own part, namespaced under b_comp
        assert doc.get_part('b_comp.b_part') is not None
        # C's parts appear as b_comp.c_comp.body (nested namespace)
        # Transitive imports are visible — B's full registry (including what B imported) is
        # namespaced under b_comp, so C's parts appear as b_comp.c_comp.body in A.
        assert doc.get_part('b_comp.c_comp.body') is not None


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestImportErrors:

    def test_missing_file_raises(self, tmp_path):
        main_yaml = """
imports:
  - path: ./nonexistent.yaml
    as: missing

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises((TiaCADParserError, ComponentImportError)):
            TiaCADParser.parse_file(main_file)

    def test_missing_path_field_raises(self, tmp_path):
        main_yaml = """
imports:
  - as: comp
    # missing 'path'

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises((TiaCADParserError, ComponentImportError)):
            TiaCADParser.parse_file(main_file)

    def test_missing_as_field_raises(self, tmp_path):
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    # missing 'as'

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises((TiaCADParserError, ComponentImportError)):
            TiaCADParser.parse_file(main_file)

    def test_invalid_namespace_raises(self, tmp_path):
        write_yaml(str(tmp_path), 'comp.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp.yaml
    as: "invalid-name"   # hyphens not allowed in identifiers

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises((TiaCADParserError, ComponentImportError)):
            TiaCADParser.parse_file(main_file)

    def test_circular_import_raises(self, tmp_path):
        """File A imports B which imports A → circular import error."""
        a_path = os.path.join(str(tmp_path), 'a.yaml')
        b_path = os.path.join(str(tmp_path), 'b.yaml')

        a_yaml = f"""
imports:
  - path: ./b.yaml
    as: b_comp

parts:
  a_part:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        b_yaml = f"""
imports:
  - path: ./a.yaml
    as: a_comp

parts:
  b_part:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        with open(a_path, 'w') as f:
            f.write(a_yaml)
        with open(b_path, 'w') as f:
            f.write(b_yaml)

        with pytest.raises((TiaCADParserError, ComponentImportError)):
            TiaCADParser.parse_file(a_path)

    def test_namespace_collision_raises(self, tmp_path):
        """Two imports using the same namespace raise an error."""
        write_yaml(str(tmp_path), 'comp1.yaml', SIMPLE_BOX_COMPONENT)
        write_yaml(str(tmp_path), 'comp2.yaml', SIMPLE_BOX_COMPONENT)

        main_yaml = """
imports:
  - path: ./comp1.yaml
    as: shared
  - path: ./comp2.yaml
    as: shared   # same namespace → collision on 'shared.body'

parts:
  base:
    primitive: box
    parameters:
      width: 1
      height: 1
      depth: 1
"""
        main_file = write_yaml(str(tmp_path), 'main.yaml', main_yaml)
        with pytest.raises((TiaCADParserError, ComponentImportError, ValueError)):
            TiaCADParser.parse_file(main_file)


# ---------------------------------------------------------------------------
# ComponentImporter unit tests
# ---------------------------------------------------------------------------

class TestComponentImporterUnit:

    def test_validate_import_def_missing_path(self):
        with pytest.raises(ComponentImportError, match="path"):
            ComponentImporter._validate_import_def({'as': 'comp'}, 0)

    def test_validate_import_def_missing_as(self):
        with pytest.raises(ComponentImportError, match="'as'"):
            ComponentImporter._validate_import_def({'path': './comp.yaml'}, 0)

    def test_validate_import_def_invalid_identifier(self):
        with pytest.raises(ComponentImportError, match="identifier"):
            ComponentImporter._validate_import_def({'path': './comp.yaml', 'as': '123bad'}, 0)

    def test_validate_import_def_valid(self):
        # Should not raise
        ComponentImporter._validate_import_def({'path': './comp.yaml', 'as': 'my_comp'}, 0)

    def test_validate_import_def_not_a_dict(self):
        with pytest.raises(ComponentImportError, match="mapping"):
            ComponentImporter._validate_import_def("not_a_dict", 0)


# ---------------------------------------------------------------------------
# _resolve_path routing
# ---------------------------------------------------------------------------

class TestResolvePath:

    def test_local_path_resolved(self, tmp_path):
        result = ComponentImporter._resolve_path("./sub/bracket.yaml", tmp_path)
        assert result == str((tmp_path / "sub" / "bracket.yaml").resolve())

    def test_stdlib_uri_routed(self):
        result = ComponentImporter._resolve_path("tiacad://std/hardware/m3_screw", Path("/any"))
        assert result == str(_STDLIB_DIR / "hardware" / "m3_screw.yaml")

    def test_github_uri_routed(self, tmp_path):
        # Patch _fetch_github to avoid network
        with patch.object(ComponentImporter, '_fetch_github', return_value="/tmp/cached.yaml") as mock:
            result = ComponentImporter._resolve_path("github:user/repo/comp.yaml", tmp_path)
        mock.assert_called_once_with("github:user/repo/comp.yaml")
        assert result == "/tmp/cached.yaml"


# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------

class TestStdlibImports:

    def test_m3_screw_resolves(self):
        path = ComponentImporter._resolve_stdlib("tiacad://std/hardware/m3_screw")
        assert path == str(_STDLIB_DIR / "hardware" / "m3_screw.yaml")
        assert Path(path).exists(), "m3_screw.yaml must exist in stdlib"

    def test_yaml_extension_auto_added(self):
        path = ComponentImporter._resolve_stdlib("tiacad://std/hardware/m4_screw")
        assert path.endswith("m4_screw.yaml")

    def test_yaml_extension_not_doubled(self):
        path = ComponentImporter._resolve_stdlib("tiacad://std/hardware/m5_screw.yaml")
        assert path.endswith("m5_screw.yaml")
        assert not path.endswith(".yaml.yaml")

    def test_all_stdlib_components_exist(self):
        expected = ["m3_screw", "m4_screw", "m5_screw", "m6_bolt", "m3_washer", "m3_standoff"]
        for name in expected:
            path = ComponentImporter._resolve_stdlib(f"tiacad://std/hardware/{name}")
            assert Path(path).exists(), f"stdlib component missing: {name}"

    def test_missing_stdlib_raises_helpful_error(self):
        with pytest.raises(ComponentImportError, match="not found") as exc_info:
            ComponentImporter._resolve_stdlib("tiacad://std/hardware/nonexistent_widget")
        # Error message should list available components
        assert "m3_screw" in str(exc_info.value)

    def test_empty_stdlib_uri_raises(self):
        with pytest.raises(ComponentImportError, match="empty"):
            ComponentImporter._resolve_stdlib("tiacad://std/")

    def test_stdlib_import_builds_part(self, tmp_path):
        """End-to-end: tiacad://std URI through the full parser."""
        main_yaml = tmp_path / "assembly.yaml"
        main_yaml.write_text("""
metadata:
  name: Stdlib Test
imports:
  - path: tiacad://std/hardware/m3_screw
    as: screw
parts:
  plate:
    primitive: box
    parameters:
      width: 50
      height: 5
      depth: 50
""")
        doc = TiaCADParser.parse_file(str(main_yaml))
        part_names = doc.parts.list_parts()
        assert any("screw." in n for n in part_names), f"screw.* parts missing from {part_names}"
        assert "plate" in part_names


# ---------------------------------------------------------------------------
# GitHub imports (mocked — no network)
# ---------------------------------------------------------------------------

GITHUB_COMPONENT_YAML = """
parameters:
  radius: 5
  height: 20
parts:
  shaft:
    primitive: cylinder
    parameters:
      radius: '${radius}'
      height: '${height}'
"""


class TestGithubImports:

    def test_fetch_github_downloads_and_caches(self, tmp_path):
        cache_root = tmp_path / "cache"

        def fake_urlretrieve(url, dest):
            Path(dest).write_text(GITHUB_COMPONENT_YAML)

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            result = ComponentImporter._fetch_github("github:alice/parts/peg.yaml")

        expected = str(cache_root / "alice" / "parts" / "peg.yaml")
        assert result == expected
        assert Path(result).read_text() == GITHUB_COMPONENT_YAML

    def test_fetch_github_uses_cache_on_second_call(self, tmp_path):
        cache_root = tmp_path / "cache"
        cached_file = cache_root / "alice" / "parts" / "peg.yaml"
        cached_file.parent.mkdir(parents=True)
        cached_file.write_text(GITHUB_COMPONENT_YAML)

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve") as mock_dl:
            result = ComponentImporter._fetch_github("github:alice/parts/peg.yaml")

        mock_dl.assert_not_called()
        assert result == str(cached_file)

    def test_fetch_github_yaml_extension_auto_added(self, tmp_path):
        cache_root = tmp_path / "cache"

        def fake_urlretrieve(url, dest):
            Path(dest).write_text(GITHUB_COMPONENT_YAML)

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            result = ComponentImporter._fetch_github("github:alice/parts/peg")

        assert result.endswith("peg.yaml")

    def test_fetch_github_builds_correct_url(self, tmp_path):
        cache_root = tmp_path / "cache"
        captured_url = []

        def fake_urlretrieve(url, dest):
            captured_url.append(url)
            Path(dest).write_text(GITHUB_COMPONENT_YAML)

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            ComponentImporter._fetch_github("github:bob/my-repo/hardware/bracket.yaml")

        assert captured_url[0] == "https://raw.githubusercontent.com/bob/my-repo/main/hardware/bracket.yaml"

    def test_fetch_github_http_error_raises(self, tmp_path):
        import urllib.error
        cache_root = tmp_path / "cache"

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=urllib.error.HTTPError(
                 url=None, code=404, msg="Not Found", hdrs=None, fp=None
             )):
            with pytest.raises(ComponentImportError, match="404"):
                ComponentImporter._fetch_github("github:alice/parts/missing.yaml")

    def test_fetch_github_network_error_raises(self, tmp_path):
        import urllib.error
        cache_root = tmp_path / "cache"

        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=urllib.error.URLError("Network unreachable")):
            with pytest.raises(ComponentImportError, match="Network unreachable"):
                ComponentImporter._fetch_github("github:alice/parts/widget.yaml")

    def test_fetch_github_invalid_spec_raises(self, tmp_path):
        """Spec must have user/repo/path — 'github:user/repo' alone is invalid."""
        with pytest.raises(ComponentImportError, match="Invalid GitHub"):
            ComponentImporter._fetch_github("github:user/repo")

    def test_github_import_end_to_end(self, tmp_path):
        """End-to-end: github: URI through the full parser (mocked download)."""
        cache_root = tmp_path / "cache"

        def fake_urlretrieve(url, dest):
            Path(dest).write_text(GITHUB_COMPONENT_YAML)

        main_yaml = tmp_path / "assembly.yaml"
        main_yaml.write_text("""
metadata:
  name: Github Import Test
imports:
  - path: github:alice/parts/peg.yaml
    as: peg
parts:
  base:
    primitive: box
    parameters:
      width: 30
      height: 5
      depth: 30
""")
        with patch("tiacad_core.parser.component_importer._GITHUB_CACHE_DIR", cache_root), \
             patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            doc = TiaCADParser.parse_file(str(main_yaml))

        part_names = doc.parts.list_parts()
        assert "peg.shaft" in part_names
        assert "base" in part_names
