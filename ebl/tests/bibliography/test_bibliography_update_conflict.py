import falcon
import pytest

from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CORRECTED_TITLE,
    metadata_only_payload,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

CONCURRENT_ALIAS = {
    "value": "RN9001",
    "normalizedValue": "rn9001",
    "type": "legacy_id",
    "source": "duplicate_merge_2026-08-04",
    "status": "redirect",
}


@pytest.fixture
def active_entry(bibliography, user):
    entry = BibliographyEntryFactory.build(id="Q30000042", title="Before")
    bibliography.create(entry, user)
    return entry


def inject_concurrent_write(monkeypatch, bibliography_repository, database, update):
    def claim_lookup_values(_operation, _values):
        database["bibliography"].update_one({"_id": "Q30000042"}, update)

    monkeypatch.setattr(
        bibliography_repository, "claim_lookup_values", claim_lookup_values
    )


def stored(database):
    return database["bibliography"].find_one({"_id": "Q30000042"})


def test_metadata_update_succeeds_without_concurrent_write(
    client, database, active_entry
):
    result = post_entry(client, metadata_only_payload(active_entry))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database)["title"] == CORRECTED_TITLE


def test_concurrently_added_alias_makes_metadata_update_conflict(
    monkeypatch, bibliography, bibliography_repository, database, user, active_entry
):
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$push": {"aliases": CONCURRENT_ALIAS}},
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography.update(metadata_only_payload(active_entry), user)


def test_concurrently_added_alias_survives_the_conflict(
    monkeypatch, bibliography, bibliography_repository, database, user, active_entry
):
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$push": {"aliases": CONCURRENT_ALIAS}},
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography.update(metadata_only_payload(active_entry), user)
    stored_entry = stored(database)

    assert stored_entry["aliases"] == [CONCURRENT_ALIAS]
    assert stored_entry["title"] == active_entry["title"]


def test_concurrent_deprecation_makes_metadata_update_conflict(
    monkeypatch, bibliography, bibliography_repository, database, user, active_entry
):
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$set": {"deprecated": True, "redirectTo": "rla_9_388"}},
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography.update(metadata_only_payload(active_entry), user)


def test_concurrent_tombstone_survives_the_conflict(
    monkeypatch, bibliography, bibliography_repository, database, user, active_entry
):
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$set": {"deprecated": True, "redirectTo": "rla_9_388"}},
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography.update(metadata_only_payload(active_entry), user)
    stored_entry = stored(database)

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"
    assert stored_entry["title"] == active_entry["title"]


def test_conflict_writes_no_changelog_entry(
    monkeypatch, bibliography, bibliography_repository, database, user, active_entry
):
    before = database["changelog"].count_documents({"resource_id": "Q30000042"})
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$push": {"aliases": CONCURRENT_ALIAS}},
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography.update(metadata_only_payload(active_entry), user)

    assert database["changelog"].count_documents({"resource_id": "Q30000042"}) == before


def test_conflict_is_reported_as_http_conflict(
    monkeypatch, client, bibliography_repository, database, active_entry
):
    inject_concurrent_write(
        monkeypatch,
        bibliography_repository,
        database,
        {"$push": {"aliases": CONCURRENT_ALIAS}},
    )

    result = post_entry(client, metadata_only_payload(active_entry))

    assert result.status == falcon.HTTP_CONFLICT
