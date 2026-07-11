# TiaCAD Code Review Follow-Ups

Date: 2026-04-18

This document tracks follow-up work from the 2026-04-18 code review.

## Findings

1. Watch-mode export did not follow the same part-selection/export contract as normal document export.
2. Geometry validation CLI still exported STL through raw CadQuery calls instead of the explicit backend boundary.
3. Watch mode duplicated significant parser/build-prep logic instead of reusing shared pipeline helpers.
4. Validation helpers still assumed CadQuery-style geometry access for bounding boxes.
5. Trust renderer remained brittle: unconditional headless setup, direct stdout side effects, and a large mixed-responsibility render function.

## Status

- [x] Fix watch-mode export contract drift
- [x] Fix backend-boundary leaks in geometry validation and validation helpers
- [x] Reduce watch-mode parser/build duplication
- [x] Refactor trust renderer for better separation and less environment brittleness
- [x] Run targeted verification and record results

## Progress Log

### 2026-04-18

- Tracking doc created.
- Added shared parser/build-prep context in `tiacad_core/parser/parse_pipeline.py` so watch mode no longer reconstructs colors/sketches/imports/references through ad hoc private parser calls.
- Added shared default-part resolution in `tiacad_core/parser/tiacad_parser.py` and reused it from document export and watch auto-export paths.
- Updated `tiacad_core/watcher.py` to build a real `TiaCADDocument` for export, so watch STL/STEP/3MF export follows the same part-selection rules instead of relying on registry order.
- Updated `tiacad_core/cli.py` geometry validation to enforce the explicit CadQuery boundary instead of falling through to raw `.val().exportStl(...)` failures.
- Updated validation helpers/rules to use backend-aware `Part.get_bounds()` through `ValidationRule._get_bounding_box()` instead of assuming CadQuery-only geometry access.
- Refactored `tiacad_core/visual/trust_renderer.py` to use backend tessellation, remove direct stdout logging, and make Xvfb startup best-effort instead of unconditional.

## Verification

- `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tiacad_core/tests/test_parser/test_tiacad_parser.py tiacad_core/tests/test_dag/test_watcher.py tiacad_core/tests/test_validation/test_assembly_validator.py tiacad_core/tests/test_cli/test_cli_helpers.py tiacad_core/tests/test_visualization/test_trust_renderer.py`
  - `73 passed`
- `reveal 'imports://tiacad_core?circular'`
  - `0` circular dependencies
- `reveal 'ast://tiacad_core/watcher.py?sort=-complexity&limit=8'`
  - `FileWatcher._rebuild` reduced to complexity `5`
- `reveal 'ast://tiacad_core/visual/trust_renderer.py?sort=-complexity&limit=8'`
  - `render_trust` reduced from the prior `33` to `16`

## Residual Notes

- `render_trust` is still a relatively dense function even after the cleanup, but it is less brittle and no longer relies on STL temp-file export or raw `print()` side effects.
- `watcher._resolve_watch_paths()` is still moderately branchy; it is now the main remaining watch-mode complexity pocket rather than rebuild/export drift.
