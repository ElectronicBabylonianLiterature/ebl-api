import re
from typing import Any, Mapping, Optional, Sequence

from pydash import uniq_with

from ebl.bibliography.application.partner_identity import (
    create_partner_alias,
    generate_partner_citation_key,
    select_canonical_bibliography_id,
)
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
from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"
DEFAULT_EXPORT_LIMIT = 50
MAX_EXPORT_LIMIT = 100
PARTNER_CREATE_RETRY_LIMIT = 5
MAX_REDIRECT_DEPTH = 5


class Bibliography:
    def __init__(self, repository: BibliographyRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog

    def create(self, entry, user: User) -> str:
        created_id = self._repository.create(entry)
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
        return [
            self._follow_redirect(entry) for entry in self._repository.query_by_ids(ids)
        ]

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
        prepared_entry = self._prepare_partner_entry(entry)
        if duplicate_result := self.find_blocking_duplicate_candidates(prepared_entry):
            return duplicate_result
        self._create_prepared_partner_entry(entry, prepared_entry, user)
        return None

    def create_partner_entry_with_duplicate_override(
        self, entry: dict, override: Mapping[str, Any], user: User
    ) -> None:
        prepared_entry = self._prepare_partner_entry(entry)
        duplicate_result = self.find_duplicate_candidates(prepared_entry)
        if duplicate_result["decision"] not in BLOCKING_DUPLICATE_DECISIONS:
            raise DuplicateOverrideError(
                "No current duplicate candidates were found. "
                "Use POST /api/v1/bibliography instead."
            )
        validate_duplicate_override(override, duplicate_result)
        self._create_prepared_partner_entry(entry, prepared_entry, user)

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

    def _prepare_partner_entry(self, entry: Mapping[str, Any]) -> dict:
        submitted_partner_id = entry.get("id")
        reserved_values = (
            [submitted_partner_id] if isinstance(submitted_partner_id, str) else []
        )
        prepared_entry = {
            key: value for key, value in entry.items() if key != "citationKey"
        }
        prepared_entry["id"] = select_canonical_bibliography_id(
            self._repository.list_all_bibliography(),
            self._lookup_value_exists,
            reserved_values,
        )
        if isinstance(submitted_partner_id, str):
            self._ensure_lookup_value_available(submitted_partner_id)
            prepared_entry["aliases"] = self._merge_alias(
                entry.get("aliases"),
                create_partner_alias(submitted_partner_id),
            )
        elif "aliases" in entry:
            prepared_entry["aliases"] = list(entry["aliases"])

        citation_key = generate_partner_citation_key(
            prepared_entry, self._lookup_value_exists
        )
        if citation_key is not None:
            prepared_entry["citationKey"] = citation_key
        return prepared_entry

    def _create_prepared_partner_entry(
        self, original_entry: dict, prepared_entry: dict, user: User
    ) -> None:
        pending_entry = dict(prepared_entry)
        reserved_values = (
            [original_entry["id"]] if isinstance(original_entry.get("id"), str) else []
        )
        for _ in range(PARTNER_CREATE_RETRY_LIMIT):
            try:
                self.create(pending_entry, user)
            except DuplicateError:
                pending_entry["id"] = select_canonical_bibliography_id(
                    self._repository.list_all_bibliography(),
                    self._lookup_value_exists,
                    reserved_values,
                )
                continue

            original_entry.clear()
            original_entry.update(pending_entry)
            return

        raise DuplicateError("Unable to generate a unique bibliography id.")

    def _lookup_value_exists(self, value: str) -> bool:
        try:
            self.find(value)
        except NotFoundError:
            return False
        except DuplicateError:
            return True
        return True

    def _ensure_lookup_value_available(self, value: str) -> None:
        if self._lookup_value_exists(value):
            raise DuplicateError(f"Partner bibliography id {value} is already in use.")

    @staticmethod
    def _merge_alias(aliases: Any, alias: dict[str, str]) -> list[dict]:
        existing_aliases = [
            existing_alias
            for existing_alias in aliases or ()
            if existing_alias.get("value") != alias["value"]
        ]
        return [*existing_aliases, alias]

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
