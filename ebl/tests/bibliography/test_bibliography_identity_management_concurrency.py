import falcon
import pytest

from ebl.bibliography.application import identity_management as identity_module
from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.tests.bibliography.identity_management_test_helpers import (
    RESERVATIONS,
    admin_client,
    alias,
    entry,
    manage_identity,
    reservation,
    stored,
)


@pytest.fixture
def client(context):
    return admin_client(context)


@pytest.fixture
def identity_management(bibliography_repository, changelog, bibliography):
    return BibliographyIdentityManagement(
        bibliography_repository, changelog, bibliography.find
    )


def interleave(monkeypatch, concurrent_change):
    original = identity_module.validate_identity_state
    calls = {"count": 0}

    def validate(entry, query_by_id, query_by_redirect_target):
        if calls["count"] == 0:
            calls["count"] += 1
            concurrent_change()
        return original(entry, query_by_id, query_by_redirect_target)

    monkeypatch.setattr(identity_module, "validate_identity_state", validate)


def test_concurrent_alias_addition_is_not_lost(
    monkeypatch, client, database, bibliography, identity_management, user
):
    entry(bibliography, user, "Q30000090")
    interleave(
        monkeypatch,
        lambda: identity_management.manage_identity(
            "Q30000090", {"addAliases": [alias("concurrent-a")]}, user
        ),
    )

    result = manage_identity(
        client, "Q30000090", {"addAliases": [alias("concurrent-b")]}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert stored(database, "Q30000090")["aliases"] == [alias("concurrent-a")]


def test_concurrent_citation_key_change_is_not_lost(
    monkeypatch, client, database, bibliography, identity_management, user
):
    entry(bibliography, user, "Q30000091")
    interleave(
        monkeypatch,
        lambda: identity_management.manage_identity(
            "Q30000091", {"citationKey": "winner1999Key"}, user
        ),
    )

    result = manage_identity(client, "Q30000091", {"citationKey": "loser1999Key"})

    assert result.status == falcon.HTTP_CONFLICT
    assert stored(database, "Q30000091")["citationKey"] == "winner1999Key"


def test_conflict_leaves_no_reservation_or_changelog_trace(
    monkeypatch, client, database, bibliography, identity_management, user
):
    entry(bibliography, user, "Q30000092")
    interleave(
        monkeypatch,
        lambda: identity_management.manage_identity(
            "Q30000092", {"addAliases": [alias("winner-alias")]}, user
        ),
    )
    changelog_before = database["changelog"].count_documents(
        {"resource_id": "Q30000092"}
    )

    manage_identity(client, "Q30000092", {"addAliases": [alias("loser-alias")]})

    assert reservation(database, "loser-alias") is None
    assert database[RESERVATIONS].count_documents({"state": "pending"}) == 0
    assert (
        database["changelog"].count_documents({"resource_id": "Q30000092"})
        == changelog_before + 1
    )


def test_retry_after_conflict_succeeds(
    monkeypatch, client, database, bibliography, identity_management, user
):
    entry(bibliography, user, "Q30000093")
    interleave(
        monkeypatch,
        lambda: identity_management.manage_identity(
            "Q30000093", {"addAliases": [alias("first-alias")]}, user
        ),
    )
    assert (
        manage_identity(
            client, "Q30000093", {"addAliases": [alias("second-alias")]}
        ).status
        == falcon.HTTP_CONFLICT
    )

    result = manage_identity(
        client, "Q30000093", {"addAliases": [alias("second-alias")]}
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000093")["aliases"] == [
        alias("first-alias"),
        alias("second-alias"),
    ]


def test_stale_stored_entry_raises_a_conflict(
    bibliography, bibliography_repository, identity_management, user
):
    entry(bibliography, user, "Q30000094")
    identity_management.manage_identity(
        "Q30000094", {"citationKey": "current1999Key"}, user
    )

    with pytest.raises(BibliographyUpdateConflictError):
        bibliography_repository.update(
            {**bibliography_repository.query_by_id("Q30000094"), "title": "Stale"},
            {"citationKey": "stale1999Key"},
        )
