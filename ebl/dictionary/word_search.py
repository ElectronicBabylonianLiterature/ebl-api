import falcon
import pydash


class WordSearch:
    # pylint: disable=R0903
    def __init__(self, dictionary):
        self._dictionary = dictionary

    def on_get(self, req, resp):
        if 'query' in req.params:
            words = self._dictionary.search(req.params['query'])
            resp.media = pydash.map_(
                words,
                lambda word: pydash.defaults({'_id': str(word['_id'])}, word)
            )
        else:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
