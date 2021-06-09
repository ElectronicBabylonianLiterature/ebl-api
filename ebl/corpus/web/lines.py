import falcon
from marshmallow import Schema, fields

from ebl.corpus.web.chapter_schemas import ApiChapterSchema, ApiLineSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
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
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        self._corpus.update_lines(
            chapter_id, LinesDtoSchema().load(req.media)["lines"], req.context.user
        )
        updated_chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(updated_chapter)


class LinesImportResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(LinesImportSchema())
    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        self._corpus.import_lines(chapter_id, req.media["atf"], req.context.user)
        updated_chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(updated_chapter)
