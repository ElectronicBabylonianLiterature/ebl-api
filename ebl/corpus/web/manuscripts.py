import falcon
from typing import cast
from marshmallow import Schema, fields

from ebl.cache.application.custom_cache import ChapterCache
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.lines_pagination import parse_lines_view, parse_revision
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.web.chapter_schemas import ApiManuscriptSchema, MuseumNumberString
from ebl.corpus.web.saved_chapter import dump_saved_chapter
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


class ManuscriptDtoSchema(Schema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    uncertain_fragments = fields.List(
        MuseumNumberString(), load_default=(), data_key="uncertainFragments"
    )


class ManuscriptsResource:
    def __init__(
        self,
        writer: ChapterEditWriter,
        cache: ChapterCache,
        provenance_service: ProvenanceService,
    ) -> None:
        self._writer = writer
        self._cache = cache
        self._provenance_service = provenance_service

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        **chapter: str,
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        manuscripts = self._writer.find_manuscripts_with_joins(chapter_id)
        resp.media = ApiManuscriptSchema().dump(manuscripts, many=True)

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
        schema = ManuscriptDtoSchema(
            context={"provenance_service": self._provenance_service}
        )
        errors = schema.validate(req.media)
        if errors:
            raise falcon.HTTPBadRequest(
                title="Request data failed validation", description=errors
            )
        dto = cast(dict, schema.load(req.media))
        with self._cache.updating_chapter(chapter_id):
            saved = self._writer.save_manuscripts(
                chapter_id,
                ManuscriptsUpdate(
                    dto["manuscripts"], tuple(dto["uncertain_fragments"])
                ),
                revision,
                req.context.user,
            )
        resp.media = dump_saved_chapter(saved, view)
