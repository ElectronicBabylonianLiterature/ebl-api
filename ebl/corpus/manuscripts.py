import falcon
from falcon.media.validators.jsonschema import validate

from ebl.corpus.alignments import create_chapter_index
from ebl.corpus.api_serializer import serialize
from ebl.corpus.text_serializer import TextDeserializer
from ebl.corpus.text_utils import create_text_id
from ebl.corpus.texts import MANUSCRIPT_DTO_SCHEMA
from ebl.require_scope import require_scope

MANUSCRIPTS_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'manuscripts': {
            'type': 'array',
            'items': MANUSCRIPT_DTO_SCHEMA
        }
    },
    'required': ['manuscripts']
}


class ManuscriptsResource:

    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'write:texts')
    @validate(MANUSCRIPTS_DTO_SCHEMA)
    def on_post(self,
                req: falcon.Request,
                resp: falcon.Response,
                category: str,
                index: str,
                chapter_index: str) -> None:
        deserializer = TextDeserializer()
        self._corpus.update_manuscripts(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            tuple(
                deserializer.deserialize_manuscript(manuscript)
                for manuscript
                in req.media['manuscripts']
            ),
            req.context['user']
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
