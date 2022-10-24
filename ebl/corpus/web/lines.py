from typing import Tuple

import falcon
from falcon_caching import Cache
from marshmallow import Schema, fields, post_load

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.web.chapter_schemas import ApiChapterSchema, ApiLineSchema
from ebl.corpus.web.display_schemas import LineDetailsDisplay, LineDetailsDisplaySchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.errors import NotFoundError
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class LineEditSchema(Schema):
    index = fields.Integer(required=True)
    line = fields.Nested(ApiLineSchema, required=True)

    @post_load
    def make_line_edit(self, data: dict, **kwargs) -> Tuple[int, Line]:
        return data["index"], data["line"]


class LinesUpdateSchema(Schema):
    new = fields.Nested(ApiLineSchema, many=True, required=True)
    deleted = fields.List(fields.Integer, required=True)
    edited = fields.Nested(LineEditSchema, many=True, required=True)

    @post_load
    def make_lines_update(self, data: dict, **kwargs) -> LinesUpdate:
        return LinesUpdate(data["new"], set(data["deleted"]), dict(data["edited"]))


class LinesImportSchema(Schema):
    atf = fields.String(required=True)


class LinesResource:
    def __init__(self, corpus: Corpus, cache: Cache):
        self._corpus = corpus
        self._cache = cache

    @falcon.before(require_scope, "write:texts")
    @validate(LinesUpdateSchema())
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
        self._cache.delete(str(chapter_id))
        updated_chapter = self._corpus.update_lines(
            chapter_id, LinesUpdateSchema().load(req.media), req.context.user
        )
        resp.media = ApiChapterSchema().dump(updated_chapter)


class LinesImportResource:
    def __init__(self, corpus: Corpus):
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
        updated_chapter = self._corpus.import_lines(
            chapter_id, req.media["atf"], req.context.user
        )
        resp.media = ApiChapterSchema().dump(updated_chapter)


class LineResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus
    @falcon.before(require_scope, "read:texts")
    def on_get(
        self,
        _,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
        number: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)

        try:
            line, manuscripts = self._corpus.find_line_with_manuscript_joins(
                chapter_id, int(number)
            )
            line_details = LineDetailsDisplay.from_line_manuscripts(line, manuscripts)
            resp.media = LineDetailsDisplaySchema().dump(line_details)
        except (IndexError, ValueError) as error:
            raise NotFoundError(f"{chapter_id} line {number} not found.") from error
