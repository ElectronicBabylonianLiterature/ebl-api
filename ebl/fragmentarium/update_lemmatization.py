import os
from pymongo import MongoClient

from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.lemmatization import Lemmatization


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


def create_updater(fragment_repository, counter_factory):

    def update_fragments():
        fragments = fragment_repository.find_transliterated()
        counter = counter_factory(len(fragments))

        for fragment in fragments:
            counter.increment(fragment.number)
            update_fragment(fragment)

        counter.done()

    def update_fragment(fragment):
        lemmatization =\
            Lemmatization.of_transliteration(fragment.transliteration)
        fragment_repository._mongo_collection.update_one(
            {'_id': fragment.number},
            {'$set': {
                'lemmatization': lemmatization.tokens,
            }}
        )
    return update_fragments


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    create_updater(FRAGMENT_REPOSITORY, Counter)()
