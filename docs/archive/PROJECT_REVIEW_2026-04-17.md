# TiaCAD Project Review

Date: 2026-04-17

Note: parts of this review were addressed immediately after it was written. In particular,
packaging metadata, several stale documentation links, CLI version reporting, parser
schema-version defaults, watch-mode import tracking, and a substantial portion of the
backend-boundary cleanup were updated in follow-up changes.

## Scope

This review covered:

- Top-level project docs and developer docs
- Core build path: parser, parts/operations builders, CLI, DAG, watcher
- Packaging metadata (`pyproject.toml`, `requirements.txt`)
- Targeted test execution

Test run used:

```bash
env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tiacad_core/tests/test_dag \
  tiacad_core/tests/test_parser \
  tiacad_core/tests/test_validation \
  tiacad_core/tests/test_correctness/test_example_contracts.py
```

Result: `884 passed in 89.08s`

## Executive Summary

The codebase is in materially better shape than the project-level status docs suggest. The targeted parser/DAG/validation/correctness slice passed cleanly, and the core implementation appears coherent.

The main problems are not broad correctness failures in the reviewed code path. The biggest issues are:

1. Packaging metadata does not match implemented features.
2. Schema/version contracts are internally inconsistent.
3. Watch mode does not track imported component files.
4. Documentation has drifted badly enough to reduce trust.
5. The advertised backend abstraction exists, but the implementation is still tightly coupled to CadQuery.

## Findings

### 1. Packaging bug: published dependencies are incomplete for documented features

Severity: High

Evidence:

- [`pyproject.toml:29`](../pyproject.toml#L29) does not declare `networkx`.
- [`requirements.txt:10`](../requirements.txt#L10) does declare `networkx>=3.0`.
- [`tiacad_core/dag/model_graph.py:11`](../tiacad_core/dag/model_graph.py#L11) imports `networkx as nx`.

Impact:

- A user installing from package metadata (`pip install .` or published wheel/sdist) can get a broken DAG/watch/`--show-deps` feature set even though those features are documented as complete.
- The repo currently relies on `requirements.txt` for completeness, but packaging tools and downstream users typically rely on `pyproject.toml`.

Related gap:

- `jsonschema` is required for `--validate-schema` to do real work, but it is not declared in [`pyproject.toml:29`](../pyproject.toml#L29) or [`requirements.txt:1`](../requirements.txt#L1).

Recommendation:

- Make `pyproject.toml` the source of truth.
- Add `networkx` to core dependencies.
- Add extras such as `schema`, `viz`, and `export` if optionality is intentional.
- Add a packaging smoke test that installs from package metadata and exercises `tiacad build --show-deps`.

### 2. Schema/version contract is inconsistent across parser, schema, and docs

Severity: High

Evidence:

- Parser only lists [`SUPPORTED_SCHEMA_VERSIONS = ["2.0"]`](../tiacad_core/parser/tiacad_parser.py#L284).
- JSON schema defaults to and validates `3.0` at [`tiacad-schema.json:8`](../tiacad-schema.json#L8).
- YAML reference is versioned `3.1.1` at [`docs/user/YAML_REFERENCE.md:3`](user/YAML_REFERENCE.md#L3).

Impact:

- The documented “current” format and the parser’s declared supported version diverge.
- Users who follow the schema/docs can get warnings from the parser for a version that the schema itself defines as current.
- This also makes maintenance harder because “current format” is ambiguous.

Secondary doc mismatch:

- The YAML reference says `export:` is required at [`docs/user/YAML_REFERENCE.md:73`](user/YAML_REFERENCE.md#L73), but the parser treats it as optional at [`tiacad_core/parser/tiacad_parser.py:431`](../tiacad_core/parser/tiacad_parser.py#L431).

Recommendation:

- Pick one canonical schema/version story and enforce it end-to-end.
- If v3 is current, update parser support and remove the `2.0` default.
- Add one test that asserts parser version support, JSON schema version, and docs version stay aligned.

### 3. Watch mode does not rebuild when imported component files change

Severity: Medium

Evidence:

- Watch mode only schedules the directory of the main file at [`tiacad_core/watcher.py:102`](../tiacad_core/watcher.py#L102).
- It only triggers when the changed path equals the root target file at [`tiacad_core/watcher.py:92`](../tiacad_core/watcher.py#L92).
- The rebuild path does load imports at [`tiacad_core/watcher.py:162`](../tiacad_core/watcher.py#L162), but those imported files are not watched.

Impact:

- `tiacad watch assembly.yaml` will miss edits to local imported components.
- That is a real workflow bug for any non-trivial assembly using `imports:`.

Recommendation:

- Track the resolved local import graph and subscribe to those files too.
- Recompute the watch set after each successful rebuild.
- Add an integration test that edits an imported local YAML and expects a rebuild event.

### 4. Documentation reliability is currently poor

Severity: Medium

Evidence:

- `docs/README.md` references a nonexistent file `architecture/CGA_V5_ARCHITECTURE_SPEC.md` at [`docs/README.md:31`](README.md#L31).
- `docs/architecture/README.md` references the same nonexistent file at [`docs/architecture/README.md:21`](architecture/README.md#L21).
- The actual file present is `docs/architecture/CGA_V5_FUTURE_VISION.md`.
- Root README links to nonexistent `docs/MIGRATION_GUIDE_V3.md` at [`README.md:41`](../README.md#L41).
- `PROJECT.md` still points to old root-level doc locations like `YAML_REFERENCE.md` and `docs/MIGRATION_GUIDE_V3.md` at [`PROJECT.md:148`](../PROJECT.md#L148).
- Developer docs tell contributors to run `ruff` at [`docs/developer/README.md:95`](developer/README.md#L95), but `ruff` is not declared in [`pyproject.toml:42`](../pyproject.toml#L42) or [`requirements.txt:27`](../requirements.txt#L27).
- Test/status counts are inconsistent:
  - `README.md` says `1125 tests` at [`README.md:20`](../README.md#L20)
  - `PROJECT.md` says `1405 passing` at [`PROJECT.md:55`](../PROJECT.md#L55)
  - `TESTING_GUIDE.md` says `1474 passing`
  - `KNOWN_LIMITATIONS.md` says `1495 passing`

Impact:

- Users cannot trust feature status, command examples, or doc links.
- Contributor onboarding is noisier than necessary because the docs describe a repo shape that no longer exists.

Recommendation:

- Add a doc integrity pass to CI:
  - link checker
  - file existence check for referenced internal docs
  - single generated source for version/test-count badges
- Reduce repeated status claims across docs; keep them in one generated status page instead.

### 5. The backend abstraction is only partially real

Severity: Architectural

Evidence:

- The abstraction promises that all geometry operations go through `GeometryBackend` at [`tiacad_core/geometry/base.py:21`](../tiacad_core/geometry/base.py#L21).
- `PartsBuilder` directly imports CadQuery and instantiates `CadQueryBackend` itself at [`tiacad_core/parser/parts_builder.py:21`](../tiacad_core/parser/parts_builder.py#L21) and [`tiacad_core/parser/parts_builder.py:61`](../tiacad_core/parser/parts_builder.py#L61).
- Large parts of the parser/build pipeline use CadQuery types directly rather than backend interfaces.

Impact:

- The code carries the complexity cost of an abstraction without getting full decoupling benefits.
- Mock backend usage is limited mostly to tests, not the production construction path.
- Future claims about swappable backends are not credible in the current structure.

Recommendation:

- Make an explicit decision:
  - either commit to CadQuery as the only kernel and simplify the abstraction,
  - or finish pushing primitive creation/export/selection behind backend boundaries.
- Avoid the current middle state.

## Other Issues Worth Fixing

- CLI version string is stale: [`tiacad_core/cli.py:799`](../tiacad_core/cli.py#L799) still reports `3.1.1` while package metadata is `3.1.2` at [`pyproject.toml:7`](../pyproject.toml#L7).
- CLI docs drift from implementation:
  - implementation defaults `build` output to `.3mf` at [`tiacad_core/cli.py:807`](../tiacad_core/cli.py#L807)
  - CLI docs still say default is `.stl` in places.
- `PROJECT.md` mixes “maintenance mode”, “v3.1 complete”, and unchecked v3.1 goals in the same file, which makes planning status hard to interpret.

## Recommended Next Steps

### Priority 1

1. Fix packaging metadata in `pyproject.toml`.
2. Unify schema/version handling around one current version.
3. Repair broken internal doc links and remove stale path references.

### Priority 2

1. Extend watch mode to include imported local files.
2. Add CI checks for docs, packaging, and a packaged-install smoke test.
3. Stop hardcoding test counts and release status in multiple places.

### Priority 3

1. Decide whether `GeometryBackend` is strategic or incidental.
2. If strategic, introduce backend injection into builders instead of direct `CadQueryBackend()` construction.
3. If not strategic, simplify the abstraction and document CadQuery as the intentional kernel boundary.

## Bottom Line

The project looks technically viable and substantially tested in the reviewed areas. The highest-value work now is not broad feature expansion. It is tightening the contract between code, packaging, and documentation so the project’s public surface reflects the state of the implementation.
