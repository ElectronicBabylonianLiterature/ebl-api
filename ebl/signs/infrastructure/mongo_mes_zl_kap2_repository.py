from typing import Mapping, Sequence

from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.signs.application.mes_zl_kap2_repository import MesZlKap2Repository
from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry, mes_zl_number_variants

COLLECTION = "meszl_kap2"


def first_entry(
    spellings: Sequence[str], entries: Mapping[str, MesZlKap2Entry]
) -> MesZlKap2Entry | None:
    return next((entries[key] for key in spellings if key in entries), None)


class MongoMesZlKap2Repository(MesZlKap2Repository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def find_by_numbers(self, numbers: Sequence[str]) -> Sequence[MesZlKap2Entry]:
        spellings = [mes_zl_number_variants(number) for number in numbers]
        keys = [key for variants in spellings for key in variants]
        stored = {
            document["_id"]: MesZlKap2Entry(document["number"], document["text"])
            for document in self._collection.find_many({"_id": {"$in": keys}})
        }
        found = (first_entry(variants, stored) for variants in spellings)
        return list(dict.fromkeys(entry for entry in found if entry is not None))
