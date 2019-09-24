import falcon
from falcon.media.validators.jsonschema import validate

from ebl.corpus.application.text_utils import create_chapter_index, \
    create_text_id
from ebl.corpus.domain.alignment import Alignment
from ebl.corpus.web.api_serializer import serialize
from ebl.require_scope import require_scope

ALIGNMENT_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'alignment': {
            'type': 'array',
            'items': {
                'type': 'array',
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'value': {
                                'type': 'string'
                            },
                            'alignment': {
                                'type': ['integer', 'null'],
                                'minimum': 0
                            }
                        },
                        'required': ['value']
                    }
                }
            }
        }
    },
    'required': ['alignment']
}


class AlignmentResource:

    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'write:texts')
    @validate(ALIGNMENT_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str,
                chapter_index: str) -> None:
        self._corpus.update_alignment(create_text_id(category, index),
                                      create_chapter_index(chapter_index),
                                      Alignment.from_dict(
                                          req.media['alignment']),
                                      req.context.user)
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
