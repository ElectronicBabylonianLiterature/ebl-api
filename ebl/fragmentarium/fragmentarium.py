from ebl.fragmentarium.transliteration_query import TransliterationQuery


TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class Fragmentarium:

    def __init__(self, repository, changelog, sign_list):
        self._repository = repository
        self._changelog = changelog
        self._sign_list = sign_list

    def update_transliteration(self, number, transliteration, user):
        fragment = self._repository.find(number)
        updated_fragment = fragment.update_transliteration(
            transliteration.with_signs(self._sign_list),
            user
        )

        self._changelog.create(
            self._repository.collection,
            user.profile,
            fragment.to_dict(),
            updated_fragment.to_dict()
        )

        self._repository.update_transliteration(updated_fragment)

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
        signs = transliteration.to_sign_matrix(self._sign_list)
        query = TransliterationQuery(signs)
        return [
            fragment.add_matching_lines(query)
            for fragment
            in self._repository.search_signs(query)
        ]

    def create(self, fragment):
        return self._repository.create(fragment)
