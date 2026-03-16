#!/usr/bin/env python3
"""
trust_render.py — render one or more TiaCAD YAML files for visual trust verification.

Usage:
    python scripts/trust_render.py examples/trust/box_basic.yaml
    python scripts/trust_render.py examples/trust/          # all YAMLs in a dir
    python scripts/trust_render.py --gallery                # all trust scenarios + HTML gallery
    python scripts/trust_render.py examples/pcb_standoff_assembly.yaml --out /tmp/pcb.png
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.visual.trust_renderer import render_trust

TRUST_EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "trust"
TRUST_OUTPUT_DIR = Path(__file__).parent.parent / "trust_output"


def render_file(yaml_path: Path, output_path: Path) -> bool:
    print(f"\n→ {yaml_path.name}")
    try:
        parser = TiaCADParser()
        doc = parser.parse_file(str(yaml_path))
        title = yaml_path.stem.replace("_", " ")
        out = render_trust(doc, str(output_path), title=title)
        print(f"  ✓ {out}")
        return True
    except Exception as e:
        print(f"  ✗ {e}")
        return False


def make_gallery(results: list, gallery_path: Path):
    """Generate a simple HTML gallery from (name, png_path, ok) tuples."""
    items = ""
    for name, png_path, ok in results:
        status = "✓" if ok else "✗ FAILED"
        rel = os.path.relpath(png_path, gallery_path.parent)
        items += f"""
        <div class="card {'failed' if not ok else ''}">
          <div class="label">{status} {name}</div>
          {'<img src="' + rel + '" alt="' + name + '">' if ok else '<div class="err">render failed</div>'}
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TiaCAD Trust Gallery</title>
<style>
  body {{ font-family: sans-serif; background: #f0f0f0; padding: 20px; }}
  h1 {{ color: #333; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 20px; }}
  .card {{ background: white; border-radius: 8px; padding: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.15); max-width: 740px; }}
  .card.failed {{ border: 2px solid #e63946; }}
  .label {{ font-weight: bold; margin-bottom: 8px; color: #333; font-size: 14px; }}
  .err {{ color: #e63946; padding: 20px; }}
  img {{ max-width: 100%; border-radius: 4px; }}
</style>
</head>
<body>
<h1>TiaCAD Trust Gallery</h1>
<p>Visual verification renders — each scenario should match its description.</p>
<div class="grid">{items}
</div>
</body>
</html>"""

    gallery_path.write_text(html)
    print(f"\n  Gallery: {gallery_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Render TiaCAD YAML for visual trust verification")
    parser.add_argument("paths", nargs="*", help="YAML file(s) or directory")
    parser.add_argument("--out", help="Output PNG path (single file only)")
    parser.add_argument("--gallery", action="store_true", help="Render all trust scenarios + generate HTML gallery")
    args = parser.parse_args()

    TRUST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.gallery or (not args.paths):
        # Render all trust scenarios
        yaml_files = sorted(TRUST_EXAMPLES_DIR.glob("*.yaml"))
        if not yaml_files:
            print(f"No YAML files found in {TRUST_EXAMPLES_DIR}")
            sys.exit(1)
        results = []
        for yf in yaml_files:
            out_path = TRUST_OUTPUT_DIR / (yf.stem + ".png")
            ok = render_file(yf, out_path)
            results.append((yf.stem, out_path, ok))
        make_gallery(results, TRUST_OUTPUT_DIR / "gallery.html")
        return

    # Collect input files
    yaml_files = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            yaml_files.extend(sorted(path.glob("*.yaml")))
        elif path.exists():
            yaml_files.append(path)
        else:
            print(f"Not found: {p}")
            sys.exit(1)

    if not yaml_files:
        print("No YAML files found")
        sys.exit(1)

    if args.out and len(yaml_files) == 1:
        out_path = Path(args.out)
    else:
        out_path = None

    results = []
    for yf in yaml_files:
        dest = out_path or (TRUST_OUTPUT_DIR / (yf.stem + ".png"))
        ok = render_file(yf, dest)
        results.append((yf.stem, dest, ok))

    if len(results) > 1:
        make_gallery(results, TRUST_OUTPUT_DIR / "gallery.html")

    failed = [r for r in results if not r[2]]
    if failed:
        print(f"\n{len(failed)} scenario(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
