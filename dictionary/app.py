import falcon

from .words import WordsResource 

api = application = falcon.API()
api.add_route('/words/{lemma}/{homonym}', WordsResource())
