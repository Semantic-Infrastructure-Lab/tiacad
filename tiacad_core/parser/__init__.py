"""Public parser package surface for TiaCAD YAML parsing and model building."""

from .. import __version__

from .parameter_resolver import ParameterResolver, ParameterResolutionError
from .parts_builder import PartsBuilder, PartsBuilderError
from .operations_builder import OperationsBuilder, OperationsBuilderError
from .errors import TiaCADParserError
from .tiacad_parser import (
    TiaCADParser,
    TiaCADDocument,
    parse  # Convenience function
)
from .component_importer import ComponentImporter, ComponentImportError

__all__ = [
    # Parameter resolution
    'ParameterResolver',
    'ParameterResolutionError',
    # Parts building
    'PartsBuilder',
    'PartsBuilderError',
    # Operations
    'OperationsBuilder',
    'OperationsBuilderError',
    # Main parser
    'TiaCADParser',
    'TiaCADDocument',
    'TiaCADParserError',
    'parse',
    # Component imports
    'ComponentImporter',
    'ComponentImportError',
]
