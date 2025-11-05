"""
Shared pytest fixtures for TiaCAD tests.

This file provides common fixtures to reduce code duplication and
improve test maintainability.

Fixtures provided:
- Common geometries (box, cylinder, sphere)
- Parts with various configurations
- Part registries (empty, with single part, with multiple parts)
- Temporary directories and output files
- YAML test data

Usage:
    def test_something(simple_box):
        # simple_box is automatically created
        assert simple_box is not None
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import cadquery as cq
from tiacad_core.part import Part, PartRegistry
from tiacad_core.geometry import (
    GeometryBackend,
    CadQueryBackend,
    MockBackend,
    get_default_backend,
    set_default_backend,
    reset_default_backend,
)


# ============================================================================
# Backend Selection
# ============================================================================

@pytest.fixture
def mock_backend() -> MockBackend:
    """
    Fast mock backend for unit tests.

    Use this for tests that don't need real CAD operations.
    10-100x faster than CadQueryBackend.

    Examples:
        def test_something(mock_backend):
            box = mock_backend.create_box(10, 10, 10)
            part = Part("test", box, backend=mock_backend)
    """
    return MockBackend()


@pytest.fixture
def cadquery_backend() -> CadQueryBackend:
    """
    Real CadQuery backend for integration tests.

    Use this for tests that need actual CAD geometry.

    Examples:
        @pytest.mark.integration
        def test_something(cadquery_backend):
            box = cadquery_backend.create_box(10, 10, 10)
            part = Part("test", box, backend=cadquery_backend)
    """
    return CadQueryBackend()


@pytest.fixture
def backend(request) -> GeometryBackend:
    """
    Auto-select backend based on test markers.

    - Tests marked with @pytest.mark.unit get MockBackend (fast)
    - Tests marked with @pytest.mark.integration get CadQueryBackend (real)
    - Default: CadQueryBackend for backward compatibility

    Examples:
        @pytest.mark.unit
        def test_fast(backend):
            # Gets MockBackend automatically
            box = backend.create_box(10, 10, 10)

        @pytest.mark.integration
        def test_real(backend):
            # Gets CadQueryBackend automatically
            box = backend.create_box(10, 10, 10)
    """
    if request.node.get_closest_marker("unit"):
        return MockBackend()
    else:
        return CadQueryBackend()


# ============================================================================
# Common Geometries
# ============================================================================

@pytest.fixture
def simple_box():
    """Standard 10x10x10 box geometry"""
    return cq.Workplane("XY").box(10, 10, 10)


@pytest.fixture
def simple_cylinder():
    """Standard cylinder: radius=5, height=20"""
    return cq.Workplane("XY").cylinder(20, 5)


@pytest.fixture
def simple_sphere():
    """Standard sphere: radius=10"""
    return cq.Workplane("XY").sphere(10)


@pytest.fixture
def large_box():
    """Larger box: 50x50x50"""
    return cq.Workplane("XY").box(50, 50, 50)


# ============================================================================
# Parts
# ============================================================================

@pytest.fixture
def box_part(simple_box) -> Part:
    """Part instance with simple box"""
    return Part(name="test_box", geometry=simple_box)


@pytest.fixture
def colored_box_part(simple_box) -> Part:
    """Box with red color metadata"""
    return Part(
        name="red_box",
        geometry=simple_box,
        metadata={'color': (1.0, 0.0, 0.0, 1.0)}  # Red RGBA
    )


@pytest.fixture
def transparent_box_part(simple_box) -> Part:
    """Box with transparent blue color"""
    return Part(
        name="glass_box",
        geometry=simple_box,
        metadata={'color': (0.0, 0.5, 1.0, 0.3)}  # Transparent blue
    )


@pytest.fixture
def cylinder_part(simple_cylinder) -> Part:
    """Part instance with cylinder"""
    return Part(name="test_cylinder", geometry=simple_cylinder)


@pytest.fixture
def sphere_part(simple_sphere) -> Part:
    """Part instance with sphere"""
    return Part(name="test_sphere", geometry=simple_sphere)


# ============================================================================
# Registries
# ============================================================================

@pytest.fixture
def empty_registry() -> PartRegistry:
    """Empty part registry"""
    return PartRegistry()


@pytest.fixture
def registry_with_box(box_part) -> PartRegistry:
    """Registry containing one box"""
    registry = PartRegistry()
    registry.add(box_part)
    return registry


@pytest.fixture
def registry_with_multiple_parts(simple_box, simple_cylinder, simple_sphere) -> PartRegistry:
    """Registry with box, cylinder, and sphere"""
    registry = PartRegistry()

    box = Part("box", simple_box)
    cylinder = Part("cylinder", simple_cylinder)
    sphere = Part("sphere", simple_sphere)

    registry.add(box)
    registry.add(cylinder)
    registry.add(sphere)

    return registry


# ============================================================================
# File System
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory, cleaned up after test"""
    tmp_path = Path(tempfile.mkdtemp(prefix="tiacad_test_"))
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def output_file(temp_dir: Path) -> Path:
    """Temporary output file path"""
    return temp_dir / "output.stl"


@pytest.fixture
def output_dir(temp_dir: Path) -> Path:
    """Temporary output directory"""
    output = temp_dir / "output"
    output.mkdir(exist_ok=True)
    return output


# ============================================================================
# YAML Fixtures
# ============================================================================

@pytest.fixture
def simple_box_yaml() -> str:
    """Minimal valid YAML for a simple box"""
    return """
metadata:
  name: Simple Box
  version: "1.0"

parameters:
  width: 50
  height: 30
  depth: 20

parts:
  box:
    primitive: box
    size: ['${width}', '${depth}', '${height}']
"""


@pytest.fixture
def parameterized_yaml() -> str:
    """YAML with parameters and references"""
    return """
metadata:
  name: Parameterized Design

parameters:
  outer_width: 100
  outer_height: 50
  wall_thickness: 5

parts:
  outer_box:
    primitive: box
    size: ['${outer_width}', '${outer_width}', '${outer_height}']
"""


@pytest.fixture
def yaml_with_operations() -> str:
    """YAML with multiple parts and operations"""
    return """
metadata:
  name: Assembly Example

parts:
  base:
    primitive: box
    size: [100, 100, 10]

  post:
    primitive: cylinder
    radius: 5
    height: 50

operations:
  - type: translate
    part: post
    offset: [0, 0, 30]

  - type: union
    parts: [base, post]
    name: assembly
"""


@pytest.fixture
def complex_yaml_file(temp_dir: Path) -> Path:
    """YAML file with complex assembly"""
    yaml_content = """
metadata:
  name: Complex Assembly

parts:
  base:
    primitive: box
    size: [100, 100, 10]

  post:
    primitive: cylinder
    radius: 5
    height: 50

  top:
    primitive: sphere
    radius: 8

operations:
  - type: translate
    part: post
    offset: [0, 0, 30]

  - type: translate
    part: top
    offset: [0, 0, 60]

  - type: union
    parts: [base, post, top]
    name: complete_assembly
"""
    file_path = temp_dir / "complex.yaml"
    file_path.write_text(yaml_content)
    return file_path


# ============================================================================
# Markers Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, minimal dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (use real CadQuery)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take >2 seconds"
    )
    config.addinivalue_line(
        "markers",
        "flaky: Known flaky tests (quarantined)"
    )
