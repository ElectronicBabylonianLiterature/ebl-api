from typing import Sequence

from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.bibliography.application.serialization import create_object_entry
from ebl.mongo_collection import MongoCollection


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
