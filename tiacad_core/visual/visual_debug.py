"""
Visual Debugging Tools for Transform Sequences

Exports geometry at each step of a transform sequence as STL files
for visual inspection in CAD viewers (FreeCAD, Blender, etc.)

This helps catch rotation bugs early by making them VISIBLE.
"""

import os
from typing import List, Dict, Any
from pathlib import Path


def export_transform_steps(
    geometry,
    transforms: List[Dict[str, Any]],
    output_dir: str = "/tmp/tiacad_debug",
    base_name: str = "part"
) -> List[str]:
    """
    Apply transforms step-by-step and export geometry at each stage

    Args:
        geometry: Starting CadQuery Workplane
        transforms: List of transform specifications
        output_dir: Directory to write STL files
        base_name: Base name for output files

    Returns:
        List of paths to generated STL files

    Example:
        files = export_transform_steps(arm, [
            {'type': 'translate', 'offset': [10, 0, 0]},
            {'type': 'rotate', 'angle': 45, 'axis': 'Z', 'origin': [0,0,0]},
        ])
        # Creates:
        # - /tmp/tiacad_debug/part_step_0_original.stl
        # - /tmp/tiacad_debug/part_step_1_translate.stl
        # - /tmp/tiacad_debug/part_step_2_rotate.stl

        print(f"Open {files[0]} in FreeCAD to verify!")
    """
    from tiacad_core.transform_tracker import TransformTracker

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tracker = TransformTracker(geometry)
    output_files = []

    # Step 0: Export original geometry
    step_0_path = os.path.join(output_dir, f"{base_name}_step_0_original.stl")
    _export_geometry(geometry, step_0_path)
    output_files.append(step_0_path)

    # Apply transforms and export after each
    for i, transform in enumerate(transforms, 1):
        tracker.apply_transform(transform)
        current_geom = tracker.get_geometry()

        # Generate filename
        transform_type = transform.get('type', 'unknown')
        filename = f"{base_name}_step_{i}_{transform_type}.stl"
        filepath = os.path.join(output_dir, filename)

        # Export
        _export_geometry(current_geom, filepath)
        output_files.append(filepath)

    # Create summary file
    summary_path = os.path.join(output_dir, f"{base_name}_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(f"Transform Sequence Debug: {base_name}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Total Steps: {len(transforms) + 1}\n\n")

        f.write("Transform Summary:\n")
        f.write(tracker.get_summary())
        f.write("\n\n")

        f.write("Generated Files:\n")
        for i, filepath in enumerate(output_files):
            f.write(f"  Step {i}: {os.path.basename(filepath)}\n")

        f.write("\n")
        f.write("How to view:\n")
        f.write("  1. Open FreeCAD or Blender\n")
        f.write("  2. Import STL files in order\n")
        f.write("  3. Verify each step looks correct\n")
        f.write("  4. Look for unexpected jumps or rotations\n")

    print(f"✅ Debug files written to: {output_dir}")
    print(f"📄 Summary: {summary_path}")
    print(f"📦 {len(output_files)} STL files created")
    print(f"\n💡 Load {output_files[0]} in FreeCAD to start debugging!")

    return output_files


def _export_geometry(geometry, filepath: str):
    """
    Export geometry to STL file

    For testing with mocks: writes placeholder file
    For real CadQuery: exports actual STL
    """
    # Check if this is a mock (for testing)
    if hasattr(geometry, 'center_point'):
        # Mock geometry - write placeholder
        with open(filepath, 'w') as f:
            f.write(f"# Mock STL for testing\n")
            f.write(f"# Center: {geometry.center_point}\n")
        return

    # Real CadQuery geometry
    try:
        # CadQuery export API
        geometry.val().exportStl(filepath)
    except Exception as e:
        print(f"⚠️  Warning: Could not export {filepath}: {e}")
        # Write placeholder on error
        with open(filepath, 'w') as f:
            f.write(f"# Export failed: {e}\n")


def compare_geometries(
    geom1,
    geom2,
    output_dir: str = "/tmp/tiacad_debug",
    name1: str = "geometry_a",
    name2: str = "geometry_b"
) -> Dict[str, Any]:
    """
    Compare two geometries and export both for visual inspection

    Args:
        geom1: First geometry
        geom2: Second geometry
        output_dir: Where to export files
        name1: Name for first geometry
        name2: Name for second geometry

    Returns:
        Dict with comparison results:
        - files: List of exported files
        - bbox_diff: Bounding box differences
        - volume_diff: Volume difference

    Example:
        result = compare_geometries(
            rotate_then_translate_result,
            translate_then_rotate_result,
            name1="rotate_first",
            name2="translate_first"
        )
        # Shows that order matters!
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Export both
    file1 = os.path.join(output_dir, f"{name1}.stl")
    file2 = os.path.join(output_dir, f"{name2}.stl")

    _export_geometry(geom1, file1)
    _export_geometry(geom2, file2)

    # Compare properties (if not mock)
    result = {
        'files': [file1, file2],
        'bbox_diff': None,
        'volume_diff': None,
    }

    if hasattr(geom1, 'center_point') and hasattr(geom2, 'center_point'):
        # Mock comparison
        import math
        center_diff = math.sqrt(sum(
            (a - b)**2
            for a, b in zip(geom1.center_point, geom2.center_point)
        ))
        result['center_distance'] = center_diff

        print(f"📊 Comparison:")
        print(f"  {name1}: center={geom1.center_point}")
        print(f"  {name2}: center={geom2.center_point}")
        print(f"  Distance: {center_diff:.6f}")

    print(f"\n✅ Exported:")
    print(f"  {file1}")
    print(f"  {file2}")
    print(f"\n💡 Load both in CAD viewer to compare visually!")

    return result


# ============================================================================
# Guitar Hanger Debug Example
# ============================================================================

def debug_guitar_hanger_arm():
    """
    Example: Debug guitar hanger arm positioning

    Creates step-by-step STL files for the guitar hanger arm transform sequence
    """
    try:
        import cadquery as cq
    except ImportError:
        print("⚠️  CadQuery not installed - using mock geometry for demo")
        from test_transform_tracker import MockWorkplane
        arm = MockWorkplane(center_point=(0, 0, 0))
    else:
        arm = cq.Workplane("XY").box(22, 70, 16)

    beam_front_center = (0, 37.5, 0)
    arm_length = 70

    transforms = [
        # Step 1: Move to beam front
        {
            'type': 'translate',
            'offset': list(beam_front_center)
        },
        # Step 2: Push arm out
        {
            'type': 'translate',
            'offset': [0, arm_length / 2, 0]
        },
        # Step 3: Rotate around attachment point
        {
            'type': 'rotate',
            'angle': 10,
            'axis': 'X',
            'origin': beam_front_center  # THE KEY!
        },
    ]

    files = export_transform_steps(
        arm,
        transforms,
        output_dir="/tmp/tiacad_debug/guitar_hanger_arm",
        base_name="arm"
    )

    print("\n" + "=" * 60)
    print("GUITAR HANGER ARM DEBUG")
    print("=" * 60)
    print(f"\nExpected behavior:")
    print("  Step 0: Arm at origin")
    print("  Step 1: Arm at beam front (0, 37.5, 0)")
    print("  Step 2: Arm pushed out (0, 72.5, 0)")
    print("  Step 3: Arm tilted UP 10° around attachment point")
    print(f"\n  → Arm BASE should stay at beam front")
    print(f"  → Arm TIP should tilt UP and slightly BACK")
    print(f"\nLoad files in FreeCAD to verify!")

    return files


if __name__ == "__main__":
    # Run guitar hanger debug example
    debug_guitar_hanger_arm()
