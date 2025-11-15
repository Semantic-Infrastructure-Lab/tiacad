#!/usr/bin/env python3
"""
Update Visual Reference Images

This script helps manage visual regression test reference images.

Usage:
    # Update all reference images
    python scripts/update_visual_references.py

    # Update specific test
    python scripts/update_visual_references.py --test simple_box

    # List all current references
    python scripts/update_visual_references.py --list

Author: TiaCAD Team
Version: 3.1.0
"""

import argparse
import os
import sys
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(
        description="Manage visual regression test reference images"
    )
    parser.add_argument(
        "--test",
        "-t",
        help="Update specific test only (e.g., 'simple_box')",
        default=None
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all current reference images"
    )
    parser.add_argument(
        "--clean",
        "-c",
        action="store_true",
        help="Clean all test outputs and diffs"
    )

    args = parser.parse_args()

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define directories
    ref_dir = project_root / "tiacad_core" / "visual_references"
    output_dir = project_root / "tiacad_core" / "visual_output"
    diff_dir = project_root / "tiacad_core" / "visual_diffs"

    if args.list:
        list_references(ref_dir)
        return 0

    if args.clean:
        clean_outputs(output_dir, diff_dir)
        return 0

    # Update references
    update_references(args.test, project_root)
    return 0


def list_references(ref_dir: Path):
    """List all current reference images"""
    if not ref_dir.exists():
        print(f"No reference directory found at {ref_dir}")
        return

    refs = sorted(ref_dir.glob("*.png"))

    if not refs:
        print("No reference images found")
        print(f"Directory: {ref_dir}")
        return

    print(f"Found {len(refs)} reference images:")
    print(f"Location: {ref_dir}\n")

    for ref in refs:
        size_kb = ref.stat().st_size / 1024
        print(f"  - {ref.name} ({size_kb:.1f} KB)")


def clean_outputs(output_dir: Path, diff_dir: Path):
    """Clean test outputs and diff images"""
    import shutil

    cleaned = []

    if output_dir.exists():
        shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cleaned.append(str(output_dir))

    if diff_dir.exists():
        shutil.rmtree(diff_dir)
        diff_dir.mkdir(parents=True, exist_ok=True)
        cleaned.append(str(diff_dir))

    if cleaned:
        print("✓ Cleaned directories:")
        for d in cleaned:
            print(f"  - {d}")
    else:
        print("No output directories to clean")


def update_references(test_name: str, project_root: Path):
    """Update reference images by running pytest with UPDATE_VISUAL_REFERENCES=1"""

    # Change to project root
    os.chdir(project_root)

    # Build pytest command
    cmd = ["pytest", "-m", "visual", "-v"]

    if test_name:
        cmd.extend(["-k", test_name])

    # Set environment variable
    env = os.environ.copy()
    env["UPDATE_VISUAL_REFERENCES"] = "1"

    print("=" * 60)
    print("Updating Visual Reference Images")
    print("=" * 60)

    if test_name:
        print(f"Test: {test_name}")
    else:
        print("Updating: All visual tests")

    print(f"Command: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd, env=env)

    print()
    print("=" * 60)

    if result.returncode == 0:
        print("✓ Reference images updated successfully")
        print()
        print("Next steps:")
        print("  1. Review the updated images")
        print("  2. Run 'pytest -m visual' to verify")
        print("  3. Commit the changes to git")
    else:
        print("✗ Failed to update reference images")
        print(f"Exit code: {result.returncode}")
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
