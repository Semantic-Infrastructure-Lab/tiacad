"""Parse-error hints for ${...} templates written unquoted in inline YAML (TCAD-UX-10)."""

import pytest

from tiacad_core.parser.yaml_with_lines import parse_yaml_with_lines


def _error(text):
    with pytest.raises(ValueError) as exc:
        parse_yaml_with_lines(text)
    return str(exc.value)


def test_unquoted_template_in_flow_mapping_gets_quote_hint():
    msg = _error("parameters: {width: ${w}, depth: 5}\n")
    assert "Invalid YAML" in msg
    assert "Quote each template" in msg


def test_unquoted_template_in_flow_sequence_gets_quote_hint():
    assert "Quote each template" in _error("origin: [${x}, 0, 0]\n")


def test_negated_template_keeps_its_own_hint():
    msg = _error("origin: [-${w/2}, 0, 0]\n")
    assert "negating a template" in msg
    assert "Quote each template" not in msg


def test_quoted_templates_parse():
    data, _ = parse_yaml_with_lines("parameters: {width: '${w}'}\norigin: ['${x}', 0, 0]\n")
    assert data["parameters"]["width"] == "${w}"
    assert data["origin"][0] == "${x}"


def test_unrelated_yaml_error_gets_no_hint():
    assert "Hint" not in _error("a: [1, 2\nb: 3\n")
