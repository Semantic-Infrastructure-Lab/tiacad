"""Tests for testing/geometry_summary.py."""

import cadquery as cq
import pytest

from tiacad_core.geometry import CadQueryBackend, MockBackend
from tiacad_core.part import Part, PartRegistry
from tiacad_core.testing.geometry_summary import (
    GeometrySummaryError,
    summarize_part_geometry,
    summarize_part_registry,
)


class TestSummarizePartGeometry:
    """Test structured geometry summaries for individual parts."""

    def test_cadquery_part_summary_includes_metrics_and_mesh(self):
        backend = CadQueryBackend()
        part = Part(
            name="box",
            geometry=cq.Workplane("XY").box(10, 20, 30),
            backend=backend,
        )
        part.add_transform('translate', {'offset': [5, 0, 0]})

        summary = summarize_part_geometry(part)

        assert summary['name'] == 'box'
        assert summary['backend'] == 'CadQueryBackend'
        assert summary['extents']['x'] == pytest.approx(10.0, abs=0.01)
        assert summary['extents']['y'] == pytest.approx(20.0, abs=0.01)
        assert summary['extents']['z'] == pytest.approx(30.0, abs=0.01)
        assert summary['transform_count'] == 1
        assert summary['transform_types'] == ['translate']
        assert summary['metrics']['volume'] == pytest.approx(6000.0, rel=0.01)
        assert summary['metrics']['surface_area'] is not None
        assert summary['mesh']['available'] is True
        assert summary['mesh']['vertex_count'] > 0
        assert summary['mesh']['triangle_count'] > 0

    def test_mock_backend_summary_degrades_gracefully(self):
        backend = MockBackend()
        part = Part(
            name="mock_box",
            geometry=backend.create_box(10, 20, 30),
            backend=backend,
        )

        summary = summarize_part_geometry(part)

        assert summary['backend'] == 'MockBackend'
        assert summary['extents'] == {'x': 10.0, 'y': 30.0, 'z': 20.0}
        assert summary['metrics']['volume'] is None
        assert summary['metrics']['surface_area'] is None
        assert summary['mesh']['available'] is True
        assert summary['mesh']['vertex_count'] == 8
        assert summary['mesh']['triangle_count'] == 12

    def test_summary_can_skip_mesh(self):
        backend = MockBackend()
        part = Part(
            name="mock_box",
            geometry=backend.create_box(5, 5, 5),
            backend=backend,
        )

        summary = summarize_part_geometry(part, include_mesh=False)

        assert 'mesh' not in summary

    def test_invalid_part_raises_error(self):
        with pytest.raises(GeometrySummaryError, match="Part instance"):
            summarize_part_geometry("not a part")


class TestSummarizePartRegistry:
    """Test structured summaries across a registry."""

    def test_registry_summary_returns_all_parts(self):
        backend = MockBackend()
        registry = PartRegistry()
        registry.add(Part("a", backend.create_box(10, 10, 10), backend=backend))
        registry.add(Part("b", backend.create_cylinder(5, 20), backend=backend))

        summary = summarize_part_registry(registry, include_mesh=False)

        assert set(summary.keys()) == {'a', 'b'}
        assert summary['a']['name'] == 'a'
        assert summary['b']['name'] == 'b'

    def test_invalid_registry_raises_error(self):
        with pytest.raises(GeometrySummaryError, match="PartRegistry instance"):
            summarize_part_registry({})
