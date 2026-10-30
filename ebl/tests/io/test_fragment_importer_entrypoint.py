import importlib
import os
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

import pytest

from ebl.io.fragments import importer

LEGACY_MODULE = "ebl.io.fragments.importer"
CANONICAL_MODULE = "ebl.io.fragments.importer_cli"


def _run_cli(module: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


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
def test_legacy_module_matches_canonical_cli(
    arguments: list[str], expected_status: int
) -> None:
    canonical = _run_cli(CANONICAL_MODULE, arguments)
    legacy = _run_cli(LEGACY_MODULE, arguments)

    assert canonical.returncode == expected_status
    assert canonical.stdout or canonical.stderr
    assert (legacy.returncode, legacy.stdout, legacy.stderr) == (
        canonical.returncode,
        canonical.stdout,
        canonical.stderr,
    )


def test_legacy_module_preserves_process_context_and_arguments(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    arguments = ["import", "file name.json", "", "literal;$HOME", "line\nbreak"]
    monkeypatch.setattr(sys, "argv", [LEGACY_MODULE, *arguments])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IMPORTER_ENTRYPOINT_TEST", "unchanged value")
    environment = dict(os.environ)
    streams = (sys.stdin, sys.stdout, sys.stderr)

    with patch.object(os, "execv", side_effect=OSError("exec boundary")) as execute:
        with pytest.raises(OSError, match="exec boundary"):
            runpy.run_path(str(importer.__file__), run_name="__main__")

    execute.assert_called_once_with(
        sys.executable, [sys.executable, "-m", CANONICAL_MODULE, *arguments]
    )
    assert Path.cwd() == tmp_path
    assert dict(os.environ) == environment
    assert (sys.stdin, sys.stdout, sys.stderr) == streams


def test_importing_helpers_does_not_delegate() -> None:
    with patch.object(os, "execv") as execute:
        importlib.reload(importer)

    execute.assert_not_called()
    assert importer.load_data([]) == {}
