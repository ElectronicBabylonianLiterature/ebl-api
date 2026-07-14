from typing import Any, Mapping, Optional, Protocol

import jsonschema

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.duplicate_override import (
    BLOCKING_DUPLICATE_DECISIONS,
    DuplicateOverrideError,
    validate_duplicate_override,
)
from ebl.bibliography.application.partner_identity import (
    create_partner_alias,
    generate_partner_citation_key,
    select_canonical_bibliography_id,
)
from ebl.bibliography.domain.bibliography_entry import (
    CSL_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)
from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.users.domain.user import User

DEFAULT_EXPORT_LIMIT = 50
MAX_EXPORT_LIMIT = 100
PARTNER_CREATE_RETRY_LIMIT = 5
PARTNER_METADATA_FIELDS = frozenset(CSL_JSON_SCHEMA["properties"]) - (
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS | {"id"}
)


class BibliographyCore(Protocol):
    def create(self, entry, user: User) -> str:
        ...

    def update(self, entry, user: User):
        ...

    def find(self, id_: str):
        ...

    def find_duplicate_candidates(self, entry: dict, limit: int = 10) -> dict:
        ...


class PartnerBibliography:
    def __init__(
        self, bibliography: BibliographyCore, repository: BibliographyRepository
    ):
        self._bibliography = bibliography
        self._repository = repository

    def create_entry(self, entry: dict, user: User) -> Optional[dict]:
        prepared_entry = self._prepare_entry(entry)
        if duplicate_result := self._find_blocking_duplicate_candidates(
            prepared_entry
        ):
            return duplicate_result
        self._create_prepared_entry(entry, prepared_entry, user)
        return None

    def create_entry_with_duplicate_override(
        self, entry: dict, override: Mapping[str, Any], user: User
    ) -> None:
        prepared_entry = self._prepare_entry(entry)
        duplicate_result = self._bibliography.find_duplicate_candidates(prepared_entry)
        if duplicate_result["decision"] not in BLOCKING_DUPLICATE_DECISIONS:
            raise DuplicateOverrideError(
                "No current duplicate candidates were found. "
                "Use POST /api/v1/bibliography instead."
            )
        validate_duplicate_override(override, duplicate_result)
        self._create_prepared_entry(entry, prepared_entry, user)

    def update_entry(self, id_: str, entry: dict, user: User) -> Optional[dict]:
        self._reject_server_owned_fields(entry)
        stored_entry = self._bibliography.find(id_)
        updated_entry = {
            "id": stored_entry["id"],
            **self._project_metadata(entry),
            **{
                field: stored_entry[field]
                for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
                if field in stored_entry
            },
        }
        self._validate_internal_entry(updated_entry)
        if duplicate_result := self._find_blocking_duplicate_candidates(updated_entry):
            return duplicate_result
        self._bibliography.update(updated_entry, user)
        return None

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

    def find_entry(self, id_: str) -> dict:
        return partner_bibliography_entry(self._bibliography.find(id_))

    def _find_blocking_duplicate_candidates(self, entry: dict) -> Optional[dict]:
        duplicate_result = self._bibliography.find_duplicate_candidates(entry)
        return (
            duplicate_result
            if duplicate_result["decision"] in BLOCKING_DUPLICATE_DECISIONS
            else None
        )

    def _prepare_entry(self, entry: Mapping[str, Any]) -> dict:
        self._reject_server_owned_fields(entry)
        submitted_partner_id = entry.get("id")
        reserved_values = (
            [submitted_partner_id] if isinstance(submitted_partner_id, str) else []
        )
        prepared_entry = self._project_metadata(entry)
        prepared_entry["id"] = select_canonical_bibliography_id(
            self._repository.list_all_bibliography(),
            self._lookup_value_exists,
            reserved_values,
        )
        if isinstance(submitted_partner_id, str):
            self._ensure_lookup_value_available(submitted_partner_id)
            prepared_entry["aliases"] = [create_partner_alias(submitted_partner_id)]

        citation_key = generate_partner_citation_key(
            prepared_entry, self._lookup_value_exists
        )
        if citation_key is not None:
            prepared_entry["citationKey"] = citation_key
        self._validate_internal_entry(prepared_entry)
        return prepared_entry

    def _create_prepared_entry(
        self, original_entry: dict, prepared_entry: dict, user: User
    ) -> None:
        pending_entry = dict(prepared_entry)
        reserved_values = (
            [original_entry["id"]] if isinstance(original_entry.get("id"), str) else []
        )
        for _ in range(PARTNER_CREATE_RETRY_LIMIT):
            try:
                self._bibliography.create(pending_entry, user)
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
            self._bibliography.find(value)
        except NotFoundError:
            return False
        except DuplicateError:
            return True
        return True

    def _ensure_lookup_value_available(self, value: str) -> None:
        if self._lookup_value_exists(value):
            raise DuplicateError(f"Partner bibliography id {value} is already in use.")

    @staticmethod
    def _project_metadata(entry: Mapping[str, Any]) -> dict:
        return {key: entry[key] for key in PARTNER_METADATA_FIELDS if key in entry}

    @staticmethod
    def _reject_server_owned_fields(entry: Mapping[str, Any]) -> None:
        forbidden_fields = sorted(SERVER_OWNED_BIBLIOGRAPHY_FIELDS.intersection(entry))
        if forbidden_fields:
            raise DataError(
                "Partner bibliography payload may not include server-owned fields: "
                f"{', '.join(forbidden_fields)}."
            )

    @staticmethod
    def _validate_internal_entry(entry: Mapping[str, Any]) -> None:
        try:
            jsonschema.validate(entry, CSL_JSON_SCHEMA)
        except jsonschema.ValidationError as error:
            raise DataError(error.message) from error


def partner_bibliography_entry(entry: Mapping[str, Any]) -> dict:
    return {
        "id": entry["id"],
        "citationKey": entry.get("citationKey"),
        "bibliographyEntry": dict(entry),
    }
