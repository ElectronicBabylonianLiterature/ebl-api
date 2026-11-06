import json
from pathlib import Path
import runpy
import sys

import pytest

from ebl.fragmentarium.application.map_artifact_cli import main
from scripts.maps.generate_assur_map_artifacts import main as generate_assur


def test_packaged_generator_cli_publishes_versioned_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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
    assert "Mappings: 315" in capsys.readouterr().out
    report = json.loads(
        (tmp_path / "assur_findspot_polygon_curation_report.json").read_text()
    )
    assert report["schemaVersion"] == 1
    assert report["counts"]["verifiedMappings"] == 315
    assert not list(tmp_path.glob("*.md"))


def test_assur_compatibility_cli_accepts_explicit_arguments(tmp_path: Path) -> None:
    assert (
        generate_assur(
            ["--source-revision", "cli-revision", "--output-dir", str(tmp_path)]
        )
        == 0
    )


@pytest.mark.parametrize(
    "module_name",
    [
        "ebl.fragmentarium.application.map_artifact_cli",
        "scripts.maps.generate_findspot_map_artifacts",
        "scripts.maps.generate_assur_map_artifacts",
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
    if module_name != "scripts.maps.generate_assur_map_artifacts":
        arguments.extend(["--site", "ASSUR"])
    monkeypatch.setattr(sys, "argv", arguments)

    with pytest.raises(SystemExit) as result:
        runpy.run_module(module_name, run_name="__main__")

    assert result.value.code == 0
    assert (tmp_path / "assur_artifact_manifest.json").is_file()
