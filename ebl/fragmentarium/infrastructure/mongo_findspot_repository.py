from typing import Sequence
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FINDSPOTS_COLLECTION
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema


class MongoFindspotRepository:
    def __init__(self, database, provenance_service):
        self._findspots = MongoCollection(database, FINDSPOTS_COLLECTION)
        self._provenance_service = provenance_service

    def _schema(self):
        return FindspotSchema(context={"provenance_service": self._provenance_service})

    def create(self, findspot: Findspot) -> None:
        return self._findspots.insert_one(self._schema().dump(findspot))

    def find_all(self) -> Sequence[Findspot]:
        return self._schema().load(self._findspots.find_many({}), many=True)
