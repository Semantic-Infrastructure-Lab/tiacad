#!/usr/bin/env python3
"""Integration test for sweep fix"""

import sys
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.geometry.cadquery_backend import CadQueryBackend

def test_sweep_example():
    """Test the pipe_sweep.yaml example"""
    print("Testing sweep operation with pipe_sweep_simple.yaml...")

    try:
        # Parse the file
        parser = TiaCADParser()
        result = parser.parse_file("examples/pipe_sweep_simple.yaml")

        print(f"✅ Parse succeeded!")
        print(f"   Parts created: {len(result.parts)}")

        # Check if we got the expected part
        if "curved_pipe" in result.parts:
            part = result.parts.get("curved_pipe")
            print(f"✅ Curved pipe created successfully!")
            print(f"   Geometry: {part.geometry}")

            # Try to export to STL
            try:
                import os
                output_path = "output/pipe_sweep_test.stl"
                os.makedirs("output", exist_ok=True)

                # Export using CadQuery's built-in STL export
                part.geometry.val().exportStl(output_path)
                print(f"✅ STL export succeeded: {output_path}")

                # Check file size
                size = os.path.getsize(output_path)
                print(f"   File size: {size} bytes")

                return True
            except Exception as e:
                print(f"❌ STL export failed: {e}")
                return False
        else:
            print(f"❌ Expected part 'curved_pipe' not found")
            parts_list = [part.name for part in result.parts._parts.values()]
            print(f"   Available parts: {parts_list}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sweep_example()
    sys.exit(0 if success else 1)
