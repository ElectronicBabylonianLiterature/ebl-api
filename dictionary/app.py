import falcon

class DictionaryReource:
    def on_get(self, req, resp, lemma, homonym):
        entry = {
            'lemma': lemma.split(' '),
            'homonym': homonym
        }

        resp.media = entry

api = application = falcon.API()
api.add_route('/{lemma}/{homonym}', DictionaryReource())
