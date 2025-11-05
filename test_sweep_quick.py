#!/usr/bin/env python3
"""Quick test to see sweep error"""

import cadquery as cq

# Simple circular profile on XY plane
profile = cq.Workplane("XY").circle(5)

# Simple curved path
path_points = [(0, 0, 0), (10, 0, 0), (10, 10, 0)]
path_wire = cq.Wire.makePolygon([cq.Vector(*pt) for pt in path_points])

print("Profile created:", profile)
print("Path wire created:", path_wire)

try:
    result = profile.sweep(path_wire)
    print("✅ Sweep succeeded!")
    print("Result:", result)
except Exception as e:
    print(f"❌ Sweep failed: {e}")
    print(f"Error type: {type(e).__name__}")
