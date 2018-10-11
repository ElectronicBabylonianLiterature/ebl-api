import falcon

from ebl.require_scope import require_scope
from ebl.fragmentarium.transliterations import Transliteration


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        param_names = list(req.params)
        if len(param_names) == 1:
            self._select_method(param_names)(req, resp)
        else:
            self._unprocessable_entity(req, resp)

    def _select_method(self, param_names):
        methods = {
            'number': self._search,
            'random': self._find_random,
            'interesting': self._find_interesting,
            'transliteration': self._search_transliteration
        }
        return methods.get(param_names[0], self._unprocessable_entity)

    def _search(self, req, resp):
        resp.media = self._map_fragments(
            self._fragmentarium.search(req.params['number']),
            req.context['user']
        )

    def _find_random(self, req, resp):
        resp.media = self._map_fragments(
            self._fragmentarium.find_random(),
            req.context['user']
        )

    def _find_interesting(self, req, resp):
        resp.media = self._map_fragments(
            self._fragmentarium.find_interesting(),
            req.context['user']
        )

    def _search_transliteration(self, req, resp):
        transliteration =\
            Transliteration.without_notes(req.params['transliteration'])
        resp.media = [
            {
                **(fragment_and_lines[0].to_dict_for(req.context['user'])),
                'matching_lines': fragment_and_lines[1]
            }
            for fragment_and_lines
            in self._fragmentarium.search_signs(transliteration)
        ]

    @staticmethod
    def _unprocessable_entity(_, resp):
        resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY

    @staticmethod
    def _map_fragments(fragments, user):
        return [fragment.to_dict_for(user) for fragment in fragments]
