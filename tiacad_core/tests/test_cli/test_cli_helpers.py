"""Tests for extracted CLI helper behavior."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from tiacad_core.cli import (
    _build_check_rows,
    _empty_audit_result,
    _export_document,
    _format_audit_dims,
    _format_watch_rebuild_line,
    _get_default_part_name,
    _get_part_display_type,
    _make_watch_rebuild_callback,
    _measure_audit_final_part,
    _print_debug_bundle_summary,
    _print_info_report,
    _print_info_statistics,
    _print_key_value_section,
    _print_operation_section,
    _print_part_section,
    _resolve_build_output,
    _resolve_debug_bundle_path,
    _resolve_render_output_path,
    _resolve_watch_export_path,
    cmd_debug,
    cmd_render,
    _visible_parts,
)
from tiacad_core.watcher import WatchBuildResult
from tiacad_core.parser.tiacad_parser import TiaCADParser


def test_get_default_part_name_prefers_last_operation():
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        },
        'operations': {
            'moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [{'translate': [5, 0, 0]}],
            }
        },
    })

    assert _get_default_part_name(doc) == 'moved'


def test_visible_parts_excludes_internal_names():
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            },
            '_internal': {
                'primitive': 'box',
                'parameters': {'width': 1, 'height': 1, 'depth': 1},
            },
        },
    })

    assert _visible_parts(doc) == ['box']


def test_build_check_rows_marks_final_part():
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        },
        'operations': {
            'moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [{'translate': [5, 0, 0]}],
            }
        },
    })

    rows, errors = _build_check_rows(doc)

    assert errors == []
    assert [row['name'] for row in rows] == ['box', 'moved']
    assert [row['is_final'] for row in rows] == [False, True]


def test_measure_audit_final_part_warns_on_non_positive_volume():
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        }
    })
    result = _empty_audit_result(input_file=type('FakePath', (), {'name': 'box.yaml'})())

    with patch('tiacad_core.cli.audit._measure_part_dimensions', return_value={
        'width': 10.0,
        'height': 10.0,
        'depth': 10.0,
        'volume': 0.0,
    }):
        _measure_audit_final_part(doc, result)

    assert result['status'] == 'warn'
    assert result['dims'] == (10.0, 10.0, 10.0)
    assert result['issues'] == ['zero/negative volume: 0.0']


def test_format_audit_dims_prefers_truncated_error():
    result = _empty_audit_result(input_file=type('FakePath', (), {'name': 'box.yaml'})())
    result['error'] = 'x' * 40

    assert _format_audit_dims(result) == 'x' * 30


def test_resolve_build_output_defaults_to_3mf(tmp_path):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")

    output_file = _resolve_build_output(input_file, None)

    assert output_file == input_file.with_suffix('.3mf')


def test_resolve_build_output_rejects_unknown_extension(tmp_path, capsys):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")

    output_file = _resolve_build_output(input_file, str(tmp_path / "box.obj"))

    captured = capsys.readouterr()
    assert output_file is None
    assert "Unsupported output format: .obj" in captured.err


def test_export_document_dispatches_by_extension(tmp_path):
    class FakeDoc:
        def __init__(self):
            self.calls = []

        def export_stl(self, path, part_name=None):
            self.calls.append(("stl", path, part_name))

        def export_3mf(self, path, part_name=None):
            self.calls.append(("3mf", path, part_name))

        def export_step(self, path, part_name=None):
            self.calls.append(("step", path, part_name))

    doc = FakeDoc()

    _export_document(doc, tmp_path / "box.stl", "part_a")
    _export_document(doc, tmp_path / "box.3mf", "part_b")
    _export_document(doc, tmp_path / "box.step", None)

    assert doc.calls == [
        ("stl", str(tmp_path / "box.stl"), "part_a"),
        ("3mf", str(tmp_path / "box.3mf"), "part_b"),
        ("step", str(tmp_path / "box.step"), None),
    ]


def test_resolve_watch_export_path_accepts_supported_extension(tmp_path):
    export_path = _resolve_watch_export_path(str(tmp_path / "watch.3mf"))

    assert export_path == tmp_path / "watch.3mf"


def test_resolve_watch_export_path_rejects_unknown_extension(tmp_path, capsys):
    export_path = _resolve_watch_export_path(str(tmp_path / "watch.obj"))

    captured = capsys.readouterr()
    assert export_path is None
    assert "Unsupported export format: .obj" in captured.err


def test_format_watch_rebuild_line_success_includes_cache_and_export():
    result = WatchBuildResult(
        rebuild_ms=112,
        rebuilt=1,
        cached=3,
        exported_path="/tmp/output.3mf",
        is_initial=False,
    )

    line = _format_watch_rebuild_line(result)

    assert "changed" in line
    assert "1 rebuilt, 3 cached" in line
    assert "output.3mf" in line


def test_format_watch_rebuild_line_failure_includes_error():
    result = WatchBuildResult(error="build exploded", is_initial=True)

    line = _format_watch_rebuild_line(result)

    assert "initial" in line
    assert "build exploded" in line


def test_make_watch_rebuild_callback_prints_line(capsys):
    callback = _make_watch_rebuild_callback()
    callback(WatchBuildResult(rebuild_ms=10, rebuilt=1))

    captured = capsys.readouterr()
    assert "1 rebuilt" in captured.out


def test_get_part_display_type_prefers_operation_type():
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        },
        'operations': {
            'moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [{'translate': [5, 0, 0]}],
            }
        },
    })

    assert _get_part_display_type(doc.parts.get('moved')) == 'transform'


def test_print_key_value_section_skips_empty(capsys):
    _print_key_value_section("Metadata:", [])

    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_part_section_uses_visible_parts_and_display_type(capsys):
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            },
            '_internal': {
                'primitive': 'box',
                'parameters': {'width': 1, 'height': 1, 'depth': 1},
            },
        },
        'operations': {
            'moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [{'translate': [5, 0, 0]}],
            }
        },
    })

    visible_parts = _print_part_section(doc)

    captured = capsys.readouterr()
    assert visible_parts == ['box', 'moved']
    assert "box (box)" in captured.out
    assert "moved (transform)" in captured.out
    assert "_internal" not in captured.out


def test_print_operation_section_skips_empty_doc(capsys):
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        }
    })

    _print_operation_section(doc)

    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_info_statistics_uses_visible_part_count(capsys):
    doc = TiaCADParser.parse_dict({
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            },
            '_internal': {
                'primitive': 'box',
                'parameters': {'width': 1, 'height': 1, 'depth': 1},
            },
        }
    })

    _print_info_statistics(doc, ['box'])

    captured = capsys.readouterr()
    assert "Total parts: 1" in captured.out
    assert "Parameters: 0" in captured.out
    assert "Operations: 0" in captured.out


def test_print_info_report_includes_sections(capsys, tmp_path):
    input_file = tmp_path / "example.yaml"
    input_file.write_text("parts: {}\n")
    doc = TiaCADParser.parse_dict({
        'metadata': {'name': 'Example'},
        'parameters': {'width': 10},
        'parts': {
            'box': {
                'primitive': 'box',
                'parameters': {'width': 10, 'height': 10, 'depth': 10},
            }
        },
        'operations': {
            'moved': {
                'type': 'transform',
                'input': 'box',
                'transforms': [{'translate': [5, 0, 0]}],
            }
        },
    })

    _print_info_report(input_file, doc)

    captured = capsys.readouterr()
    assert input_file.name in captured.out
    assert "Metadata:" in captured.out
    assert "Parameters (1):" in captured.out
    assert "Parts (2):" in captured.out
    assert "Operations (1):" in captured.out
    assert "Total parts: 2" in captured.out


def test_resolve_debug_bundle_path_defaults_from_input(tmp_path):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")

    bundle_dir = _resolve_debug_bundle_path(input_file, None)

    assert bundle_dir == (tmp_path / "box.tiacad-debug").resolve()


def test_print_debug_bundle_summary_includes_trust_warning(capsys, tmp_path):
    manifest = {
        'summary': {
            'parts_total': 2,
            'visible_parts_total': 1,
            'operations_total': 1,
            'default_part': 'final',
            'validation': {'passed': True, 'error_count': 0, 'warning_count': 1, 'info_count': 0},
            'compare': {'enabled': True, 'changed_parts_total': 2, 'changed_operations_total': 1},
        },
        'outputs': {'final_trust': None},
    }

    _print_debug_bundle_summary(manifest, tmp_path / "bundle")

    captured = capsys.readouterr()
    assert "Debug bundle written" in captured.out
    assert "Trust render unavailable" in captured.out
    assert "2 changed parts" in captured.out


def test_cmd_debug_prints_manifest_json(tmp_path, capsys):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")
    bundle_dir = tmp_path / "bundle"
    manifest = {
        'summary': {
            'parts_total': 1,
            'visible_parts_total': 1,
            'operations_total': 0,
            'default_part': 'box',
            'validation': {'passed': True, 'error_count': 0, 'warning_count': 0, 'info_count': 0},
        },
        'outputs': {'final_trust': 'final_trust.png'},
    }
    args = SimpleNamespace(
        input=str(input_file),
        bundle=str(bundle_dir),
        validate_schema=False,
        no_trust_render=False,
        compare=None,
        json=True,
        verbose=False,
    )

    with patch('tiacad_core.debug_bundle.create_debug_bundle', return_value=manifest):
        rc = cmd_debug(args)

    captured = capsys.readouterr()
    assert rc == 0
    json_start = captured.out.find('{')
    assert json_start >= 0
    payload = json.loads(captured.out[json_start:])
    assert payload['summary']['default_part'] == 'box'


def test_resolve_render_output_path_defaults_from_input(tmp_path):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")

    output_path = _resolve_render_output_path(input_file, None)

    assert output_path == (tmp_path / "box_trust.png").resolve()


def test_resolve_render_output_path_honors_explicit_arg(tmp_path):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")

    output_path = _resolve_render_output_path(input_file, str(tmp_path / "custom.png"))

    assert output_path == (tmp_path / "custom.png").resolve()


def test_cmd_render_reports_missing_file(tmp_path, capsys):
    args = SimpleNamespace(
        input=str(tmp_path / "missing.yaml"),
        output=None,
        validate_schema=False,
        verbose=False,
    )

    rc = cmd_render(args)

    captured = capsys.readouterr()
    assert rc == 1
    assert "File not found" in captured.out or "File not found" in captured.err


def test_cmd_render_writes_png(tmp_path, capsys):
    input_file = tmp_path / "box.yaml"
    input_file.write_text("parts: {}\n")
    output_path = tmp_path / "box_trust.png"
    args = SimpleNamespace(
        input=str(input_file),
        output=str(output_path),
        validate_schema=False,
        verbose=False,
    )

    fake_doc = object()
    fake_issues = []

    with patch('tiacad_core.parser.tiacad_parser.TiaCADParser.parse_file', return_value=fake_doc), \
         patch('tiacad_core.validation.assembly_validator.AssemblyValidator.validate_document') as mock_validate, \
         patch('tiacad_core.visual.trust_renderer.render_trust', return_value=str(output_path)) as mock_render:
        mock_validate.return_value = SimpleNamespace(issues=fake_issues)
        rc = cmd_render(args)

    captured = capsys.readouterr()
    assert rc == 0
    assert "Trust render written" in captured.out
    mock_render.assert_called_once_with(fake_doc, str(output_path), title="box", issues=fake_issues)
