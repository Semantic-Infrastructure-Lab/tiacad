#!/usr/bin/env python3
"""
Test script to investigate CadQuery text engraving workarounds.
"""

import cadquery as cq
import sys

print("Testing CadQuery text engraving workarounds...\n")

# Create a simple box
print("1. Creating base box...")
box = cq.Workplane("XY").box(30, 30, 10)
print("   ✓ Box created")

# Try different approaches to engraving
print("\n2. Testing different engraving approaches:")

# Approach 1: Standard face workplane + cut (current implementation)
print("\n   Approach 1: Face workplane + cut (current)")
try:
    wp = box.faces(">Z").workplane()
    text = wp.text("TEST", fontsize=5, distance=1, combine=False)
    result = box.cut(text)

    # Check if geometry is valid
    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 2: Create text separately, then cut
print("\n   Approach 2: Separate text creation + positioning")
try:
    # Create text on XY plane
    text = cq.Workplane("XY").text("TEST", fontsize=5, distance=1, combine=False)

    # Position text on top of box
    text_positioned = text.translate((0, 0, 10))

    # Cut from box
    result = box.cut(text_positioned)

    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 3: Use extrude and cut instead of text distance
print("\n   Approach 3: Text with manual extrude")
try:
    # Create 2D text sketch
    wp = box.faces(">Z").workplane()

    # Try creating text as 2D first
    # Note: CadQuery text() always creates 3D, can't easily get 2D
    print("   ⚠ SKIP - CadQuery doesn't support 2D text sketches")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 4: Smaller text depth
print("\n   Approach 4: Very shallow engraving (0.1mm)")
try:
    wp = box.faces(">Z").workplane()
    text = wp.text("TEST", fontsize=5, distance=0.1, combine=False)
    result = box.cut(text)

    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 5: Check if it's a font issue
print("\n   Approach 5: Different font (Arial)")
try:
    wp = box.faces(">Z").workplane()
    text = wp.text("TEST", fontsize=5, distance=1, font="Arial", combine=False)
    result = box.cut(text)

    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 6: Use combine=True
print("\n   Approach 6: Using combine=True in text()")
try:
    # Create fresh box for each test
    box_test = cq.Workplane("XY").box(30, 30, 10)
    wp = box_test.faces(">Z").workplane()

    # Use combine=True and cut=True
    result = wp.text("TEST", fontsize=5, distance=1, combine=True, cut=True)

    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

# Approach 7: Check if embossing works (control)
print("\n   Approach 7: Embossing (control test)")
try:
    wp = box.faces(">Z").workplane()
    text = wp.text("TEST", fontsize=5, distance=1, combine=False)
    result = box.union(text)

    try:
        bbox = result.val().BoundingBox()
        print(f"   ✓ SUCCESS - BBox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
    except Exception as e:
        print(f"   ✗ FAILED - BBox error: {e}")

except Exception as e:
    print(f"   ✗ FAILED - {e}")

print("\n" + "="*60)
print("CONCLUSION:")
print("="*60)
print("Checking which approaches succeeded...")
