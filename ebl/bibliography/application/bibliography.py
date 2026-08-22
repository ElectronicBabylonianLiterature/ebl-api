from typing import Any, Mapping, Optional, Sequence

import attr
from pydash import uniq_with

from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    BibliographyUpdateConflictError,
)
from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    create_with_identity_claims,
    update_with_identity_claims,
)
from ebl.bibliography.application.partner_bibliography import PartnerBibliography
from ebl.bibliography.application.redirect_resolution import (
    follow_bibliography_redirect,
)
from ebl.bibliography.application.search_queries import (
    parse_author_year_and_title,
    parse_container_title_short_and_collection_number,
    parse_title_short_and_volume,
)
from ebl.bibliography.application.server_owned_fields import (
    changed_server_owned_fields,
    preserve_persisted_fields,
    reject_submitted_server_owned_fields,
)
from ebl.bibliography.domain.reference import BibliographyId, Reference
from ebl.changelog import Changelog
from ebl.errors import DataError, NotFoundError
from ebl.users.domain.user import User


class Bibliography:
    def __init__(self, repository: BibliographyRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog
        self._partner = PartnerBibliography(self, repository)
        self._identity = BibliographyIdentityContext(repository, changelog, self.find)

    def create(self, entry, user: User) -> str:
        """Create an entry, claiming whatever identity state it carries.

        Trusted internal caller path, mirroring `update`: the identity fields
        are taken as given because the caller (`PartnerBibliography`) built
        them server-side. Client submissions go through `create_metadata`.
        """
        return create_with_identity_claims(self._identity, entry, user)

    def create_metadata(self, entry: dict, user: User) -> str:
        """Create an entry on behalf of a client.

        Identity state has a dedicated trusted operation, so a submitted
        server-owned field is refused here rather than silently dropped.
        """
        reject_submitted_server_owned_fields(entry)
        return self.create(entry, user)

    def find(self, id_: str):
        for query in (
            self._repository.query_by_id,
            self._repository.query_by_citation_key,
            self._repository.query_by_alias,
        ):
            try:
                result = query(id_)
            except NotFoundError:
                continue
            return self._follow_redirect(result)
        raise NotFoundError(f"bibliography {id_} not found.")

    def find_many(self, ids: Sequence[str]):
        resolved_entries: list[dict] = []
        seen_ids: set[str] = set()
        for entry in self._repository.query_by_ids(ids):
            resolved_entry = self._follow_redirect(entry)
            resolved_id = resolved_entry["id"]
            if resolved_id not in seen_ids:
                resolved_entries.append(resolved_entry)
                seen_ids.add(resolved_id)
        return resolved_entries

    def _follow_redirect(self, entry: dict) -> dict:
        return follow_bibliography_redirect(entry, self._repository.query_by_id)

    def update(self, entry: dict, user: User) -> None:
        """Edit the metadata of an entry, keeping its persisted identity state.

        Trusted internal caller path: submitted server-owned fields are ignored
        rather than rejected, because the caller (`PartnerBibliography`) has
        already screened them out and rebuilt the entry from stored state.
        """
        stored_entry = self._stored_entry_for_update(entry)
        self._persist_update(entry, stored_entry, user)

    def update_metadata(self, entry: dict, user: User) -> None:
        """Edit the metadata of an entry on behalf of a client.

        Same persistence as `update`, but a submitted server-owned field that
        disagrees with stored state is reported as a conflict instead of being
        silently dropped.
        """
        stored_entry = self._stored_entry_for_update(entry)
        self._reject_changed_server_owned_fields(entry, stored_entry)
        self._persist_update(entry, stored_entry, user)

    def _persist_update(self, entry: dict, stored_entry: dict, user: User) -> None:
        update_with_identity_claims(
            self._identity,
            preserve_persisted_fields(entry, stored_entry),
            user,
            stored_entry,
        )

    @staticmethod
    def _reject_changed_server_owned_fields(entry: dict, stored_entry: dict) -> None:
        if changed_fields := changed_server_owned_fields(entry, stored_entry):
            raise BibliographyUpdateConflictError(stored_entry["id"], changed_fields)

    def _stored_entry_for_update(self, entry: dict) -> dict:
        id_ = entry.get("id")
        if not isinstance(id_, str) or not id_:
            raise DataError("Bibliography entry id is required.")
        stored_entry = self._repository.query_by_id(id_)
        if stored_entry.get("deprecated"):
            raise DataError(
                f"Bibliography entry {id_} is deprecated; "
                f"edit {stored_entry.get('redirectTo')} instead."
            )
        return stored_entry

    def search(self, query: str) -> Sequence[dict]:
        author_query_result: Sequence[dict] = []
        author_query = parse_author_year_and_title(query)
        if any(value is not None for value in author_query.values()):
            author_query_result = self.search_author_year_and_title(
                author_query["author"], author_query["year"], author_query["title"]
            )

        container_query_result: Sequence[dict] = []
        container_query = parse_container_title_short_and_collection_number(query)
        if any(value is not None for value in list(container_query.values())):
            container_query_result = self.search_container_title_and_collection_number(
                container_query["container_title_short"],
                container_query["collection_number"],
            )

        title_short_volume_result: Sequence[dict] = []
        title_short_volume_query = parse_title_short_and_volume(query)
        if any(value is not None for value in list(title_short_volume_query.values())):
            title_short_volume_result = self.search_title_short_and_volume(
                title_short_volume_query["title_short"],
                title_short_volume_query["volume"],
            )
        results = uniq_with(
            [*author_query_result, *container_query_result, *title_short_volume_result],
            lambda a, b: a == b,
        )
        return [entry for entry in results if not entry.get("deprecated", False)]

    def list_all_bibliography(self) -> Sequence[str]:
        return self._repository.list_all_bibliography()

    def find_duplicate_candidates(self, entry: dict, limit: int = 10) -> dict:
        return (
            BibliographyDuplicateDetector(self._repository)
            .find_candidates(entry, limit)
            .to_dict()
        )

    def create_partner_entry(self, entry: dict, user: User) -> Optional[dict]:
        return self._partner.create_entry(entry, user)

    def create_partner_entry_with_duplicate_override(
        self, entry: dict, override: Mapping[str, Any], user: User
    ) -> None:
        self._partner.create_entry_with_duplicate_override(entry, override, user)

    def update_partner_entry(self, id_: str, entry: dict, user: User) -> Optional[dict]:
        return self._partner.update_entry(id_, entry, user)

    def export_page(self, cursor: Optional[str] = None, limit: int = 50) -> dict:
        return self._partner.export_page(cursor, limit)

    def find_partner_entry(self, id_: str) -> dict:
        return self._partner.find_entry(id_)

    def search_author_year_and_title(
        self,
        author: Optional[str] = None,
        year: Optional[int] = None,
        title: Optional[str] = None,
    ) -> Sequence[dict]:
        return self._repository.query_by_author_year_and_title(author, year, title)

    def search_container_title_and_collection_number(
        self,
        container_title: Optional[str] = None,
        collection_number: Optional[str] = None,
    ) -> Sequence[dict]:
        return self._repository.query_by_container_title_and_collection_number(
            container_title, collection_number
        )

    def search_title_short_and_volume(
        self,
        title_short: Optional[str] = None,
        volume: Optional[str] = None,
    ) -> Sequence[dict]:
        return self._repository.query_by_title_short_and_volume(title_short, volume)

    def canonicalize_references(
        self, references: Sequence[Reference]
    ) -> tuple[Reference, ...]:
        canonical_references: list[Reference] = []
        invalid_references: list[str] = []

        for reference in references:
            try:
                entry = self.find(reference.id)
            except NotFoundError:
                invalid_references.append(reference.id)
            else:
                canonical_references.append(
                    attr.evolve(reference, id=BibliographyId(entry["id"]))
                )

        if invalid_references:
            raise DataError(
                f"Unknown bibliography entries: {', '.join(invalid_references)}."
            )

        return tuple(canonical_references)
