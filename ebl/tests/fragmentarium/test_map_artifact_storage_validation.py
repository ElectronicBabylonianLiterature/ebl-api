import json
import os
from pathlib import Path
from typing import cast

import pytest

from ebl.fragmentarium.application import map_artifact_storage as storage


PREFIX = "assur"
FILENAME = "assur_polygon_inventory.json"
OTHER_FILENAME = "assur_findspot_polygon_mappings.json"


def _publish(directory: Path) -> dict[str, bytes]:
    storage.publish_artifact_set(
        directory, PREFIX, "revision-1", {FILENAME: "[]", OTHER_FILENAME: "[]"}
    )
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def _write_manifest(directory: Path, payload: object) -> None:
    (directory / storage.artifact_manifest_name(PREFIX)).write_text(
        json.dumps(payload), encoding="utf-8"
    )


@pytest.mark.parametrize("missing_directory", [False, True])
def test_read_requires_a_published_artifact_directory(
    tmp_path: Path, missing_directory: bool
) -> None:
    directory = tmp_path / "missing" if missing_directory else tmp_path

    with pytest.raises(FileNotFoundError, match="does not exist"):
        storage.read_validated_artifact(directory, PREFIX, FILENAME)


def test_read_rejects_a_file_not_declared_by_the_manifest(tmp_path: Path) -> None:
    _publish(tmp_path)
    (tmp_path / "extra.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="does not declare extra.json"):
        storage.read_validated_artifact(tmp_path, PREFIX, "extra.json")


def test_read_rejects_a_missing_declared_file(tmp_path: Path) -> None:
    _publish(tmp_path)
    (tmp_path / OTHER_FILENAME).unlink()

    with pytest.raises(FileNotFoundError, match="Declared map artifact"):
        storage.read_validated_artifact(tmp_path, PREFIX, FILENAME)


@pytest.mark.parametrize("payload", [None, [], 1, "manifest"])
def test_read_rejects_a_nonobject_manifest(tmp_path: Path, payload: object) -> None:
    _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="must be a JSON object"):
        storage.read_validated_artifact(tmp_path, PREFIX, FILENAME)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"schemaVersion": True}, "schemaVersion"),
        ({"schemaVersion": "1"}, "schemaVersion"),
        ({"schemaVersion": None}, "schemaVersion"),
        ({"sourceRevision": None}, "sourceRevision"),
        ({"sourceRevision": " \t"}, "sourceRevision"),
        ({"files": None}, "nonempty object"),
        ({"files": []}, "nonempty object"),
        ({"files": {}}, "nonempty object"),
        ({"files": {FILENAME: 1}}, "checksum.*must be a string"),
    ],
)
def test_read_rejects_invalid_manifest_fields(
    tmp_path: Path, change: dict[str, object], message: str
) -> None:
    original = _publish(tmp_path)
    manifest = json.loads(original[storage.artifact_manifest_name(PREFIX)])
    _write_manifest(tmp_path, {**manifest, **change})

    with pytest.raises(ValueError, match=message):
        storage.read_validated_artifact(tmp_path, PREFIX, FILENAME)


@pytest.mark.parametrize(
    "filename",
    ["../outside.json", "nested/file.json", "nested\\file.json", "", ".", ".."],
)
def test_read_rejects_unsafe_manifest_filenames(tmp_path: Path, filename: str) -> None:
    _write_manifest(
        tmp_path,
        {"schemaVersion": 1, "sourceRevision": "r1", "files": {filename: "hash"}},
    )

    with pytest.raises(ValueError, match="invalid filename"):
        storage.read_validated_artifact(tmp_path, PREFIX, FILENAME)


@pytest.mark.parametrize("contents", [{}, {"../escape.json": "[]"}, {"": "[]"}])
def test_publish_rejects_missing_or_unsafe_contents(
    tmp_path: Path, contents: dict[str, str]
) -> None:
    with pytest.raises(ValueError, match="at least one file|must be a basename"):
        storage.publish_artifact_set(tmp_path, PREFIX, "r1", contents)

    assert list(tmp_path.iterdir()) == []


def test_publish_rejects_a_nonstring_filename(tmp_path: Path) -> None:
    contents = cast(dict[str, str], {1: "[]"})

    with pytest.raises(ValueError, match="must be a basename"):
        storage.publish_artifact_set(tmp_path, PREFIX, "r1", contents)


@pytest.mark.parametrize(
    "prefix",
    ["../outside", "nested\\outside", "", ".", "..", "drive:outside", "null\x00"],
)
def test_publish_rejects_an_unsafe_manifest_prefix(tmp_path: Path, prefix: str) -> None:
    with pytest.raises(ValueError, match="prefix must be a basename"):
        storage.publish_artifact_set(tmp_path, prefix, "r1", {FILENAME: "[]"})

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("revision", ["", " \t"])
def test_publish_rejects_a_blank_revision(tmp_path: Path, revision: str) -> None:
    with pytest.raises(ValueError, match="sourceRevision must not be blank"):
        storage.publish_artifact_set(tmp_path, PREFIX, revision, {FILENAME: "[]"})


def test_publish_rejects_a_caller_supplied_manifest(tmp_path: Path) -> None:
    manifest_name = storage.artifact_manifest_name(PREFIX)

    with pytest.raises(ValueError, match="must not provide their own manifest"):
        storage.publish_artifact_set(tmp_path, PREFIX, "r1", {manifest_name: "{}"})


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize(
    "failing_name", [OTHER_FILENAME, storage.artifact_manifest_name(PREFIX)]
)
def test_publish_rolls_back_new_and_existing_targets_including_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    existing: bool,
    failing_name: str,
) -> None:
    before = _publish(tmp_path) if existing else {}
    original_replace = os.replace
    failed = False

    def fail_once(
        source: str | os.PathLike[str], destination: str | os.PathLike[str]
    ) -> None:
        nonlocal failed
        if not failed and Path(destination).name == failing_name:
            failed = True
            raise OSError("publication failure")
        original_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_once)

    with pytest.raises(OSError, match="publication failure"):
        storage.publish_artifact_set(
            tmp_path, PREFIX, "r2", {FILENAME: "[1]", OTHER_FILENAME: "[2]"}
        )

    assert failed
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
