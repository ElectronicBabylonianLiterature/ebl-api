import falcon  # pyre-ignore[21]
from marshmallow import Schema, fields  # pyre-ignore[21]

from ebl.corpus.web.text_schemas import ApiLineSchema
from ebl.marshmallowschema import validate
from ebl.corpus.web.alignments import create_chapter_index
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_text_id
from ebl.users.web.require_scope import require_scope


class LinesDtoSchema(Schema):  # pyre-ignore[11]
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


class LinesResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")  # pyre-ignore[56]
    @validate(LinesDtoSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        self._corpus.update_lines(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            LinesDtoSchema().load(req.media)["lines"],  # pyre-ignore[16]
            req.context.user,
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
