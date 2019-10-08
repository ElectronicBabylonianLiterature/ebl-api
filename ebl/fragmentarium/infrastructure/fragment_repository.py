from marshmallow import EXCLUDE

from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.application.fragment_info_schema import \
    FragmentInfoSchema
from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.fragmentarium.infrastructure.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.queries import HAS_TRANSLITERATION, \
    aggregate_interesting, aggregate_latest, aggregate_lemmas, \
    aggregate_needs_revision, aggregate_random, fragment_is, number_is
from ebl.mongo_collection import MongoCollection

COLLECTION = 'fragments'


class MongoFragmentRepository(FragmentRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def count_transliterated_fragments(self):
        return self._collection.count_documents(HAS_TRANSLITERATION)

    def count_lines(self):
        result = self._collection.aggregate([
            {'$match': {'text.lines.type': 'TextLine'}},
            {'$unwind': '$text.lines'},
            {'$replaceRoot': {'newRoot': '$text.lines'}},
            {'$match': {'type': 'TextLine'}},
            {'$count': 'lines'}
        ])

        return result.next()['lines']

    def create(self, fragment):
        return self._collection.insert_one(FragmentSchema().dump(fragment))

    def query_by_fragment_number(self, number):
        data = self._collection.find_one_by_id(number)
        return FragmentSchema(unknown=EXCLUDE).load(data)

    def query_by_fragment_cdli_or_accession_number(self, number):
        cursor = self._collection.find_many(number_is(number))

        return self._map_fragments(cursor)

    def query_random_by_transliterated(self):
        cursor = self._collection.aggregate(aggregate_random())

        return self._map_fragments(cursor)

    def query_by_kuyunjik_not_transliterated_joined_or_published(self):
        cursor = self._collection.aggregate(aggregate_interesting())

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = self._collection.find_many(HAS_TRANSLITERATION)

        return self._map_fragments(cursor)

    def query_by_transliterated_sorted_by_date(self):
        cursor = self._collection.aggregate(aggregate_latest())
        return self._map_fragments(cursor)

    def query_by_transliterated_not_revised_by_other(self):
        cursor = self._collection.aggregate(aggregate_needs_revision())
        return FragmentInfoSchema(many=True).load(cursor)

    def query_by_transliteration(self, query):
        cursor = self._collection.find_many({
            'signs': {'$regex': query.regexp}
        })
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        self._collection.update_one(
            fragment_is(fragment),
            {'$set': FragmentSchema(
                only=('text', 'notes', 'signs', 'record'),
             ).dump(fragment)}
        )

    def update_lemmatization(self, fragment):
        self._collection.update_one(
            fragment_is(fragment),
            {'$set': FragmentSchema(only=('text',)).dump(fragment)}
        )

    def query_next_and_previous_folio(self, folio_name, folio_number, number):
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
            cursor = self._collection.aggregate(query)
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

    def query_lemmas(self, word):
        cursor = self._collection.aggregate(aggregate_lemmas(word))
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
        self._collection.update_one(
            fragment_is(fragment),
            {'$set': FragmentSchema(only=('references',)).dump(fragment)}
        )

    def _map_fragments(self, cursor):
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
