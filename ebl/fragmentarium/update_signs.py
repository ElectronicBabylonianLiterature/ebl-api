import os
from pymongo import MongoClient

from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.sign_list.sign_repository import MemoizingSignRepository
from ebl.sign_list.sign_list import SignList
from ebl.fragmentarium.transliterations import clean


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
        signs = map_transliteration(fragment.transliteration)

        if signs != fragment.signs:
            fragment_repository.update_transliteration(
                fragment.set_signs(signs)
            )

    def map_transliteration(transliteration):
        cleaned_transliteration = clean(transliteration)
        signs = sign_list.map_transliteration(cleaned_transliteration)
        return '\n'.join([
            ' '.join(row)
            for row in signs
        ])

    return update_fragments


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    SIGN_REPOSITORY = MemoizingSignRepository(DATABASE)
    SIGN_LIST = SignList(SIGN_REPOSITORY)
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    create_updater(SIGN_LIST, FRAGMENT_REPOSITORY, Counter)()
