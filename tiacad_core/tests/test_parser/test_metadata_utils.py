"""
Unit tests for metadata_utils module

Tests centralized metadata propagation logic.
"""

import pytest
from tiacad_core.parser.metadata_utils import (
    copy_propagating_metadata,
    merge_metadata,
    PROPAGATING_METADATA,
    OPERATION_SPECIFIC_METADATA
)


class TestCopyPropagatingMetadata:
    """Test copy_propagating_metadata function"""

    def test_copy_color_from_source(self):
        """Color should propagate from source to target"""
        source = {
            'color': (1.0, 0.0, 0.0, 1.0),
            'primitive_type': 'box'
        }
        target = {
            'operation_type': 'transform',
            'source': 'red_box'
        }

        result = copy_propagating_metadata(source, target)

        assert result['color'] == (1.0, 0.0, 0.0, 1.0)
        assert result['operation_type'] == 'transform'
        assert result['source'] == 'red_box'
        assert 'primitive_type' not in result  # Should NOT propagate

    def test_copy_material_from_source(self):
        """Material should propagate from source to target"""
        source = {'material': 'steel', 'color': (0.5, 0.5, 0.5, 1.0)}
        target = {'operation_type': 'boolean'}

        result = copy_propagating_metadata(source, target)

        assert result['material'] == 'steel'
        assert result['color'] == (0.5, 0.5, 0.5, 1.0)

    def test_none_source_metadata(self):
        """Should handle None source metadata gracefully"""
        target = {'operation_type': 'transform'}

        result = copy_propagating_metadata(None, target)

        assert result == target
        assert 'color' not in result

    def test_empty_source_metadata(self):
        """Should handle empty source metadata"""
        source = {}
        target = {'operation_type': 'pattern'}

        result = copy_propagating_metadata(source, target)

        assert result == target

    def test_override_color(self):
        """Explicit override should take precedence"""
        source = {'color': (1.0, 0.0, 0.0, 1.0)}
        target = {'operation_type': 'transform'}
        overrides = {'color': (0.0, 1.0, 0.0, 1.0)}

        result = copy_propagating_metadata(source, target, overrides)

        assert result['color'] == (0.0, 1.0, 0.0, 1.0)  # Override wins

    def test_operation_specific_not_copied(self):
        """Operation-specific metadata should NOT propagate"""
        source = {
            'primitive_type': 'box',
            'source': 'original',
            'operation_type': 'transform',
            'color': (1.0, 0.0, 0.0, 1.0)
        }
        target = {'operation_type': 'boolean'}

        result = copy_propagating_metadata(source, target)

        # Color should copy
        assert result['color'] == (1.0, 0.0, 0.0, 1.0)

        # Operation-specific should NOT copy
        assert result['operation_type'] == 'boolean'  # Target value, not source
        assert 'primitive_type' not in result
        assert result.get('source') != 'original'  # Should not copy source's source

    def test_multiple_propagating_fields(self):
        """Multiple propagating fields should all copy"""
        source = {
            'color': (1.0, 0.0, 0.0, 1.0),
            'material': 'metal',
            'transparency': 0.5
        }
        target = {'operation_type': 'transform'}

        result = copy_propagating_metadata(source, target)

        assert result['color'] == (1.0, 0.0, 0.0, 1.0)
        assert result['material'] == 'metal'
        assert result['transparency'] == 0.5

    def test_partial_propagating_fields(self):
        """Only present propagating fields should copy"""
        source = {
            'color': (1.0, 0.0, 0.0, 1.0),
            # No material
        }
        target = {'operation_type': 'transform'}

        result = copy_propagating_metadata(source, target)

        assert result['color'] == (1.0, 0.0, 0.0, 1.0)
        assert 'material' not in result

    def test_transform_metadata_example(self):
        """Real-world example: transform operation"""
        source = {
            'color': (1.0, 0.0, 0.0, 1.0),
            'primitive_type': 'box'
        }
        target = {
            'source': 'red_box',
            'operation_type': 'transform'
        }

        result = copy_propagating_metadata(source, target)

        assert result == {
            'source': 'red_box',
            'operation_type': 'transform',
            'color': (1.0, 0.0, 0.0, 1.0)
        }

    def test_boolean_metadata_example(self):
        """Real-world example: boolean operation"""
        source = {
            'color': (0.0, 0.0, 1.0, 1.0),
            'material': 'plastic'
        }
        target = {
            'operation_type': 'boolean',
            'boolean_op': 'difference'
        }

        result = copy_propagating_metadata(source, target)

        assert result['color'] == (0.0, 0.0, 1.0, 1.0)
        assert result['material'] == 'plastic'
        assert result['boolean_op'] == 'difference'

    def test_pattern_metadata_example(self):
        """Real-world example: pattern operation"""
        source = {
            'color': (0.0, 1.0, 0.0, 1.0)
        }
        target = {
            'operation_type': 'pattern',
            'pattern_type': 'linear',
            'pattern_index': 2,
            'source': 'green_box'
        }

        result = copy_propagating_metadata(source, target)

        assert result['color'] == (0.0, 1.0, 0.0, 1.0)
        assert result['pattern_index'] == 2


class TestMergeMetadata:
    """Test merge_metadata function"""

    def test_merge_two_dicts(self):
        """Basic merge of two dictionaries"""
        dict1 = {'color': (1, 0, 0, 1), 'material': 'metal'}
        dict2 = {'transparency': 0.5}

        result = merge_metadata(dict1, dict2)

        assert result['color'] == (1, 0, 0, 1)
        assert result['material'] == 'metal'
        assert result['transparency'] == 0.5

    def test_merge_override_last(self):
        """Later dict should override earlier (default behavior)"""
        dict1 = {'color': (1, 0, 0, 1)}
        dict2 = {'color': (0, 1, 0, 1)}

        result = merge_metadata(dict1, dict2, prefer_last=True)

        assert result['color'] == (0, 1, 0, 1)  # dict2 wins

    def test_merge_override_first(self):
        """Earlier dict should override later when prefer_last=False"""
        dict1 = {'color': (1, 0, 0, 1)}
        dict2 = {'color': (0, 1, 0, 1)}

        result = merge_metadata(dict1, dict2, prefer_last=False)

        assert result['color'] == (1, 0, 0, 1)  # dict1 wins

    def test_merge_with_none(self):
        """Should handle None values in input"""
        dict1 = {'color': (1, 0, 0, 1)}
        dict2 = None

        result = merge_metadata(dict1, dict2)

        assert result == dict1

    def test_merge_empty_dicts(self):
        """Should handle empty dictionaries"""
        result = merge_metadata({}, {})

        assert result == {}


class TestMetadataConstants:
    """Test metadata constant sets"""

    def test_propagating_metadata_contains_color(self):
        """Color should be in propagating metadata"""
        assert 'color' in PROPAGATING_METADATA

    def test_propagating_metadata_contains_material(self):
        """Material should be in propagating metadata"""
        assert 'material' in PROPAGATING_METADATA

    def test_operation_specific_contains_source(self):
        """Source should be in operation-specific metadata"""
        assert 'source' in OPERATION_SPECIFIC_METADATA

    def test_operation_specific_contains_type(self):
        """Operation type should be in operation-specific metadata"""
        assert 'operation_type' in OPERATION_SPECIFIC_METADATA

    def test_sets_are_disjoint(self):
        """Propagating and operation-specific sets should be disjoint"""
        overlap = PROPAGATING_METADATA & OPERATION_SPECIFIC_METADATA
        assert len(overlap) == 0, f"Sets overlap: {overlap}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
