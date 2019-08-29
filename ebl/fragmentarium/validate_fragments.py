import os

from pymongo import MongoClient

from ebl.auth0 import ApiUser
from ebl.bibliography.bibliography import MongoBibliography
from ebl.fragment.fragment_factory import FragmentFactory
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MemoizingSignRepository
from ebl.text.transliteration_error import TransliterationError


def update_fragments(sign_list, fragment_repository):
    user = ApiUser('validate_fragments.py')
    invalid = 0
    fragments = fragment_repository.find_transliterated()

    for fragment in fragments:
        transliteration = Transliteration(
            fragment.text.atf,
            fragment.notes
        ).with_signs(sign_list)

        try:
            fragment.update_transliteration(
                transliteration,
                user
            )
        except TransliterationError as error:
            invalid += 1
            for index, error in enumerate(error.errors):
                atf = fragment.text.lines[error["lineNumber"] - 1].atf
                number = (fragment.number
                          if index == 0 else
                          len(fragment.number) * ' ')
                print(f'{number}\t{atf}')

    print('# ========================')
    print(f'# Invalid fragments: {invalid}')


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    SIGN_REPOSITORY = MemoizingSignRepository(DATABASE)
    SIGN_LIST = SignList(SIGN_REPOSITORY)
    FRAGMENT_REPOSITORY = MongoFragmentRepository(
        DATABASE,
        FragmentFactory(MongoBibliography(DATABASE))
    )
    update_fragments(SIGN_LIST, FRAGMENT_REPOSITORY)
