import json
import falcon
import pydash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from ebl.require_scope import require_scope


WORD_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        '_id': {'type': 'string'},
        'lemma': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
            'minItems': 1
        },
        'homonym': {'type': 'string'},
        'attested': {'type': 'boolean'},
        'legacyLemma': {'type': 'string'},
        'forms': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'lemma': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'minItems': 1
                    },
                    'notes': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        }
                    },
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
                    'notes': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
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
                        'lemma': {
                            'type': 'array',
                            'items': {
                                'type': 'string'
                            },
                            'minItems': 1
                        },
                        'notes': {
                            'type': 'array',
                            'items': {
                                'type': 'string'
                            }
                        },
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
                'lemma': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    },
                    'minItems': 1
                },
                'notes': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                },
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
                    'vowels': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string'
                                    },
                                    'minItems': 2,
                                    'maxItems': 2
                                },
                                'notes': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': ['value', 'notes']
                        }
                    },
                    'entries': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'meaning': {'type': 'string'},
                                'vowels': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'value': {
                                                'type': 'array',
                                                'items': {
                                                    'type': 'string'
                                                },
                                                'minItems': 2,
                                                'maxItems': 2
                                            },
                                            'notes': {
                                                'type': 'array',
                                                'items': {
                                                    'type': 'string'
                                                }
                                            }
                                        },
                                        'required': ['value', 'notes']
                                    }
                                }
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
        '_id',
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
        'roots',
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
    def on_post(self, req, resp, object_id):
        try:
            word = json.loads(req.stream.read())
            word['_id'] = ObjectId(object_id)
            self._dictionary.update(word, req.context['user'])
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
