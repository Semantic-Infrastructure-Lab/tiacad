"""
Tests for InvalidationTracker — dirty set computation between graph snapshots.
"""

import pytest
from tiacad_core.dag.graph_builder import GraphBuilder
from tiacad_core.dag.invalidation_tracker import InvalidationTracker


def _build(yaml_data: dict):
    return GraphBuilder().build_graph(yaml_data)


class TestInvalidationTrackerBasics:

    def test_empty_graphs_no_dirty(self):
        old = _build({})
        new = _build({})
        tracker = InvalidationTracker(old)
        assert tracker.compute_dirty_set(new) == set()

    def test_identical_graphs_no_dirty(self):
        yaml_data = {
            'parameters': {'width': 100, 'height': 50},
            'parts': {'box': {'type': 'box', 'width': '${width}', 'height': '${height}', 'depth': 10}},
        }
        old = _build(yaml_data)
        new = _build(yaml_data)
        tracker = InvalidationTracker(old)
        assert tracker.compute_dirty_set(new) == set()

    def test_new_node_is_dirty(self):
        old = _build({'parameters': {'width': 100}})
        new = _build({'parameters': {'width': 100, 'height': 50}})
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)
        assert 'parameter:height' in dirty

    def test_deleted_node_in_deleted_set(self):
        old = _build({'parameters': {'width': 100, 'height': 50}})
        new = _build({'parameters': {'width': 100}})
        tracker = InvalidationTracker(old)
        deleted = tracker.compute_deleted_set(new)
        assert 'parameter:height' in deleted

    def test_deleted_node_not_in_dirty_set(self):
        old = _build({'parameters': {'width': 100, 'height': 50}})
        new = _build({'parameters': {'width': 100}})
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)
        # Deleted node is gone from new graph — not in dirty
        assert 'parameter:height' not in dirty


class TestInvalidationTrackerPropagation:

    def test_changed_parameter_dirties_dependent_part(self):
        yaml_base = {
            'parameters': {'width': 100},
            'parts': {'box': {'type': 'box', 'width': '${width}', 'height': 50, 'depth': 10}},
        }
        yaml_changed = {
            'parameters': {'width': 200},  # changed
            'parts': {'box': {'type': 'box', 'width': '${width}', 'height': 50, 'depth': 10}},
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)

        assert 'parameter:width' in dirty
        assert 'part:box' in dirty

    def test_unchanged_parameter_clean(self):
        yaml_data = {
            'parameters': {'width': 100, 'height': 50},
            'parts': {
                'wide': {'type': 'box', 'width': '${width}', 'height': 10, 'depth': 10},
                'tall': {'type': 'box', 'width': 10, 'height': '${height}', 'depth': 10},
            },
        }
        yaml_changed = {
            'parameters': {'width': 200, 'height': 50},  # only width changed
            'parts': {
                'wide': {'type': 'box', 'width': '${width}', 'height': 10, 'depth': 10},
                'tall': {'type': 'box', 'width': 10, 'height': '${height}', 'depth': 10},
            },
        }
        old = _build(yaml_data)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)

        assert 'parameter:width' in dirty
        assert 'part:wide' in dirty
        assert 'parameter:height' not in dirty
        assert 'part:tall' not in dirty

    def test_transitive_chain_fully_dirty(self):
        """Parameter → part → operation: changing parameter dirties all downstream."""
        yaml_base = {
            'parameters': {'radius': 5},
            'parts': {'cyl': {'type': 'cylinder', 'radius': '${radius}', 'height': 20}},
            'operations': {'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1}},
        }
        yaml_changed = {
            'parameters': {'radius': 8},  # changed
            'parts': {'cyl': {'type': 'cylinder', 'radius': '${radius}', 'height': 20}},
            'operations': {'chamfered': {'type': 'chamfer', 'input': 'cyl', 'distance': 1}},
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)

        assert 'parameter:radius' in dirty
        assert 'part:cyl' in dirty
        assert 'operation:chamfered' in dirty

    def test_independent_part_not_dirty(self):
        """Parts with no connection to changed parameter stay clean."""
        yaml_base = {
            'parameters': {'radius': 5},
            'parts': {
                'cyl': {'type': 'cylinder', 'radius': '${radius}', 'height': 20},
                'standalone': {'type': 'box', 'width': 10, 'height': 10, 'depth': 10},
            },
        }
        yaml_changed = {
            'parameters': {'radius': 8},
            'parts': {
                'cyl': {'type': 'cylinder', 'radius': '${radius}', 'height': 20},
                'standalone': {'type': 'box', 'width': 10, 'height': 10, 'depth': 10},
            },
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)

        assert 'part:standalone' not in dirty

    def test_sketch_operation_chain(self):
        """Changed sketch parameter propagates through sketch → operation."""
        yaml_base = {
            'parameters': {'profile_w': 50},
            'sketches': {
                'profile': {'type': 'rectangle', 'width': '${profile_w}', 'height': 20}
            },
            'operations': {
                'body': {'type': 'extrude', 'sketch': 'profile', 'depth': 100}
            },
        }
        yaml_changed = {
            'parameters': {'profile_w': 80},  # changed
            'sketches': {
                'profile': {'type': 'rectangle', 'width': '${profile_w}', 'height': 20}
            },
            'operations': {
                'body': {'type': 'extrude', 'sketch': 'profile', 'depth': 100}
            },
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        dirty = tracker.compute_dirty_set(new)

        assert 'parameter:profile_w' in dirty
        assert 'sketch:profile' in dirty
        assert 'operation:body' in dirty


class TestInvalidationTrackerReport:

    def test_full_report_structure(self):
        yaml_base = {
            'parameters': {'width': 100, 'height': 50},
            'parts': {'box': {'type': 'box', 'width': '${width}', 'height': '${height}', 'depth': 10}},
        }
        yaml_changed = {
            'parameters': {'width': 200, 'height': 50},  # width changed, height unchanged
            'parts': {'box': {'type': 'box', 'width': '${width}', 'height': '${height}', 'depth': 10}},
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        report = tracker.compute_full_report(new)

        assert 'added' in report
        assert 'deleted' in report
        assert 'modified' in report
        assert 'dirty' in report
        assert 'clean' in report
        assert 'hit_rate' in report

        assert 'parameter:width' in report['modified']
        assert 'parameter:height' not in report['modified']
        assert 'parameter:height' in report['clean']
        assert 0.0 < report['hit_rate'] < 1.0

    def test_full_report_all_clean(self):
        yaml_data = {'parameters': {'width': 100}}
        old = _build(yaml_data)
        new = _build(yaml_data)
        tracker = InvalidationTracker(old)
        report = tracker.compute_full_report(new)

        assert report['dirty'] == set()
        assert report['hit_rate'] == 1.0

    def test_full_report_hit_rate_partial(self):
        """Changing one param in a 4-node graph gives 50-75% hit rate."""
        yaml_base = {
            'parameters': {'a': 1, 'b': 2},
            'parts': {
                'p1': {'type': 'box', 'width': '${a}', 'height': 10, 'depth': 10},
                'p2': {'type': 'box', 'width': '${b}', 'height': 10, 'depth': 10},
            },
        }
        yaml_changed = {
            'parameters': {'a': 99, 'b': 2},  # only a changed
            'parts': {
                'p1': {'type': 'box', 'width': '${a}', 'height': 10, 'depth': 10},
                'p2': {'type': 'box', 'width': '${b}', 'height': 10, 'depth': 10},
            },
        }
        old = _build(yaml_base)
        new = _build(yaml_changed)
        tracker = InvalidationTracker(old)
        report = tracker.compute_full_report(new)

        # 4 nodes total, 2 dirty (parameter:a + part:p1), 2 clean
        assert report['hit_rate'] == 0.5
