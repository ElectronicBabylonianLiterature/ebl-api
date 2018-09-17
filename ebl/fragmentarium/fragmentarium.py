import datetime
import pydash
from ebl.fragmentarium.transliteration_query import TransliterationQuery
from ebl.fragmentarium.transliterations import clean


EBL_NAME = 'https://ebabylon.org/eblName'
TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


def _record_for(fragment, updates, user_profile):
    old_transliteration = fragment['transliteration']
    new_transliteration = updates['transliteration']

    if new_transliteration != old_transliteration:
        return _create_record(old_transliteration, user_profile)
    else:
        return None


def _create_record(old_transliteration, user_profile):
    record_type = REVISION if old_transliteration else TRANSLITERATION
    user = user_profile[EBL_NAME] or user_profile['name']
    return {
        'user': user,
        'type': record_type,
        'date': datetime.datetime.utcnow().isoformat()
    }


class Fragmentarium:

    def __init__(self, repository, changelog, sign_list):
        self._repository = repository
        self._changelog = changelog
        self._sign_list = sign_list

    def update_transliteration(self, number, updates, user_profile):
        fragment = self._repository.find(number)

        filtered_updates = pydash.pick(updates, 'transliteration', 'notes')
        filtered_updates['signs'] = self._create_signs(
            filtered_updates['transliteration']
        )

        record = _record_for(fragment, updates, user_profile)

        self._changelog.create(
            self._repository.collection,
            user_profile,
            pydash.pick(fragment, '_id', 'transliteration', 'notes', 'signs'),
            pydash.defaults(filtered_updates, {'_id': number})
        )

        self._repository.update_transliteration(number,
                                                filtered_updates,
                                                record)

    def _create_signs(self, transliteration):
        cleaned_transliteration = clean(transliteration)
        signs = self._sign_list.map_transliteration(cleaned_transliteration)
        return '\n'.join([
            ' '.join(row)
            for row in signs
        ])

    def statistics(self):
        return {
            'transliteratedFragments': (self
                                        ._repository
                                        .count_transliterated_fragments()),
            'lines': self._repository.count_lines()
        }

    def find(self, number):
        return self._repository.find(number)

    def search(self, number):
        return self._repository.search(number)

    def find_random(self):
        return self._repository.find_random()

    def find_interesting(self):
        return self._repository.find_interesting()

    def search_signs(self, transliteration):
        cleaned_transliteration = clean(transliteration)
        signs = self._sign_list.map_transliteration(cleaned_transliteration)
        query = TransliterationQuery(signs)
        return [
            (fragment, query.get_matching_lines(fragment))
            for fragment
            in self._repository.search_signs(query)
        ]

    def create(self, fragment):
        return self._repository.create(fragment)
