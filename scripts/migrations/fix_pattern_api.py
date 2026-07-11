#!/usr/bin/env python3
"""
Fix pattern API changes in TiaCAD examples.

Old format:
  spacing: '${value}'
  direction: X

New format:
  spacing: ['${value}', 0, 0]

Usage:
  python fix_pattern_api.py
"""

import re
import sys
from pathlib import Path


def fix_pattern_in_file(filepath):
    """Fix pattern API in a single YAML file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes = []

    # Pattern 1: spacing with direction X
    pattern_x = re.compile(
        r"(\s+)spacing:\s*([^\n]+)\n\s+direction:\s*X",
        re.MULTILINE
    )
    matches = list(pattern_x.finditer(content))
    for match in reversed(matches):  # Process in reverse to maintain positions
        indent = match.group(1)
        spacing_value = match.group(2)
        old_text = match.group(0)
        new_text = f"{indent}spacing: [{spacing_value}, 0, 0]"
        content = content[:match.start()] + new_text + content[match.end():]
        changes.append(f"  X-direction: {spacing_value} → [{spacing_value}, 0, 0]")

    # Pattern 2: spacing with direction Y
    pattern_y = re.compile(
        r"(\s+)spacing:\s*([^\n]+)\n\s+direction:\s*Y",
        re.MULTILINE
    )
    matches = list(pattern_y.finditer(content))
    for match in reversed(matches):
        indent = match.group(1)
        spacing_value = match.group(2)
        old_text = match.group(0)
        new_text = f"{indent}spacing: [0, {spacing_value}, 0]"
        content = content[:match.start()] + new_text + content[match.end():]
        changes.append(f"  Y-direction: {spacing_value} → [0, {spacing_value}, 0]")

    # Pattern 3: spacing with direction Z
    pattern_z = re.compile(
        r"(\s+)spacing:\s*([^\n]+)\n\s+direction:\s*Z",
        re.MULTILINE
    )
    matches = list(pattern_z.finditer(content))
    for match in reversed(matches):
        indent = match.group(1)
        spacing_value = match.group(2)
        old_text = match.group(0)
        new_text = f"{indent}spacing: [0, 0, {spacing_value}]"
        content = content[:match.start()] + new_text + content[match.end():]
        changes.append(f"  Z-direction: {spacing_value} → [0, 0, {spacing_value}]")

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True, changes
    return False, []


def main():
    examples_dir = Path('examples')

    if not examples_dir.exists():
        print("Error: examples/ directory not found")
        sys.exit(1)

    print("Fixing pattern API in TiaCAD examples...\n")

    yaml_files = list(examples_dir.glob('*.yaml'))
    fixed_count = 0

    for filepath in sorted(yaml_files):
        changed, changes = fix_pattern_in_file(filepath)
        if changed:
            fixed_count += 1
            print(f"✓ Fixed {filepath.name}")
            for change in changes:
                print(change)
            print()

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} files")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
