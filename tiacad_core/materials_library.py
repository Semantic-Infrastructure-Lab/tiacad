"""
TiaCAD Material Library

Built-in materials with realistic PBR properties for rendering and export.

Design Goals:
- Physically accurate colors
- Professional quality
- Common engineering materials
- 3D printing materials
- Easy to extend
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Material:
    """Material definition with PBR properties"""

    name: str
    color: Tuple[float, float, float]  # RGB 0-1
    finish: str = 'satin'  # matte, satin, glossy, metallic, brushed, polished, anodized
    metalness: float = 0.0  # 0=dielectric, 1=metal
    roughness: float = 0.5  # 0=mirror, 1=rough
    opacity: float = 1.0  # 0=transparent, 1=opaque

    # Optional physical properties
    density: Optional[float] = None  # g/cm³
    cost: Optional[float] = None  # $/kg

    # Optional manufacturing properties
    print_material: Optional[str] = None
    cnc_suitable: bool = True

    def copy(self) -> 'Material':
        """Create a copy for customization"""
        return Material(
            name=self.name,
            color=self.color,
            finish=self.finish,
            metalness=self.metalness,
            roughness=self.roughness,
            opacity=self.opacity,
            density=self.density,
            cost=self.cost,
            print_material=self.print_material,
            cnc_suitable=self.cnc_suitable
        )

    def update(self, **kwargs):
        """Update properties"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# ============================================================================
# BUILT-IN MATERIAL LIBRARY
# ============================================================================

METALS = {
    'aluminum': Material(
        name='aluminum',
        color=(0.75, 0.75, 0.75),  # Light gray
        finish='brushed',
        metalness=0.95,
        roughness=0.4,
        density=2.7,  # g/cm³
        cost=3.0,  # $/kg (approximate)
        cnc_suitable=True
    ),

    'aluminum-anodized-black': Material(
        name='aluminum-anodized-black',
        color=(0.15, 0.15, 0.15),
        finish='anodized',
        metalness=0.9,
        roughness=0.25,
        density=2.7,
        cost=5.0
    ),

    'aluminum-anodized-blue': Material(
        name='aluminum-anodized-blue',
        color=(0.20, 0.40, 0.80),
        finish='anodized',
        metalness=0.9,
        roughness=0.25,
        density=2.7,
        cost=5.0
    ),

    'aluminum-anodized-red': Material(
        name='aluminum-anodized-red',
        color=(0.80, 0.20, 0.20),
        finish='anodized',
        metalness=0.9,
        roughness=0.25,
        density=2.7,
        cost=5.0
    ),

    'steel': Material(
        name='steel',
        color=(0.50, 0.50, 0.50),  # Medium gray
        finish='polished',
        metalness=0.98,
        roughness=0.2,
        density=7.85,
        cost=1.0
    ),

    'steel-brushed': Material(
        name='steel-brushed',
        color=(0.50, 0.50, 0.50),
        finish='brushed',
        metalness=0.98,
        roughness=0.35,
        density=7.85,
        cost=1.0
    ),

    'stainless': Material(
        name='stainless',
        color=(0.55, 0.55, 0.55),
        finish='polished',
        metalness=0.98,
        roughness=0.15,
        density=8.0,
        cost=4.0
    ),

    'brass': Material(
        name='brass',
        color=(0.88, 0.78, 0.50),  # Gold-ish
        finish='polished',
        metalness=0.95,
        roughness=0.3,
        density=8.5,
        cost=7.0
    ),

    'brass-aged': Material(
        name='brass-aged',
        color=(0.65, 0.55, 0.35),  # Darker, oxidized
        finish='satin',
        metalness=0.9,
        roughness=0.5,
        density=8.5,
        cost=7.0
    ),

    'copper': Material(
        name='copper',
        color=(0.95, 0.64, 0.54),  # Reddish
        finish='polished',
        metalness=0.96,
        roughness=0.25,
        density=8.96,
        cost=10.0
    ),

    'bronze': Material(
        name='bronze',
        color=(0.80, 0.50, 0.20),
        finish='satin',
        metalness=0.94,
        roughness=0.4,
        density=8.8,
        cost=8.0
    ),

    'titanium': Material(
        name='titanium',
        color=(0.65, 0.65, 0.70),  # Slightly blue-gray
        finish='brushed',
        metalness=0.97,
        roughness=0.35,
        density=4.5,
        cost=30.0
    ),

    'chrome': Material(
        name='chrome',
        color=(0.80, 0.80, 0.82),
        finish='polished',
        metalness=0.99,
        roughness=0.05,  # Very shiny
        density=7.19,
        cost=15.0
    ),

    'gold': Material(
        name='gold',
        color=(1.00, 0.84, 0.00),
        finish='polished',
        metalness=0.99,
        roughness=0.15,
        density=19.3,
        cost=60000.0  # Expensive!
    ),

    'silver': Material(
        name='silver',
        color=(0.95, 0.95, 0.95),
        finish='polished',
        metalness=0.99,
        roughness=0.1,
        density=10.5,
        cost=800.0
    ),
}

PLASTICS = {
    'abs-white': Material(
        name='abs-white',
        color=(0.95, 0.95, 0.95),
        finish='satin',
        metalness=0.0,
        roughness=0.5,
        density=1.04,
        cost=5.0,
        print_material='ABS'
    ),

    'abs-black': Material(
        name='abs-black',
        color=(0.05, 0.05, 0.05),
        finish='satin',
        metalness=0.0,
        roughness=0.5,
        density=1.04,
        cost=5.0,
        print_material='ABS'
    ),

    'pla-red': Material(
        name='pla-red',
        color=(0.85, 0.15, 0.15),
        finish='satin',
        metalness=0.0,
        roughness=0.4,
        density=1.24,
        cost=3.0,
        print_material='PLA'
    ),

    'pla-blue': Material(
        name='pla-blue',
        color=(0.15, 0.40, 0.85),
        finish='satin',
        metalness=0.0,
        roughness=0.4,
        density=1.24,
        cost=3.0,
        print_material='PLA'
    ),

    'pla-green': Material(
        name='pla-green',
        color=(0.15, 0.70, 0.15),
        finish='satin',
        metalness=0.0,
        roughness=0.4,
        density=1.24,
        cost=3.0,
        print_material='PLA'
    ),

    'pla-natural': Material(
        name='pla-natural',
        color=(0.95, 0.92, 0.85),  # Slightly yellow-white
        finish='satin',
        metalness=0.0,
        roughness=0.4,
        density=1.24,
        cost=2.5,
        print_material='PLA'
    ),

    'petg-clear': Material(
        name='petg-clear',
        color=(1.0, 1.0, 1.0),
        finish='glossy',
        metalness=0.0,
        roughness=0.1,
        opacity=0.3,  # Transparent!
        density=1.27,
        cost=4.0,
        print_material='PETG'
    ),

    'petg-black': Material(
        name='petg-black',
        color=(0.05, 0.05, 0.05),
        finish='glossy',
        metalness=0.0,
        roughness=0.3,
        density=1.27,
        cost=4.0,
        print_material='PETG'
    ),

    'tpu-flexible': Material(
        name='tpu-flexible',
        color=(0.20, 0.20, 0.20),
        finish='matte',
        metalness=0.0,
        roughness=0.7,
        density=1.21,
        cost=8.0,
        print_material='TPU',
        cnc_suitable=False
    ),

    'nylon-natural': Material(
        name='nylon-natural',
        color=(0.95, 0.95, 0.90),
        finish='satin',
        metalness=0.0,
        roughness=0.45,
        density=1.14,
        cost=10.0,
        print_material='Nylon'
    ),
}

WOODS = {
    'oak': Material(
        name='oak',
        color=(0.76, 0.60, 0.42),
        finish='satin',
        metalness=0.0,
        roughness=0.6,
        density=0.75,
        cost=5.0,
        cnc_suitable=True
    ),

    'walnut': Material(
        name='walnut',
        color=(0.36, 0.25, 0.20),
        finish='satin',
        metalness=0.0,
        roughness=0.5,
        density=0.64,
        cost=12.0
    ),

    'maple': Material(
        name='maple',
        color=(0.90, 0.82, 0.70),
        finish='satin',
        metalness=0.0,
        roughness=0.55,
        density=0.71,
        cost=8.0
    ),

    'cherry': Material(
        name='cherry',
        color=(0.73, 0.41, 0.28),
        finish='satin',
        metalness=0.0,
        roughness=0.5,
        density=0.58,
        cost=10.0
    ),

    'pine': Material(
        name='pine',
        color=(0.91, 0.76, 0.52),
        finish='satin',
        metalness=0.0,
        roughness=0.65,
        density=0.52,
        cost=3.0
    ),

    'mahogany': Material(
        name='mahogany',
        color=(0.49, 0.25, 0.15),
        finish='glossy',
        metalness=0.0,
        roughness=0.4,
        density=0.70,
        cost=15.0
    ),
}

# Named colors for convenience
NAMED_COLORS = {
    # Basic colors
    'red': (1.0, 0.0, 0.0),
    'green': (0.0, 1.0, 0.0),
    'blue': (0.0, 0.0, 1.0),
    'yellow': (1.0, 1.0, 0.0),
    'orange': (1.0, 0.5, 0.0),
    'purple': (0.5, 0.0, 0.5),
    'pink': (1.0, 0.5, 0.8),
    'brown': (0.6, 0.3, 0.1),

    # Neutrals
    'white': (1.0, 1.0, 1.0),
    'black': (0.0, 0.0, 0.0),
    'gray': (0.5, 0.5, 0.5),
    'grey': (0.5, 0.5, 0.5),
    'silver': (0.75, 0.75, 0.75),

    # Extended
    'cyan': (0.0, 1.0, 1.0),
    'magenta': (1.0, 0.0, 1.0),
    'lime': (0.5, 1.0, 0.0),
    'navy': (0.0, 0.0, 0.5),
    'teal': (0.0, 0.5, 0.5),
    'olive': (0.5, 0.5, 0.0),
    'maroon': (0.5, 0.0, 0.0),
}


# ============================================================================
# MATERIAL LIBRARY CLASS
# ============================================================================

class MaterialLibrary:
    """Manages built-in and custom materials"""

    def __init__(self):
        # Combine all built-in materials
        self.built_in = {}
        self.built_in.update(METALS)
        self.built_in.update(PLASTICS)
        self.built_in.update(WOODS)

        # Custom materials defined in YAML
        self.custom = {}

    def get(self, name: str) -> Material:
        """Get material by name (custom takes precedence)"""
        name_lower = name.lower()

        if name_lower in self.custom:
            return self.custom[name_lower]
        elif name_lower in self.built_in:
            return self.built_in[name_lower]
        else:
            # Try to find close matches
            matches = self._find_similar(name_lower)
            if matches:
                raise ValueError(
                    f"Unknown material '{name}'\n"
                    f"Did you mean: {', '.join(matches[:3])}?\n\n"
                    f"Available materials:\n"
                    f"  Metals: {', '.join(sorted(METALS.keys())[:5])}, ...\n"
                    f"  Plastics: {', '.join(sorted(PLASTICS.keys())[:5])}, ...\n"
                    f"  Woods: {', '.join(sorted(WOODS.keys())[:5])}, ..."
                )
            else:
                raise ValueError(
                    f"Unknown material '{name}'\n\n"
                    f"Available materials:\n"
                    f"  Metals: {', '.join(sorted(METALS.keys()))}\n"
                    f"  Plastics: {', '.join(sorted(PLASTICS.keys()))}\n"
                    f"  Woods: {', '.join(sorted(WOODS.keys()))}"
                )

    def define(self, name: str, spec: dict):
        """Define custom material"""
        if 'base' in spec:
            # Extend existing material
            base = self.get(spec['base'])
            material = base.copy()

            # Override with spec
            if 'color' in spec:
                material.color = spec['color']
            if 'finish' in spec:
                material.finish = spec['finish']
            if 'metalness' in spec:
                material.metalness = spec['metalness']
            if 'roughness' in spec:
                material.roughness = spec['roughness']
            if 'opacity' in spec:
                material.opacity = spec['opacity']

            material.name = name
        else:
            # Create from scratch
            material = Material(
                name=name,
                color=spec.get('color', (0.7, 0.7, 0.7)),
                finish=spec.get('finish', 'satin'),
                metalness=spec.get('metalness', 0.0),
                roughness=spec.get('roughness', 0.5),
                opacity=spec.get('opacity', 1.0),
                density=spec.get('density'),
                cost=spec.get('cost'),
                print_material=spec.get('print_material'),
                cnc_suitable=spec.get('cnc_suitable', True)
            )

        self.custom[name.lower()] = material

    def list_all(self) -> List[str]:
        """List all available material names"""
        return sorted(list(self.built_in.keys()) + list(self.custom.keys()))

    def _find_similar(self, name: str) -> List[str]:
        """Find similar material names (simple fuzzy match)"""
        from difflib import get_close_matches
        all_names = self.list_all()
        return get_close_matches(name, all_names, n=3, cutoff=0.6)


# Singleton instance
_material_library = MaterialLibrary()


def get_material_library() -> MaterialLibrary:
    """Get the global material library instance"""
    return _material_library
