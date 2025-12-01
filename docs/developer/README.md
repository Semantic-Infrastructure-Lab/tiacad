# TiaCAD Developer Documentation

Documentation for TiaCAD contributors and advanced users.

---

## 🔧 Developer Resources

### Command-Line Interface
**[CLI.md](CLI.md)**

Complete CLI reference:
- All commands and options
- Build, render, validate operations
- Output formats and configuration
- Advanced usage patterns

### Testing
**[TESTING_GUIDE.md](TESTING_GUIDE.md)**

Comprehensive testing documentation:
- Test organization and structure
- Writing new tests
- Test utilities and fixtures
- Running test suites
- Coverage and CI/CD

**Quick Reference:** [TESTING_QUICK_REFERENCE.md](TESTING_QUICK_REFERENCE.md)

### Migration and Compatibility
**[MIGRATION_GUIDE_V3.md](MIGRATION_GUIDE_V3.md)**

Upgrading from TiaCAD v2 to v3:
- Breaking changes
- New features
- Updated syntax
- Migration scripts and tools

### Code Organization
**[SCHEMA_VALIDATION.md](SCHEMA_VALIDATION.md)**

YAML schema validation system:
- Schema definition
- Validation rules
- Error handling
- Custom validators

**[TERMINOLOGY_GUIDE.md](TERMINOLOGY_GUIDE.md)**

Canonical terminology for code and docs:
- Standardized terms
- Rationale for naming choices
- Consistency guidelines
- 30+ concept definitions

---

## 🚀 Getting Started as a Contributor

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone https://github.com/scottsen/tiacad.git
cd tiacad

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests to verify setup
pytest
```

### 2. Understand the Architecture

Read [Architecture Documentation](../architecture/) to understand:
- System design decisions
- Code organization principles
- Core abstractions (sketches, operations, spatial references)
- Future direction (CGA integration)

### 3. Write Tests

All contributions should include tests:
- Follow patterns in [TESTING_GUIDE.md](TESTING_GUIDE.md)
- Use existing test utilities
- Aim for >80% coverage

### 4. Follow Conventions

- **Terminology:** Use canonical terms from [TERMINOLOGY_GUIDE.md](TERMINOLOGY_GUIDE.md)
- **Code style:** Run `ruff check` before committing
- **Documentation:** Update docs with code changes
- **Examples:** Add examples for new features

---

## 📋 Development Workflows

### Adding a New Feature

1. **Design:** Review architecture docs, consider existing patterns
2. **Test:** Write tests first (TDD) or alongside implementation
3. **Implement:** Follow code organization principles
4. **Document:** Update YAML_REFERENCE.md, add examples
5. **Validate:** Run full test suite, check code quality
6. **Review:** Submit PR with tests, docs, and examples

### Debugging

- Use `tiacad build <file> --verbose` for detailed output
- Check validation errors (provide line numbers)
- Run specific test: `pytest tests/test_specific.py::test_function`
- Use visual regression tests for geometry validation

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_parser/

# With coverage
pytest --cov=tiacad_core --cov-report=html

# Quick smoke test
pytest tests/test_integration.py -k "simple"
```

---

## 🏗️ Code Structure

```
tiacad_core/
├── parser/          # YAML parsing and builders
├── geometry/        # Geometric primitives and backends
├── exporters/       # STL, 3MF, STEP export
├── validation/      # Schema and rule validation
├── testing/         # Test utilities
├── visualization/   # Rendering and visual output
└── utils/           # Common utilities
```

See [Architecture Documentation](../architecture/) for detailed design docs.

---

## 📚 Additional Resources

- **[Main README](../../README.md)** - Project overview
- **[Architecture Docs](../architecture/)** - System design
- **[User Docs](../user/)** - User-facing features
- **[Examples](../../examples/)** - Working code to reference

---

## 🤝 Contributing

We welcome contributions! Please:
1. Read this developer documentation
2. Follow existing patterns and conventions
3. Include tests and documentation
4. Submit clear, focused pull requests
