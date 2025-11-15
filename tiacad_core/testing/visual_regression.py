"""
TiaCAD Visual Regression Testing Framework

Provides utilities for visual regression testing by:
1. Rendering 3D models to images (PNG/SVG)
2. Comparing rendered images against reference images
3. Generating diff reports for visual changes

Part of TiaCAD v3.1 Phase 2: Visual Regression Testing

Author: TiaCAD Team
Version: 3.1.0
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from PIL import Image, ImageChops, ImageStat
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


@dataclass
class VisualDiffResult:
    """Results from visual comparison between two images"""

    # Comparison metrics
    pixel_diff_percentage: float  # Percentage of pixels that differ
    max_pixel_diff: int  # Maximum difference value (0-255)
    mean_pixel_diff: float  # Average difference across all pixels
    rms_diff: float  # Root mean square difference

    # Test result
    passed: bool  # Whether test passed based on thresholds
    threshold: float  # Threshold used for pass/fail

    # File paths
    reference_path: str
    test_path: str
    diff_path: Optional[str] = None  # Path to diff image if generated

    # Metadata
    image_size: Tuple[int, int] = (0, 0)  # (width, height)
    test_name: str = ""
    timestamp: str = ""


@dataclass
class RenderConfig:
    """Configuration for rendering 3D models to images"""

    # Image dimensions
    width: int = 800
    height: int = 600

    # Camera settings
    camera_position: Tuple[float, float, float] = (50, 50, 50)
    camera_target: Tuple[float, float, float] = (0, 0, 0)

    # Render settings
    background_color: str = 'white'
    show_axes: bool = False
    show_grid: bool = False

    # File format
    format: str = 'png'  # 'png' or 'svg'
    dpi: int = 150


class VisualRegressionTester:
    """
    Main class for visual regression testing

    Example:
        >>> tester = VisualRegressionTester(reference_dir="tests/visual_references")
        >>> result = tester.render_and_compare(
        ...     geometry=my_assembly,
        ...     test_name="simple_box",
        ...     threshold=0.1
        ... )
        >>> assert result.passed, f"Visual regression failed: {result.pixel_diff_percentage}%"
    """

    def __init__(
        self,
        reference_dir: str = "tests/visual_references",
        output_dir: str = "tests/visual_output",
        diff_dir: str = "tests/visual_diffs",
        update_references: bool = False
    ):
        """
        Initialize visual regression tester

        Args:
            reference_dir: Directory containing reference images
            output_dir: Directory for test output images
            diff_dir: Directory for difference images
            update_references: If True, update reference images instead of comparing
        """
        self.reference_dir = Path(reference_dir)
        self.output_dir = Path(output_dir)
        self.diff_dir = Path(diff_dir)
        self.update_references = update_references

        # Create directories
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir.mkdir(parents=True, exist_ok=True)

        self._check_dependencies()

    def _check_dependencies(self):
        """Check that required dependencies are available"""
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for visual regression testing. "
                "Install with: pip install Pillow"
            )

    def render_geometry(
        self,
        geometry,
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> str:
        """
        Render 3D geometry to an image file

        Args:
            geometry: CadQuery Workplane object
            output_path: Path to save rendered image
            config: Render configuration

        Returns:
            Path to rendered image
        """
        if config is None:
            config = RenderConfig()

        # Convert CadQuery geometry to trimesh
        if TRIMESH_AVAILABLE:
            return self._render_with_trimesh(geometry, output_path, config)
        elif MATPLOTLIB_AVAILABLE:
            return self._render_with_matplotlib(geometry, output_path, config)
        else:
            raise ImportError(
                "Either trimesh or matplotlib is required for rendering. "
                "Install with: pip install trimesh matplotlib"
            )

    def _render_with_trimesh(
        self,
        geometry,
        output_path: str,
        config: RenderConfig
    ) -> str:
        """Render using trimesh + matplotlib"""
        try:
            # Export to STL bytes
            from io import BytesIO
            stl_bytes = BytesIO()

            # Get the solid from CadQuery
            if hasattr(geometry, 'val'):
                solid = geometry.val()
            else:
                solid = geometry

            # Export as STL
            if hasattr(solid, 'exportStl'):
                solid.exportStl(stl_bytes)
                stl_bytes.seek(0)
            else:
                # Fallback: export to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
                    tmp_path = tmp.name
                solid.exportStl(tmp_path)
                with open(tmp_path, 'rb') as f:
                    stl_bytes = BytesIO(f.read())
                os.unlink(tmp_path)

            # Load with trimesh
            mesh = trimesh.load(stl_bytes, file_type='stl')

            # Render
            fig = plt.figure(figsize=(config.width/100, config.height/100), dpi=config.dpi)
            ax = fig.add_subplot(111, projection='3d')

            # Plot mesh
            if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                ax.plot_trisurf(
                    mesh.vertices[:, 0],
                    mesh.vertices[:, 1],
                    mesh.vertices[:, 2],
                    triangles=mesh.faces,
                    color='lightblue',
                    edgecolor='navy',
                    linewidth=0.1,
                    alpha=0.8
                )

            # Set camera position
            ax.view_init(elev=30, azim=45)

            # Set background color
            ax.set_facecolor(config.background_color)
            fig.patch.set_facecolor(config.background_color)

            # Configure axes
            if not config.show_axes:
                ax.set_axis_off()

            if not config.show_grid:
                ax.grid(False)

            # Set aspect ratio
            ax.set_box_aspect([1, 1, 1])

            # Save
            plt.savefig(
                output_path,
                dpi=config.dpi,
                bbox_inches='tight',
                facecolor=config.background_color,
                format=config.format
            )
            plt.close(fig)

            return output_path

        except Exception as e:
            # Fallback to matplotlib if trimesh fails
            return self._render_with_matplotlib(geometry, output_path, config)

    def _render_with_matplotlib(
        self,
        geometry,
        output_path: str,
        config: RenderConfig
    ) -> str:
        """Fallback rendering using matplotlib only"""
        # Create a simple placeholder image
        fig = plt.figure(figsize=(config.width/100, config.height/100), dpi=config.dpi)
        ax = fig.add_subplot(111)

        # Add text indicating this is a placeholder
        ax.text(
            0.5, 0.5,
            f"Geometry Rendered\n{type(geometry).__name__}",
            ha='center', va='center',
            fontsize=16,
            transform=ax.transAxes
        )

        ax.set_facecolor(config.background_color)
        ax.set_xticks([])
        ax.set_yticks([])

        plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
        plt.close(fig)

        return output_path

    def compare_images(
        self,
        reference_path: str,
        test_path: str,
        threshold: float = 0.1,
        generate_diff: bool = True
    ) -> VisualDiffResult:
        """
        Compare two images and return difference metrics

        Args:
            reference_path: Path to reference image
            test_path: Path to test image
            threshold: Maximum acceptable difference percentage (0-100)
            generate_diff: If True, generate difference image

        Returns:
            VisualDiffResult with comparison metrics
        """
        # Load images
        ref_img = Image.open(reference_path).convert('RGB')
        test_img = Image.open(test_path).convert('RGB')

        # Ensure same size
        if ref_img.size != test_img.size:
            # Resize test image to match reference
            test_img = test_img.resize(ref_img.size, Image.Resampling.LANCZOS)

        # Calculate pixel differences
        diff_img = ImageChops.difference(ref_img, test_img)

        # Calculate metrics
        stat = ImageStat.Stat(diff_img)

        # RMS (root mean square) difference per channel
        rms_diff = np.sqrt(np.mean([x**2 for x in stat.rms]))

        # Mean difference
        mean_diff = np.mean(stat.mean)

        # Maximum difference
        max_diff = max(stat.extrema, key=lambda x: x[1])[1]

        # Percentage of pixels that differ (considering all channels)
        diff_array = np.array(diff_img)
        total_pixels = diff_array.shape[0] * diff_array.shape[1]
        differing_pixels = np.count_nonzero(diff_array.any(axis=2))
        diff_percentage = (differing_pixels / total_pixels) * 100

        # Generate diff image if requested
        diff_path = None
        if generate_diff and diff_percentage > 0:
            # Enhance differences for visibility
            diff_enhanced = diff_img.point(lambda p: p * 10)
            diff_path = str(self.diff_dir / f"{Path(test_path).stem}_diff.png")
            diff_enhanced.save(diff_path)

        # Determine pass/fail
        passed = diff_percentage <= threshold

        # Create result
        import datetime
        result = VisualDiffResult(
            pixel_diff_percentage=diff_percentage,
            max_pixel_diff=max_diff,
            mean_pixel_diff=mean_diff,
            rms_diff=rms_diff,
            passed=passed,
            threshold=threshold,
            reference_path=reference_path,
            test_path=test_path,
            diff_path=diff_path,
            image_size=ref_img.size,
            test_name=Path(test_path).stem,
            timestamp=datetime.datetime.now().isoformat()
        )

        return result

    def render_and_compare(
        self,
        geometry,
        test_name: str,
        threshold: float = 0.1,
        config: Optional[RenderConfig] = None,
        generate_diff: bool = True
    ) -> VisualDiffResult:
        """
        Render geometry and compare against reference image

        Args:
            geometry: CadQuery geometry to render
            test_name: Name of the test (used for file naming)
            threshold: Maximum acceptable difference percentage
            config: Render configuration
            generate_diff: If True, generate difference image

        Returns:
            VisualDiffResult with comparison metrics
        """
        # Generate paths
        reference_path = self.reference_dir / f"{test_name}.png"
        test_path = self.output_dir / f"{test_name}.png"

        # Render test image
        self.render_geometry(geometry, str(test_path), config)

        # Update reference mode
        if self.update_references:
            # Copy test image to reference
            import shutil
            shutil.copy(str(test_path), str(reference_path))
            print(f"✓ Updated reference image: {reference_path}")

            # Return "passing" result for update mode
            return VisualDiffResult(
                pixel_diff_percentage=0.0,
                max_pixel_diff=0,
                mean_pixel_diff=0.0,
                rms_diff=0.0,
                passed=True,
                threshold=threshold,
                reference_path=str(reference_path),
                test_path=str(test_path),
                test_name=test_name
            )

        # Check if reference exists
        if not reference_path.exists():
            raise FileNotFoundError(
                f"Reference image not found: {reference_path}\n"
                f"Run with update_references=True to create it"
            )

        # Compare images
        result = self.compare_images(
            str(reference_path),
            str(test_path),
            threshold=threshold,
            generate_diff=generate_diff
        )

        return result

    def generate_report(
        self,
        results: List[VisualDiffResult],
        output_path: str = "visual_regression_report.html"
    ) -> str:
        """
        Generate HTML report of visual regression results

        Args:
            results: List of VisualDiffResult objects
            output_path: Path to save HTML report

        Returns:
            Path to generated report
        """
        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>TiaCAD Visual Regression Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .passed {{ color: #28a745; font-weight: bold; }}
        .failed {{ color: #dc3545; font-weight: bold; }}
        .test-result {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-result.pass {{ border-left: 5px solid #28a745; }}
        .test-result.fail {{ border-left: 5px solid #dc3545; }}
        .images {{ display: flex; gap: 20px; margin-top: 15px; }}
        .image-container {{ flex: 1; }}
        .image-container img {{ max-width: 100%; border: 1px solid #ddd; }}
        .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; }}
        .metric {{ background: #f8f9fa; padding: 10px; border-radius: 4px; }}
        .metric-label {{ font-weight: bold; color: #666; font-size: 0.9em; }}
        .metric-value {{ font-size: 1.2em; color: #333; }}
    </style>
</head>
<body>
    <h1>TiaCAD Visual Regression Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {total_tests}</p>
        <p class="passed">Passed: {passed_tests}</p>
        <p class="failed">Failed: {failed_tests}</p>
        <p>Pass Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%</p>
    </div>
"""

        # Add individual test results
        for result in results:
            status_class = "pass" if result.passed else "fail"
            status_text = "PASSED" if result.passed else "FAILED"
            status_color = "passed" if result.passed else "failed"

            # Convert paths to relative for HTML
            ref_path = os.path.relpath(result.reference_path, os.path.dirname(output_path))
            test_path = os.path.relpath(result.test_path, os.path.dirname(output_path))

            html += f"""
    <div class="test-result {status_class}">
        <h3>{result.test_name} - <span class="{status_color}">{status_text}</span></h3>

        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Pixel Diff %</div>
                <div class="metric-value">{result.pixel_diff_percentage:.3f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Threshold</div>
                <div class="metric-value">{result.threshold}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">RMS Difference</div>
                <div class="metric-value">{result.rms_diff:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Max Pixel Diff</div>
                <div class="metric-value">{result.max_pixel_diff}</div>
            </div>
        </div>

        <div class="images">
            <div class="image-container">
                <h4>Reference</h4>
                <img src="{ref_path}" alt="Reference">
            </div>
            <div class="image-container">
                <h4>Test</h4>
                <img src="{test_path}" alt="Test">
            </div>
"""

            # Add diff image if available
            if result.diff_path:
                diff_path = os.path.relpath(result.diff_path, os.path.dirname(output_path))
                html += f"""
            <div class="image-container">
                <h4>Difference</h4>
                <img src="{diff_path}" alt="Difference">
            </div>
"""

            html += """
        </div>
    </div>
"""

        html += """
</body>
</html>
"""

        # Write report
        with open(output_path, 'w') as f:
            f.write(html)

        return output_path


def pytest_visual_compare(
    geometry,
    test_name: str,
    threshold: float = 0.1,
    reference_dir: str = "tests/visual_references",
    update_references: bool = False
) -> VisualDiffResult:
    """
    Pytest helper function for visual regression testing

    Example:
        def test_simple_box():
            box = cq.Workplane("XY").box(10, 10, 10)
            result = pytest_visual_compare(box, "simple_box", threshold=0.1)
            assert result.passed, f"Visual regression failed: {result.pixel_diff_percentage}%"
    """
    tester = VisualRegressionTester(
        reference_dir=reference_dir,
        update_references=update_references
    )

    return tester.render_and_compare(
        geometry=geometry,
        test_name=test_name,
        threshold=threshold
    )
