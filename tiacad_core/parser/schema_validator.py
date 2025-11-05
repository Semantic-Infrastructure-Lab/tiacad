"""
TiaCAD JSON Schema Validator

Provides optional schema validation for TiaCAD YAML files using JSON Schema.
Enables IDE autocomplete and early error detection.

Usage:
    from tiacad_core.parser.schema_validator import SchemaValidator

    validator = SchemaValidator()
    errors = validator.validate_file("design.yaml")
    if errors:
        for error in errors:
            print(f"Validation error: {error}")
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import jsonschema
    from jsonschema import ValidationError, SchemaError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = None
    SchemaError = None

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class SchemaValidator:
    """
    Validates TiaCAD YAML documents against JSON Schema.

    Provides:
    - Schema validation with clear error messages
    - IDE autocomplete support (via .vscode/settings.json)
    - Early error detection before parsing
    """

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize schema validator.

        Args:
            schema_path: Path to JSON schema file (defaults to tiacad-schema.json)
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning(
                "jsonschema package not available. "
                "Install with: pip install jsonschema"
            )
            self.schema = None
            return

        # Default to schema in project root
        if schema_path is None:
            schema_path = Path(__file__).parent.parent.parent / "tiacad-schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load JSON schema from file"""
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return None

        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            logger.debug(f"Loaded schema from {self.schema_path}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return None

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate YAML data against schema.

        Args:
            data: Parsed YAML data (dict)

        Returns:
            List of validation error messages (empty if valid)
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.debug("Skipping validation (jsonschema not available)")
            return []

        if self.schema is None:
            logger.debug("Skipping validation (schema not loaded)")
            return []

        errors = []
        try:
            jsonschema.validate(instance=data, schema=self.schema)
            logger.info("Schema validation passed")
        except ValidationError as e:
            error_msg = self._format_validation_error(e)
            errors.append(error_msg)
            logger.warning(f"Schema validation failed: {error_msg}")
        except SchemaError as e:
            error_msg = f"Invalid schema: {e.message}"
            errors.append(error_msg)
            logger.error(error_msg)

        return errors

    def validate_file(self, file_path: str) -> List[str]:
        """
        Validate YAML file against schema.

        Args:
            file_path: Path to YAML file

        Returns:
            List of validation error messages (empty if valid)
        """
        import yaml

        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            return self.validate(data)
        except Exception as e:
            return [f"Failed to load YAML file: {e}"]

    def _format_validation_error(self, error: 'ValidationError') -> str:
        """
        Format validation error with helpful context.

        Args:
            error: jsonschema ValidationError

        Returns:
            Formatted error message
        """
        # Get path to error location
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"

        # Format message
        if error.validator == 'required':
            missing = error.message.split("'")[1]
            return f"Missing required field '{missing}' at {path}"
        elif error.validator == 'enum':
            valid_values = error.validator_value
            return f"Invalid value at {path}. Must be one of: {', '.join(map(str, valid_values))}"
        elif error.validator == 'type':
            expected = error.validator_value
            actual = type(error.instance).__name__
            return f"Type error at {path}: expected {expected}, got {actual}"
        elif error.validator == 'minProperties':
            return f"At least {error.validator_value} properties required at {path}"
        else:
            return f"Validation error at {path}: {error.message}"

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded schema.

        Returns:
            Dict with schema metadata
        """
        if self.schema is None:
            return {
                "loaded": False,
                "available": JSONSCHEMA_AVAILABLE,
                "path": str(self.schema_path) if hasattr(self, 'schema_path') else None
            }

        return {
            "loaded": True,
            "available": JSONSCHEMA_AVAILABLE,
            "path": str(self.schema_path),
            "title": self.schema.get("title", "Unknown"),
            "version": self.schema.get("$id", "Unknown"),
            "required_fields": self.schema.get("required", [])
        }


def validate_yaml_file(file_path: str, strict: bool = False) -> bool:
    """
    Convenience function to validate a YAML file.

    Args:
        file_path: Path to YAML file
        strict: If True, raise exception on validation errors

    Returns:
        True if valid, False otherwise

    Raises:
        SchemaValidationError: If strict=True and validation fails
    """
    validator = SchemaValidator()
    errors = validator.validate_file(file_path)

    if errors:
        if strict:
            raise SchemaValidationError(
                f"Schema validation failed for {file_path}",
                errors=errors
            )
        return False

    return True


# Export public API
__all__ = [
    'SchemaValidator',
    'SchemaValidationError',
    'validate_yaml_file',
    'JSONSCHEMA_AVAILABLE'
]
