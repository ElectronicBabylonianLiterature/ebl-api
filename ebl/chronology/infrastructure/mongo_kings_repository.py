from typing import Sequence
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.chronology.chronology import King, KingSchema
from ebl.chronology.application.kings_repository import KingsRepository

COLLECTION = "kings"


class MongoKingsRepository(KingsRepository):
    def __init__(self, database: Database):
        self._kings = MongoCollection(database, COLLECTION)

    def list_all_kings(self, *args, **kwargs) -> Sequence[King]:
        data = self._kings.aggregate([])
        return KingSchema().load(list(data), many=True)
