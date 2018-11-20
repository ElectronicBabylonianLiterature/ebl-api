import falcon

from ebl.dispatcher import create_dispatcher
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliteration import Transliteration


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium
        self._dispatch = create_dispatcher({
            'number': self._search,
            'random': self._find_random,
            'interesting': self._find_interesting,
            'transliteration': self._search_transliteration
        })

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        user = req.context['user']
        fragments = self._dispatch(req)
        resp.media = [fragment.to_dict_for(user) for fragment in fragments]

    def _search(self, number):
        return self._fragmentarium.search(number)

    def _find_random(self, _):
        return self._fragmentarium.find_random()

    def _find_interesting(self, _):
        return self._fragmentarium.find_interesting()

    def _search_transliteration(self, query):
        transliteration = Transliteration(query)
        return self._fragmentarium.search_signs(transliteration)
