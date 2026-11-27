from typing import Sequence

from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.signs.application.mes_zl_kap2_repository import (
    MesZlKap2Entry,
    MesZlKap2Repository,
    mes_zl_number_variants,
)

COLLECTION = "meszl_kap2"


def _entry(document: dict) -> MesZlKap2Entry:
    # An alias (e.g. eBL's 115a for Borger's 115) names the entry it shows.
    return MesZlKap2Entry(document.get("number", document["_id"]), document["text"])


class MongoMesZlKap2Repository(MesZlKap2Repository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def find(self, number: str) -> MesZlKap2Entry:
        try:
            document = self._collection.find_one(
                {"_id": {"$in": mes_zl_number_variants(number)}}
            )
        except NotFoundError as error:
            raise NotFoundError(
                f"No MesZL Kapitel II entry for number {number}."
            ) from error
        return _entry(document)

    def find_many(self, numbers: Sequence[str]) -> Sequence[MesZlKap2Entry]:
        entries: list[MesZlKap2Entry] = []
        for number in numbers:
            try:
                entry = self.find(number)
            except NotFoundError:
                continue
            if entry not in entries:
                entries.append(entry)
        return entries
