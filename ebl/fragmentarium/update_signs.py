import os

from progress.bar import Bar
from pymongo import MongoClient

from ebl.auth0 import ApiUser
from ebl.bibliography.bibliography import MongoBibliography
from ebl.fragment.fragment_factory import FragmentFactory
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MemoizingSignRepository


def create_updater(sign_list, fragment_repository):

    def update_fragments():
        fragments = fragment_repository.find_transliterated()

        with Bar(
            'Updating',
            max=len(fragments),
            suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]'
        ) as bar:
            for fragment in fragments:
                update_fragment(fragment)
                bar.next()

    def update_fragment(fragment):
        transliteration = Transliteration(
            fragment.text.atf,
            fragment.notes
        ).with_signs(sign_list)

        if transliteration.signs != fragment.signs:
            fragment_repository.update_transliteration(
                fragment.update_transliteration(
                    transliteration, ApiUser('update_signs.py')
                )
            )

    return update_fragments


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    SIGN_REPOSITORY = MemoizingSignRepository(DATABASE)
    SIGN_LIST = SignList(SIGN_REPOSITORY)
    FRAGMENT_REPOSITORY = MongoFragmentRepository(
        DATABASE,
        FragmentFactory(MongoBibliography(DATABASE))
    )
    create_updater(SIGN_LIST, FRAGMENT_REPOSITORY)()
