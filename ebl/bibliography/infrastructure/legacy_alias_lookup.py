from typing import Any, Mapping, Sequence

from pymongo.database import Database

from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"
LEGACY_ALIAS_FILTER = {
    "aliases": {
        "$elemMatch": {
            "value": {"$type": "string"},
            "$or": [
                {"normalizedValue": {"$exists": False}},
                {"normalizedValue": None},
                {"normalizedValue": ""},
            ],
        }
    }
}
LEGACY_ALIAS_PROJECTION = {"aliases.value": 1, "aliases.normalizedValue": 1}


class MongoLegacyAliasLookup:
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def owners(self, values: Sequence[str]) -> dict[str, list[str]]:
        normalized_by_value = {value: normalize_partner_id(value) for value in values}
        wanted = {
            normalized for normalized in normalized_by_value.values() if normalized
        }
        if not wanted:
            return {}
        owner_ids = self._owner_ids_by_normalized_alias(wanted)
        return {
            value: owner_ids[normalized]
            for value, normalized in normalized_by_value.items()
            if normalized in owner_ids
        }

    def _owner_ids_by_normalized_alias(self, wanted: set[str]) -> dict[str, list[str]]:
        owner_ids: dict[str, list[str]] = {}
        for entry in self._collection.find_many(
            LEGACY_ALIAS_FILTER, LEGACY_ALIAS_PROJECTION
        ):
            for normalized in legacy_normalized_aliases(entry) & wanted:
                owner_ids.setdefault(normalized, []).append(entry["_id"])
        return owner_ids


def legacy_normalized_aliases(entry: Mapping[str, Any]) -> set[str]:
    return {
        normalize_partner_id(alias["value"])
        for alias in entry.get("aliases", [])
        if _is_legacy_alias(alias)
    }


def _is_legacy_alias(alias: object) -> bool:
    return (
        isinstance(alias, Mapping)
        and not alias.get("normalizedValue")
        and isinstance(alias.get("value"), str)
    )
