import falcon
from marshmallow import fields, Schema

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.users.web.require_scope import require_scope
from ebl.transliteration.application.text_schema import TextSchema


class UnplacedLinesSchema(Schema):
    siglum = fields.String()
    unplaced_lines = fields.Nested(TextSchema, data_key="text")


class UnplacedLinesResource:

    auth = {"exempt_methods": ["GET"]}

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
        manuscripts = [
            manuscript
            for manuscript in self._corpus.find_manuscripts(chapter_id)
            if not manuscript.unplaced_lines.is_empty
        ]
        resp.media = UnplacedLinesSchema().dump(manuscripts, many=True)
