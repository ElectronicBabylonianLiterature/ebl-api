import falcon

from ebl.corpus.application.chapter_edit_reader import ChapterEditReader
from ebl.corpus.web.chapter_outline_schemas import ChapterOutlineSchema
from ebl.corpus.web.text_utils import create_chapter_id


class ChapterOutlineResource:
    def __init__(self, reader: ChapterEditReader) -> None:
        self._reader = reader

    def on_get(
        self,
        _: falcon.Request,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        resp.media = ChapterOutlineSchema().dump(self._reader.find_outline(chapter_id))
