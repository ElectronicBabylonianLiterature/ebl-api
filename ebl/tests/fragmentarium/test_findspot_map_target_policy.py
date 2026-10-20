from unittest.mock import MagicMock

import pytest

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.findspot_map_location_target import (
    ExpectedFingerprint,
    MappingInputs,
    fingerprint_database,
    is_local_mongo_uri,
    is_protected_target,
    validate_approved_development_target,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.tests.fragmentarium.map_import_test_helpers import location


def target_database(current: str | None = None) -> MagicMock:
    database = MagicMock()
    database.name = "ebldev"
    provenance = MagicMock()
    provenance.find_one.return_value = {"longName": "Assur"}
    findspots = MagicMock()
    document: dict[str, object] = {"_id": 1, "site": "Assur"}
    if current:
        document["mapLocation"] = MapLocationSchema().dump(location(current))
    findspots.find.return_value = [document]
    findspots.count_documents.side_effect = [3, 3, int(current is not None), 0]
    database.__getitem__.side_effect = {
        "provenances": provenance,
        "findspots": findspots,
    }.__getitem__
    return database


def mapping_inputs(previous: bool = False) -> MappingInputs:
    return MappingInputs(
        (MapLocationImportRecord(1, location("new")),),
        {"new"},
        (MapLocationImportRecord(1, location("old")),) if previous else (),
    )


@pytest.mark.parametrize(
    "current,previous,approved",
    [
        (None, False, True),
        ("new", False, True),
        ("old", True, True),
        ("other", False, False),
    ],
)
def test_dataset_fingerprint_requires_matching_locations(
    current: str | None, previous: bool, approved: bool
) -> None:
    fingerprint = fingerprint_database(
        target_database(current), mapping_inputs(previous), ExpectedFingerprint(3, 3)
    )
    assert fingerprint.is_approved_development is approved
    assert fingerprint.unresolved_assur_findspots == 2


def test_valid_target_validation_is_read_only() -> None:
    database = target_database()
    fingerprint = validate_approved_development_target(
        "mongodb://dev.example/ebldev",
        database,
        "ebldev",
        mapping_inputs(),
        ExpectedFingerprint(3, 3, 2),
    )
    assert fingerprint.is_approved_development
    database["findspots"].update_one.assert_not_called()


@pytest.mark.parametrize(
    "reason", ["confirmation", "database", "protected", "fingerprint"]
)
def test_invalid_target_rejected(reason: str) -> None:
    database = target_database()
    if reason == "database":
        database.name = "other"
    with pytest.raises(ValueError):
        validate_approved_development_target(
            "mongodb://production.example/ebldev"
            if reason == "protected"
            else "mongodb://dev.example/ebldev",
            database,
            None if reason == "confirmation" else "ebldev",
            mapping_inputs(),
        )


def test_missing_provenance_cannot_be_approved() -> None:
    database = target_database()
    database["provenances"].find_one.return_value = None
    database["findspots"].count_documents.side_effect = [3, 0, 0]
    fingerprint = fingerprint_database(database, mapping_inputs())
    assert not fingerprint.assur_provenance_exists
    assert not fingerprint.is_approved_development


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("mongodb://localhost:27017", True),
        ("mongodb://127.0.0.1,[::1]:27017", True),
        ("mongodb://localhost,remote.example", False),
        ("mongodb://[2001:db8::1]:27017", False),
        ("mongodb://", False),
    ],
)
def test_local_target_host_policy(uri: str, expected: bool) -> None:
    assert is_local_mongo_uri(uri) is expected


def test_protected_replica_host_is_rejected() -> None:
    assert is_protected_target(
        "mongodb://dev.example,production.example/ebldev", "ebldev"
    )
    assert not is_protected_target(
        "mongodb://production:password@localhost/ebldev", "ebldev"
    )
