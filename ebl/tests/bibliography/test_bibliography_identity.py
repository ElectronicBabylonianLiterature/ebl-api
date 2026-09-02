from typing import Optional

import pytest

from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    create_with_identity_claims,
    update_with_identity_claims,
)
from ebl.bibliography.application.bibliography_repository import LookupValueInUseError
from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.lookup_reservation import LookupReservationOperation
from ebl.errors import Defect, NotFoundError


class ChangelogSpy:
    def create(self, *_args):
        raise AssertionError("changelog should not be created")


class ChangelogNoop:
    def create(self, *_args):
        return None


class RepositorySpy:
    def __init__(self, create_error=None):
        self.create_error = create_error
        self.operation: Optional[LookupReservationOperation] = None
        self.released_owners: list[str] = []

    @property
    def claimed_owner(self) -> str:
        assert self.operation is not None
        return self.operation.owner

    def claim_lookup_values(
        self, operation: LookupReservationOperation, _values
    ) -> None:
        self.operation = operation

    def create(self, _entry):
        if self.create_error:
            raise self.create_error
        return "Q30000000"

    def commit_lookup_values(self, *_args):
        raise AssertionError("claims should not be committed")

    def retire_lookup_values(self, *_args):
        raise AssertionError("claims should not be retired")

    def release_pending_lookup_values(self, owner):
        self.released_owners.append(owner)


def identity_context(repository, changelog, find):
    return BibliographyIdentityContext(repository, changelog, find)


def test_create_releases_claims_when_post_claim_lookup_finds_existing_entry(user):
    repository = RepositorySpy()

    with pytest.raises(LookupValueInUseError):
        create_with_identity_claims(
            identity_context(
                repository, ChangelogSpy(), lambda _value: {"id": "OTHER"}
            ),
            {"id": "Q30000000", "type": "book"},
            user,
        )

    assert repository.released_owners == [repository.claimed_owner]


def test_lookup_values_skip_non_mapping_aliases():
    entry = {
        "id": "Q30000000",
        "aliases": ["legacy-id", {"value": "alias-id", "normalizedValue": "alias-id"}],
    }

    assert bibliography_lookup_values(entry) == ["Q30000000", "alias-id", "alias-id"]


class UpdateRepositorySpy:
    def __init__(self, old_entry, update_error=None):
        self.old_entry = old_entry
        self.update_error = update_error
        self.claimed_values = None
        self.retired_values = None
        self.released_owners = []

    def query_by_id(self, _id):
        return self.old_entry

    def claim_lookup_values(self, _operation, values):
        self.claimed_values = values

    def update(self, _entry, expected_server_owned_fields):
        self.expected_server_owned_fields = expected_server_owned_fields
        if self.update_error:
            raise self.update_error

    def commit_lookup_values(self, *_args):
        return None

    def retire_lookup_values(self, _entry_id, values, _now):
        self.retired_values = values

    def release_pending_lookup_values(self, owner):
        self.released_owners.append(owner)


def missing_lookup(_value):
    raise NotFoundError("missing")


def test_update_claims_added_alias_and_retires_removed_citation_key(user):
    old_entry = {"id": "Q30000000", "type": "book", "citationKey": "old-key"}
    new_entry = {
        "id": "Q30000000",
        "type": "book",
        "aliases": [{"value": "new-alias", "normalizedValue": "new-alias"}],
    }
    repository = UpdateRepositorySpy(old_entry)

    update_with_identity_claims(
        identity_context(repository, ChangelogNoop(), missing_lookup), new_entry, user
    )

    assert repository.claimed_values == ["new-alias"]
    assert repository.retired_values == ["old-key"]


def test_update_failure_releases_new_claims_without_retiring_old_claims(user):
    old_entry = {"id": "Q30000000", "type": "book", "citationKey": "old-key"}
    new_entry = {"id": "Q30000000", "type": "book", "citationKey": "new-key"}
    repository = UpdateRepositorySpy(old_entry, RuntimeError("update failed"))

    with pytest.raises(RuntimeError, match="update failed"):
        update_with_identity_claims(
            identity_context(repository, ChangelogSpy(), missing_lookup),
            new_entry,
            user,
        )

    assert repository.claimed_values == ["new-key"]
    assert repository.retired_values is None
    assert repository.released_owners


def test_create_releases_claims_when_repository_insert_fails(user):
    repository = RepositorySpy(RuntimeError("insert failed"))

    with pytest.raises(RuntimeError, match="insert failed"):
        create_with_identity_claims(
            identity_context(
                repository,
                ChangelogSpy(),
                lambda _value: (_ for _ in ()).throw(NotFoundError("missing")),
            ),
            {"id": "Q30000000", "type": "book"},
            user,
        )

    assert repository.released_owners == [repository.claimed_owner]


def test_update_rejects_a_stored_entry_for_a_different_record(user):
    repository = UpdateRepositorySpy({"id": "OTHER", "type": "book"})

    with pytest.raises(Defect, match="does not match"):
        update_with_identity_claims(
            identity_context(repository, ChangelogSpy(), missing_lookup),
            {"id": "Q30000000", "type": "book"},
            user,
            {"id": "OTHER", "type": "book"},
        )

    assert repository.claimed_values is None
    assert repository.retired_values is None
    assert repository.released_owners == []


def test_update_passes_stored_server_owned_state_to_the_repository(user):
    old_entry = {
        "id": "Q30000000",
        "type": "book",
        "citationKey": "old-key",
        "aliases": [{"value": "old-alias", "normalizedValue": "old-alias"}],
    }
    repository = UpdateRepositorySpy(old_entry)

    update_with_identity_claims(
        identity_context(repository, ChangelogNoop(), missing_lookup),
        {"id": "Q30000000", "type": "book", "citationKey": "new-key"},
        user,
    )

    assert repository.expected_server_owned_fields == {
        "citationKey": "old-key",
        "aliases": [{"value": "old-alias", "normalizedValue": "old-alias"}],
    }
