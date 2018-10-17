from bson.code import Code
import pydash
from ebl.mongo_repository import MongoRepository
from ebl.fragmentarium.fragment import Fragment


COLLECTION = 'fragments'
HAS_TRANSLITERATION = {'transliteration': {'$ne': ''}}
SAMPLE_SIZE_ONE = {
    '$sample': {
        'size': 1
    }
}


class MongoFragmentRepository():
    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)

    @property
    def collection(self):
        return self._mongo_repository.collection

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

    def count_transliterated_fragments(self):
        return self._mongo_collection.count_documents(HAS_TRANSLITERATION)

    def count_lines(self):
        count_lines = Code('function() {'
                           '  const lines = this.transliteration'
                           '    .split("\\n")'
                           '    .filter(line => /^\\d/.test(line));'
                           '  emit("lines", lines.length);'
                           '}')
        sum_lines = Code('function(key, values) {'
                         '  return values.reduce((acc, cur) => acc + cur, 0);'
                         '}')
        result = self._mongo_collection.inline_map_reduce(
            count_lines,
            sum_lines,
            query=HAS_TRANSLITERATION)

        return result[0]['value'] if result else 0

    def create(self, fragment):
        return self._mongo_repository.create(fragment.to_dict())

    def find(self, number):
        return Fragment(self._mongo_repository.find(number))

    def search(self, number):
        cursor = self._mongo_collection.find({
            '$or': [
                {'_id': number},
                {'cdliNumber': number},
                {'accession': number}
            ]
        })

        return self._map_fragments(cursor)

    def find_random(self):
        cursor = self._mongo_collection.aggregate([
            {'$match': HAS_TRANSLITERATION},
            SAMPLE_SIZE_ONE
        ])

        return self._map_fragments(cursor)

    def find_interesting(self):
        cursor = self._mongo_collection.aggregate([
            {
                '$match': {
                    '$and': [
                        {'transliteration': ''},
                        {'joins': []},
                        {'publication': ''},
                        {'hits': 0}
                    ]
                }
            },
            SAMPLE_SIZE_ONE
        ])

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = self._mongo_collection.find(
            {'transliteration': {'$ne': ''}}
        )

        return self._map_fragments(cursor)

    def search_signs(self, query):
        cursor = self._mongo_collection.find({
            'signs': {'$regex': query.regexp}
        })
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        result = self._mongo_collection.update_one(
            {'_id': fragment.number},
            {'$set': pydash.omit_by({
                'transliteration': fragment.transliteration.atf,
                'notes': fragment.transliteration.notes,
                'signs': fragment.transliteration.signs,
                'record': fragment.record.entries
            }, lambda value: value is None)}
        )

        if result.matched_count == 0:
            raise KeyError

    @staticmethod
    def _map_fragments(cursor):
        return [Fragment(fragment) for fragment in cursor]
