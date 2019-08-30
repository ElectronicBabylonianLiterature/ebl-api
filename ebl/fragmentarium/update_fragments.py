import os

from progress.bar import Bar
from pymongo import MongoClient

from ebl.auth0 import ApiUser
from ebl.bibliography.bibliography import MongoBibliography
from ebl.changelog import Changelog
from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragment.fragment_factory import FragmentFactory
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MemoizingSignRepository
from ebl.text.lemmatization import LemmatizationError
from ebl.text.transliteration_error import TransliterationError


def update_fragments(fragment_repository, fragmentarium):
    user = ApiUser('update_fragments.py')
    invalid_atf = 0
    invalid_lemmas = 0
    updated = 0
    errors = []
    fragments = [
        fragment.number for fragment
        in fragment_repository.find_transliterated()
    ]

    with Bar('Updating', max=len(fragments)) as bar:
        for number in fragments:
            fragment = fragmentarium.find(number)
            transliteration = Transliteration(
                fragment.text.atf,
                fragment.notes
            )

            try:
                fragmentarium.update_transliteration(fragment.number,
                                                     transliteration,
                                                     user)
                updated += 1
            except TransliterationError as error:
                invalid_atf += 1
                for index, error in enumerate(error.errors):
                    atf = fragment.text.lines[error['lineNumber'] - 1].atf
                    number = (fragment.number
                              if index == 0 else
                              len(fragment.number) * ' ')
                    errors.append(f'{number}\t{atf}')
            except LemmatizationError as error:
                invalid_lemmas += 1
                errors.append(f'{fragment.number}\t{error}')

            bar.next()

    with open('invalid_fragments.tsv', 'w', encoding='utf-8') as file:
        file.write('\n'.join([
            *errors,
            f'# Updated fragments: {updated}',
            f'# Invalid ATF: {invalid_atf}',
            f'# Invalid lemmas: {invalid_lemmas}',
        ]))


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    SIGN_REPOSITORY = MemoizingSignRepository(DATABASE)
    SIGN_LIST = SignList(SIGN_REPOSITORY)
    FRAGMENT_REPOSITORY = MongoFragmentRepository(
        DATABASE,
        FragmentFactory(MongoBibliography(DATABASE))
    )
    FRAGMENTARIUM = Fragmentarium(
        FRAGMENT_REPOSITORY,
        Changelog(DATABASE),
        SIGN_LIST,
        MongoDictionary(DATABASE),
        MongoBibliography(DATABASE))
    update_fragments(FRAGMENT_REPOSITORY, FRAGMENTARIUM)
