import falcon
from typing import cast

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.alignment import Alignment
from ebl.corpus.web.alignment_schema import AlignmentSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


class AlignmentResource:
    def __init__(self, corpus: Corpus, cache: ChapterCache) -> None:
        self._corpus = corpus
        self._cache = cache

    @falcon.before(require_scope, "write:texts")
    @validate(AlignmentSchema())
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        with self._cache.updating_chapter(chapter_id):
            updated_chapter = self._corpus.update_alignment(
                chapter_id,
                cast(Alignment, AlignmentSchema().load(req.media)),
                req.context.user,
            )
        resp.media = ApiChapterSchema().dump(updated_chapter)
