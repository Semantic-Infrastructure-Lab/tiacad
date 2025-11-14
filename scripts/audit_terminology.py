#!/usr/bin/env python3
"""
TiaCAD Terminology Audit Script

Scans documentation files for terminology inconsistencies based on
docs/TERMINOLOGY_GUIDE.md

Usage:
    python3 scripts/audit_terminology.py
    python3 scripts/audit_terminology.py --fix  # Auto-fix simple cases (coming soon)
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import sys

# Terminology rules: pattern to find → correct term to use
TERMINOLOGY_RULES = {
    # Spatial terms
    r'\b(local\s+)?coordinate\s+system\b(?!.*local frame)': {
        'wrong': 'coordinate system',
        'correct': 'local frame',
        'severity': 'HIGH',
        'context': 'Use "local frame" not "coordinate system"'
    },
    r'\bglobal\s+coordinates?\b': {
        'wrong': 'global coordinates',
        'correct': 'world space',
        'severity': 'HIGH',
        'context': 'Use "world space" not "global coordinates"'
    },
    r'\bworld\s+coordinates?\b': {
        'wrong': 'world coordinates',
        'correct': 'world space',
        'severity': 'MEDIUM',
        'context': 'Use "world space" not "world coordinates"'
    },
    r'\bdisplacement\b(?!.*offset)': {
        'wrong': 'displacement',
        'correct': 'offset',
        'severity': 'MEDIUM',
        'context': 'Use "offset" not "displacement" for positioning'
    },

    # Geometry terms (in CAD context)
    r'\bsurface\b(?=.*(?:face|anchor|geometry))': {
        'wrong': 'surface',
        'correct': 'face',
        'severity': 'LOW',
        'context': 'Use "face" not "surface" when referring to solid geometry'
    },

    # Anchor terminology
    r'\bauto-?references?\b': {
        'wrong': 'auto-reference(s)',
        'correct': 'auto-generated anchors',
        'severity': 'HIGH',
        'context': 'Use "auto-generated anchors" not "auto-references"'
    },
    r'\bbuilt-?in\s+anchors?\b': {
        'wrong': 'built-in anchor(s)',
        'correct': 'auto-generated anchors',
        'severity': 'MEDIUM',
        'context': 'Use "auto-generated anchors" not "built-in anchors"'
    },
    r'\bdefault\s+anchors?\b': {
        'wrong': 'default anchor(s)',
        'correct': 'auto-generated anchors',
        'severity': 'MEDIUM',
        'context': 'Use "auto-generated anchors" not "default anchors"'
    },

    # Positioning language
    r'\blocation\b(?=.*(?:position|coordinate|spatial))': {
        'wrong': 'location',
        'correct': 'position',
        'severity': 'LOW',
        'context': 'Use "position" not "location" in technical contexts'
    },
    r'\btranslate\s+(?:moves?|shifting)': {
        'wrong': 'translate moves/shifting',
        'correct': 'translate positions',
        'severity': 'MEDIUM',
        'context': 'Say "translate positions" not "translate moves"'
    },
}

# Files to scan (patterns)
DOC_PATTERNS = [
    '*.md',
    'docs/**/*.md',
    'examples/**/*.yaml',
]

# Files to skip
SKIP_FILES = [
    'docs/TERMINOLOGY_GUIDE.md',  # Skip the guide itself
    'CHANGELOG.md',  # Historical records shouldn't be changed
]

class TerminologyIssue:
    def __init__(self, file_path, line_num, line_text, rule_key, rule_info):
        self.file_path = file_path
        self.line_num = line_num
        self.line_text = line_text.strip()
        self.rule_key = rule_key
        self.wrong_term = rule_info['wrong']
        self.correct_term = rule_info['correct']
        self.severity = rule_info['severity']
        self.context = rule_info['context']

    def __repr__(self):
        return (f"{self.file_path}:{self.line_num} [{self.severity}] "
                f"'{self.wrong_term}' → '{self.correct_term}'")

def should_skip_file(file_path):
    """Check if file should be skipped"""
    file_str = str(file_path)
    for skip_pattern in SKIP_FILES:
        if skip_pattern in file_str:
            return True
    return False

def scan_file(file_path):
    """Scan a single file for terminology issues"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip code blocks (lines starting with 4+ spaces or tabs)
                if line.startswith('    ') or line.startswith('\t'):
                    continue

                # Check each terminology rule
                for pattern, rule_info in TERMINOLOGY_RULES.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(TerminologyIssue(
                            file_path, line_num, line, pattern, rule_info
                        ))
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return issues

def scan_documentation(project_root):
    """Scan all documentation files"""
    project_path = Path(project_root)
    all_issues = []

    # Find all markdown files
    for pattern in DOC_PATTERNS:
        for file_path in project_path.glob(pattern):
            if file_path.is_file() and not should_skip_file(file_path):
                issues = scan_file(file_path)
                all_issues.extend(issues)

    return all_issues

def group_issues(issues):
    """Group issues by severity and file"""
    by_severity = defaultdict(list)
    by_file = defaultdict(list)

    for issue in issues:
        by_severity[issue.severity].append(issue)
        by_file[str(issue.file_path)].append(issue)

    return by_severity, by_file

def print_report(issues):
    """Print audit report"""
    if not issues:
        print("✅ No terminology issues found! Documentation is consistent.")
        return

    by_severity, by_file = group_issues(issues)

    print(f"🔍 TiaCAD Terminology Audit Report")
    print(f"=" * 60)
    print(f"Total issues found: {len(issues)}")
    print()

    # Summary by severity
    print("📊 Issues by Severity:")
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        count = len(by_severity[severity])
        if count > 0:
            emoji = '🔴' if severity == 'HIGH' else '🟡' if severity == 'MEDIUM' else '🟢'
            print(f"  {emoji} {severity}: {count} issues")
    print()

    # Issues by file
    print("📁 Issues by File:")
    print()
    for file_path in sorted(by_file.keys()):
        file_issues = by_file[file_path]
        print(f"  {file_path} ({len(file_issues)} issues)")

        # Group by severity within file
        high = [i for i in file_issues if i.severity == 'HIGH']
        medium = [i for i in file_issues if i.severity == 'MEDIUM']
        low = [i for i in file_issues if i.severity == 'LOW']

        for issue in high + medium + low:
            emoji = '🔴' if issue.severity == 'HIGH' else '🟡' if issue.severity == 'MEDIUM' else '🟢'
            print(f"    {emoji} Line {issue.line_num}: '{issue.wrong_term}' → '{issue.correct_term}'")
            print(f"       {issue.context}")
            print(f"       | {issue.line_text[:80]}...")
            print()

    # Recommendations
    print("=" * 60)
    print("📝 Next Steps:")
    print()
    if len(by_severity['HIGH']) > 0:
        print(f"1. Fix {len(by_severity['HIGH'])} HIGH priority issues first")
    if len(by_severity['MEDIUM']) > 0:
        print(f"2. Fix {len(by_severity['MEDIUM'])} MEDIUM priority issues")
    if len(by_severity['LOW']) > 0:
        print(f"3. Consider fixing {len(by_severity['LOW'])} LOW priority issues")
    print()
    print("Reference: docs/TERMINOLOGY_GUIDE.md")

def main():
    # Detect project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print(f"Scanning TiaCAD documentation in: {project_root}")
    print()

    # Scan all documentation
    issues = scan_documentation(project_root)

    # Print report
    print_report(issues)

    # Exit code
    if issues:
        sys.exit(1)  # Non-zero exit for CI integration
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
