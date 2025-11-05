# TiaCAD Color System - YAML Interface Design

**Status:** Design Phase
**Version:** Draft 1.0
**Date:** 2025-10-25
**Purpose:** Explore YAML interface options for color support

---

## Design Philosophy

Before diving into syntax, let's establish principles:

1. **Progressive Disclosure**: Simple for beginners, powerful for experts
2. **Consistency**: Match existing TiaCAD patterns
3. **Clear Defaults**: Sensible behavior when color not specified
4. **Multiple Use Cases**: Support different workflows
5. **Future-Proof**: Extensible to materials, finishes, etc.

---

## Use Case Analysis

### Use Case 1: Quick Visual Differentiation

**User Need:** "I just want red, blue, green to tell parts apart"

**Simplest Possible:**
```yaml
parts:
  base: {primitive: box, size: [100,100,10], color: red}
  arm: {primitive: box, size: [20,70,16], color: blue}
  cover: {primitive: box, size: [100,100,2], color: green}
```

**Requirements:**
- Named colors (red, blue, green, etc.)
- Minimal syntax
- No color theory knowledge needed

---

### Use Case 2: Realistic Materials

**User Need:** "I want aluminum, steel, brass colors for realistic rendering"

**Material-Based:**
```yaml
parts:
  bracket:
    primitive: box
    size: [80, 80, 6]
    material: aluminum    # Implies color

  bolt:
    primitive: cylinder
    radius: 3
    height: 20
    material: steel       # Implies color
```

**Requirements:**
- Material presets
- Realistic colors
- Simple material names

---

### Use Case 3: Brand/Design System

**User Need:** "I need specific RGB values for my company's brand colors"

**Precise Colors:**
```yaml
parts:
  branded_cover:
    primitive: box
    size: [100, 100, 10]
    color: [0.8, 0.2, 0.2]      # RGB values
    # OR
    color: "#CC3333"             # Hex color
    # OR
    color: {r: 204, g: 51, b: 51}  # 0-255 RGB
```

**Requirements:**
- Precise control
- Multiple format support
- Matches web/design tools

---

### Use Case 4: Color Schemes

**User Need:** "I have a palette and want to use consistent colors across parts"

**Named Palette:**
```yaml
colors:
  primary: "#0066CC"
  secondary: "#CC6600"
  accent: "#CC0066"
  neutral: "#808080"

parts:
  main_body: {color: primary}
  detail_1: {color: accent}
  detail_2: {color: accent}
  frame: {color: neutral}
```

**Requirements:**
- Define once, use many times
- Easy to change entire color scheme
- Professional workflow

---

### Use Case 5: Multi-Color 3D Printing

**User Need:** "I need specific filament colors for multi-material printing"

**Print Materials:**
```yaml
parts:
  structure:
    primitive: box
    color: black           # Visual
    filament: PLA-Black    # Actual print material

  flexible_seal:
    color: red
    filament: TPU-Red

  support:
    color: gray
    filament: PVA-Soluble
```

**Requirements:**
- Visual color separate from material
- Printing-specific metadata
- Slicer compatibility

---

## Design Options

### Option A: Simple Color Field

**Most Minimal:**

```yaml
parts:
  my_part:
    primitive: box
    size: [10, 10, 10]
    color: red              # String
    # OR
    color: [1.0, 0.0, 0.0] # RGB array
    # OR
    color: "#FF0000"        # Hex string
```

**Pros:**
- ✅ Dead simple
- ✅ Matches user expectation
- ✅ Easy to parse
- ✅ Consistent with existing fields

**Cons:**
- ❌ Doesn't support transparency
- ❌ Doesn't scale to materials
- ❌ No palette support built-in

**When to Use:** Simple visualization, quick prototypes

---

### Option B: Visual Properties Object

**Structured Appearance:**

```yaml
parts:
  my_part:
    primitive: box
    size: [10, 10, 10]
    appearance:
      color: red
      opacity: 0.5         # 0-1, 0=transparent, 1=opaque
      finish: matte        # matte, glossy, metallic
```

**Pros:**
- ✅ Groups visual properties
- ✅ Extensible (finish, texture, etc.)
- ✅ Clear intent
- ✅ Room for future features

**Cons:**
- ❌ More verbose for simple cases
- ❌ Extra nesting

**When to Use:** Realistic rendering, presentation models

---

### Option C: Material-Based

**Material Presets:**

```yaml
parts:
  my_part:
    primitive: box
    size: [10, 10, 10]
    material: aluminum     # Preset name
    # OR
    material:
      name: aluminum
      finish: brushed      # Override preset
    # OR
    material:
      color: [0.75, 0.75, 0.75]
      metalness: 0.9
      roughness: 0.3
```

**Pros:**
- ✅ Realistic defaults
- ✅ Matches engineering thinking
- ✅ Could include physical properties later
- ✅ Professional workflow

**Cons:**
- ❌ Requires material library
- ❌ Color becomes indirect
- ❌ Overkill for simple coloring

**When to Use:** Engineering, CAM integration, physical simulation

---

### Option D: Dual System (Color + Material)

**Best of Both Worlds:**

```yaml
parts:
  simple_part:
    primitive: box
    color: red                    # Simple case

  realistic_part:
    primitive: box
    material: aluminum            # Material preset

  custom_part:
    primitive: box
    appearance:
      color: "#CC3333"
      finish: glossy

  precise_part:
    primitive: box
    material:
      base: aluminum              # Start with preset
      color: "#AABBCC"           # Override color
      finish: anodized           # Override finish
```

**Pros:**
- ✅ Simple when you want simple
- ✅ Powerful when you need it
- ✅ Progressive disclosure
- ✅ Multiple workflows supported

**Cons:**
- ❌ Two ways to do the same thing
- ❌ Potential confusion
- ❌ More complex to document

**When to Use:** General purpose - supports all use cases

---

### Option E: Palette-First Design

**Define Colors, Then Use:**

```yaml
# Top-level palette definition
colors:
  brand-blue: "#0066CC"
  brand-orange: "#CC6600"
  steel-gray: [0.5, 0.5, 0.5]
  aluminum:
    rgb: [0.75, 0.75, 0.75]
    metalness: 0.9

parts:
  cover:
    primitive: box
    color: brand-blue         # Reference palette

  frame:
    primitive: box
    color: aluminum           # Reference palette

  detail:
    primitive: box
    color: "#FF00FF"          # Or inline color
```

**Pros:**
- ✅ Design system friendly
- ✅ Consistency across parts
- ✅ Easy to change entire scheme
- ✅ Professional workflow

**Cons:**
- ❌ Extra section to learn
- ❌ Indirection for simple cases

**When to Use:** Design systems, brand compliance, teams

---

## Color Format Options

Regardless of structure, what formats for color values?

### Format 1: Named Colors

```yaml
color: red
color: blue
color: aluminum
color: steel
```

**Standard Web Colors:**
- red, green, blue, yellow, orange, purple
- white, black, gray, silver
- cyan, magenta, lime, navy, teal
- + 100+ more web colors

**Material Colors:**
- aluminum, steel, brass, copper, gold
- wood-oak, wood-walnut, wood-pine
- plastic-abs, plastic-pla

**Pros:** Readable, no numbers needed
**Cons:** Limited palette, ambiguous shades

---

### Format 2: Hex Strings (Web Standard)

```yaml
color: "#FF0000"      # Red
color: "#0066CC"      # Blue
color: "#CCCCCC"      # Gray
```

**Pros:**
- Web designer familiarity
- Compact (6 characters)
- Copy from design tools
- Widely understood

**Cons:**
- Not intuitive for non-designers
- No transparency support (in 6-char form)
- Need # prefix

**Extension for Alpha:**
```yaml
color: "#FF0000FF"    # Red, fully opaque
color: "#0066CC80"    # Blue, 50% transparent
```

---

### Format 3: RGB Array (0-1 range)

```yaml
color: [1.0, 0.0, 0.0]      # Red
color: [0.0, 0.4, 0.8]      # Blue
color: [0.8, 0.8, 0.8]      # Gray
```

**Pros:**
- Standard in 3D/CAD world
- Natural for computation
- Clean YAML array syntax

**Cons:**
- 0-1 range not intuitive for beginners
- Verbose for typing

**Extension for Alpha:**
```yaml
color: [1.0, 0.0, 0.0, 0.5]  # Red, 50% transparent (RGBA)
```

---

### Format 4: RGB Object (0-255 range)

```yaml
color:
  r: 255
  g: 0
  b: 0
  # Optional
  a: 128    # Alpha: 0-255
```

**Pros:**
- Matches Photoshop, design tools
- Most familiar to designers
- Self-documenting (r, g, b labels)

**Cons:**
- Verbose
- Lots of nesting

---

### Format 5: HSL (Hue, Saturation, Lightness)

```yaml
color:
  h: 0      # 0-360 degrees
  s: 100    # 0-100 percent
  l: 50     # 0-100 percent
```

**Pros:**
- Intuitive for color relationships
- Easy to create variations
- Designer-friendly

**Cons:**
- Less common in CAD
- More complex to implement

---

## Recommended Hybrid Approach

**Support Multiple Formats, Parse Intelligently:**

```yaml
# All of these should work:

parts:
  part1:
    color: red                      # Named color

  part2:
    color: "#FF0000"                # Hex string

  part3:
    color: [1.0, 0.0, 0.0]         # RGB array (0-1)

  part4:
    color: {r: 255, g: 0, b: 0}    # RGB object (0-255)

  part5:
    color: aluminum                 # Material preset

  part6:
    appearance:
      color: red
      opacity: 0.5
      finish: matte
```

**Parser Logic:**
```python
def parse_color(color_value):
    if isinstance(color_value, str):
        if color_value.startswith('#'):
            return parse_hex(color_value)
        else:
            return parse_named_color(color_value)

    elif isinstance(color_value, list):
        return parse_rgb_array(color_value)

    elif isinstance(color_value, dict):
        if 'r' in color_value:
            return parse_rgb_dict(color_value)
        elif 'h' in color_value:
            return parse_hsl_dict(color_value)
        else:
            return parse_appearance_dict(color_value)
```

---

## Palette System Design

### Top-Level Palettes

```yaml
colors:
  # Simple name: color
  primary: "#0066CC"
  secondary: "#CC6600"

  # Or detailed definition
  aluminum:
    rgb: [0.75, 0.75, 0.75]
    metalness: 0.9
    roughness: 0.3

  brand-red:
    hex: "#CC3333"
    name: "Acme Red"

# Use in parts
parts:
  cover:
    color: primary

  frame:
    color: aluminum
```

### Material Presets

```yaml
# Built-in materials (no need to define)
parts:
  bracket:
    material: aluminum      # Uses built-in aluminum preset

  bolt:
    material: steel         # Uses built-in steel preset

# Custom materials
materials:
  custom-aluminum:
    base: aluminum          # Extend built-in
    finish: anodized
    color: "#6699CC"        # Override color

parts:
  special-part:
    material: custom-aluminum
```

---

## Edge Cases & Considerations

### 1. Color on Operations

**Question:** Can operations have color?

```yaml
operations:
  # Option A: Operations don't have color (use part color)
  combined:
    type: boolean
    operation: union
    inputs: [part1, part2]
    # Result inherits part1's color? Or loses color?

  # Option B: Operations can override color
  combined:
    type: boolean
    operation: union
    inputs: [part1, part2]
    color: blue             # Override result color
```

**Recommendation:** Operations inherit color from base part, but can override

---

### 2. Pattern Colors

**Question:** Should pattern instances have different colors?

```yaml
operations:
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: 6
    # All same color? Or vary by index?

  # Option: Color variation
  bolt_circle:
    type: pattern
    pattern: circular
    input: bolt_hole
    count: 6
    colors: [red, orange, yellow, green, blue, purple]  # Rainbow!
    # OR
    color_scheme: rainbow
```

**Recommendation:** Start simple (all same color), add variation later

---

### 3. Transparency

**Question:** How to handle transparent parts?

```yaml
parts:
  window:
    primitive: box
    color: [0.8, 0.9, 1.0, 0.3]    # RGBA, 30% opaque
    # OR
    appearance:
      color: light-blue
      opacity: 0.3
```

**Use Cases:**
- Windows/enclosures
- Internal part visibility
- Ghost views for documentation

**Recommendation:** Support via RGBA or appearance.opacity

---

### 4. Color Inheritance

**Question:** Do child operations inherit parent colors?

```yaml
parts:
  base: {color: red}

operations:
  moved_base:
    type: transform
    input: base
    # Does moved_base inherit red color?
```

**Recommendation:** Yes, always inherit unless explicitly overridden

---

## Proposal: Recommended Design

**Three-Tier System:**

### Tier 1: Simple (Beginner)

```yaml
parts:
  my_part:
    primitive: box
    color: red              # Named color or hex
```

**Features:**
- Named colors (red, blue, aluminum, steel)
- Hex colors (#FF0000)
- Minimal syntax

---

### Tier 2: Palette (Intermediate)

```yaml
colors:
  primary: "#0066CC"
  secondary: "#CC6600"
  frame: aluminum

parts:
  cover: {color: primary}
  detail: {color: secondary}
  bracket: {color: frame}
```

**Features:**
- Reusable color definitions
- Material presets
- Design system support

---

### Tier 3: Advanced (Expert)

```yaml
materials:
  anodized-aluminum:
    base: aluminum
    color: "#6699CC"
    finish: anodized
    roughness: 0.2

parts:
  custom_part:
    primitive: box
    appearance:
      color: [0.8, 0.2, 0.2, 0.5]  # RGBA
      finish: glossy
      metalness: 0.8
```

**Features:**
- Full PBR properties
- Custom materials
- Precise control

---

## YAML Schema Addition

```yaml
# Extend current schema

# NEW: Optional top-level sections
colors:              # Optional: color palette
  <name>: <color>   # Simple
  # OR
  <name>:           # Detailed
    rgb: [r, g, b]
    hex: "#RRGGBB"
    metalness: 0-1
    roughness: 0-1

materials:           # Optional: material definitions
  <name>:
    base: <material> # Optional: extend preset
    color: <color>
    finish: matte|glossy|metallic
    # Future: density, strength, cost, etc.

# EXTEND: Parts
parts:
  <name>:
    primitive: box|cylinder|sphere|cone
    # ... existing fields ...

    # NEW: Color options (pick one)
    color: <color>           # Simple
    material: <material>     # Material preset
    appearance:              # Detailed
      color: <color>
      opacity: 0-1
      finish: matte|glossy|metallic
      metalness: 0-1
      roughness: 0-1

# Color Value Formats:
# <color> can be:
#   - "red"                   Named color
#   - "#FF0000"               Hex color
#   - [1.0, 0.0, 0.0]        RGB array (0-1)
#   - [1.0, 0.0, 0.0, 0.5]   RGBA array (0-1)
#   - {r: 255, g: 0, b: 0}   RGB object (0-255)
#   - palette_name            Reference to colors: section
```

---

## Migration Path

### Phase 1: Basic Color (Week 1-2)
- Add `color` field to parts
- Support named colors + hex
- Store in metadata
- No export changes yet

### Phase 2: Multiple Formats (Week 3)
- Add RGB array support
- Add RGB object support
- Smart parser (auto-detect format)

### Phase 3: Palettes (Week 4)
- Add `colors:` top-level section
- Color references
- Named palette support

### Phase 4: Materials (Month 2)
- Add `materials:` section
- Material presets
- PBR properties

### Phase 5: Export (Month 3)
- STEP export with colors
- OBJ export with materials
- 3MF export for printing

---

## Questions to Answer

### 1. Default Color Behavior

**What happens if no color specified?**

Options:
- A) Random color per part (easy to differentiate)
- B) Gray for everything (neutral)
- C) Color by primitive type (all boxes blue, cylinders red)
- D) Color by operation type (booleans green, patterns yellow)

**Recommendation:** Gray (neutral), with option for random via export setting

---

### 2. Palette Conflicts

**What if palette name conflicts with built-in color?**

```yaml
colors:
  red: "#0000FF"    # Redefine "red" as blue!

parts:
  my_part:
    color: red      # Use palette or built-in?
```

**Options:**
- A) Palette always wins
- B) Require prefix: `palette:red`
- C) Warning + use built-in

**Recommendation:** Palette wins (allows overrides)

---

### 3. Performance

**Colors on every part = bigger files?**

Not really - color is tiny metadata.
But rendering lots of colors = slower viewport?

**Recommendation:** Optimize later, not a concern for Phase 1

---

## Next Steps

1. **Feedback:** Which approach do you prefer?
2. **Refinement:** Adjust based on feedback
3. **Prototype:** Implement basic version
4. **Test:** Real examples with colors
5. **Document:** Add to YAML_REFERENCE.md
6. **Implement:** Full color system

---

## Summary Table

| Approach | Simplicity | Power | Beginner-Friendly | Professional |
|----------|-----------|-------|-------------------|--------------|
| Option A: Simple Field | ⭐⭐⭐⭐⭐ | ⭐⭐ | ✅ Yes | ❌ Limited |
| Option B: Appearance | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Maybe | ✅ Good |
| Option C: Material | ⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ No | ✅ Great |
| Option D: Dual System | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Great |
| Option E: Palette-First | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Maybe | ✅ Great |

**Recommended:** Option D (Dual System) - Progressive disclosure, supports all users

---

**Status:** Design draft complete, awaiting feedback
**Next:** Discuss trade-offs, choose approach, prototype
