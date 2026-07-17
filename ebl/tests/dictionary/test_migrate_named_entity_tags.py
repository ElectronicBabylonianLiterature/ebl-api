import runpy

import pymongo
from mockito import mock

import ebl.dictionary.migrate_named_entity_tags as module

COLLECTION = "words"


def _insert(database, document):
    database[COLLECTION].insert_one(document)


def test_deduplicate_preserves_order_and_removes_duplicates():
    assert module.deduplicate(["DN", "GN", "DN", "PN", "GN"]) == ["DN", "GN", "PN"]


def test_split_pos_separates_named_entities_from_grammatical():
    grammatical, named = module.split_pos(["N", "DN", "V", "GN"])
    assert grammatical == ["N", "V"]
    assert named == ["DN", "GN"]


def test_run_migration_moves_named_entity_codes(database):
    _insert(database, {"_id": "Marduk I", "pos": ["N", "DN"]})

    stats = module.run_migration(database[COLLECTION])

    document = database[COLLECTION].find_one({"_id": "Marduk I"})
    assert document["pos"] == ["N"]
    assert document["namedEntityTags"] == ["DN"]
    assert stats == {
        "scanned": 1,
        "documents_with_moved_tags": 1,
        "tags_moved": 1,
        "documents_backfilled": 0,
    }


def test_run_migration_backfills_documents_without_named_entity_codes(database):
    _insert(database, {"_id": "verb I", "pos": ["V"]})

    stats = module.run_migration(database[COLLECTION])

    document = database[COLLECTION].find_one({"_id": "verb I"})
    assert document["pos"] == ["V"]
    assert document["namedEntityTags"] == []
    assert stats["documents_with_moved_tags"] == 0
    assert stats["documents_backfilled"] == 1


def test_run_migration_merges_with_existing_named_entity_tags(database):
    _insert(
        database,
        {"_id": "Anu I", "pos": ["DN", "GN"], "namedEntityTags": ["DN"]},
    )

    module.run_migration(database[COLLECTION])

    document = database[COLLECTION].find_one({"_id": "Anu I"})
    assert document["pos"] == []
    assert document["namedEntityTags"] == ["DN", "GN"]


def test_run_migration_is_idempotent(database):
    _insert(database, {"_id": "Ishtar I", "pos": ["N", "DN"]})

    module.run_migration(database[COLLECTION])
    first = database[COLLECTION].find_one({"_id": "Ishtar I"})

    second_stats = module.run_migration(database[COLLECTION])
    second = database[COLLECTION].find_one({"_id": "Ishtar I"})

    assert first == second
    assert second_stats["documents_with_moved_tags"] == 0
    assert second_stats["tags_moved"] == 0


def test_run_migration_dry_run_does_not_write(database):
    _insert(database, {"_id": "Enlil I", "pos": ["N", "DN"]})

    stats = module.run_migration(database[COLLECTION], dry_run=True)

    document = database[COLLECTION].find_one({"_id": "Enlil I"})
    assert document["pos"] == ["N", "DN"]
    assert "namedEntityTags" not in document
    assert stats == {
        "scanned": 1,
        "documents_with_moved_tags": 1,
        "tags_moved": 1,
        "documents_backfilled": 0,
    }


def test_dry_run_reports_backfill_for_documents_without_named_codes(database):
    _insert(database, {"_id": "verb I", "pos": ["V"]})

    stats = module.run_migration(database[COLLECTION], dry_run=True)

    assert "namedEntityTags" not in database[COLLECTION].find_one({"_id": "verb I"})
    assert stats["documents_backfilled"] == 1


def test_get_database(monkeypatch, when):
    client = mock()
    expected_database = mock()
    monkeypatch.setenv("MONGODB_URI", "mongodb://uri")
    monkeypatch.setenv("MONGODB_DB", "ebl")
    when(module).MongoClient("mongodb://uri").thenReturn(client)
    when(client).get_database("ebl").thenReturn(expected_database)

    assert module.get_database() == expected_database


def test_main_runs_migration(monkeypatch, database, when):
    database[COLLECTION].insert_one({"_id": "Sin I", "pos": ["DN"]})
    monkeypatch.setattr(module.sys, "argv", ["migrate"])
    when(module).get_database().thenReturn(database)

    stats = module.main()

    assert stats["documents_with_moved_tags"] == 1
    assert database[COLLECTION].find_one({"_id": "Sin I"})["pos"] == []


def test_main_dry_run(monkeypatch, database, when):
    database[COLLECTION].insert_one({"_id": "Adad I", "pos": ["DN"]})
    monkeypatch.setattr(module.sys, "argv", ["migrate", "--dry-run"])
    when(module).get_database().thenReturn(database)

    module.main()

    assert database[COLLECTION].find_one({"_id": "Adad I"})["pos"] == ["DN"]


def test_module_runs_as_script(monkeypatch, database, when):
    database[COLLECTION].insert_one({"_id": "Nabu I", "pos": ["DN"]})
    monkeypatch.setenv("MONGODB_URI", "mongodb://uri")
    monkeypatch.setenv("MONGODB_DB", "ebl")
    monkeypatch.setattr(module.sys, "argv", ["migrate"])
    client = mock()
    when(client).get_database("ebl").thenReturn(database)
    monkeypatch.setattr(pymongo, "MongoClient", lambda _uri: client)

    runpy.run_path(module.__file__, run_name="__main__")

    document = database[COLLECTION].find_one({"_id": "Nabu I"})
    assert document["pos"] == []
    assert document["namedEntityTags"] == ["DN"]
