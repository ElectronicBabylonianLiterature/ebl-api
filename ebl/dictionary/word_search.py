import falcon
from ebl.require_scope import require_scope


class WordSearch:
    # pylint: disable=R0903
    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._commands = {
            'query': self._search,
            'lemma': self._search_lemma,
        }

    @falcon.before(require_scope, 'read:words')
    def on_get(self, req, resp):
        param_names = list(req.params)
        if len(param_names) == 1:
            param = param_names[0]
            value = req.params[param]
            resp.media = self._get_command(param)(value)
        else:
            raise falcon.HTTPUnprocessableEntity()

    def _get_command(self, param):
        if param in self._commands:
            return self._commands[param]
        else:
            raise falcon.HTTPUnprocessableEntity()

    def _search(self, query):
        return self._dictionary.search(query)

    def _search_lemma(self, lemma):
        return self._dictionary.search_lemma(lemma)
