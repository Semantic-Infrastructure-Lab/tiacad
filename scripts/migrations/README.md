# One-off migration scripts (archived)

These are **completed, historical** migration tools kept for provenance. They are
not part of the test suite or any automated flow. Do **not** re-run one unless you
are deliberately re-migrating from the exact old format it targets — several do
**in-place, no-backup, no-dry-run** rewrites of files under `examples/`.

| Script | Migrated | Effect | Status |
|--------|----------|--------|--------|
| `fix_pattern_api.py` | v3.0 `pattern` API: `spacing: '${v}'` + `direction: X` → `spacing: ['${v}', 0, 0]` | In-place regex rewrite of every `examples/*.yaml` (no backup, no dry-run) | ✅ Completed; kept for reference only |

**Before running any script here:** commit/stash your working tree first, since
these overwrite files with no backup. Prefer reading the script to understand the
transform rather than running it blind.

Moved here from the repo root on 2026-07-10 (was orphaned at top level, exactly
where an accidental re-run is easiest). See
`docs/developer/VALIDATION_STRENGTHENING.md` section 5 (housekeeping).
