from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_with_identity_claims,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.errors import NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

RESERVATIONS = "bibliography_lookup_reservations"
FUTURE = datetime(2099, 1, 1)


@dataclass(frozen=True)
class BibliographyIdentityUpdateContext:
    bibliography: Bibliography
    bibliography_repository: MongoBibliographyRepository
    database: Database
    changelog: Changelog
    user: User


@pytest.fixture
def bibliography_identity_update_context(request: pytest.FixtureRequest):
    return BibliographyIdentityUpdateContext(
        request.getfixturevalue("bibliography"),
        request.getfixturevalue("bibliography_repository"),
        request.getfixturevalue("database"),
        request.getfixturevalue("changelog"),
        request.getfixturevalue("user"),
    )


def bibliography_entry(id_: str, citation_key: str, **overrides):
    return BibliographyEntryFactory.build(
        id=id_, citationKey=citation_key, DOI=f"10.1000/{id_}", PMID=id_, **overrides
    )


def alias(value: str):
    return {"value": value, "normalizedValue": value}


def state(database, value: str):
    return database[RESERVATIONS].find_one({"_id": value})["state"]


def claim(database, value: str):
    return database[RESERVATIONS].find_one({"_id": value})


def reclaim(bibliography_repository, value: str):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("other", "Q39999999", FUTURE + timedelta(hours=1)),
        [value],
    )


def update_identity(context: "BibliographyIdentityUpdateContext", entry: dict) -> None:
    update_with_identity_claims(
        BibliographyIdentityContext(
            context.bibliography_repository,
            context.changelog,
            context.bibliography.find,
        ),
        entry,
        context.user,
    )


def fail_once(monkeypatch, target, name: str, message: str):
    original = getattr(target, name)
    calls = {"count": 0}

    def failing(*args, **kwargs):
        if calls["count"] == 0:
            calls["count"] += 1
            raise RuntimeError(message)
        return original(*args, **kwargs)

    monkeypatch.setattr(target, name, failing)
    return original


def test_update_commit_failure_recovers_new_claims_and_retires_old(
    monkeypatch, bibliography_identity_update_context
):
    context = bibliography_identity_update_context
    old_entry = bibliography_entry("Q30000000", "old-update-key")
    new_entry = {
        **old_entry,
        "citationKey": "new-update-key",
        "aliases": [alias("new-update-alias")],
    }
    context.bibliography.create(old_entry, context.user)
    original_commit = fail_once(
        monkeypatch,
        context.bibliography_repository,
        "commit_lookup_values",
        "commit failed",
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        update_identity(context, new_entry)

    assert context.bibliography_repository.query_by_id(old_entry["id"]) == new_entry
    assert (
        state(context.database, old_entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, new_entry["citationKey"])
        == LookupReservationState.PENDING.value
    )
    monkeypatch.setattr(
        context.bibliography_repository, "commit_lookup_values", original_commit
    )
    context.bibliography_repository.reconcile_lookup_reservations(FUTURE)

    assert (
        state(context.database, new_entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, old_entry["citationKey"])
        == LookupReservationState.ABANDONED.value
    )
    assert context.bibliography.find("new-update-alias") == new_entry
    update_identity(context, new_entry)
    assert (
        context.database["bibliography"].count_documents({"_id": old_entry["id"]}) == 1
    )


def test_update_retirement_failure_reconciles_stale_old_claim(
    monkeypatch, bibliography_identity_update_context
):
    context = bibliography_identity_update_context
    old_entry = bibliography_entry("Q30000000", "old-retire-key")
    new_entry = {**old_entry, "citationKey": "new-retire-key"}
    context.bibliography.create(old_entry, context.user)
    fail_once(
        monkeypatch,
        context.bibliography_repository,
        "retire_lookup_values",
        "retire failed",
    )

    with pytest.raises(RuntimeError, match="retire failed"):
        update_identity(context, new_entry)

    assert context.bibliography.find(new_entry["citationKey"]) == new_entry
    assert (
        state(context.database, new_entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, old_entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    context.bibliography_repository.reconcile_lookup_reservations(FUTURE)

    assert (
        state(context.database, old_entry["citationKey"])
        == LookupReservationState.ABANDONED.value
    )
    reclaim(context.bibliography_repository, old_entry["citationKey"])
    assert claim(context.database, old_entry["citationKey"])["state"] == "pending"
    context.bibliography_repository.release_pending_lookup_values("other")
    assert context.bibliography.find(new_entry["citationKey"]) == new_entry


def test_update_changelog_failure_keeps_persisted_update(
    monkeypatch, bibliography_identity_update_context
):
    context = bibliography_identity_update_context
    old_entry = bibliography_entry("Q30000000", "old-changelog-key")
    new_entry = {**old_entry, "citationKey": "new-changelog-key"}
    context.bibliography.create(old_entry, context.user)
    fail_once(monkeypatch, context.changelog, "create", "changelog failed")

    with pytest.raises(RuntimeError, match="changelog failed"):
        update_identity(context, new_entry)

    assert context.bibliography_repository.query_by_id(old_entry["id"]) == new_entry
    assert (
        state(context.database, new_entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, old_entry["citationKey"])
        == LookupReservationState.ABANDONED.value
    )
    context.bibliography_repository.reconcile_lookup_reservations(FUTURE)
    update_identity(context, new_entry)

    with pytest.raises(NotFoundError):
        context.bibliography.find(old_entry["citationKey"])
    assert context.bibliography.find(new_entry["citationKey"]) == new_entry
    assert (
        context.database["bibliography"].count_documents({"_id": old_entry["id"]}) == 1
    )
