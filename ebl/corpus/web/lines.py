from typing import Tuple, cast

import falcon
from marshmallow import Schema, fields, post_load

from ebl.cache.application.custom_cache import ChapterCache
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.corpus.application.chapter_edit_reader import ChapterEditReader
from ebl.corpus.application.chapter_lines_writer import ChapterLinesWriter, SavedLines
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.lines_pagination import (
    LinesView,
    parse_lines_page_query,
    parse_lines_view,
    parse_revision,
)
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.web.chapter_outline_schemas import (
    ChapterOutlineSchema,
    create_lines_page_schema,
)
from ebl.corpus.web.chapter_schemas import ApiChapterSchema, ApiLineSchema
from ebl.corpus.web.display_schemas import LineDetailsDisplay, LineDetailsDisplaySchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.errors import NotFoundError
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


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


def _dump_saved_lines(saved: SavedLines, view: LinesView) -> dict:
    return cast(
        dict,
        ChapterOutlineSchema().dump(
            ChapterOutline.of_chapter(saved.chapter, saved.revision)
        )
        if view is LinesView.OUTLINE
        else ApiChapterSchema().dump(saved.chapter),
    )


class LinesResource:
    def __init__(
        self,
        writer: ChapterLinesWriter,
        cache: ChapterCache,
        provenance_service: ProvenanceService,
        reader: ChapterEditReader,
    ) -> None:
        self._writer = writer
        self._cache = cache
        self._provenance_service = provenance_service
        self._reader = reader

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        pagination = parse_lines_page_query(req.params)
        resp.media = create_lines_page_schema(pagination.include_tokens).dump(
            self._reader.find_lines(chapter_id, pagination)
        )

    @falcon.before(require_scope, "write:texts")
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        view = parse_lines_view(req.params)
        revision = parse_revision(req.params)
        schema = LinesUpdateSchema(
            context={"provenance_service": self._provenance_service}
        )
        errors = schema.validate(req.media)
        if errors:
            raise falcon.HTTPBadRequest(
                title="Request data failed validation", description=errors
            )
        with self._cache.updating_chapter(chapter_id):
            saved = self._writer.save_lines(
                chapter_id,
                cast(LinesUpdate, schema.load(req.media)),
                revision,
                req.context.user,
            )
        resp.media = _dump_saved_lines(saved, view)


class LinesImportResource:
    def __init__(self, corpus: Corpus, cache: ChapterCache):
        self._corpus = corpus
        self._cache = cache

    @falcon.before(require_scope, "write:texts")
    @validate(LinesImportSchema())
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        with self._cache.updating_chapter(chapter_id):
            updated_chapter = self._corpus.import_lines(
                chapter_id, req.media["atf"], req.context.user
            )
        resp.media = ApiChapterSchema().dump(updated_chapter)


class LineResource:
    def __init__(self, corpus: Corpus, cache: ChapterCache):
        self._corpus = corpus
        self._cache = cache

    def on_get(
        self,
        _,
        resp: falcon.Response,
        number: str,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        cache_id = f"{str(chapter_id)} line-{number}"

        def create() -> dict:
            line, manuscripts = self._corpus.find_line_with_manuscript_joins(
                chapter_id, int(number)
            )
            line_details = LineDetailsDisplay.from_line_manuscripts(line, manuscripts)
            return cast(dict, LineDetailsDisplaySchema().dump(line_details))

        try:
            resp.media = self._cache.get_or_create(chapter_id, cache_id, create)
        except (IndexError, ValueError) as error:
            raise NotFoundError(f"{chapter_id} line {number} not found.") from error
