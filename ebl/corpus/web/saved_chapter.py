from typing import Callable, Mapping, TypeVar, cast

import falcon
from marshmallow import Schema

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.chapter_edit_writer import SavedChapter
from ebl.corpus.application.lines_pagination import (
    LinesView,
    parse_lines_view,
    parse_required_revision,
)
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.web.chapter_outline_schemas import ChapterOutlineSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.users.domain.user import User
from ebl.users.web.user_request import UserRequest

Edit = TypeVar("Edit")
EditSave = Callable[[ChapterId, Edit, str, User], SavedChapter]


def dump_saved_chapter(saved: SavedChapter, view: LinesView) -> dict:
    return cast(
        dict,
        ChapterOutlineSchema().dump(saved.outline)
        if view is LinesView.OUTLINE
        else ApiChapterSchema().dump(saved.chapter),
    )


class RevisionSaveResponder:
    def __init__(self, cache: ChapterCache) -> None:
        self._cache = cache

    def respond(
        self,
        req: UserRequest,
        resp: falcon.Response,
        chapter: Mapping[str, str],
        schema: Schema,
        save: EditSave[Edit],
    ) -> None:
        edit = cast(Edit, schema.load(req.media))
        chapter_id = create_chapter_id(**chapter)
        view = parse_lines_view(req.params)
        revision = parse_required_revision(req.params)
        with self._cache.updating_chapter(chapter_id):
            saved = save(chapter_id, edit, revision, req.context.user)
        resp.media = dump_saved_chapter(saved, view)
