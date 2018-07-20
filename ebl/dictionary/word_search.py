import falcon
import pydash
from ebl.require_scope import require_scope


class WordSearch:
    # pylint: disable=R0903
    def __init__(self, dictionary):
        self._dictionary = dictionary

    @falcon.before(require_scope, 'read:words')
    def on_get(self, req, resp):
        if 'query' in req.params:
            words = self._dictionary.search(req.params['query'])
            resp.media = pydash.map_(
                words,
                lambda word: pydash.defaults({'_id': str(word['_id'])}, word)
            )
        else:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
