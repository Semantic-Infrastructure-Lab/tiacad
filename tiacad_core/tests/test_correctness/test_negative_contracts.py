"""
Negative Input Contracts (Tier 5)

Proves the parser fails *loudly and correctly* on bad input — never a raw
traceback, never a silent empty/wrong solid. The counterpart to every
happy-path corpus in this repo: every model under
examples/validation/negative/ is *intentionally broken* in one specific way,
and each must raise a specific, typed TiaCADError subclass (never a bare
Exception, never an uncaught traceback, never a silent success) with a
message that names the actual problem.

See docs/developer/VALIDATION_STRENGTHENING.md section 3, Tier 5.

Author: TIA
"""

from pathlib import Path

import pytest

from tiacad_core.parser import TiaCADParser
from tiacad_core.parser.parameter_resolver import ParameterResolutionError
from tiacad_core.parser.parts_builder import PartsBuilderError
from tiacad_core.parser.operations_builder import OperationsBuilderError
from tiacad_core.parser.errors import TiaCADParserError
from tiacad_core.utils.exceptions import TiaCADError

NEGATIVE_DIR = (
    Path(__file__).parent.parent.parent.parent / "examples" / "validation" / "negative"
)


def _path(name: str) -> str:
    p = NEGATIVE_DIR / name
    assert p.exists(), f"Fixture missing: {p}"
    return str(p)


def test_negative_directory_is_discoverable():
    """
    Guards against a silently-empty fixture set (e.g. a renamed/deleted
    directory) — if this fails, every test below is vacuous.
    """
    files = sorted(NEGATIVE_DIR.glob("N*.tiacad"))
    assert len(files) >= 6, (
        f"Expected at least 6 negative fixtures under {NEGATIVE_DIR}, found "
        f"{len(files)}: {[f.name for f in files]}"
    )


class TestBadSpatialReference:
    """N1: translate: to: references a part that doesn't exist."""

    def test_raises_typed_error(self):
        with pytest.raises(TiaCADError) as exc_info:
            TiaCADParser.parse_file(_path("N1_bad_spatial_ref.tiacad"))
        # Currently surfaces through the inline-transform path as an
        # OperationsBuilderError wrapping a SpatialResolverError — either
        # way it must be a real TiaCADError, not KeyError/AttributeError.
        assert isinstance(exc_info.value, OperationsBuilderError)
        message = str(exc_info.value)
        assert "nonexistent_part" in message
        assert "not found" in message.lower()


class TestCyclicParameterDependency:
    """N2: parameter `a` depends on `b`, `b` depends on `a`."""

    def test_raises_typed_error(self):
        with pytest.raises(ParameterResolutionError) as exc_info:
            TiaCADParser.parse_file(_path("N2_cyclic_parameter.tiacad"))
        message = str(exc_info.value)
        assert "circular" in message.lower()
        # Cycle-node order depends on set iteration (PYTHONHASHSEED), so
        # assert both offending parameter names appear rather than a fixed
        # order.
        assert "a" in message and "b" in message


class TestNegativeDimension:
    """
    N3: box width is negative.

    Before the 2026-07-11 fix, this reached the OCCT kernel unchecked and
    raised a message-less Standard_DomainError, wrapped into a
    PartsBuilderError with an EMPTY message body — technically typed, but
    not "loudly and correctly" per this tier's bar. See
    KNOWN_LIMITATIONS.md #12.
    """

    def test_raises_typed_error_with_useful_message(self):
        with pytest.raises(PartsBuilderError) as exc_info:
            TiaCADParser.parse_file(_path("N3_negative_dimension.tiacad"))
        message = str(exc_info.value)
        assert message.strip(), "error message must not be empty"
        assert "width" in message.lower()
        assert "-10" in message


class TestUnknownPrimitive:
    """N4: primitive: boxx is misspelled/unknown."""

    def test_raises_typed_error(self):
        with pytest.raises(PartsBuilderError) as exc_info:
            TiaCADParser.parse_file(_path("N4_unknown_primitive.tiacad"))
        message = str(exc_info.value)
        assert "boxx" in message
        assert "unknown" in message.lower() or "primitive" in message.lower()


class TestMalformedSchemaMissingField:
    """N5: box primitive missing the required 'depth' parameter."""

    def test_raises_typed_error(self):
        with pytest.raises(PartsBuilderError) as exc_info:
            TiaCADParser.parse_file(_path("N5_malformed_schema.tiacad"))
        message = str(exc_info.value)
        assert "depth" in message.lower()
        assert "missing" in message.lower()


class TestDuplicatePartName:
    """
    N6: 'block' is defined twice under parts:.

    Before the 2026-07-11 fix, PyYAML's default SafeLoader silently let the
    second definition clobber the first with no error at all — a
    silent-wrong-output bug, not a parse failure. See KNOWN_LIMITATIONS.md
    #12.
    """

    def test_raises_typed_error(self):
        with pytest.raises(TiaCADParserError) as exc_info:
            TiaCADParser.parse_file(_path("N6_duplicate_part_name.tiacad"))
        message = str(exc_info.value)
        assert "duplicate" in message.lower()
        assert "block" in message


# ---------------------------------------------------------------------------
# Cross-cutting: every negative fixture must raise a TiaCADError subclass,
# never a bare/builtin exception (KeyError, AttributeError, TypeError, ...)
# and never succeed silently.
# ---------------------------------------------------------------------------

ALL_NEGATIVE_FIXTURES = [
    "N1_bad_spatial_ref.tiacad",
    "N2_cyclic_parameter.tiacad",
    "N3_negative_dimension.tiacad",
    "N4_unknown_primitive.tiacad",
    "N5_malformed_schema.tiacad",
    "N6_duplicate_part_name.tiacad",
]


@pytest.mark.parametrize("filename", ALL_NEGATIVE_FIXTURES)
def test_every_negative_fixture_raises_typed_tiacad_error(filename):
    try:
        TiaCADParser.parse_file(_path(filename))
    except TiaCADError:
        return  # correct: a typed TiaCAD error, loudly and specifically
    except Exception as e:  # pragma: no cover - failure path
        pytest.fail(
            f"{filename} raised a raw/untyped exception "
            f"{type(e).__module__}.{type(e).__name__}: {e} "
            f"— expected a TiaCADError subclass"
        )
    else:
        pytest.fail(f"{filename} parsed successfully — expected a TiaCADError")
