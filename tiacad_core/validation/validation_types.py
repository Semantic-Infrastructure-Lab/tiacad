"""
Common Types for TiaCAD Validation System

Shared data structures used across all validation components.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import json


class Severity(Enum):
    """Validation issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Represents a single validation issue found in a TiaCAD document"""
    severity: Severity
    category: str  # "connectivity", "geometry", "appearance", "parameters", "positioning"
    message: str
    part_name: Optional[str] = None
    suggestion: Optional[str] = None
    location: Optional[Dict] = None  # For future YAML line number tracking

    def __str__(self) -> str:
        parts = [f"[{self.severity.value}]", f"({self.category})"]

        # Add location if available (YAML line:column)
        if self.location and 'line' in self.location:
            line = self.location['line']
            col = self.location.get('column', 0)
            file_path = self.location.get('file_path', '')
            if file_path:
                parts.append(f"at {file_path}:{line}:{col}")
            else:
                parts.append(f"at line {line}:{col}")

        if self.part_name:
            parts.append(f"Part '{self.part_name}':")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"→ {self.suggestion}")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            'severity': self.severity.value,
            'category': self.category,
            'message': self.message,
            'part_name': self.part_name,
            'suggestion': self.suggestion,
            'location': self.location
        }


@dataclass
class ValidationReport:
    """Summary report of validation results"""
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    @property
    def passed(self) -> bool:
        """Returns True if no errors found"""
        return self.error_count == 0

    def add_issue(self, issue: ValidationIssue):
        """Add an issue to the report"""
        self.issues.append(issue)

    def print_summary(self, show_info: bool = False):
        """Print a human-readable summary of validation results"""
        if not self.issues:
            print("✅ Validation passed - no issues found")
            return

        print(f"\n{'='*70}")
        print(f"Validation Report: {self.error_count} errors, {self.warning_count} warnings, {self.info_count} info")
        print(f"{'='*70}\n")

        # Print errors first
        errors = [i for i in self.issues if i.severity == Severity.ERROR]
        if errors:
            print("🚨 ERRORS:")
            for issue in errors:
                print(f"  {issue}")
            print()

        # Then warnings
        warnings = [i for i in self.issues if i.severity == Severity.WARNING]
        if warnings:
            print("⚠️  WARNINGS:")
            for issue in warnings:
                print(f"  {issue}")
            print()

        # Info messages (optional)
        if show_info:
            infos = [i for i in self.issues if i.severity == Severity.INFO]
            if infos:
                print("💡 INFO:")
                for issue in infos:
                    print(f"  {issue}")
                print()

    def to_json(self) -> str:
        """Export report as JSON"""
        return json.dumps({
            'passed': self.passed,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'issues': [i.to_dict() for i in self.issues]
        }, indent=2)
