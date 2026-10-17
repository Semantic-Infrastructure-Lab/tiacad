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
from tiacad_core.validation.rules.missing_position_rule import MissingPositionRule
from tiacad_core.validation.rules.unused_parts_rule import UnusedPartsRule
from tiacad_core.validation.rules.unused_parameters_rule import UnusedParametersRule


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
        """
        TCAD-VAL-8: guitar_hanger_with_holes.yaml has no genuinely orphaned
        part — 'beam' is listed in export.parts, so it's correctly *not*
        flagged. (Prior to the TCAD-VAL-8 fix, _get_used_parts/_get_exported_parts
        always returned empty sets due to a dict-vs-attribute mismatch, so
        every primitive looked unpositioned regardless of real usage — this
        test used to pass for the wrong reason.) Use a document with a truly
        unreferenced, unexported part to verify detection still works.
        """
        validator = AssemblyValidator()

        doc = TiaCADParser.parse_string("""
metadata:
  name: orphan_test
parts:
  used_box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  orphan_box:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center
operations:
  positioned:
    type: transform
    input: used_box
    transforms:
      - translate: [0, 0, 0]
export:
  default_part: positioned
""")

        report = validator.validate_document(doc)

        positioning_warnings = [
            i for i in report.issues
            if i.category == "positioning" and 'orphan_box' in (i.part_name or '').lower()
        ]

        assert len(positioning_warnings) > 0, "Should detect orphan_box not positioned"

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
        registry.add(Part("mock_box", backend.create_box(10, 30, 20), backend=backend))

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

    def test_hole_edge_proximity_non_cylindrical_cutter_is_not_a_round_hole(self):
        """A box-shaped cutter (slot/pocket) with a backend attached has no
        cylindrical face: it is not a round hole, so there is no radius (TCAD-VAL-14)."""
        backend = MockBackend()
        hole_part = Part("hole", backend.create_box(6, 20, 6), backend=backend)

        rule = HoleEdgeProximityRule()
        bbox = rule._get_bounding_box(hole_part)

        assert rule._get_hole_radius(hole_part, bbox) is None

    def test_hole_edge_proximity_without_backend_still_estimates_from_bbox(self):
        hole_part = Part("hole", cq.Workplane("XY").box(6, 6, 20))  # no backend attached

        rule = HoleEdgeProximityRule()
        bbox = rule._get_bounding_box(hole_part)

        assert rule._get_hole_radius(hole_part, bbox) == rule._estimate_hole_radius(bbox)

    def test_hole_edge_proximity_large_box_pocket_is_not_flagged(self):
        """Regression (TCAD-VAL-14): a 70 mm box pocket in a 74 mm part used to read as a
        'hole' of radius 35 sitting 2 mm from the edge."""
        backend = MockBackend()
        base = Part("base", backend.create_box(74, 20, 74), backend=backend)
        pocket = Part("pocket", backend.create_box(70, 10, 70), backend=backend)

        rule = HoleEdgeProximityRule()
        issues = rule._check_hole_proximity(
            "pocket", {"base": base, "pocket": pocket}, "base", rule._get_bounding_box(base)
        )

        assert issues == []

    def test_hole_edge_proximity_round_hole_near_edge_is_still_flagged(self):
        """Positive control: the rule can still fire for a real cylindrical hole."""
        backend = MockBackend()
        base = Part("base", backend.create_box(20, 20, 20), backend=backend)
        near_edge = backend.translate(backend.create_cylinder(radius=3, height=30), (8, 0, 0))
        hole = Part("hole", near_edge, backend=backend)

        rule = HoleEdgeProximityRule()
        issues = rule._check_hole_proximity(
            "hole", {"base": base, "hole": hole}, "base", rule._get_bounding_box(base)
        )

        assert len(issues) == 1


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

    def _fb_issues(self, backend, cutter_size, cutter_offset, base_size=(10, 10, 10)):
        base = Part("base", backend.create_box(*base_size), backend=backend)
        cutter = Part("cutter", backend.translate(backend.create_box(*cutter_size), cutter_offset), backend=backend)
        operation = {"type": "boolean", "operation": "difference", "base": "base", "subtract": ["cutter"]}
        return FeatureBoundsRule()._check_difference_op(operation, {"base": base, "cutter": cutter})

    def test_feature_bounds_open_top_pocket_is_not_reported(self, backend):
        """TCAD-VAL-14: overshooting one face with the other axes inside the base is a clean cut."""
        # 6x6 footprint centred, 8 tall, raised so it pokes out of the +Z face only
        assert self._fb_issues(backend, (6, 6, 8), (0, 0, 4)) == []

    def test_feature_bounds_through_hole_traversing_both_ends_is_not_reported(self, backend):
        assert self._fb_issues(backend, (4, 4, 30), (0, 0, 0)) == []

    def test_feature_bounds_corner_notch_poking_two_axes_is_still_reported(self, backend):
        assert len(self._fb_issues(backend, (6, 6, 6), (4, 4, 0))) == 1  # exits +X and +Y

    def test_feature_bounds_cutter_wholly_beyond_base_is_still_reported(self, backend):
        assert len(self._fb_issues(backend, (4, 4, 4), (20, 0, 0))) == 1  # removes nothing

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

    def test_bounding_box_issue_has_world_position(self, backend):
        """
        TCAD-2 follow-on: BoundingBoxRule issues should report world_position
        at the flagged part's own center, so a trust render can point
        directly at the degenerate/oversized part.
        """
        sliver = backend.create_box(10, 0.0001, 10)
        part = Part("sliver", sliver, backend=backend)

        rule = BoundingBoxRule()
        issues = rule._check_part_bbox("sliver", part)

        assert len(issues) == 1
        assert issues[0].world_position is not None
        assert issues[0].world_position == rule._part_center(part)

    def test_missing_position_issue_has_world_position(self):
        """
        TCAD-2 follow-on: MissingPositionRule issues should report
        world_position at the orphaned part's own (unpositioned) center,
        so a trust render can point at where it sits by default.

        'beam' in guitar_hanger_with_holes.yaml is exported, not orphaned, so
        (post TCAD-VAL-8 fix) it's no longer a valid orphan fixture — use a
        synthetic document with a genuinely unreferenced, unexported part.
        """
        doc = TiaCADParser.parse_string("""
metadata:
  name: orphan_test
parts:
  used_box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  orphan_box:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center
operations:
  positioned:
    type: transform
    input: used_box
    transforms:
      - translate: [0, 0, 0]
export:
  default_part: positioned
""")

        rule = MissingPositionRule()
        issues = rule.check(doc)

        orphan_issues = [i for i in issues if i.part_name == 'orphan_box']
        assert len(orphan_issues) == 1
        assert orphan_issues[0].world_position is not None
        expected = rule._part_center(doc.parts.get('orphan_box'))
        assert orphan_issues[0].world_position == expected

    def test_unused_parts_issue_has_world_position_and_catches_dead_end_operation(self):
        """
        TCAD-VAL-8: UnusedPartsRule now does real per-part/per-operation usage
        detection instead of only checking whether an export: section exists.
        It should catch both a truly orphaned base part (like MissingPositionRule)
        and a dead-end operation result — geometry that was built but whose
        output is never consumed by another operation or exported. That second
        case is the whole reason this rule is distinct from MissingPositionRule,
        which deliberately filters operation results out.
        """
        doc = TiaCADParser.parse_string("""
metadata:
  name: unused_parts_test
parts:
  used_box:
    primitive: box
    parameters: {width: 10, height: 10, depth: 10}
    origin: center
  orphan_box:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center
  feeder_box:
    primitive: box
    parameters: {width: 3, height: 3, depth: 3}
    origin: center
operations:
  positioned:
    type: transform
    input: used_box
    transforms:
      - translate: [0, 0, 0]
  dead_end:
    type: transform
    input: feeder_box
    transforms:
      - translate: [1, 1, 1]
export:
  default_part: positioned
""")

        rule = UnusedPartsRule()
        issues = rule.check(doc)
        flagged = {i.part_name for i in issues}

        assert flagged == {'orphan_box', 'dead_end'}
        for issue in issues:
            assert issue.world_position is not None
            assert issue.world_position == rule._part_center(doc.parts.get(issue.part_name))

    def test_underscore_prefixed_placeholder_not_flagged_as_unused_or_unpositioned(self):
        """
        TCAD-BUG-4: sketch-only designs (revolve/extrude/sweep/loft/hull) are
        currently required to declare a `parts:` block even though the real
        geometry comes from the sketch operation — YAML_REFERENCE.md's
        documented workaround is a placeholder part named with a leading
        underscore (`_placeholder`, `_dummy` — see examples/bottle_revolve.yaml,
        examples/egg.yaml, examples/text_simple.yaml). That placeholder used to
        get flagged by both UnusedPartsRule and MissingPositionRule every
        single time, permanently, for every sketch-only file — 2 spurious
        "dead work" warnings baked into the validation baseline. Both rules
        should recognize the convention and stay silent for it.
        """
        doc = TiaCADParser.parse_string("""
metadata:
  name: placeholder_test
parts:
  _placeholder:
    primitive: box
    parameters: {width: 1, height: 1, depth: 1}
  real_orphan:
    primitive: box
    parameters: {width: 5, height: 5, depth: 5}
    origin: center
""")

        unused_flagged = {i.part_name for i in UnusedPartsRule().check(doc)}
        missing_pos_flagged = {i.part_name for i in MissingPositionRule().check(doc)}

        assert '_placeholder' not in unused_flagged
        assert '_placeholder' not in missing_pos_flagged
        # A genuinely unreferenced part must still be caught -- this isn't a
        # blanket suppression, only underscore-prefixed names are exempt.
        assert 'real_orphan' in unused_flagged
        assert 'real_orphan' in missing_pos_flagged

    def test_unused_parameters_rule_flags_dead_parameters_not_live_ones(self):
        """
        TCAD-BUG-2: a file can declare `parameters:` that look load-bearing
        (plausible names, sane values) while nothing in the sketch/parts
        actually references them via ${...} -- the exact shape of the bug
        found building examples/egg.yaml's first draft, where `length`,
        `max_diameter`, and `blunt_fraction` were declared but the sketch's
        points were 49 hardcoded literals. `tiacad validate` reported this
        as a perfectly fine parametric file. UnusedParametersRule should
        flag the dead ones and stay silent on parameters that are actually
        referenced -- including a parameter referenced only from within
        another parameter's own definition, which is a legitimate dependency,
        not dead work.
        """
        doc = TiaCADParser.parse_string("""
metadata:
  name: unused_parameters_test
parameters:
  live_width: 10
  dead_length: 58
  derived_from_live: "${live_width * 2}"
parts:
  box:
    primitive: box
    parameters: {width: 5, height: 5, depth: "${derived_from_live}"}
    origin: center
export:
  default_part: box
""")

        issues = UnusedParametersRule().check(doc)
        flagged = {i.message.split("'")[1] for i in issues}

        # live_width is never referenced directly by any part -- only from
        # within derived_from_live's own definition -- and must NOT be
        # flagged: that's a legitimate dependency chain, not dead work.
        assert flagged == {'dead_length'}
        assert issues[0].severity == Severity.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
