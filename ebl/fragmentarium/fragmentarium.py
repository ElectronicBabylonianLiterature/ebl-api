import pydash
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.transliteration_query import TransliterationQuery
from ebl.fragmentarium.transliterations import clean


TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class Fragmentarium:

    def __init__(self, repository, changelog, sign_list):
        self._repository = repository
        self._changelog = changelog
        self._sign_list = sign_list

    def update_transliteration(self, number, updates, user):
        fragment = self._repository.find(number)
        updated_fragment = Fragment(fragment).update_transliteration(
            updates['transliteration'],
            updates['notes'],
            user
        ).to_dict()

        filtered_updates = {
            **pydash.pick(
                updated_fragment,
                'transliteration',
                'notes',
                'record'
            ),
            'signs': self._create_signs(
                updated_fragment['transliteration']
            )
        }

        self._changelog.create(
            self._repository.collection,
            user.profile,
            pydash.pick(
                fragment,
                '_id',
                'transliteration',
                'notes',
                'record',
                'signs'
            ),
            {**filtered_updates, '_id': number}
        )

        self._repository.update_transliteration(number,
                                                filtered_updates,
                                                None)

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
