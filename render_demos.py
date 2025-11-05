#!/usr/bin/env python3
"""
Render TiaCAD demo files to PNG images for visual inspection.

This script renders the color_demo.yaml and multi_material_demo.yaml files
to PNG images from multiple angles, showing the 3D models with their proper
materials and colors.
"""

from pathlib import Path
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.visualization.renderer import ModelRenderer

def main():
    """Render demo files"""

    # Paths
    examples_dir = Path("examples")
    output_dir = Path("output/renders")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Demo files to render
    demos = [
        ("color_demo.yaml", "Demo with 7 colored parts"),
        ("multi_material_demo.yaml", "Multi-material demo")
    ]

    # Camera angles to render
    views = ['isometric', 'front', 'top', 'right']

    renderer = ModelRenderer()

    for demo_file, description in demos:
        demo_path = examples_dir / demo_file

        if not demo_path.exists():
            print(f"⚠️  {demo_file} not found, skipping")
            continue

        print(f"\n{'='*60}")
        print(f"Rendering: {demo_file}")
        print(f"Description: {description}")
        print(f"{'='*60}")

        try:
            # Parse YAML
            print(f"📖 Parsing {demo_file}...")
            doc = TiaCADParser.parse_file(str(demo_path))

            # Count parts
            num_parts = len(doc.parts.list_parts())
            print(f"✓ Parsed successfully: {num_parts} parts")

            # List parts with colors
            print(f"\nParts:")
            for part_name in doc.parts.list_parts():
                part = doc.parts.get(part_name)
                if 'color' in part.metadata:
                    r, g, b, a = part.metadata['color']
                    color_str = f"RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})"
                elif 'material' in part.metadata:
                    color_str = f"Material: {part.metadata['material']}"
                else:
                    color_str = "No color/material"
                print(f"  - {part_name:20s} {color_str}")

            # Render assembly
            base_name = demo_file.replace('.yaml', '')
            output_path = output_dir / base_name

            print(f"\n🎨 Rendering from {len(views)} angles...")
            files = renderer.render_assembly(
                doc.parts,
                str(output_path),
                views=views,
                show_edges=False
            )

            print(f"\n✓ Rendered {len(files)} images:")
            for f in files:
                file_size = Path(f).stat().st_size // 1024
                print(f"  - {Path(f).name:40s} ({file_size}KB)")

        except Exception as e:
            print(f"❌ Error rendering {demo_file}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"✨ All renders complete!")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
