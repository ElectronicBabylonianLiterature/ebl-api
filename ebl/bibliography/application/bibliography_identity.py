from datetime import datetime, timezone
from typing import Any, Callable

from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    LookupValueInUseError,
)
from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.lookup_reservation import (
    new_lookup_reservation_operation,
)
from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.changelog import Changelog
from ebl.errors import Defect, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"


def identity_values(entry: dict[str, Any]) -> set[str]:
    return set(bibliography_lookup_values(entry))


def create_with_identity_claims(
    repository: BibliographyRepository,
    changelog: Changelog,
    find: Callable[[str], dict],
    entry: dict[str, Any],
    user: User,
) -> str:
    now = datetime.now(timezone.utc)
    operation = new_lookup_reservation_operation(entry["id"], now)
    created = False
    try:
        repository.claim_lookup_values(operation, bibliography_lookup_values(entry))
        ensure_lookup_values_available(find, entry)
        created_id = repository.create(entry)
        created = True
        if created_id != entry["id"]:
            raise Defect(
                f"Created bibliography id {created_id} does not match {entry['id']}."
            )
        repository.commit_lookup_values(operation, datetime.now(timezone.utc))
        changelog.create(
            COLLECTION, user.profile, {"_id": entry["id"]}, create_mongo_entry(entry)
        )
        return created_id
    except Exception:
        if not created:
            repository.release_pending_lookup_values(operation.owner)
        raise


def update_with_identity_claims(
    repository: BibliographyRepository,
    changelog: Changelog,
    find: Callable[[str], dict],
    entry: dict[str, Any],
    user: User,
    stored_entry: dict[str, Any] | None = None,
) -> None:
    old_entry = (
        repository.query_by_id(entry["id"]) if stored_entry is None else stored_entry
    )
    old_values = identity_values(old_entry)
    new_values = identity_values(entry)
    values_to_claim = sorted(new_values - old_values)
    values_to_retire = sorted(old_values - new_values)
    now = datetime.now(timezone.utc)
    operation = new_lookup_reservation_operation(entry["id"], now)
    updated = False
    try:
        repository.claim_lookup_values(operation, values_to_claim)
        ensure_lookup_values_available(find, entry, entry["id"])
        repository.update(entry)
        updated = True
        repository.commit_lookup_values(operation, datetime.now(timezone.utc))
        repository.retire_lookup_values(
            entry["id"], values_to_retire, datetime.now(timezone.utc)
        )
        changelog.create(
            COLLECTION,
            user.profile,
            create_mongo_entry(old_entry),
            create_mongo_entry(entry),
        )
    except Exception:
        if not updated:
            repository.release_pending_lookup_values(operation.owner)
        raise


def ensure_lookup_values_available(
    find: Callable[[str], dict], entry: dict[str, Any], allowed_id: str | None = None
) -> None:
    for value in bibliography_lookup_values(entry):
        try:
            existing_entry = find(value)
        except NotFoundError:
            continue
        if allowed_id is None or existing_entry["id"] != allowed_id:
            raise LookupValueInUseError(value)
