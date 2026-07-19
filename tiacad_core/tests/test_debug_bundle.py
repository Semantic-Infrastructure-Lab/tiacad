"""Tests for AI/debug bundle generation."""

import json
from pathlib import Path

from tiacad_core.debug_bundle import (
    create_debug_bundle,
    default_debug_bundle_dir,
    _summarize_part_node,
    _summarize_operation_node,
)


def test_default_debug_bundle_dir_uses_input_stem(tmp_path):
    input_file = tmp_path / "hanger.yaml"
    input_file.write_text("parts: {}\n", encoding="utf-8")

    bundle_dir = default_debug_bundle_dir(input_file)

    assert bundle_dir == tmp_path / "hanger.tiacad-debug"


def test_create_debug_bundle_writes_expected_artifacts(tmp_path, monkeypatch):
    input_file = tmp_path / "box.yaml"
    input_file.write_text(
        """
metadata:
  name: Debug Box
parts:
  box:
    primitive: box
    parameters:
      width: 10
      height: 20
      depth: 30
""",
        encoding="utf-8",
    )
    bundle_dir = tmp_path / "bundle"

    def fake_render(doc, output_path, title, issues):
        output = tmp_path / output_path if not str(output_path).startswith("/") else output_path
        output = bundle_dir / "final_trust.png"
        output.write_bytes(b"fake-png")
        return str(output)

    monkeypatch.setattr('tiacad_core.debug_bundle._render_trust_preview', fake_render)

    manifest = create_debug_bundle(input_file, bundle_dir=bundle_dir)

    assert manifest['outputs']['resolved_model'] == 'resolved_model.json'
    assert manifest['outputs']['build_trace'] == 'build_trace.json'
    assert manifest['outputs']['part_summaries'] == 'part_summaries.json'
    assert manifest['outputs']['validation_report'] == 'validation_report.json'
    assert manifest['outputs']['trust_render_manifest'] == 'trust_render_manifest.json'
    assert manifest['outputs']['final_trust'] == 'final_trust.png'

    for filename in (
        'manifest.json',
        'resolved_model.json',
        'build_trace.json',
        'part_summaries.json',
        'validation_report.json',
        'trust_render_manifest.json',
        'final_trust.png',
    ):
        assert (bundle_dir / filename).exists()

    resolved_model = json.loads((bundle_dir / 'resolved_model.json').read_text(encoding='utf-8'))
    assert resolved_model['resolved']['default_part'] == 'box'
    assert resolved_model['resolved']['visible_parts'] == ['box']

    build_trace = json.loads((bundle_dir / 'build_trace.json').read_text(encoding='utf-8'))
    assert build_trace['default_part'] == 'box'
    assert build_trace['nodes'][0]['name'] == 'box'
    assert build_trace['nodes'][0]['node_type'] == 'part'
    assert build_trace['nodes'][0]['summary_text'] == 'box (depth=30, height=20, width=10)'

    part_summaries = json.loads((bundle_dir / 'part_summaries.json').read_text(encoding='utf-8'))
    assert 'box' in part_summaries
    assert part_summaries['box']['extents']['x'] == 10.0
    assert part_summaries['box']['extents']['y'] == 30.0
    assert part_summaries['box']['extents']['z'] == 20.0

    validation_report = json.loads((bundle_dir / 'validation_report.json').read_text(encoding='utf-8'))
    assert validation_report['passed'] is True

    trust_manifest = json.loads((bundle_dir / 'trust_render_manifest.json').read_text(encoding='utf-8'))
    assert trust_manifest['status'] == 'ok'
    assert trust_manifest['output'] == 'final_trust.png'


def test_summarize_part_node_uses_nested_parameters():
    spec = {'primitive': 'cylinder', 'parameters': {'radius': 5, 'height': 12}}
    assert _summarize_part_node(spec) == 'cylinder (height=12, radius=5)'


def test_summarize_part_node_falls_back_to_flat_spec():
    spec = {'primitive': 'box', 'width': 10, 'height': 20, 'depth': 30}
    assert _summarize_part_node(spec) == 'box (depth=30, height=20, width=10)'


def test_summarize_part_node_with_no_scalar_params():
    assert _summarize_part_node({'primitive': 'box', 'parameters': {}}) == 'box'


def test_summarize_operation_node_formats_inputs_and_outputs():
    text = _summarize_operation_node('boolean', ['base', 'lid'], ['assembly'])
    assert text == 'boolean: base, lid -> assembly'


def test_summarize_operation_node_handles_missing_type_and_io():
    assert _summarize_operation_node(None, [], []) == 'operation: (none declared) -> (none)'


def test_create_debug_bundle_records_trust_render_failure(tmp_path, monkeypatch):
    input_file = tmp_path / "box.yaml"
    input_file.write_text(
        """
parts:
  box:
    primitive: box
    parameters:
      width: 5
      height: 5
      depth: 5
""",
        encoding="utf-8",
    )
    bundle_dir = tmp_path / "bundle"

    def fake_render(_doc, _output_path, _title, _issues):
        raise RuntimeError("render backend unavailable")

    monkeypatch.setattr('tiacad_core.debug_bundle._render_trust_preview', fake_render)

    manifest = create_debug_bundle(input_file, bundle_dir=bundle_dir)

    assert manifest['outputs']['final_trust'] is None
    trust_manifest = json.loads((bundle_dir / 'trust_render_manifest.json').read_text(encoding='utf-8'))
    assert trust_manifest['status'] == 'failed'
    assert 'render backend unavailable' in trust_manifest['error']


def test_create_debug_bundle_compare_report_detects_changes(tmp_path, monkeypatch):
    previous_input = tmp_path / "previous.yaml"
    current_input = tmp_path / "current.yaml"
    previous_input.write_text(
        """
parts:
  box:
    primitive: box
    parameters:
      width: 10
      height: 10
      depth: 10
""",
        encoding="utf-8",
    )
    current_input.write_text(
        """
parts:
  box:
    primitive: box
    parameters:
      width: 20
      height: 10
      depth: 10
operations:
  moved:
    type: transform
    input: box
    transforms:
      - translate: [5, 0, 0]
""",
        encoding="utf-8",
    )

    def fake_render(_doc, output_path, _title, _issues):
        Path(output_path).write_bytes(b"fake-png")
        return str(output_path)

    monkeypatch.setattr('tiacad_core.debug_bundle._render_trust_preview', fake_render)

    previous_bundle = tmp_path / "previous-bundle"
    current_bundle = tmp_path / "current-bundle"
    create_debug_bundle(previous_input, bundle_dir=previous_bundle)
    manifest = create_debug_bundle(
        current_input,
        bundle_dir=current_bundle,
        compare_bundle_dir=previous_bundle,
    )

    assert manifest['outputs']['compare_report'] == 'compare_report.json'
    compare_report = json.loads((current_bundle / 'compare_report.json').read_text(encoding='utf-8'))
    assert compare_report['summary']['changed_parts_total'] >= 1
    assert compare_report['summary']['changed_operations_total'] == 0
    assert compare_report['summary']['added_operations_total'] == 1
    assert compare_report['default_part']['previous'] == 'box'
    assert compare_report['default_part']['current'] == 'moved'
    assert any(item['name'] == 'box' for item in compare_report['changed_parts'])
