from typing import Any, Dict, Optional, Sequence

from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.bibliography.application.serialization import create_object_entry
from ebl.mongo_collection import MongoCollection
from ebl.errors import DuplicateError, NotFoundError


def query_by_lookup_values(
    collection: MongoCollection, values: Sequence[str]
) -> Sequence[dict]:
    if not values:
        return []
    normalized = list(
        dict.fromkeys(value for raw in values if (value := normalize_partner_id(raw)))
    )
    data = collection.find_many(
        {
            "$or": [
                {"citationKey": {"$in": list(values)}},
                {"aliases.value": {"$in": list(values)}},
                {"aliases.normalizedValue": {"$in": normalized}},
            ]
        }
    )
    return [create_object_entry(item) for item in data]


def query_by_alias(collection: MongoCollection, alias: str) -> dict:
    normalized_alias = normalize_partner_id(alias)
    query: Dict[str, Any] = {"aliases.value": alias}
    if normalized_alias:
        query = {
            "$or": [
                {"aliases.value": alias},
                {"aliases.normalizedValue": normalized_alias},
            ]
        }
    data = list(collection.find_many(query))
    if not data:
        raise NotFoundError(f"bibliography alias {alias} not found.")
    if len({item["_id"] for item in data}) > 1:
        raise DuplicateError(f"bibliography alias {alias} is ambiguous.")
    return create_object_entry(data[0])


def query_by_redirect_targets(
    collection: MongoCollection, ids: Sequence[str], limit: Optional[int] = None
) -> Sequence[dict]:
    if not ids:
        return []
    data = collection.find_many({"redirectTo": {"$in": list(ids)}})
    if limit is not None:
        data = data.limit(limit)
    return [create_object_entry(item) for item in data]
