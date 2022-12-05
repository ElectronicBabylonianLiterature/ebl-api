import falcon

from ebl.dispatcher import create_dispatcher
from ebl.users.web.require_scope import require_scope


class WordSearch:
    def __init__(self, dictionary):
        self._dispatch = create_dispatcher(
            {
                frozenset(["query"]): lambda value: dictionary.search(**value),
                frozenset(["lemma"]): lambda value: dictionary.search_lemma(**value),
                frozenset(["lemmas"]): lambda value: dictionary.find_many(
                    value["lemmas"].split(",")
                ),
            }
        )

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)
