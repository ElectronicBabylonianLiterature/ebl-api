import datetime

import dictdiffer

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


class Changelog:
    def __init__(self, database):
        self._collection = MongoCollection(database, "changelog")

    def create(self, resource_type, user_profile, old, new):
        entry = create_entry(
            user_profile, resource_type, old["_id"], list(dictdiffer.diff(old, new))
        )
        return self._collection.insert_one(entry)
