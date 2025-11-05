"""
Tests for SelectorResolver - Geometric feature selection
"""

import pytest
import cadquery as cq
from tiacad_core.selector_resolver import SelectorResolver, FeatureType, parse_selector


class TestParseSelector:
    """Test selector parsing without geometry"""

    def test_parse_simple_selector(self):
        """Parse simple directional selector"""
        result = parse_selector(">Z")
        assert result == {'type': 'simple', 'parts': ['>Z']}

    def test_parse_and_combinator(self):
        """Parse AND combinator"""
        result = parse_selector("|Z and >X")
        assert result == {'type': 'and', 'parts': ['|Z', '>X']}

    def test_parse_or_combinator(self):
        """Parse OR combinator"""
        result = parse_selector(">Z or <Z")
        assert result == {'type': 'or', 'parts': ['>Z', '<Z']}

    def test_parse_not_combinator(self):
        """Parse NOT combinator"""
        result = parse_selector("not <Z")
        assert result == {'type': 'not', 'parts': ['<Z']}

    def test_parse_with_whitespace(self):
        """Parse selector with extra whitespace"""
        result = parse_selector("  |Z   and   >X  ")
        assert result == {'type': 'and', 'parts': ['|Z', '>X']}


class TestSelectorResolverSimple:
    """Test simple selector resolution"""

    def setup_method(self):
        """Create test geometry - simple box"""
        self.box = cq.Workplane("XY").box(10, 10, 10)
        self.resolver = SelectorResolver(self.box)

    def test_select_top_face(self):
        """Select top face with >Z"""
        result = self.resolver.resolve(">Z", FeatureType.FACE)
        assert len(result) == 1
        # Top face should be at z=5
        center = result[0].Center()
        assert abs(center.z - 5.0) < 0.001

    def test_select_bottom_face(self):
        """Select bottom face with <Z"""
        result = self.resolver.resolve("<Z", FeatureType.FACE)
        assert len(result) == 1
        # Bottom face should be at z=-5
        center = result[0].Center()
        assert abs(center.z - (-5.0)) < 0.001

    def test_select_front_face(self):
        """Select front face with >Y"""
        result = self.resolver.resolve(">Y", FeatureType.FACE)
        assert len(result) == 1
        center = result[0].Center()
        assert abs(center.y - 5.0) < 0.001

    def test_select_right_face(self):
        """Select right face with >X"""
        result = self.resolver.resolve(">X", FeatureType.FACE)
        assert len(result) == 1
        center = result[0].Center()
        assert abs(center.x - 5.0) < 0.001

    def test_select_vertical_edges(self):
        """Select vertical edges with |Z"""
        result = self.resolver.resolve("|Z", FeatureType.EDGE)
        # Box has 4 vertical edges
        assert len(result) == 4

    def test_select_horizontal_edges_x(self):
        """Select horizontal edges parallel to X with |X"""
        result = self.resolver.resolve("|X", FeatureType.EDGE)
        # Box has 4 edges parallel to X
        assert len(result) == 4

    def test_invalid_simple_selector(self):
        """Invalid selector should raise error"""
        with pytest.raises(ValueError, match="Invalid simple selector"):
            self.resolver.resolve("invalid", FeatureType.FACE)

    def test_unsupported_feature_type(self):
        """Unsupported feature type should raise error"""
        with pytest.raises(ValueError, match="Unsupported feature type"):
            self.resolver.resolve(">Z", FeatureType.VERTEX)


class TestSelectorResolverAnd:
    """Test AND combinator"""

    def setup_method(self):
        """Create test geometry"""
        self.box = cq.Workplane("XY").box(20, 20, 20)
        self.resolver = SelectorResolver(self.box)

    def test_and_combinator_edges(self):
        """Select edges that are both vertical AND on right side"""
        # This should select vertical edges on the +X face
        result = self.resolver.resolve("|Z and >X", FeatureType.EDGE)
        # Should get 2 vertical edges on the right face
        assert len(result) == 2

    def test_and_combinator_no_match(self):
        """AND with incompatible conditions returns empty"""
        # Can't be both top and bottom face
        result = self.resolver.resolve(">Z and <Z", FeatureType.FACE)
        assert len(result) == 0

    def test_and_invalid_multiple(self):
        """Multiple AND operators should raise error"""
        with pytest.raises(ValueError, match="Expected exactly one 'and'"):
            self.resolver.resolve(">Z and >X and >Y", FeatureType.FACE)


class TestSelectorResolverOr:
    """Test OR combinator"""

    def setup_method(self):
        """Create test geometry"""
        self.box = cq.Workplane("XY").box(10, 10, 10)
        self.resolver = SelectorResolver(self.box)

    def test_or_combinator_faces(self):
        """Select top OR bottom faces"""
        result = self.resolver.resolve(">Z or <Z", FeatureType.FACE)
        # Should get both top and bottom faces
        assert len(result) == 2

    def test_or_combinator_edges(self):
        """Select edges parallel to X OR Y"""
        result = self.resolver.resolve("|X or |Y", FeatureType.EDGE)
        # Box has 4 edges parallel to X and 4 parallel to Y
        assert len(result) == 8

    def test_or_invalid_multiple(self):
        """Multiple OR operators should raise error"""
        with pytest.raises(ValueError, match="Expected exactly one 'or'"):
            self.resolver.resolve(">Z or >X or >Y", FeatureType.FACE)


class TestSelectorResolverNot:
    """Test NOT combinator"""

    def setup_method(self):
        """Create test geometry"""
        self.box = cq.Workplane("XY").box(10, 10, 10)
        self.resolver = SelectorResolver(self.box)

    def test_not_combinator_faces(self):
        """Select all faces EXCEPT bottom"""
        result = self.resolver.resolve("not <Z", FeatureType.FACE)
        # Box has 6 faces, excluding bottom = 5 faces
        assert len(result) == 5

        # Verify bottom face is NOT in results
        for face in result:
            center = face.Center()
            assert center.z > -4.5  # Not the bottom face at z=-5

    def test_not_combinator_edges(self):
        """Select all edges EXCEPT vertical ones"""
        result = self.resolver.resolve("not |Z", FeatureType.EDGE)
        # Box has 12 edges, 4 are vertical, so 8 should remain
        assert len(result) == 8

    def test_not_unsupported_feature_type(self):
        """NOT with unsupported feature type should raise error"""
        with pytest.raises(ValueError, match="Unsupported feature type"):
            self.resolver.resolve("not >Z", FeatureType.VERTEX)


class TestSelectorResolverComplex:
    """Test complex geometry"""

    def setup_method(self):
        """Create more complex test geometry"""
        # Box with chamfered edges on top
        self.part = (
            cq.Workplane("XY")
            .box(20, 20, 10)
            .edges(">Z")
            .chamfer(1)
        )
        self.resolver = SelectorResolver(self.part)

    def test_complex_geometry_top_face(self):
        """Select top face from chamfered box"""
        result = self.resolver.resolve(">Z", FeatureType.FACE)
        # Should still have a top face (now smaller due to chamfer)
        assert len(result) >= 1

    def test_complex_geometry_edges(self):
        """Select edges from chamfered box"""
        result = self.resolver.resolve("|Z", FeatureType.EDGE)
        # Should have vertical edges
        assert len(result) >= 4


class TestSelectorResolverEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        """Create test geometry"""
        self.box = cq.Workplane("XY").box(10, 10, 10)
        self.resolver = SelectorResolver(self.box)

    def test_whitespace_handling(self):
        """Selector with extra whitespace should work"""
        result = self.resolver.resolve("  >Z  ", FeatureType.FACE)
        assert len(result) == 1

    def test_and_with_whitespace(self):
        """AND combinator with various whitespace"""
        result1 = self.resolver.resolve("|Z and >X", FeatureType.EDGE)
        result2 = self.resolver.resolve("|Z  and  >X", FeatureType.EDGE)
        assert len(result1) == len(result2)

    def test_empty_intersection(self):
        """AND that results in empty set"""
        result = self.resolver.resolve(">Z and <Z", FeatureType.FACE)
        assert len(result) == 0

    def test_full_union(self):
        """OR with multiple operators should fail"""
        # Note: Multiple OR operators should fail with "Expected exactly one 'or'"
        # which is correct behavior
        with pytest.raises(ValueError, match="Expected exactly one 'or'"):
            self.resolver.resolve("|X or |Y or |Z", FeatureType.EDGE)


class TestSelectorResolverRegex:
    """Test regex pattern matching"""

    def setup_method(self):
        """Create test geometry"""
        self.box = cq.Workplane("XY").box(10, 10, 10)
        self.resolver = SelectorResolver(self.box)

    def test_has_and_detection(self):
        """Test AND combinator detection"""
        assert self.resolver._has_and("|Z and >X")
        assert not self.resolver._has_and(">Z")
        assert not self.resolver._has_and(">Z or <Z")

    def test_has_or_detection(self):
        """Test OR combinator detection"""
        assert self.resolver._has_or(">Z or <Z")
        assert not self.resolver._has_or(">Z")
        assert not self.resolver._has_or(">Z and <Z")

    def test_has_not_detection(self):
        """Test NOT combinator detection"""
        assert self.resolver._has_not("not >Z")
        assert not self.resolver._has_not(">Z")
        assert not self.resolver._has_not("cannot >Z")  # 'not' must be at start
