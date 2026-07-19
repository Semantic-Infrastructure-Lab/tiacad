"""AI/debug bundle generation for TiaCAD models."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

import yaml

from . import __version__
from .parser.parse_pipeline import extract_yaml_sections, normalize_yaml_aliases
from .parser.tiacad_parser import TiaCADParser
from .testing.geometry_summary import summarize_part_registry
from .validation.assembly_validator import AssemblyValidator


def create_debug_bundle(
    input_file: Path,
    *,
    bundle_dir: Path,
    validate_schema: bool = False,
    include_trust_render: bool = True,
    compare_bundle_dir: Path | None = None,
) -> Dict[str, Any]:
    """Build a stable debug bundle for one TiaCAD input file."""
    input_file = Path(input_file).resolve()
    bundle_dir = Path(bundle_dir).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)

    doc = TiaCADParser.parse_file(str(input_file), validate_schema=validate_schema)
    yaml_data = _load_normalized_yaml_data(doc, input_file)
    visible_parts = [name for name in doc.parts.list_parts() if not name.startswith('_')]
    default_part = _resolve_default_part_name(doc)

    resolved_model = _build_resolved_model_snapshot(doc, yaml_data, input_file, visible_parts, default_part)
    part_summaries = summarize_part_registry(doc.parts)
    build_trace = _build_build_trace(doc, resolved_model, part_summaries)

    validation_report = AssemblyValidator().validate_document(doc)
    validation_payload = json.loads(validation_report.to_json())

    trust_payload = _write_trust_render_artifacts(
        doc,
        bundle_dir=bundle_dir,
        include_trust_render=include_trust_render,
        title=input_file.stem,
        issues=validation_report.issues,
    )

    _write_json(bundle_dir / "resolved_model.json", resolved_model)
    _write_json(bundle_dir / "part_summaries.json", part_summaries)
    _write_json(bundle_dir / "build_trace.json", build_trace)
    _write_json(bundle_dir / "validation_report.json", validation_payload)
    _write_json(bundle_dir / "trust_render_manifest.json", trust_payload)

    compare_payload = None
    if compare_bundle_dir is not None:
        compare_payload = _build_compare_report(
            current_resolved_model=resolved_model,
            current_part_summaries=part_summaries,
            previous_bundle_dir=Path(compare_bundle_dir).resolve(),
        )
        _write_json(bundle_dir / "compare_report.json", compare_payload)

    manifest = _build_manifest(
        input_file=input_file,
        bundle_dir=bundle_dir,
        doc=doc,
        visible_parts=visible_parts,
        default_part=default_part,
        validation_payload=validation_payload,
        trust_payload=trust_payload,
        compare_payload=compare_payload,
    )
    _write_json(bundle_dir / "manifest.json", manifest)
    return manifest


def default_debug_bundle_dir(input_file: Path) -> Path:
    """Return the default bundle directory path for one input model."""
    input_file = Path(input_file)
    return input_file.with_name(f"{input_file.stem}.tiacad-debug")


def _load_normalized_yaml_data(doc, input_file: Path) -> Dict[str, Any]:
    """Load and normalize the YAML data used to produce the document."""
    if getattr(doc, 'yaml_string', None):
        yaml_data = yaml.safe_load(doc.yaml_string) or {}
    else:
        yaml_data = yaml.safe_load(input_file.read_text(encoding='utf-8')) or {}

    if not isinstance(yaml_data, dict):
        raise TypeError("TiaCAD debug bundle requires a top-level YAML mapping")
    return normalize_yaml_aliases(yaml_data)


def _build_resolved_model_snapshot(
    doc,
    yaml_data: Dict[str, Any],
    input_file: Path,
    visible_parts: list[str],
    default_part: str | None,
) -> Dict[str, Any]:
    """Build the resolved-model artifact for a debug bundle."""
    sections = extract_yaml_sections(yaml_data)
    return {
        'schema_version': '1',
        'input_file': str(input_file),
        'metadata': doc.metadata,
        'sections': {
            'imports': sections['imports'],
            'colors': sections['colors'],
            'materials': sections['materials'],
            'references': sections['references'],
            'parts': sections['parts'],
            'sketches': sections['sketches'],
            'operations': sections['operations'],
            'export': sections['export'],
        },
        'resolved': {
            'parameters': doc.parameters,
            'references': doc.references,
            'export_config': doc.export_config,
            'visible_parts': visible_parts,
            'default_part': default_part,
        },
    }


def _format_spec_scalars(spec: Dict[str, Any], *, exclude: tuple = ()) -> str:
    """Render a spec dict's top-level scalar fields as 'key=value, key=value'."""
    fields = [
        f"{key}={value}"
        for key, value in sorted(spec.items())
        if key not in exclude and isinstance(value, (str, int, float, bool))
    ]
    return ', '.join(fields)


def _summarize_part_node(spec: Dict[str, Any]) -> str:
    """One-line human-readable summary of a declared part's shape and dimensions."""
    primitive = spec.get('primitive', 'part')
    params = spec.get('parameters', spec)
    scalars = _format_spec_scalars(params, exclude=('primitive',))
    return f"{primitive} ({scalars})" if scalars else str(primitive)


def _summarize_operation_node(op_type: Any, inputs: list, outputs: list) -> str:
    """One-line human-readable summary of an operation's declared inputs/outputs."""
    label = op_type or 'operation'
    input_text = ', '.join(inputs) if inputs else '(none declared)'
    output_text = ', '.join(outputs) if outputs else '(none)'
    return f"{label}: {input_text} -> {output_text}"


def _build_build_trace(doc, resolved_model: Dict[str, Any], part_summaries: Dict[str, Any]) -> Dict[str, Any]:
    """Build a simple, stable build trace from declared parts and operations."""
    sections = resolved_model['sections']
    declared_parts = sections['parts']
    declared_operations = sections['operations']
    part_names = set(doc.parts.list_parts())

    nodes = []
    for part_name, spec in declared_parts.items():
        nodes.append({
            'name': part_name,
            'node_type': 'part',
            'declared_in': 'parts',
            'inputs': [],
            'outputs': [part_name] if part_name in part_names else [],
            'spec': spec,
            'summary': part_summaries.get(part_name),
            'summary_text': _summarize_part_node(spec),
        })

    for op_name, spec in declared_operations.items():
        op_type = spec.get('type')
        inputs = _extract_operation_inputs(spec)
        outputs = _trace_outputs_for_operation(op_name, part_names)
        nodes.append({
            'name': op_name,
            'node_type': 'operation',
            'declared_in': 'operations',
            'operation_type': op_type,
            'inputs': inputs,
            'outputs': outputs,
            'spec': spec,
            'output_summaries': {name: part_summaries.get(name) for name in outputs},
            'summary_text': _summarize_operation_node(op_type, inputs, outputs),
        })

    return {
        'schema_version': '1',
        'default_part': resolved_model['resolved']['default_part'],
        'nodes': nodes,
    }


def _write_trust_render_artifacts(
    doc,
    *,
    bundle_dir: Path,
    include_trust_render: bool,
    title: str,
    issues: list,
) -> Dict[str, Any]:
    """Attempt trust rendering and return a manifest payload."""
    if not include_trust_render:
        return {
            'status': 'skipped',
            'output': None,
            'error': None,
        }

    output_name = "final_trust.png"
    output_path = bundle_dir / output_name

    try:
        written_path = _render_trust_preview(doc, output_path, title, issues)
        return {
            'status': 'ok',
            'output': output_name,
            'absolute_output': written_path,
            'error': None,
        }
    except Exception as exc:
        return {
            'status': 'failed',
            'output': None,
            'error': str(exc),
        }


def _render_trust_preview(doc, output_path: Path, title: str, issues: list) -> str:
    """Render the trust preview lazily so missing render deps do not break import."""
    from .visual.trust_renderer import render_trust

    return render_trust(doc, str(output_path), title=title, issues=issues)


def _build_manifest(
    *,
    input_file: Path,
    bundle_dir: Path,
    doc,
    visible_parts: list[str],
    default_part: str | None,
    validation_payload: Dict[str, Any],
    trust_payload: Dict[str, Any],
    compare_payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Build the top-level bundle manifest."""
    return {
        'schema_version': '1',
        'tool': 'tiacad debug',
        'tiacad_version': __version__,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'input_file': str(input_file),
        'bundle_dir': str(bundle_dir),
        'summary': {
            'parts_total': len(doc.parts.list_parts()),
            'visible_parts_total': len(visible_parts),
            'operations_total': len(doc.operations),
            'default_part': default_part,
            'validation': {
                'passed': validation_payload['passed'],
                'error_count': validation_payload['error_count'],
                'warning_count': validation_payload['warning_count'],
                'info_count': validation_payload['info_count'],
            },
            'compare': {
                'enabled': compare_payload is not None,
                'changed_parts_total': 0 if compare_payload is None else compare_payload['summary']['changed_parts_total'],
                'changed_operations_total': 0 if compare_payload is None else compare_payload['summary']['changed_operations_total'],
            },
        },
        'outputs': {
            'resolved_model': 'resolved_model.json',
            'build_trace': 'build_trace.json',
            'part_summaries': 'part_summaries.json',
            'validation_report': 'validation_report.json',
            'trust_render_manifest': 'trust_render_manifest.json',
            'final_trust': trust_payload['output'],
            'compare_report': None if compare_payload is None else 'compare_report.json',
        },
    }


def _resolve_default_part_name(doc) -> str | None:
    """Pick the default/final part for the debug bundle summary."""
    if doc.export_config.get('default_part') is not None:
        return doc.export_config['default_part']
    if doc.operations:
        return list(doc.operations.keys())[-1]
    parts = doc.parts.list_parts()
    return parts[0] if parts else None


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON payload to disk with stable formatting."""
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True),
        encoding='utf-8',
    )


def _extract_operation_inputs(spec: Dict[str, Any]) -> list[str]:
    """Extract obvious input part references from an operation spec."""
    inputs: list[str] = []
    for field in ('input', 'base', 'tool'):
        value = spec.get(field)
        if isinstance(value, str):
            inputs.append(value)
    for field in ('inputs', 'subtract', 'tools'):
        values = spec.get(field, [])
        if isinstance(values, list):
            inputs.extend(value for value in values if isinstance(value, str))
    return inputs


def _trace_outputs_for_operation(op_name: str, part_names: Iterable[str]) -> list[str]:
    """Infer output part names for an operation from the final registry."""
    outputs = []
    for part_name in sorted(part_names):
        if part_name == op_name or part_name.startswith(f"{op_name}_"):
            outputs.append(part_name)
    return outputs


def _build_compare_report(
    *,
    current_resolved_model: Dict[str, Any],
    current_part_summaries: Dict[str, Any],
    previous_bundle_dir: Path,
) -> Dict[str, Any]:
    """Compare the current bundle state against a previous debug bundle."""
    previous_resolved_model = _read_json(previous_bundle_dir / "resolved_model.json")
    previous_part_summaries = _read_json(previous_bundle_dir / "part_summaries.json")

    current_operations = current_resolved_model['sections']['operations']
    previous_operations = previous_resolved_model['sections']['operations']

    current_default = current_resolved_model['resolved']['default_part']
    previous_default = previous_resolved_model['resolved']['default_part']

    changed_parts, added_parts, removed_parts = _compare_part_summaries(
        previous_part_summaries,
        current_part_summaries,
    )
    changed_operations, added_operations, removed_operations = _compare_named_specs(
        previous_operations,
        current_operations,
    )

    return {
        'schema_version': '1',
        'previous_bundle_dir': str(previous_bundle_dir),
        'summary': {
            'changed_parts_total': len(changed_parts),
            'added_parts_total': len(added_parts),
            'removed_parts_total': len(removed_parts),
            'changed_operations_total': len(changed_operations),
            'added_operations_total': len(added_operations),
            'removed_operations_total': len(removed_operations),
            'default_part_changed': current_default != previous_default,
        },
        'default_part': {
            'previous': previous_default,
            'current': current_default,
        },
        'changed_parts': changed_parts,
        'added_parts': added_parts,
        'removed_parts': removed_parts,
        'changed_operations': changed_operations,
        'added_operations': added_operations,
        'removed_operations': removed_operations,
    }


def _compare_part_summaries(previous: Dict[str, Any], current: Dict[str, Any]):
    """Compare part summaries and return changed/added/removed collections."""
    changed = []
    added = sorted(name for name in current.keys() if name not in previous)
    removed = sorted(name for name in previous.keys() if name not in current)

    for part_name in sorted(set(previous.keys()) & set(current.keys())):
        previous_summary = previous[part_name]
        current_summary = current[part_name]
        fields = {}

        for axis in ('x', 'y', 'z'):
            prev_val = previous_summary['extents'][axis]
            curr_val = current_summary['extents'][axis]
            if prev_val != curr_val:
                fields[f'extents.{axis}'] = {
                    'previous': prev_val,
                    'current': curr_val,
                    'delta': curr_val - prev_val,
                }

        for metric_name in ('volume', 'surface_area'):
            prev_val = previous_summary['metrics'][metric_name]
            curr_val = current_summary['metrics'][metric_name]
            if prev_val != curr_val:
                fields[f'metrics.{metric_name}'] = {
                    'previous': prev_val,
                    'current': curr_val,
                    'delta': None if prev_val is None or curr_val is None else curr_val - prev_val,
                }

        prev_components = previous_summary.get('mesh', {}).get('component_count')
        curr_components = current_summary.get('mesh', {}).get('component_count')
        if prev_components != curr_components:
            fields['mesh.component_count'] = {
                'previous': prev_components,
                'current': curr_components,
            }

        if fields:
            changed.append({
                'name': part_name,
                'fields': fields,
            })

    return changed, added, removed


def _compare_named_specs(previous: Dict[str, Any], current: Dict[str, Any]):
    """Compare named sections like operations and return changed/added/removed collections."""
    changed = []
    added = sorted(name for name in current.keys() if name not in previous)
    removed = sorted(name for name in previous.keys() if name not in current)

    for name in sorted(set(previous.keys()) & set(current.keys())):
        if previous[name] != current[name]:
            changed.append({
                'name': name,
                'previous': previous[name],
                'current': current[name],
            })

    return changed, added, removed


def _read_json(path: Path) -> Dict[str, Any]:
    """Read a JSON file into a dict."""
    return json.loads(path.read_text(encoding='utf-8'))


def _json_safe(value: Any) -> Any:
    """Recursively normalize payloads to JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
