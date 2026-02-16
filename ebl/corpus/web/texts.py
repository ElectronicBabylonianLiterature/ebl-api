import falcon

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.chapter_info_schema import (
    ChapterInfosPaginationSchema,
)
from ebl.corpus.web.text_schema import ApiTextSchema
from ebl.corpus.web.text_utils import create_text_id
from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


class TextsResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    def on_get(self, _, resp: falcon.Response) -> None:
        resp.media = ApiTextSchema().dump(self._corpus.list(), many=True)


class TextResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    def on_get(
        self, _, resp: falcon.Response, genre: str, category: str, index: str
    ) -> None:
        text = self._corpus.find(create_text_id(genre, category, index))
        resp.media = ApiTextSchema().dump(text)


class TextSearchResource:
    def __init__(
        self, corpus: Corpus, transliteration_query_factory: TransliterationQueryFactory
    ):
        self._corpus = corpus
        self._transliteration_query_factory = transliteration_query_factory

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        query = self._transliteration_query_factory.create(
            req.params["transliteration"]
        )
        try:
            pagination_index = int(req.params["paginationIndex"])
        except ValueError as error:
            raise DataError("Pagination Index has to be a number") from error
        chapters = self._corpus.search_transliteration(query, pagination_index)
        resp.media = ChapterInfosPaginationSchema().dump(chapters)


class TextsAllResource:
    def __init__(
        self,
        corpus: Corpus,
    ):
        self._corpus = corpus

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._corpus.list_all_texts()
