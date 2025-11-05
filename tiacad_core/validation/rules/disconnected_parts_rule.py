"""
Disconnected Parts Rule for TiaCAD Assembly Validator

Detects groups of parts that are not physically connected in an assembly.
"""

from typing import List, Dict, Set
from ..validation_rule import ValidationRule
from ..validation_types import ValidationIssue, Severity


class DisconnectedPartsRule(ValidationRule):
    """
    Detect disconnected parts in assembly.

    Uses bounding box proximity to determine if parts are connected.
    Reports groups of disconnected parts as separate components.
    """

    @property
    def name(self) -> str:
        return "Disconnected Parts Check"

    @property
    def category(self) -> str:
        return "connectivity"

    def check(self, document) -> List[ValidationIssue]:
        """Find disconnected groups of parts in assembly."""
        issues = []

        try:
            parts_dict = self._get_parts_dict(document)

            # Need at least 2 parts to check connectivity
            if len(parts_dict) < self.constants.MIN_PARTS_FOR_CONNECTIVITY_CHECK:
                return issues

            # Compute bounding boxes for all parts
            bboxes = self._compute_bounding_boxes(parts_dict)

            if len(bboxes) < self.constants.MIN_PARTS_FOR_CONNECTIVITY_CHECK:
                return issues  # Not enough valid geometries

            # Build connectivity graph
            adjacency = self._build_adjacency_graph(bboxes)

            # Find connected components
            components = self._find_connected_components(adjacency)

            # Report if multiple disconnected groups found
            if len(components) > 1:
                issues.append(self._create_disconnected_issue(components))

        except Exception as e:
            issues.append(self._create_skip_issue(str(e)))

        return issues

    def _compute_bounding_boxes(self, parts_dict: dict) -> dict:
        """
        Compute bounding boxes for all parts with valid geometry.

        Args:
            parts_dict: Dictionary of part name -> Part object

        Returns:
            Dictionary of part name -> BoundingBox
        """
        bboxes = {}

        for part_name, part in parts_dict.items():
            if self._has_valid_geometry(part):
                try:
                    bboxes[part_name] = self._get_bounding_box(part.geometry)
                except:
                    pass  # Skip parts with invalid bounding boxes

        return bboxes

    def _has_valid_geometry(self, part) -> bool:
        """Check if part has valid geometry."""
        return hasattr(part, 'geometry') and part.geometry is not None

    def _build_adjacency_graph(self, bboxes: dict) -> Dict[str, Set[str]]:
        """
        Build adjacency graph based on bounding box proximity.

        Args:
            bboxes: Dictionary of part name -> BoundingBox

        Returns:
            Adjacency graph as dictionary of part name -> set of connected part names
        """
        adjacency = {name: set() for name in bboxes.keys()}
        part_names = list(bboxes.keys())

        for i, name1 in enumerate(part_names):
            for name2 in part_names[i+1:]:
                if self._boxes_are_close(bboxes[name1], bboxes[name2]):
                    adjacency[name1].add(name2)
                    adjacency[name2].add(name1)

        return adjacency

    def _boxes_are_close(self, bbox1, bbox2) -> bool:
        """
        Check if two bounding boxes are within tolerance distance.

        Returns True if boxes overlap or are within tolerance of each other.
        """
        # Check if boxes overlap or are close on each axis
        x_close = not (bbox1.xmax + self.tolerance < bbox2.xmin or
                      bbox2.xmax + self.tolerance < bbox1.xmin)
        y_close = not (bbox1.ymax + self.tolerance < bbox2.ymin or
                      bbox2.ymax + self.tolerance < bbox1.ymin)
        z_close = not (bbox1.zmax + self.tolerance < bbox2.zmin or
                      bbox2.zmax + self.tolerance < bbox1.zmin)

        return x_close and y_close and z_close

    def _find_connected_components(self, adjacency: Dict[str, Set[str]]) -> List[Set[str]]:
        """
        Find connected components in adjacency graph using DFS.

        Args:
            adjacency: Adjacency graph

        Returns:
            List of sets, where each set is a connected component
        """
        visited = set()
        components = []

        def dfs(node: str, component: Set[str]):
            """Depth-first search to find connected component."""
            visited.add(node)
            component.add(node)
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    dfs(neighbor, component)

        for node in adjacency:
            if node not in visited:
                component = set()
                dfs(node, component)
                components.append(component)

        return components

    def _create_disconnected_issue(self, components: List[Set[str]]) -> ValidationIssue:
        """Create issue for disconnected components."""
        component_names = [[name for name in comp] for comp in components]

        return ValidationIssue(
            severity=Severity.WARNING,
            category=self.category,
            message=f"Assembly has {len(components)} disconnected groups of parts",
            suggestion=f"Groups: {component_names}. Verify all parts are positioned correctly."
        )

    def _create_skip_issue(self, error_message: str) -> ValidationIssue:
        """Create issue when check is skipped due to error."""
        return ValidationIssue(
            severity=Severity.INFO,
            category=self.category,
            message=f"Connectivity analysis skipped: {error_message}"
        )
