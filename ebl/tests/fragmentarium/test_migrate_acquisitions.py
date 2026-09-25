from ebl.fragmentarium.migrate_acquisitions import COLLECTION, build_update, run_migration


def test_migrate_promotes_legacy_singular_acquisition(database):
    collection = database[COLLECTION]
    acquisition = {"description": "purchase", "supplier": "gallery", "date": 1925}
    collection.insert_one({"_id": "X.1", "acquisition": acquisition})

    stats = run_migration(collection)

    stored = collection.find_one({"_id": "X.1"})
    assert stored["acquisitions"] == [acquisition]
    assert "acquisition" not in stored
    assert stats == {
        "scanned": 1,
        "documents_migrated": 1,
        "documents_backfilled": 0,
    }


def test_migrate_preserves_canonical_acquisitions_when_both_fields_present(database):
    collection = database[COLLECTION]
    legacy_acquisition = {"description": "stale", "supplier": "old", "date": 1900}
    canonical_acquisitions = [
        {"description": "first", "supplier": "A", "date": 1920},
        {"description": "second", "supplier": "B", "date": 1930},
    ]
    collection.insert_one(
        {
            "_id": "X.2",
            "acquisition": legacy_acquisition,
            "acquisitions": canonical_acquisitions,
        }
    )

    run_migration(collection)

    stored = collection.find_one({"_id": "X.2"})
    assert stored["acquisitions"] == canonical_acquisitions
    assert "acquisition" not in stored


def test_migrate_backfills_documents_without_acquisition(database):
    collection = database[COLLECTION]
    collection.insert_one({"_id": "X.3"})

    stats = run_migration(collection)

    stored = collection.find_one({"_id": "X.3"})
    assert stored["acquisitions"] == []
    assert stats["documents_backfilled"] == 1


def test_migrate_does_not_overwrite_concurrent_canonical_write(database):
    collection = database[COLLECTION]
    legacy_acquisition = {"description": "stale", "supplier": "old", "date": 1900}
    collection.insert_one({"_id": "X.4", "acquisition": legacy_acquisition})

    stale_document = collection.find_one({"_id": "X.4"})

    concurrent_acquisitions = [
        {"description": "concurrent", "supplier": "C", "date": 1940}
    ]
    collection.update_one(
        {"_id": "X.4"},
        {"$set": {"acquisitions": concurrent_acquisitions}, "$unset": {"acquisition": ""}},
    )

    result = collection.bulk_write([build_update(stale_document)])

    stored = collection.find_one({"_id": "X.4"})
    assert result.matched_count == 0
    assert stored["acquisitions"] == concurrent_acquisitions
