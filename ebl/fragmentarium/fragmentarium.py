import datetime
import pydash
from ebl.changelog import Changelog
from ebl.fragmentarium.fragment_repository import MongoFragmenRepository
from ebl.fragmentarium.signs_search import create_query


EBL_NAME = 'https://ebabylon.org/eblName'
TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


def _create_record(old_transliteration, user_profile):
    record_type = REVISION if old_transliteration else TRANSLITERATION
    user = user_profile[EBL_NAME] or user_profile['name']
    return {
        'user': user,
        'type': record_type,
        'date': datetime.datetime.utcnow().isoformat()
    }


class Fragmentarium:

    def __init__(self, database):
        self._repository = MongoFragmenRepository(database)
        self._changelog = Changelog(database)

    def update_transliteration(self, number, updates, user_profile):
        fragment = self._repository.find(number)
        filtered_updates = pydash.pick(updates, 'transliteration', 'notes')
        
        record = None
        old_transliteration = fragment['transliteration']
        if updates['transliteration'] != old_transliteration:
            record = _create_record(old_transliteration, user_profile)

        self._changelog.create(
            self._repository.collection,
            user_profile,
            pydash.pick(fragment, '_id', 'transliteration', 'notes'),
            pydash.defaults(filtered_updates, {'_id': number})
        )

        self._repository.update_transliteration(fragment, filtered_updates, record)

    def statistics(self):
        return {
            'transliteratedFragments': self._repository.get_transliterated_fragments(),
            'lines': self._repository.get_lines()
        }

    def find(self, number):
        return self._repository.find(number)

    def search(self, number):
        return self._repository.search(number)

    def find_random(self):
        return self._repository.find_random

    def find_interesting(self):
        return self._repository.find_interesting()

    def search_signs(self, signs):
        query = create_query(signs)
        return self._repository.search_signs(query)

    def get_collection(self):
        return self._repository.get_collection()

    def create(self, fragment):
        return self._repository.create(fragment)