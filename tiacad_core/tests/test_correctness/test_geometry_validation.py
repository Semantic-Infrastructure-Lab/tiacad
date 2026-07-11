"""
Geometry Validation Tests

Tests that verify geometries are suitable for 3D printing and manufacturing:
- Single connected component (union operations actually merge parts)
- Watertight meshes (no holes or gaps)
- Positive volumes (sanity check)
- No degenerate faces

These tests catch issues where boolean operations silently fail to merge
parts, resulting in disconnected components that can't be 3D printed.

Critical for ensuring examples and user designs are actually printable.

Author: TIA
Version: 1.0
"""

import pytest
import tempfile
from pathlib import Path

import trimesh  # required dependency; ImportError here is a hard collection failure

from tiacad_core.parser import TiaCADParser
from tiacad_core.part import Part
from tiacad_core.geometry import CadQueryBackend
from tiacad_core.testing.contracts import count_solids
import cadquery as cq


def export_and_validate_mesh(part: Part) -> dict:
    """
    Export part to STL and validate mesh geometry.

    Returns dict with:
        - is_valid: bool
        - issues: list of strings
        - stats: dict of geometry stats
    """
    # Export to temp STL
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        part.geometry.val().exportStl(str(tmp_path))
        mesh = trimesh.load(str(tmp_path))

        stats = {
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': mesh.volume,
            'watertight': mesh.is_watertight,
        }

        # Check connected components
        components = mesh.split(only_watertight=False)
        stats['components'] = len(components)

        # Find issues
        issues = []

        if stats['components'] > 1:
            issues.append(
                f"❌ {stats['components']} disconnected parts (expected 1)"
            )

        if not stats['watertight']:
            issues.append("❌ Mesh not watertight (will cause slicing errors)")

        if stats['volume'] <= 0:
            issues.append(f"❌ Invalid volume: {stats['volume']:.2f} mm³")

        if stats['vertices'] == 0:
            issues.append("❌ Empty mesh (no vertices)")

        if stats['faces'] == 0:
            issues.append("❌ No faces")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'stats': stats
        }
    finally:
        tmp_path.unlink(missing_ok=True)


class TestSinglePartGeometry:
    """Test geometry validation for single parts"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_simple_box_is_valid(self):
        """Test simple box produces valid geometry"""
        box = Part(
            name="test_box",
            geometry=cq.Workplane("XY").box(50, 30, 20),
            backend=self.backend
        )

        result = export_and_validate_mesh(box)

        assert result['is_valid'], f"Validation failed: {result['issues']}"
        assert result['stats']['components'] == 1
        assert result['stats']['watertight'] is True
        assert result['stats']['volume'] > 0

    def test_cylinder_is_valid(self):
        """Test cylinder produces valid geometry"""
        cylinder = Part(
            name="test_cylinder",
            geometry=cq.Workplane("XY").circle(10).extrude(30),
            backend=self.backend
        )

        result = export_and_validate_mesh(cylinder)

        assert result['is_valid'], f"Validation failed: {result['issues']}"
        assert result['stats']['components'] == 1
        assert result['stats']['watertight'] is True


class TestBooleanOperationGeometry:
    """Test that boolean operations produce valid unified geometry"""

    def setup_method(self):
        """Setup test fixtures"""
        self.backend = CadQueryBackend()

    def test_union_creates_single_component(self):
        """Test union actually merges parts into single component"""
        # Create two overlapping boxes
        box1 = cq.Workplane("XY").box(50, 30, 20).translate((0, 0, 0))
        box2 = cq.Workplane("XY").box(30, 30, 20).translate((40, 0, 0))

        # Union should merge them
        unioned = box1.union(box2)

        part = Part(
            name="test_union",
            geometry=unioned,
            backend=self.backend
        )

        result = export_and_validate_mesh(part)

        assert result['is_valid'], f"Validation failed: {result['issues']}"
        assert result['stats']['components'] == 1, \
            f"Union produced {result['stats']['components']} components, expected 1"

    def test_difference_is_watertight(self):
        """Test difference produces watertight geometry"""
        # Create box with hole
        box = cq.Workplane("XY").box(50, 30, 20)
        hole = cq.Workplane("XY").workplane(offset=5).circle(5).extrude(20)
        result_geom = box.cut(hole)

        part = Part(
            name="test_difference",
            geometry=result_geom,
            backend=self.backend
        )

        result = export_and_validate_mesh(part)

        assert result['is_valid'], f"Validation failed: {result['issues']}"
        assert result['stats']['watertight'] is True

    def test_intersection_is_valid(self):
        """Test intersection produces valid geometry"""
        # Create two overlapping cylinders
        cyl1 = cq.Workplane("XY").circle(20).extrude(50)
        cyl2 = cq.Workplane("XZ").circle(20).extrude(50)
        intersected = cyl1.intersect(cyl2)

        part = Part(
            name="test_intersection",
            geometry=intersected,
            backend=self.backend
        )

        result = export_and_validate_mesh(part)

        assert result['is_valid'], f"Validation failed: {result['issues']}"
        assert result['stats']['components'] == 1


class TestExampleGeometry:
    """Test that example files produce valid geometry"""

    def test_simple_guitar_hanger_is_valid(self):
        """Test simple_guitar_hanger example is actually printable"""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        yaml_path = examples_dir / "simple_guitar_hanger.yaml"

        if not yaml_path.exists():
            pytest.fail(f"Example not found: {yaml_path} — example was deleted or renamed")

        # Parse and build
        doc = TiaCADParser.parse_file(str(yaml_path))

        # Get final part
        part_names = doc.parts.list_parts()
        if not part_names:
            pytest.fail("No parts found in document")

        # Export last operation (convention: final result)
        if doc.operations:
            part_name = list(doc.operations.keys())[-1]
        else:
            part_name = part_names[0]

        part = doc.parts.get(part_name)

        # Validate geometry
        result = export_and_validate_mesh(part)

        assert result['is_valid'], \
            f"simple_guitar_hanger example invalid: {result['issues']}"
        assert result['stats']['components'] == 1, \
            "Example should produce single printable part"

    def test_bracket_with_hole_is_valid(self):
        """Test bracket_with_hole example is valid"""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        yaml_path = examples_dir / "bracket_with_hole.yaml"

        if not yaml_path.exists():
            pytest.fail(f"Example not found: {yaml_path} — example was deleted or renamed")

        doc = TiaCADParser.parse_file(str(yaml_path))

        # Get final part
        if doc.operations:
            part_name = list(doc.operations.keys())[-1]
        else:
            part_name = doc.parts.list_parts()[0]

        part = doc.parts.get(part_name)

        result = export_and_validate_mesh(part)

        assert result['is_valid'], \
            f"bracket_with_hole example invalid: {result['issues']}"

    def test_awesome_guitar_hanger_is_valid(self):
        """Test awesome_guitar_hanger example produces single printable component"""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        yaml_path = examples_dir / "awesome_guitar_hanger.yaml"

        if not yaml_path.exists():
            pytest.fail(f"Example not found: {yaml_path} — example was deleted or renamed")

        doc = TiaCADParser.parse_file(str(yaml_path))

        if doc.operations:
            part_name = list(doc.operations.keys())[-1]
        else:
            part_name = doc.parts.list_parts()[0]

        part = doc.parts.get(part_name)

        result = export_and_validate_mesh(part)

        assert result['is_valid'], \
            f"awesome_guitar_hanger example invalid: {result['issues']}"
        assert result['stats']['components'] == 1, \
            f"Expected 1 component, got {result['stats']['components']}"

    def test_pipe_sweep_simple_is_valid(self):
        """pipe_sweep_simple: r=5 L-pipe sweep should produce single printable body."""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "pipe_sweep_simple.yaml"))
        part = doc.parts.get(list(doc.operations.keys())[-1])
        result = export_and_validate_mesh(part)
        assert result['stats']['watertight'] is True
        assert result['stats']['components'] == 1
        assert result['stats']['volume'] > 0

    def test_bottle_revolve_is_valid(self):
        """bottle_revolve: revolved profile should produce single printable body."""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "bottle_revolve.yaml"))
        part = doc.parts.get(list(doc.operations.keys())[-1])
        result = export_and_validate_mesh(part)
        assert result['stats']['watertight'] is True
        assert result['stats']['components'] == 1
        assert result['stats']['volume'] > 0

    def test_transition_loft_is_valid(self):
        """transition_loft: loft between profiles should produce single printable body."""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "transition_loft.yaml"))
        part = doc.parts.get(list(doc.operations.keys())[-1])
        result = export_and_validate_mesh(part)
        assert result['stats']['watertight'] is True
        assert result['stats']['components'] == 1
        assert result['stats']['volume'] > 0

    def test_mounting_plate_bolt_circle_watertight(self):
        """
        mounting_plate_with_bolt_circle: plate with bolt-hole pattern should be a single
        watertight solid. Through-holes cause CadQuery STL to export inner hole surfaces
        as separate shells, so mesh-island counting over-counts here -- component count
        is asserted at the BREP/kernel level instead (count_solids), which is the
        connectivity gate VALIDATION_STRENGTHENING.md section 3 Tier 3 calls for
        (see also examples/validation/T3_plate_bolt_circle.tiacad, which reproduces this
        example's fix and its own components: 1 / watertight: true expect: contract).
        """
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "mounting_plate_with_bolt_circle.yaml"))
        part = doc.parts.get("final_plate")
        result = export_and_validate_mesh(part)
        assert result['stats']['watertight'] is True
        assert result['stats']['volume'] > 0
        assert count_solids(part) == 1, \
            f"Expected 1 BREP solid, got {count_solids(part)} — holes disconnected the plate"

    def test_chamfered_bracket_is_single_component(self):
        """chamfered_bracket should be a single merged L-bracket body."""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "chamfered_bracket.yaml"))
        part = doc.parts.get(list(doc.operations.keys())[-1])
        result = export_and_validate_mesh(part)
        assert result['stats']['components'] == 1, \
            f"Expected 1 component, got {result['stats']['components']} — bracket pieces not joined"

    def test_lego_brick_2x1_is_single_component(self):
        """lego_brick_2x1 final_brick should be a single watertight merged body.

        Note: trimesh.split() returns >1 for hollow geometries (inner tube surfaces
        are closed manifolds with inverted normals), so mesh-island counting can't be
        used as the connectivity gate here. Component count is asserted at the
        BREP/kernel level instead (count_solids), which correctly distinguishes "one
        hollow body" from "N disconnected floaters" -- the exact bug class this example
        shipped with historically (see CHANGELOG.md 2026-03-17: 6 disconnected bodies).
        See also examples/validation/T3_lego_2x1.tiacad, the Tier 3 corpus model this
        example is named for in VALIDATION_STRENGTHENING.md section 3.
        """
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        doc = TiaCADParser.parse_file(str(examples_dir / "lego_brick_2x1.yaml"))
        part = doc.parts.get("final_brick")
        result = export_and_validate_mesh(part)
        assert result['stats']['watertight'], \
            "Brick mesh is not watertight — parts are disconnected or union failed"
        assert result['stats']['volume'] > 0, \
            f"Invalid volume: {result['stats']['volume']:.1f} mm³"
        assert count_solids(part) == 1, \
            f"Expected 1 BREP solid, got {count_solids(part)} — studs/posts not merged"
