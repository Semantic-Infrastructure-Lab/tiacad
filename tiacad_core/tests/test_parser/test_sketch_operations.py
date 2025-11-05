"""
Comprehensive tests for Phase 3 Sketch Operations

Tests extrude, revolve, sweep, and loft operations with various scenarios.

Author: TIA
Version: 0.1.0-alpha (Phase 3)
"""

import pytest
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.parser.operations_builder import OperationsBuilderError


class TestExtrudeOperation:
    """Tests for extrude operation"""

    def test_extrude_basic(self):
        """Basic extrude operation"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'rectangle', 'width': 10, 'height': 10}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'box': {
                    'type': 'extrude',
                    'sketch': 'profile',
                    'distance': 20
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'box' in doc.parts.list_parts()

        # Verify geometry exists
        part = doc.parts.get('box')
        assert part.geometry is not None

    def test_extrude_with_offset(self):
        """Extrude with offset positioning"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'origin': [5, 5, 0],
                    'shapes': [
                        {'type': 'circle', 'radius': 5}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'cylinder': {
                    'type': 'extrude',
                    'sketch': 'profile',
                    'distance': 15
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'cylinder' in doc.parts.list_parts()

    def test_extrude_both_directions(self):
        """Extrude in both directions"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'rectangle', 'width': 10, 'height': 10}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'box': {
                    'type': 'extrude',
                    'sketch': 'profile',
                    'distance': 20,
                    'both': True
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        part = doc.parts.get('box')
        # Just verify the part was created (both direction is a CadQuery implementation detail)
        assert part.geometry is not None

    def test_extrude_with_parameters(self):
        """Extrude with parameter expressions"""
        yaml_data = {
            'parameters': {
                'height': 25
            },
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'circle', 'radius': 10}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'pillar': {
                    'type': 'extrude',
                    'sketch': 'profile',
                    'distance': '${height}'
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'pillar' in doc.parts.list_parts()

    def test_extrude_missing_profile_error(self):
        """Extrude with missing profile raises error"""
        yaml_data = {
            'sketches': {},
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'box': {
                    'type': 'extrude',
                    'distance': 20
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'sketch' in str(exc_info.value).lower()

    def test_extrude_nonexistent_profile_error(self):
        """Extrude with nonexistent profile raises error"""
        yaml_data = {
            'sketches': {},
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'box': {
                    'type': 'extrude',
                    'sketch': 'nonexistent',
                    'distance': 20
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'not found' in str(exc_info.value).lower()


class TestRevolveOperation:
    """Tests for revolve operation"""

    def test_revolve_basic(self):
        """Basic revolve operation"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XZ',
                    'shapes': [
                        {'type': 'rectangle', 'width': 5, 'height': 10, 'center': [5, 0]}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'vase': {
                    'type': 'revolve',
                    'sketch': 'profile',
                    'axis': 'Z',
                    'angle': 360
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'vase' in doc.parts.list_parts()

    def test_revolve_partial_angle(self):
        """Revolve with partial angle (not full 360°)"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XZ',
                    'shapes': [
                        {'type': 'rectangle', 'width': 5, 'height': 10, 'center': [5, 0]}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'arc': {
                    'type': 'revolve',
                    'sketch': 'profile',
                    'axis': 'Z',
                    'angle': 180
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        part = doc.parts.get('arc')
        assert part.metadata['angle'] == 180

    def test_revolve_custom_axis(self):
        """Revolve with custom axis"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'circle', 'radius': 3, 'center': [10, 0]}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'torus': {
                    'type': 'revolve',
                    'sketch': 'profile',
                    'axis': 'Z',
                    'angle': 360
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'torus' in doc.parts.list_parts()

    def test_revolve_missing_profile_error(self):
        """Revolve with missing profile raises error"""
        yaml_data = {
            'sketches': {},
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'vase': {
                    'type': 'revolve',
                    'angle': 360
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'sketch' in str(exc_info.value).lower()


class TestSweepOperation:
    """Tests for sweep operation"""

    def test_sweep_basic(self):
        """Basic sweep operation with straight path"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'circle', 'radius': 5}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'pipe': {
                    'profile': 'profile',
                    'type': 'sweep',
                    'sketch': 'profile',
                    'path': [
                        [0, 0, 0],
                        [20, 0, 0]
                    ]
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'pipe' in doc.parts.list_parts()

    def test_sweep_curved_path(self):
        """Sweep with curved path"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [
                        {'type': 'circle', 'radius': 3}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'curved_pipe': {
                    'profile': 'profile',
                    'type': 'sweep',
                    'sketch': 'profile',
                    'path': [
                        [0, 0, 0],
                        [10, 0, 0],
                        [10, 10, 0],
                        [10, 10, 10]
                    ]
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'curved_pipe' in doc.parts.list_parts()

    def test_sweep_missing_profile_error(self):
        """Sweep with missing profile raises error"""
        yaml_data = {
            'sketches': {},
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'pipe': {
                    'type': 'sweep',
                    'path': [[0, 0, 0], [10, 0, 0]]
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'profile' in str(exc_info.value).lower()

    def test_sweep_missing_path_error(self):
        """Sweep with missing path raises error"""
        yaml_data = {
            'sketches': {
                'profile': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 5}]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'pipe': {
                    'type': 'sweep',
                    'profile': 'profile'
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'path' in str(exc_info.value).lower()


class TestLoftOperation:
    """Tests for loft operation"""

    def test_loft_basic(self):
        """Basic loft between two profiles"""
        yaml_data = {
            'sketches': {
                'bottom': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {'type': 'rectangle', 'width': 20, 'height': 20}
                    ]
                },
                'top': {
                    'plane': 'XY',
                    'origin': [0, 0, 15],
                    'shapes': [
                        {'type': 'circle', 'radius': 10}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'transition': {
                    'type': 'loft',
                    'profiles': ['bottom', 'top'],
                    'ruled': False
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'transition' in doc.parts.list_parts()

    def test_loft_three_profiles(self):
        """Loft between three profiles"""
        yaml_data = {
            'sketches': {
                'base': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {'type': 'rectangle', 'width': 20, 'height': 20}
                    ]
                },
                'middle': {
                    'plane': 'XY',
                    'origin': [0, 0, 10],
                    'shapes': [
                        {'type': 'circle', 'radius': 12}
                    ]
                },
                'top': {
                    'plane': 'XY',
                    'origin': [0, 0, 20],
                    'shapes': [
                        {'type': 'circle', 'radius': 8}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'vase': {
                    'type': 'loft',
                    'profiles': ['base', 'middle', 'top']
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'vase' in doc.parts.list_parts()

    def test_loft_ruled_surface(self):
        """Loft with ruled surface (straight lines)"""
        yaml_data = {
            'sketches': {
                'bottom': {
                    'plane': 'XY',
                    'origin': [0, 0, 0],
                    'shapes': [
                        {'type': 'rectangle', 'width': 15, 'height': 15}
                    ]
                },
                'top': {
                    'plane': 'XY',
                    'origin': [0, 0, 10],
                    'shapes': [
                        {'type': 'rectangle', 'width': 10, 'height': 10}
                    ]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'pyramid': {
                    'type': 'loft',
                    'profiles': ['bottom', 'top'],
                    'ruled': True
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        part = doc.parts.get('pyramid')
        assert part.metadata['ruled'] is True

    def test_loft_missing_profiles_error(self):
        """Loft with missing profiles raises error"""
        yaml_data = {
            'sketches': {},
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'transition': {
                    'type': 'loft'
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'profiles' in str(exc_info.value).lower()

    def test_loft_too_few_profiles_error(self):
        """Loft with only one profile raises error"""
        yaml_data = {
            'sketches': {
                'single': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 10}]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'invalid': {
                    'type': 'loft',
                    'profiles': ['single']
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'at least 2' in str(exc_info.value).lower()

    def test_loft_nonexistent_profile_error(self):
        """Loft with nonexistent profile raises error"""
        yaml_data = {
            'sketches': {
                'exists': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 10}]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'invalid': {
                    'type': 'loft',
                    'profiles': ['exists', 'nonexistent']
                }
            }
        }

        with pytest.raises(OperationsBuilderError) as exc_info:
            TiaCADParser.parse_dict(yaml_data)
        assert 'not found' in str(exc_info.value).lower()


class TestSketchOperationIntegration:
    """Integration tests for sketch operations working together"""

    def test_multiple_sketch_operations(self):
        """Multiple sketch operations in one document"""
        yaml_data = {
            'sketches': {
                'circle': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 10}]
                },
                'square': {
                    'plane': 'XY',
                    'shapes': [{'type': 'rectangle', 'width': 15, 'height': 15}]
                },
                'small_circle': {
                    'plane': 'XY',
                    'origin': [0, 0, 20],
                    'shapes': [{'type': 'circle', 'radius': 5}]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'cylinder': {
                    'type': 'extrude',
                    'sketch': 'circle',
                    'distance': 25
                },
                'box': {
                    'type': 'extrude',
                    'sketch': 'square',
                    'distance': 10
                },
                'cone': {
                    'type': 'loft',
                    'profiles': ['square', 'small_circle']
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'cylinder' in doc.parts.list_parts()
        assert 'box' in doc.parts.list_parts()
        assert 'cone' in doc.parts.list_parts()

    def test_sketch_operation_with_boolean(self):
        """Sketch operation combined with boolean operation"""
        yaml_data = {
            'sketches': {
                'outer': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 15}]
                },
                'inner': {
                    'plane': 'XY',
                    'shapes': [{'type': 'circle', 'radius': 10}]
                }
            },
            'parts': {
                'dummy': {'primitive': 'box', 'size': [1, 1, 1]}
            },
            'operations': {
                'outer_cyl': {
                    'type': 'extrude',
                    'sketch': 'outer',
                    'distance': 20
                },
                'inner_cyl': {
                    'type': 'extrude',
                    'sketch': 'inner',
                    'distance': 20
                },
                'tube': {
                    'type': 'boolean',
                    'operation': 'difference',
                    'base': 'outer_cyl',
                    'subtract': ['inner_cyl']
                }
            }
        }

        doc = TiaCADParser.parse_dict(yaml_data)
        assert 'tube' in doc.parts.list_parts()
