#!/usr/bin/env python3
"""
Render TiaCAD demo files to multi-view grid composites.

Creates single PNG images showing multiple camera angles in a grid layout,
perfect for technical documentation and visual verification.
"""

from pathlib import Path
from tiacad_core.parser.tiacad_parser import TiaCADParser
from tiacad_core.visualization.renderer import ModelRenderer

def main():
    """Render demo files to grid composites"""

    # Paths
    examples_dir = Path("examples")
    output_dir = Path("output/renders")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Demo files to render
    demos = [
        ("color_demo.yaml", "TiaCAD Color System Demo"),
        ("multi_material_demo.yaml", "Multi-Material 3D Printing Demo")
    ]

    # Grid configurations
    grid_configs = [
        {
            'name': '2x2',
            'views': ['isometric', 'front', 'top', 'right'],
            'grid_size': (2, 2),
            'cell_size': (600, 450)
        },
        {
            'name': '6view',
            'views': ['isometric', 'front', 'back', 'top', 'bottom', 'right'],
            'grid_size': (3, 2),
            'cell_size': (500, 400)
        }
    ]

    renderer = ModelRenderer()

    for demo_file, title in demos:
        demo_path = examples_dir / demo_file

        if not demo_path.exists():
            print(f"⚠️  {demo_file} not found, skipping")
            continue

        print(f"\n{'='*70}")
        print(f"📋 {title}")
        print(f"{'='*70}")

        try:
            # Parse YAML
            print(f"📖 Parsing {demo_file}...")
            doc = TiaCADParser.parse_file(str(demo_path))

            num_parts = len(doc.parts.list_parts())
            print(f"✓ Loaded {num_parts} parts")

            # Render each grid configuration
            for config in grid_configs:
                base_name = demo_file.replace('.yaml', '')
                output_file = output_dir / f"{base_name}_grid_{config['name']}.png"

                print(f"\n🎨 Creating {config['name']} grid ({len(config['views'])} views)...")

                renderer.render_grid(
                    doc.parts,
                    str(output_file),
                    views=config['views'],
                    grid_size=config['grid_size'],
                    cell_size=config['cell_size'],
                    title=title,
                    show_labels=True,
                    show_edges=False
                )

                file_size = output_file.stat().st_size // 1024
                print(f"✓ Saved: {output_file.name} ({file_size}KB)")

        except Exception as e:
            print(f"❌ Error rendering {demo_file}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"✨ Grid composites complete!")
    print(f"📁 Output: {output_dir.absolute()}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
