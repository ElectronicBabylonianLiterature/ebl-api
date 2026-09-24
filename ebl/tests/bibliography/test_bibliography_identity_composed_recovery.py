from dataclasses import dataclass
import logging

import pytest
from pymongo.database import Database

from ebl.bibliography.application import identity_management as identity_module
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    BibliographyUpdateConflictError,
)
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.tests.bibliography.identity_management_test_helpers import (
    RESERVATIONS,
    alias,
    entry,
    stored,
)
from ebl.users.domain.user import User


@dataclass(frozen=True)
class ComposedRecoveryContext:
    bibliography: Bibliography
    bibliography_repository: BibliographyRepository
    database: Database
    identity_management: BibliographyIdentityManagement
    user: User


@pytest.fixture
def recovery_context(context, database, user) -> ComposedRecoveryContext:
    return ComposedRecoveryContext(
        context.get_bibliography(),
        context.bibliography_repository,
        database,
        BibliographyIdentityManagement(
            context.bibliography_repository, context.changelog
        ),
        user,
    )


def test_failed_commit_then_redirect_race_releases_forward_alias_claim(
    monkeypatch, recovery_context
):
    context = recovery_context
    bibliography_repository = context.bibliography_repository
    database = context.database
    source = entry(context.bibliography, context.user, "Q30000160")
    entry(context.bibliography, context.user, "Q30000161")
    original_commit = bibliography_repository.commit_lookup_values
    original_release = bibliography_repository.release_pending_lookup_values
    commit_calls = {"count": 0}
    forward_owner = {"value": ""}
    released_owners = []

    def fail_forward_commit(operation, now):
        if commit_calls["count"] == 0:
            commit_calls["count"] += 1
            forward_owner["value"] = operation.owner
            raise RuntimeError("forward commit failed")
        return original_commit(operation, now)

    def record_release(owner):
        released_owners.append(owner)
        return original_release(owner)

    original_persist = identity_module.update_identity_fields_only
    persist_calls = {"count": 0}

    def introduce_redirect_race(context, entry_, current_user, stored_entry):
        if persist_calls["count"] == 0:
            persist_calls["count"] += 1
            database["bibliography"].update_one(
                {"_id": "Q30000161"},
                {"$set": {"deprecated": True, "redirectTo": "Q30000160"}},
            )
        return original_persist(context, entry_, current_user, stored_entry)

    monkeypatch.setattr(
        bibliography_repository, "commit_lookup_values", fail_forward_commit
    )
    monkeypatch.setattr(
        bibliography_repository, "release_pending_lookup_values", record_release
    )
    monkeypatch.setattr(
        identity_module, "update_identity_fields_only", introduce_redirect_race
    )

    with pytest.raises(BibliographyUpdateConflictError):
        context.identity_management.manage_identity(
            source["id"],
            {
                "addAliases": [alias("composed-recovery-alias")],
                "deprecateTo": "Q30000161",
            },
            context.user,
        )

    assert bibliography_repository.query_by_id(source["id"]) == source
    assert stored(database, source["id"]).get("redirectTo") is None
    assert released_owners == [forward_owner["value"]]
    assert database[RESERVATIONS].find_one({"_id": "composed-recovery-alias"}) is None
    assert not bibliography_repository.lookup_value_is_reserved(
        "composed-recovery-alias"
    )


def test_release_failure_after_redirect_rollback_keeps_conflict_response(
    monkeypatch, caplog, recovery_context
):
    context = recovery_context
    entry(context.bibliography, context.user, "Q30000162")
    entry(context.bibliography, context.user, "Q30000163")
    original_persist = identity_module.update_identity_fields_only
    persist_calls = {"count": 0}

    def introduce_redirect_race(identity, entry_, current_user, stored_entry):
        if persist_calls["count"] == 0:
            persist_calls["count"] += 1
            context.database["bibliography"].update_one(
                {"_id": "Q30000163"},
                {"$set": {"deprecated": True, "redirectTo": "Q30000162"}},
            )
        return original_persist(identity, entry_, current_user, stored_entry)

    def fail_release(_owner):
        raise RuntimeError("release failed")

    monkeypatch.setattr(
        identity_module, "update_identity_fields_only", introduce_redirect_race
    )
    monkeypatch.setattr(
        context.bibliography_repository,
        "release_pending_lookup_values",
        fail_release,
    )

    with caplog.at_level(logging.ERROR), pytest.raises(BibliographyUpdateConflictError):
        context.identity_management.manage_identity(
            "Q30000162", {"deprecateTo": "Q30000163"}, context.user
        )

    assert "deprecated" not in stored(context.database, "Q30000162")
    assert "release failed" in caplog.text
