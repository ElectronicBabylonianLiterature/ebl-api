import falcon
import pydash

from ebl.dispatcher import create_dispatcher
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliteration import Transliteration


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._dispatch = create_dispatcher({
            'number': fragmentarium.search,
            'random': lambda _: fragmentarium.find_random(),
            'interesting': lambda _: fragmentarium.find_interesting(),
            'transliteration': pydash.flow(
                Transliteration,
                fragmentarium.search_signs
            )
        })

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        user = req.context['user']
        fragments = self._dispatch(req)
        resp.media = [fragment.to_dict_for(user) for fragment in fragments]
