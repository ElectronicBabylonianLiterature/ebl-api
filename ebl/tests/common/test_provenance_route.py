import falcon

from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord
from ebl.common.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)
from ebl.errors import NotFoundError


def clear_provenances(repository: MongoProvenanceRepository) -> None:
    if repository._collection.count_documents({}) > 0:
        try:
            repository._collection.delete_many({"_id": {"$exists": True}})
        except NotFoundError:
            pass


def test_get_provenances(
    client, provenance_repository: MongoProvenanceRepository
):
    clear_provenances(provenance_repository)
    record1 = ProvenanceRecord(
        id="TEST_BABYLON", long_name="Test Babylon", abbreviation="Bab"
    )
    record2 = ProvenanceRecord(
        id="TEST_NINEVEH", long_name="Test Nineveh", abbreviation="Nin"
    )

    provenance_repository.create(record1)
    provenance_repository.create(record2)

    result = client.simulate_get("/provenances")

    assert result.status == falcon.HTTP_OK
    ids = {item["id"] for item in result.json}
    assert {"TEST_BABYLON", "TEST_NINEVEH"}.issubset(ids)


def test_get_provenance_by_id(
    client, provenance_repository: MongoProvenanceRepository
):
    clear_provenances(provenance_repository)
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    record = ProvenanceRecord(
        id="TEST_BABYLON",
        long_name="Test Babylon",
        abbreviation="Bab",
        coordinates=coord,
    )
    provenance_repository.create(record)

    result = client.simulate_get("/provenances/TEST_BABYLON")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == "TEST_BABYLON"
    assert result.json["longName"] == "Test Babylon"
    assert result.json["coordinates"]["latitude"] == 32.5


def test_get_provenance_not_found(client):
    result = client.simulate_get("/provenances/NONEXISTENT")
    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_provenance_children(
    client, provenance_repository: MongoProvenanceRepository
):
    clear_provenances(provenance_repository)
    parent = ProvenanceRecord(
        id="TEST_PARENT", long_name="Test Parent", abbreviation="Tpa"
    )
    child1 = ProvenanceRecord(
        id="TEST_CHILD_1",
        long_name="Test Child 1",
        abbreviation="Tc1",
        parent="TEST_PARENT",
    )
    child2 = ProvenanceRecord(
        id="TEST_CHILD_2",
        long_name="Test Child 2",
        abbreviation="Tc2",
        parent="TEST_PARENT",
    )

    provenance_repository.create(parent)
    provenance_repository.create(child1)
    provenance_repository.create(child2)

    result = client.simulate_get("/provenances/TEST_PARENT/children")

    assert result.status == falcon.HTTP_OK
    ids = {item["id"] for item in result.json}
    assert ids == {"TEST_CHILD_1", "TEST_CHILD_2"}


def test_update_provenance(
    client, provenance_repository: MongoProvenanceRepository, user
):
    clear_provenances(provenance_repository)
    record = ProvenanceRecord(
        id="TEST_BABYLON",
        long_name="Test Babylon",
        abbreviation="Bab",
    )
    provenance_repository.create(record)

    update_data = {
        "longName": "Babylon Updated",
        "abbreviation": "BabU",
        "coordinates": {
            "latitude": 32.5,
            "longitude": 44.4,
        },
    }

    result = client.simulate_put("/provenances/TEST_BABYLON", json=update_data)

    assert result.status == falcon.HTTP_OK
    assert result.json["longName"] == "Babylon Updated"

    updated = provenance_repository.query_by_id("TEST_BABYLON")
    assert updated.long_name == "Babylon Updated"
    assert updated.coordinates is not None
    assert updated.coordinates.latitude == 32.5
