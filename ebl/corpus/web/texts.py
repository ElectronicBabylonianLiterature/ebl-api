import falcon

from ebl.corpus.application.corpus import Corpus

from ebl.corpus.web.text_schema import ApiTextSchema
from ebl.corpus.web.text_utils import create_text_id


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


class TextsAllResource:
    def __init__(
        self,
        corpus: Corpus,
    ):
        self._corpus = corpus

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._corpus.list_all_texts()
