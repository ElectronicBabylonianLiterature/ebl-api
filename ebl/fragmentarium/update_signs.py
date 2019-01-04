import os
from pymongo import MongoClient

from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.transliteration import Transliteration
from ebl.sign_list.sign_repository import MemoizingSignRepository
from ebl.sign_list.sign_list import SignList


class ApiUser:
    # pylint: disable=R0201
    def __init__(self, script_name):
        self._script_name = script_name

    @property
    def profile(self):
        return {
            'name': self._script_name
        }

    @property
    def ebl_name(self):
        return 'Script'

    def has_scope(self, _):
        return False

    def can_read_folio(self, _):
        return False


class Counter:
    def __init__(self, total):
        self.total = total
        self.current = 0

    def increment(self, number):
        self.current += 1
        print(self.total - self.current, number)

    @staticmethod
    def done():
        print('Updating signs done!')


def create_updater(sign_list, fragment_repository, counter_factory):

    def update_fragments():
        fragments = fragment_repository.find_transliterated()
        counter = counter_factory(len(fragments))

        for fragment in fragments:
            counter.increment(fragment.number)
            update_fragment(fragment)

        counter.done()

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
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    create_updater(SIGN_LIST, FRAGMENT_REPOSITORY, Counter)()
