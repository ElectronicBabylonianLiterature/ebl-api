import falcon

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.users.web.require_scope import require_scope


class ChaptersResource:
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
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(chapter)
