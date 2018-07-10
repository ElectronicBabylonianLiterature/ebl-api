import datetime
from ebl.mongo_repository import MongoRepository

RECORD_TYPE = 'Transliteration'


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')

    def update_transliteration(self, number, transliteration, user):
        result = self.get_collection().update_one(
            {'_id': number},
            {
                '$set': {'transliteration': transliteration},
                '$push': {'record': {
                    'user': user,
                    'type': RECORD_TYPE,
                    'date': datetime.datetime.utcnow().isoformat()
                }}
            }
        )

        if result.matched_count == 0:
            raise KeyError
