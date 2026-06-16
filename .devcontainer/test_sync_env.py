import importlib.util
import os
import runpy
import types
from pathlib import Path

import pytest


def load_sync_env() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "sync_env",
        Path(__file__).parent / "sync-env.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sync_env = load_sync_env()


class TestParseEnv:
    def test_parses_key_value_pairs(self) -> None:
        result = sync_env.parse_env("KEY=value\nOTHER=123\n")
        assert result == {"KEY": "value", "OTHER": "123"}

    def test_ignores_comment_lines(self) -> None:
        result = sync_env.parse_env("# comment\nKEY=value\n")
        assert result == {"KEY": "value"}

    def test_ignores_blank_lines(self) -> None:
        result = sync_env.parse_env("\n\nKEY=value\n\n")
        assert result == {"KEY": "value"}

    def test_ignores_lines_without_equals(self) -> None:
        result = sync_env.parse_env("NOEQUALSSIGN\nKEY=value\n")
        assert result == {"KEY": "value"}

    def test_preserves_value_containing_equals(self) -> None:
        result = sync_env.parse_env("KEY=a=b=c\n")
        assert result == {"KEY": "a=b=c"}

    def test_strips_whitespace_from_key(self) -> None:
        result = sync_env.parse_env("  KEY  =value\n")
        assert result == {"KEY": "value"}

    def test_empty_content_returns_empty_dict(self) -> None:
        assert sync_env.parse_env("") == {}

    def test_empty_value_is_preserved(self) -> None:
        result = sync_env.parse_env("KEY=\n")
        assert result == {"KEY": ""}


class TestMain:
    def test_appends_missing_keys(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        example = tmp_path / ".env.example"
        example.write_text("EXISTING=placeholder\nMISSING=placeholder\n")
        env = tmp_path / ".env"
        env.write_text("EXISTING=real_value\n")

        _run_main_in(tmp_path)

        result = env.read_text()
        assert "MISSING=placeholder" in result
        assert "EXISTING=real_value" in result
        captured = capsys.readouterr()
        assert "Added missing keys to .env: MISSING" in captured.out

    def test_no_change_when_all_keys_present(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        example = tmp_path / ".env.example"
        example.write_text("KEY=placeholder\n")
        env = tmp_path / ".env"
        original = "KEY=real_value\n"
        env.write_text(original)

        _run_main_in(tmp_path)

        assert env.read_text() == original
        captured = capsys.readouterr()
        assert ".env already contains all keys from .env.example" in captured.out

    def test_appended_key_on_new_line_when_no_trailing_newline(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        example = tmp_path / ".env.example"
        example.write_text("EXISTING=x\nNEW=placeholder\n")
        env = tmp_path / ".env"
        env.write_text("EXISTING=real_value")

        _run_main_in(tmp_path)

        lines = env.read_text().splitlines()
        assert "EXISTING=real_value" in lines
        assert "NEW=placeholder" in lines

    def test_multiple_missing_keys_all_appended(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        example = tmp_path / ".env.example"
        example.write_text("A=1\nB=2\nC=3\n")
        env = tmp_path / ".env"
        env.write_text("")

        _run_main_in(tmp_path)

        content = env.read_text()
        assert "A=1" in content
        assert "B=2" in content
        assert "C=3" in content
        captured = capsys.readouterr()
        assert "A" in captured.out
        assert "B" in captured.out
        assert "C" in captured.out


def _run_main_in(directory: Path) -> None:
    original_dir = Path.cwd()

    os.chdir(directory)
    try:
        sync_env.main()
    finally:
        os.chdir(original_dir)


class TestEntryPoint:
    def test_runs_as_script(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        (tmp_path / ".env.example").write_text("KEY=placeholder\n")
        (tmp_path / ".env").write_text("KEY=value\n")
        script = str(Path(__file__).parent / "sync-env.py")

        original_dir = Path.cwd()
        os.chdir(tmp_path)
        try:
            runpy.run_path(script, run_name="__main__")
        finally:
            os.chdir(original_dir)

        captured = capsys.readouterr()
        assert ".env already contains all keys from .env.example" in captured.out
