import os
from pymongo import MongoClient
import dictdiffer
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.text.atf import AtfSyntaxError
from ebl.text.atf_parser import parse_atf


class Counter:
    def __init__(self, total):
        self.total = total
        self.current = 0

    def increment(self, number):
        self.current += 1
        print(self.total - self.current, number)

    @staticmethod
    def done():
        print('Done!')


def create_updater(fragment_repository, counter_factory):

    def update_fragments():
        fragments = fragment_repository.find_transliterated()
        counter = counter_factory(len(fragments))

        for fragment in fragments:
            counter.increment(fragment.number)
            update_fragment(fragment)

        counter.done()

    def update_fragment(fragment):
        try:
            atf = fragment.text.atf
            text = parse_atf(atf)
            if fragment.text != text:
                diff = list(dictdiffer.diff(
                    fragment.text.to_dict(),
                    text.to_dict()
                ))
                flavour = (
                    'Different'
                    if (
                        (len(fragment.text.lines) == len(text.lines)) or
                        (
                            len(fragment.text.lines) - 1 == len(text.lines) and
                            diff[-1][0] == 'remove'
                        )
                    )
                    else 'Failure'
                )
                print(f'{flavour}: {fragment.number}')
                print(diff)
                fragment_repository._mongo_collection.update_one(
                    {'_id': fragment.number},
                    {'$set': {
                        'text': text.to_dict(),
                    }}
                )
        except AtfSyntaxError as error:
            print(f'Error: {fragment.number} - {error}')

    return update_fragments


if __name__ == '__main__':
    CLIENT = MongoClient(os.environ['MONGODB_URI'])
    DATABASE = CLIENT.get_database()
    FRAGMENT_REPOSITORY = MongoFragmentRepository(DATABASE)
    create_updater(FRAGMENT_REPOSITORY, Counter)()
