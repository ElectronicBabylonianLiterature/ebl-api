import falcon
from falcon.media.validators.jsonschema import validate
import pydash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from ebl.require_scope import require_scope


LEMMA_DTO_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'string'
    },
    'minItems': 1
}


NOTES_DTO_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'string'
    }
}


VOWELS_DTO_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'value': {
                'type': 'array',
                'items': {
                    'type': 'string'
                }
            },
            'notes': NOTES_DTO_SCHEMA
        },
        'required': ['value', 'notes']
    }
}


WORD_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        '_id': {'type': 'string'},
        'lemma': LEMMA_DTO_SCHEMA,
        'homonym': {'type': 'string'},
        'attested': {'type': 'boolean'},
        'legacyLemma': {'type': 'string'},
        'forms': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'lemma': LEMMA_DTO_SCHEMA,
                    'notes': NOTES_DTO_SCHEMA,
                    'attested': {'type': 'boolean'}
                },
                'required': ['lemma', 'notes', 'attested']
            }
        },
        'meaning': {'type': 'string'},
        'logograms': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'logogram': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'minItems': 1
                    },
                    'notes': NOTES_DTO_SCHEMA
                },
                'required': ['logogram', 'notes']
            }
        },
        'derived': {
            'type': 'array',
            'items': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'lemma': LEMMA_DTO_SCHEMA,
                        'notes': NOTES_DTO_SCHEMA,
                        'homonym': {'type': 'string'}
                    },
                    'required': ['lemma', 'notes', 'homonym']
                }
            },
            'minItems': 1
        },
        'derivedFrom': {
            'type': ['null', 'object'],
            'properties': {
                'lemma': LEMMA_DTO_SCHEMA,
                'notes': NOTES_DTO_SCHEMA,
                'homonym': {'type': 'string'}
            },
            'required': ['lemma', 'notes', 'homonym']
        },
        'amplifiedMeanings': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'key': {'type': 'string'},
                    'meaning': {'type': 'string'},
                    'vowels': VOWELS_DTO_SCHEMA,
                    'entries': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'meaning': {'type': 'string'},
                                'vowels': VOWELS_DTO_SCHEMA
                            },
                            'required': ['meaning', 'vowels']
                        }
                    }
                },
                'required': ['key', 'meaning', 'vowels', 'entries']
            }
        },
        'source': {'type': 'string'},
        'roots': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'pos': {'type': 'string'}
    },
    'required': [
        'lemma',
        'homonym',
        'attested',
        'legacyLemma',
        'forms',
        'meaning',
        'logograms',
        'derived',
        'derivedFrom',
        'amplifiedMeanings',
        'source',
        'pos'
    ]
}


class WordsResource:

    def __init__(self, dictionary):
        self._dictionary = dictionary

    @falcon.before(require_scope, 'read:words')
    def on_get(self, _req, resp, object_id):
        try:
            word = self._dictionary.find(ObjectId(object_id))
            resp.media = pydash.defaults({'_id': object_id}, word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'write:words')
    @validate(WORD_DTO_SCHEMA)
    def on_post(self, req, resp, object_id):
        try:
            word = {
                **req.media,
                '_id': ObjectId(object_id)
            }
            self._dictionary.update(word, req.context['user'])
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
