import json

import pytest

from ebl.fragmentarium.application.findspot_map_location_importer import (
    ImportPaths,
    load_import_records,
    load_polygon_inventory,
    run_import,
)
from ebl.fragmentarium.application.findspot_map_location_target import (
    ExpectedFingerprint,
    MappingInputs,
    fingerprint_database,
    is_protected_target,
    validate_approved_development_target,
)
from ebl.transliteration.infrastructure.collections import FINDSPOTS_COLLECTION
from scripts.maps import import_findspot_map_locations as cli


POLYGON_ID = "assur-test-1"
SOURCE = "Assur Tafeln.ods"
REVISION = "2026-07-27"


def _mapping(findspot_id: int) -> dict:
    return {
        "findspotId": findspot_id,
        "polygonIds": [POLYGON_ID],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": SOURCE,
        "sourceRevision": REVISION,
    }


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_target(database, map_location=None, extra_site=False) -> None:
    database["provenances"].insert_one(
        {"_id": "ASSUR", "longName": "Aššur", "abbreviation": "Ass"}
    )
    first_findspot = {"_id": 1, "site": "Aššur"}
    if map_location is not None:
        first_findspot["mapLocation"] = map_location
    database[FINDSPOTS_COLLECTION].insert_many(
        [
            first_findspot,
            {"_id": 2, "site": "Aššur"},
            {"_id": 3, "site": "Nineveh"}
            if extra_site
            else {"_id": 3, "site": "Aššur"},
        ]
    )


def _records(tmp_path):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, [_mapping(1), _mapping(2)])
    _write_json(inventory, [{"polygonId": POLYGON_ID}])
    polygon_ids = load_polygon_inventory(inventory)
    records, issues, _ = load_import_records(mappings, polygon_ids)
    assert issues == ()
    return records, polygon_ids


def test_remote_targets_remain_rejected_by_default(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid/ebldev")
    monkeypatch.setenv("MONGODB_DB", "ebldev")

    assert cli.main(["--dry-run"]) == 2


def test_approved_development_requires_database_confirmation(tmp_path, database):
    _seed_target(database)
    records, polygon_ids = _records(tmp_path)

    with pytest.raises(ValueError):
        validate_approved_development_target(
            "mongodb://dev.example/ebldev",
            database,
            None,
            MappingInputs(records, polygon_ids),
            ExpectedFingerprint(total_findspots=3, assur_findspots=3, unresolved=1),
        )


def test_wrong_database_name_is_rejected(tmp_path, database):
    _seed_target(database)
    records, polygon_ids = _records(tmp_path)

    with pytest.raises(ValueError):
        validate_approved_development_target(
            "mongodb://dev.example/ebldev",
            database,
            "ebldev",
            MappingInputs(records, polygon_ids),
            ExpectedFingerprint(total_findspots=3, assur_findspots=3, unresolved=1),
        )


def test_wrong_dataset_fingerprint_is_rejected(tmp_path, database):
    _seed_target(database, extra_site=True)
    records, polygon_ids = _records(tmp_path)

    with pytest.raises(ValueError):
        validate_approved_development_target(
            "mongodb://dev.example/ebldev",
            database.client["ebldev"],
            "ebldev",
            MappingInputs(records, polygon_ids),
            ExpectedFingerprint(total_findspots=3, assur_findspots=3, unresolved=1),
        )


def test_production_and_staging_like_targets_are_rejected():
    assert is_protected_target("mongodb://prod.example/ebldev", "ebldev")
    assert is_protected_target("mongodb://dev.example/staging", "ebldev")


def test_valid_development_fingerprint_passes_dry_run(tmp_path, database):
    _seed_target(database)
    records, polygon_ids = _records(tmp_path)

    fingerprint = fingerprint_database(
        database,
        MappingInputs(records, polygon_ids),
        ExpectedFingerprint(total_findspots=3, assur_findspots=3, unresolved=1),
    )
    summary = run_import(
        database,
        ImportPaths(tmp_path / "mappings.json", tmp_path / "inventory.json"),
    )

    assert fingerprint.is_approved_development
    assert summary.dry_run is True
    assert summary.applied == 0
    assert (
        database[FINDSPOTS_COLLECTION].count_documents(
            {"mapLocation": {"$exists": True}}
        )
        == 0
    )
