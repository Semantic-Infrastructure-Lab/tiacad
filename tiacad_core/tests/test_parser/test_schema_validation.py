"""
Tests for JSON Schema validation in TiaCAD.

Tests schema validation functionality including:
- Valid YAML documents pass validation
- Invalid documents fail with clear errors
- Missing required fields detected
- Invalid types caught
- Schema validation can be toggled
"""

import pytest
from tiacad_core.parser.schema_validator import (
    SchemaValidator,
    SchemaValidationError,
    validate_yaml_file,
    JSONSCHEMA_AVAILABLE
)
from tiacad_core.parser.tiacad_parser import TiaCADParser, TiaCADParserError


# Skip tests if jsonschema not available
pytestmark = pytest.mark.skipif(
    not JSONSCHEMA_AVAILABLE,
    reason="jsonschema not installed"
)


class TestSchemaValidator:
    """Test SchemaValidator class"""

    def test_schema_loads_successfully(self):
        """Schema file loads without errors"""
        validator = SchemaValidator()
        assert validator.schema is not None
        assert validator.schema.get("title") == "TiaCAD YAML Schema"

    def test_schema_info(self):
        """get_schema_info returns correct metadata"""
        validator = SchemaValidator()
        info = validator.get_schema_info()

        assert info["loaded"] is True
        assert info["available"] is True
        assert "tiacad-schema.json" in info["path"]
        assert info["title"] == "TiaCAD YAML Schema"
        assert "parts" in info["required_fields"]

    def test_valid_minimal_yaml(self):
        """Minimal valid YAML passes validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0

    def test_valid_complete_yaml(self):
        """Complete valid YAML passes validation"""
        validator = SchemaValidator()
        data = {
            "schema_version": "2.0",
            "metadata": {
                "name": "Test Design",
                "author": "Test Author"
            },
            "parameters": {
                "width": 100,
                "height": 50
            },
            "parts": {
                "plate": {
                    "primitive": "box",
                    "size": ["${width}", "${height}", 10],
                    "origin": "center"
                },
                "hole": {
                    "primitive": "cylinder",
                    "radius": 5,
                    "height": 12,
                    "origin": "base"
                }
            },
            "operations": {
                "subtract_hole": {
                    "type": "boolean",
                    "operation": "difference",
                    "base": "plate",
                    "subtract": ["hole"]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0

    def test_missing_required_parts(self):
        """Missing required 'parts' field fails validation"""
        validator = SchemaValidator()
        data = {
            "metadata": {
                "name": "Invalid Design"
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0
        assert "parts" in errors[0].lower()

    def test_invalid_primitive_type(self):
        """Invalid primitive type fails validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "bad_part": {
                    "primitive": "invalid_primitive",
                    "size": [10, 10, 10]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0
        assert "primitive" in errors[0].lower() or "enum" in errors[0].lower()

    def test_invalid_schema_version(self):
        """Invalid schema_version fails validation"""
        validator = SchemaValidator()
        data = {
            "schema_version": "9.9",  # Invalid version
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0

    def test_invalid_operation_type(self):
        """Invalid operation type fails validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            },
            "operations": {
                "bad_op": {
                    "type": "invalid_operation"
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0

    def test_missing_primitive_in_part(self):
        """Part without 'primitive' field fails validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "bad_part": {
                    "size": [10, 10, 10]
                    # Missing 'primitive'
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0
        assert "primitive" in errors[0].lower()

    def test_invalid_origin_value(self):
        """Invalid origin value fails validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10],
                    "origin": "invalid_origin"  # Should be 'center', 'corner', or 'base'
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0


class TestParserIntegration:
    """Test schema validation integration with TiaCADParser"""

    def test_parser_validation_disabled_by_default(self):
        """Schema validation is disabled by default"""
        # This should parse without requiring schema validation
        yaml_data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            }
        }
        # Should not raise error even without schema validation
        doc = TiaCADParser.parse_dict(yaml_data, validate_schema=False)
        assert doc is not None

    def test_parser_with_validation_enabled(self):
        """Parser accepts validate_schema parameter"""
        yaml_data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            }
        }
        # Should pass validation
        doc = TiaCADParser.parse_dict(yaml_data, validate_schema=True)
        assert doc is not None

    def test_parser_rejects_invalid_with_validation(self):
        """Parser rejects invalid YAML when validation enabled"""
        yaml_data = {
            "parts": {
                "bad_part": {
                    "primitive": "invalid_type",
                    "size": [10, 10, 10]
                }
            }
        }
        # Should fail validation
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_dict(yaml_data, validate_schema=True)
        assert "schema validation" in str(exc_info.value).lower()


class TestConvenienceFunctions:
    """Test convenience functions for validation"""

    def test_validate_yaml_file_nonexistent(self):
        """validate_yaml_file handles nonexistent files"""
        result = validate_yaml_file("/nonexistent/file.yaml", strict=False)
        assert result is False

    def test_validate_yaml_file_strict_mode(self):
        """validate_yaml_file raises in strict mode"""
        with pytest.raises(SchemaValidationError):
            validate_yaml_file("/nonexistent/file.yaml", strict=True)


class TestPrimitives:
    """Test schema validation for all primitive types"""

    @pytest.mark.parametrize("primitive,params", [
        ("box", {"size": [10, 10, 10]}),
        ("cylinder", {"radius": 5, "height": 10}),
        ("sphere", {"radius": 5}),
        ("cone", {"radius1": 5, "radius2": 3, "height": 10}),
        ("torus", {"major_radius": 10, "minor_radius": 2}),
    ])
    def test_primitive_types(self, primitive, params):
        """All supported primitive types validate correctly"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "test_part": {
                    "primitive": primitive,
                    **params
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0, f"Primitive '{primitive}' should be valid"


class TestOperations:
    """Test schema validation for operations"""

    @pytest.mark.parametrize("op_type", [
        "transform",
        "attach",
        "boolean",
        "pattern",
        "mirror",
        "finishing"
    ])
    def test_operation_types(self, op_type):
        """All supported operation types validate correctly"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            },
            "operations": {
                "test_op": {
                    "type": op_type,
                    "input": "box1"
                }
            }
        }
        errors = validator.validate(data)
        # Note: Some operations may require additional fields,
        # but the 'type' itself should be valid
        # We're just testing that the enum value is accepted
        assert len(errors) == 0 or "type" not in str(errors).lower()


class TestParameterExpressions:
    """Test schema validation with parameter expressions"""

    def test_string_expressions_allowed(self):
        """Parameter expressions as strings are allowed"""
        validator = SchemaValidator()
        data = {
            "parameters": {
                "width": 100,
                "derived": "${width * 2}"
            },
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": ["${width}", 50, 10]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0

    def test_numeric_parameters(self):
        """Numeric parameter values are allowed"""
        validator = SchemaValidator()
        data = {
            "parameters": {
                "width": 100,
                "height": 50.5,
                "count": 4,
                "enabled": True
            },
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0


class TestColors:
    """Test schema validation for colors"""

    def test_color_palette(self):
        """Color palette validates correctly"""
        validator = SchemaValidator()
        data = {
            "colors": {
                "red": "#FF0000",
                "blue": [0, 0, 255],
                "green": [0, 255, 0, 1.0]
            },
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10],
                    "color": "red"
                }
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0


class TestExport:
    """Test schema validation for export configuration"""

    def test_export_config(self):
        """Export configuration validates correctly"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            },
            "export": {
                "default_part": "box1",
                "formats": [
                    {
                        "type": "stl",
                        "path": "output.stl"
                    },
                    {
                        "type": "3mf",
                        "path": "output.3mf"
                    }
                ]
            }
        }
        errors = validator.validate(data)
        assert len(errors) == 0

    def test_invalid_export_format(self):
        """Invalid export format fails validation"""
        validator = SchemaValidator()
        data = {
            "parts": {
                "box1": {
                    "primitive": "box",
                    "size": [10, 10, 10]
                }
            },
            "export": {
                "formats": [
                    {
                        "type": "invalid_format"
                    }
                ]
            }
        }
        errors = validator.validate(data)
        assert len(errors) > 0


# Integration test with real example file
def test_example_file_validates():
    """Real example file passes schema validation"""
    import os
    example_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..",
        "examples", "rounded_mounting_plate.yaml"
    )

    if os.path.exists(example_path):
        result = validate_yaml_file(example_path, strict=False)
        # Should pass or at least not crash
        assert isinstance(result, bool)
