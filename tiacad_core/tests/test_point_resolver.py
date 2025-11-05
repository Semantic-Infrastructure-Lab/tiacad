"""
Tests for PointResolver - Point expression resolution

Tests cover:
1. Absolute coordinates [x, y, z]
2. Dot notation parsing and resolution
3. Offset notation {from: ..., offset: [...]}
4. Error handling and validation
5. Integration with Part and SelectorResolver
"""

import pytest
import cadquery as cq
from tiacad_core.point_resolver import PointResolver, PointResolverError
from tiacad_core.part import Part, PartRegistry


@pytest.fixture
def registry_with_parts():
    """Create registry with test parts"""
    registry = PartRegistry()

    # Create a beam at origin
    beam = cq.Workplane("XY").box(100, 50, 25).translate((0, 0, 0))
    registry.add(Part(name="beam", geometry=beam))

    # Create an arm offset from origin
    arm = cq.Workplane("XY").box(22, 70, 16).translate((0, 72.5, 0))
    registry.add(Part(name="arm", geometry=arm))

    return registry


@pytest.fixture
def resolver(registry_with_parts):
    """Create resolver with test parts"""
    return PointResolver(registry_with_parts)


# =============================================================================
# Test Absolute Coordinates
# =============================================================================

class TestAbsoluteCoordinates:
    """Test resolution of absolute coordinates [x, y, z]"""

    def test_resolve_simple_coordinates(self, resolver):
        """Test resolving basic [x, y, z] coordinates"""
        result = resolver.resolve([10, 20, 30])
        assert result == (10.0, 20.0, 30.0)

    def test_resolve_negative_coordinates(self, resolver):
        """Test negative coordinates"""
        result = resolver.resolve([-5, -10, -15])
        assert result == (-5.0, -10.0, -15.0)

    def test_resolve_zero_coordinates(self, resolver):
        """Test zero coordinates"""
        result = resolver.resolve([0, 0, 0])
        assert result == (0.0, 0.0, 0.0)

    def test_resolve_float_coordinates(self, resolver):
        """Test floating point coordinates"""
        result = resolver.resolve([1.5, 2.7, 3.9])
        assert result == (1.5, 2.7, 3.9)

    def test_invalid_coordinate_count(self, resolver):
        """Test error when not exactly 3 coordinates"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve([10, 20])
        assert "exactly 3 values" in str(exc.value)

    def test_invalid_coordinate_type(self, resolver):
        """Test error when coordinates are not numeric"""
        with pytest.raises(PointResolverError):
            resolver.resolve(["a", "b", "c"])


# =============================================================================
# Test Dot Notation Parsing
# =============================================================================

class TestDotNotationParsing:
    """Test parsing of dot notation expressions"""

    def test_parse_basic_face_center(self, resolver):
        """Test parsing 'part.face(selector).center'"""
        parsed = resolver._parse_dot_notation("beam.face('>Z').center")
        assert parsed['part'] == 'beam'
        assert parsed['feature'] == 'face'
        assert parsed['selector'] == '>Z'
        assert parsed['location'] == 'center'

    def test_parse_edge_start(self, resolver):
        """Test parsing edge with start location"""
        parsed = resolver._parse_dot_notation("arm.edge('|Z').start")
        assert parsed['part'] == 'arm'
        assert parsed['feature'] == 'edge'
        assert parsed['selector'] == '|Z'
        assert parsed['location'] == 'start'

    def test_parse_with_whitespace(self, resolver):
        """Test parsing handles extra whitespace"""
        parsed = resolver._parse_dot_notation("  beam.face('>Z').center  ")
        assert parsed['part'] == 'beam'

    def test_invalid_format_no_feature(self, resolver):
        """Test error on missing feature"""
        with pytest.raises(PointResolverError) as exc:
            resolver._parse_dot_notation("beam.center")
        assert "Invalid dot notation" in str(exc.value)

    def test_invalid_format_no_selector(self, resolver):
        """Test error on missing selector"""
        with pytest.raises(PointResolverError):
            resolver._parse_dot_notation("beam.face().center")

    def test_invalid_feature_type(self, resolver):
        """Test error on unknown feature type"""
        with pytest.raises(PointResolverError):
            resolver._parse_dot_notation("beam.solid('>Z').center")


# =============================================================================
# Test Dot Notation Resolution
# =============================================================================

class TestDotNotationResolution:
    """Test full resolution of dot notation to coordinates"""

    def test_resolve_face_center(self, resolver):
        """Test resolving face center"""
        # Top face of beam at z=12.5
        point = resolver.resolve("beam.face('>Z').center")
        assert isinstance(point, tuple)
        assert len(point) == 3
        assert point[2] == pytest.approx(12.5, abs=0.1)  # Top of 25mm box

    def test_resolve_different_part(self, resolver):
        """Test resolving from different part"""
        # Arm is at y=72.5
        point = resolver.resolve("arm.face('>Y').center")
        assert point[1] > 70  # Should be around 107.5

    def test_resolve_face_min(self, resolver):
        """Test resolving minimum point of face"""
        point = resolver.resolve("beam.face('>Z').min")
        # Min corner of top face
        assert point[0] == pytest.approx(-50, abs=0.1)
        assert point[1] == pytest.approx(-25, abs=0.1)
        assert point[2] == pytest.approx(12.5, abs=0.1)

    def test_resolve_face_max(self, resolver):
        """Test resolving maximum point of face"""
        point = resolver.resolve("beam.face('>Z').max")
        # Max corner of top face
        assert point[0] == pytest.approx(50, abs=0.1)
        assert point[1] == pytest.approx(25, abs=0.1)
        assert point[2] == pytest.approx(12.5, abs=0.1)

    def test_resolve_edge_start(self, resolver):
        """Test resolving edge start point"""
        # Get a vertical edge
        point = resolver.resolve("beam.edge('|Z').start")
        assert isinstance(point, tuple)
        assert len(point) == 3

    def test_resolve_edge_end(self, resolver):
        """Test resolving edge end point"""
        point = resolver.resolve("beam.edge('|Z').end")
        assert isinstance(point, tuple)
        assert len(point) == 3

    def test_error_nonexistent_part(self, resolver):
        """Test error when part doesn't exist"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve("nonexistent.face('>Z').center")
        assert "not found" in str(exc.value)
        assert "beam" in str(exc.value)  # Should list available parts

    def test_error_invalid_selector(self, resolver):
        """Test error when selector matches nothing"""
        with pytest.raises(PointResolverError) as exc:
            # Invalid selector that won't match anything
            resolver.resolve("beam.face('INVALID').center")
        assert "selection failed" in str(exc.value).lower()

    def test_error_start_on_face(self, resolver):
        """Test error when using .start on face (only valid for edges)"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve("beam.face('>Z').start")
        assert ".start" in str(exc.value)
        assert "edge" in str(exc.value)


# =============================================================================
# Test Offset Notation
# =============================================================================

class TestOffsetNotation:
    """Test offset notation {from: ..., offset: [...]}"""

    def test_offset_from_absolute(self, resolver):
        """Test offset from absolute coordinates"""
        result = resolver.resolve({
            'from': [10, 20, 30],
            'offset': [5, -5, 10]
        })
        assert result == (15.0, 15.0, 40.0)

    def test_offset_from_dot_notation(self, resolver):
        """Test offset from dot notation point"""
        # Get beam top center, then offset up by 10mm
        result = resolver.resolve({
            'from': "beam.face('>Z').center",
            'offset': [0, 0, 10]
        })
        assert result[2] == pytest.approx(22.5, abs=0.1)  # 12.5 + 10

    def test_offset_zero(self, resolver):
        """Test zero offset (should equal base point)"""
        base = resolver.resolve([10, 20, 30])
        with_offset = resolver.resolve({
            'from': [10, 20, 30],
            'offset': [0, 0, 0]
        })
        assert base == with_offset

    def test_nested_offset(self, resolver):
        """Test offset from another offset (recursive)"""
        result = resolver.resolve({
            'from': {
                'from': [0, 0, 0],
                'offset': [10, 10, 10]
            },
            'offset': [5, 5, 5]
        })
        assert result == (15.0, 15.0, 15.0)

    def test_error_missing_from(self, resolver):
        """Test error when 'from' key missing"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve({'offset': [0, 0, 0]})
        # New error message is more comprehensive
        assert "Invalid dict specification" in str(exc.value)

    def test_error_missing_offset(self, resolver):
        """Test error when 'offset' key missing"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve({'from': [0, 0, 0]})
        # New error message is more comprehensive
        assert "Invalid dict specification" in str(exc.value)

    def test_error_invalid_offset_length(self, resolver):
        """Test error when offset not 3 values"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve({
                'from': [0, 0, 0],
                'offset': [10, 20]  # Only 2 values
            })
        assert "3 values" in str(exc.value)


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test comprehensive error handling"""

    def test_invalid_type(self, resolver):
        """Test error on completely invalid type"""
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve(42)  # Integer not valid
        assert "Invalid point specification type" in str(exc.value)

    def test_empty_registry(self):
        """Test error messages when registry is empty"""
        empty_registry = PartRegistry()
        resolver = PointResolver(empty_registry)

        with pytest.raises(PointResolverError) as exc:
            resolver.resolve("part.face('>Z').center")
        assert "not found" in str(exc.value)

    def test_helpful_error_messages(self, resolver):
        """Test that error messages are helpful"""
        # Should suggest available parts
        with pytest.raises(PointResolverError) as exc:
            resolver.resolve("wrong.face('>Z').center")
        error_msg = str(exc.value)
        assert "Available parts" in error_msg or "beam" in error_msg


# =============================================================================
# Test Integration
# =============================================================================

class TestIntegration:
    """Test integration with other components"""

    def test_with_part_registry(self):
        """Test PointResolver works with Part and PartRegistry"""
        registry = PartRegistry()

        # Add a simple box
        box = cq.Workplane("XY").box(10, 10, 10)
        registry.add(Part(name="box", geometry=box))

        resolver = PointResolver(registry)

        # Should be able to resolve points
        point = resolver.resolve("box.face('>Z').center")
        assert point[2] == pytest.approx(5, abs=0.1)  # Top of 10mm box

    def test_multiple_parts(self):
        """Test with multiple parts in registry"""
        registry = PartRegistry()

        # Add several parts
        box1 = cq.Workplane("XY").box(10, 10, 10).translate((0, 0, 0))
        box2 = cq.Workplane("XY").box(5, 5, 5).translate((20, 0, 0))
        box3 = cq.Workplane("XY").box(8, 8, 8).translate((0, 20, 0))

        registry.add(Part(name="box1", geometry=box1))
        registry.add(Part(name="box2", geometry=box2))
        registry.add(Part(name="box3", geometry=box3))

        resolver = PointResolver(registry)

        # Should resolve from correct parts
        p1 = resolver.resolve("box1.face('>Z').center")
        p2 = resolver.resolve("box2.face('>Z').center")

        assert p1 != p2  # Different parts, different locations


# =============================================================================
# Test Real-World Use Cases
# =============================================================================

class TestRealWorldUseCases:
    """Test realistic TiaCAD use cases"""

    def test_guitar_hanger_rotation_origin(self, resolver):
        """Test getting rotation origin for guitar hanger arm"""
        # This is the actual use case from TiaCAD design
        # Get the front face center of beam as rotation origin
        origin = resolver.resolve("beam.face('>Y').center")

        assert isinstance(origin, tuple)
        assert len(origin) == 3
        # Beam is 50mm wide (Y), centered at 0, so front is at y=25
        assert origin[1] == pytest.approx(25, abs=0.1)

    def test_offset_for_clearance(self, resolver):
        """Test adding clearance offset to a face"""
        # Get top of beam, then add 2mm clearance
        point = resolver.resolve({
            'from': "beam.face('>Z').center",
            'offset': [0, 0, 2]  # 2mm clearance
        })

        # Beam top is at 12.5, plus 2mm = 14.5
        assert point[2] == pytest.approx(14.5, abs=0.1)

    def test_attachment_point_workflow(self, resolver):
        """Test complete workflow: get point, offset it, use for attachment"""
        # 1. Get base point
        base = resolver.resolve("beam.face('>Y').center")

        # 2. Offset outward by 35mm
        attachment = resolver.resolve({
            'from': "beam.face('>Y').center",
            'offset': [0, 35, 0]
        })

        # Should be 35mm further in Y
        assert attachment[1] == pytest.approx(base[1] + 35, abs=0.1)
