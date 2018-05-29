import falcon

class WordsResource:
    def on_get(self, req, resp, lemma, homonym):
        entry = {
            'lemma': lemma.split(' '),
            'homonym': homonym
        }

        resp.media = entry

api = application = falcon.API()
api.add_route('/words/{lemma}/{homonym}', WordsResource())
