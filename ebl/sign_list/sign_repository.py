from typing import List, Optional, Tuple

import pydash

from ebl.mongo_repository import MongoRepository

COLLECTION = 'signs'


class MongoSignRepository(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)

    def search(self, reading, sub_index):
        sub_index_query = \
            {'$exists': False} if sub_index is None else sub_index
        return self.get_collection().find_one({
            'values': {
                '$elemMatch': {
                    'value': reading,
                    'subIndex': sub_index_query
                }
            }
        })

    def search_many(self, readings: List[Tuple[str, Optional[int]]]):
        if readings:
            elem_queries = [
                {
                    'value': reading,
                    'subIndex': {
                        '$exists': False
                    } if sub_index is None else sub_index
                } for (reading, sub_index) in readings
            ]

            return [sign for sign in self.get_collection().find({
                'values': {
                    '$elemMatch': {
                        '$or': elem_queries
                    }
                }
            })]
        else:
            return []


class MemoizingSignRepository(MongoSignRepository):

    def __init__(self, database):
        super().__init__(database)
        self.search = pydash.memoize(super().search)
        self.search_many = pydash.memoize(super().search_many)
