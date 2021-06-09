import falcon

from ebl.corpus.web.alignment_schema import AlignmentSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class AlignmentResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(AlignmentSchema())
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
        self._corpus.update_alignment(
            chapter_id, AlignmentSchema().load(req.media), req.context.user
        )
        updated_chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(updated_chapter)
