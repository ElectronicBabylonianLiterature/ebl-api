from unittest.mock import patch

from ebl.common.migrate_provenances import migrate_provenances
from ebl.common.domain.provenance_data import build_provenance_records


def test_migrate_provenances(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    count = collection.count_documents({})

    assert count == len(build_provenance_records())


def test_migrate_provenances_creates_indexes(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    indexes = collection.index_information()

    assert "longName_1" in indexes
    assert "abbreviation_1" in indexes
    assert "parent_1" in indexes


def test_migrate_provenances_with_coordinates(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    babylon = collection.find_one({"_id": "BABYLON"})

    assert babylon is not None
    assert babylon["longName"] == "Babylon"
    assert "coordinates" in babylon
    assert babylon["coordinates"]["latitude"] == 32.5425
    assert babylon["coordinates"]["longitude"] == 44.4275


def test_migrate_provenances_without_coordinates(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    standard_text = collection.find_one({"_id": "STANDARD_TEXT"})

    assert standard_text is not None
    assert standard_text["longName"] == "Standard Text"
    assert "coordinates" not in standard_text


def test_migrate_provenances_preserves_parent_relationships(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    babylon = collection.find_one({"_id": "BABYLON"})

    assert babylon["parent"] == "Babylonia"

    children = list(collection.find({"parent": "Babylonia"}))
    assert len(children) > 0
    assert any(c["_id"] == "BABYLON" for c in children)


def test_migrate_provenances_idempotent(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()
        count1 = database["provenances"].count_documents({})

        migrate_provenances()
        count2 = database["provenances"].count_documents({})

        assert count1 == count2


def test_migrate_provenances_all_fields(database):
    with patch("ebl.common.migrate_provenances.get_database", return_value=database):
        migrate_provenances()

    collection = database["provenances"]
    record = collection.find_one({"_id": "NINEVEH"})

    assert record["_id"] == "NINEVEH"
    assert record["longName"] == "Nineveh"
    assert record["abbreviation"] == "Nin"
    assert record["parent"] == "Assyria"
    assert "cigsKey" in record
    assert "sortKey" in record
