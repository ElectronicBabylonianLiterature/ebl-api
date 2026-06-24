import re
from typing import Any, Mapping, Optional, Sequence

from pydash import uniq_with

from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)
from ebl.bibliography.application.duplicate_override import (
    BLOCKING_DUPLICATE_DECISIONS,
    DuplicateOverrideError,
    validate_duplicate_override,
)
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.bibliography.domain.reference import Reference
from ebl.changelog import Changelog
from ebl.errors import DataError, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"
DEFAULT_EXPORT_LIMIT = 50
MAX_EXPORT_LIMIT = 100


class Bibliography:
    def __init__(self, repository: BibliographyRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog

    def create(self, entry, user: User) -> str:
        self._changelog.create(
            COLLECTION, user.profile, {"_id": entry["id"]}, create_mongo_entry(entry)
        )
        return self._repository.create(entry)

    def find(self, id_: str):
        return self._repository.query_by_id(id_)

    def find_many(self, ids: Sequence[str]):
        return self._repository.query_by_ids(ids)

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
        return uniq_with(
            [*author_query_result, *container_query_result, *title_short_volume_result],
            lambda a, b: a == b,
        )

    def list_all_bibliography(self) -> Sequence[str]:
        return self._repository.list_all_bibliography()

    def find_duplicate_candidates(self, entry: dict, limit: int = 10) -> dict:
        return (
            BibliographyDuplicateDetector(self._repository)
            .find_candidates(entry, limit)
            .to_dict()
        )

    def create_partner_entry(self, entry: dict, user: User) -> Optional[dict]:
        if duplicate_result := self.find_blocking_duplicate_candidates(entry):
            return duplicate_result
        self.create(entry, user)
        return None

    def create_partner_entry_with_duplicate_override(
        self, entry: dict, override: Mapping[str, Any], user: User
    ) -> None:
        duplicate_result = self.find_duplicate_candidates(entry)
        if duplicate_result["decision"] not in BLOCKING_DUPLICATE_DECISIONS:
            raise DuplicateOverrideError(
                "No current duplicate candidates were found. "
                "Use POST /api/v1/bibliography instead."
            )
        validate_duplicate_override(override, duplicate_result)
        self.create(entry, user)

    def update_partner_entry(self, id_: str, entry: dict, user: User) -> Optional[dict]:
        updated_entry = {**entry, "id": id_}
        if duplicate_result := self.find_blocking_duplicate_candidates(updated_entry):
            return duplicate_result
        self.update(updated_entry, user)
        return None

    def find_blocking_duplicate_candidates(self, entry: dict) -> Optional[dict]:
        duplicate_result = self.find_duplicate_candidates(entry)
        return (
            duplicate_result
            if duplicate_result["decision"] in BLOCKING_DUPLICATE_DECISIONS
            else None
        )

    def export_page(
        self, cursor: Optional[str] = None, limit: int = DEFAULT_EXPORT_LIMIT
    ) -> dict:
        result_limit = max(1, min(limit, MAX_EXPORT_LIMIT))
        entries = list(self._repository.query_page(cursor, result_limit + 1))
        items = entries[:result_limit]
        return {
            "items": [partner_bibliography_entry(entry) for entry in items],
            "nextCursor": items[-1]["id"] if len(entries) > result_limit else None,
            "limit": result_limit,
        }

    def find_partner_entry(self, id_: str) -> dict:
        return partner_bibliography_entry(self.find(id_))

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
        def is_invalid(reference):
            try:
                self.find(reference.id)
                return False
            except NotFoundError:
                return True

        invalid_references = [
            reference.id for reference in references if is_invalid(reference)
        ]
        if invalid_references:
            raise DataError(
                f"Unknown bibliography entries: {', '.join(invalid_references)}."
            )


def partner_bibliography_entry(entry: Mapping[str, Any]) -> dict:
    return {
        "id": entry["id"],
        "citationKey": entry.get("citationKey"),
        "bibliographyEntry": dict(entry),
    }
