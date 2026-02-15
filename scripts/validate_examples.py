#!/usr/bin/env python3
"""
Validate all TiaCAD examples for API compatibility and parsing correctness.

This script is used in CI/CD to prevent API breakage in examples.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tiacad_core.parser import TiaCADParser


# Known exceptions
EXPECTED_FAILURES = {
    "error_demo.yaml": "Intentionally broken for error handling testing",
    "pipe_sweep.yaml": "Known OCCT geometry limitation (sweep + hollow + sharp corners)",
}


def validate_example(example_path: Path) -> Tuple[bool, str]:
    """
    Validate a single example file.

    Returns:
        (success: bool, message: str)
    """
    try:
        # Parse YAML (uses default backend - CadQueryBackend or whatever is set)
        TiaCADParser.parse_file(str(example_path))

        return True, "✅ Valid"

    except Exception as e:
        error_msg = str(e)
        # Truncate long error messages
        if len(error_msg) > 200:
            error_msg = error_msg[:197] + "..."
        return False, f"❌ {error_msg}"


def validate_all_examples(examples_dir: Path) -> Dict[str, dict]:
    """
    Validate all example files.

    Returns:
        Dictionary of {filename: {success: bool, message: str, expected_failure: bool}}
    """
    results = {}

    # Find all YAML files
    yaml_files = sorted(examples_dir.glob("*.yaml"))

    for example_file in yaml_files:
        filename = example_file.name

        # Check if this is an expected failure
        expected_failure = filename in EXPECTED_FAILURES

        if expected_failure:
            results[filename] = {
                "success": False,
                "message": f"⚠️ Expected failure: {EXPECTED_FAILURES[filename]}",
                "expected_failure": True,
            }
        else:
            success, message = validate_example(example_file)
            results[filename] = {
                "success": success,
                "message": message,
                "expected_failure": False,
            }

    return results


def print_results_human(results: Dict[str, dict]) -> int:
    """
    Print results in human-readable format.

    Returns:
        Exit code (0 = success, 1 = failures)
    """
    print("\n" + "=" * 80)
    print("TiaCAD Example Validation Report")
    print("=" * 80 + "\n")

    # Categorize results
    passing = []
    failing = []
    expected_failures = []

    for filename, result in sorted(results.items()):
        if result["expected_failure"]:
            expected_failures.append((filename, result["message"]))
        elif result["success"]:
            passing.append(filename)
        else:
            failing.append((filename, result["message"]))

    # Print passing examples
    if passing:
        print(f"✅ PASSING ({len(passing)} examples):")
        for filename in passing:
            print(f"   ✓ {filename}")
        print()

    # Print failing examples
    if failing:
        print(f"❌ FAILING ({len(failing)} examples):")
        for filename, message in failing:
            print(f"   ✗ {filename}")
            print(f"     {message}")
        print()

    # Print expected failures
    if expected_failures:
        print(f"⚠️  EXPECTED FAILURES ({len(expected_failures)} examples):")
        for filename, message in expected_failures:
            print(f"   ⚠ {filename}")
            print(f"     {message}")
        print()

    # Summary
    total = len(results)
    print("-" * 80)
    print(f"SUMMARY: {len(passing)}/{total - len(expected_failures)} passing")
    print(f"         {len(expected_failures)} expected failures (not counted)")

    if failing:
        print(f"         {len(failing)} unexpected failures ⚠️")
        print("-" * 80)
        return 1
    else:
        pass_rate = (len(passing) / (total - len(expected_failures))) * 100
        print(f"         {pass_rate:.1f}% pass rate ✅")
        print("-" * 80)
        return 0


def print_results_github(results: Dict[str, dict]) -> int:
    """
    Print results in GitHub Actions format with annotations.

    Returns:
        Exit code (0 = success, 1 = failures)
    """
    # GitHub Actions grouping
    print("::group::Example Validation Results")

    failing_count = 0
    passing_count = 0
    expected_failure_count = 0

    for filename, result in sorted(results.items()):
        if result["expected_failure"]:
            expected_failure_count += 1
            print(f"⚠️ {filename}: {result['message']}")
        elif result["success"]:
            passing_count += 1
            print(f"✅ {filename}: {result['message']}")
        else:
            failing_count += 1
            print(f"❌ {filename}: {result['message']}")
            # GitHub Actions error annotation
            print(f"::error file=examples/{filename}::{result['message']}")

    print("::endgroup::")

    # Summary
    total = len(results)
    working_total = total - expected_failure_count
    pass_rate = (passing_count / working_total * 100) if working_total > 0 else 0

    print(f"\n📊 Summary: {passing_count}/{working_total} passing ({pass_rate:.1f}% pass rate)")
    print(f"   Expected failures: {expected_failure_count} (not counted)")

    if failing_count > 0:
        print(f"   ⚠️ Unexpected failures: {failing_count}")
        print(f"::warning::Example validation failed: {failing_count} examples have errors")
        return 1
    else:
        print("   ✅ All examples valid!")
        return 0


def save_report(results: Dict[str, dict], output_path: Path):
    """Save validation report as JSON."""
    # Add statistics
    passing = sum(1 for r in results.values() if r["success"] and not r["expected_failure"])
    failing = sum(1 for r in results.values() if not r["success"] and not r["expected_failure"])
    expected = sum(1 for r in results.values() if r["expected_failure"])
    total = len(results)

    report = {
        "total_examples": total,
        "passing": passing,
        "failing": failing,
        "expected_failures": expected,
        "pass_rate": (passing / (total - expected)) * 100 if (total - expected) > 0 else 0,
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate TiaCAD examples for API compatibility"
    )
    parser.add_argument(
        "--format",
        choices=["human", "github"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=Path(__file__).parent.parent / "examples",
        help="Path to examples directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("example_validation_report.json"),
        help="Output path for JSON report",
    )

    args = parser.parse_args()

    # Validate examples
    print(f"🔍 Validating examples in: {args.examples_dir}\n")
    results = validate_all_examples(args.examples_dir)

    # Save report
    save_report(results, args.output)

    # Print results
    if args.format == "github":
        exit_code = print_results_github(results)
    else:
        exit_code = print_results_human(results)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
