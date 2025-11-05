#!/usr/bin/env python3
"""
Quick integration test for text operations.
Tests the full pipeline: YAML -> Parser -> Builder -> CadQuery -> STL
"""

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.executor.tiacad_executor import TiaCADExecutor
import sys

def test_simple_text():
    """Test simple text example"""
    print("Testing examples/text_simple.yaml...")

    try:
        # Parse YAML
        parser = TiaCADParser()
        design = parser.parse_file('examples/text_simple.yaml')
        print(f"✓ Parsed design successfully")
        print(f"  - Sketches: {len(design.get('sketches', {}))}")
        print(f"  - Operations: {len(design.get('operations', {}))}")

        # Execute (build geometry)
        executor = TiaCADExecutor(design)
        executor.execute()
        print(f"✓ Executed successfully")

        # Get result
        result = executor.get_result('text_3d')
        if result:
            print(f"✓ Got result for 'text_3d' operation")
            print(f"  Result type: {type(result)}")

            # Export to STL
            result.val().exportStl('/tmp/text_simple_test.stl')
            print(f"✓ Exported to /tmp/text_simple_test.stl")
            print(f"\n✅ SUCCESS: Simple text example works!")
            return True
        else:
            print(f"✗ No result found for 'text_3d'")
            return False

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_engraved_text():
    """Test engraved text example"""
    print("\n" + "="*60)
    print("Testing examples/text_engraved.yaml...")

    try:
        # Parse YAML
        parser = TiaCADParser()
        design = parser.parse_file('examples/text_engraved.yaml')
        print(f"✓ Parsed design successfully")

        # Execute (build geometry)
        executor = TiaCADExecutor(design)
        executor.execute()
        print(f"✓ Executed successfully")

        # Get result
        result = executor.get_result('final_sign')
        if result:
            print(f"✓ Got result for 'final_sign' operation")

            # Export to STL
            result.val().exportStl('/tmp/text_engraved_test.stl')
            print(f"✓ Exported to /tmp/text_engraved_test.stl")
            print(f"\n✅ SUCCESS: Engraved text (2.5D carving) works!")
            return True
        else:
            print(f"✗ No result found for 'final_sign'")
            return False

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_label():
    """Test product label example"""
    print("\n" + "="*60)
    print("Testing examples/text_label.yaml...")

    try:
        # Parse YAML
        parser = TiaCADParser()
        design = parser.parse_file('examples/text_label.yaml')
        print(f"✓ Parsed design successfully")

        # Execute (build geometry)
        executor = TiaCADExecutor(design)
        executor.execute()
        print(f"✓ Executed successfully")

        # Get result
        result = executor.get_result('final_label')
        if result:
            print(f"✓ Got result for 'final_label' operation")

            # Export to STL
            result.val().exportStl('/tmp/text_label_test.stl')
            print(f"✓ Exported to /tmp/text_label_test.stl")
            print(f"\n✅ SUCCESS: Product label with text works!")
            return True
        else:
            print(f"✗ No result found for 'final_label'")
            return False

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("TiaCAD Text Operations - Integration Test")
    print("="*60)

    results = []
    results.append(("Simple Text", test_simple_text()))
    results.append(("Engraved Text", test_engraved_text()))
    results.append(("Product Label", test_label()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED")
        sys.exit(1)
