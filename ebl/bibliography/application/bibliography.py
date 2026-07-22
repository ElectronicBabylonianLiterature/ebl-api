import re
from typing import Any, Mapping, Optional, Sequence

import attr
from pydash import uniq_with

from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.partner_bibliography import PartnerBibliography
from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.bibliography.domain.reference import BibliographyId, Reference
from ebl.changelog import Changelog
from ebl.errors import DataError, Defect, DuplicateError, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"
MAX_REDIRECT_DEPTH = 5


class Bibliography:
    def __init__(self, repository: BibliographyRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog
        self._partner = PartnerBibliography(self, repository)

    def create(self, entry, user: User) -> str:
        created_id = self._repository.create(entry)
        if created_id != entry["id"]:
            raise Defect(
                f"Created bibliography id {created_id} does not match {entry['id']}."
            )
        self._changelog.create(
            COLLECTION, user.profile, {"_id": entry["id"]}, create_mongo_entry(entry)
        )
        return created_id

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
        current = entry
        visited_ids: set[str] = set()
        redirects_followed = 0

        while current.get("deprecated", False):
            current_id = current.get("id")
            redirect_to = current.get("redirectTo")
            if not isinstance(redirect_to, str) or not redirect_to:
                raise NotFoundError(
                    f"Deprecated bibliography {current_id} has no redirect target."
                )
            if current_id in visited_ids or redirect_to in visited_ids:
                raise DuplicateError(
                    f"Bibliography redirect loop detected at {current_id}."
                )
            if redirects_followed >= MAX_REDIRECT_DEPTH:
                raise DuplicateError(
                    f"Bibliography redirect from {entry.get('id')} exceeds "
                    f"the maximum depth of {MAX_REDIRECT_DEPTH}."
                )

            if isinstance(current_id, str):
                visited_ids.add(current_id)
            try:
                current = self._repository.query_by_id(redirect_to)
            except NotFoundError as error:
                raise NotFoundError(
                    f"Bibliography redirect target {redirect_to} not found."
                ) from error
            redirects_followed += 1

        return current

    def update(self, entry, user: User):
        old_entry = self._repository.query_by_id(entry["id"])
        self._changelog.create(
            COLLECTION,
            user.profile,
            create_mongo_entry(old_entry),
            create_mongo_entry(entry),
        )
        self._repository.update(entry)

    def search(self, query: str) -> Sequence[dict]:
        author_query_result = []
        author_query = self._parse_author_year_and_title(query)
        if any(value is not None for value in author_query.values()):
            author_query_result = self.search_author_year_and_title(
                author_query["author"], author_query["year"], author_query["title"]
            )

        container_query_result = []
        container_query = self._parse_container_title_short_and_collection_number(query)
        if any(value is not None for value in list(container_query.values())):
            container_query_result = self.search_container_title_and_collection_number(
                container_query["container_title_short"],
                container_query["collection_number"],
            )

        title_short_volume_result = []
        title_short_volume_query = self._parse_title_short_and_volume(query)
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

    @staticmethod
    def _parse_author_year_and_title(query: str) -> dict:
        parsed_query = dict.fromkeys(["author", "year", "title"])
        if match := re.match(r"^([^\d]+)(?: (\d{1,4})(?: (.*))?)?$", query):
            parsed_query["author"] = match[1]
            parsed_query["year"] = int(match[2]) if match[2] else None
            parsed_query["title"] = match[3]
        return parsed_query

    @staticmethod
    def _parse_container_title_short_and_collection_number(query: str) -> dict:
        parsed_query = dict.fromkeys(["container_title_short", "collection_number"])
        if match := re.match(r"^([^\s]+)(?: (\d*))?$", query):
            parsed_query["container_title_short"] = match[1]
            parsed_query["collection_number"] = match[2]
        return parsed_query

    @staticmethod
    def _parse_title_short_and_volume(query: str) -> dict:
        parsed_query = dict.fromkeys(["title_short", "volume"])
        if match := re.match(r"^([^\s]+)(?: (\d*))?$", query):
            parsed_query["title_short"] = match[1]
            parsed_query["volume"] = match[2]
        return parsed_query

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

    def validate_references(self, references: Sequence[Reference]):
        self.canonicalize_references(references)

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
