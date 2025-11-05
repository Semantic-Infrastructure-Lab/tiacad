#!/usr/bin/env python3
"""Test sweep fixes"""

import cadquery as cq
import math

def test_sweep_basic():
    """Test basic sweep - profile perpendicular to path"""
    print("\n=== Test 1: Basic sweep with perpendicular profile ===")

    # Path along X axis
    path_points = [(0, 0, 0), (10, 0, 0), (10, 10, 0)]
    path_wire = cq.Wire.makePolygon([cq.Vector(*pt) for pt in path_points])

    # Profile on YZ plane (perpendicular to X axis)
    profile = cq.Workplane("YZ").circle(2)

    try:
        result = profile.sweep(path_wire)
        print("✅ Sweep succeeded with YZ profile!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_sweep_with_spline():
    """Test sweep with spline path"""
    print("\n=== Test 2: Sweep with spline path ===")

    # Create smooth spline path
    path_points = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (5, 15, 0)]
    path = cq.Workplane("XY").spline(path_points)

    # Profile perpendicular to first path segment
    profile = cq.Workplane("YZ").circle(2)

    try:
        result = profile.sweep(path)
        print("✅ Sweep with spline succeeded!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_sweep_multisection():
    """Test multi-section sweep (like sweep but with profile positioning)"""
    print("\n=== Test 3: Multi-section sweep ===")

    # Create path
    path = (cq.Workplane("XZ")
           .moveTo(0, 0)
           .lineTo(10, 0)
           .lineTo(10, 10))

    # Create profile at start
    s1 = cq.Workplane("YZ").workplane(offset=0).circle(2)
    s2 = cq.Workplane("YZ").workplane(offset=10).circle(3)
    s3 = cq.Workplane("YZ").workplane(offset=10).circle(1)

    try:
        # This might work better
        result = s1.loft([s2, s3], combine=False)
        print("✅ Loft (alternative to sweep) succeeded!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_sweep_with_aux_spine():
    """Test sweep with auxiliary spine (advanced)"""
    print("\n=== Test 4: Sweep with auxiliary spine ===")

    # Path points
    path_pts = [(0, 0, 0), (10, 0, 0), (10, 10, 0)]

    # Use CadQuery's sweepAlongWire with multisection
    try:
        # Create profile
        profile = cq.Workplane("YZ").circle(2)

        # Create wire from path points
        path_wire = cq.Wire.makePolygon([cq.Vector(*pt) for pt in path_pts])

        # Use CadQuery 2.x sweep
        result = profile.sweep(path_wire, multisection=True)
        print("✅ Sweep with multisection succeeded!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_workplane_positioning():
    """Test creating workplane aligned with path"""
    print("\n=== Test 5: Workplane aligned with path start ===")

    path_pts = [(0, 0, 0), (10, 0, 0), (10, 10, 0)]

    # Calculate path direction at start
    v1 = cq.Vector(*path_pts[0])
    v2 = cq.Vector(*path_pts[1])
    direction = v2 - v1

    print(f"Path starts at {v1}, goes toward {v2}")
    print(f"Direction: {direction}")

    # Create workplane perpendicular to path direction
    # For path along +X, we want YZ plane
    profile = cq.Workplane("YZ").circle(2)
    path_wire = cq.Wire.makePolygon([cq.Vector(*pt) for pt in path_pts])

    try:
        result = profile.sweep(path_wire)
        print("✅ Aligned workplane sweep succeeded!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

# Run all tests
if __name__ == "__main__":
    results = []
    results.append(("Basic perpendicular", test_sweep_basic()))
    results.append(("Spline path", test_sweep_with_spline()))
    results.append(("Multi-section", test_sweep_multisection()))
    results.append(("Auxiliary spine", test_sweep_with_aux_spine()))
    results.append(("Aligned workplane", test_workplane_positioning()))

    print("\n" + "="*60)
    print("RESULTS SUMMARY:")
    print("="*60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, s in results if s)
    print(f"\nPassed: {passed}/{len(results)}")
