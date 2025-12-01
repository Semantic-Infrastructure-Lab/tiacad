# TiaCAD User Documentation

Documentation for TiaCAD users - learn to design parametric CAD models in YAML.

---

## 📖 Learning Path

### 1. Start Here: Tutorial
**[TUTORIAL.md](TUTORIAL.md)**

Step-by-step introduction to TiaCAD fundamentals:
- Installation and setup
- Your first model
- Core concepts (parts, sketches, operations)
- Building progressively complex designs

**Time:** ~30-60 minutes

### 2. Explore Examples
**[EXAMPLES_GUIDE.md](EXAMPLES_GUIDE.md)**

Comprehensive guide to all example files:
- Basic shapes and operations
- Advanced features (lofts, sweeps, patterns)
- Real-world projects (guitar hanger, enclosures)
- Organized by difficulty level

**Browse:** [`examples/` directory](../../examples/)

### 3. Reference: YAML Syntax
**[YAML_REFERENCE.md](YAML_REFERENCE.md)**

Complete syntax reference for TiaCAD YAML:
- All supported primitives
- Operations and transformations
- Parameters and expressions
- Assembly features
- Material and color definitions

**Use:** Keep open while designing

### 4. Understand Terminology
**[GLOSSARY.md](GLOSSARY.md)**

Canonical definitions of TiaCAD concepts:
- Parts, sketches, and operations
- Spatial references and anchors
- Frames and transformations
- Assembly and constraints

### 5. Master Auto-References
**[AUTO_REFERENCES_GUIDE.md](AUTO_REFERENCES_GUIDE.md)**

Deep dive into TiaCAD's automatic spatial referencing system:
- How auto-generated anchors work
- Reference types and selection
- Coordinate frames and transformations
- Best practices

---

## 🎯 Common Tasks

| I want to... | Documentation |
|--------------|---------------|
| Learn the basics | [TUTORIAL.md](TUTORIAL.md) |
| See working examples | [EXAMPLES_GUIDE.md](EXAMPLES_GUIDE.md) + [examples/](../../examples/) |
| Look up YAML syntax | [YAML_REFERENCE.md](YAML_REFERENCE.md) |
| Understand a term | [GLOSSARY.md](GLOSSARY.md) |
| Use advanced referencing | [AUTO_REFERENCES_GUIDE.md](AUTO_REFERENCES_GUIDE.md) |
| Export to STL/3MF | [YAML_REFERENCE.md](YAML_REFERENCE.md) (Export section) |
| Define parameters | [YAML_REFERENCE.md](YAML_REFERENCE.md) (Parameters section) |

---

## 💡 Tips for Learning

1. **Start simple:** Begin with `examples/simple_box.yaml`
2. **Iterate:** Modify examples to understand behavior
3. **Use the CLI:** Run `tiacad build <file.yaml>` to see results
4. **Read error messages:** TiaCAD provides helpful validation errors
5. **Reference the glossary:** When confused about terminology

---

## 🆘 Getting Help

- **Error messages:** TiaCAD provides detailed error messages with line numbers
- **Examples:** Check [`examples/`](../../examples/) for similar use cases
- **Issues:** Report bugs or ask questions on GitHub
- **Community:** (Add links to community channels if available)

---

## 📚 Next Steps

Once comfortable with user docs, explore:
- **[Developer Documentation](../developer/)** - For contributors
- **[Architecture Documentation](../architecture/)** - System design
