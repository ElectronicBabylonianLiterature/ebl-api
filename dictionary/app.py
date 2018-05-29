import falcon

from .words import WordsResource 

words = WordsResource([
    {
        'lemma': ['part1', 'part2'],
        'homonym': 'I'
    }
])

api = application = falcon.API()
api.add_route('/words/{lemma}/{homonym}', words)
