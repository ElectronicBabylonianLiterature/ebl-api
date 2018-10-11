import falcon

from ebl.require_scope import require_scope
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.transliterations import Transliteration


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium
        self._commands = {
            'number': self._search,
            'random': self._find_random,
            'interesting': self._find_interesting,
            'transliteration': self._search_transliteration
        }

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        param_names = list(req.params)
        user = req.context['user']
        if len(param_names) == 1:
            param = param_names[0]
            value = req.params[param]
            fragments = self._get_command(param)(value)
            resp.media = [fragment.to_dict_for(user) for fragment in fragments]
        else:
            raise falcon.HTTPUnprocessableEntity()

    def _get_command(self, param):
        if param in self._commands:
            return self._commands[param]
        else:
            raise falcon.HTTPUnprocessableEntity()

    def _search(self, number):
        return self._fragmentarium.search(number)

    def _find_random(self, _):
        return self._fragmentarium.find_random()

    def _find_interesting(self, _):
        return self._fragmentarium.find_interesting()

    def _search_transliteration(self, query):
        transliteration =\
            Transliteration.without_notes(query)
        return [
            Fragment({
                **fragment_and_lines[0].to_dict(),
                'matching_lines': fragment_and_lines[1]
            })
            for fragment_and_lines
            in self._fragmentarium.search_signs(transliteration)
        ]
