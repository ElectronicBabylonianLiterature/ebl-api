import pytest

from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord
from ebl.common.application.provenance_repository import ProvenanceRepository
from ebl.errors import NotFoundError


def test_create_provenance(provenance_repository: ProvenanceRepository):
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
        parent="BABYLONIA",
        cigs_key="BAB",
    )
    result_id = provenance_repository.create(record)
    assert result_id == "BABYLON"


def test_find_all(provenance_repository: ProvenanceRepository):
    record1 = ProvenanceRecord(id="BABYLON", long_name="Babylon", abbreviation="Bab")
    record2 = ProvenanceRecord(id="NINEVEH", long_name="Nineveh", abbreviation="Nin")
    record3 = ProvenanceRecord(id="URUK", long_name="Uruk", abbreviation="Urk")

    provenance_repository.create(record1)
    provenance_repository.create(record2)
    provenance_repository.create(record3)

    result = provenance_repository.find_all()
    assert len(result) == 3
    assert {r.id for r in result} == {"BABYLON", "NINEVEH", "URUK"}


def test_query_by_id(provenance_repository: ProvenanceRepository):
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
        coordinates=coord,
    )
    provenance_repository.create(record)

    result = provenance_repository.query_by_id("BABYLON")
    assert result.id == "BABYLON"
    assert result.long_name == "Babylon"
    assert result.coordinates is not None
    assert result.coordinates.latitude == 32.5


def test_query_by_id_not_found(provenance_repository: ProvenanceRepository):
    with pytest.raises(NotFoundError):
        provenance_repository.query_by_id("NONEXISTENT")


def test_update(provenance_repository: ProvenanceRepository):
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
    )
    provenance_repository.create(record)

    updated_record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon Updated",
        abbreviation="BabU",
        coordinates=GeoCoordinate(latitude=32.5, longitude=44.4),
    )
    provenance_repository.update(updated_record)

    result = provenance_repository.query_by_id("BABYLON")
    assert result.long_name == "Babylon Updated"
    assert result.abbreviation == "BabU"
    assert result.coordinates is not None
    assert result.coordinates.latitude == 32.5


def test_find_children(provenance_repository: ProvenanceRepository):
    parent = ProvenanceRecord(
        id="BABYLONIA", long_name="Babylonia", abbreviation="Baba"
    )
    child1 = ProvenanceRecord(
        id="BABYLON", long_name="Babylon", abbreviation="Bab", parent="BABYLONIA"
    )
    child2 = ProvenanceRecord(
        id="URUK", long_name="Uruk", abbreviation="Urk", parent="BABYLONIA"
    )
    child3 = ProvenanceRecord(
        id="NINEVEH", long_name="Nineveh", abbreviation="Nin", parent="ASSYRIA"
    )

    provenance_repository.create(parent)
    provenance_repository.create(child1)
    provenance_repository.create(child2)
    provenance_repository.create(child3)

    result = provenance_repository.find_children("BABYLONIA")
    assert len(result) == 2
    assert {r.id for r in result} == {"BABYLON", "URUK"}


def test_find_children_none(provenance_repository: ProvenanceRepository):
    record = ProvenanceRecord(id="BABYLON", long_name="Babylon", abbreviation="Bab")
    provenance_repository.create(record)

    result = provenance_repository.find_children("BABYLON")
    assert len(result) == 0
