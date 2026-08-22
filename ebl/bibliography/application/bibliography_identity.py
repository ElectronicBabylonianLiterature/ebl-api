"""Trusted bibliography identity primitives.

`update_with_identity_claims` and `update_identity_fields_only` are the two
paths allowed to change the server-owned identity of an entry: both diff the
lookup values, claim the added ones, retire the removed ones, and recover
reservations when persistence fails. They differ only in what they persist.

`update_with_identity_claims` replaces the whole document. `Bibliography.update`
is the generic CSL metadata editor and deliberately calls it with identity
preserved, so a metadata edit never claims or retires anything; the full
replace is correct there because writing new CSL content is the point.

`update_identity_fields_only` writes just the four identity fields via
`$set`/`$unset`. The trusted identity operation reads a document once, does
further I/O (redirect validation, lookup claims) before it can persist, and
must never let that first read's copy of CSL content overwrite a metadata
edit that lands in between -- a full replace would do exactly that.

Callers that need to mutate identity must supply the new values themselves
rather than routing through the metadata editor.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    LookupValueInUseError,
)
from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.lookup_reservation import (
    new_lookup_reservation_operation,
)
from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.bibliography.application.server_owned_fields import stored_server_owned_fields
from ebl.changelog import Changelog
from ebl.errors import Defect, DuplicateError, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"


@dataclass(frozen=True)
class BibliographyIdentityContext:
    repository: BibliographyRepository
    changelog: Changelog
    find: Callable[[str], dict]


def identity_values(entry: dict[str, Any]) -> set[str]:
    return set(bibliography_lookup_values(entry))


def create_with_identity_claims(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
) -> str:
    repository = context.repository
    now = datetime.now(timezone.utc)
    operation = new_lookup_reservation_operation(entry["id"], now)
    created = False
    try:
        repository.claim_lookup_values(operation, bibliography_lookup_values(entry))
        ensure_lookup_values_available(repository, bibliography_lookup_values(entry))
        created_id = repository.create(entry)
        created = True
        if created_id != entry["id"]:
            raise Defect(
                f"Created bibliography id {created_id} does not match {entry['id']}."
            )
        repository.commit_lookup_values(operation, datetime.now(timezone.utc))
        context.changelog.create(
            COLLECTION, user.profile, {"_id": entry["id"]}, create_mongo_entry(entry)
        )
        return created_id
    except Exception:
        if not created:
            repository.release_pending_lookup_values(operation.owner)
        raise


def _claim_persist_and_record(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    old_entry: dict[str, Any],
    persist: Callable[[dict[str, Any], Mapping[str, Any]], None],
) -> None:
    repository = context.repository
    if old_entry.get("id") != entry["id"]:
        raise Defect(
            f"Stored bibliography {old_entry.get('id')} does not match "
            f"the entry being updated {entry['id']}."
        )
    expected_server_owned_fields = stored_server_owned_fields(old_entry)
    old_values = identity_values(old_entry)
    new_values = identity_values(entry)
    values_to_claim = sorted(new_values - old_values)
    values_to_retire = sorted(old_values - new_values)
    now = datetime.now(timezone.utc)
    operation = new_lookup_reservation_operation(entry["id"], now)
    updated = False
    try:
        repository.claim_lookup_values(operation, values_to_claim)
        ensure_lookup_values_available(repository, values_to_claim, entry["id"])
        persist(entry, expected_server_owned_fields)
        updated = True
        repository.commit_lookup_values(operation, datetime.now(timezone.utc))
        repository.retire_lookup_values(
            entry["id"], values_to_retire, datetime.now(timezone.utc)
        )
        context.changelog.create(
            COLLECTION,
            user.profile,
            create_mongo_entry(old_entry),
            create_mongo_entry(entry),
        )
    except Exception:
        if not updated:
            repository.release_pending_lookup_values(operation.owner)
        raise


def update_with_identity_claims(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any] | None = None,
) -> None:
    old_entry = (
        context.repository.query_by_id(entry["id"])
        if stored_entry is None
        else stored_entry
    )
    _claim_persist_and_record(
        context, entry, user, old_entry, context.repository.update
    )


def update_identity_fields_only(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any],
) -> None:
    _claim_persist_and_record(
        context, entry, user, stored_entry, context.repository.update_identity_fields
    )


def raw_lookup_owner(
    repository: BibliographyRepository, value: str
) -> Optional[dict[str, Any]]:
    """The document that literally stores `value`, without following redirects.

    A deprecated entry's own lookup values stay physically present on its
    document until retired, even though reads resolve it to its redirect
    target. An availability check based on the resolved read would see the
    target as already owning the value and let the target claim it too.
    """
    for query in (
        repository.query_by_id,
        repository.query_by_citation_key,
        repository.query_by_alias,
    ):
        try:
            return query(value)
        except NotFoundError:
            continue
    return None


def ensure_lookup_values_available(
    repository: BibliographyRepository,
    values: Sequence[str],
    allowed_id: str | None = None,
) -> None:
    for value in values:
        try:
            existing_entry = raw_lookup_owner(repository, value)
        except DuplicateError:
            raise LookupValueInUseError(value) from None
        if existing_entry is None:
            continue
        if allowed_id is None or existing_entry["id"] != allowed_id:
            raise LookupValueInUseError(value)
