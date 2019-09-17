import pydash
from marshmallow import EXCLUDE

from ebl.dictionary.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.fragment_schema import FragmentSchema
from ebl.fragmentarium.fragmentarium import FragmentRepository
from ebl.fragmentarium.queries import HAS_TRANSLITERATION, \
    aggregate_interesting, aggregate_latest, aggregate_lemmas, \
    aggregate_needs_revision, aggregate_random, fragment_is, number_is
from ebl.mongo_repository import MongoRepository

COLLECTION = 'fragments'


class MongoFragmentRepository(FragmentRepository):
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
        result = self._mongo_collection.aggregate([
            {'$match': {'text.lines.type': 'TextLine'}},
            {'$unwind': '$text.lines'},
            {'$replaceRoot': {'newRoot': '$text.lines'}},
            {'$match': {'type': 'TextLine'}},
            {'$count': 'lines'}
        ])

        return result.next()['lines']

    def create(self, fragment):
        return self._mongo_repository.create(fragment.to_dict())

    def find(self, number):
        data = self._mongo_repository.find(number)
        return FragmentSchema(unknown=EXCLUDE).load(data)

    def search(self, number):
        cursor = self._mongo_collection.find(number_is(number))

        return self._map_fragments(cursor)

    def find_random(self):
        cursor = self._mongo_collection.aggregate(aggregate_random())

        return self._map_fragments(cursor)

    def find_interesting(self):
        cursor = self._mongo_collection.aggregate(aggregate_interesting())

        return self._map_fragments(cursor)

    def find_transliterated(self):
        cursor = self._mongo_collection.find(HAS_TRANSLITERATION)

        return self._map_fragments(cursor)

    def find_latest(self):
        cursor = self._mongo_collection.aggregate(aggregate_latest())
        return self._map_fragments(cursor)

    def find_needs_revision(self):
        cursor = self._mongo_collection.aggregate(aggregate_needs_revision())
        return FragmentInfoSchema(many=True).load(cursor)

    def search_signs(self, query):
        cursor = self._mongo_collection.find({
            'signs': {'$regex': query.regexp}
        })
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        result = self._mongo_collection.update_one(
            fragment_is(fragment),
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
            fragment_is(fragment),
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
        cursor = self._mongo_collection.aggregate(aggregate_lemmas(word))
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
            fragment_is(fragment),
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
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
