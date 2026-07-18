"""
Negative trust scenarios: intentionally-bad models that must be flagged by
AssemblyValidator, proving the validators catch real defect classes rather
than just passing everything.

Distinct from examples/validation/negative/ (the Tier-5 parse/build negative
corpus, which covers malformed schema, unknown primitives, etc.) — every
model here parses and builds successfully. The defect is semantic: the
built geometry is wrong in a way a human or AI reviewer would need to catch
by eye if the validator didn't. See docs/developer/MODEL_VALIDATION.md
"Best Next Improvements" #7.
"""

from pathlib import Path

from tiacad_core.parser import TiaCADParser
from tiacad_core.validation.assembly_validator import AssemblyValidator

NEGATIVE_TRUST_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "validation" / "negative_trust"


def _validate(filename):
    doc = TiaCADParser.parse_file(str(NEGATIVE_TRUST_DIR / filename))
    return AssemblyValidator().validate_document(doc)


def test_nt1_hole_misses_plate_builds_successfully():
    # Must NOT raise — this is a semantic defect, not a parse/build failure.
    doc = TiaCADParser.parse_file(str(NEGATIVE_TRUST_DIR / "NT1_hole_misses_plate.tiacad"))
    assert doc.parts.get("result") is not None


def test_nt1_hole_misses_plate_is_flagged_as_error():
    report = _validate("NT1_hole_misses_plate.tiacad")
    assert not report.passed

    geometry_errors = [
        i for i in report.issues
        if i.category == "geometry" and i.severity.value == "ERROR"
    ]
    assert len(geometry_errors) == 1
    assert "Difference" in geometry_errors[0].message
    assert "removed 0.000mm" in geometry_errors[0].message


def test_nt2_disconnected_parts_builds_successfully():
    doc = TiaCADParser.parse_file(str(NEGATIVE_TRUST_DIR / "NT2_disconnected_parts.tiacad"))
    assert doc.parts.get("moved_floating_block") is not None


def test_nt2_disconnected_parts_is_flagged():
    report = _validate("NT2_disconnected_parts.tiacad")

    # DisconnectedPartsRule reports at WARNING, not ERROR — disconnected
    # groups can be legitimate (e.g. a multi-part kit), so this must not be
    # a hard build-blocking failure. It must still be surfaced.
    assert report.error_count == 0
    connectivity_issues = [i for i in report.issues if i.category == "connectivity"]
    assert len(connectivity_issues) == 1
    assert "disconnected" in connectivity_issues[0].message.lower()
