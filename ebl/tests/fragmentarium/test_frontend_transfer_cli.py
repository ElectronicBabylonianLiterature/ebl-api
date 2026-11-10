import pytest
from pathlib import Path
import runpy
import sys

from scripts.maps import build_frontend_transfer_archive as cli
from scripts.maps import frontend_transfer_archive as transfer
from scripts.maps.map_artifact_generator import DEFAULT_OUTPUT_DIR


def test_default_output_is_outside_repo_and_repeatable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli.tempfile, "gettempdir", lambda: str(tmp_path))

    def fake_git(*args: str) -> str:
        return "# branch.oid " + "a" * 40 + "\0"

    monkeypatch.setattr(transfer, "_git", fake_git)
    output = Path(tmp_path) / "map-multi-site-canonical-artifacts.tar.gz"

    assert cli._parse_args([]).output == output
    assert cli.main([]) == 0
    first = output.read_bytes()
    assert cli.main([]) == 0
    assert output.read_bytes() == first


def test_module_main_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "main-guard.tar.gz"
    monkeypatch.setattr(
        transfer, "_git", lambda *args: "# branch.oid " + "a" * 40 + "\0"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_frontend_transfer_archive",
            "--data-dir",
            str(DEFAULT_OUTPUT_DIR),
            "--output",
            str(output),
        ],
    )
    monkeypatch.delitem(sys.modules, "scripts.maps.build_frontend_transfer_archive")
    with pytest.raises(SystemExit) as result:
        runpy.run_module(
            "scripts.maps.build_frontend_transfer_archive", run_name="__main__"
        )
    assert result.value.code == 0
    assert output.is_file()
