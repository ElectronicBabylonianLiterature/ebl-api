from typing import Any, Mapping

from pymongo.database import Database

from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.bibliography.application.serialization import create_object_entry
from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"


class MongoLegacyAliasLookup:
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def query(self, alias: str) -> dict[str, Any]:
        normalized_alias = normalize_partner_id(alias)
        matches = [
            entry
            for entry in self._collection.find_many(
                {
                    "aliases": {
                        "$elemMatch": {
                            "$or": [
                                {"normalizedValue": {"$exists": False}},
                                {"normalizedValue": None},
                                {"normalizedValue": ""},
                            ],
                        }
                    }
                }
            )
            if self._matches(entry, normalized_alias)
        ]
        if not matches:
            raise NotFoundError(f"legacy bibliography alias {alias} not found.")
        if len(matches) > 1:
            raise DuplicateError(f"legacy bibliography alias {alias} is ambiguous.")
        return create_object_entry(matches[0])

    @staticmethod
    def _matches(entry: Mapping[str, Any], normalized_alias: str) -> bool:
        if not normalized_alias:
            return False
        return any(
            MongoLegacyAliasLookup._alias_matches(stored_alias, normalized_alias)
            for stored_alias in entry.get("aliases", [])
        )

    @staticmethod
    def _alias_matches(stored_alias: object, normalized_alias: str) -> bool:
        if not isinstance(stored_alias, Mapping):
            return False
        if stored_alias.get("normalizedValue"):
            return False
        value = stored_alias.get("value")
        if not isinstance(value, str):
            return False
        return normalize_partner_id(value) == normalized_alias
