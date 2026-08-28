"""Trusted bibliography identity primitives."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    LookupValueInUseError,
)
from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
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


def _persist_with_identity_claims(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any],
    persist: Callable[[dict[str, Any], dict[str, Any]], None],
) -> None:
    repository = context.repository
    if stored_entry.get("id") != entry["id"]:
        raise Defect(
            f"Stored bibliography {stored_entry.get('id')} does not match "
            f"the entry being updated {entry['id']}."
        )
    expected_server_owned_fields = stored_server_owned_fields(stored_entry)
    old_values = identity_values(stored_entry)
    new_values = identity_values(entry)
    values_to_claim = sorted(new_values - old_values)
    values_to_retire = sorted(old_values - new_values)
    operation = new_lookup_reservation_operation(
        entry["id"], datetime.now(timezone.utc)
    )
    try:
        repository.claim_lookup_values(operation, values_to_claim)
        ensure_lookup_values_available(repository, values_to_claim, entry["id"])
        persist(entry, expected_server_owned_fields)
    except Exception:
        repository.release_pending_lookup_values(operation.owner)
        raise
    _finalize_identity_write(
        context, operation, entry, stored_entry, values_to_retire, user
    )


def _finalize_identity_write(
    context: BibliographyIdentityContext,
    operation: LookupReservationOperation,
    entry: dict[str, Any],
    stored_entry: dict[str, Any],
    values_to_retire: Sequence[str],
    user: User,
) -> None:
    now = datetime.now(timezone.utc)
    try:
        context.repository.commit_lookup_values(operation, now)
        context.repository.retire_lookup_values(entry["id"], values_to_retire, now)
        context.changelog.create(
            COLLECTION,
            user.profile,
            create_mongo_entry(stored_entry),
            create_mongo_entry(entry),
        )
    except Exception:
        logging.exception(
            "Bibliography identity write for %s persisted but finalization "
            "(lookup-reservation commit / changelog) failed; reservations will "
            "be reconciled and the changelog entry may be missing",
            entry["id"],
        )


def update_with_identity_claims(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any] | None = None,
) -> None:
    resolved_stored_entry: dict[str, Any] = (
        stored_entry
        if stored_entry is not None
        else context.repository.query_by_id(entry["id"])
    )
    _persist_with_identity_claims(
        context, entry, user, resolved_stored_entry, context.repository.update
    )


def update_identity_fields_only(
    context: BibliographyIdentityContext,
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any],
) -> None:
    _persist_with_identity_claims(
        context,
        entry,
        user,
        stored_entry,
        context.repository.update_identity_fields,
    )


def raw_lookup_owner(
    repository: BibliographyRepository, value: str
) -> Optional[dict[str, Any]]:
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
