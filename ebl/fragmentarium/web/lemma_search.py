import falcon  # pyre-ignore

from ebl.dispatcher import create_dispatcher
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


class LemmaSearch:
    def __init__(self, finder: FragmentFinder):
        self._dispatch = create_dispatcher({
            frozenset(["word"]): lambda values: finder.find_lemmas(**values),
        })

    @falcon.before(require_scope, "read:fragments")
    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)
