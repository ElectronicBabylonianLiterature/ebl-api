from copy import deepcopy
import json

import pytest

from ebl.fragmentarium.application.findspot_map_location_importer import (
    ImportPaths,
    run_import,
)
from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.findspot_map_location_importer_plan import (
    build_plan,
    write_operations,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory


def _location(polygon: str) -> MapLocation:
    return MapLocation(
        polygon_ids=(polygon,),
        location_precision=MapLocationPrecision.EXCAVATION_AREA,
        match_method=MapLocationMatchMethod.CURATED,
        source="$review fixture",
        source_revision="$1",
    )


def _stored_location(polygon: str) -> dict:
    document = MapLocationSchema().dump(_location(polygon))
    assert isinstance(document, dict)
    document["polygonIds"] = [f" {polygon} "]
    document["source"] = " $review fixture "
    document["sourceRevision"] = " $1 "
    return dict(reversed(tuple(document.items())))


def _concurrent_document(original: dict | None, change: str) -> dict:
    document: dict = {"_id": 1, "extraField": "preserved"}
    if original is not None:
        document["mapLocation"] = deepcopy(original)
    if change == "value":
        document["mapLocation"] = _stored_location("concurrent")
    elif change == "extra":
        document["mapLocation"] = {**(original or {}), "newField": "concurrent"}
    elif change == "null":
        document["mapLocation"] = None
    elif change == "scalar":
        document["mapLocation"] = "concurrent"
    elif change == "missing":
        document.pop("mapLocation", None)
    return document


@pytest.mark.parametrize("mode", ["new", "replace", "migrate", "rollback", "clear"])
@pytest.mark.parametrize(
    "change", ["unchanged", "value", "extra", "null", "scalar", "missing"]
)
def test_import_compares_complete_raw_snapshot(database, mode: str, change: str):
    rollback = mode in {"rollback", "clear"}
    original = None if mode == "new" else "new" if rollback else "old"
    raw = _stored_location(original) if original else None
    current = _location(original) if original else None
    findspot = FindspotFactory.build(id_=1, map_location=current)
    record = MapLocationImportRecord(1, _location("new"))
    previous = (
        (MapLocationImportRecord(1, _location("old")),)
        if mode in {"migrate", "rollback"}
        else ()
    )
    *_, operations = build_plan((record,), {1: findspot}, rollback, previous, {1: raw})
    document = _concurrent_document(raw, change)
    collection = database["findspots"]
    collection.insert_one(deepcopy(document))
    matches = change == "unchanged" or (mode == "new" and change in {"null", "missing"})

    assert write_operations(collection, operations) == int(matches)

    stored = collection.find_one({"_id": 1})
    assert stored is not None
    assert stored["extraField"] == "preserved"
    if not matches:
        assert stored == document
    elif mode == "clear":
        assert "mapLocation" not in stored
    else:
        expected = _location("old" if mode == "rollback" else "new")
        assert stored["mapLocation"] == MapLocationSchema().dump(expected)


def test_import_uses_raw_snapshot_from_database_read(
    tmp_path, database, findspot_repository, seeded_provenance_service
):
    findspot_repository.create(
        FindspotFactory.build(
            id_=1,
            site=seeded_provenance_service.find_by_id("ASSUR"),
            map_location=_location("old"),
        )
    )
    database["findspots"].update_one(
        {"_id": 1}, {"$set": {"mapLocation": _stored_location("old"), "extraField": 1}}
    )
    desired = MapLocationSchema().dump(_location("new"))
    assert isinstance(desired, dict)
    mappings = tmp_path / "mappings.json"
    inventory = tmp_path / "inventory.json"
    mappings.write_text(json.dumps([{"findspotId": 1, **desired}]), encoding="utf-8")
    inventory.write_text(json.dumps([{"polygonId": "new"}]), encoding="utf-8")

    result = run_import(database, ImportPaths(mappings, inventory), dry_run=False)

    assert result.applied == 1
    assert database["findspots"].find_one({"_id": 1})["mapLocation"] == desired
    assert database["findspots"].find_one({"_id": 1})["extraField"] == 1
