# TiaCAD Testing Confidence - Implementation Roadmap

**Version:** 1.0
**Created:** 2025-11-10
**Session:** galactic-expedition-1110
**Parent Document:** [TESTING_CONFIDENCE_PLAN.md](./TESTING_CONFIDENCE_PLAN.md)

---

## Overview

This document provides an actionable, week-by-week roadmap for implementing the TiaCAD Testing Confidence Plan. It breaks down the plan into concrete tasks with clear deliverables and acceptance criteria.

**Related Documents:**
- [TESTING_CONFIDENCE_PLAN.md](./TESTING_CONFIDENCE_PLAN.md) - Full strategic plan
- [PROJECT.md](../PROJECT.md) - TiaCAD project overview

---

## Quick Reference

**Timeline:**
- **Phase 1 (v3.1):** Q1 2026 - 6-8 weeks - Foundation utilities
- **Phase 2 (v3.2):** Q2 2026 - 8-10 weeks - Visual regression & advanced features
- **Phase 3 (v3.3+):** Q3+ 2026 - Ongoing - Stress testing & optimization

**Success Criteria:**
- v3.1: 950+ tests, 90% coverage, core measurement utilities
- v3.2: 1050+ tests, visual regression for all examples
- v3.3+: 1200+ tests, stress testing, property-based testing

---

## Phase 1: v3.1 - Foundation (Q1 2026)

**Duration:** 6-8 weeks
**Goal:** Implement core measurement utilities and expand test coverage

### Week 1: Measurement Utilities - Distance & Position

**Tasks:**

1. **Create `tiacad_core/testing/` module**
   - [ ] Create `tiacad_core/testing/__init__.py`
   - [ ] Create `tiacad_core/testing/measurements.py`
   - [ ] Add module docstring and overview

2. **Implement distance measurement**
   - [ ] Implement `measure_distance(part1, part2, ref1, ref2) -> float`
   - [ ] Support auto-references (e.g., "face_top", "center")
   - [ ] Add comprehensive docstring with examples
   - [ ] Write 5+ unit tests for `measure_distance()`

3. **Implement bounding box utilities**
   - [ ] Implement `get_bounding_box_dimensions(part) -> Dict[str, float]`
   - [ ] Returns {"width", "height", "depth"}
   - [ ] Write 3+ unit tests

**Deliverables:**
- `tiacad_core/testing/measurements.py` (100-150 lines)
- `tests/test_testing/test_measurements.py` (8+ tests)

**Acceptance Criteria:**
- ✅ All unit tests passing
- ✅ Documentation complete with examples
- ✅ Can measure distance between any two parts at any reference points

### Week 2: Orientation & Rotation Utilities

**Tasks:**

1. **Create orientation module**
   - [ ] Create `tiacad_core/testing/orientation.py`
   - [ ] Add module docstring

2. **Implement orientation extraction**
   - [ ] Implement `get_orientation_angles(part) -> Dict[str, float]`
   - [ ] Returns {"roll", "pitch", "yaw"} in degrees
   - [ ] Handle edge cases (gimbal lock, etc.)
   - [ ] Write 5+ unit tests

3. **Implement normal vector extraction**
   - [ ] Implement `get_normal_vector(part, face_ref) -> np.ndarray`
   - [ ] Extract from SpatialRef orientation
   - [ ] Write 3+ unit tests

4. **Implement alignment utilities**
   - [ ] Implement `parts_aligned(part1, part2, axis, tolerance) -> bool`
   - [ ] Write 3+ unit tests

**Deliverables:**
- `tiacad_core/testing/orientation.py` (150-200 lines)
- `tests/test_testing/test_orientation.py` (11+ tests)

**Acceptance Criteria:**
- ✅ Can extract rotation angles from any part
- ✅ Can verify face normals point in expected directions
- ✅ Can verify part alignment along axes

### Week 3: Dimensional Accuracy Utilities

**Tasks:**

1. **Create dimensions module**
   - [ ] Create `tiacad_core/testing/dimensions.py`
   - [ ] Add module docstring

2. **Implement dimension extraction**
   - [ ] Implement `get_dimensions(part) -> Dict[str, float]`
   - [ ] Implement `get_volume(part) -> float`
   - [ ] Implement `get_surface_area(part) -> float`
   - [ ] Write 10+ unit tests covering all primitives

**Deliverables:**
- `tiacad_core/testing/dimensions.py` (100-150 lines)
- `tests/test_testing/test_dimensions.py` (10+ tests)

**Acceptance Criteria:**
- ✅ Can extract dimensions from all primitive types
- ✅ Volume calculations accurate to 1%
- ✅ Surface area calculations accurate to 1%

### Week 4: Attachment Correctness Tests

**Tasks:**

1. **Create attachment test suite**
   - [ ] Create `tests/test_correctness/test_attachment_correctness.py`
   - [ ] Add module docstring

2. **Write basic attachment tests**
   - [ ] Test cylinder on box top (distance = 0)
   - [ ] Test box beside box (face-to-face)
   - [ ] Test sphere on plane
   - [ ] Test rotated attachment
   - [ ] Write 10+ tests total

3. **Write pattern attachment tests**
   - [ ] Test linear pattern spacing
   - [ ] Test circular pattern spacing
   - [ ] Test grid pattern alignment
   - [ ] Write 5+ tests

**Deliverables:**
- `tests/test_correctness/test_attachment_correctness.py` (15+ tests, 200-300 lines)

**Acceptance Criteria:**
- ✅ 15+ attachment tests passing
- ✅ Tests verify zero-distance attachments
- ✅ Tests verify pattern spacing correctness

### Week 5: Rotation Correctness Tests

**Tasks:**

1. **Create rotation test suite**
   - [ ] Create `tests/test_correctness/test_rotation_correctness.py`

2. **Write basic rotation tests**
   - [ ] Test 90° rotation around each axis (X, Y, Z)
   - [ ] Test 45° rotation verification
   - [ ] Test arbitrary angle rotations
   - [ ] Write 8+ tests

3. **Write normal vector tests**
   - [ ] Test face normals after rotation
   - [ ] Test face_top normal points up (before rotation)
   - [ ] Test face_top normal after 90° rotation
   - [ ] Write 5+ tests

4. **Write transform composition tests**
   - [ ] Test translate-then-rotate vs rotate-then-translate
   - [ ] Test multiple rotation composition
   - [ ] Write 3+ tests

**Deliverables:**
- `tests/test_correctness/test_rotation_correctness.py` (16+ tests, 250-350 lines)

**Acceptance Criteria:**
- ✅ 16+ rotation tests passing
- ✅ Tests verify angle accuracy to 0.1°
- ✅ Tests verify normal vectors after rotation

### Week 6: Dimensional Accuracy Tests

**Tasks:**

1. **Create dimensional test suite**
   - [ ] Create `tests/test_correctness/test_dimensional_accuracy.py`

2. **Write primitive dimension tests**
   - [ ] Test box dimensions (width, height, depth)
   - [ ] Test cylinder dimensions (radius, height)
   - [ ] Test sphere dimensions (radius)
   - [ ] Test cone dimensions
   - [ ] Write 8+ tests

3. **Write volume tests**
   - [ ] Test box volume calculation
   - [ ] Test cylinder volume calculation
   - [ ] Test sphere volume calculation
   - [ ] Write 5+ tests

4. **Write boolean operation tests**
   - [ ] Test union volume
   - [ ] Test difference volume
   - [ ] Test intersection volume
   - [ ] Write 4+ tests

**Deliverables:**
- `tests/test_correctness/test_dimensional_accuracy.py` (17+ tests, 250-350 lines)

**Acceptance Criteria:**
- ✅ 17+ dimensional tests passing
- ✅ Dimension accuracy to 0.01 units
- ✅ Volume accuracy to 1%

### Week 7: Pytest Markers & CI Integration

**Tasks:**

1. **Add pytest markers**
   - [ ] Update `pytest.ini` with new markers
   - [ ] Add `attachment`, `rotation`, `dimensions` markers
   - [ ] Mark all new tests appropriately

2. **Update documentation**
   - [ ] Create `docs/TESTING_GUIDE.md`
   - [ ] Document all new utilities with examples
   - [ ] Add "How to run" section for each test category

3. **Update CI/CD**
   - [ ] Update `.github/workflows/test.yml`
   - [ ] Add separate job for correctness tests
   - [ ] Configure test reporting

**Deliverables:**
- Updated `pytest.ini`
- `docs/TESTING_GUIDE.md` (new file)
- Updated CI/CD configuration

**Acceptance Criteria:**
- ✅ Can run `pytest -m attachment` to run only attachment tests
- ✅ Can run `pytest -m rotation` to run only rotation tests
- ✅ CI/CD runs all correctness tests automatically

### Week 8: Coverage & Polish

**Tasks:**

1. **Achieve 90% coverage**
   - [ ] Run coverage report: `pytest --cov=tiacad_core`
   - [ ] Identify gaps in coverage
   - [ ] Add tests to reach 90% threshold

2. **Add example-based tests**
   - [ ] Test 5 key examples end-to-end with new utilities
   - [ ] Guitar hanger attachment correctness
   - [ ] Mounting bracket dimensional accuracy
   - [ ] Auto-references box stack rotation correctness

3. **Polish & cleanup**
   - [ ] Review all new code for consistency
   - [ ] Add missing docstrings
   - [ ] Run linters and fix issues
   - [ ] Update RELEASE_NOTES.md for v3.1

**Deliverables:**
- 90% code coverage
- 5+ example-based correctness tests
- Clean, polished codebase

**Acceptance Criteria:**
- ✅ Coverage report shows 90%+
- ✅ All linters pass (ruff, mypy)
- ✅ All 950+ tests passing

### Phase 1 Summary

**Expected Outcomes:**
- ✅ 950+ tests (from 896 baseline)
- ✅ 90% code coverage (from 84%)
- ✅ 3 new testing utility modules
- ✅ 48+ new correctness tests
- ✅ Comprehensive documentation

**Metrics:**

| Metric | Before (v3.0) | After (v3.1) | Change |
|--------|---------------|--------------|--------|
| Total Tests | 896 | 950+ | +54+ |
| Coverage | 84% | 90% | +6% |
| Attachment Tests | ~5 | 20+ | +15+ |
| Rotation Tests | ~10 | 26+ | +16+ |
| Dimensional Tests | ~15 | 32+ | +17+ |

---

## Phase 2: v3.2 - Visual Regression & Advanced Features (Q2 2026)

**Duration:** 8-10 weeks
**Goal:** Add visual regression testing and advanced verification

### Week 1-2: Research & Design

**Tasks:**

1. **Research visual regression tools**
   - [ ] Evaluate trimesh for rendering
   - [ ] Evaluate matplotlib for image generation
   - [ ] Evaluate scikit-image for SSIM comparison
   - [ ] Document findings and recommendations

2. **Design visual regression architecture**
   - [ ] Design `VisualRegression` class API
   - [ ] Design reference image storage strategy
   - [ ] Design CI/CD integration approach
   - [ ] Create design document

3. **Prototype rendering pipeline**
   - [ ] Prototype part-to-trimesh conversion
   - [ ] Prototype rendering from standard angles
   - [ ] Prototype image comparison
   - [ ] Validate approach with 2-3 examples

**Deliverables:**
- Visual regression design document
- Proof-of-concept rendering pipeline

**Acceptance Criteria:**
- ✅ Can render parts to PNG images
- ✅ Can compare images with SSIM
- ✅ Validated approach on real examples

### Week 3-4: Visual Regression Implementation

**Tasks:**

1. **Create visual regression module**
   - [ ] Create `tiacad_core/testing/visual_regression.py`
   - [ ] Implement `VisualRegression` class
   - [ ] Implement `render_thumbnail()` method
   - [ ] Implement `compare_images()` method
   - [ ] Implement `save_reference()` method
   - [ ] Implement `verify_against_reference()` method

2. **Add image utilities**
   - [ ] Implement `part_to_trimesh()` conversion
   - [ ] Implement camera positioning logic
   - [ ] Implement diff image generation
   - [ ] Write 10+ unit tests

**Deliverables:**
- `tiacad_core/testing/visual_regression.py` (300-400 lines)
- `tests/test_testing/test_visual_regression.py` (10+ tests)

**Acceptance Criteria:**
- ✅ Can render any part to PNG
- ✅ Can compare images with >95% accuracy threshold
- ✅ Can save and load reference images

### Week 5-6: Generate Reference Images

**Tasks:**

1. **Generate references for all 40 examples**
   - [ ] Run `SAVE_REFERENCE=1 pytest -m visual` for all examples
   - [ ] Review all generated images manually
   - [ ] Re-generate any incorrect references
   - [ ] Store in `tests/visual_references/`

2. **Create visual test suite**
   - [ ] Create `tests/test_correctness/test_visual_correctness.py`
   - [ ] Add test for each example (40+ tests)
   - [ ] Add parametrized tests for multiple angles
   - [ ] Total: 50+ visual tests

**Deliverables:**
- `tests/visual_references/` with 40+ reference images
- `tests/test_correctness/test_visual_correctness.py` (50+ tests)

**Acceptance Criteria:**
- ✅ All 40 examples have reference images
- ✅ All visual tests passing
- ✅ Manual review confirms references are correct

### Week 7: Contact Detection & Advanced Attachment

**Tasks:**

1. **Implement contact detection**
   - [ ] Implement `parts_in_contact(part1, part2, tolerance) -> bool`
   - [ ] Implement bounding box proximity check (fast path)
   - [ ] Implement surface-to-surface distance (slow path)
   - [ ] Write 5+ unit tests

2. **Implement contact graph utilities**
   - [ ] Implement `build_contact_graph(parts, tolerance) -> Graph`
   - [ ] Implement `is_fully_connected(graph) -> bool`
   - [ ] Write 3+ unit tests

3. **Add assembly verification tests**
   - [ ] Test guitar hanger is fully connected
   - [ ] Test mounting bracket assembly
   - [ ] Test complex assemblies
   - [ ] Write 5+ tests

**Deliverables:**
- Contact detection in `measurements.py` (+100 lines)
- 13+ new tests

**Acceptance Criteria:**
- ✅ Can detect part contact accurately
- ✅ Can verify assembly connectivity
- ✅ Tests pass for all example assemblies

### Week 8: Advanced Dimensional Verification

**Tasks:**

1. **Implement hole detection**
   - [ ] Implement `find_cylindrical_holes(part) -> List[Hole]`
   - [ ] Extract hole radius, depth, position, normal
   - [ ] Write 5+ unit tests

2. **Implement feature detection**
   - [ ] Implement `find_fillets(part) -> List[Fillet]`
   - [ ] Implement `find_chamfers(part) -> List[Chamfer]`
   - [ ] Write 4+ unit tests

3. **Add hole verification tests**
   - [ ] Test mounting hole dimensions
   - [ ] Test hole spacing
   - [ ] Test hole alignment
   - [ ] Write 5+ tests

**Deliverables:**
- Feature detection in `dimensions.py` (+150 lines)
- 14+ new tests

**Acceptance Criteria:**
- ✅ Can find and measure cylindrical holes
- ✅ Can detect fillets and chamfers
- ✅ Hole dimension accuracy to 0.1 units

### Week 9: CI/CD Integration

**Tasks:**

1. **Add visual regression to CI**
   - [ ] Set up S3 bucket for reference images
   - [ ] Add CI step to download references
   - [ ] Add CI step to run visual tests
   - [ ] Add CI step to upload diffs on failure

2. **Configure automated updates**
   - [ ] Add workflow to update references (manual trigger)
   - [ ] Add review process for reference updates
   - [ ] Document reference update process

**Deliverables:**
- Updated `.github/workflows/test.yml`
- Reference image management documentation

**Acceptance Criteria:**
- ✅ Visual tests run automatically in CI
- ✅ Failures produce diff images for review
- ✅ Can update references via workflow trigger

### Week 10: Polish & Documentation

**Tasks:**

1. **Update documentation**
   - [ ] Create `docs/VISUAL_REGRESSION_GUIDE.md`
   - [ ] Create `docs/TESTING_UTILITIES_API.md`
   - [ ] Update main testing guide
   - [ ] Add troubleshooting section

2. **Polish & cleanup**
   - [ ] Review all v3.2 code
   - [ ] Add missing docstrings
   - [ ] Run linters
   - [ ] Update release notes

**Deliverables:**
- 2 new documentation files
- Updated testing guide
- Clean, polished codebase

**Acceptance Criteria:**
- ✅ All documentation complete
- ✅ All linters pass
- ✅ Ready for v3.2 release

### Phase 2 Summary

**Expected Outcomes:**
- ✅ 1050+ tests (from 950)
- ✅ Visual regression for all 40 examples
- ✅ Advanced attachment and dimensional verification
- ✅ CI/CD integration complete

**Metrics:**

| Metric | Before (v3.1) | After (v3.2) | Change |
|--------|---------------|--------------|--------|
| Total Tests | 950 | 1050+ | +100+ |
| Visual Tests | 0 | 50+ | +50+ |
| Contact Tests | 0 | 8+ | +8+ |
| Hole/Feature Tests | 0 | 9+ | +9+ |

---

## Phase 3: v3.3+ - Stress Testing & Optimization (Q3+ 2026)

**Duration:** Ongoing
**Goal:** Large assemblies, performance, property-based testing

### Ongoing Tasks

**Stress Testing:**
- [ ] Create large assembly test fixtures (100+ parts)
- [ ] Test precision accumulation (1000+ operations)
- [ ] Memory profiling and optimization
- [ ] Performance benchmarking

**Property-Based Testing:**
- [ ] Integrate Hypothesis library
- [ ] Generate random valid YAML
- [ ] Verify geometric invariants
- [ ] Find edge cases automatically

**Differential Testing:**
- [ ] Compare CadQuery vs. other backends
- [ ] Verify identical results
- [ ] Document differences

**Mutation Testing:**
- [ ] Set up mutation testing framework
- [ ] Measure test effectiveness
- [ ] Improve test suite based on findings
- [ ] Target 80%+ mutation score

### Phase 3 Summary

**Expected Outcomes:**
- ✅ 1200+ tests
- ✅ Stress testing infrastructure
- ✅ Property-based testing framework
- ✅ Performance benchmarks

---

## Tracking & Reporting

### Weekly Check-ins

**Template:**
```markdown
## Week [N] Progress Report

**Week of:** [Date]
**Phase:** [1/2/3]
**Goal:** [Week goal]

### Completed
- [x] Task 1
- [x] Task 2

### In Progress
- [ ] Task 3 (50% complete)

### Blockers
- None / [Describe blocker]

### Next Week
- [ ] Task 4
- [ ] Task 5

### Metrics
- Tests: [N] (target: [M])
- Coverage: [X]% (target: [Y]%)
```

### Milestone Reviews

**Phase Completion Checklist:**

Phase 1 (v3.1):
- [ ] 950+ tests passing
- [ ] 90% code coverage
- [ ] All utilities implemented
- [ ] Documentation complete
- [ ] CI/CD updated

Phase 2 (v3.2):
- [ ] 1050+ tests passing
- [ ] Visual regression working
- [ ] All 40 examples have references
- [ ] CI/CD runs visual tests
- [ ] Documentation complete

Phase 3 (v3.3+):
- [ ] 1200+ tests passing
- [ ] Stress tests implemented
- [ ] Property-based tests working
- [ ] Performance benchmarks established

---

## Risk Management

### Identified Risks

**Risk 1: Visual Regression False Positives**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Use high similarity threshold (95%+)
  - Allow manual review of failures
  - Document expected variations

**Risk 2: Test Suite Performance**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Keep visual tests separate (`pytest -m "not visual"`)
  - Optimize rendering pipeline
  - Use parallel test execution

**Risk 3: Reference Image Storage**
- **Impact:** Low
- **Probability:** Low
- **Mitigation:**
  - Use S3 for centralized storage
  - Keep references out of main repo
  - Implement cleanup for outdated references

**Risk 4: Maintenance Burden**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Automate reference updates
  - Clear documentation for contributors
  - Quarterly review and cleanup

---

## Success Criteria

### Phase 1 (v3.1) Success

✅ **Quantitative:**
- 950+ tests (from 896)
- 90% coverage (from 84%)
- <5 min test execution time

✅ **Qualitative:**
- Developers can verify attachment correctness
- Developers can verify rotation correctness
- Developers can verify dimensional accuracy
- Clear patterns established for future tests

### Phase 2 (v3.2) Success

✅ **Quantitative:**
- 1050+ tests (from 950)
- 50+ visual tests
- <10 min total test execution time

✅ **Qualitative:**
- Visual regressions caught automatically
- CI/CD provides confidence for merges
- Reference images maintained easily

### Phase 3 (v3.3+) Success

✅ **Quantitative:**
- 1200+ tests
- 100+ part assemblies supported
- 80%+ mutation score

✅ **Qualitative:**
- High confidence in TiaCAD correctness
- Users trust YAML → model translation
- Rare production issues

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-10 | TIA (galactic-expedition-1110) | Initial roadmap |

---

**End of Document**
