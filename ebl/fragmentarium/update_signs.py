import os

from progress.bar import Bar
from pymongo import MongoClient

from ebl.auth0 import ApiUser
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.transliteration_search.application.transliteration_search import \
    TransliterationSearch
from ebl.transliteration_search.infrastructure.menoizing_sign_repository \
    import \
    MemoizingSignRepository
from ebl.transliteration_search.infrastructure.mongo_sign_repository import \
    MongoSignRepository


def create_updater(transliteration_factory, fragment_repository):

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
        transliteration = transliteration_factory.create(
            fragment.text.atf,
            fragment.notes
        )

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
    SIGN_REPOSITORY = MemoizingSignRepository(MongoSignRepository(DATABASE))
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    TRANSLITERATION_SEARCH = TransliterationSearch(SIGN_REPOSITORY,
                                                   FRAGMENT_REPOSITORY)
    TRANSLITERATION_UPDATE_FACTORY = \
        TransliterationUpdateFactory(TRANSLITERATION_SEARCH)
    create_updater(TRANSLITERATION_UPDATE_FACTORY, FRAGMENT_REPOSITORY)()
