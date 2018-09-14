import falcon

from ebl.require_scope import require_scope
from ebl.fragmentarium.transliterations import clean


def _unprocessable_entity(_, resp):
    resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium, sign_list):
        self._fragmentarium = fragmentarium
        self._sign_list = sign_list

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        param_names = list(req.params)
        if len(param_names) == 1:
            self._select_method(param_names)(req, resp)
        else:
            _unprocessable_entity(req, resp)

    def _select_method(self, param_names):
        methods = {
            'number': self._search,
            'random': self._find_random,
            'interesting': self._find_interesting,
            'transliteration': self._search_transliteration
        }
        return methods.get(param_names[0], _unprocessable_entity)

    def _search(self, req, resp):
        resp.media = self._fragmentarium.search(req.params['number'])

    def _find_random(self, _, resp):
        resp.media = self._fragmentarium.find_random()

    def _find_interesting(self, _, resp):
        resp.media = self._fragmentarium.find_interesting()

    def _search_transliteration(self, req, resp):
        transliteration = req.params['transliteration']
        cleaned_transliteration = clean(transliteration)
        signs = self._sign_list.map_transliteration(cleaned_transliteration)
        resp.media = self._fragmentarium.search_signs(signs)
