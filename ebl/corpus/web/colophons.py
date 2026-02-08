import falcon
from marshmallow import fields, Schema

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.transliteration.application.text_schema import TextSchema


class CorpusColophonSchema(Schema):
    siglum = fields.String()
    colophon = fields.Nested(TextSchema, data_key="text")


class CorpusColophonsResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

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
        manuscripts = [
            manuscript
            for manuscript in self._corpus.find_manuscripts(chapter_id)
            if not manuscript.colophon.is_empty
        ]
        resp.media = CorpusColophonSchema().dump(manuscripts, many=True)
