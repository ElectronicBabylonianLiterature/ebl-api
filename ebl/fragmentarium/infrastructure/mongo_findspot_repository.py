from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FINDSPOTS_COLLECTION
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema


class MongoFindspotRepository:
    def __init__(self, database):
        self._findspots = MongoCollection(database, FINDSPOTS_COLLECTION)

    def create(self, findspot: Findspot):
        return self._findspots.insert_one(FindspotSchema().dump(findspot))
