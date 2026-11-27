from typing import Mapping

from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.signs.application.mes_zl_kap2_repository import (
    MesZlKap2Entry,
    MesZlKap2Repository,
    mes_zl_number_variants,
)

COLLECTION = "meszl_kap2"


class MongoMesZlKap2Repository(MesZlKap2Repository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)
        self._raw_collection = database[COLLECTION]

    def find(self, number: str) -> MesZlKap2Entry:
        try:
            document = self._collection.find_one(
                {"_id": {"$in": mes_zl_number_variants(number)}}
            )
        except NotFoundError as error:
            raise NotFoundError(
                f"No MesZL Kapitel II entry for number {number}."
            ) from error
        return MesZlKap2Entry(document["_id"], document["text"])

    def replace_all(self, entries: Mapping[str, str]) -> int:
        # A full re-import: the wrapped collection refuses to delete nothing.
        self._raw_collection.delete_many({})
        if entries:
            self._raw_collection.insert_many(
                [{"_id": number, "text": text} for number, text in entries.items()]
            )
        return len(entries)
