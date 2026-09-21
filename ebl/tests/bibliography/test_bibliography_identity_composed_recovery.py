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
    alias,
    entry,
    stored,
)


@pytest.fixture
def identity_management(bibliography_repository, changelog):
    return BibliographyIdentityManagement(bibliography_repository, changelog)


def test_failed_commit_then_redirect_race_releases_forward_alias_claim(
    monkeypatch,
    bibliography,
    bibliography_repository,
    database,
    identity_management,
    user,
):
    source = entry(bibliography, user, "Q30000160")
    entry(bibliography, user, "Q30000161")
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
        identity_management.manage_identity(
            source["id"],
            {
                "addAliases": [alias("composed-recovery-alias")],
                "deprecateTo": "Q30000161",
            },
            user,
        )

    assert bibliography_repository.query_by_id(source["id"]) == source
    assert stored(database, source["id"]).get("redirectTo") is None
    assert released_owners == [forward_owner["value"]]
    assert database[RESERVATIONS].find_one({"_id": "composed-recovery-alias"}) is None
    assert not bibliography_repository.lookup_value_is_reserved(
        "composed-recovery-alias"
    )
