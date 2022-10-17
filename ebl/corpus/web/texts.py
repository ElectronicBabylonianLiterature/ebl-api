import falcon
from falcon_caching import Cache
from falcon_caching.utils import register

from ebl.cache import DEFAULT_TIMEOUT, cache_control
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
from ebl.users.web.require_scope import require_scope


class TextsResource:
    auth = {"exempt_methods": ["GET"]}

    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    def on_get(self, _, resp: falcon.Response) -> None:
        resp.media = ApiTextSchema().dump(self._corpus.list(), many=True)


class TextResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "read:texts")
    def on_get(
        self, _, resp: falcon.Response, genre: str, category: str, index: str
    ) -> None:
        text = self._corpus.find(create_text_id(genre, category, index))
        resp.media = ApiTextSchema().dump(text)


def make_text_search_resource(
    cache: Cache,
    corpus: Corpus,
    transliteration_query_factory: TransliterationQueryFactory,
):
    class TextSearchResource:
        def __init__(
            self,
            corpus: Corpus,
            transliteration_query_factory: TransliterationQueryFactory,
        ):
            self._corpus = corpus
            self._transliteration_query_factory = transliteration_query_factory

        @register(
            falcon.before(require_scope, "read:texts"),
            cache_control(["private", f"max-age={DEFAULT_TIMEOUT}"]),
            cache.cached(timeout=DEFAULT_TIMEOUT),
        )
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

    return TextSearchResource(corpus, transliteration_query_factory)
