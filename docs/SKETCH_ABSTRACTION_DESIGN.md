# Sketch Operations Backend Abstraction Design

**Created:** 2025-10-26
**Session:** wise-sage-1026
**Status:** Design Phase

## Executive Summary

This document outlines a **pragmatic abstraction strategy** for TiaCAD's sketch-based operations (extrude, revolve, sweep, loft) to reduce coupling to CadQuery while maintaining code simplicity.

## Current State Analysis

### What's Already Abstracted ✅

**`geometry/base.py` - GeometryBackend interface:**
- ✅ Primitives (box, cylinder, sphere)
- ✅ Boolean operations (union, difference, intersection)
- ✅ Transforms (translate, rotate, scale)
- ✅ Finishing (fillet, chamfer)
- ✅ Queries (bounding box, center)
- ✅ Tessellation (mesh export)

**Implementations:**
- `CadQueryBackend` - Production implementation
- `MockBackend` - Fast testing (no CadQuery dependency)

### What's NOT Abstracted ❌

**Sketch Operations (Phase 3 work):**
- ❌ 2D shape building (Rectangle2D, Circle2D, Polygon2D)
- ❌ Extrude operation
- ❌ Revolve operation
- ❌ Sweep operation
- ❌ Loft operation

**Coupling Points:**
```python
# sketch.py - Shape2D classes
def build(self, workplane: cq.Workplane) -> cq.Workplane:
    # Returns CadQuery-specific type

# extrude_builder.py
base_wp = cq.Workplane(sketch.plane)          # Direct CadQuery
geometry = base_wp.extrude(distance)          # CadQuery method
geometry = geometry.union(shape_solid)        # CadQuery method
```

**Files with direct CadQuery imports:** 28 files

---

## Design Philosophy

### Pragmatic Abstraction Strategy

**Goal:** Decouple where it provides value, keep simple where it works.

**Approach:** **Hybrid Abstraction**
- **HIGH abstraction:** 3D operations (extrude, revolve, sweep, loft)
- **LOW abstraction:** 2D shape building (keep CadQuery for now)

**Rationale:**

1. **2D shapes are simple and stable**
   - Rectangle, circle, polygon building is straightforward
   - CadQuery handles this well
   - Not a pain point or bottleneck
   - Minimal coupling risk

2. **3D operations are complex and valuable to abstract**
   - Extrude, revolve have business logic
   - Different backends might optimize differently
   - Testing benefits from mocking
   - Future flexibility (build123d, etc.)

3. **Avoid over-engineering**
   - Don't abstract for abstract's sake
   - Focus on real architectural benefits
   - Balance purity with pragmatism

---

## Proposed Design

### Phase 1: Extend GeometryBackend with Sketch Operations

**Add to `geometry/base.py`:**

```python
class GeometryBackend(ABC):
    # ... existing methods ...

    # ========================================================================
    # Sketch Operations (Phase 3)
    # ========================================================================

    @abstractmethod
    def extrude(self, profile: Any, distance: float,
                direction: str = 'Z', taper: float = 0) -> Any:
        """
        Extrude a 2D profile to create 3D geometry.

        Args:
            profile: 2D profile to extrude (workplane for CadQuery)
            distance: Extrusion distance
            direction: Extrusion direction ('X', 'Y', or 'Z')
            taper: Draft angle in degrees (0 = straight extrusion)

        Returns:
            3D geometry object
        """
        pass

    @abstractmethod
    def revolve(self, profile: Any, axis: str = 'Z',
                angle: float = 360) -> Any:
        """
        Revolve a 2D profile around an axis.

        Args:
            profile: 2D profile to revolve
            axis: Axis of revolution ('X', 'Y', or 'Z')
            angle: Revolution angle in degrees (360 = full rotation)

        Returns:
            3D geometry object
        """
        pass

    @abstractmethod
    def sweep(self, profile: Any, path: List[Tuple[float, float, float]],
              transition: str = 'transformed') -> Any:
        """
        Sweep a 2D profile along a 3D path.

        Args:
            profile: 2D profile to sweep
            path: List of 3D points defining sweep path
            transition: Transition mode ('transformed', 'right', etc.)

        Returns:
            3D geometry object
        """
        pass

    @abstractmethod
    def loft(self, profiles: List[Any], ruled: bool = False) -> Any:
        """
        Loft between multiple 2D profiles.

        Args:
            profiles: List of 2D profiles to blend between
            ruled: If True, use straight (ruled) blending;
                   if False, use smooth blending

        Returns:
            3D geometry object
        """
        pass
```

**Benefits:**
- ✅ Operation builders can use `backend.extrude()` instead of direct CadQuery
- ✅ Testable with MockBackend
- ✅ Swappable backends in future
- ✅ Clean separation of concerns

### Phase 2: Implement in CadQueryBackend

**Update `geometry/cadquery_backend.py`:**

```python
class CadQueryBackend(GeometryBackend):
    # ... existing methods ...

    def extrude(self, profile: cq.Workplane, distance: float,
                direction: str = 'Z', taper: float = 0) -> cq.Workplane:
        """Extrude using CadQuery"""
        # Move existing logic from ExtrudeBuilder here
        if taper == 0:
            return profile.extrude(distance)
        else:
            return profile.extrude(distance, taper=taper)

    def revolve(self, profile: cq.Workplane, axis: str = 'Z',
                angle: float = 360) -> cq.Workplane:
        """Revolve using CadQuery"""
        # Move existing logic from RevolveBuilder here
        axis_vector = self._get_axis_vector(axis)
        return profile.revolve(angle, axis_vector)

    # ... sweep, loft implementations ...
```

**Benefits:**
- ✅ Encapsulates CadQuery-specific logic
- ✅ Single place to fix sweep/loft issues
- ✅ Reusable across operation builders

### Phase 3: Implement in MockBackend

**Update `geometry/mock_backend.py`:**

```python
class MockBackend(GeometryBackend):
    # ... existing methods ...

    def extrude(self, profile: MockGeometry, distance: float,
                direction: str = 'Z', taper: float = 0) -> MockGeometry:
        """Mock extrude - record operation"""
        return MockGeometry(
            shape_type='extrude',
            parameters={
                'distance': distance,
                'direction': direction,
                'taper': taper,
                'profile': profile
            },
            operation_history=profile.operation_history + ['extrude']
        )

    # ... similar for revolve, sweep, loft ...
```

**Benefits:**
- ✅ Fast testing without CadQuery
- ✅ Validates operation builder logic
- ✅ Enables unit testing of YAML parsing without 3D ops

### Phase 4: Refactor Operation Builders

**Update `extrude_builder.py` to use backend:**

```python
class ExtrudeBuilder:
    def __init__(self, part_registry, sketches, resolver,
                 line_tracker, backend: GeometryBackend):
        # ... existing init ...
        self.backend = backend  # Inject backend dependency

    def _extrude_sketch(self, sketch, distance, direction, taper, context):
        """Extrude using backend abstraction"""

        # Separate shapes
        add_shapes = [s for s in sketch.shapes if s.operation == 'add']
        subtract_shapes = [s for s in sketch.shapes if s.operation == 'subtract']

        # Build 2D profile (still using CadQuery for now)
        base_wp = cq.Workplane(sketch.plane)
        # ... origin handling ...
        base_wp = add_shapes[0].build(base_wp)

        # Use backend for extrusion (abstracted!)
        geometry = self.backend.extrude(base_wp, distance, direction, taper)

        # Union additional shapes
        for shape in add_shapes[1:]:
            shape_wp = cq.Workplane(sketch.plane)
            shape_wp = shape.build(shape_wp)
            shape_solid = self.backend.extrude(shape_wp, distance, direction, taper)
            geometry = self.backend.boolean_union(geometry, shape_solid)

        # Subtract holes
        for shape in subtract_shapes:
            shape_wp = cq.Workplane(sketch.plane)
            shape_wp = shape.build(shape_wp)
            cut_solid = self.backend.extrude(shape_wp, distance * 1.1, direction, 0)
            geometry = self.backend.boolean_difference(geometry, cut_solid)

        return geometry
```

**Benefits:**
- ✅ Reduced CadQuery coupling
- ✅ Uses existing boolean operations from backend
- ✅ Cleaner separation
- ✅ Still keeps simple 2D shape building in CadQuery

---

## What We're NOT Abstracting (Yet)

### 2D Shape Building (Pragmatic Decision)

**Keep as-is:**
```python
# sketch.py - Shape2D classes
def build(self, workplane: cq.Workplane) -> cq.Workplane:
    # Still uses CadQuery directly
```

**Reasons:**
1. **Simple and stable** - rectangle, circle, polygon are straightforward
2. **Low coupling risk** - not a pain point
3. **Diminishing returns** - abstraction overhead > benefit
4. **Easy to abstract later** - if needed, can wrap in future

**When to revisit:**
- If we add complex 2D constraints
- If 2D sketch building becomes a bottleneck
- If we want to support alternative 2D engines
- If we need pure-Python sketch parsing

---

## Implementation Plan

### Step 1: Design Validation (1-2 hours)
- [x] Review current coupling
- [ ] Validate abstraction approach
- [ ] Get feedback on design

### Step 2: Extend GeometryBackend (2-3 hours)
- [ ] Add sketch operation methods to `base.py`
- [ ] Document parameters and return types
- [ ] Add docstrings with examples

### Step 3: Implement CadQueryBackend (1 day)
- [ ] Move extrude logic to backend
- [ ] Move revolve logic to backend
- [ ] Move sweep logic to backend (and fix!)
- [ ] Move loft logic to backend (and fix!)
- [ ] Handle edge cases and errors

### Step 4: Implement MockBackend (4-6 hours)
- [ ] Add mock extrude
- [ ] Add mock revolve
- [ ] Add mock sweep
- [ ] Add mock loft
- [ ] Write unit tests for mock operations

### Step 5: Refactor Operation Builders (1-2 days)
- [ ] Update ExtrudeBuilder to use backend
- [ ] Update RevolveBuilder to use backend
- [ ] Update SweepBuilder to use backend
- [ ] Update LoftBuilder to use backend
- [ ] Update tests to inject backend

### Step 6: Integration & Testing (1 day)
- [ ] Run full test suite
- [ ] Fix any regressions
- [ ] Test all example YAML files
- [ ] Verify STL export still works

**Total Estimated Effort:** 4-5 days

---

## Benefits of This Approach

### Architectural Benefits
- ✅ **Reduced coupling** - 3D operations abstracted from CadQuery
- ✅ **Testability** - MockBackend enables fast unit tests
- ✅ **Future-proof** - Can swap backends (build123d, etc.)
- ✅ **Cleaner code** - Backend encapsulates complexity

### Pragmatic Benefits
- ✅ **Balanced approach** - Abstraction where it matters
- ✅ **Low risk** - Incremental refactoring
- ✅ **Quick wins** - Can fix sweep/loft while refactoring
- ✅ **Maintainable** - Easier to reason about

### Testing Benefits
- ✅ **Fast tests** - Mock operations run 10-100x faster
- ✅ **Isolated testing** - Test YAML parsing separately from 3D
- ✅ **Better coverage** - Can test edge cases without slow CAD ops

---

## Success Criteria

### Must Have
- [ ] All sketch operations use GeometryBackend methods
- [ ] Zero regressions in existing tests (556 tests passing)
- [ ] All example YAML files still work
- [ ] MockBackend supports all sketch operations

### Should Have
- [ ] Sweep operation fixed (profile orientation)
- [ ] Loft operation fixed (wire management)
- [ ] New tests using MockBackend
- [ ] Documentation updated

### Nice to Have
- [ ] Performance benchmarks (mock vs real)
- [ ] Alternative backend prototype (build123d?)
- [ ] Migration guide for future backends

---

## Risks & Mitigations

### Risk: Over-abstraction
**Mitigation:** Keep 2D shape building in CadQuery (pragmatic)

### Risk: Breaking changes
**Mitigation:** Incremental refactoring, comprehensive tests

### Risk: Performance overhead
**Mitigation:** Backend methods should be thin wrappers

### Risk: API design issues
**Mitigation:** Start simple, iterate based on usage

---

## Future Considerations

### When to Abstract 2D Shapes

**Consider abstracting when:**
- Adding sketch constraints (dimensions, relationships)
- Supporting alternative 2D engines
- 2D building becomes complex
- Performance issues with CadQuery 2D

**Not before:** It's working well as-is

### Alternative Backends

**Potential future backends:**
- **build123d** - When it hits 1.0 stable
- **pythonOCC** - For direct OpenCascade access
- **Pure Python** - For web-based deployment

**Enable by:** This abstraction layer!

---

## Conclusion

This **pragmatic hybrid abstraction** provides:
- ✅ Real architectural benefits (3D operation abstraction)
- ✅ Practical improvements (testability, flexibility)
- ✅ Balanced complexity (not over-engineered)
- ✅ Future-proof (can swap backends)

**Recommendation:** Proceed with implementation.

**Next Steps:**
1. Validate this design
2. Extend GeometryBackend interface
3. Implement in both backends
4. Refactor operation builders
5. Fix sweep/loft while we're at it!

---

**Author:** TIA
**Session:** wise-sage-1026
**Date:** 2025-10-26
