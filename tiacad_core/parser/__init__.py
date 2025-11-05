"""
TiaCAD Parser - YAML to 3D Model Pipeline

This package provides parsing and building capabilities for TiaCAD YAML files.

Main Components:
- ParameterResolver: Resolves ${...} expressions in parameters ✅ COMPLETE
- PartsBuilder: Builds Part objects from primitive specifications ✅ COMPLETE
- OperationsBuilder: Builds operation pipeline from YAML operations ✅ COMPLETE
- TiaCADParser: Main entry point for parsing YAML files ✅ COMPLETE
- TiaCADDocument: Executable document representing complete model ✅ COMPLETE

Version: 0.1.0-alpha
Status: Phase 1 Implementation - COMPLETE! 🎉

Test Coverage: 86/86 tests passing (100%)
"""

__version__ = "0.1.0-alpha"

# All components implemented!
from .parameter_resolver import ParameterResolver, ParameterResolutionError
from .parts_builder import PartsBuilder, PartsBuilderError
from .operations_builder import OperationsBuilder, OperationsBuilderError
from .tiacad_parser import (
    TiaCADParser,
    TiaCADDocument,
    TiaCADParserError,
    parse  # Convenience function
)

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
]
