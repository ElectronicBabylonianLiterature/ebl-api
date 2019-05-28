import re

import pydash
from bson.code import Code

from ebl.errors import NotFoundError
from ebl.fragment.record import RecordType
from ebl.mongo_repository import MongoRepository
from ebl.text.atf import ATF_SPEC, ATF_EXTENSIONS
from ebl.dictionary.word import WordId

COLLECTION = 'fragments'
HAS_TRANSLITERATION = {'text.lines.type': {'$exists': True}}
NUMBER_OF_LATEST_TRANSLITERATIONS = 40


def sample_size_one():
    return {
        '$sample': {
            'size': 1
        }
    }


class MongoFragmentRepository():
    def __init__(self, database, fragment_factory):
        self._mongo_repository = MongoRepository(database, COLLECTION)
        self._fragment_factory = fragment_factory

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
        return self._fragment_factory.create(data)

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
                        {'collection': 'Kuyunjik'},
                        {'uncuratedReferences': {'$exists': True}},
                        {'uncuratedReferences.3': {'$exists': False}}
                    ]
                }
            },
            sample_size_one()
        ])

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = self._mongo_collection.find(HAS_TRANSLITERATION)

        return self._map_fragments(cursor)

    def find_latest(self):
        temp_field_name = '_temp'
        cursor = self._mongo_collection.aggregate([
            {'$match': {'record.type': RecordType.TRANSLITERATION.value}},
            {'$addFields': {
                temp_field_name: {
                    '$filter': {
                        'input': '$record',
                        'as': 'entry',
                        'cond': {
                            '$eq': [
                                '$$entry.type',
                                RecordType.TRANSLITERATION.value
                            ]
                        }
                    }
                }
            }},
            {'$sort': {f'{temp_field_name}.date': -1}},
            {'$limit': NUMBER_OF_LATEST_TRANSLITERATIONS},
            {'$project': {temp_field_name: 0}}
        ])
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
        ignore = [
            ATF_SPEC['lacuna']['begin'],
            r'\(',
            r'\)',
            ATF_SPEC['lacuna']['end'],
            ATF_SPEC['flags']['uncertainty'],
            ATF_SPEC['flags']['collation'],
            ATF_SPEC['flags']['damage'],
            ATF_SPEC['flags']['correction'],
            ATF_EXTENSIONS['erasure_illegible'],
            ATF_EXTENSIONS['erasure_boundary']
        ]
        ignore_regex = f'({"|".join(ignore)})*'
        cleaned_word = re.sub(ignore_regex, '', word)
        word_regex = (
            f'^{ignore_regex}' +
            ''.join([
                f"{re.escape(char)}{ignore_regex}" for char in cleaned_word
            ]) +
            '$'
        )

        cursor = self._mongo_collection.aggregate([
            {'$match': {
                'text.lines.content': {
                    '$elemMatch': {
                        'value': {'$regex': word_regex},
                        'uniqueLemma.0': {'$exists': True}
                    }
                }
            }},
            {'$project': {'lines': '$text.lines'}},
            {'$unwind': '$lines'},
            {'$project': {'tokens': '$lines.content'}},
            {'$unwind': '$tokens'},
            {'$match': {
                'tokens.value': {'$regex': word_regex},
                'tokens.uniqueLemma.0': {'$exists': True}
            }},
            {'$group': {
                '_id': '$tokens.uniqueLemma',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ])
        return [
            [
                WordId(unique_lemma)
                for unique_lemma
                in result['_id']
            ]
            for result
            in cursor
        ]

    def update_references(self, fragment):
        result = self._mongo_collection.update_one(
            {'_id': fragment.number},
            {'$set': {
                'references': [
                    reference.to_dict()
                    for reference in fragment.references
                ]
            }}
        )

        if result.matched_count == 0:
            raise NotFoundError(f'Fragment {fragment.number} not found.')

    def _map_fragments(self, cursor):
        return [
            self._fragment_factory.create(fragment)
            for fragment in cursor
        ]
