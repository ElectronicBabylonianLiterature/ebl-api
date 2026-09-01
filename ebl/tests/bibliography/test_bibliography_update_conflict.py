from dataclasses import dataclass

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CORRECTED_TITLE,
    metadata_only_payload,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

ENTRY_ID = "Q30000042"
ORIGINAL_TITLE = "Before"
CONCURRENT_ALIAS = {
    "value": "RN9001",
    "normalizedValue": "rn9001",
    "type": "legacy_id",
    "source": "duplicate_merge_2026-08-04",
    "status": "redirect",
}
ADD_ALIAS = {"$push": {"aliases": CONCURRENT_ALIAS}}
DEPRECATE = {"$set": {"deprecated": True, "redirectTo": "rla_9_388"}}


@dataclass(frozen=True)
class UpdateConflictContext:
    bibliography: Bibliography
    bibliography_repository: MongoBibliographyRepository
    database: Database
    client: testing.TestClient
    user: User
    entry: dict


@pytest.fixture
def conflict_context(request: pytest.FixtureRequest) -> UpdateConflictContext:
    bibliography = request.getfixturevalue("bibliography")
    user = request.getfixturevalue("user")
    entry = BibliographyEntryFactory.build(id=ENTRY_ID, title=ORIGINAL_TITLE)
    bibliography.create(entry, user)
    return UpdateConflictContext(
        bibliography,
        request.getfixturevalue("bibliography_repository"),
        request.getfixturevalue("database"),
        request.getfixturevalue("client"),
        user,
        entry,
    )


def inject_concurrent_write(
    monkeypatch: pytest.MonkeyPatch, context: UpdateConflictContext, update: dict
) -> None:
    def claim_lookup_values(_operation, _values) -> None:
        context.database["bibliography"].update_one({"_id": ENTRY_ID}, update)

    monkeypatch.setattr(
        context.bibliography_repository, "claim_lookup_values", claim_lookup_values
    )


def update_metadata(context: UpdateConflictContext) -> None:
    context.bibliography.update(metadata_only_payload(context.entry), context.user)


def stored(context: UpdateConflictContext) -> dict:
    document = context.database["bibliography"].find_one({"_id": ENTRY_ID})
    assert document is not None
    return document


def changelog_count(context: UpdateConflictContext) -> int:
    return context.database["changelog"].count_documents({"resource_id": ENTRY_ID})


def test_metadata_update_succeeds_without_concurrent_write(conflict_context):
    result = post_entry(
        conflict_context.client, metadata_only_payload(conflict_context.entry)
    )

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(conflict_context)["title"] == CORRECTED_TITLE


def test_concurrently_added_alias_makes_metadata_update_conflict(
    monkeypatch, conflict_context
):
    inject_concurrent_write(monkeypatch, conflict_context, ADD_ALIAS)

    with pytest.raises(BibliographyUpdateConflictError):
        update_metadata(conflict_context)


def test_concurrently_added_alias_survives_the_conflict(monkeypatch, conflict_context):
    inject_concurrent_write(monkeypatch, conflict_context, ADD_ALIAS)

    with pytest.raises(BibliographyUpdateConflictError):
        update_metadata(conflict_context)
    stored_entry = stored(conflict_context)

    assert stored_entry["aliases"] == [CONCURRENT_ALIAS]
    assert stored_entry["title"] == ORIGINAL_TITLE


def test_concurrent_deprecation_makes_metadata_update_conflict(
    monkeypatch, conflict_context
):
    inject_concurrent_write(monkeypatch, conflict_context, DEPRECATE)

    with pytest.raises(BibliographyUpdateConflictError):
        update_metadata(conflict_context)


def test_concurrent_tombstone_survives_the_conflict(monkeypatch, conflict_context):
    inject_concurrent_write(monkeypatch, conflict_context, DEPRECATE)

    with pytest.raises(BibliographyUpdateConflictError):
        update_metadata(conflict_context)
    stored_entry = stored(conflict_context)

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"
    assert stored_entry["title"] == ORIGINAL_TITLE


def test_conflict_writes_no_changelog_entry(monkeypatch, conflict_context):
    before = changelog_count(conflict_context)
    inject_concurrent_write(monkeypatch, conflict_context, ADD_ALIAS)

    with pytest.raises(BibliographyUpdateConflictError):
        update_metadata(conflict_context)

    assert changelog_count(conflict_context) == before


def test_conflict_is_reported_as_http_conflict(monkeypatch, conflict_context):
    inject_concurrent_write(monkeypatch, conflict_context, ADD_ALIAS)

    result = post_entry(
        conflict_context.client, metadata_only_payload(conflict_context.entry)
    )

    assert result.status == falcon.HTTP_CONFLICT


def test_conflict_error_names_the_mismatched_fields():
    error = BibliographyUpdateConflictError(ENTRY_ID, ["aliases", "citationKey"])

    assert error.fields == ("aliases", "citationKey")
    assert "aliases, citationKey" in str(error)
    assert "reload the entry and retry" in str(error)


def test_conflict_error_without_fields_reports_a_concurrent_change():
    error = BibliographyUpdateConflictError(ENTRY_ID)

    assert error.fields == ()
    assert "changed by another operation" in str(error)
