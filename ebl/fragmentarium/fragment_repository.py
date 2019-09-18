import pydash
from marshmallow import EXCLUDE

from ebl.dictionary.word import WordId
from ebl.fragmentarium.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.fragment_schema import FragmentSchema
from ebl.fragmentarium.fragmentarium import FragmentRepository
from ebl.fragmentarium.queries import HAS_TRANSLITERATION, \
    aggregate_interesting, aggregate_latest, aggregate_lemmas, \
    aggregate_needs_revision, aggregate_random, fragment_is, number_is
from ebl.mongo_repository import MongoRepository

COLLECTION = 'fragments'


class MongoFragmentRepository(MongoRepository, FragmentRepository):
    def __init__(self, database):
        MongoRepository.__init__(self, database, COLLECTION)

    def count_transliterated_fragments(self):
        return super()._count_documents(HAS_TRANSLITERATION)

    def count_lines(self):
        result = super()._aggregate([
            {'$match': {'text.lines.type': 'TextLine'}},
            {'$unwind': '$text.lines'},
            {'$replaceRoot': {'newRoot': '$text.lines'}},
            {'$match': {'type': 'TextLine'}},
            {'$count': 'lines'}
        ])

        return result.next()['lines']

    def create(self, fragment):
        return super()._insert_one(fragment.to_dict())

    def find(self, number):
        data = super()._find_one_by_id(number)
        return FragmentSchema(unknown=EXCLUDE).load(data)

    def search(self, number):
        cursor = super()._find_many(number_is(number))

        return self._map_fragments(cursor)

    def find_random(self):
        cursor = super()._aggregate(aggregate_random())

        return self._map_fragments(cursor)

    def find_interesting(self):
        cursor = super()._aggregate(aggregate_interesting())

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = super()._find_many(HAS_TRANSLITERATION)

        return self._map_fragments(cursor)

    def find_latest(self):
        cursor = super()._aggregate(aggregate_latest())
        return self._map_fragments(cursor)

    def find_needs_revision(self):
        cursor = super()._aggregate(aggregate_needs_revision())
        return FragmentInfoSchema(many=True).load(cursor)

    def search_signs(self, query):
        cursor = super()._find_many({
            'signs': {'$regex': query.regexp}
        })
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        super()._update_one(
            fragment_is(fragment),
            {'$set': pydash.omit_by({
                'text': fragment.text.to_dict(),
                'notes': fragment.notes,
                'signs': fragment.signs,
                'record': fragment.record.to_list()
            }, lambda value: value is None)}
        )

    def update_lemmatization(self, fragment):
        super()._update_one(
            fragment_is(fragment),
            {'$set': {
                'text': fragment.text.to_dict()
            }}
        )

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
            cursor = super()._aggregate(query)
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
        cursor = super()._aggregate(aggregate_lemmas(word))
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
        super()._update_one(
            fragment_is(fragment),
            {'$set': {
                'references': [
                    reference.to_dict()
                    for reference in fragment.references
                ]
            }}
        )

    def _map_fragments(self, cursor):
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
