import falcon
from falcon.media.validators.jsonschema import validate

from ebl.corpus.api_serializer import deserialize, serialize, ApiSerializer
from ebl.bibliography.reference import REFERENCE_DTO_SCHEMA
from ebl.corpus.text import (TextId, Chapter, Manuscript, Line, ManuscriptLine)
from ebl.corpus.enums import Classification, ManuscriptType, Provenance, \
    PeriodModifier, Period, Stage
from ebl.errors import NotFoundError
from ebl.require_scope import require_scope

MANUSCRIPT_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'minimum': 1
        },
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
    'required': ['id', 'siglumDisambiguator', 'museumNumber', 'accession',
                 'periodModifier', 'period', 'provenance', 'type', 'notes',
                 'references']
}


MANUSCRIPT_LINE_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'manuscriptId': {
            'type': 'integer',
            'minimum': 1
        },
        'labels': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'number': {
            'type': 'string'
        },
        'atf': {
            'type': 'string'
        }
    },
    'required': ['manuscriptId', 'labels', 'number', 'atf']
}


LINE_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'number': {
            'type': 'string'
        },
        'reconstruction': {
            'type': 'string'
        },
        'manuscripts': {
            'type': 'array',
            'items': MANUSCRIPT_LINE_DTO_SCHEMA,
        }
    },
    'required': ['number', 'reconstruction', 'manuscripts']
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
        },
        'lines': {
            'type': 'array',
            'items': LINE_DTO_SCHEMA
        }
    },
    'required': ['classification', 'stage', 'name', 'order', 'manuscripts',
                 'lines']
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


def create_text_id(category: str, index: str) -> TextId:
    try:
        return TextId(int(category), int(index))
    except ValueError:
        raise NotFoundError(f'{category}.{index}')


class PublicTextSerializer(ApiSerializer):
    def visit_chapter(self, chapter: Chapter) -> None:
        pass

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        pass

    def visit_line(self, line: Line) -> None:
        pass

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        pass


class TextsResource:
    # pylint: disable=R0903

    auth = {
        'exempt_methods': ['GET']
    }

    def __init__(self, corpus):
        self._corpus = corpus

    def on_get(self,
               _,
               resp: falcon.Response) -> None:
        texts = self._corpus.list()
        resp.media = [
            PublicTextSerializer.serialize(text, False)
            for text in texts
        ]

    @falcon.before(require_scope, 'create:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        text = deserialize(req.media)
        self._corpus.create(text, req.context['user'])
        resp.status = falcon.HTTP_CREATED
        resp.location = f'/texts/{text.category}/{text.index}'
        resp.media = serialize(self._corpus.find(text.id))


class TextResource:
    # pylint: disable=R0903

    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'read:texts')
    def on_get(
            self, _, resp: falcon.Response, category: str, index: str
    ) -> None:
        text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(text)

    @falcon.before(require_scope, 'write:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str) -> None:
        text = deserialize(req.media)
        self._corpus.update(
            create_text_id(category, index),
            text,
            req.context['user']
        )
        updated_text = self._corpus.find(text.id)
        resp.media = serialize(updated_text)
