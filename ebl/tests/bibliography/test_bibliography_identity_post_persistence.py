from dataclasses import dataclass
from datetime import datetime

import pytest
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationState,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.errors import DuplicateError
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

RESERVATIONS = "bibliography_lookup_reservations"
FUTURE = datetime(2099, 1, 1)


@dataclass(frozen=True)
class BibliographyIdentityContext:
    bibliography: Bibliography
    bibliography_repository: MongoBibliographyRepository
    database: Database
    changelog: Changelog
    user: User


@pytest.fixture
def bibliography_identity_context(request: pytest.FixtureRequest):
    return BibliographyIdentityContext(
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


def state(database, value: str):
    return database[RESERVATIONS].find_one({"_id": value})["state"]


def assert_no_pending(database):
    assert database[RESERVATIONS].count_documents({"state": "pending"}) == 0


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


def test_create_commit_failure_recovers_lookup_claims(
    monkeypatch, bibliography_identity_context
):
    context = bibliography_identity_context
    entry = bibliography_entry("Q30000000", "create-commit-key")
    original_commit = fail_once(
        monkeypatch,
        context.bibliography_repository,
        "commit_lookup_values",
        "commit failed",
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        context.bibliography.create(entry, context.user)

    assert context.bibliography_repository.query_by_id(entry["id"]) == entry
    assert state(context.database, entry["id"]) == LookupReservationState.PENDING.value
    assert (
        state(context.database, entry["citationKey"])
        == LookupReservationState.PENDING.value
    )
    monkeypatch.setattr(
        context.bibliography_repository, "commit_lookup_values", original_commit
    )
    context.bibliography_repository.reconcile_lookup_reservations(FUTURE)

    assert (
        state(context.database, entry["id"]) == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    assert context.bibliography.find(entry["citationKey"]) == entry
    with pytest.raises(DuplicateError):
        context.bibliography.create(entry, context.user)
    assert context.database["bibliography"].count_documents({"_id": entry["id"]}) == 1


def test_create_changelog_failure_keeps_committed_claims(
    monkeypatch, bibliography_identity_context
):
    context = bibliography_identity_context
    entry = bibliography_entry("Q30000000", "create-changelog-key")
    fail_once(monkeypatch, context.changelog, "create", "changelog failed")

    with pytest.raises(RuntimeError, match="changelog failed"):
        context.bibliography.create(entry, context.user)

    assert context.bibliography_repository.query_by_id(entry["id"]) == entry
    assert (
        state(context.database, entry["id"]) == LookupReservationState.COMMITTED.value
    )
    assert (
        state(context.database, entry["citationKey"])
        == LookupReservationState.COMMITTED.value
    )
    context.bibliography_repository.reconcile_lookup_reservations(FUTURE)
    with pytest.raises(DuplicateError):
        context.bibliography.create(
            bibliography_entry("Q30000001", entry["citationKey"]), context.user
        )
    assert_no_pending(context.database)
