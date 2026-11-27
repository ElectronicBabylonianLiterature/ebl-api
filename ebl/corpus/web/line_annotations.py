from abc import ABC, abstractmethod
from functools import partial
from typing import Callable, Mapping, cast

import falcon
from marshmallow import Schema, fields

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter, SavedChapter
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_schema import LineVariantLemmatizationSchema
from ebl.corpus.application.lines_pagination import (
    parse_lines_view,
    parse_required_revision,
)
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.web.alignment_schema import ManuscriptAlignmentSchema
from ebl.corpus.web.saved_chapter import dump_saved_chapter
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.errors import NotFoundError
from ebl.marshmallowschema import validate
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest

LineSave = Callable[[str, User], SavedChapter]


class LineAlignmentSchema(Schema):
    variants = fields.List(
        fields.Nested(ManuscriptAlignmentSchema, many=True),
        required=True,
        data_key="alignment",
    )


class LineLemmatizationSchema(Schema):
    variants = fields.List(
        fields.Nested(LineVariantLemmatizationSchema),
        required=True,
        data_key="lemmatization",
    )


def parse_line_position(chapter_id: ChapterId, number: str) -> int:
    try:
        return int(number)
    except ValueError as error:
        raise NotFoundError(f"{chapter_id} line {number} not found.") from error


class LineSaveResource(ABC):
    def __init__(self, writer: ChapterEditWriter, cache: ChapterCache) -> None:
        self._writer = writer
        self._cache = cache

    @abstractmethod
    def _create_save(self, chapter_id: ChapterId, index: int, media: dict) -> LineSave:
        raise NotImplementedError

    def _save(
        self,
        req: UserRequest,
        resp: falcon.Response,
        number: str,
        chapter: Mapping[str, str],
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        save = self._create_save(
            chapter_id, parse_line_position(chapter_id, number), req.media
        )
        view = parse_lines_view(req.params)
        revision = parse_required_revision(req.params)
        with self._cache.updating_chapter(chapter_id):
            saved = save(revision, req.context.user)
        resp.media = dump_saved_chapter(saved, view)


class LineAlignmentResource(LineSaveResource):
    @falcon.before(require_scope, "write:texts")
    @validate(LineAlignmentSchema())
    def on_post(
        self, req: UserRequest, resp: falcon.Response, number: str, **chapter: str
    ) -> None:
        self._save(req, resp, number, chapter)

    def _create_save(self, chapter_id: ChapterId, index: int, media: dict) -> LineSave:
        variants = cast(dict, LineAlignmentSchema().load(media))["variants"]
        alignment = LineAlignment(index, variants)
        return partial(self._writer.save_line_alignment, chapter_id, alignment)


class LineLemmatizationResource(LineSaveResource):
    @falcon.before(require_scope, "write:texts")
    @validate(LineLemmatizationSchema())
    def on_post(
        self, req: UserRequest, resp: falcon.Response, number: str, **chapter: str
    ) -> None:
        self._save(req, resp, number, chapter)

    def _create_save(self, chapter_id: ChapterId, index: int, media: dict) -> LineSave:
        variants = cast(dict, LineLemmatizationSchema().load(media))["variants"]
        lemmatization = LineLemmatization(index, variants)
        return partial(self._writer.save_line_lemmatization, chapter_id, lemmatization)
