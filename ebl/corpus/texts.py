import falcon
from falcon.media.validators.jsonschema import validate
import pydash
from parsy import ParseError

from ebl.bibliography.reference import REFERENCE_DTO_SCHEMA
from ebl.corpus.text import (Classification, ManuscriptType, Period,
                             PeriodModifier, Provenance, Stage, Text, TextId)
from ebl.text.labels import LineNumberLabel
from ebl.errors import DataError, NotFoundError
from ebl.require_scope import require_scope
from ebl.text.text_parser import TEXT_LINE


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


def parse_text(media: dict) -> Text:
    def parse_manuscript(manuscript_dto: dict):
        try:
            atf_line_number =\
                LineNumberLabel(manuscript_dto['number']).to_atf()
            line = \
                TEXT_LINE.parse(f'{atf_line_number} {manuscript_dto["atf"]}')
        except ParseError as error:
            raise DataError(error)

        return pydash.omit({
            **manuscript_dto,
            'line': line.to_dict()
        }, 'atf')

    parsed_media = {
        **media,
        'chapters': [
            {
                **chapter,
                'lines': [
                    {
                        **line,
                        'manuscripts': [
                            parse_manuscript(manuscript)
                            for manuscript in line['manuscripts']
                        ]
                    } for line in chapter['lines']
                ]
            } for chapter in media['chapters']
        ]
    }
    try:
        return Text.from_dict(parsed_media)
    except ValueError as error:
        raise DataError(error)


def to_dto(text):
    return {
        **text.to_dict(True),
        'chapters': [
            {
                **chapter.to_dict(True),
                'lines': [
                    {
                        **line.to_dict(),
                        'manuscripts': [
                            pydash.omit({
                                **manuscript.to_dict(),
                                'number':
                                    manuscript.line.line_number.to_value(),
                                'atf': manuscript.line.atf[len(manuscript
                                                               .line
                                                               .line_number
                                                               .to_atf()) + 1:]
                            }, 'line') for manuscript in line.manuscripts
                        ]
                    } for line in chapter.lines
                ]
            } for chapter in text.chapters
        ]
    }


def create_text_id(category: str, index: str) -> TextId:
    try:
        return TextId(int(category), int(index))
    except ValueError:
        raise NotFoundError(f'{category}.{index}')


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
        resp.media = to_dto(self._corpus.find(text.id))


class TextResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'read:texts')
    def on_get(
            self, _, resp: falcon.Response, category: str, index: str
    ) -> None:
        text = self._corpus.find(create_text_id(category, index))
        resp.media = to_dto(text)

    @falcon.before(require_scope, 'write:texts')
    @validate(TEXT_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str) -> None:
        text = parse_text(req.media)
        self._corpus.update(
            create_text_id(category, index),
            text,
            req.context['user']
        )
        updated_text = self._corpus.find(text.id)
        resp.media = to_dto(updated_text)
