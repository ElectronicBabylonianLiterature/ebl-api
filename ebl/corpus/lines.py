import falcon
from falcon.media.validators.jsonschema import validate

from ebl.corpus.alignments import create_chapter_index
from ebl.corpus.api_serializer import deserialize_lines, serialize
from ebl.corpus.text_utils import create_text_id
from ebl.corpus.texts import LINE_DTO_SCHEMA
from ebl.require_scope import require_scope

LINES_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'lines': {
            'type': 'array',
            'items': LINE_DTO_SCHEMA
        }
    },
    'required': ['lines']
}


class LinesResource:

    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'write:texts')
    @validate(LINES_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str,
                chapter_index: str) -> None:
        self._corpus.update_lines(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            deserialize_lines(req.media['lines']),
            req.context.user
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
