import falcon  # pyre-ignore

from ebl.dispatcher import create_dispatcher
from ebl.users.web.require_scope import require_scope


class WordSearch:
    def __init__(self, dictionary):
        self._dispatch = create_dispatcher(
            {"query": lambda x: dictionary.search(*x),
             "lemma": lambda x: dictionary.search_lemma(*x), }
        )

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)
