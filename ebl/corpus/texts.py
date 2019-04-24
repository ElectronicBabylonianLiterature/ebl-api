import falcon
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.reference import REFERENCE_DTO_SCHEMA
from ebl.corpus.text import (Classification, ManuscriptType, Period,
                             PeriodModifier, Provenance, Stage, Text, TextId)
from ebl.errors import DataError, NotFoundError
from ebl.require_scope import require_scope

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
        'periodModifier': {
            'type': 'string',
            'enum': [modifier.value for modifier in PeriodModifier]
        },
        'period': {
            'type': 'string',
            'enum': [period.value for period in Period]
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
    'required': ['siglumDisambiguator', 'museumNumber', 'accession',
                 'periodModifier', 'period', 'provenance', 'type', 'notes',
                 'references']
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
            'enum': [stage.value for stage in Stage]
        },
        'version': {
            'type': 'string'
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


def parse_text(media: dict) -> Text:
    try:
        return Text.from_dict(media)
    except ValueError as error:
        raise DataError(error)


def create_text_id(category: str, index: str) -> TextId:
    return TextId(int(category), int(index))


@falcon.before(require_scope, 'create:texts')
class TextsResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'create:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        text = parse_text(req.media)
        self._corpus.create(text, req.context['user'])
        resp.status = falcon.HTTP_CREATED
        resp.location = f'/texts/{text.category}/{text.index}'
        resp.media = self._corpus.find(text.id).to_dict(True)


class TextResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'read:texts')
    def on_get(
            self, _, resp: falcon.Response, category: str, index: str
    ) -> None:
        try:
            text = self._corpus.find(create_text_id(category, index))
            resp.media = text.to_dict(True)
        except ValueError:
            raise NotFoundError(f'{category}.{index}')

    @falcon.before(require_scope, 'write:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str) -> None:
        text = parse_text(req.media)
        try:
            self._corpus.update(
                create_text_id(category, index),
                text,
                req.context['user']
            )
            updated_text = self._corpus.find(text.id)
            resp.media = updated_text.to_dict(True)
        except ValueError:
            raise NotFoundError(f'{category}.{index}')
