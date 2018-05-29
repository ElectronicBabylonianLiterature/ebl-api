import falcon

class DictionaryReource:
    def on_get(self, req, resp, lemma):
        entry = {
            'lemma': lemma.split(' ')
        }

        resp.media = entry

api = application = falcon.API()
api.add_route('/{lemma}', DictionaryReource())
