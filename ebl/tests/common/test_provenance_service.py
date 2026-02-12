from ebl.common.application.provenance_service import ProvenanceService
from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord
from ebl.common.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)
from ebl.errors import NotFoundError


def clear_provenances(provenance_repository: MongoProvenanceRepository) -> None:
    if provenance_repository._collection.count_documents({}) > 0:
        try:
            provenance_repository._collection.delete_many({"_id": {"$exists": True}})
        except NotFoundError:
            pass


def test_find_by_name_from_repository(provenance_repository):
    clear_provenances(provenance_repository)
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    record = ProvenanceRecord(
        id="TEST_BABYLON",
        long_name="Test Babylon",
        abbreviation="Bab",
        coordinates=coord,
    )
    provenance_repository.create(record)

    service = ProvenanceService(provenance_repository)
    result = service.find_by_name("Test Babylon")

    assert result is not None
    assert result.id == "TEST_BABYLON"
    assert result.long_name == "Test Babylon"
    assert result.coordinates is not None
    assert result.coordinates.latitude == 32.5


def test_find_by_name_not_found(provenance_repository):
    clear_provenances(provenance_repository)
    service = ProvenanceService(provenance_repository)
    result = service.find_by_name("Nonexistent")

    assert result is None


def test_find_all(provenance_repository):
    clear_provenances(provenance_repository)
    record1 = ProvenanceRecord(
        id="TEST_BABYLON", long_name="Test Babylon", abbreviation="Bab"
    )
    record2 = ProvenanceRecord(
        id="TEST_NINEVEH", long_name="Test Nineveh", abbreviation="Nin"
    )

    provenance_repository.create(record1)
    provenance_repository.create(record2)

    service = ProvenanceService(provenance_repository)
    result = service.find_all()

    assert len(result) == 2
    assert {r.id for r in result} == {"TEST_BABYLON", "TEST_NINEVEH"}


def test_find_all_caching(provenance_repository):
    clear_provenances(provenance_repository)
    record = ProvenanceRecord(
        id="TEST_BABYLON", long_name="Test Babylon", abbreviation="Bab"
    )
    provenance_repository.create(record)

    service = ProvenanceService(provenance_repository)
    result1 = service.find_all()
    result2 = service.find_all()

    assert result1 == result2


def test_update_clears_cache(provenance_repository):
    clear_provenances(provenance_repository)
    record = ProvenanceRecord(
        id="TEST_BABYLON",
        long_name="Test Babylon",
        abbreviation="Bab",
    )
    provenance_repository.create(record)

    service = ProvenanceService(provenance_repository)
    service.find_by_name("Test Babylon")

    updated_record = ProvenanceRecord(
        id="TEST_BABYLON",
        long_name="Test Babylon Updated",
        abbreviation="BabU",
    )
    service.update(updated_record)

    result = service.find_by_name("Test Babylon Updated")
    assert result is not None
    assert result.long_name == "Test Babylon Updated"
