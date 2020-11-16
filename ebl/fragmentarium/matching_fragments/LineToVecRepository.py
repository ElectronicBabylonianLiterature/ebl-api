from abc import ABC, abstractmethod

from ebl.fragmentarium.application.fragment_schema import LineToVecSchema
from ebl.mongo_collection import MongoCollection


class LineToVecRepository(ABC):
    @abstractmethod
    def insert_all(self, entries: dict) -> None:
        ...

    @abstractmethod
    def get_line_to_vec_with_rulings(self):
        ...

    @abstractmethod
    def get_line_to_vec_all(self):
        ...


COLLECTION = "lineToVec"


class MongoLineToVecRepository(LineToVecRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def insert_all(self, entries: dict):
        self._collection.update_one(
            {"_id": "lineToVec"},
            {
                "$set": {
                    "lineToVec": {
                        k: LineToVecSchema().dump(v)  # pyre-ignore[16]
                        for k, v in entries.items()
                    }
                }
            },
        )

    def get_line_to_vec_with_rulings(self):
        doc = self._collection.find_one_by_id("lineToVec")
        return {
            k: LineToVecSchema().load(v)
            for k, v in doc["lineToVec"].items()
            if v["complexity"] > 0
        }

    def get_line_to_vec_all(self):
        return self._collection.find_one_by_id("lineToVec")
