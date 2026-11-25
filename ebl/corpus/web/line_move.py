import falcon
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Range

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.web.saved_chapter import RevisionSaveResponder
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
        self._responder = RevisionSaveResponder(cache)

    @falcon.before(require_scope, "write:texts")
    @validate(LineMoveSchema())
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        self._responder.respond(
            req, resp, chapter, LineMoveSchema(), self._writer.move_line
        )
