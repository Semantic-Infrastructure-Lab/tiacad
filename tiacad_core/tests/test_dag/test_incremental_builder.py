"""
Tests for IncrementalBuilder — incremental model rebuild orchestration.

Uses mock builders to avoid CadQuery geometry dependencies.
Focus: cache hit/miss logic, dirty propagation, structural changes.
"""

import pytest
from tiacad_core.dag.incremental_builder import (
    IncrementalBuilder, IncrementalState, BuildStats
)
from tiacad_core.dag.build_cache import BuildCache
from tiacad_core.dag.graph_builder import GraphBuilder
from tiacad_core.part import Part, PartRegistry


# ─── Mock helpers ───────────────────────────────────────────────────────────

class MockGeometry:
    """Stands in for a CadQuery Workplane."""
    def __init__(self, label: str):
        self.label = label

    def __repr__(self):
        return f"MockGeometry({self.label!r})"


def _make_part(name: str) -> Part:
    from unittest.mock import MagicMock
    geometry = MockGeometry(name)
    backend = MagicMock()
    return Part(name=name, geometry=geometry, metadata={}, backend=backend)


class MockPartsBuilder:
    """
    Records which parts were built (name → call count).
    Returns sentinel Part objects.
    """
    def __init__(self):
        self.build_calls: list[str] = []

    def build_part(self, name: str, spec: dict) -> Part:
        self.build_calls.append(name)
        return _make_part(name)


class MockOpsBuilder:
    """
    Records which operations were executed.
    On execute, adds a sentinel part to the registry.
    """
    def __init__(self, registry: PartRegistry):
        self.execute_calls: list[str] = []
        self.registry = registry

    def execute_operation(self, name: str, spec: dict) -> None:
        self.execute_calls.append(name)
        part = _make_part(name)
        self.registry.add(part)


def _build(
    yaml_data: dict,
    parts_spec: dict = None,
    operations_spec: dict = None,
    old_state: IncrementalState = None,
):
    """Helper: run IncrementalBuilder with mock builders."""
    parts_spec = parts_spec or yaml_data.get('parts', {})
    operations_spec = operations_spec or yaml_data.get('operations', {})

    registry = PartRegistry()
    parts_builder = MockPartsBuilder()
    ops_builder = MockOpsBuilder(registry)

    builder = IncrementalBuilder()
    result = builder.build(
        yaml_data=yaml_data,
        parts_spec=parts_spec,
        operations_spec=operations_spec,
        registry=registry,
        parts_builder=parts_builder,
        ops_builder=ops_builder,
        old_state=old_state,
    )
    result._parts_builder = parts_builder
    result._ops_builder = ops_builder
    return result


# ─── Full build (no old_state) ───────────────────────────────────────────────

class TestIncrementalBuilderFullBuild:

    def test_full_build_no_old_state(self):
        yaml_data = {
            'parameters': {'w': 10},
            'parts': {'box': {'primitive': 'box', 'width': '${w}', 'height': 5, 'depth': 5}},
        }
        result = _build(yaml_data)

        assert 'box' in result.registry
        assert result._parts_builder.build_calls == ['box']
        assert result.stats.rebuilt >= 1
        assert result.stats.cached == 0

    def test_full_build_caches_parts(self):
        yaml_data = {
            'parameters': {},
            'parts': {
                'a': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1},
                'b': {'primitive': 'cylinder', 'radius': 1, 'height': 1},
            },
        }
        result = _build(yaml_data)

        assert len(result._parts_builder.build_calls) == 2
        # State should be populated for next incremental build
        assert result.state.cache is not None
        assert result.state.graph is not None

    def test_full_build_with_operations(self):
        yaml_data = {
            'parameters': {},
            'parts': {'base': {'primitive': 'box', 'width': 10, 'height': 10, 'depth': 10}},
            'operations': {'final': {'type': 'chamfer', 'input': 'base', 'distance': 1}},
        }
        result = _build(yaml_data)

        assert 'base' in result.registry
        assert 'final' in result.registry
        assert result._ops_builder.execute_calls == ['final']


# ─── Incremental build — clean parts not rebuilt ─────────────────────────────

class TestIncrementalBuilderCacheHits:

    def test_unchanged_parts_not_rebuilt(self):
        yaml_data = {
            'parameters': {'w': 10},
            'parts': {
                'box': {'primitive': 'box', 'width': '${w}', 'height': 5, 'depth': 5},
                'cyl': {'primitive': 'cylinder', 'radius': 3, 'height': 10},
            },
        }
        # First build
        first = _build(yaml_data)
        assert len(first._parts_builder.build_calls) == 2

        # Second build — same yaml, should be all cached
        second = _build(yaml_data, old_state=first.state)
        assert second._parts_builder.build_calls == []
        assert second.stats.cached >= 2
        assert second.stats.rebuilt == 0

    def test_changed_parameter_dirties_dependent_part(self):
        yaml_base = {
            'parameters': {'w': 10},
            'parts': {
                'wide': {'primitive': 'box', 'width': '${w}', 'height': 5, 'depth': 5},
                'fixed': {'primitive': 'cylinder', 'radius': 3, 'height': 10},
            },
        }
        yaml_changed = {
            'parameters': {'w': 99},  # changed
            'parts': {
                'wide': {'primitive': 'box', 'width': '${w}', 'height': 5, 'depth': 5},
                'fixed': {'primitive': 'cylinder', 'radius': 3, 'height': 10},
            },
        }
        first = _build(yaml_base)
        second = _build(yaml_changed, old_state=first.state)

        # 'wide' depends on w → must rebuild; 'fixed' has no dependency → cached
        assert 'wide' in second._parts_builder.build_calls
        assert 'fixed' not in second._parts_builder.build_calls
        assert second.stats.rebuilt >= 1
        assert second.stats.cached >= 1

    def test_unchanged_operations_not_re_executed(self):
        yaml_data = {
            'parameters': {'r': 5},
            'parts': {'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20}},
            'operations': {'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1}},
        }
        yaml_unchanged = {
            'parameters': {'r': 5},
            'parts': {'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20}},
            'operations': {'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1}},
        }
        first = _build(yaml_data)
        second = _build(yaml_unchanged, old_state=first.state)

        assert second._ops_builder.execute_calls == []
        assert 'chamfered' in second.registry


# ─── Dirty propagation: parameter → part → operation ─────────────────────────

class TestIncrementalBuilderDirtyPropagation:

    def test_changed_part_dirties_downstream_operation(self):
        yaml_base = {
            'parameters': {'r': 5},
            'parts': {
                'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20},
                'base': {'primitive': 'box', 'width': 10, 'height': 10, 'depth': 2},
            },
            'operations': {
                'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1},
                'standalone': {'type': 'chamfer', 'input': 'base', 'distance': 0.5},
            },
        }
        yaml_changed = {
            'parameters': {'r': 99},  # changed — dirties cyl → chamfered, not standalone
            'parts': {
                'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20},
                'base': {'primitive': 'box', 'width': 10, 'height': 10, 'depth': 2},
            },
            'operations': {
                'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1},
                'standalone': {'type': 'chamfer', 'input': 'base', 'distance': 0.5},
            },
        }
        first = _build(yaml_base)
        second = _build(yaml_changed, old_state=first.state)

        assert 'cyl' in second._parts_builder.build_calls
        assert 'base' not in second._parts_builder.build_calls
        assert 'chamfered' in second._ops_builder.execute_calls
        assert 'standalone' not in second._ops_builder.execute_calls

    def test_three_level_chain_fully_dirty(self):
        """Changing a param dirties its part and ALL downstream ops."""
        yaml_base = {
            'parameters': {'r': 5},
            'parts': {'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20}},
            'operations': {
                'step1': {'type': 'chamfer', 'input': 'cyl', 'distance': 1},
                'step2': {'type': 'chamfer', 'input': 'step1', 'distance': 0.5},
            },
        }
        yaml_changed = {
            'parameters': {'r': 8},
            'parts': {'cyl': {'primitive': 'cylinder', 'radius': '${r}', 'height': 20}},
            'operations': {
                'step1': {'type': 'chamfer', 'input': 'cyl', 'distance': 1},
                'step2': {'type': 'chamfer', 'input': 'step1', 'distance': 0.5},
            },
        }
        first = _build(yaml_base)
        second = _build(yaml_changed, old_state=first.state)

        assert 'cyl' in second._parts_builder.build_calls
        assert 'step1' in second._ops_builder.execute_calls
        assert 'step2' in second._ops_builder.execute_calls


# ─── Structural changes: add/remove parts or operations ──────────────────────

class TestIncrementalBuilderStructuralChanges:

    def test_new_part_added(self):
        yaml_base = {
            'parameters': {},
            'parts': {'a': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1}},
        }
        yaml_with_new = {
            'parameters': {},
            'parts': {
                'a': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1},
                'b': {'primitive': 'cylinder', 'radius': 1, 'height': 1},  # new
            },
        }
        first = _build(yaml_base)
        second = _build(yaml_with_new, old_state=first.state)

        # Only 'b' was built fresh; 'a' should be cached
        assert 'b' in second._parts_builder.build_calls
        assert 'a' not in second._parts_builder.build_calls

    def test_new_operation_added(self):
        yaml_base = {
            'parameters': {},
            'parts': {'box': {'primitive': 'box', 'width': 5, 'height': 5, 'depth': 5}},
            'operations': {},
        }
        yaml_with_op = {
            'parameters': {},
            'parts': {'box': {'primitive': 'box', 'width': 5, 'height': 5, 'depth': 5}},
            'operations': {'chamfered': {'type': 'chamfer', 'input': 'box', 'distance': 1}},
        }
        first = _build(yaml_base)
        second = _build(yaml_with_op, old_state=first.state)

        assert 'chamfered' in second._ops_builder.execute_calls
        assert 'box' not in second._parts_builder.build_calls  # cached


# ─── Result structure ─────────────────────────────────────────────────────────

class TestIncrementalBuilderResult:

    def test_result_has_all_fields(self):
        yaml_data = {
            'parameters': {},
            'parts': {'box': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1}},
        }
        result = _build(yaml_data)

        assert result.registry is not None
        assert result.graph is not None
        assert result.state is not None
        assert result.state.graph is result.graph
        assert result.state.cache is not None
        assert result.stats is not None

    def test_stats_total_ms_positive(self):
        yaml_data = {
            'parameters': {},
            'parts': {'box': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1}},
        }
        result = _build(yaml_data)
        assert result.stats.total_ms >= 0

    def test_build_stats_repr(self):
        stats = BuildStats(rebuilt=3, cached=27, total_ms=140.0)
        r = repr(stats)
        assert "rebuilt=3" in r
        assert "cached=27" in r
        assert "90.0%" in r

    def test_state_is_passed_between_builds(self):
        yaml_data = {
            'parameters': {},
            'parts': {'box': {'primitive': 'box', 'width': 1, 'height': 1, 'depth': 1}},
        }
        first = _build(yaml_data)
        assert first.state.graph is not None
        assert first.state.cache is not None

        second = _build(yaml_data, old_state=first.state)
        # State should be a new snapshot (new graph object)
        assert second.state is not first.state
