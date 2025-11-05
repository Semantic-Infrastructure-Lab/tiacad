"""
Validation Rules for TiaCAD Assembly Validator

Each rule is a separate, testable module that implements a specific validation check.
"""

from .missing_position_rule import MissingPositionRule
from .disconnected_parts_rule import DisconnectedPartsRule
from .hole_edge_proximity_rule import HoleEdgeProximityRule
from .parameter_sanity_rule import ParameterSanityRule
from .bounding_box_rule import BoundingBoxRule
from .boolean_gaps_rule import BooleanGapsRule
from .feature_bounds_rule import FeatureBoundsRule
from .unused_parts_rule import UnusedPartsRule

__all__ = [
    'MissingPositionRule',
    'DisconnectedPartsRule',
    'HoleEdgeProximityRule',
    'ParameterSanityRule',
    'BoundingBoxRule',
    'BooleanGapsRule',
    'FeatureBoundsRule',
    'UnusedPartsRule',
]
