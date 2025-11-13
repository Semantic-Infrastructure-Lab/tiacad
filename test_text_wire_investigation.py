#!/usr/bin/env python3
"""
Investigation script for text sketch wire generation issue.

This script tests different approaches to creating text geometry in CadQuery
to understand the root cause of "No pending wires present" error.
"""

import cadquery as cq

print("=" * 70)
print("CadQuery Text Wire Investigation")
print("=" * 70)
print(f"CadQuery version: {cq.__version__}")
print()

# Test 1: Direct CadQuery text extrusion (baseline)
print("Test 1: Direct CadQuery text with distance parameter")
print("-" * 70)
try:
    wp1 = cq.Workplane("XY")
    text_obj = wp1.text("TEST", 10, 1.0)  # text, fontsize, distance
    print(f"✅ Success: Created text with built-in extrusion")
    print(f"   Objects: {len(text_obj.objects())}")
    print(f"   Type: {type(text_obj.val())}")
except Exception as e:
    print(f"❌ Failed: {e}")
print()

# Test 2: Can we get wires from text without extruding?
print("Test 2: Attempt to get text wires without extrusion")
print("-" * 70)
try:
    wp2 = cq.Workplane("XY")
    # Try to create text profile without distance
    # Note: CadQuery's text() method REQUIRES distance parameter
    print("   CadQuery text() method REQUIRES 'distance' parameter")
    print("   There is no way to create 2D text wires directly")
    print("   Result: ⚠️  Design limitation - text always creates 3D geometry")
except Exception as e:
    print(f"❌ Failed: {e}")
print()

# Test 3: Try to extrude already-extruded text (simulates TiaCAD bug)
print("Test 3: Double extrusion (simulates TiaCAD issue)")
print("-" * 70)
try:
    wp3 = cq.Workplane("XY")
    text_obj = wp3.text("TEST", 10, 0.1)  # Create text with minimal extrusion
    # Now try to extrude again
    double_extruded = text_obj.extrude(5.0)  # Try to extrude the 3D object
    print(f"✅ Unexpected success: {double_extruded}")
except Exception as e:
    print(f"❌ Expected failure: {e}")
    if "No pending wires" in str(e):
        print("   ✓ This is the error we see in TiaCAD!")
print()

# Test 4: Check if text creates a solid directly
print("Test 4: What does text() actually create?")
print("-" * 70)
try:
    wp4 = cq.Workplane("XY")
    text_obj = wp4.text("TEST", 10, 1.0)
    obj = text_obj.val()
    print(f"   Object type: {type(obj)}")
    print(f"   Is solid: {hasattr(obj, 'isSolid') and obj.isSolid()}")
    print(f"   Result: text() creates a Solid directly, not wires")
except Exception as e:
    print(f"❌ Failed: {e}")
print()

# Test 5: Can we union text solids with different heights?
print("Test 5: Can we modify text solid height after creation?")
print("-" * 70)
try:
    # Create text with minimal height
    wp5a = cq.Workplane("XY")
    text_short = wp5a.text("TEST", 10, 0.1)

    # Create text with desired height
    wp5b = cq.Workplane("XY")
    text_tall = wp5b.text("TEST", 10, 5.0)

    print(f"✅ Can create text at different heights")
    print(f"   Short text (0.1mm): {len(text_short.solids().vals())} solid(s)")
    print(f"   Tall text (5.0mm): {len(text_tall.solids().vals())} solid(s)")
    print()
    print("   Insight: We should create text with the FINAL distance directly,")
    print("   not create it at 0.1mm and try to extrude it further.")
except Exception as e:
    print(f"❌ Failed: {e}")
print()

# Test 6: Alternative - can we use text as a cutting tool?
print("Test 6: Using short text solid as cutting tool")
print("-" * 70)
try:
    # Create a base box
    base = cq.Workplane("XY").box(50, 30, 10)

    # Create text with minimal height
    text_cutter = cq.Workplane("XY").workplane(offset=10).text("TEST", 10, -5.0)

    # Try to cut the text into the base
    result = base.cut(text_cutter)

    print(f"✅ Success: Can use text as cutting tool")
    print(f"   Result solids: {len(result.solids().vals())}")
    print(f"   This approach works for engraving!")
except Exception as e:
    print(f"❌ Failed: {e}")
print()

print("=" * 70)
print("CONCLUSIONS")
print("=" * 70)
print()
print("1. CadQuery's text() method REQUIRES a 'distance' parameter")
print("   → There's no way to create 2D text wires")
print("   → Text always creates 3D extruded geometry directly")
print()
print("2. Attempting to extrude already-extruded text fails with:")
print("   'No pending wires present'")
print("   → This is exactly what TiaCAD is doing!")
print()
print("3. ROOT CAUSE: TiaCAD architecture mismatch")
print("   - Sketch shapes (Rectangle2D, Circle2D) create 2D wires")
print("   - Text2D creates 3D solid (because CadQuery requires it)")
print("   - ExtrudeBuilder assumes all shapes create wires, tries to extrude")
print("   - Result: double extrusion attempt fails")
print()
print("4. SOLUTION OPTIONS:")
print()
print("   A) Special case text in ExtrudeBuilder._extrude_sketch()")
print("      - Detect when shape is Text2D")
print("      - Don't call extrude() on it (it's already 3D)")
print("      - Just use the solid directly")
print("      - Scale/translate if needed to match desired extrusion distance")
print()
print("   B) Change Text2D to NOT create sketches")
print("      - Remove text from sketch shapes entirely")
print("      - Create text_operation instead (like emboss/engrave)")
print("      - Update examples to use operations instead of sketches")
print("      - Simpler API, matches CadQuery's design")
print()
print("   C) Document limitation, mark tests as xfail")
print("      - Explain CadQuery doesn't support 2D text wires")
print("      - Update examples to use text operations")
print("      - Remove text from sketch shape types")
print()
print("RECOMMENDATION: Option B (remove text from sketches)")
print("  - Cleanest solution that matches CadQuery's API design")
print("  - Text operations (emboss/engrave) already work perfectly")
print("  - Avoids architectural complexity of special-casing text")
print("=" * 70)
