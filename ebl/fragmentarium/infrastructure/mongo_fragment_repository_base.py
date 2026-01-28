from marshmallow import EXCLUDE
from typing import Sequence
from ebl.mongo_collection import MongoCollection
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.fragmentarium.infrastructure.collections import JOINS_COLLECTION


class MongoFragmentRepositoryBase(FragmentRepository):
    def __init__(self, database):
        self._fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._joins = MongoCollection(database, JOINS_COLLECTION)

    def _map_fragments(self, cursor) -> Sequence[Fragment]:
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
