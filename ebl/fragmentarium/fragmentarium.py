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
            self._update(updates, fragment, user)
        else:
            raise KeyError

    def _update(self, updates, fragment, user):
        mongo_update = {
            '$set': {
                'transliteration': updates['transliteration'],
                'notes': updates['notes']
            }
        }

        old_transliteration = fragment['transliteration']
        if updates['transliteration'] != old_transliteration:
            record_type = REVISION if old_transliteration else TRANSLITERATION
            mongo_update['$push'] = {'record': {
                'user': user,
                'type': record_type,
                'date': datetime.datetime.utcnow().isoformat()
            }}

        self.get_collection().update_one(
            {'_id': fragment['_id']},
            mongo_update
        )
