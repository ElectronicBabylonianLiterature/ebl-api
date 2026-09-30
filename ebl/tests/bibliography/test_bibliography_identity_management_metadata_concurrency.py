"""A trusted identity operation must never revert a concurrent, unrelated
metadata edit: it reads the stored entry once, then does further I/O
(redirect validation, lookup claims) before it can persist, and a caller of
`POST /bibliography/{id}/identity` never submits any CSL field at all, so it
has no way to know its request could otherwise carry stale CSL content back
into storage.
"""

from dataclasses import dataclass

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.bibliography.application import identity_management as identity_module
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
)
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    body,
    changelog_entries,
    entry,
    manage_identity,
    stored,
)
from ebl.users.domain.user import User


@pytest.fixture
def client(context):
    return admin_client(context)


@pytest.fixture
def identity_management(bibliography_repository, changelog, bibliography):
    return BibliographyIdentityManagement(bibliography_repository, changelog)


@dataclass(frozen=True)
class ReactivationContext:
    client: testing.TestClient
    database: Database
    bibliography: Bibliography
    bibliography_repository: BibliographyRepository
    identity_management: BibliographyIdentityManagement
    user: User


@pytest.fixture
def reactivation_context(
    context, database, bibliography, identity_management, user
) -> ReactivationContext:
    return ReactivationContext(
        admin_client(context),
        database,
        bibliography,
        context.bibliography_repository,
        identity_management,
        user,
    )


def interleave_metadata_edit(monkeypatch, bibliography, user, id_: str, **changes):
    """Land an ordinary metadata edit between the identity operation's read
    of the stored entry and its persistence step.
    """
    original = identity_module.validate_identity_state
    calls = {"count": 0}

    def validate(entry, query_by_id, query_by_redirect_target):
        if calls["count"] == 0:
            calls["count"] += 1
            stored_entry = bibliography.find(id_)
            bibliography.update_metadata({**stored_entry, **changes}, user)
        return original(entry, query_by_id, query_by_redirect_target)

    monkeypatch.setattr(identity_module, "validate_identity_state", validate)


def test_concurrent_title_edit_survives_an_alias_addition(
    monkeypatch, reactivation_context
):
    context = reactivation_context
    entry(context.bibliography, context.user, "Q30000160")
    interleave_metadata_edit(
        monkeypatch,
        context.bibliography,
        context.user,
        "Q30000160",
        title="Concurrent title",
    )

    result = manage_identity(
        context.client, "Q30000160", {"addAliases": [alias("new-alias")]}
    )

    assert result.status == falcon.HTTP_OK
    assert body(result)["title"] == "Concurrent title"
    stored_entry = stored(context.database, "Q30000160")
    assert result.json == context.bibliography_repository.query_by_id("Q30000160")
    assert stored_entry["title"] == "Concurrent title"
    assert stored_entry["aliases"] == [alias("new-alias")]


def test_concurrent_metadata_edits_are_last_write_wins(
    bibliography, bibliography_repository, user
):
    original = entry(bibliography, user, "Q30000168")
    first_edit = {**original, "title": "First title"}
    second_edit = {**original, "title": "Second title"}

    bibliography.update_metadata(first_edit, user)
    bibliography.update_metadata(second_edit, user)

    assert bibliography_repository.query_by_id("Q30000168")["title"] == "Second title"


def test_noop_returns_an_authoritative_concurrent_metadata_edit(
    monkeypatch,
    bibliography,
    bibliography_repository,
    identity_management,
    user,
):
    bibliography_entry = entry(bibliography, user, "Q30000167")
    original_apply = identity_module.apply_identity_commands

    def apply_with_concurrent_edit(stored_entry, commands):
        updated_entry = original_apply(stored_entry, commands)
        bibliography.update_metadata(
            {**bibliography_entry, "title": "Concurrent title"}, user
        )
        return updated_entry

    monkeypatch.setattr(
        identity_module, "apply_identity_commands", apply_with_concurrent_edit
    )

    result = identity_management.manage_identity("Q30000167", {}, user)

    assert result == bibliography_repository.query_by_id("Q30000167")
    assert result["title"] == "Concurrent title"


def test_concurrent_title_edit_survives_a_citation_key_change(
    monkeypatch, client, database, bibliography, user
):
    entry(bibliography, user, "Q30000161", citationKey="old1999Key")
    interleave_metadata_edit(
        monkeypatch, bibliography, user, "Q30000161", title="Concurrent title"
    )

    result = manage_identity(client, "Q30000161", {"citationKey": "new1999Key"})

    assert result.status == falcon.HTTP_OK
    stored_entry = stored(database, "Q30000161")
    assert stored_entry["title"] == "Concurrent title"
    assert stored_entry["citationKey"] == "new1999Key"


def test_concurrent_title_edit_survives_a_deprecation(
    monkeypatch, client, database, bibliography, user
):
    entry(bibliography, user, "Q30000162")
    target = entry(bibliography, user, "Q30000163")
    interleave_metadata_edit(
        monkeypatch, bibliography, user, "Q30000162", title="Concurrent title"
    )

    result = manage_identity(client, "Q30000162", {"deprecateTo": target["id"]})

    assert result.status == falcon.HTTP_OK
    stored_entry = stored(database, "Q30000162")
    assert stored_entry["title"] == "Concurrent title"
    assert stored_entry["deprecated"] is True


def test_a_title_edit_concurrent_with_deprecation_survives_a_later_reactivation(
    monkeypatch, reactivation_context
):
    """A metadata edit can never itself race a reactivation -- an entry
    rejects metadata edits outright while it is deprecated -- so this races
    the edit against the deprecation instead and checks the title is still
    intact once the entry is reactivated.
    """
    context = reactivation_context
    entry(context.bibliography, context.user, "Q30000164")
    target = entry(context.bibliography, context.user, "Q30000165")
    interleave_metadata_edit(
        monkeypatch,
        context.bibliography,
        context.user,
        "Q30000164",
        title="Concurrent title",
    )

    deprecate_result = manage_identity(
        context.client, "Q30000164", {"deprecateTo": target["id"]}
    )
    assert deprecate_result.status == falcon.HTTP_OK

    result = context.identity_management.manage_identity(
        "Q30000164", {"reactivate": True}, context.user
    )

    assert result["title"] == "Concurrent title"
    stored_entry = stored(context.database, "Q30000164")
    assert stored_entry["title"] == "Concurrent title"
    assert "deprecated" not in stored_entry


def test_the_identity_changelog_entry_names_only_the_identity_change(
    monkeypatch, client, database, bibliography, user
):
    entry(bibliography, user, "Q30000166")
    interleave_metadata_edit(
        monkeypatch, bibliography, user, "Q30000166", title="Concurrent title"
    )

    manage_identity(client, "Q30000166", {"addAliases": [alias("logged-alias")]})

    identity_entries = [
        changelog_entry
        for changelog_entry in changelog_entries(database, "Q30000166")
        if any("aliases" in str(change) for change in changelog_entry["diff"])
    ]
    assert len(identity_entries) == 1
    assert not any("title" in str(change) for change in identity_entries[0]["diff"])
