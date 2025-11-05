"""
ParameterResolver - Resolve ${...} expressions in TiaCAD YAML

Handles parameter substitution and expression evaluation for parametric design.
Supports:
- Simple references: ${width}
- Arithmetic: ${width * 2}, ${height / 2}
- Functions: ${max(a, b)}, ${sqrt(value)}
- Nested references: ${inner_width} where inner_width = ${width - 10}

Author: TIA
Version: 0.1.0-alpha
"""

import re
import logging
import math
from typing import Any, Dict, Union, List
from simpleeval import simple_eval, NameNotDefined, InvalidExpression

from ..utils.exceptions import TiaCADError

logger = logging.getLogger(__name__)


class ParameterResolutionError(TiaCADError):
    """Error during parameter resolution"""
    def __init__(self, message: str, parameter: str = None, expression: str = None):
        super().__init__(message)
        self.parameter = parameter
        self.expression = expression


class ParameterResolver:
    """
    Resolves ${...} expressions in parameter values.

    Usage:
        params = {
            'width': 100,
            'height': 50,
            'area': '${width * height}'
        }
        resolver = ParameterResolver(params)
        area = resolver.resolve(params['area'])  # → 5000
    """

    # Pattern to match ${...} expressions
    EXPR_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize parameter resolver.

        Args:
            parameters: Dictionary of parameter name → value
                       Values can contain ${...} expressions
        """
        self.raw_parameters = parameters.copy()
        self.resolved_cache: Dict[str, Any] = {}
        self.resolution_stack: List[str] = []  # For circular reference detection

        # Functions available in expressions
        self.functions = {
            'min': min,
            'max': max,
            'abs': abs,
            'sqrt': math.sqrt,
            'pow': pow,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'pi': math.pi,
        }

    def resolve(self, value: Any) -> Any:
        """
        Recursively resolve ${...} expressions in a value.

        Args:
            value: Value to resolve (can be str, list, dict, or scalar)

        Returns:
            Resolved value with all ${...} expressions evaluated

        Raises:
            ParameterResolutionError: If expression is invalid or references missing parameter
        """
        # Base cases - no resolution needed
        if value is None or isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value

        # String - check for ${...} expressions
        if isinstance(value, str):
            return self._resolve_string(value)

        # List - resolve each element
        if isinstance(value, list):
            return [self.resolve(item) for item in value]

        # Dict - resolve each value
        if isinstance(value, dict):
            return {key: self.resolve(val) for key, val in value.items()}

        # Unknown type - return as-is
        logger.warning(f"Unknown type for resolution: {type(value)}, returning as-is")
        return value

    def _resolve_string(self, value: str) -> Union[str, int, float, bool]:
        """
        Resolve ${...} expressions in a string.

        If the entire string is a single ${...} expression, returns the evaluated result.
        If the string contains multiple expressions or mixed text, returns a string with
        expressions substituted.

        Args:
            value: String potentially containing ${...} expressions

        Returns:
            Resolved value (may be string, number, or bool depending on expression)
        """
        # Find all ${...} expressions
        matches = list(self.EXPR_PATTERN.finditer(value))

        if not matches:
            # No expressions - return as-is
            return value

        # Check if entire string is a single expression
        if len(matches) == 1:
            match = matches[0]
            if match.start() == 0 and match.end() == len(value):
                # Entire string is ${...} - evaluate and return result
                expression = match.group(1).strip()
                return self._evaluate_expression(expression)

        # Multiple expressions or mixed text - substitute each and return string
        result = value
        # Process in reverse order to maintain correct indices
        for match in reversed(matches):
            expression = match.group(1).strip()
            evaluated = self._evaluate_expression(expression)
            # Convert to string for substitution
            result = result[:match.start()] + str(evaluated) + result[match.end():]

        return result

    def _evaluate_expression(self, expression: str) -> Union[int, float, bool, str]:
        """
        Evaluate a single expression (without ${...} wrapper).

        Args:
            expression: Expression to evaluate (e.g., "width * 2")

        Returns:
            Evaluated result

        Raises:
            ParameterResolutionError: If evaluation fails
        """
        try:
            # Build names dict with resolved parameters
            names = self._build_names_dict()

            # Evaluate using simpleeval (safe evaluation)
            result = simple_eval(
                expression,
                names=names,
                functions=self.functions
            )

            return result

        except NameNotDefined as e:
            raise ParameterResolutionError(
                f"Parameter '{e.name}' not found in expression: {expression}",
                expression=expression
            )
        except InvalidExpression as e:
            raise ParameterResolutionError(
                f"Invalid expression: {expression}\n{str(e)}",
                expression=expression
            )
        except ZeroDivisionError:
            raise ParameterResolutionError(
                f"Division by zero in expression: {expression}",
                expression=expression
            )
        except Exception as e:
            raise ParameterResolutionError(
                f"Error evaluating expression '{expression}': {str(e)}",
                expression=expression
            )

    def _build_names_dict(self) -> Dict[str, Any]:
        """
        Build dictionary of parameter names → resolved values for expression evaluation.

        Only includes parameters that can be resolved without circular reference.
        Parameters currently being resolved are excluded.

        Returns:
            Dict mapping parameter names to their resolved values
        """
        names = {}
        for param_name in self.raw_parameters:
            # Skip parameters currently being resolved (avoid circular reference)
            if param_name in self.resolution_stack:
                continue

            # Use cached value if available
            if param_name in self.resolved_cache:
                names[param_name] = self.resolved_cache[param_name]
                continue

            # Try to resolve, but if it fails, skip it
            # This allows expressions to reference parameters defined earlier
            try:
                names[param_name] = self.get_parameter(param_name)
            except ParameterResolutionError:
                # Parameter can't be resolved yet, skip it
                # This happens when there are forward references
                pass

        return names

    def get_parameter(self, name: str) -> Any:
        """
        Get resolved value of a parameter by name.

        Handles circular reference detection and caching.

        Args:
            name: Parameter name

        Returns:
            Resolved parameter value

        Raises:
            ParameterResolutionError: If parameter not found or circular reference detected
        """
        # Check cache
        if name in self.resolved_cache:
            return self.resolved_cache[name]

        # Check parameter exists
        if name not in self.raw_parameters:
            raise ParameterResolutionError(
                f"Parameter '{name}' not found. Available parameters: {list(self.raw_parameters.keys())}",
                parameter=name
            )

        # Check for circular reference
        if name in self.resolution_stack:
            cycle = ' -> '.join(self.resolution_stack + [name])
            raise ParameterResolutionError(
                f"Circular reference detected: {cycle}",
                parameter=name
            )

        # Resolve parameter
        try:
            self.resolution_stack.append(name)
            raw_value = self.raw_parameters[name]
            resolved_value = self.resolve(raw_value)

            # Cache result
            self.resolved_cache[name] = resolved_value

            logger.debug(f"Resolved parameter '{name}': {raw_value} → {resolved_value}")
            return resolved_value

        finally:
            self.resolution_stack.pop()

    def resolve_all(self) -> Dict[str, Any]:
        """
        Resolve all parameters and return as dictionary.

        Returns:
            Dict of parameter name → resolved value
        """
        result = {}
        for name in self.raw_parameters:
            result[name] = self.get_parameter(name)
        return result

    def __repr__(self) -> str:
        return f"ParameterResolver({len(self.raw_parameters)} parameters)"
