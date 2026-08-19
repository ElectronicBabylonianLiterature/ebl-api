import attr
import json

from ebl.fragmentarium.application.findspot_map_location_importer import (
    ImportPaths,
    run_import,
)
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory


SOURCE = "Assur Tafeln.ods"
REVISION = "2026-07-27"
OLD_POLYGON = "assur-old"
NEW_POLYGON = "assur-new"
ADDED_POLYGON = "assur-added"


def _location(polygon_id):
    return MapLocation(
        polygon_ids=(polygon_id,),
        location_precision=MapLocationPrecision.EXCAVATION_AREA,
        match_method=MapLocationMatchMethod.VERIFIED_SOURCE,
        source=SOURCE,
        source_revision=REVISION,
    )


def _record(findspot_id, polygon_id):
    return {
        "findspotId": findspot_id,
        "polygonIds": [polygon_id],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": SOURCE,
        "sourceRevision": REVISION,
    }


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_findspot(repository, provenance_service, findspot_id, map_location=None):
    site = provenance_service.find_by_id("ASSUR")
    repository.create(
        attr.evolve(
            FindspotFactory.build(id_=findspot_id, site=site, map_location=map_location)
        )
    )


def _write_artifacts(tmp_path):
    previous_mappings = tmp_path / "previous-mappings.json"
    previous_inventory = tmp_path / "previous-inventory.json"
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    _write_json(previous_inventory, [{"polygonId": OLD_POLYGON}])
    _write_json(inventory, [{"polygonId": NEW_POLYGON}, {"polygonId": ADDED_POLYGON}])
    _write_json(previous_mappings, [_record(1, OLD_POLYGON), _record(2, OLD_POLYGON)])
    _write_json(
        mappings,
        [
            _record(1, NEW_POLYGON),
            _record(2, NEW_POLYGON),
            _record(3, ADDED_POLYGON),
        ],
    )
    return ImportPaths(mappings, inventory, previous_mappings, previous_inventory)


def test_exact_migration_replaces_inserts_idempotently_and_rolls_back(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    paths = _write_artifacts(tmp_path)
    _create_findspot(
        findspot_repository, seeded_provenance_service, 1, _location(OLD_POLYGON)
    )
    _create_findspot(
        findspot_repository, seeded_provenance_service, 2, _location(OLD_POLYGON)
    )
    _create_findspot(findspot_repository, seeded_provenance_service, 3)

    dry_run = run_import(database, paths, dry_run=True)
    applied = run_import(database, paths, dry_run=False)
    idempotent = run_import(database, paths, dry_run=True)
    rollback = run_import(database, paths, dry_run=False, rollback=True)

    assert (dry_run.changed, dry_run.new, dry_run.applied) == (2, 1, 0)
    assert applied.applied == 3
    assert (idempotent.existing, idempotent.changed, idempotent.new) == (3, 0, 0)
    assert rollback.applied == 3
    assert database["findspots"].find_one({"_id": 1})["mapLocation"]["polygonIds"] == [
        OLD_POLYGON
    ]
    assert "mapLocation" not in database["findspots"].find_one({"_id": 3})


def test_exact_migration_blocks_unexpected_current_value(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    paths = _write_artifacts(tmp_path)
    _create_findspot(
        findspot_repository, seeded_provenance_service, 1, _location("other")
    )
    _create_findspot(
        findspot_repository, seeded_provenance_service, 2, _location(OLD_POLYGON)
    )
    _create_findspot(findspot_repository, seeded_provenance_service, 3)

    summary = run_import(database, paths, dry_run=False)

    assert summary.invalid == 1
    assert summary.applied == 0
    assert database["findspots"].find_one({"_id": 2})["mapLocation"]["polygonIds"] == [
        OLD_POLYGON
    ]
