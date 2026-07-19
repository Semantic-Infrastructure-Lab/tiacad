"""
Unit tests for TiaCAD Assembly Validator

Tests validation of common design issues:
- Disconnected parts
- Missing positions
- Invalid parameters
- Geometric issues
"""

import pytest
import cadquery as cq
from tiacad_core.geometry import MockBackend
from tiacad_core.geometry.cadquery_backend import CadQueryBackend
from tiacad_core.part import Part, PartRegistry
from tiacad_core.validation.assembly_validator import (
    AssemblyValidator,
    ValidationReport,
    ValidationIssue,
    Severity
)
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.validation.rules.bounding_box_rule import BoundingBoxRule
from tiacad_core.validation.rules.hole_edge_proximity_rule import HoleEdgeProximityRule
from tiacad_core.validation.rules.boolean_gaps_rule import BooleanGapsRule
from tiacad_core.validation.rules.disconnected_parts_rule import DisconnectedPartsRule
from tiacad_core.validation.rules.feature_bounds_rule import FeatureBoundsRule


class TestValidationIssue:
    """Test ValidationIssue data structure"""

    def test_create_issue(self):
        issue = ValidationIssue(
            severity=Severity.ERROR,
            category="geometry",
            message="Test error",
            part_name="test_part",
            suggestion="Fix it"
        )

        assert issue.severity == Severity.ERROR
        assert issue.category == "geometry"
        assert issue.message == "Test error"
        assert issue.part_name == "test_part"
        assert issue.suggestion == "Fix it"

    def test_issue_to_string(self):
        issue = ValidationIssue(
            severity=Severity.WARNING,
            category="connectivity",
            message="Parts disconnected",
            suggestion="Check positions"
        )

        result = str(issue)
        assert "[WARNING]" in result
        assert "(connectivity)" in result
        assert "Parts disconnected" in result
        assert "Check positions" in result

    def test_issue_to_dict(self):
        issue = ValidationIssue(
            severity=Severity.INFO,
            category="parameters",
            message="Info message"
        )

        d = issue.to_dict()
        assert d['severity'] == "INFO"
        assert d['category'] == "parameters"
        assert d['message'] == "Info message"


class TestValidationReport:
    """Test ValidationReport functionality"""

    def test_empty_report(self):
        report = ValidationReport()

        assert report.error_count == 0
        assert report.warning_count == 0
        assert report.info_count == 0
        assert report.passed is True
        assert len(report.issues) == 0

    def test_add_issues(self):
        report = ValidationReport()

        report.add_issue(ValidationIssue(
            severity=Severity.ERROR,
            category="test",
            message="Error 1"
        ))

        report.add_issue(ValidationIssue(
            severity=Severity.WARNING,
            category="test",
            message="Warning 1"
        ))

        report.add_issue(ValidationIssue(
            severity=Severity.INFO,
            category="test",
            message="Info 1"
        ))

        assert report.error_count == 1
        assert report.warning_count == 1
        assert report.info_count == 1
        assert report.passed is False

    def test_report_to_json(self):
        report = ValidationReport()
        report.add_issue(ValidationIssue(
            severity=Severity.ERROR,
            category="test",
            message="Test"
        ))

        json_str = report.to_json()
        assert "ERROR" in json_str
        assert "test" in json_str
        assert "passed" in json_str
        assert "false" in json_str.lower()


class TestAssemblyValidator:
    """Test AssemblyValidator core functionality"""

    def test_create_validator(self):
        validator = AssemblyValidator()
        assert validator.tolerance == 0.1

        validator_custom = AssemblyValidator(tolerance=0.5)
        assert validator_custom.tolerance == 0.5

    def test_parameter_sanity_negative_dimensions(self):
        """Test detection of negative dimensions"""

        class MockDoc:
            parameters = {
                'width': -10,
                'height': 20,
                'length': -5
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1  # Should catch negative width
        assert any('width' in i.message.lower() for i in errors)

    def test_parameter_sanity_zero_dimensions(self):
        """Test detection of zero dimensions"""

        class MockDoc:
            parameters = {
                'beam_width': 0,
                'height': 20
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1
        assert any('beam_width' in i.message for i in errors)

    def test_parameter_sanity_valid_dimensions(self):
        """Test that valid dimensions pass"""

        class MockDoc:
            parameters = {
                'width': 100,
                'height': 75,
                'depth': 10
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_parameter_sanity_suspiciously_small(self):
        """Test detection of suspiciously small dimensions"""

        class MockDoc:
            parameters = {
                'width': 0.001,  # Very small but not zero
                'height': 20
            }

        validator = AssemblyValidator()
        issues = validator.check_parameter_sanity(MockDoc())

        warnings = [i for i in issues if i.severity == Severity.WARNING]
        assert len(warnings) >= 1
        assert any('small' in i.message.lower() for i in warnings)


class TestValidatorIntegration:
    """Integration tests using real YAML files"""

    def test_validate_color_demo(self):
        """Test validation on working color demo file"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/color_demo.yaml')

        report = validator.validate_document(doc)

        # Should have no critical errors
        assert report.error_count == 0

    def test_validate_multi_material_demo(self):
        """Test validation on working multi-material demo"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/multi_material_demo.yaml')

        report = validator.validate_document(doc)

        # Should have no critical errors
        assert report.error_count == 0

    def test_validate_guitar_hanger_broken(self):
        """Test validation catches issues in broken guitar hanger"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/guitar_hanger_with_holes.yaml')

        report = validator.validate_document(doc)

        # Should detect missing beam position
        positioning_warnings = [
            i for i in report.issues
            if i.category == "positioning" and 'beam' in (i.part_name or '').lower()
        ]

        assert len(positioning_warnings) > 0, "Should detect beam not positioned"

    def test_validate_guitar_hanger_fixed(self):
        """Test validation on fixed guitar hanger"""
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_file('examples/guitar_hanger_named_points.yaml')

        report = validator.validate_document(doc)

        # Fixed design should pass (no errors, warnings are OK)
        assert report.error_count == 0


class TestBackendAwareValidation:
    """Validation helpers should work with backend-aware Part objects."""

    def test_bounding_box_rule_supports_mock_backend_part(self):
        backend = MockBackend()
        registry = PartRegistry()
        registry.add(Part("mock_box", backend.create_box(10, 20, 30), backend=backend))

        class MockDoc:
            parts = registry

        issues = BoundingBoxRule().check(MockDoc())
        errors = [issue for issue in issues if issue.severity == Severity.WARNING]

        assert errors == []

    def test_hole_edge_proximity_uses_real_radius_not_bbox_estimate(self):
        """A tall, narrow hole should use its true BREP radius, not the
        larger bbox-derived estimate (max half-dimension), when a backend
        is attached."""
        backend = MockBackend()
        # radius=3 but height=20 -> bbox half-dimension estimate would be 10,
        # more than 3x the real radius.
        hole_part = Part("hole", backend.create_cylinder(radius=3, height=20), backend=backend)

        rule = HoleEdgeProximityRule()
        bbox = rule._get_bounding_box(hole_part)
        radius = rule._get_hole_radius(hole_part, bbox)

        assert radius == 3
        assert rule._estimate_hole_radius(bbox) == 10, "sanity check: bbox estimate would have been wrong"

    def test_hole_edge_proximity_falls_back_to_bbox_for_non_cylindrical_geometry(self):
        """Geometry with no cylindrical face (e.g. a slot cut from a box)
        has nothing for the backend to query -> bbox estimate."""
        backend = MockBackend()
        hole_part = Part("hole", backend.create_box(6, 6, 20), backend=backend)

        rule = HoleEdgeProximityRule()
        bbox = rule._get_bounding_box(hole_part)
        radius = rule._get_hole_radius(hole_part, bbox)

        assert radius == rule._estimate_hole_radius(bbox)


class TestConnectivityChecks:
    """Test disconnected parts detection"""

    def test_find_connected_components_simple(self):
        """Test connected component detection with simple graph"""
        validator = AssemblyValidator()

        # Graph: A-B, C-D (two components)
        adjacency = {
            'A': {'B'},
            'B': {'A'},
            'C': {'D'},
            'D': {'C'}
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 2
        assert {'A', 'B'} in components
        assert {'C', 'D'} in components

    def test_find_connected_components_all_connected(self):
        """Test when all parts are connected"""
        validator = AssemblyValidator()

        # Graph: A-B-C (one component)
        adjacency = {
            'A': {'B'},
            'B': {'A', 'C'},
            'C': {'B'}
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 1
        assert components[0] == {'A', 'B', 'C'}

    def test_find_connected_components_isolated(self):
        """Test detection of isolated parts"""
        validator = AssemblyValidator()

        # Graph: A-B, C (isolated), D (isolated)
        adjacency = {
            'A': {'B'},
            'B': {'A'},
            'C': set(),
            'D': set()
        }

        components = validator._find_connected_components(adjacency)

        assert len(components) == 3  # A-B (connected), C (isolated), D (isolated)
        assert {'A', 'B'} in components
        assert {'C'} in components
        assert {'D'} in components


def test_validation_report_summary(capsys):
    """Test that validation report prints correctly"""
    report = ValidationReport()

    report.add_issue(ValidationIssue(
        severity=Severity.ERROR,
        category="test",
        message="Test error"
    ))

    report.add_issue(ValidationIssue(
        severity=Severity.WARNING,
        category="test",
        message="Test warning"
    ))

    report.print_summary()

    captured = capsys.readouterr()
    assert "ERRORS" in captured.out
    assert "WARNINGS" in captured.out
    assert "Test error" in captured.out
    assert "Test warning" in captured.out


class TestBrepGeometryValidation:
    """
    Rules that switched from bbox heuristics to real BREP distance/volume
    queries (TCAD-ARCH-7): boolean_gaps_rule, disconnected_parts_rule,
    feature_bounds_rule. Uses real CadQueryBackend geometry, since the
    whole point is a case where the bbox estimate would be wrong.
    """

    @pytest.fixture
    def backend(self):
        return CadQueryBackend()

    def test_boolean_gaps_uses_real_distance_for_touching_l_shape(self, backend):
        """
        An L-shaped base (two boxes fused) has a non-convex bbox. A part
        placed in the bbox's "notch" reads as bbox-close even though it
        doesn't actually touch the L-shape -- bbox would false-negative
        (miss the gap). Real distance() must still catch it.
        """
        arm1 = backend.create_box(10, 10, 10)
        arm2 = backend.translate(backend.create_box(10, 10, 10), (10, 10, 0))
        l_shape = backend.boolean_union(arm1, arm2)
        # Sits in the notch of the L: within the combined bbox, but not
        # touching either arm.
        notch_part = backend.translate(backend.create_box(4, 4, 4), (10, 0, 0))

        base_part = Part("l_shape", l_shape, backend=backend)
        add_part = Part("notch", notch_part, backend=backend)

        rule = BooleanGapsRule()
        base_bbox = rule._get_bounding_box(base_part)
        add_bbox = rule._get_bounding_box(add_part)

        assert rule._boxes_are_close(base_bbox, add_bbox), \
            "sanity check: bbox heuristic should think these are close/touching"

        gap = rule._get_gap(base_part, add_part, base_bbox, add_bbox)
        assert gap > 0, "real BREP distance should catch the gap bbox missed"

    def test_boolean_gaps_falls_back_to_bbox_without_backend(self):
        base_part = Part("base", cq.Workplane("XY").box(10, 10, 10))  # no backend attached
        add_part = Part("add", cq.Workplane("XY").box(10, 10, 10).translate((15, 0, 0)))

        rule = BooleanGapsRule()
        base_bbox = rule._get_bounding_box(base_part)
        add_bbox = rule._get_bounding_box(add_part)
        gap = rule._get_gap(base_part, add_part, base_bbox, add_bbox)

        assert gap == rule._calculate_bbox_gap(base_bbox, add_bbox)

    def test_disconnected_parts_real_distance_catches_l_shape_gap(self, backend):
        """Same non-convex-bbox trap as above, exercised via the connectivity rule."""
        arm1 = backend.create_box(10, 10, 10)
        arm2 = backend.translate(backend.create_box(10, 10, 10), (10, 10, 0))
        l_shape = backend.boolean_union(arm1, arm2)
        notch_part = backend.translate(backend.create_box(4, 4, 4), (10, 0, 0))

        p1 = Part("l_shape", l_shape, backend=backend)
        p2 = Part("notch", notch_part, backend=backend)

        rule = DisconnectedPartsRule()
        bbox1 = rule._get_bounding_box(p1.geometry)
        bbox2 = rule._get_bounding_box(p2.geometry)

        assert rule._boxes_are_close(bbox1, bbox2), \
            "sanity check: bbox heuristic should think these are connected"
        assert not rule._are_connected(p1, p2, bbox1, bbox2), \
            "real BREP distance should show these parts are not actually touching"

    def test_feature_bounds_real_check_catches_bbox_false_negative(self, backend):
        """
        L-shaped base: a feature sitting in the L's empty notch is fully
        within the *combined* bbox (so `_bound_overflows` finds nothing
        to flag) while being 100% outside the real solid. The real
        cut-volume check must run independently of that bbox pre-check
        to catch this, or it's silently skipped.
        """
        arm1 = backend.create_box(10, 10, 10)
        arm2 = backend.translate(backend.create_box(10, 10, 10), (10, 10, 0))
        l_shape = backend.boolean_union(arm1, arm2)
        notch_hole = backend.translate(backend.create_box(2, 2, 2), (10, 0, 0))

        base_part = Part("l_shape", l_shape, backend=backend)
        subtract_part = Part("hole", notch_hole, backend=backend)

        rule = FeatureBoundsRule()
        base_bbox = rule._get_bounding_box(base_part)
        subtract_bbox = rule._get_bounding_box(subtract_part)
        overflows = rule._bound_overflows(subtract_bbox, base_bbox, rule.constants.FEATURE_EXTENSION_TOLERANCE)

        assert overflows == [], "sanity check: bbox pre-check should find nothing to flag here"
        assert rule._really_overflows(base_part, subtract_part, overflows) is True

    def test_feature_bounds_real_check_confirms_true_positive(self, backend):
        base = backend.create_box(10, 10, 10)
        poking_hole = backend.translate(backend.create_box(4, 4, 4), (9, 0, 0))

        base_part = Part("base", base, backend=backend)
        subtract_part = Part("hole", poking_hole, backend=backend)

        rule = FeatureBoundsRule()
        assert rule._really_overflows(base_part, subtract_part, ["X-max by 3.00mm"]) is True

    def test_feature_bounds_falls_back_to_bbox_without_backend(self):
        base_part = Part("base", cq.Workplane("XY").box(10, 10, 10))
        subtract_part = Part("hole", cq.Workplane("XY").box(4, 4, 4).translate((9, 0, 0)))

        rule = FeatureBoundsRule()
        assert rule._really_overflows(base_part, subtract_part, ["X-max by 3.00mm"]) is True
        assert rule._really_overflows(base_part, subtract_part, []) is False

    def test_feature_bounds_issue_has_world_position(self, backend):
        """
        TCAD-UX-5 follow-on: FeatureBoundsRule issues should report
        world_position at the offending feature (subtract part), not the
        base, so a trust render can point directly at what overflowed.
        """
        base = backend.create_box(10, 10, 10)
        poking_hole = backend.translate(backend.create_box(4, 4, 4), (9, 0, 0))

        base_part = Part("base", base, backend=backend)
        subtract_part = Part("hole", poking_hole, backend=backend)
        parts_dict = {"base": base_part, "hole": subtract_part}

        operation = {
            "type": "boolean",
            "operation": "difference",
            "base": "base",
            "subtract": ["hole"],
        }

        rule = FeatureBoundsRule()
        issues = rule._check_difference_op(operation, parts_dict)

        assert len(issues) == 1
        assert issues[0].world_position is not None
        expected = rule._part_center(subtract_part)
        assert issues[0].world_position == expected

    def test_boolean_gaps_issue_has_world_position_at_midpoint(self, backend):
        """
        TCAD-UX-5 follow-on: BooleanGapsRule issues should report
        world_position as the midpoint between the two parts, since the
        gap itself sits between them rather than inside either part.
        """
        base = backend.create_box(10, 10, 10)
        add = backend.translate(backend.create_box(10, 10, 10), (15, 0, 0))

        base_part = Part("base", base, backend=backend)
        add_part = Part("add", add, backend=backend)
        parts_dict = {"base": base_part, "add": add_part}

        operation = {
            "type": "boolean",
            "operation": "union",
            "base": "base",
            "add": ["add"],
        }

        rule = BooleanGapsRule()
        issues = rule._check_union_gap("union1", operation, parts_dict)

        assert len(issues) == 1
        assert issues[0].world_position is not None
        expected = rule._gap_midpoint(base_part, add_part)
        assert issues[0].world_position == expected
        # Sanity: midpoint should sit between the two part centers on X.
        assert 0 < issues[0].world_position[0] < 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
