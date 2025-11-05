# TiaCAD Color System - Complete Specification

**Status:** Full Implementation Spec
**Version:** 1.0.0
**Date:** 2025-10-25
**Approach:** Go Full - All Features Day 1

---

## Philosophy: Opinionated Excellence

**Principles:**
1. **Support all workflows** - From "color: red" to full PBR materials
2. **Smart defaults** - Beautiful out of the box
3. **Professional quality** - Production-ready materials
4. **Future-proof** - Room for textures, CAM, simulation

---

## Complete YAML Schema

### Top-Level Sections

```yaml
metadata:
  name: My Design
  description: ...

# NEW: Color palette definitions
colors:
  <color-name>: <color-value>
  # OR detailed
  <color-name>:
    value: <color-value>
    description: "Human readable"
    metalness: 0-1
    roughness: 0-1

# NEW: Material library
materials:
  <material-name>:
    base: <preset-material>      # Optional: extend built-in
    color: <color-value>
    finish: matte|satin|glossy|metallic|brushed|polished|anodized
    metalness: 0-1               # PBR: how metallic (0=dielectric, 1=metal)
    roughness: 0-1               # PBR: surface roughness (0=mirror, 1=rough)
    opacity: 0-1                 # Optional: transparency (0=transparent, 1=opaque)

    # Future: Physical properties
    density: <g/cm³>
    cost: <$/kg>

    # Future: Manufacturing
    print_material: <filament>
    cnc_feeds_speeds: {...}

parameters:
  # Existing parameters

parts:
  <part-name>:
    primitive: ...

    # COLOR OPTIONS (choose one approach):

    # Option 1: Simple inline color
    color: <color-value>

    # Option 2: Reference palette
    color: <color-name>          # From colors: section

    # Option 3: Material preset
    material: <material-name>    # From materials: section or built-in

    # Option 4: Full appearance definition
    appearance:
      color: <color-value>
      finish: matte|satin|glossy|metallic|brushed|polished
      metalness: 0-1
      roughness: 0-1
      opacity: 0-1

operations:
  # Operations can override color/material
  <operation-name>:
    type: ...
    color: <color-value>         # Optional: override result color
    material: <material-name>    # Optional: override result material

export:
  default_part: ...
  formats:                       # Multiple export formats
    - stl                        # Geometry only (no color)
    - step                       # CAD with colors
    - obj                        # 3D with materials (.mtl file)
    - 3mf                        # Multi-color printing

  # Export options
  color_mode: realistic|schematic|print|custom
  default_color: <color-value> # For parts without color
```

---

## Color Value Formats

**All formats supported, auto-detected:**

### 1. Named Colors

```yaml
color: red
color: blue
color: aluminum
color: steel
color: primary          # Reference to colors: section
```

**Built-in Named Colors:**
- **Basic:** red, green, blue, yellow, orange, purple, pink, brown
- **Neutrals:** white, black, gray, silver, gold
- **Extended:** cyan, magenta, lime, navy, teal, olive, maroon
- **Materials:** aluminum, steel, brass, copper, bronze, titanium, chrome
- **Woods:** oak, walnut, maple, cherry, pine
- **Plastics:** abs-white, abs-black, pla-natural, petg-clear

### 2. Hex Strings

```yaml
color: "#FF0000"        # Red
color: "#0066CC"        # Blue
color: "#FF0000FF"      # Red with alpha (RGBA hex)
color: "#0066CC80"      # Blue, 50% transparent
```

### 3. RGB/RGBA Arrays (0-1 range)

```yaml
color: [1.0, 0.0, 0.0]           # Red (RGB)
color: [0.0, 0.4, 0.8]           # Blue
color: [1.0, 0.0, 0.0, 0.5]      # Red, 50% transparent (RGBA)
```

### 4. RGB/RGBA Objects (0-255 range)

```yaml
color:
  r: 255
  g: 0
  b: 0
  a: 128    # Optional alpha
```

### 5. HSL Objects

```yaml
color:
  h: 0      # Hue: 0-360 degrees
  s: 100    # Saturation: 0-100%
  l: 50     # Lightness: 0-100%
  a: 0.5    # Optional alpha: 0-1
```

---

## Material Library

### Built-In Materials

**Metals:**

```yaml
# These work out of the box, no definition needed:

material: aluminum      # Brushed aluminum (common)
material: steel         # Polished steel
material: stainless     # Stainless steel
material: brass         # Polished brass
material: copper        # Polished copper
material: bronze        # Bronze
material: titanium      # Titanium
material: chrome        # Chrome plated
material: gold          # Gold
material: silver        # Silver

# Variations:
material: aluminum-anodized-black
material: aluminum-anodized-blue
material: steel-brushed
material: brass-aged
```

**Properties:**
```yaml
aluminum:
  color: [0.75, 0.75, 0.75]
  finish: brushed
  metalness: 0.95
  roughness: 0.4
  density: 2.7

steel:
  color: [0.50, 0.50, 0.50]
  finish: polished
  metalness: 0.98
  roughness: 0.2
  density: 7.85

brass:
  color: [0.88, 0.78, 0.50]
  finish: polished
  metalness: 0.95
  roughness: 0.3
  density: 8.5
```

**Plastics:**

```yaml
material: abs-white
material: abs-black
material: pla-red
material: pla-blue
material: petg-clear
material: tpu-flexible
material: nylon-natural
```

**Properties:**
```yaml
abs-white:
  color: [0.95, 0.95, 0.95]
  finish: satin
  metalness: 0.0
  roughness: 0.5
  density: 1.04
  print_material: ABS

petg-clear:
  color: [1.0, 1.0, 1.0]
  finish: glossy
  metalness: 0.0
  roughness: 0.1
  opacity: 0.3
  density: 1.27
```

**Woods:**

```yaml
material: oak
material: walnut
material: maple
material: cherry
material: pine
material: mahogany
```

**Properties:**
```yaml
oak:
  color: [0.76, 0.60, 0.42]
  finish: satin
  metalness: 0.0
  roughness: 0.6
  density: 0.75

walnut:
  color: [0.36, 0.25, 0.20]
  finish: satin
  metalness: 0.0
  roughness: 0.5
  density: 0.64
```

---

## Color Palette System

### Simple Palette

```yaml
colors:
  primary: "#0066CC"
  secondary: "#CC6600"
  accent: "#CC0066"
  neutral: "#808080"

  light: "#F0F0F0"
  dark: "#333333"

parts:
  main_body: {color: primary}
  detail: {color: accent}
  frame: {color: neutral}
```

### Advanced Palette

```yaml
colors:
  # Simple colors
  brand-blue: "#0066CC"

  # Detailed colors with PBR
  custom-aluminum:
    value: "#AABBCC"
    description: "Custom anodized blue aluminum"
    metalness: 0.9
    roughness: 0.3
    finish: anodized

  # Reference materials
  frame-material:
    base: aluminum
    color: "#6699CC"
    finish: anodized

parts:
  cover: {color: brand-blue}
  bracket: {color: custom-aluminum}
  frame: {color: frame-material}
```

---

## Complete Examples

### Example 1: Simple Colors

```yaml
metadata:
  name: Color Basics
  description: Simple color usage

parts:
  red_box:
    primitive: box
    size: [10, 10, 10]
    color: red

  blue_cylinder:
    primitive: cylinder
    radius: 5
    height: 20
    color: "#0066CC"

  green_sphere:
    primitive: sphere
    radius: 8
    color: [0.0, 0.8, 0.0]

export:
  default_part: red_box
  formats: [stl, step]
```

### Example 2: Material Presets

```yaml
metadata:
  name: Realistic Materials
  description: Using built-in material library

parts:
  aluminum_bracket:
    primitive: box
    size: [80, 80, 6]
    material: aluminum

  steel_bolt:
    primitive: cylinder
    radius: 3
    height: 20
    material: steel

  brass_spacer:
    primitive: cylinder
    radius: 5
    height: 10
    material: brass

export:
  default_part: aluminum_bracket
  formats: [step, obj]
  color_mode: realistic
```

### Example 3: Design System

```yaml
metadata:
  name: Corporate Design
  description: Brand color palette

colors:
  # Corporate colors
  acme-blue: "#0066CC"
  acme-orange: "#CC6600"
  acme-gray: "#808080"

  # Functional colors
  structure: aluminum
  fasteners: steel
  highlights: acme-orange

parts:
  main_housing:
    primitive: box
    size: [100, 100, 50]
    color: acme-blue

  mounting_bracket:
    primitive: box
    size: [80, 80, 6]
    color: structure

  bolt:
    primitive: cylinder
    radius: 3
    height: 20
    color: fasteners

  logo_plate:
    primitive: box
    size: [40, 20, 2]
    color: highlights

export:
  default_part: main_housing
  formats: [step, obj]
```

### Example 4: Multi-Material 3D Printing

```yaml
metadata:
  name: Multi-Material Print
  description: Different filaments for different parts

materials:
  # Main structure
  black-pla:
    base: pla-black
    color: "#000000"
    print_material: "Generic PLA - Black"

  # Flexible seal
  red-tpu:
    base: tpu-flexible
    color: "#CC0000"
    print_material: "NinjaFlex TPU - Red"

  # Transparent window
  clear-petg:
    base: petg-clear
    color: [1.0, 1.0, 1.0]
    opacity: 0.3
    print_material: "eSUN PETG - Clear"

parts:
  enclosure_body:
    primitive: box
    size: [100, 80, 60]
    material: black-pla

  window:
    primitive: box
    size: [40, 2, 30]
    material: clear-petg

  gasket:
    primitive: box
    size: [90, 70, 2]
    material: red-tpu

export:
  default_part: enclosure_body
  formats: [3mf]  # 3MF supports multi-material
  color_mode: print
```

### Example 5: Advanced PBR Materials

```yaml
metadata:
  name: Custom Materials
  description: Full PBR control

materials:
  # Anodized aluminum
  blue-anodized:
    base: aluminum
    color: "#3366CC"
    finish: anodized
    metalness: 0.9
    roughness: 0.25

  # Brushed stainless
  brushed-stainless:
    base: stainless
    finish: brushed
    roughness: 0.35

  # Matte black plastic
  matte-black-abs:
    base: abs-black
    finish: matte
    roughness: 0.8

parts:
  main_body:
    primitive: box
    size: [100, 100, 50]
    material: blue-anodized

  handle:
    primitive: cylinder
    radius: 15
    height: 80
    material: brushed-stainless

  knob:
    primitive: cylinder
    radius: 20
    height: 15
    material: matte-black-abs

export:
  formats: [step, obj]
  color_mode: realistic
```

### Example 6: Transparency & Opacity

```yaml
metadata:
  name: Transparent Parts
  description: Using opacity for windows and enclosures

parts:
  opaque_base:
    primitive: box
    size: [100, 100, 10]
    color: "#333333"

  transparent_window:
    primitive: box
    size: [80, 80, 2]
    appearance:
      color: [0.8, 0.9, 1.0]  # Light blue
      opacity: 0.3            # 30% opaque (70% transparent)
      finish: glossy

  translucent_cover:
    primitive: box
    size: [100, 100, 20]
    appearance:
      color: white
      opacity: 0.6            # 60% opaque
      finish: satin

export:
  formats: [obj, step]
```

---

## Export Format Support

### STL Export
```yaml
export:
  formats: [stl]
  # Note: STL has no color support
  # Use for:
  # - 3D printing (single material)
  # - CNC machining
  # - Universal compatibility
```

### STEP Export (Recommended for Color)
```yaml
export:
  formats: [step]
  color_mode: realistic

  # STEP supports:
  # - Colors per part
  # - Assembly structure
  # - Exact geometry (no triangulation)
  # - Professional CAD compatibility
  # Opens in: SolidWorks, Fusion 360, FreeCAD, etc.
```

### OBJ Export (Best for Rendering)
```yaml
export:
  formats: [obj]
  include_mtl: true  # Generate .mtl material file

  # OBJ + MTL supports:
  # - Full PBR materials
  # - Textures (future)
  # - Rendering engines
  # Opens in: Blender, Maya, 3ds Max, etc.
```

### 3MF Export (Best for Multi-Color Printing)
```yaml
export:
  formats: [3mf]
  color_mode: print

  # 3MF supports:
  # - Multiple materials
  # - Color per object
  # - Modern slicers
  # Opens in: PrusaSlicer, Cura, Simplify3D, etc.
```

### Multiple Formats
```yaml
export:
  formats: [stl, step, obj, 3mf]

  # Generates:
  # - design.stl (geometry only)
  # - design.step (CAD with colors)
  # - design.obj + design.mtl (rendering)
  # - design.3mf (printing)
```

---

## Color Modes

### Realistic Mode
```yaml
export:
  color_mode: realistic

# Uses:
# - Actual material colors (aluminum, steel, etc.)
# - PBR properties for realistic rendering
# - Best for: Presentations, marketing, visualization
```

### Schematic Mode
```yaml
export:
  color_mode: schematic

# Uses:
# - High contrast colors for differentiation
# - Ignores materials, uses bright colors
# - Best for: Assembly instructions, documentation
```

### Print Mode
```yaml
export:
  color_mode: print

# Uses:
# - Maps to actual print materials
# - Respects print_material properties
# - Best for: 3D printing, manufacturing
```

### Custom Mode
```yaml
export:
  color_mode: custom
  color_mapping:
    aluminum: "#AABBCC"   # Custom colors per material
    steel: "#667788"
    default: "#CCCCCC"
```

---

## Parser Implementation

### Color Parser Interface

```python
class ColorParser:
    """Parse all color value formats"""

    def parse(self, value: Any) -> Color:
        """Auto-detect format and parse

        Supports:
        - Named colors: "red", "aluminum"
        - Hex: "#FF0000"
        - RGB array: [1.0, 0.0, 0.0]
        - RGBA array: [1.0, 0.0, 0.0, 0.5]
        - RGB object: {r: 255, g: 0, b: 0}
        - HSL object: {h: 0, s: 100, l: 50}
        """
        if isinstance(value, str):
            return self._parse_string(value)
        elif isinstance(value, list):
            return self._parse_array(value)
        elif isinstance(value, dict):
            return self._parse_object(value)
        else:
            raise ValueError(f"Invalid color format: {value}")

    def _parse_string(self, s: str) -> Color:
        if s.startswith('#'):
            return self._parse_hex(s)
        else:
            return self._parse_named(s)

    # ... implementation details
```

### Material System

```python
class MaterialLibrary:
    """Built-in and custom material definitions"""

    BUILT_IN_MATERIALS = {
        'aluminum': Material(
            color=[0.75, 0.75, 0.75],
            finish='brushed',
            metalness=0.95,
            roughness=0.4,
            density=2.7
        ),
        'steel': Material(
            color=[0.50, 0.50, 0.50],
            finish='polished',
            metalness=0.98,
            roughness=0.2,
            density=7.85
        ),
        # ... more materials
    }

    def __init__(self):
        self.custom_materials = {}

    def get(self, name: str) -> Material:
        """Get material by name (custom or built-in)"""
        if name in self.custom_materials:
            return self.custom_materials[name]
        elif name in self.BUILT_IN_MATERIALS:
            return self.BUILT_IN_MATERIALS[name]
        else:
            raise ValueError(f"Unknown material: {name}")

    def define(self, name: str, spec: dict):
        """Define custom material"""
        if 'base' in spec:
            # Extend existing material
            base = self.get(spec['base'])
            material = base.copy()
            material.update(spec)
        else:
            # Create from scratch
            material = Material.from_spec(spec)

        self.custom_materials[name] = material
```

---

## Validation Rules

### Color Validation

```python
def validate_color(value: Any) -> List[str]:
    """Return validation errors"""
    errors = []

    # Check format
    if isinstance(value, str):
        if value.startswith('#'):
            if not re.match(r'^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$', value):
                errors.append(f"Invalid hex color: {value}")
        # else: named color, check later

    elif isinstance(value, list):
        if len(value) not in [3, 4]:
            errors.append(f"RGB array must have 3 or 4 values, got {len(value)}")
        if not all(0 <= v <= 1 for v in value):
            errors.append("RGB values must be 0-1")

    elif isinstance(value, dict):
        if 'r' in value:
            # RGB object
            required = ['r', 'g', 'b']
            missing = [k for k in required if k not in value]
            if missing:
                errors.append(f"Missing RGB keys: {missing}")
            # Check ranges (0-255)
            for k in ['r', 'g', 'b', 'a']:
                if k in value and not (0 <= value[k] <= 255):
                    errors.append(f"{k} must be 0-255, got {value[k]}")

        elif 'h' in value:
            # HSL object
            required = ['h', 's', 'l']
            missing = [k for k in required if k not in value]
            if missing:
                errors.append(f"Missing HSL keys: {missing}")
            # Check ranges
            if not (0 <= value.get('h', 0) <= 360):
                errors.append("Hue must be 0-360")
            if not (0 <= value.get('s', 0) <= 100):
                errors.append("Saturation must be 0-100")
            if not (0 <= value.get('l', 0) <= 100):
                errors.append("Lightness must be 0-100")

    return errors
```

---

## Default Behaviors

### No Color Specified

```python
# Default: Neutral gray
DEFAULT_COLOR = [0.7, 0.7, 0.7]  # Light gray

# Or: Random per part (for differentiation)
def random_color(seed: str) -> Color:
    """Deterministic random color based on part name"""
    random.seed(seed)
    h = random.random() * 360
    return hsl_to_rgb(h, 70, 60)  # Pastel colors
```

### Color Inheritance

```yaml
parts:
  base: {color: red}

operations:
  moved_base:
    type: transform
    input: base
    # Inherits red color automatically

  painted_base:
    type: transform
    input: base
    color: blue
    # Override: now blue
```

**Rule:** Operations inherit color from input, unless explicitly overridden

---

## Error Messages

### Clear, Helpful Errors

```
Error: Invalid color value 'rde' in part 'my_part'
  Did you mean: red?

  Valid named colors: red, green, blue, aluminum, steel, ...
  Or use hex: "#FF0000"
  Or use RGB: [1.0, 0.0, 0.0]
```

```
Error: Unknown material 'alumnium' in part 'bracket'
  Did you mean: aluminum?

  Built-in materials:
    Metals: aluminum, steel, brass, copper, ...
    Plastics: abs-white, pla-red, petg-clear, ...
    Woods: oak, walnut, maple, ...

  Or define custom material in 'materials:' section
```

```
Error: RGB values must be 0-1, got [255, 0, 0] in part 'my_part'

  For 0-255 range, use object syntax:
    color: {r: 255, g: 0, b: 0}

  For 0-1 range, use array:
    color: [1.0, 0.0, 0.0]
```

---

## Testing Strategy

### Unit Tests

```python
def test_parse_named_color():
    color = ColorParser().parse("red")
    assert color.rgb == [1.0, 0.0, 0.0]

def test_parse_hex_color():
    color = ColorParser().parse("#FF0000")
    assert color.rgb == [1.0, 0.0, 0.0]

def test_parse_rgb_array():
    color = ColorParser().parse([1.0, 0.0, 0.0])
    assert color.rgb == [1.0, 0.0, 0.0]

def test_parse_rgba_array():
    color = ColorParser().parse([1.0, 0.0, 0.0, 0.5])
    assert color.rgb == [1.0, 0.0, 0.0]
    assert color.alpha == 0.5

def test_material_library():
    lib = MaterialLibrary()
    mat = lib.get('aluminum')
    assert mat.metalness == 0.95
```

### Integration Tests

```python
def test_color_in_yaml():
    yaml = """
    parts:
      red_box:
        primitive: box
        size: [10, 10, 10]
        color: red
    """
    result = parse_yaml(yaml)
    assert result.parts['red_box'].color.rgb == [1.0, 0.0, 0.0]

def test_material_preset():
    yaml = """
    parts:
      bracket:
        primitive: box
        material: aluminum
    """
    result = parse_yaml(yaml)
    assert result.parts['bracket'].material.name == 'aluminum'

def test_custom_material():
    yaml = """
    materials:
      custom:
        base: aluminum
        color: "#6699CC"

    parts:
      part:
        material: custom
    """
    result = parse_yaml(yaml)
    assert result.parts['part'].material.color.hex == "#6699CC"
```

---

## Documentation Updates

### YAML_REFERENCE.md Additions

- Color value formats section
- Material presets table
- Palette system examples
- Export formats comparison

### TUTORIAL.md Additions

- "Adding Colors" chapter
- "Using Materials" chapter
- "Multi-color printing" tutorial

### EXAMPLES_GUIDE.md Additions

- Example 7: Colorful Assembly
- Example 8: Multi-Material Print

---

## Roadmap

### Phase 1: Core Color (Week 1)
- ✅ Color parser (all formats)
- ✅ Color field in parts
- ✅ Named colors (web + materials)
- ✅ Store in metadata
- ✅ Tests

### Phase 2: Palettes (Week 1-2)
- ✅ `colors:` section
- ✅ Color references
- ✅ Palette validation
- ✅ Tests

### Phase 3: Materials (Week 2)
- ✅ Material library (built-in)
- ✅ `materials:` section
- ✅ Material inheritance
- ✅ PBR properties
- ✅ Tests

### Phase 4: Export (Week 3)
- STEP export with colors
- OBJ export with MTL
- 3MF export
- Multi-format support

### Phase 5: Advanced (Week 4)
- Color modes
- Export options
- Validation and errors
- Documentation

---

## Success Criteria

✅ **Simple works:**
```yaml
color: red  # Just works
```

✅ **Palette works:**
```yaml
colors:
  primary: "#0066CC"
parts:
  x: {color: primary}
```

✅ **Materials work:**
```yaml
parts:
  x: {material: aluminum}
```

✅ **Custom materials work:**
```yaml
materials:
  custom:
    base: aluminum
    color: blue
```

✅ **Export works:**
- STEP with colors ✅
- OBJ with materials ✅
- 3MF for printing ✅

✅ **Errors are helpful:**
- Typo suggestions
- Format hints
- Clear messages

---

**Status:** Complete specification ready
**Next:** Implement!
**Estimated:** 2-3 weeks for full system
**Result:** Production-ready color system

Let's build this! 🚀
