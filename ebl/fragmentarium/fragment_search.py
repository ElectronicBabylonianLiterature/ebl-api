import falcon
import pydash

from ebl.dispatcher import create_dispatcher
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.dtos import create_response_dto
from ebl.require_scope import require_scope


class FragmentSearch:
    def __init__(self, fragmentarium):
        self._dispatch = create_dispatcher({
            'number': fragmentarium.search,
            'random': lambda _: fragmentarium.find_random(),
            'interesting': lambda _: fragmentarium.find_interesting(),
            'latest': lambda _: fragmentarium.find_latest(),
            'transliteration': pydash.flow(
                Transliteration,
                fragmentarium.search_signs
            )
        })

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        user = req.context['user']
        fragments = self._dispatch(req.params)
        resp.media = [
            create_response_dto(fragment, user)
            for fragment in fragments
        ]
