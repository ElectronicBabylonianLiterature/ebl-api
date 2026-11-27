from typing import Mapping, Sequence, cast

from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.signs.application.mes_zl_kap2_repository import MesZlKap2Repository
from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry
from ebl.signs.infrastructure.mes_zl_kap2_schemas import MesZlKap2DocumentSchema

COLLECTION = "meszl_kap2"


def load_entry(document: Mapping) -> MesZlKap2Entry:
    return cast(MesZlKap2Entry, MesZlKap2DocumentSchema().load(document))


class MongoMesZlKap2Repository(MesZlKap2Repository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def find_by_numbers(self, numbers: Sequence[str]) -> Sequence[MesZlKap2Entry]:
        keys = list(dict.fromkeys(numbers))
        if not keys:
            return []
        entries_by_key: dict[str, MesZlKap2Entry] = {}
        for document in self._collection.find_many(
            {"$or": [{"_id": {"$in": keys}}, {"aliases": {"$in": keys}}]}
        ):
            entry = load_entry(document)
            for key in [document["_id"], *document["aliases"]]:
                entries_by_key[key] = entry
        unique: dict[str, MesZlKap2Entry] = {}
        for key in keys:
            if key in entries_by_key:
                unique.setdefault(entries_by_key[key].number, entries_by_key[key])
        return list(unique.values())
