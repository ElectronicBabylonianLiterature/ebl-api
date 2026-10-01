import pytest

from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.errors import NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

COLLECTION = "bibliography"


def test_update_identity_fields_sets_a_new_citation_key(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)

    bibliography_repository.update_identity_fields(
        {**bibliography_entry, "citationKey": "new-key"}, {}
    )

    stored = bibliography_repository.query_by_id(bibliography_entry["id"])
    assert stored["citationKey"] == "new-key"
    assert stored["title"] == bibliography_entry["title"]


def test_update_identity_fields_leaves_a_concurrent_metadata_edit_in_place(
    bibliography_repository,
):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)
    bibliography_repository.update(
        {**bibliography_entry, "title": "Concurrent title"}, {}
    )

    bibliography_repository.update_identity_fields(
        {**bibliography_entry, "citationKey": "new-key"}, {}
    )

    stored = bibliography_repository.query_by_id(bibliography_entry["id"])
    assert stored["title"] == "Concurrent title"
    assert stored["citationKey"] == "new-key"


def test_update_identity_fields_unsets_a_removed_citation_key(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="old-key")
    bibliography_repository.create(bibliography_entry)

    bibliography_repository.update_identity_fields(
        {
            key: value
            for key, value in bibliography_entry.items()
            if key != "citationKey"
        },
        {"citationKey": "old-key"},
    )

    stored = bibliography_repository.query_by_id(bibliography_entry["id"])
    assert "citationKey" not in stored


def test_update_identity_fields_not_found(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()

    with pytest.raises(NotFoundError):
        bibliography_repository.update_identity_fields(bibliography_entry, {})


def test_update_identity_fields_detects_a_conflict(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="old-key")
    bibliography_repository.create(bibliography_entry)

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography_repository.update_identity_fields(
            {**bibliography_entry, "citationKey": "new-key"},
            {"citationKey": "stale-key"},
        )

    stored = bibliography_repository.query_by_id(bibliography_entry["id"])
    assert stored["citationKey"] == "old-key"


def test_update_identity_fields_never_touches_a_non_identity_field(
    bibliography_repository, database
):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)

    bibliography_repository.update_identity_fields(
        {**bibliography_entry, "title": "Ignored", "citationKey": "new-key"}, {}
    )

    stored = database[COLLECTION].find_one({"_id": bibliography_entry["id"]})
    assert stored["title"] == bibliography_entry["title"]
    assert stored["citationKey"] == "new-key"
