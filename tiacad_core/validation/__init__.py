"""
TiaCAD Validation Module

Provides assembly validation and design rule checking for TiaCAD documents.
"""

from .assembly_validator import AssemblyValidator, ValidationReport, ValidationIssue, Severity

__all__ = ['AssemblyValidator', 'ValidationReport', 'ValidationIssue', 'Severity']
