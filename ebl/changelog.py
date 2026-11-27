import datetime

import bson
import dictdiffer
from bson import ObjectId
from pymongo.common import MAX_BSON_SIZE

from ebl.mongo_collection import MongoCollection


def create_entry(user_profile: dict, resource_type, resource_id, diff) -> dict:
    return {
        "user_profile": {
            key.replace(".", "_"): value for key, value in user_profile.items()
        },
        "resource_type": resource_type,
        "resource_id": resource_id,
        "date": datetime.datetime.utcnow().isoformat(),
        "diff": diff,
    }


def is_storable(entry: dict) -> bool:
    return len(bson.encode({"_id": ObjectId(), **entry})) <= MAX_BSON_SIZE


class Changelog:
    def __init__(self, database):
        self._collection = MongoCollection(database, "changelog")

    def create(self, resource_type, user_profile, old, new):
        return self.insert(
            create_entry(
                user_profile, resource_type, old["_id"], list(dictdiffer.diff(old, new))
            )
        )

    def insert(self, entry: dict) -> ObjectId:
        return self._collection.insert_one(entry)
