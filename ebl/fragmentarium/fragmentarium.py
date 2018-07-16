import datetime
from ebl.mongo_repository import MongoRepository

TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')

    def update_transliteration(self, number, updates, user):
        fragment = self.get_collection().find_one(
            {'_id': number},
            {'transliteration': 1}
        )

        if fragment:
            old_transliteration = fragment['transliteration']
            record_type = REVISION if old_transliteration else TRANSLITERATION
            self.get_collection().update_one(
                {'_id': number},
                {
                    '$set': {
                        'transliteration': updates['transliteration'],
                        'notes': updates['notes']
                    },
                    '$push': {'record': {
                        'user': user,
                        'type': record_type,
                        'date': datetime.datetime.utcnow().isoformat()
                    }}
                }
            )
        else:
            raise KeyError
