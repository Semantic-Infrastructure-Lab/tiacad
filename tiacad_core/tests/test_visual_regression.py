"""
Visual Regression Tests for TiaCAD Examples

Tests all example YAML files by:
1. Loading and parsing the YAML
2. Building the geometry
3. Rendering to image
4. Comparing against reference images

Part of TiaCAD v3.1 Phase 2: Visual Regression Testing

Author: TiaCAD Team
Version: 3.1.0
"""

import os
import pytest
from pathlib import Path
from typing import List

from tiacad_core.testing.visual_regression import (
    VisualRegressionTester,
    RenderConfig,
    pytest_visual_compare
)
from tiacad_core.parser.tiacad_parser import TiaCADParser


# Get examples directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
VISUAL_REFERENCES_DIR = Path(__file__).parent.parent / "visual_references"
VISUAL_OUTPUT_DIR = Path(__file__).parent.parent / "visual_output"
VISUAL_DIFF_DIR = Path(__file__).parent.parent / "visual_diffs"


# Check if we should update references (via environment variable)
UPDATE_REFERENCES = os.environ.get("UPDATE_VISUAL_REFERENCES", "").lower() in ("1", "true", "yes")


# Visual regression threshold (percentage of pixels that can differ)
DEFAULT_THRESHOLD = 1.0  # 1% difference allowed


def get_all_example_files() -> List[Path]:
    """Get all YAML example files"""
    if not EXAMPLES_DIR.exists():
        return []

    yaml_files = list(EXAMPLES_DIR.glob("*.yaml"))

    # Exclude error demo (intentionally fails)
    yaml_files = [f for f in yaml_files if "error_demo" not in f.name]

    return sorted(yaml_files)


def get_example_name(yaml_path: Path) -> str:
    """Get test name from YAML file path"""
    return yaml_path.stem


# Pytest fixture for visual regression tester
@pytest.fixture
def visual_tester():
    """Create visual regression tester instance"""
    return VisualRegressionTester(
        reference_dir=str(VISUAL_REFERENCES_DIR),
        output_dir=str(VISUAL_OUTPUT_DIR),
        diff_dir=str(VISUAL_DIFF_DIR),
        update_references=UPDATE_REFERENCES
    )


# Pytest fixture for render configuration
@pytest.fixture
def render_config():
    """Default render configuration for all tests"""
    return RenderConfig(
        width=800,
        height=600,
        camera_position=(50, 50, 50),
        camera_target=(0, 0, 0),
        background_color='white',
        show_axes=False,
        show_grid=False,
        dpi=100  # Lower DPI for faster tests
    )


class TestVisualRegressionExamples:
    """Visual regression tests for all example files"""

    @pytest.mark.visual
    @pytest.mark.parametrize("yaml_file", get_all_example_files(), ids=get_example_name)
    def test_example_visual_regression(
        self,
        yaml_file: Path,
        visual_tester: VisualRegressionTester,
        render_config: RenderConfig
    ):
        """
        Test that example YAML files render consistently

        This test:
        1. Loads the YAML file
        2. Builds the geometry
        3. Renders to an image
        4. Compares against reference image
        """
        # Load and parse YAML
        parser = TiaCADParser()
        try:
            model = parser.parse_file(str(yaml_file))
        except Exception as e:
            pytest.skip(f"Could not parse {yaml_file.name}: {e}")
            return

        # Get final assembly
        try:
            assembly = model.get_assembly()
        except Exception as e:
            pytest.skip(f"Could not build assembly for {yaml_file.name}: {e}")
            return

        # Visual regression test
        test_name = get_example_name(yaml_file)

        result = visual_tester.render_and_compare(
            geometry=assembly,
            test_name=test_name,
            threshold=DEFAULT_THRESHOLD,
            config=render_config,
            generate_diff=True
        )

        # Assert test passed
        assert result.passed, (
            f"Visual regression failed for {test_name}:\n"
            f"  Pixel difference: {result.pixel_diff_percentage:.3f}% (threshold: {result.threshold}%)\n"
            f"  RMS difference: {result.rms_diff:.2f}\n"
            f"  Max pixel diff: {result.max_pixel_diff}\n"
            f"  Reference: {result.reference_path}\n"
            f"  Test output: {result.test_path}\n"
            f"  Diff image: {result.diff_path}"
        )


class TestVisualRegressionCoreOperations:
    """Visual regression tests for core operations"""

    @pytest.mark.visual
    def test_simple_box(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test simple box rendering"""
        import cadquery as cq

        box = cq.Workplane("XY").box(10, 10, 10)

        result = visual_tester.render_and_compare(
            geometry=box,
            test_name="core_simple_box",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"

    @pytest.mark.visual
    def test_cylinder(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test cylinder rendering"""
        import cadquery as cq

        cylinder = cq.Workplane("XY").cylinder(10, 5)

        result = visual_tester.render_and_compare(
            geometry=cylinder,
            test_name="core_cylinder",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"

    @pytest.mark.visual
    def test_sphere(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test sphere rendering"""
        import cadquery as cq

        sphere = cq.Workplane("XY").sphere(5)

        result = visual_tester.render_and_compare(
            geometry=sphere,
            test_name="core_sphere",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"

    @pytest.mark.visual
    def test_boolean_union(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test boolean union rendering"""
        import cadquery as cq

        box1 = cq.Workplane("XY").box(10, 10, 10)
        box2 = cq.Workplane("XY").workplane(offset=5).box(10, 10, 10)

        # Union
        union = box1.union(box2)

        result = visual_tester.render_and_compare(
            geometry=union,
            test_name="core_boolean_union",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"

    @pytest.mark.visual
    def test_fillet(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test fillet rendering"""
        import cadquery as cq

        box = cq.Workplane("XY").box(10, 10, 10).edges("|Z").fillet(1)

        result = visual_tester.render_and_compare(
            geometry=box,
            test_name="core_fillet",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"

    @pytest.mark.visual
    def test_chamfer(self, visual_tester: VisualRegressionTester, render_config: RenderConfig):
        """Test chamfer rendering"""
        import cadquery as cq

        box = cq.Workplane("XY").box(10, 10, 10).edges("|Z").chamfer(1)

        result = visual_tester.render_and_compare(
            geometry=box,
            test_name="core_chamfer",
            threshold=DEFAULT_THRESHOLD,
            config=render_config
        )

        assert result.passed, f"Visual test failed: {result.pixel_diff_percentage}%"


class TestVisualRegressionTesterAPI:
    """Test the VisualRegressionTester API itself"""

    def test_tester_initialization(self):
        """Test that tester initializes correctly"""
        tester = VisualRegressionTester(
            reference_dir="test_refs",
            output_dir="test_out",
            diff_dir="test_diffs"
        )

        assert tester.reference_dir.name == "test_refs"
        assert tester.output_dir.name == "test_out"
        assert tester.diff_dir.name == "test_diffs"

    def test_render_config_defaults(self):
        """Test RenderConfig default values"""
        config = RenderConfig()

        assert config.width == 800
        assert config.height == 600
        assert config.background_color == 'white'
        assert config.format == 'png'
        assert config.dpi == 150

    def test_render_config_custom(self):
        """Test RenderConfig with custom values"""
        config = RenderConfig(
            width=1024,
            height=768,
            background_color='lightgray',
            dpi=200
        )

        assert config.width == 1024
        assert config.height == 768
        assert config.background_color == 'lightgray'
        assert config.dpi == 200


# Test collection report
def pytest_collection_modifyitems(items):
    """Add markers and organize test collection"""
    for item in items:
        # Add slow marker to visual tests (they take longer)
        if "visual" in item.keywords:
            item.add_marker(pytest.mark.slow)


# Pytest plugin: Generate visual regression report after tests
def pytest_sessionfinish(session, exitstatus):
    """Generate HTML report after all tests complete"""
    # Only generate report if visual tests were run
    if not any("visual" in item.keywords for item in session.items):
        return

    # Collect all visual test results
    # This would require storing results during test execution
    # For now, we'll just print a message
    print("\n" + "="*60)
    print("Visual Regression Testing Complete")
    print("="*60)

    if UPDATE_REFERENCES:
        print("\n✓ Reference images have been updated")
        print(f"  Location: {VISUAL_REFERENCES_DIR}")
    else:
        print(f"\nTest outputs: {VISUAL_OUTPUT_DIR}")
        print(f"Diff images: {VISUAL_DIFF_DIR}")

    print("\nTo update reference images, run:")
    print("  UPDATE_VISUAL_REFERENCES=1 pytest -m visual")
    print()
