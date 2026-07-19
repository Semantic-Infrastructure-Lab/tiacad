"""Tests for `tiacad watch` (cmd_watch) — TCAD-VAL-9.

cmd_watch's core loop (FileWatcher.start()) blocks on a filesystem observer
until Ctrl+C — not something to run for real in a unit test (test_dag/
test_watcher.py already covers FileWatcher/IncrementalBuilder directly).
Instead this mocks FileWatcher to verify cmd_watch's own CLI-level
responsibilities: argument validation, wiring FileWatcher up correctly, and
handling KeyboardInterrupt cleanly.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tiacad_core.cli import cmd_watch
from tiacad_core.cli.watch import _resolve_watch_export_path

_SIMPLE_MODEL = """
parts:
  box:
    primitive: box
    parameters: { width: 10, height: 10, depth: 10 }
"""


def _args(input_path, export=None):
    return SimpleNamespace(input=str(input_path), export=export)


@pytest.fixture
def simple_model(tmp_path):
    model = tmp_path / "box.tiacad"
    model.write_text(_SIMPLE_MODEL)
    return model


class TestResolveWatchExportPath:
    def test_no_export_arg_returns_none(self):
        assert _resolve_watch_export_path(None) is None

    @pytest.mark.parametrize("ext", [".stl", ".3mf", ".step"])
    def test_supported_extension_returns_path(self, ext):
        result = _resolve_watch_export_path(f"out{ext}")
        assert result == Path(f"out{ext}")

    def test_unsupported_extension_returns_none(self, capsys):
        result = _resolve_watch_export_path("out.obj")
        assert result is None
        assert "Unsupported export format" in capsys.readouterr().err


class TestCmdWatch:
    def test_missing_file_fails(self, capsys):
        exit_code = cmd_watch(_args("does_not_exist.tiacad"))
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.out + captured.err

    def test_invalid_export_extension_fails(self, simple_model, capsys):
        exit_code = cmd_watch(_args(simple_model, export="out.obj"))
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unsupported export format" in captured.out + captured.err

    def test_constructs_filewatcher_and_starts_it(self, simple_model):
        with patch("tiacad_core.watcher.FileWatcher") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            exit_code = cmd_watch(_args(simple_model, export="out.stl"))

            assert exit_code == 0
            mock_cls.assert_called_once()
            call_args = mock_cls.call_args
            assert call_args.args[0] == Path(simple_model)
            assert call_args.kwargs["export_path"] == Path("out.stl")
            assert callable(call_args.kwargs["on_rebuild"])
            mock_instance.start.assert_called_once()

    def test_keyboard_interrupt_stops_cleanly(self, simple_model, capsys):
        with patch("tiacad_core.watcher.FileWatcher") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.start.side_effect = KeyboardInterrupt
            mock_cls.return_value = mock_instance

            exit_code = cmd_watch(_args(simple_model))

            assert exit_code == 0
            assert "Stopped" in capsys.readouterr().out
