from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

import pymongo

from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    BibliographyUpdateConflictError,
)
from ebl.bibliography.application.duplicate_audit import PROJECTION
from ebl.bibliography.application.lookup_reservation import LookupReservationOperation
from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.bibliography.application.serialization import (
    create_mongo_entry,
    create_object_entry,
)
from ebl.bibliography.infrastructure.bibliography_queries import (
    ACTIVE_BIBLIOGRAPHY_FILTER,
    author_year_title_match,
    bibliography_query_pipeline,
    server_owned_state_filter,
)
from ebl.bibliography.infrastructure.duplicate_candidate_queries import (
    duplicate_candidate_queries,
)
from ebl.bibliography.infrastructure.lookup_reservations import MongoLookupReservations
from ebl.bibliography.infrastructure.reference_documents import join_reference_documents
from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"
DUPLICATE_CANDIDATE_QUERY_MAX_TIME_MS = 5000
ALIASES_VALUE_FIELD = "aliases.value"
__all__ = ["MongoBibliographyRepository", "join_reference_documents"]


class MongoBibliographyRepository(BibliographyRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)
        self._lookup_reservations = MongoLookupReservations(database)

    def create_indexes(self) -> None:
        self._collection.create_index([("citationKey", pymongo.ASCENDING)])
        self._collection.create_index([(ALIASES_VALUE_FIELD, pymongo.ASCENDING)])
        self._collection.create_index([("aliases.normalizedValue", pymongo.ASCENDING)])
        self._lookup_reservations.create_indexes()

    def claim_lookup_values(
        self, operation: LookupReservationOperation, values: Sequence[str]
    ) -> None:
        now = datetime.now(timezone.utc)
        self.reconcile_lookup_reservations(now)
        self._lookup_reservations.claim(
            operation, values, now, self._entry_owns_lookup_value
        )

    def commit_lookup_values(
        self, operation: LookupReservationOperation, now: datetime
    ) -> None:
        self._lookup_reservations.commit(operation, now)

    def release_pending_lookup_values(self, owner: str) -> None:
        self._lookup_reservations.release_pending(owner)

    def retire_lookup_values(
        self, entry_id: str, values: Sequence[str], now: datetime
    ) -> None:
        self._lookup_reservations.retire(entry_id, values, now)

    def lookup_value_is_reserved(self, value: str) -> bool:
        return self._lookup_reservations.is_active(
            value, datetime.now(timezone.utc), self._entry_owns_lookup_value
        )

    def reconcile_lookup_reservations(self, now: datetime, limit: int = 100) -> int:
        return self._lookup_reservations.reconcile(
            now, self._entry_owns_lookup_value, limit
        )

    def create(self, entry) -> str:
        mongo_entry = create_mongo_entry(entry)
        return self._collection.insert_one(mongo_entry)

    def query_by_id(self, id_: str) -> dict:
        data = self._collection.find_one_by_id(id_)
        return create_object_entry(data)

    def query_by_citation_key(self, citation_key: str) -> dict:
        data = list(self._collection.find_many({"citationKey": citation_key}).limit(2))
        if not data:
            raise NotFoundError(f"bibliography citation key {citation_key} not found.")
        if len(data) > 1:
            raise DuplicateError(
                f"bibliography citation key {citation_key} is ambiguous."
            )
        return create_object_entry(data[0])

    def query_by_alias(self, alias: str) -> dict:
        normalized_alias = normalize_partner_id(alias)
        query: Dict[str, Any] = {ALIASES_VALUE_FIELD: alias}
        if normalized_alias:
            query = {
                "$or": [
                    {ALIASES_VALUE_FIELD: alias},
                    {"aliases.normalizedValue": normalized_alias},
                ]
            }
        data = list(self._collection.find_many(query))
        if not data:
            raise NotFoundError(f"bibliography alias {alias} not found.")
        if len({item["_id"] for item in data}) > 1:
            raise DuplicateError(f"bibliography alias {alias} is ambiguous.")
        return create_object_entry(data[0])

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[dict]:
        data = self._collection.find_many({"_id": {"$in": ids}})
        return [create_object_entry(item) for item in data]

    def update(self, entry, expected_server_owned_fields: Mapping[str, Any]) -> None:
        mongo_entry = create_mongo_entry(entry)
        id_ = mongo_entry["_id"]
        try:
            self._collection.replace_one(
                mongo_entry,
                filter_=server_owned_state_filter(id_, expected_server_owned_fields),
            )
        except NotFoundError as error:
            if not self._collection.exists({"_id": id_}):
                raise
            raise BibliographyUpdateConflictError(id_) from error

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[dict]:
        return self._query(
            author_year_title_match(author, year, title),
            trailing_sort_field="title",
        )

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if container_title_short:
            match["container-title-short"] = container_title_short
        if collection_number:
            match["collection-number"] = collection_number
        return self._query(match, trailing_sort_field="collection-title")

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if title_short:
            match["title-short"] = title_short
        if volume:
            match["volume"] = volume
        return self._query(match, trailing_sort_field="collection-title")

    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        candidates: dict[str, dict] = {}
        for query in duplicate_candidate_queries(entry):
            cursor = self._collection.find_many(
                {"$and": [query, ACTIVE_BIBLIOGRAPHY_FILTER]}, projection=PROJECTION
            ).max_time_ms(DUPLICATE_CANDIDATE_QUERY_MAX_TIME_MS)
            for data in cursor.limit(limit):
                candidates[data["_id"]] = create_object_entry(data)
        return list(candidates.values())[:limit]

    def query_page(self, after: Optional[str], limit: int) -> Sequence[Any]:
        query: Dict[str, Any] = dict(ACTIVE_BIBLIOGRAPHY_FILTER)
        if after:
            query["_id"] = {"$gt": after}
        data = self._collection.find_many(query).sort("_id", 1).limit(limit)
        return [create_object_entry(item) for item in data]

    def _query(self, match: Dict[str, Any], trailing_sort_field: str) -> Sequence[dict]:
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                bibliography_query_pipeline(match, trailing_sort_field),
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def list_all_bibliography(self) -> Sequence[str]:
        return self._collection.get_all_values("_id", ACTIVE_BIBLIOGRAPHY_FILTER)

    def _entry_owns_lookup_value(self, entry_id: str, value: str) -> bool:
        if entry_id == value and self._collection.exists({"_id": entry_id}):
            return True

        normalized_value = normalize_partner_id(value)
        lookup_query: Dict[str, Any] = {
            "$or": [
                {"citationKey": value},
                {ALIASES_VALUE_FIELD: value},
            ]
        }
        if normalized_value:
            lookup_query["$or"].append({"aliases.normalizedValue": normalized_value})

        matching_ids = self._collection.get_all_values("_id", lookup_query)
        return matching_ids == [entry_id]
