import falcon

from ebl.dispatcher import create_dispatcher
from ebl.require_scope import require_scope


class WordSearch:
    # pylint: disable=R0903
    def __init__(self, dictionary):
        self._dispatch = create_dispatcher({
            'query': dictionary.search,
            'lemma': dictionary.search_lemma,
        })

    @falcon.before(require_scope, 'read:words')
    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)
