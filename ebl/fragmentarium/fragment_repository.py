from bson.code import Code
import pydash
from ebl.mongo_repository import MongoRepository
from ebl.errors import NotFoundError
from ebl.fragmentarium.fragment import Fragment
from ebl.text.token import UniqueLemma


COLLECTION = 'fragments'
HAS_TRANSLITERATION = {'text.lines.type': {'$exists': True}}


def sample_size_one():
    return {
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
                           '  const lines = this.text.lines'
                           '    .filter(line => line.type == "TextLine");'
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
        data = self._mongo_repository.find(number)
        return Fragment.from_dict(data)

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
            sample_size_one()
        ])

        return self._map_fragments(cursor)

    def find_interesting(self):
        cursor = self._mongo_collection.aggregate([
            {
                '$match': {
                    '$and': [
                        {'text.lines': []},
                        {'joins': []},
                        {'publication': ''},
                        {'hits': 0}
                    ]
                }
            },
            sample_size_one()
        ])

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = self._mongo_collection.find(HAS_TRANSLITERATION)

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
                'text': fragment.text.to_dict(),
                'notes': fragment.notes,
                'signs': fragment.signs,
                'record': fragment.record.to_list()
            }, lambda value: value is None)}
        )

        if result.matched_count == 0:
            raise NotFoundError(f'Fragment {fragment.number} not found.')

    def update_lemmatization(self, fragment):
        result = self._mongo_collection.update_one(
            {'_id': fragment.number},
            {'$set': {
                'text': fragment.text.to_dict()
            }}
        )

        if result.matched_count == 0:
            raise NotFoundError(f'Fragment {fragment.number} not found.')

    def folio_pager(self, folio_name, folio_number, number):
        base_pipeline = [
            {'$match': {'folios.name': folio_name}},
            {'$unwind': '$folios'},
            {'$project': {
                'name': '$folios.name',
                'number': '$folios.number',
                'key': {'$concat': ['$folios.number', '-', '$_id']}
            }},
            {'$match': {'name': folio_name}},
        ]
        ascending = [
            {'$sort': {'key': 1}},
            {'$limit': 1}
        ]
        descending = [
            {'$sort': {'key': -1}},
            {'$limit': 1}
        ]

        def create_query(*parts):
            return [
                *base_pipeline,
                *parts
            ]

        def get_numbers(query):
            cursor = self._mongo_collection.aggregate(query)
            if cursor.alive:
                entry = cursor.next()
                return {
                    'fragmentNumber': entry['_id'],
                    'folioNumber': entry['number']
                }
            else:
                return None

        first = create_query(*ascending)
        previous = create_query(
            {'$match': {'key': {'$lt': f'{folio_number}-{number}'}}},
            *descending
        )
        next_ = create_query(
            {'$match': {'key': {'$gt': f'{folio_number}-{number}'}}},
            *ascending
        )
        last = create_query(*descending)

        return {
            'previous': get_numbers(previous) or get_numbers(last),
            'next': get_numbers(next_) or get_numbers(first)
        }

    def find_lemmas(self, word):
        cursor = self._mongo_collection.aggregate([
            {'$match': {
                'text.lines.content': {
                    '$elemMatch': {
                        'value': word,
                        'uniqueLemma': {'$ne': []}
                    }
                }
            }},
            {'$project': {'lines': '$text.lines'}},
            {'$unwind': '$lines'},
            {'$project': {'tokens': '$lines.content'}},
            {'$unwind': '$tokens'},
            {'$match': {
                'tokens.value': word,
                'tokens.uniqueLemma': {'$ne': []}
            }},
            {'$group': {
                '_id': '$tokens.uniqueLemma',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ])

        return [
            tuple(
                UniqueLemma(unique_lemma)
                for unique_lemma
                in result['_id']
            )
            for result
            in cursor
        ]

    @staticmethod
    def _map_fragments(cursor):
        return [
            Fragment.from_dict(fragment)
            for fragment in cursor
        ]
