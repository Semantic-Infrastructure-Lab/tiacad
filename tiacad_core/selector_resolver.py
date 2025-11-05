"""
TiaCAD Selector Resolution

Solves Critical Gap #2: Selector → CadQuery Mapping

Handles:
1. Simple selectors: ">Z", "<X", "|Y" → pass to CadQuery
2. Combinators: "and", "or", "not" → set operations
3. Both faces and edges

Examples:
    ">Z" → top face
    "|Z and >X" → right vertical edges
    ">Z or <Z" → top and bottom faces
    "not <Z" → all faces except bottom
"""

from typing import List, Any
from enum import Enum
import re


class FeatureType(Enum):
    """Type of geometric feature to select"""
    FACE = "face"
    EDGE = "edge"
    VERTEX = "vertex"


class SelectorResolver:
    """Resolves YAML selectors to geometric features

    CadQuery already supports directional selectors like ">Z", "|X".
    This class adds combinator support (and/or/not) via set operations.
    """

    # Regex patterns
    SIMPLE_SELECTOR = re.compile(r'^[><|#][XYZ]$')
    AND_COMBINATOR = re.compile(r'\s+and\s+')
    OR_COMBINATOR = re.compile(r'\s+or\s+')
    NOT_COMBINATOR = re.compile(r'^not\s+')

    def __init__(self, part_geometry):
        """Initialize resolver with part geometry

        Args:
            part_geometry: CadQuery Workplane or compatible object with
                          .faces() and .edges() methods
        """
        self.geometry = part_geometry

    def resolve(self,
                selector: str,
                feature_type: FeatureType = FeatureType.FACE) -> List[Any]:
        """Resolve a selector string to list of features

        Args:
            selector: Selector string (e.g., ">Z", "|Z and >X")
            feature_type: Type of feature to select (face, edge, vertex)

        Returns:
            List of selected features (CadQuery Face/Edge objects)

        Examples:
            resolve(">Z", FACE) → [top_face]
            resolve("|Z and >X", EDGE) → [right_vertical_edges...]
            resolve(">Z or <Z", FACE) → [top_face, bottom_face]
        """
        # Normalize whitespace
        selector = selector.strip()

        # Check for combinators
        if self._has_not(selector):
            return self._resolve_not(selector, feature_type)
        elif self._has_and(selector):
            return self._resolve_and(selector, feature_type)
        elif self._has_or(selector):
            return self._resolve_or(selector, feature_type)
        else:
            # Simple selector - pass to CadQuery
            return self._resolve_simple(selector, feature_type)

    def _has_and(self, selector: str) -> bool:
        """Check if selector contains 'and' combinator"""
        return bool(self.AND_COMBINATOR.search(selector))

    def _has_or(self, selector: str) -> bool:
        """Check if selector contains 'or' combinator"""
        return bool(self.OR_COMBINATOR.search(selector))

    def _has_not(self, selector: str) -> bool:
        """Check if selector starts with 'not'"""
        return bool(self.NOT_COMBINATOR.match(selector))

    def _resolve_simple(self,
                        selector: str,
                        feature_type: FeatureType) -> List[Any]:
        """Resolve simple selector using CadQuery

        Args:
            selector: Simple selector (">Z", "<X", etc.)
            feature_type: Feature type to select

        Returns:
            List of selected features

        Raises:
            ValueError: If selector is invalid
        """
        if not self.SIMPLE_SELECTOR.match(selector):
            raise ValueError(
                f"Invalid simple selector: '{selector}'. "
                f"Expected format: >X, <Y, |Z, #X, etc."
            )

        try:
            if feature_type == FeatureType.FACE:
                result = self.geometry.faces(selector)
            elif feature_type == FeatureType.EDGE:
                result = self.geometry.edges(selector)
            else:
                raise ValueError(f"Unsupported feature type: {feature_type}")

            # Convert to list
            return result.vals() if hasattr(result, 'vals') else [result.val()]

        except Exception as e:
            raise ValueError(
                f"CadQuery error with selector '{selector}': {e}"
            )

    def _resolve_and(self,
                     selector: str,
                     feature_type: FeatureType) -> List[Any]:
        """Resolve 'and' combinator using set intersection

        Args:
            selector: Selector with 'and' (e.g., "|Z and >X")
            feature_type: Feature type

        Returns:
            List of features matching ALL selectors
        """
        parts = self.AND_COMBINATOR.split(selector)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid 'and' expression: '{selector}'. "
                f"Expected exactly one 'and' operator."
            )

        left, right = parts

        # Resolve both sides
        left_results = set(self.resolve(left.strip(), feature_type))
        right_results = set(self.resolve(right.strip(), feature_type))

        # Intersection
        return list(left_results & right_results)

    def _resolve_or(self,
                    selector: str,
                    feature_type: FeatureType) -> List[Any]:
        """Resolve 'or' combinator using set union

        Args:
            selector: Selector with 'or' (e.g., ">Z or <Z")
            feature_type: Feature type

        Returns:
            List of features matching ANY selector
        """
        parts = self.OR_COMBINATOR.split(selector)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid 'or' expression: '{selector}'. "
                f"Expected exactly one 'or' operator."
            )

        left, right = parts

        # Resolve both sides
        left_results = set(self.resolve(left.strip(), feature_type))
        right_results = set(self.resolve(right.strip(), feature_type))

        # Union
        return list(left_results | right_results)

    def _resolve_not(self,
                     selector: str,
                     feature_type: FeatureType) -> List[Any]:
        """Resolve 'not' combinator using set difference

        Args:
            selector: Selector with 'not' (e.g., "not <Z")
            feature_type: Feature type

        Returns:
            List of features NOT matching the selector
        """
        # Remove 'not ' prefix
        inner_selector = self.NOT_COMBINATOR.sub('', selector).strip()

        # Get all features of this type
        if feature_type == FeatureType.FACE:
            all_features = set(self.geometry.faces().vals())
        elif feature_type == FeatureType.EDGE:
            all_features = set(self.geometry.edges().vals())
        else:
            raise ValueError(f"Unsupported feature type: {feature_type}")

        # Get features matching inner selector
        matching_features = set(self.resolve(inner_selector, feature_type))

        # Complement (all - matching)
        return list(all_features - matching_features)


def parse_selector(selector_string: str) -> dict:
    """Parse a selector string into components

    This is a helper function for understanding selector structure
    without needing geometry.

    Args:
        selector_string: Selector string

    Returns:
        Dictionary with:
            - type: 'simple', 'and', 'or', 'not'
            - parts: List of component selectors

    Examples:
        parse_selector(">Z") →
            {'type': 'simple', 'parts': ['>Z']}

        parse_selector("|Z and >X") →
            {'type': 'and', 'parts': ['|Z', '>X']}
    """
    selector = selector_string.strip()

    if re.match(r'^not\s+', selector):
        inner = re.sub(r'^not\s+', '', selector).strip()
        return {'type': 'not', 'parts': [inner]}

    elif ' and ' in selector:
        parts = [p.strip() for p in selector.split(' and ')]
        return {'type': 'and', 'parts': parts}

    elif ' or ' in selector:
        parts = [p.strip() for p in selector.split(' or ')]
        return {'type': 'or', 'parts': parts}

    else:
        return {'type': 'simple', 'parts': [selector]}
