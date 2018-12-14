import re
from ebl.changelog import Changelog
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'words'
LEMMA_SEARCH_LIMIT = 10


def _create_substring_expression(query, _input):
    return {
        '$eq': [{
            '$substrCP': [{
                '$reduce': {
                    'input': _input,
                    'initialValue': '',
                    'in': {
                        '$concat': [
                            '$$value',
                            '$$this',
                            ' '
                        ]
                    }
                }
            }, 0, len(query)]
        }, query]
    }


def _create_lemma_search_pipeline(query):
    return [
        {
            '$match': {
                '$or': [{
                    '$expr': _create_substring_expression(query, '$lemma')
                }, {
                    '$expr': {
                        '$anyElementTrue': {
                            '$map': {
                                'input': "$forms",
                                'as': "form",
                                'in': _create_substring_expression(
                                    query,
                                    '$$form.lemma'
                                )
                            }
                        }
                    }
                }]
            }
        },
        {
            '$addFields': {
                'lemmaLength': {
                    '$sum': {
                        '$map': {
                            'input': '$lemma',
                            'as': 'part',
                            'in': {'$strLenCP': '$$part'}
                        }
                    }
                }
            }
        },
        {'$sort': {'lemmaLength': 1, '_id': 1}},
        {'$limit': LEMMA_SEARCH_LIMIT},
        {'$project': {'lemmaLength': 0}}
    ]


class MongoDictionary(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)
        self._changelog = Changelog(database)

    def search(self, query):
        lemma = query.split(' ')
        cursor = self.get_collection().find({
            '$or': [
                {'lemma': lemma},
                {'forms': {'$elemMatch': {'lemma': lemma}}},
                {'meaning': {'$regex': re.escape(query)}}
            ]
        })

        return [word for word in cursor]

    def search_lemma(self, query):
        cursor = self.get_collection().aggregate(
            _create_lemma_search_pipeline(query),
            collation={
                'locale': 'en',
                'strength': 1,
                'normalization': True
            }
        )

        return [word for word in cursor]

    def update(self, word, user):
        query = {'_id': word['_id']}
        old_word = self.get_collection().find_one(
            query
        )
        if old_word:
            self._changelog.create(
                COLLECTION,
                user.profile,
                old_word,
                word
            )
            self.get_collection().update_one(
                query,
                {'$set': word}
            )
        else:
            raise NotFoundError(f'Word {word["_id"]} not found.')
