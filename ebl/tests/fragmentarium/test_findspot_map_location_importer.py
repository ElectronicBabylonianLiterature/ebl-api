import attr
import json
import pytest

from ebl.fragmentarium.application import (
    findspot_map_location_importer as importer,
)
from ebl.fragmentarium.application.findspot_map_location_importer import run_import
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory

SOURCE = "Assur Tafeln.ods"
REVISION = "2026-07-27"
POLYGON_ID = "assur-test-1"
OTHER_POLYGON_ID = "assur-test-2"


def _inventory(*polygon_ids):
    return [{"polygonId": polygon_id, "name": polygon_id} for polygon_id in polygon_ids]


def _mapping(findspot_id, polygon_ids=(POLYGON_ID,), match_method="verified-source"):
    return [
        {
            "findspotId": findspot_id,
            "polygonIds": list(polygon_ids),
            "locationPrecision": "excavation-area",
            "matchMethod": match_method,
            "source": SOURCE,
            "sourceRevision": REVISION,
        }
    ]


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _map_location(*polygon_ids, match_method=MapLocationMatchMethod.VERIFIED_SOURCE):
    return MapLocation(
        polygon_ids=tuple(polygon_ids),
        location_precision=MapLocationPrecision.EXCAVATION_AREA,
        match_method=match_method,
        source=SOURCE,
        source_revision=REVISION,
    )


def _create_findspot(
    findspot_repository,
    provenance_service,
    findspot_id,
    site_id="ASSUR",
    map_location=None,
):
    site = provenance_service.find_by_id(site_id)
    findspot = attr.evolve(
        FindspotFactory.build(id_=findspot_id, site=site, map_location=map_location)
    )
    findspot_repository.create(findspot)
    return findspot


def test_run_import_defaults_to_dry_run(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, _mapping(1))
    _write_json(inventory, _inventory(POLYGON_ID))
    _create_findspot(findspot_repository, seeded_provenance_service, 1)

    summary = run_import(database, mappings, inventory)

    assert summary.dry_run is True
    assert summary.new == 1
    assert summary.applied == 0
    assert database["findspots"].find_one({"_id": 1}).get("mapLocation") is None


def test_run_import_applies_and_is_idempotent(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, _mapping(1))
    _write_json(inventory, _inventory(POLYGON_ID))
    _create_findspot(findspot_repository, seeded_provenance_service, 1)

    summary = run_import(database, mappings, inventory, dry_run=False)
    rerun = run_import(database, mappings, inventory)

    assert summary.new == 1
    assert summary.applied == 1
    assert database["findspots"].find_one({"_id": 1})["mapLocation"] == {
        "polygonIds": [POLYGON_ID],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": SOURCE,
        "sourceRevision": REVISION,
    }
    assert rerun.existing == 1
    assert rerun.new == rerun.changed == rerun.applied == 0


@pytest.mark.parametrize(
    "mappings, inventory",
    [
        (_mapping(404), _inventory(POLYGON_ID)),
        (_mapping(1, polygon_ids=(OTHER_POLYGON_ID,)), _inventory(POLYGON_ID)),
        (_mapping(1, polygon_ids=(POLYGON_ID, POLYGON_ID)), _inventory(POLYGON_ID)),
        (
            [
                {
                    "findspotId": 1,
                    "polygonIds": [POLYGON_ID],
                    "locationPrecision": "invalid",
                    "matchMethod": "verified-source",
                    "source": SOURCE,
                    "sourceRevision": REVISION,
                }
            ],
            _inventory(POLYGON_ID),
        ),
        (
            [
                {
                    "findspotId": 1,
                    "polygonIds": [POLYGON_ID],
                    "locationPrecision": "excavation-area",
                    "matchMethod": "not-a-method",
                    "source": SOURCE,
                    "sourceRevision": REVISION,
                }
            ],
            _inventory(POLYGON_ID),
        ),
    ],
)
def test_run_import_invalid_rows_prevent_writes(
    tmp_path,
    database,
    findspot_repository,
    seeded_provenance_service,
    monkeypatch,
    mappings,
    inventory,
):
    mappings_path = tmp_path / "mappings.json"
    inventory_path = tmp_path / "inventory.json"
    _write_json(mappings_path, mappings)
    _write_json(inventory_path, inventory)
    _create_findspot(findspot_repository, seeded_provenance_service, 1)
    calls = {"write": 0}

    def wrapped(*args, **kwargs):
        calls["write"] += 1
        raise AssertionError("write helper should not be called for invalid input")

    monkeypatch.setattr(
        importer,
        "_write_operations",
        wrapped,
    )

    summary = run_import(database, mappings_path, inventory_path, dry_run=False)

    assert summary.invalid == 1
    assert summary.applied == 0
    assert calls["write"] == 0


def test_run_import_duplicate_records_are_invalid(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, _mapping(1) + _mapping(1))
    _write_json(inventory, _inventory(POLYGON_ID))
    _create_findspot(findspot_repository, seeded_provenance_service, 1)

    summary = run_import(database, mappings, inventory)

    assert summary.invalid == 1
    assert summary.applied == 0


def test_run_import_empty_file_is_noop(tmp_path, database):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, [])
    _write_json(inventory, _inventory(POLYGON_ID))

    summary = run_import(database, mappings, inventory)

    assert summary.scanned == 0
    assert summary.valid == summary.invalid == summary.applied == 0


def test_run_import_preserves_unrelated_fields_and_blocks_partial_updates(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(mappings, _mapping(1) + _mapping(2))
    _write_json(inventory, _inventory(POLYGON_ID))
    _create_findspot(findspot_repository, seeded_provenance_service, 1)
    _create_findspot(
        findspot_repository, seeded_provenance_service, 2, site_id="NINEVEH"
    )
    database["findspots"].update_one({"_id": 1}, {"$set": {"extraField": "keep"}})

    summary = run_import(database, mappings, inventory, dry_run=False)

    assert summary.invalid == 1
    assert summary.applied == 0
    assert database["findspots"].find_one({"_id": 1})["extraField"] == "keep"
    assert database["findspots"].find_one({"_id": 1}).get("mapLocation") is None
    assert database["findspots"].find_one({"_id": 2}).get("mapLocation") is None
