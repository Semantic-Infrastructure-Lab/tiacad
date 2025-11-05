"""
Pytest fixtures for visualization tests.

These fixtures ensure proper cleanup of PyVista and matplotlib state
to prevent test pollution and flakiness.
"""

import pytest
import gc
import sys


@pytest.fixture(autouse=True)
def cleanup_visualization_state():
    """
    Automatically clean up visualization state after each test.

    This prevents PyVista plotter instances and matplotlib state
    from leaking between tests, which causes flaky test failures.
    """
    # Run test
    yield

    # Force garbage collection to clean up plotter instances
    gc.collect()

    # Clean up PyVista state
    try:
        import pyvista as pv
        # Close all active plotters
        pv.close_all()
    except (ImportError, AttributeError):
        pass

    # Clean up matplotlib state (PyVista uses matplotlib for some operations)
    try:
        import matplotlib.pyplot as plt
        plt.close('all')
        # Clear the current figure
        plt.clf()
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Provide a temporary directory for test output files.

    Automatically cleaned up after test completes.
    """
    output_dir = tmp_path / "renders"
    output_dir.mkdir(exist_ok=True)
    return output_dir
