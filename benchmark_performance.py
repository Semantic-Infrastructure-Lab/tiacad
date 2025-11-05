#!/usr/bin/env python3
"""
TiaCAD v3.0 Performance Benchmark

Measures parsing and build times for various example files to ensure
no performance regression from v3.0 unified spatial reference system.
"""

import time
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from tiacad_core.parser.tiacad_parser import TiaCADParser


def benchmark_file(filepath: Path, iterations: int = 3) -> Dict[str, float]:
    """
    Benchmark parsing and building a YAML file.

    Args:
        filepath: Path to YAML file
        iterations: Number of iterations to average

    Returns:
        Dict with timing results (in milliseconds)
    """
    parser = TiaCADParser()

    # Load YAML once
    with open(filepath) as f:
        yaml_content = yaml.safe_load(f)

    load_times = []
    parse_times = []
    total_times = []

    for _ in range(iterations):
        # Measure total time
        start_total = time.perf_counter()

        # Measure parse time
        start_parse = time.perf_counter()
        try:
            result = parser.parse_dict(yaml_content)
            parse_time = (time.perf_counter() - start_parse) * 1000
            parse_times.append(parse_time)

            total_time = (time.perf_counter() - start_total) * 1000
            total_times.append(total_time)
        except Exception as e:
            print(f"  Error parsing {filepath.name}: {e}")
            return None

    return {
        "parse_avg": sum(parse_times) / len(parse_times),
        "parse_min": min(parse_times),
        "parse_max": max(parse_times),
        "total_avg": sum(total_times) / len(total_times),
        "total_min": min(total_times),
        "total_max": max(total_times),
    }


def run_benchmarks(examples_dir: Path = Path("examples")) -> List[Tuple[str, Dict]]:
    """
    Run benchmarks on all example files.

    Args:
        examples_dir: Directory containing example YAML files

    Returns:
        List of (filename, results) tuples
    """
    results = []

    # Categories of examples to benchmark
    categories = {
        "v3.0 Auto-References": [
            "auto_references_box_stack.yaml",
            "auto_references_cylinder_assembly.yaml",
            "auto_references_rotation.yaml",
            "auto_references_with_offsets.yaml",
            "references_demo.yaml",
        ],
        "Primitives": [
            "simple_box.yaml",
            "simple_guitar_hanger.yaml",
        ],
        "Boolean Operations": [
            "guitar_hanger_with_holes.yaml",
            "bracket_with_hole.yaml",
        ],
        "Patterns": [
            "mounting_plate_with_bolt_circle.yaml",
        ],
        "Finishing": [
            "rounded_mounting_plate.yaml",
            "chamfered_bracket.yaml",
        ],
        "Sketch Operations": [
            "simple_extrude.yaml",
            "bottle_revolve.yaml",
            "pipe_sweep_simple.yaml",
            "transition_loft.yaml",
        ],
    }

    print("=" * 80)
    print("TiaCAD v3.0 Performance Benchmark")
    print("=" * 80)
    print()

    for category, files in categories.items():
        print(f"\n{category}")
        print("-" * 80)

        for filename in files:
            filepath = examples_dir / filename
            if not filepath.exists():
                print(f"  ⚠️  {filename:40s} [MISSING]")
                continue

            print(f"  {filename:40s} ", end="", flush=True)
            result = benchmark_file(filepath, iterations=3)

            if result:
                results.append((filename, result))
                print(f"Parse: {result['parse_avg']:6.2f}ms  Total: {result['total_avg']:6.2f}ms")
            else:
                print("[FAILED]")

    return results


def print_summary(results: List[Tuple[str, Dict]]):
    """Print benchmark summary statistics."""
    if not results:
        print("\nNo results to summarize")
        return

    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)

    parse_times = [r['parse_avg'] for _, r in results]
    total_times = [r['total_avg'] for _, r in results]

    print(f"\nTotal files benchmarked: {len(results)}")
    print(f"\nParse times:")
    print(f"  Average: {sum(parse_times) / len(parse_times):.2f}ms")
    print(f"  Min:     {min(parse_times):.2f}ms")
    print(f"  Max:     {max(parse_times):.2f}ms")

    print(f"\nTotal times:")
    print(f"  Average: {sum(total_times) / len(total_times):.2f}ms")
    print(f"  Min:     {min(total_times):.2f}ms")
    print(f"  Max:     {max(total_times):.2f}ms")

    # Find slowest files
    print(f"\nSlowest 5 files (parse time):")
    sorted_results = sorted(results, key=lambda x: x[1]['parse_avg'], reverse=True)
    for filename, result in sorted_results[:5]:
        print(f"  {filename:40s} {result['parse_avg']:6.2f}ms")

    print()


def main():
    """Run performance benchmarks."""
    try:
        results = run_benchmarks()
        print_summary(results)

        print("=" * 80)
        print("✓ Performance benchmark complete")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\nError running benchmarks: {e}")
        raise


if __name__ == "__main__":
    main()
