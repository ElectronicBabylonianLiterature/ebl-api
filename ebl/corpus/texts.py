import falcon
from falcon.media.validators.jsonschema import validate
from ebl.errors import DataError, NotFoundError
from ebl.require_scope import require_scope
from ebl.bibliography.reference import REFERENCE_DTO_SCHEMA
from ebl.corpus.text import (
    Text, Period, Provenance, ManuscriptType, Classification, Stage
)

MANUSCRIPT_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'siglumDisambiguator': {
            'type': 'string'
        },
        'museumNumber': {
            'type': 'string'
        },
        'accession': {
            'type': 'string'
        },
        'period': {
            'type': 'string',
            'enum': [period.long_name for period in Period]
        },
        'provenance': {
            'type': 'string',
            'enum': [provenance.long_name for provenance in Provenance]
        },
        'type': {
            'type': 'string',
            'enum': [type_.long_name for type_ in ManuscriptType]
        },
        'notes': {
            'type': 'string'
        },
        'references': {
            'type': 'array',
            'items': REFERENCE_DTO_SCHEMA
        }
    },
    'required': ['siglumDisambiguator', 'museumNumber', 'accession', 'period',
                 'provenance', 'type', 'notes', 'references']
}


CHAPTER_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'classification': {
            'type': 'string',
            'enum': [classification.value for classification in Classification]
        },
        'stage': {
            'type': 'string',
            'enum': [stage.long_name for stage in Stage]
        },
        'name': {
            'type': 'string',
            'minLength': 1
        },
        'order': {
            'type': 'integer'
        },
        'manuscripts': {
            'type': 'array',
            'items': MANUSCRIPT_DTO_SCHEMA
        }
    },
    'required': ['classification', 'stage', 'name', 'order', 'manuscripts']
}


TEXT_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'category': {
            'type': 'integer',
            'minimum': 0
        },
        'index': {
            'type': 'integer',
            'minimum': 0
        },
        'name': {
            'type': 'string',
            'minLength': 1
        },
        'numberOfVerses': {
            'type': 'integer',
            'minimum': 0
        },
        'approximateVerses': {
            'type': 'boolean'
        },
        'chapters': {
            'type': 'array',
            'items': CHAPTER_DTO_SCHEMA
        }
    },
    'required': ['category', 'index', 'name', 'numberOfVerses',
                 'approximateVerses', 'chapters']
}


def parse_text(media):
    try:
        return Text.from_dict(media)
    except ValueError as error:
        raise DataError(error)


@falcon.before(require_scope, 'create:texts')
class TextsResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'create:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_put(self, req, resp):
        text = parse_text(req.media)
        self._corpus.create(text, req.context['user'])
        resp.status = falcon.HTTP_NO_CONTENT


class TextResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'read:texts')
    def on_get(self, _, resp, category, index):
        try:
            text = self._corpus.find(int(category), int(index))
            resp.media = text.to_dict(True)
        except ValueError:
            raise NotFoundError(f'{category}.{index}')

    @falcon.before(require_scope, 'write:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self, req, resp, category, index):
        text = parse_text(req.media)
        try:
            self._corpus.update(
                int(category),
                int(index),
                text,
                req.context['user']
            )
            updated_text = self._corpus.find(text.category, text.index)
            resp.media = updated_text.to_dict(Text)
        except ValueError:
            raise NotFoundError(f'{category}.{index}')
