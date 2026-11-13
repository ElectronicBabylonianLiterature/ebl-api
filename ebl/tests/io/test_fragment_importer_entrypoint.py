import os
from pathlib import Path
import runpy
import sys
from typing import cast
from unittest.mock import Mock, patch

import pytest

from ebl.io.fragments import importer, importer_cli


@pytest.mark.parametrize(
    "arguments,expected_status",
    [
        (["--help"], 0),
        (["import", "--help"], 0),
        (["validate", "--help"], 0),
        (["reindex", "--help"], 0),
        (["invalid command with spaces"], 2),
        ([], 2),
    ],
    ids=["help", "import-help", "validate-help", "reindex-help", "invalid", "empty"],
)
def test_canonical_module_cli_contract(
    arguments: list[str], expected_status: int, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        importer_cli.main(arguments)

    assert exit_info.value.code == expected_status
    captured_output, captured_error = cast(tuple[str, str], capsys.readouterr())
    assert captured_output or captured_error


def test_canonical_module_preserves_process_context_and_arguments(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    arguments = ["import", "file name.json", "", "literal;$HOME", "line\nbreak"]
    monkeypatch.setattr(sys, "argv", ["importer_cli", *arguments])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IMPORTER_ENTRYPOINT_TEST", "unchanged value")
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid")
    environment = dict(os.environ)
    streams = (sys.stdin, sys.stdout, sys.stderr)
    target = Mock()
    with patch.object(importer_cli, "MongoClient", return_value=target) as connect:
        with patch.object(importer_cli, "run") as run:
            importer_cli.main(arguments)

    connect.assert_called_once_with("mongodb://example.invalid")
    run.assert_called_once()
    parsed, database = run.call_args.args
    assert parsed.subcommand == "import"
    assert parsed.fragments == arguments[1:]
    assert database == target.get_database.return_value
    target.get_database.assert_called_once_with(parsed.database)
    assert Path.cwd() == tmp_path
    assert dict(os.environ) == environment
    assert (sys.stdin, sys.stdout, sys.stderr) == streams


def test_importing_helpers_does_not_delegate() -> None:
    original_load_data = importer.load_data
    with patch.object(importer_cli, "main") as main:
        namespace = runpy.run_path(str(importer.__file__), run_name="__main__")

    main.assert_not_called()
    assert namespace["load_data"]([]) == {}
    assert importer.load_data is original_load_data
    assert importer.load_data([]) == {}
