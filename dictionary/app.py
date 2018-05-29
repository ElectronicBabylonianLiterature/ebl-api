import falcon

class DictionaryReource:
    def on_get(self, req, resp):
        entry = {
            'lemma': ['abā\'u']
        }

        resp.media = entry

api = application = falcon.API()
api.add_route('/', DictionaryReource())
