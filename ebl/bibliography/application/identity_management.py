import logging
from typing import Any, Mapping

from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_identity_fields_only,
)
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    BibliographyUpdateConflictError,
)
from ebl.bibliography.application.identity_state import apply_identity_commands
from ebl.bibliography.application.identity_validation import validate_identity_state
from ebl.changelog import Changelog
from ebl.errors import DataError, NotFoundError
from ebl.users.domain.user import User


class BibliographyIdentityManagement:
    def __init__(
        self,
        repository: BibliographyRepository,
        changelog: Changelog,
    ):
        self._repository = repository
        self._identity = BibliographyIdentityContext(repository, changelog)

    def manage_identity(
        self, id_: str, commands: Mapping[str, Any], user: User
    ) -> dict[str, Any]:
        stored_entry = self._stored_entry(id_)
        entry = apply_identity_commands(stored_entry, commands)
        self._validate(entry)

        if entry != stored_entry:
            reservation_owner = update_identity_fields_only(
                self._identity, entry, user, stored_entry
            )
            self._reject_concurrent_redirect_break(
                entry, stored_entry, user, reservation_owner
            )

        return self._stored_entry(id_)

    def _stored_entry(self, id_: str) -> dict[str, Any]:
        try:
            return self._repository.query_by_id(id_)
        except NotFoundError:
            raise NotFoundError(f"Bibliography entry {id_} not found.") from None

    def _validate(self, entry: Mapping[str, Any]) -> None:
        validate_identity_state(
            entry,
            self._repository.query_by_id,
            self._repository.query_by_redirect_target,
        )

    def _reject_concurrent_redirect_break(
        self,
        entry: dict[str, Any],
        stored_entry: dict[str, Any],
        user: User,
        reservation_owner: str,
    ) -> None:
        try:
            self._validate(entry)
        except DataError as validation_error:
            try:
                update_identity_fields_only(self._identity, stored_entry, user, entry)
                self._repository.release_pending_lookup_values(reservation_owner)
            except Exception:
                logging.exception(
                    "Failed to fully recover bibliography identity write for %s "
                    "after post-write redirect validation failed (%s)",
                    entry["id"],
                    validation_error,
                )
            raise BibliographyUpdateConflictError(entry["id"]) from validation_error
