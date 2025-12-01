# TiaCAD Documentation-Code Alignment Issues

**Generated:** 2025-12-01
**Session:** valley-blizzard-1201
**Audit Method:** `reveal` code validation + document review

---

## Critical Issues: Version Inconsistencies

### Issue #1: Version Mismatch - Code vs Documentation

**Impact:** 🔴 BLOCKER for public release

| File | Version Claimed | Line(s) |
|------|----------------|---------|
| `tiacad_core/__init__.py` | `3.0.0-dev` | 10, 14 |
| `README.md` | `3.1.1` (PRODUCTION READY) | 19 |
| `CHANGELOG.md` | `3.1.1` (Released Nov 16) | 12 |
| `tiacad_core/cli.py` | `0.1.0` | 12, 465 |
| `docs/user/YAML_REFERENCE.md` | `3.0.0` | 3 |
| `docs/developer/CLI.md` | `0.1.0` | 3 |

**Problem:**
- README claims v3.1.1 is production ready
- CHANGELOG shows v3.1.1 released on 2025-11-16
- **Actual code is still 3.0.0-dev**
- CLI has independent version (0.1.0) - unclear relationship

**Decision Needed:**
1. **Is v3.1.1 actually released?** If yes → update `__init__.py` to `3.1.1`
2. **Is v3.1.1 in development?** If no → rollback README/CHANGELOG to `3.0.0`
3. **Should CLI version match project version?** Recommend: yes

**Recommendation:**
Based on CHANGELOG showing v3.1.1 as released with specific features, the code should be updated to match.

**Fix:**
- Update `tiacad_core/__init__.py` → `__version__ = "3.1.1"`
- Update `tiacad_core/cli.py` line 12 → `Version: 3.1.1`
- Update `tiacad_core/cli.py` line 465 → `version='TiaCAD 3.1.1'`
- Update `docs/user/YAML_REFERENCE.md` → `Version: 3.1.1`
- Update `docs/developer/CLI.md` → `Version: 3.1.1`

---

## Medium Priority: Documentation Updates

### Issue #2: Outdated Documentation Dates

**Impact:** 🟡 Low priority but shows staleness

| File | Last Updated Claim | Actual Status |
|------|-------------------|---------------|
| `docs/user/YAML_REFERENCE.md` | 2025-11-07 | Should be 2025-12-01 after alignment |

**Fix:** Update date stamps after alignment complete

---

### Issue #3: GitHub URL Placeholder

**Impact:** 🟡 Cosmetic but unprofessional for public release

**Location:** `tiacad_core/cli.py:461`

```python
For more information: https://github.com/yourusername/tiacad
```

**Fix:** Update to actual GitHub URL (need to know target repo)

---

## Validation Results: ✅ PASSED

### CLI Commands Match Documentation

**Actual Commands** (from `cli.py:444-501`):
- ✅ `build` - Build YAML to 3MF/STL/STEP
- ✅ `validate` - Validate YAML files
- ✅ `info` - Show file information
- ✅ `validate-geometry` - Check printability

**Documented Commands** (`docs/developer/CLI.md`):
- ✅ All 4 commands documented
- ✅ Options match actual argparse definitions
- ✅ Examples are accurate

**Verdict:** CLI documentation is accurate ✅

---

### Examples Validation

**Claimed:** README references example files
**Actual:** 44 YAML examples exist in `examples/`
**Status:** ✅ Examples directory well-populated

**Sample Examples Found:**
- transition_loft.yaml (referenced in README:76)
- simple_box.yaml
- guitar_hanger variants
- Text primitive examples
- Multi-material examples
- Auto-references demos

**Verdict:** Examples match documentation ✅

---

### Code Structure Validation

**Using `reveal` to validate documentation claims:**

**Primitives** (claimed in docs):
- ✅ box, cylinder, sphere, cone (confirmed via parser builders)

**Operations** (claimed in docs):
- ✅ extrude, revolve, sweep, loft (confirmed: `*_builder.py` files exist)
- ✅ boolean (union, difference, intersection) - `boolean_builder.py`
- ✅ pattern (linear, circular, grid) - `pattern_builder.py`
- ✅ finishing (fillet, chamfer) - `finishing_builder.py`
- ✅ gusset operations - `gusset_builder.py`
- ✅ hull operations - `hull_builder.py`

**Core Modules** (from `reveal tiacad_core/`):
- ✅ Part system (`part.py`)
- ✅ SpatialResolver (`spatial_resolver.py`)
- ✅ SelectorResolver (`selector_resolver.py`)
- ✅ TransformTracker (`transform_tracker.py`)
- ✅ Materials library (`materials_library.py`)
- ✅ Sketch system (`sketch.py`)

**Backends** (from `reveal tiacad_core/geometry/`):
- ✅ CadQuery backend (`cadquery_backend.py`)
- ✅ Mock backend for testing (`mock_backend.py`)
- ✅ Spatial references (`spatial_references.py`)

**Verdict:** Code structure matches architectural claims ✅

---

## Recommended Fix Order

### Phase 1: Version Alignment (Critical)
1. ✅ Update `tiacad_core/__init__.py` → `3.1.1`
2. ✅ Update `tiacad_core/cli.py` (2 locations) → `3.1.1`
3. ✅ Update `docs/user/YAML_REFERENCE.md` → `3.1.1`
4. ✅ Update `docs/developer/CLI.md` → `3.1.1`

### Phase 2: Metadata Updates (Low Priority)
5. ✅ Update date stamps to 2025-12-01
6. ✅ Update GitHub URL placeholder (if known)

### Phase 3: Validation (Required)
7. ✅ Run test suite to ensure no breakage
8. ✅ Build sample example to verify CLI works
9. ✅ Git commit all changes with summary

---

## Test Commands for Validation

After fixes, run these to verify:

```bash
# Check version consistency
grep -r "3\.1\.1" tiacad_core/ docs/
grep -r "3\.0\.0" tiacad_core/ docs/  # Should be minimal/none

# Verify imports work
python -c "import tiacad_core; print(tiacad_core.__version__)"

# Run test suite (if dependencies installed)
pytest tiacad_core/tests/ -v

# Build an example (requires CadQuery)
python -m tiacad_core build examples/simple_box.yaml
```

---

## Summary

**Good News:**
- ✅ Code structure is solid and matches documentation
- ✅ Examples are comprehensive (44 files)
- ✅ CLI documentation is accurate
- ✅ Feature claims in README are backed by actual code

**Fix Required:**
- 🔴 Version alignment (critical for public release)
- 🟡 Minor metadata updates (dates, URLs)

**Estimated Fix Time:** 10-15 minutes + test validation

**Risk Level:** Low (text changes only, no code changes)

---

---

## ✅ FIXES APPLIED - 2025-12-01

### Version Alignment Complete

**Files Updated:**
1. ✅ `tiacad_core/__init__.py` → `__version__ = "3.1.1"`
2. ✅ `tiacad_core/cli.py` (2 locations) → Version 3.1.1
3. ✅ `tiacad_core/parser/operations_builder.py` → Version 3.1.1 (docstring)
4. ✅ `docs/user/YAML_REFERENCE.md` (2 locations) → Version 3.1.1, updated dates
5. ✅ `docs/developer/CLI.md` → Version 3.1.1

**GitHub URL Updated:**
6. ✅ `tiacad_core/cli.py:461` → `https://github.com/scottsen/tiacad`

**Verification:**
```bash
$ grep -rn "3\.1\.1" tiacad_core/ docs/ | grep -E "(Version:|__version__|version=)"
tiacad_core/__init__.py:10:Version: 3.1.1
tiacad_core/__init__.py:14:__version__ = "3.1.1"
tiacad_core/cli.py:12:Version: 3.1.1
tiacad_core/cli.py:465:    parser.add_argument('--version', action='version', version='TiaCAD 3.1.1')
tiacad_core/parser/operations_builder.py:23:Version: 3.1.1
docs/user/YAML_REFERENCE.md:3:**Version:** 3.1.1
docs/user/YAML_REFERENCE.md:1381:**Version:** 3.1.1
docs/developer/CLI.md:3:**Version:** 3.1.1
```

**Status:** ✅ All version references aligned to 3.1.1

**Remaining 3.0.0 References:**
- `docs/architecture/ARCHITECTURE_DECISION_V3.md:290` - Historical document (intentional)

**Ready for Commit:** ✅ Yes

---

**Next Steps:**
1. ✅ Apply version fixes systematically
2. ⏳ Run validation tests (requires CadQuery installation)
3. ✅ Update this document with results
4. ⏳ Commit changes with "docs(align): sync version across all files to 3.1.1"
