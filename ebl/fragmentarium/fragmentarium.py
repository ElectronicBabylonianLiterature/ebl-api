from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.fragmentarium.validator import Validator


class Fragmentarium:

    def __init__(self,
                 repository,
                 changelog,
                 sign_list,
                 dictionary,
                 bibliography):

        self._repository = repository
        self._changelog = changelog
        self._sign_list = sign_list
        self._dictionary = dictionary
        self._bibliography = bibliography

    def update_transliteration(self, number, transliteration, user):
        transliteration_with_signs =\
            transliteration.with_signs(self._sign_list)
        Validator(transliteration_with_signs).validate()
        fragment = self._repository.find(number)
        updated_fragment = fragment.update_transliteration(
            transliteration_with_signs,
            user
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_transliteration(updated_fragment)

        return updated_fragment

    def update_lemmatization(self, number, lemmatization, user):
        fragment = self._repository.find(number)
        updated_fragment = fragment.update_lemmatization(
            lemmatization
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_lemmatization(updated_fragment)

        return updated_fragment

    def update_references(self, number, references, user):
        fragment = self._repository.find(number)
        self._bibliography.validate_references(references)

        updated_fragment = fragment.set_references(references)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_references(updated_fragment)

        return updated_fragment

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

    def find_latest(self):
        return self._repository.find_latest()

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

    def folio_pager(self, folio_name, folio_number, number):
        return self._repository.folio_pager(folio_name, folio_number, number)

    def find_lemmas(self, word):
        return [
            [
                self._dictionary.find(unique_lemma)
                for unique_lemma
                in result
            ]
            for result
            in self._repository.find_lemmas(word)
        ]

    def _create_changlelog(self, user, fragment, updated_fragment):
        self._changelog.create(
            self._repository.collection,
            user.profile,
            fragment.to_dict(),
            updated_fragment.to_dict()
        )
