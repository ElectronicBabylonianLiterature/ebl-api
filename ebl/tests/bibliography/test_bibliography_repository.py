import pydash
import pytest

from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

COLLECTION = "bibliography"


def test_create_indexes(database, bibliography_repository):
    bibliography_repository.create_indexes()

    index_keys = [
        index["key"] for index in database[COLLECTION].index_information().values()
    ]

    assert [("citationKey", 1)] in index_keys
    assert [("aliases.value", 1)] in index_keys
    assert [("aliases.normalizedValue", 1)] in index_keys
    assert [("redirectTo", 1)] in index_keys
    reservation_indexes = database[
        "bibliography_lookup_reservations"
    ].index_information()
    reservation_index_keys = [index["key"] for index in reservation_indexes.values()]
    assert reservation_indexes["bibliography_lookup_value_unique"]["unique"] is True
    assert reservation_indexes["bibliography_lookup_value_unique"]["key"] == [
        ("value", 1)
    ]
    assert [("entryId", 1)] in reservation_index_keys
    assert [("owner", 1)] in reservation_index_keys
    assert [("state", 1), ("expiresAt", 1)] in reservation_index_keys
    ttl_indexes = [
        index
        for index in reservation_indexes.values()
        if index["key"] == [("deleteAt", 1)]
    ]
    assert ttl_indexes[0]["expireAfterSeconds"] == 0


def test_create(database, bibliography_repository, create_mongo_bibliography_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)

    assert (
        database[COLLECTION].find_one({"_id": bibliography_entry["id"]})
        == create_mongo_bibliography_entry()
    )


def test_create_duplicate(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)
    with pytest.raises(DuplicateError):
        bibliography_repository.create(bibliography_entry)


def test_find(database, bibliography_repository, create_mongo_bibliography_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"])
        == bibliography_entry
    )


def test_find_by_citation_key(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="miccadei2002")
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert (
        bibliography_repository.query_by_citation_key(bibliography_entry["citationKey"])
        == bibliography_entry
    )


def test_find_by_ambiguous_citation_key(bibliography_repository):
    first_entry = BibliographyEntryFactory.build(
        id="Q30000001", citationKey="miccadei2002"
    )
    second_entry = BibliographyEntryFactory.build(
        id="Q30000002", citationKey="miccadei2002"
    )
    bibliography_repository.create(first_entry)
    bibliography_repository.create(second_entry)

    with pytest.raises(DuplicateError):
        bibliography_repository.query_by_citation_key("miccadei2002")


def test_find_by_alias_value(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    alias = "Leipzig/ABC 123"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": "leipzig-abc-123"}]
    )
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert bibliography_repository.query_by_alias(alias) == bibliography_entry


def test_find_by_normalized_alias(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[
            {
                "value": "Leipzig/ABC 123",
                "normalizedValue": "leipzig-abc-123",
            }
        ]
    )
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert (
        bibliography_repository.query_by_alias("Leipzig ABC 123") == bibliography_entry
    )


@pytest.mark.parametrize(
    "alias_case",
    [
        ("Leipzig/ABC 123", "Leipzig ABC 123", "leipzig-abc-123"),
        ("Von_Soden:Alte/Orient", "Von Soden Alte Orient", "von-soden-alte-orient"),
        ("D’Agostino", "D'Agostino", "d-agostino"),
        ("Müller", "Muller", "muller"),
        ("šulgi", "sulgi", "sulgi"),
        ("Moon(-Killick)", "Moon Killick", "moon-killick"),
    ],
)
def test_find_by_special_character_alias(
    alias_case,
    database,
    bibliography_repository,
    create_mongo_bibliography_entry,
):
    alias, lookup, normalized_value = alias_case
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": normalized_value}]
    )
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert bibliography_repository.query_by_alias(lookup) == bibliography_entry


def test_find_by_ambiguous_alias(bibliography_repository):
    first_entry = BibliographyEntryFactory.build(
        id="Q30000001", aliases=[{"value": "legacy", "normalizedValue": "legacy"}]
    )
    second_entry = BibliographyEntryFactory.build(
        id="Q30000002", aliases=[{"value": "legacy", "normalizedValue": "legacy"}]
    )
    bibliography_repository.create(first_entry)
    bibliography_repository.create(second_entry)

    with pytest.raises(DuplicateError):
        bibliography_repository.query_by_alias("legacy")


def test_find_by_conflicting_normalized_alias(bibliography_repository):
    first_entry = BibliographyEntryFactory.build(
        id="Q30000001",
        aliases=[{"value": "D’Agostino", "normalizedValue": "d-agostino"}],
    )
    second_entry = BibliographyEntryFactory.build(
        id="Q30000002",
        aliases=[{"value": "D'Agostino", "normalizedValue": "d-agostino"}],
    )
    bibliography_repository.create(first_entry)
    bibliography_repository.create(second_entry)

    with pytest.raises(DuplicateError):
        bibliography_repository.query_by_alias("D'Agostino")


def test_entry_not_found(bibliography_repository):
    with pytest.raises(NotFoundError):
        bibliography_repository.query_by_id("not found")


def test_update(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    updated_entry = pydash.omit({**bibliography_entry, "title": "New Title"}, "PMID")
    bibliography_repository.create(bibliography_entry)
    bibliography_repository.update(updated_entry, {})

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"]) == updated_entry
    )


def test_update_not_found(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    with pytest.raises(NotFoundError):
        bibliography_repository.update(bibliography_entry, {})


def test_update_detects_a_concurrently_removed_null_redirect(
    bibliography_repository, database
):
    bibliography_entry = BibliographyEntryFactory.build(redirectTo=None)
    bibliography_repository.create(bibliography_entry)
    database[COLLECTION].update_one(
        {"_id": bibliography_entry["id"]}, {"$unset": {"redirectTo": ""}}
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography_repository.update(
            {**bibliography_entry, "title": "New Title"}, {"redirectTo": None}
        )

    assert (
        database[COLLECTION].find_one({"_id": bibliography_entry["id"]})["title"]
        == bibliography_entry["title"]
    )


def test_update_accepts_an_unchanged_null_redirect(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build(redirectTo=None)
    updated_entry = {**bibliography_entry, "title": "New Title"}
    bibliography_repository.create(bibliography_entry)

    bibliography_repository.update(updated_entry, {"redirectTo": None})

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"]) == updated_entry
    )
