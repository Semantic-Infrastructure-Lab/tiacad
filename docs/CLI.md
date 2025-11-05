# TiaCAD Command-Line Interface

**Version:** 0.1.0 (QW4 Enhanced CLI)

The TiaCAD CLI provides a professional command-line interface for building, validating, and inspecting TiaCAD YAML files.

---

## Installation

### Option 1: Direct Script (No Installation)

```bash
cd tiacad
./tiacad --help
```

### Option 2: Python Module

```bash
python -m tiacad_core --help
```

### Option 3: Install Package (Future)

```bash
pip install tiacad
tiacad --help
```

---

## Commands

### `tiacad build` - Build YAML to STL/3MF/STEP

Build a TiaCAD YAML file and export to STL, 3MF, or STEP format.

**Usage:**
```bash
tiacad build INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - Input YAML file path

**Options:**
- `-o, --output FILE` - Output file path (default: same name with .stl extension)
- `-p, --part NAME` - Specific part to export (default: last operation result)
- `-s, --stats` - Show build statistics
- `--validate-schema` - Enable JSON schema validation
- `-v, --verbose` - Verbose output with full traceback

**Output Formats:**
- `.stl` - STL mesh format (universal, good for 3D printing)
- `.3mf` - 3MF multi-material format (best for multi-color printing)
- `.step` - STEP BREP format (best for CAM/manufacturing)

**Examples:**

```bash
# Build to STL (default)
tiacad build examples/plate.yaml

# Build to specific output file
tiacad build examples/plate.yaml --output mounting_plate.stl

# Build to 3MF for multi-material printing
tiacad build examples/multi_material_demo.yaml --output demo.3mf

# Build specific part from file
tiacad build examples/assembly.yaml --part base_plate

# Build with statistics
tiacad build examples/bracket.yaml --stats

# Build with schema validation
tiacad build examples/new_design.yaml --validate-schema
```

**Output Example:**
```
ℹ Building examples/simple_box.yaml
✓ Parsed in 0.00s
ℹ Exporting to simple_box.stl
✓ Exported in 0.00s
✓ Total time: 0.01s
✓ Output: simple_box.stl

📊 Statistics:
  Parts: 1
  Parameters: 3
  Operations: 0
```

---

### `tiacad validate` - Validate YAML Files

Validate one or more TiaCAD YAML files without building geometry. Fast way to check syntax and structure.

**Usage:**
```bash
tiacad validate FILES...
```

**Arguments:**
- `FILES...` - One or more YAML files (supports glob patterns)

**Examples:**

```bash
# Validate single file
tiacad validate examples/plate.yaml

# Validate multiple files
tiacad validate examples/plate.yaml examples/bracket.yaml

# Validate all examples (glob pattern)
tiacad validate examples/*.yaml

# Validate specific pattern
tiacad validate examples/bolt_*.yaml
```

**Output Example:**
```
Validating 3 file(s)...
✓ examples/simple_box.yaml
✓ examples/mounting_plate.yaml
✗ examples/broken_design.yaml
  └─ Part 'bolt_hol' not found. Did you mean 'bolt_hole'?

Summary:
  ✓ Valid: 2
  ✗ Invalid: 1
```

**Exit Codes:**
- `0` - All files valid
- `1` - One or more files invalid

---

### `tiacad info` - Show File Information

Display information about a TiaCAD YAML file without building it. Shows metadata, parameters, parts, and operations.

**Usage:**
```bash
tiacad info INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - Input YAML file path

**Options:**
- `-v, --verbose` - Verbose output with full details

**Examples:**

```bash
# Show file info
tiacad info examples/mounting_plate.yaml

# Show detailed info
tiacad info examples/assembly.yaml --verbose
```

**Output Example:**
```
📄 rounded_mounting_plate.yaml

Metadata:
  name: Rounded Mounting Plate with Filleted Edges
  description: Demonstrates fillet finishing operation
  version: 1.0
  author: TIA

Parameters (8):
  plate_width: 150
  plate_height: 150
  plate_thickness: 8
  bolt_count: 6
  ...

Parts (10):
  • plate (box)
  • bolt_hole (cylinder)
  • center_hole (cylinder)
  ...

Operations (3):
  • bolt_circle (pattern)
  • plate_with_holes (boolean)
  • finished_plate (finishing)

Statistics:
  Total parts: 10
  Parameters: 8
  Operations: 3
```

---

## Global Options

Available for all commands:

- `--version` - Show TiaCAD version and exit
- `--no-color` - Disable colored output (useful for CI/scripts)
- `-h, --help` - Show help message

**Examples:**

```bash
# Show version
tiacad --version

# Disable colors for CI
tiacad build examples/plate.yaml --no-color

# Show help
tiacad --help
tiacad build --help
```

---

## Features

### 🎨 Color Output

The CLI uses color to make output easier to read:
- ✅ **Green** - Success messages
- ❌ **Red** - Error messages
- ⚠️  **Yellow** - Warning messages
- ℹ️  **Blue** - Info messages
- **Bold** - Headers and important text

Colors automatically disable when:
- Output is redirected to a file
- Terminal doesn't support colors
- `--no-color` flag is used

### 📊 Statistics

Use `--stats` with the `build` command to see:
- Total parts in design
- Number of parameters
- Number of operations
- Parse and export times

### ⚡ Performance

The CLI is designed for speed:
- Parse-only validation is fast (~0.01s for simple files)
- Info command doesn't build geometry
- Progress indicators for slow operations

### 🔍 Enhanced Error Messages

Thanks to QW6, errors show exact line and column numbers:

```
Error at line 23, column 16
At: parts → box1 → primitive
Unknown primitive type 'unknown_primitive' for part 'box1'
```

---

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
# Validate all designs in CI

set -e  # Exit on error

echo "Validating TiaCAD designs..."
tiacad validate designs/*.yaml --no-color

echo "Building production parts..."
tiacad build designs/production_part.yaml --output dist/part.stl --no-color

echo "✓ Build successful"
```

### Makefile Integration

```makefile
# Makefile for TiaCAD project

DESIGNS = $(wildcard designs/*.yaml)
OUTPUTS = $(DESIGNS:designs/%.yaml=output/%.stl)

all: $(OUTPUTS)

output/%.stl: designs/%.yaml
	tiacad build $< --output $@

validate:
	tiacad validate designs/*.yaml

clean:
	rm -f output/*.stl

.PHONY: all validate clean
```

### Build Script

```bash
#!/bin/bash
# Build all variants of a parametric design

DESIGNS=(
  "bracket_small.yaml"
  "bracket_medium.yaml"
  "bracket_large.yaml"
)

for design in "${DESIGNS[@]}"; do
  echo "Building $design..."
  tiacad build "designs/$design" --output "output/${design%.yaml}.stl" --stats
done

echo "All builds complete!"
```

---

## Troubleshooting

### Command Not Found

**Problem:** `bash: tiacad: command not found`

**Solutions:**
1. Use full path: `./tiacad` or `python -m tiacad_core`
2. Add to PATH: `export PATH="$PATH:/path/to/tiacad"`
3. Install package (future): `pip install tiacad`

### Colors Not Working

**Problem:** Colors show as escape codes like `\033[92m`

**Solutions:**
1. Use `--no-color` flag
2. Check terminal supports ANSI colors
3. Update terminal emulator

### Build Fails on Export

**Problem:** `Part 'finished_plate' not found`

**Solutions:**
1. Specify part explicitly: `--part plate_with_holes`
2. Check operations create parts in registry
3. Use `tiacad info` to see available parts

### Validation Shows Warnings

**Problem:** Warnings about unknown materials or patterns

**Solutions:**
1. Check spelling of material names
2. Ensure all referenced parts exist
3. Use `--verbose` for detailed error info

---

## Exit Codes

The CLI uses standard exit codes:

- `0` - Success
- `1` - Error (validation failed, build failed, etc.)
- `130` - Interrupted by user (Ctrl+C)

This makes the CLI easy to use in scripts:

```bash
if tiacad validate design.yaml; then
  echo "Valid!"
  tiacad build design.yaml
else
  echo "Invalid design"
  exit 1
fi
```

---

## Future Enhancements

Planned features for future CLI versions:

### QW8: Interactive Wizard
```bash
tiacad wizard
# Interactive prompts to generate YAML
```

### Render Command
```bash
tiacad render examples/bracket.yaml --view isometric --output preview.png
```

### Watch Mode
```bash
tiacad watch examples/design.yaml --auto-build
# Rebuild on file changes
```

### Batch Export
```bash
tiacad export examples/*.yaml --format stl --output-dir dist/
```

---

## Tips & Best Practices

### 1. Validate Before Building

Always validate first to catch errors quickly:
```bash
tiacad validate design.yaml && tiacad build design.yaml
```

### 2. Use Stats for Performance

Use `--stats` to identify slow operations:
```bash
tiacad build complex_assembly.yaml --stats
```

### 3. Script Your Workflow

Create build scripts for repeatable builds:
```bash
#!/bin/bash
tiacad validate *.yaml || exit 1
tiacad build production.yaml --output final.stl
```

### 4. Disable Colors in Scripts

Always use `--no-color` in CI/scripts:
```bash
tiacad build design.yaml --no-color > build.log
```

### 5. Check Info Before Building

Use `info` to understand complex files:
```bash
tiacad info complex_design.yaml
```

---

## Comparison with Old Method

### Before (Direct Python)

```bash
python -m tiacad_core.parser.tiacad_parser examples/plate.yaml
# No options, no feedback, no validation
```

### After (Enhanced CLI)

```bash
tiacad build examples/plate.yaml --output plate.stl --stats
# Professional interface, options, progress, statistics
```

**Benefits:**
- ✅ Cleaner interface
- ✅ Better error messages
- ✅ Progress indicators
- ✅ Multiple commands (build/validate/info)
- ✅ File validation
- ✅ Statistics and feedback

---

## Contributing

Want to improve the CLI?

**Feature Requests:**
- Open an issue describing the feature
- Tag with `enhancement` and `cli`

**Bug Reports:**
- Include command used
- Include error output
- Include TiaCAD version (`tiacad --version`)

---

**CLI Version:** 0.1.0 (QW4 Enhanced CLI)
**Last Updated:** 2025-10-26
**Author:** TIA
