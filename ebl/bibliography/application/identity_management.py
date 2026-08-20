"""The trusted bibliography identity operation.

This is the deliberate replacement for identity mutation through the ordinary
metadata route, which was made metadata-only. It is the only reachable caller
allowed to change `aliases`, `citationKey`, `deprecated` and `redirectTo` on an
existing record.

Ordering is fixed by `update_with_identity_claims` and is not reimplemented
here: validate, claim the new lookup values, persist, commit the claims, retire
the removed ones, write the changelog. This service only decides *what* the new
identity state is and refuses to persist an unacceptable one.

The canonical `_id` is never renamed. The new entry is built from the stored
record, so its id is the loaded one by construction, and the primitive raises
`Defect` if that ever stops holding.
"""

from typing import Any, Callable, Mapping

from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_with_identity_claims,
)
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
)
from ebl.bibliography.application.identity_state import apply_identity_commands
from ebl.bibliography.application.identity_validation import validate_identity_state
from ebl.changelog import Changelog
from ebl.users.domain.user import User


class BibliographyIdentityManagement:
    def __init__(
        self,
        repository: BibliographyRepository,
        changelog: Changelog,
        find: Callable[[str], dict],
    ):
        self._repository = repository
        self._identity = BibliographyIdentityContext(repository, changelog, find)

    def manage_identity(
        self, id_: str, commands: Mapping[str, Any], user: User
    ) -> dict[str, Any]:
        stored_entry = self._repository.query_by_id(id_)
        entry = apply_identity_commands(stored_entry, commands)
        validate_identity_state(entry, self._repository.query_by_id)

        if entry != stored_entry:
            update_with_identity_claims(self._identity, entry, user, stored_entry)

        return entry
