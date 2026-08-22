from dataclasses import dataclass

import pytest
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.errors import DataError
from ebl.tests.bibliography.identity_management_test_helpers import (
    RESERVATIONS,
    alias,
    changelog_entries,
    entry,
    reservation,
    reservation_state,
    stored,
)
from ebl.users.domain.user import User

COMMITTED = LookupReservationState.COMMITTED.value
ABANDONED = LookupReservationState.ABANDONED.value


@pytest.fixture
def identity_management(bibliography_repository, changelog, bibliography):
    return BibliographyIdentityManagement(
        bibliography_repository, changelog, bibliography.find
    )


@dataclass(frozen=True)
class RecoveryContext:
    identity_management: BibliographyIdentityManagement
    bibliography_repository: MongoBibliographyRepository
    changelog: Changelog
    database: Database
    bibliography: Bibliography
    user: User


@pytest.fixture
def recovery_context(request: pytest.FixtureRequest) -> RecoveryContext:
    return RecoveryContext(
        request.getfixturevalue("identity_management"),
        request.getfixturevalue("bibliography_repository"),
        request.getfixturevalue("changelog"),
        request.getfixturevalue("database"),
        request.getfixturevalue("bibliography"),
        request.getfixturevalue("user"),
    )


def fail_once(monkeypatch, target, name: str, message: str) -> None:
    original = getattr(target, name)
    calls = {"count": 0}

    def failing(*args, **kwargs):
        if calls["count"] == 0:
            calls["count"] += 1
            raise RuntimeError(message)
        return original(*args, **kwargs)

    monkeypatch.setattr(target, name, failing)


def test_claim_failure_leaves_identity_untouched(monkeypatch, recovery_context):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000130", citationKey="intact1999Key")
    fail_once(
        monkeypatch,
        context.bibliography_repository,
        "claim_lookup_values",
        "claim failed",
    )

    with pytest.raises(RuntimeError, match="claim failed"):
        context.identity_management.manage_identity(
            "Q30000130", {"addAliases": [alias("never-claimed")]}, context.user
        )

    assert "aliases" not in stored(context.database, "Q30000130")
    assert reservation(context.database, "never-claimed") is None
    assert reservation_state(context.database, "intact1999Key") == COMMITTED


def test_persistence_failure_releases_pending_claims(monkeypatch, recovery_context):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000131")
    fail_once(
        monkeypatch,
        context.bibliography_repository,
        "update_identity_fields",
        "update failed",
    )

    with pytest.raises(RuntimeError, match="update failed"):
        context.identity_management.manage_identity(
            "Q30000131", {"addAliases": [alias("rolled-back")]}, context.user
        )

    assert "aliases" not in stored(context.database, "Q30000131")
    assert reservation(context.database, "rolled-back") is None
    assert context.database[RESERVATIONS].count_documents({"state": "pending"}) == 0


def test_commit_failure_keeps_old_value_claimed_until_reconciled(
    monkeypatch, recovery_context
):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000132", citationKey="old1999Key")
    fail_once(
        monkeypatch,
        context.bibliography_repository,
        "commit_lookup_values",
        "commit failed",
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        context.identity_management.manage_identity(
            "Q30000132", {"citationKey": "new1999Key"}, context.user
        )

    assert stored(context.database, "Q30000132")["citationKey"] == "new1999Key"
    assert reservation_state(context.database, "old1999Key") == COMMITTED
    assert reservation_state(context.database, "new1999Key") == "pending"


def test_retirement_failure_does_not_retire_before_the_new_value_is_persisted(
    monkeypatch, recovery_context
):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000133", citationKey="old1999Key")
    fail_once(
        monkeypatch,
        context.bibliography_repository,
        "retire_lookup_values",
        "retire failed",
    )

    with pytest.raises(RuntimeError, match="retire failed"):
        context.identity_management.manage_identity(
            "Q30000133", {"citationKey": "new1999Key"}, context.user
        )

    assert stored(context.database, "Q30000133")["citationKey"] == "new1999Key"
    assert reservation_state(context.database, "new1999Key") == COMMITTED
    assert reservation_state(context.database, "old1999Key") == COMMITTED


def test_changelog_failure_keeps_the_persisted_identity(monkeypatch, recovery_context):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000134")
    changelog_before = len(changelog_entries(context.database, "Q30000134"))
    fail_once(monkeypatch, context.changelog, "create", "changelog failed")

    with pytest.raises(RuntimeError, match="changelog failed"):
        context.identity_management.manage_identity(
            "Q30000134", {"addAliases": [alias("logged-late")]}, context.user
        )

    assert stored(context.database, "Q30000134")["aliases"] == [alias("logged-late")]
    assert reservation_state(context.database, "logged-late") == COMMITTED
    assert len(changelog_entries(context.database, "Q30000134")) == changelog_before


def test_validation_failure_writes_nothing(
    identity_management, database, bibliography, user
):
    entry(bibliography, user, "Q30000135")
    changelog_before = len(changelog_entries(database, "Q30000135"))

    with pytest.raises(DataError, match="cannot redirect to itself"):
        identity_management.manage_identity(
            "Q30000135", {"deprecateTo": "Q30000135"}, user
        )

    assert "deprecated" not in stored(database, "Q30000135")
    assert database[RESERVATIONS].count_documents({"state": "pending"}) == 0
    assert len(changelog_entries(database, "Q30000135")) == changelog_before
