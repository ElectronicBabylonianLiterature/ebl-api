import falcon
from ebl.dispatcher import create_dispatcher
from ebl.require_scope import require_scope


class WordSearch:
    # pylint: disable=R0903
    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._dispatch = create_dispatcher({
            'query': self._search,
            'lemma': self._search_lemma,
        })

    @falcon.before(require_scope, 'read:words')
    def on_get(self, req, resp):
        resp.media = self._dispatch(req)

    def _search(self, query):
        return self._dictionary.search(query)

    def _search_lemma(self, lemma):
        return self._dictionary.search_lemma(lemma)
