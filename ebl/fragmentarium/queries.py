import re

from ebl.fragment.record import RecordType
from ebl.text.word_cleaner import IGNORE_REGEX, clean_word

HAS_TRANSLITERATION = {'text.lines.type': {'$exists': True}}
NUMBER_OF_LATEST_TRANSLITERATIONS = 40


def fragment_is(fragment):
    return {'_id': fragment.number}


def number_is(number):
    return {
        '$or': [
            {'_id': number},
            {'cdliNumber': number},
            {'accession': number}
        ]
    }


def sample_size_one():
    return {
        '$sample': {
            'size': 1
        }
    }


def aggregate_random():
    return [
        {'$match': HAS_TRANSLITERATION},
        sample_size_one()
    ]


def aggregate_lemmas(word):
    cleaned_word = clean_word(word)
    word_regex = (
            f'^{IGNORE_REGEX}' +
            ''.join([
                f"{re.escape(char)}{IGNORE_REGEX}" for char in cleaned_word
            ]) +
            '$'
    )
    pipeline = [
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
    ]
    return pipeline


def aggregate_latest():
    temp_field_name = '_temp'
    return [
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
    ]


def aggregate_needs_revision():
    return [
        {'$match': {'record.type': 'Transliteration'}},
        {'$unwind': '$record'},
        {'$sort': {'record.date': 1}},
        {'$group': {
            '_id': '$_id',
            'accession': {'$first': '$accession'},
            'description': {'$first': '$description'},
            'record': {'$push': '$record'}
        }},
        {
            '$addFields': {
                'transliterations': {
                    '$filter': {
                        'input': '$record',
                        'as': 'item',
                        'cond': {'$eq': ['$$item.type', 'Transliteration']}
                    }
                },
                'revisions': {
                    '$filter': {
                        'input': '$record',
                        'as': 'item',
                        'cond': {'$eq': ['$$item.type', 'Revision']}
                    }
                }
            }
        },
        {
            '$addFields': {
                'transliterators': {
                    '$map':
                        {
                            'input': '$transliterations',
                            'as': 'item',
                            'in': '$$item.user'
                        }
                },
                'dates': {
                    '$map':
                        {
                            'input': '$transliterations',
                            'as': 'item',
                            'in': '$$item.date'
                        }
                },
                'revisors':
                    {
                        '$map':
                            {
                                'input': '$revisions',
                                'as': 'item',
                                'in': '$$item.user'
                            }
                    }
            }
        },
        {'$match': {'$expr': {
            '$eq': [{'$setDifference': ['$revisors', '$transliterators']},
                    []]}}},
        {'$project': {'accession': 1, 'description': 1,
                      'date': {'$arrayElemAt': ['$dates', 0]},
                      'editor': {'$arrayElemAt': ['$transliterators', 0]}}},
        {'$sort': {'date': 1}},
        {'$limit': 20}
    ]


def aggregate_interesting():
    return [
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
    ]
