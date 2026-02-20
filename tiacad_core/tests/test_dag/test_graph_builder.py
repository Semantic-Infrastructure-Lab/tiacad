"""
Tests for GraphBuilder - Dependency extraction from YAML

Author: TIA
Version: 3.2.0
"""

import pytest
from tiacad_core.dag.graph_builder import GraphBuilder, GraphBuilderError
from tiacad_core.dag.model_graph import NodeType


class TestGraphBuilder:
    """Tests for GraphBuilder class"""

    def test_empty_yaml(self):
        """Test building graph from minimal YAML"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {},
            'parts': {},
            'operations': {}
        }

        graph = builder.build_graph(yaml_data)
        assert len(graph) == 0

    def test_parameter_nodes(self):
        """Test adding parameter nodes"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'width': 100,
                'height': 50
            }
        }

        graph = builder.build_graph(yaml_data)

        assert len(graph) == 2
        assert "parameter:width" in graph
        assert "parameter:height" in graph
        assert graph.nodes["parameter:width"].spec == {'value': 100}

    def test_parameter_dependencies(self):
        """Test extracting parameter -> parameter dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'width': 100,
                'area': '${width * width}'  # Depends on width
            }
        }

        graph = builder.build_graph(yaml_data)

        # area depends on width
        deps = graph.get_dependencies("parameter:area")
        assert "parameter:width" in deps

    def test_nested_parameter_dependencies(self):
        """Test extracting dependencies from complex expressions"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'width': 100,
                'height': 50,
                'depth': 30,
                'volume': '${width * height * depth}'  # Depends on all three
            }
        }

        graph = builder.build_graph(yaml_data)

        deps = graph.get_dependencies("parameter:volume")
        assert deps == {"parameter:width", "parameter:height", "parameter:depth"}

    def test_part_nodes(self):
        """Test adding part nodes"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            }
        }

        graph = builder.build_graph(yaml_data)

        assert "part:base" in graph
        assert graph.nodes["part:base"].node_type == NodeType.PART

    def test_part_parameter_dependencies(self):
        """Test extracting part -> parameter dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'box_width': 100
            },
            'parts': {
                'base': {
                    'type': 'box',
                    'width': '${box_width}',
                    'height': 50,
                    'depth': 30
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        # part:base depends on parameter:box_width
        deps = graph.get_dependencies("part:base")
        assert "parameter:box_width" in deps

    def test_operation_nodes(self):
        """Test adding operation nodes"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'filleted': {
                    'type': 'fillet',
                    'input': 'base',
                    'radius': 5
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        assert "operation:filleted" in graph
        assert graph.nodes["operation:filleted"].node_type == NodeType.OPERATION

    def test_operation_part_dependencies(self):
        """Test extracting operation -> part dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'filleted': {
                    'type': 'fillet',
                    'input': 'base',
                    'radius': 5
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        # operation:filleted depends on part:base
        deps = graph.get_dependencies("operation:filleted")
        assert "part:base" in deps

    def test_operation_parameter_dependencies(self):
        """Test extracting operation -> parameter dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'fillet_radius': 5
            },
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'filleted': {
                    'type': 'fillet',
                    'input': 'base',
                    'radius': '${fillet_radius}'
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        # operation:filleted depends on parameter:fillet_radius
        deps = graph.get_dependencies("operation:filleted")
        assert "parameter:fillet_radius" in deps

    def test_boolean_operation_dependencies(self):
        """Test extracting boolean operation dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30},
                'hole': {'type': 'cylinder', 'radius': 5, 'height': 50}
            },
            'operations': {
                'result': {
                    'type': 'subtract',
                    'base': 'base',
                    'subtract': ['hole']
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        # operation:result depends on both base and hole
        deps = graph.get_dependencies("operation:result")
        assert "part:base" in deps
        assert "part:hole" in deps

    def test_union_operation_dependencies(self):
        """Test union operation with multiple parts"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'part1': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30},
                'part2': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30},
                'part3': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'combined': {
                    'type': 'union',
                    'base': 'part1',
                    'union': ['part2', 'part3']
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        deps = graph.get_dependencies("operation:combined")
        assert "part:part1" in deps
        assert "part:part2" in deps
        assert "part:part3" in deps

    def test_pattern_operation_marked(self):
        """Test that pattern operations are marked as patterns"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'repeated': {
                    'type': 'pattern',
                    'input': 'base',
                    'spacing': 10,
                    'count': 5
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        node = graph.nodes["operation:repeated"]
        assert node.is_pattern

    def test_circular_parameter_error(self):
        """Test that circular parameter dependencies raise error"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'a': '${b}',
                'b': '${a}'  # Cycle: a -> b -> a
            }
        }

        with pytest.raises(GraphBuilderError, match="Circular dependency"):
            builder.build_graph(yaml_data)

    def test_circular_operation_error(self):
        """Test detecting cycles in operations"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'operations': {
                'op1': {
                    'type': 'union',
                    'base': 'base',
                    'union': ['op2']
                },
                'op2': {
                    'type': 'union',
                    'base': 'base',
                    'union': ['op1']
                }
            }
        }

        with pytest.raises(GraphBuilderError, match="Circular dependency"):
            builder.build_graph(yaml_data)

    def test_reference_nodes(self):
        """Test adding reference nodes"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'references': {
                'top_face': {
                    'part': 'base',
                    'selector': 'faces',
                    'filter': 'top'
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        assert "reference:top_face" in graph
        assert graph.nodes["reference:top_face"].node_type == NodeType.REFERENCE

    def test_reference_part_dependencies(self):
        """Test extracting reference -> part dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parts': {
                'base': {'type': 'box', 'width': 100, 'height': 50, 'depth': 30}
            },
            'references': {
                'top_face': {
                    'part': 'base',
                    'selector': 'faces'
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        deps = graph.get_dependencies("reference:top_face")
        assert "part:base" in deps

    def test_sketch_nodes(self):
        """Test adding sketch nodes"""
        builder = GraphBuilder()

        yaml_data = {
            'sketches': {
                'profile': {
                    'type': 'rectangle',
                    'width': 100,
                    'height': 50
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        assert "sketch:profile" in graph
        assert graph.nodes["sketch:profile"].node_type == NodeType.SKETCH

    def test_sketch_parameter_dependencies(self):
        """Test extracting sketch -> parameter dependencies"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'sketch_width': 100
            },
            'sketches': {
                'profile': {
                    'type': 'rectangle',
                    'width': '${sketch_width}',
                    'height': 50
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        deps = graph.get_dependencies("sketch:profile")
        assert "parameter:sketch_width" in deps

    def test_part_sketch_dependencies(self):
        """Test part referencing sketch"""
        builder = GraphBuilder()

        yaml_data = {
            'sketches': {
                'profile': {
                    'type': 'rectangle',
                    'width': 100,
                    'height': 50
                }
            },
            'parts': {
                'extruded': {
                    'type': 'extrude',
                    'sketch': 'profile',
                    'height': 30
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        deps = graph.get_dependencies("part:extruded")
        assert "sketch:profile" in deps

    def test_complex_dependencies(self):
        """Test complete dependency chain"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'base_size': 100,
                'hole_radius': 5
            },
            'parts': {
                'base': {
                    'type': 'box',
                    'width': '${base_size}',
                    'height': '${base_size}',
                    'depth': 30
                },
                'hole': {
                    'type': 'cylinder',
                    'radius': '${hole_radius}',
                    'height': 30
                }
            },
            'operations': {
                'drilled': {
                    'type': 'subtract',
                    'base': 'base',
                    'subtract': ['hole']
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        # Verify complete dependency chain
        assert len(graph) == 5  # 2 params + 2 parts + 1 operation

        # operation depends on parts
        op_deps = graph.get_transitive_dependencies("operation:drilled")
        assert "part:base" in op_deps
        assert "part:hole" in op_deps
        assert "parameter:base_size" in op_deps
        assert "parameter:hole_radius" in op_deps

    def test_topological_order_complete(self):
        """Test that complete YAML produces valid topological order"""
        builder = GraphBuilder()

        yaml_data = {
            'parameters': {
                'width': 100,
                'area': '${width * width}'
            },
            'parts': {
                'base': {
                    'type': 'box',
                    'width': '${width}',
                    'height': 50,
                    'depth': 30
                }
            },
            'operations': {
                'final': {
                    'type': 'fillet',
                    'input': 'base',
                    'radius': 5
                }
            }
        }

        graph = builder.build_graph(yaml_data)

        order = graph.topological_sort()

        # Expected order: width -> area -> base -> final
        # (area can be anywhere after width)
        width_idx = order.index("parameter:width")
        area_idx = order.index("parameter:area")
        base_idx = order.index("part:base")
        final_idx = order.index("operation:final")

        assert width_idx < area_idx  # width before area
        assert width_idx < base_idx  # width before base
        assert base_idx < final_idx  # base before final
