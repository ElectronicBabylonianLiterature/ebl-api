from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from threading import Barrier

import pytest

from ebl.fragmentarium.application.map_artifact_storage import (
    artifact_manifest_name,
    publish_artifact_set,
    read_validated_artifact,
)


PREFIX = "assur"
INVENTORY = "assur_polygon_inventory.json"
MAPPINGS = "assur_findspot_polygon_mappings.json"


def _contents(marker: str) -> dict[str, str]:
    return {
        INVENTORY: json.dumps({"marker": marker, "kind": "inventory"}),
        MAPPINGS: json.dumps({"marker": marker, "kind": "mappings"}),
    }


def test_publish_artifact_set_writes_validated_complete_set(tmp_path):
    publish_artifact_set(tmp_path, PREFIX, "revision-1", _contents("one"))

    assert json.loads(read_validated_artifact(tmp_path, PREFIX, INVENTORY)) == {
        "marker": "one",
        "kind": "inventory",
    }
    assert json.loads(read_validated_artifact(tmp_path, PREFIX, MAPPINGS)) == {
        "marker": "one",
        "kind": "mappings",
    }
    manifest = json.loads(
        (tmp_path / artifact_manifest_name(PREFIX)).read_text(encoding="utf-8")
    )
    assert manifest["schemaVersion"] == 1
    assert manifest["sourceRevision"] == "revision-1"
    assert set(manifest["files"]) == {INVENTORY, MAPPINGS}
    assert not [path for path in tmp_path.iterdir() if path.name.startswith(".assur-")]


def test_read_validated_artifact_rejects_checksum_mismatch(tmp_path):
    publish_artifact_set(tmp_path, PREFIX, "revision-1", _contents("one"))
    (tmp_path / INVENTORY).write_text('{"marker": "tampered"}', encoding="utf-8")

    with pytest.raises(ValueError, match=f"checksum mismatch for {INVENTORY}"):
        read_validated_artifact(tmp_path, PREFIX, INVENTORY)


def test_read_validated_artifact_rejects_invalid_manifest(tmp_path):
    publish_artifact_set(tmp_path, PREFIX, "revision-1", _contents("one"))
    manifest_path = tmp_path / artifact_manifest_name(PREFIX)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schemaVersion"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported map artifact manifest"):
        read_validated_artifact(tmp_path, PREFIX, INVENTORY)


@pytest.mark.parametrize("content", ['{"key": 1, "key": 2}', '{"key": NaN}'])
def test_publish_artifact_set_rejects_ambiguous_json(tmp_path, content):
    with pytest.raises(ValueError, match="Duplicate JSON key|Non-finite JSON value"):
        publish_artifact_set(tmp_path, PREFIX, "revision-1", {INVENTORY: content})


def test_publish_artifact_set_rolls_back_complete_set_on_replace_failure(
    tmp_path, monkeypatch
):
    original_contents = _contents("old")
    publish_artifact_set(tmp_path, PREFIX, "revision-old", original_contents)
    original_replace = os.replace
    failure_injected = False

    def fail_second_artifact_once(source, destination):
        nonlocal failure_injected
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not failure_injected
            and source_path.parent != tmp_path
            and destination_path == tmp_path / MAPPINGS
        ):
            failure_injected = True
            raise OSError("injected replace failure")
        original_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_artifact_once)

    with pytest.raises(OSError, match="injected replace failure"):
        publish_artifact_set(tmp_path, PREFIX, "revision-new", _contents("new"))

    assert (
        read_validated_artifact(tmp_path, PREFIX, INVENTORY)
        == original_contents[INVENTORY]
    )
    assert (
        read_validated_artifact(tmp_path, PREFIX, MAPPINGS)
        == original_contents[MAPPINGS]
    )
    manifest = json.loads(
        (tmp_path / artifact_manifest_name(PREFIX)).read_text(encoding="utf-8")
    )
    assert manifest["sourceRevision"] == "revision-old"
    assert not [path for path in tmp_path.iterdir() if path.name.startswith(".assur-")]


def test_concurrent_publishers_leave_one_complete_validated_revision(tmp_path):
    barrier = Barrier(2)

    def publish(revision: str) -> None:
        barrier.wait()
        publish_artifact_set(tmp_path, PREFIX, revision, _contents(revision))

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(publish, revision) for revision in ("one", "two")]
        for future in futures:
            future.result()

    manifest = json.loads(
        (tmp_path / artifact_manifest_name(PREFIX)).read_text(encoding="utf-8")
    )
    revision = manifest["sourceRevision"]
    assert revision in {"one", "two"}
    assert (
        json.loads(read_validated_artifact(tmp_path, PREFIX, INVENTORY))["marker"]
        == revision
    )
    assert (
        json.loads(read_validated_artifact(tmp_path, PREFIX, MAPPINGS))["marker"]
        == revision
    )
