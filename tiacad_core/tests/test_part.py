"""
Tests for Part representation class

Tests cover:
1. Basic part creation
2. Position tracking
3. Transform history
4. Metadata storage
5. Part cloning
6. Registry operations
"""

import pytest
import cadquery as cq
from tiacad_core.part import Part, PartRegistry


class TestPartBasics:
    """Test basic Part creation and properties"""

    def test_create_simple_part(self):
        """Can create a part with minimal info"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="test_box", geometry=box)

        assert part.name == "test_box"
        assert part.geometry is not None
        assert part.metadata == {}
        assert part.transform_history == []

    def test_part_auto_calculates_center(self):
        """Part calculates its center automatically"""
        # Box 10x10x10 centered at origin
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        # Should be at origin (box is centered)
        assert part.current_position is not None
        x, y, z = part.current_position
        assert abs(x) < 0.01  # Close to 0
        assert abs(y) < 0.01
        assert abs(z) < 0.01

    def test_part_with_metadata(self):
        """Can store metadata"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(
            name="box",
            geometry=box,
            metadata={
                'material': 'PLA',
                'color': 'red',
                'infill': 0.2
            }
        )

        assert part.metadata['material'] == 'PLA'
        assert part.metadata['color'] == 'red'
        assert part.metadata['infill'] == 0.2


class TestPartPositionTracking:
    """Test position tracking functionality"""

    def test_get_center(self):
        """Can get center of geometry"""
        # Box at origin
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        center = part.get_center()
        assert len(center) == 3
        assert all(abs(c) < 0.01 for c in center)

    def test_update_position(self):
        """Can update tracked position"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        part.update_position((50, 25, 10))
        assert part.current_position == (50, 25, 10)

    def test_get_bounds(self):
        """Can get bounding box"""
        # Box 10x20x30 at origin
        box = cq.Workplane('XY').box(10, 20, 30)
        part = Part(name="box", geometry=box)

        bounds = part.get_bounds()
        assert 'min' in bounds
        assert 'max' in bounds

        # Box extends ±5 in X, ±10 in Y, ±15 in Z
        min_x, min_y, min_z = bounds['min']
        max_x, max_y, max_z = bounds['max']

        assert abs(min_x - (-5)) < 0.01
        assert abs(max_x - 5) < 0.01
        assert abs(min_y - (-10)) < 0.01
        assert abs(max_y - 10) < 0.01
        assert abs(min_z - (-15)) < 0.01
        assert abs(max_z - 15) < 0.01


class TestTransformHistory:
    """Test transform tracking"""

    def test_add_transform(self):
        """Can record transforms"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        part.add_transform('translate', {'offset': [10, 0, 0]})

        assert len(part.transform_history) == 1
        assert part.transform_history[0]['type'] == 'translate'
        assert part.transform_history[0]['params'] == {'offset': [10, 0, 0]}

    def test_multiple_transforms(self):
        """Can track multiple transforms"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        part.add_transform('translate', {'to': [10, 0, 0]})
        part.update_position((10, 0, 0))
        part.add_transform('rotate', {'angle': 45, 'axis': 'Z'})

        assert len(part.transform_history) == 2
        assert part.transform_history[0]['type'] == 'translate'
        assert part.transform_history[1]['type'] == 'rotate'

        # Check position was tracked
        assert part.transform_history[1]['position_before'] == (10, 0, 0)


class TestPartCloning:
    """Test part cloning functionality"""

    def test_clone_part(self):
        """Can clone a part"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part1 = Part(name="original", geometry=box, metadata={'color': 'red'})
        part1.add_transform('translate', {'to': [10, 0, 0]})

        part2 = part1.clone('copy')

        assert part2.name == 'copy'
        assert part2.name != part1.name
        assert part2.metadata == part1.metadata
        assert part2.current_position == part1.current_position
        assert len(part2.transform_history) == len(part1.transform_history)

    def test_clone_independence(self):
        """Cloned parts are independent"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part1 = Part(name="original", geometry=box)
        part2 = part1.clone('copy')

        # Modify clone
        part2.metadata['modified'] = True
        part2.add_transform('rotate', {'angle': 45})

        # Original should be unchanged
        assert 'modified' not in part1.metadata
        assert len(part1.transform_history) == 0


class TestPartRegistry:
    """Test PartRegistry functionality"""

    def test_create_registry(self):
        """Can create empty registry"""
        registry = PartRegistry()
        assert len(registry) == 0

    def test_add_part(self):
        """Can add parts to registry"""
        registry = PartRegistry()
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)

        registry.add(part)
        assert len(registry) == 1
        assert 'box' in registry

    def test_get_part(self):
        """Can retrieve parts by name"""
        registry = PartRegistry()
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="box", geometry=box)
        registry.add(part)

        retrieved = registry.get('box')
        assert retrieved.name == 'box'
        assert retrieved is part

    def test_duplicate_name_error(self):
        """Raises error on duplicate name"""
        registry = PartRegistry()
        box1 = cq.Workplane('XY').box(10, 10, 10)
        box2 = cq.Workplane('XY').box(20, 20, 20)

        part1 = Part(name="box", geometry=box1)
        part2 = Part(name="box", geometry=box2)

        registry.add(part1)

        with pytest.raises(ValueError, match="already exists"):
            registry.add(part2)

    def test_get_nonexistent_part(self):
        """Raises helpful error for missing part"""
        registry = PartRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get('nonexistent')

    def test_list_parts(self):
        """Can list all part names"""
        registry = PartRegistry()
        box = cq.Workplane('XY').box(10, 10, 10)
        cylinder = cq.Workplane('XY').cylinder(5, 10)

        registry.add(Part(name="box", geometry=box))
        registry.add(Part(name="cylinder", geometry=cylinder))

        parts = registry.list_parts()
        assert len(parts) == 2
        assert 'box' in parts
        assert 'cylinder' in parts

    def test_exists(self):
        """Can check if part exists"""
        registry = PartRegistry()
        box = cq.Workplane('XY').box(10, 10, 10)
        registry.add(Part(name="box", geometry=box))

        assert registry.exists('box')
        assert not registry.exists('cylinder')

    def test_clear(self):
        """Can clear registry"""
        registry = PartRegistry()
        box = cq.Workplane('XY').box(10, 10, 10)
        registry.add(Part(name="box", geometry=box))

        assert len(registry) == 1
        registry.clear()
        assert len(registry) == 0


class TestPartRepresentation:
    """Test string representation"""

    def test_repr(self):
        """Part has useful string representation"""
        box = cq.Workplane('XY').box(10, 10, 10)
        part = Part(name="test_box", geometry=box)

        repr_str = repr(part)
        assert 'test_box' in repr_str
        assert 'Part' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
