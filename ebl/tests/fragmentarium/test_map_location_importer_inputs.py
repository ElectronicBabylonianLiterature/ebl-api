import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from ebl.fragmentarium.application.findspot_map_location_importer import (
    ImportPaths,
    load_import_records,
    load_polygon_inventory,
    run_import,
)


@pytest.mark.parametrize(
    "value,message",
    [
        ({}, "Expected a JSON array"),
        ([None], "missing polygonId"),
        ([{}], "missing polygonId"),
        ([{"polygonId": 1}], "invalid polygonId"),
        ([{"polygonId": " "}], "invalid polygonId"),
    ],
)
def test_inventory_rejects_invalid_shapes(tmp_path: Path, value, message: str):
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_polygon_inventory(path)


def test_mapping_non_object_is_reported_as_invalid(tmp_path: Path):
    path = tmp_path / "mappings.json"
    path.write_text("[null]", encoding="utf-8")

    records, issues, scanned = load_import_records(path, set())

    assert records == ()
    assert scanned == 1
    assert len(issues) == 1
    assert issues[0].findspot_id is None
    assert "validation failed" in issues[0].reason


@pytest.mark.parametrize("missing_inventory", [False, True])
def test_invalid_previous_artifacts_fail_before_database_access(
    tmp_path: Path, missing_inventory: bool
):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    previous = tmp_path / "previous.json"
    mappings.write_text("[]", encoding="utf-8")
    inventory.write_text("[]", encoding="utf-8")
    previous.write_text("[null]", encoding="utf-8")
    database = Mock()
    paths = ImportPaths(
        mappings,
        inventory,
        previous,
        None if missing_inventory else inventory,
    )

    with pytest.raises(ValueError, match="previous"):
        run_import(database, paths, dry_run=False)

    assert database.mock_calls == []
