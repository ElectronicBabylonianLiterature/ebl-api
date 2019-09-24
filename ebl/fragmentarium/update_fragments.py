import os

from progress.bar import Bar
from pymongo import MongoClient

from ebl.auth0 import ApiUser
from ebl.bibliography.bibliography import MongoBibliography
from ebl.changelog import Changelog
from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.signlist.application.sign_list import SignList
from ebl.signlist.infrastructure.sign_repository import MemoizingSignRepository
from ebl.transliteration.lemmatization import LemmatizationError
from ebl.transliteration.transliteration_error import TransliterationError


def update_fragment(transliteration_factory, fragmentarium, fragment):
    transliteration = transliteration_factory.create(
        fragment.text.atf,
        fragment.notes
    )
    user = ApiUser('update_fragments.py')
    fragmentarium.update_transliteration(fragment.number,
                                         transliteration,
                                         user)


def find_transliterated(fragment_repository):
    return [
        fragment.number for fragment
        in fragment_repository.find_transliterated()
    ]


class State:
    def __init__(self):
        self.invalid_atf = 0
        self.invalid_lemmas = 0
        self.updated = 0
        self.errors = []

    def add_updated(self):
        self.updated += 1

    def add_lemmatization_error(self, error, fragment):
        self.invalid_lemmas += 1
        self.errors.append(f'{fragment.number}\t{error}')

    def add_transliteration_error(self, transliteration_error, fragment):
        self.invalid_atf += 1
        for index, error in enumerate(transliteration_error.errors):
            atf = fragment.text.lines[error['lineNumber'] - 1].atf
            number = (fragment.number
                      if index == 0 else
                      len(fragment.number) * ' ')
            self.errors.append(f'{number}\t{atf}')

    def to_tsv(self):
        return '\n'.join([
            *self.errors,
            f'# Updated fragments: {self.updated}',
            f'# Invalid ATF: {self.invalid_atf}',
            f'# Invalid lemmas: {self.invalid_lemmas}',
        ])


def update_fragments(fragment_repository,
                     transliteration_factory,
                     fragmentarium):
    state = State()
    numbers = find_transliterated(fragment_repository)

    with Bar('Updating', max=len(numbers)) as bar:
        for number in numbers:
            try:
                fragment = fragmentarium.find(number)
                update_fragment(transliteration_factory,
                                fragmentarium,
                                fragment)
                state.add_updated()
            except TransliterationError as error:
                state.add_transliteration_error(error, fragment)
            except LemmatizationError as error:
                state.add_lemmatization_error(error, fragment)

            bar.next()

    with open('invalid_fragments.tsv', 'w', encoding='utf-8') as file:
        file.write(state.to_tsv())


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    SIGN_REPOSITORY = MemoizingSignRepository(DATABASE)
    SIGN_LIST = SignList(SIGN_REPOSITORY)
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    FRAGMENTARIUM = Fragmentarium(
        FRAGMENT_REPOSITORY,
        Changelog(DATABASE),
        MongoDictionary(DATABASE),
        MongoBibliography(DATABASE)
    )
    TRANSLITERATION_FACTORY = TransliterationUpdateFactory(SIGN_LIST)
    update_fragments(FRAGMENT_REPOSITORY,
                     TRANSLITERATION_FACTORY,
                     FRAGMENTARIUM)
