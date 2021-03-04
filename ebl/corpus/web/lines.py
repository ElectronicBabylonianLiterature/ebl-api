import falcon
from marshmallow import Schema, fields

from ebl.corpus.web.text_schemas import ApiLineSchema
from ebl.marshmallowschema import validate
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.users.web.require_scope import require_scope


class LinesDtoSchema(Schema):
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


class LinesImportSchema(Schema):
    atf = fields.String(required=True)


class LinesResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(LinesDtoSchema())
    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        chapter_id = create_chapter_id(category, index, chapter_index)
        self._corpus.update_lines(
            chapter_id, LinesDtoSchema().load(req.media)["lines"], req.context.user
        )
        updated_text = self._corpus.find(chapter_id.text_id)
        resp.media = serialize(updated_text)


class LinesImportResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(LinesImportSchema())
    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        chapter_id = create_chapter_id(category, index, chapter_index)
        self._corpus.import_lines(chapter_id, req.media["atf"], req.context.user)
        updated_text = self._corpus.find(chapter_id.text_id)
        resp.media = serialize(updated_text)
