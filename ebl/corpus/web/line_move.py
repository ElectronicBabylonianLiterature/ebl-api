from typing import cast

import falcon
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Range

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.lines_pagination import (
    parse_lines_view,
    parse_required_revision,
)
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.web.saved_chapter import dump_saved_chapter
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


class LineMoveSchema(Schema):
    source = fields.Integer(
        required=True, strict=True, validate=Range(min=0), data_key="from"
    )
    target = fields.Integer(
        required=True, strict=True, validate=Range(min=0), data_key="to"
    )

    @post_load
    def make_line_move(self, data: dict, **kwargs) -> LineMove:
        return LineMove(data["source"], data["target"])


class LineMoveResource:
    def __init__(self, writer: ChapterEditWriter, cache: ChapterCache) -> None:
        self._writer = writer
        self._cache = cache

    @falcon.before(require_scope, "write:texts")
    @validate(LineMoveSchema())
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        view = parse_lines_view(req.params)
        revision = parse_required_revision(req.params)
        move = cast(LineMove, LineMoveSchema().load(req.media))
        with self._cache.updating_chapter(chapter_id):
            saved = self._writer.move_line(chapter_id, move, revision, req.context.user)
        resp.media = dump_saved_chapter(saved, view)
