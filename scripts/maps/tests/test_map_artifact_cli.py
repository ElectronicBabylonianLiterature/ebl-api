import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import sys

import pytest

from scripts.maps.map_artifact_cli import main


def test_packaged_generator_cli_publishes_versioned_report(
    tmp_path: Path,
) -> None:
    output = StringIO()
    with redirect_stdout(output):
        result = main(
            [
                "--site",
                "ASSUR",
                "--source-revision",
                "cli-revision",
                "--output-dir",
                str(tmp_path),
            ]
        )

    assert result == 0
    assert "Mappings: 315" in output.getvalue()
    report = json.loads(
        (tmp_path / "assur_findspot_polygon_curation_report.json").read_text()
    )
    assert report["schemaVersion"] == 1
    assert report["counts"]["verifiedMappings"] == 315
    assert not list(tmp_path.glob("*.md"))


def test_generator_cli_reports_invalid_input_without_a_traceback(
    tmp_path: Path,
) -> None:
    output, error = StringIO(), StringIO()
    with redirect_stdout(output), redirect_stderr(error):
        result = main(
            [
                "--site",
                "ASSUR",
                "--source-revision",
                "revision-1",
                "--output-dir",
                str(tmp_path),
                "--curated",
                str(tmp_path / "assur_findspot_polygon_mappings.json"),
            ]
        )

    assert result == 2
    assert error.getvalue().startswith("error: Reviewed curation input must not alias")
    assert "Traceback" not in error.getvalue()
    assert output.getvalue() == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "module_name",
    [
        "scripts.maps.map_artifact_cli",
        "scripts.maps.generate_findspot_map_artifacts",
    ],
)
def test_generator_modules_execute_main_guard(
    module_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = [
        module_name,
        "--source-revision",
        "cli-revision",
        "--output-dir",
        str(tmp_path),
    ]
    arguments.extend(["--site", "ASSUR"])
    monkeypatch.setattr(sys, "argv", arguments)

    with pytest.raises(SystemExit) as result:
        runpy.run_module(module_name, run_name="__main__")

    assert result.value.code == 0
    assert (tmp_path / "assur_artifact_manifest.json").is_file()
