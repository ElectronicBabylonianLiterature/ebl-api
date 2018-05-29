import falcon

from .dictionary import Dictionary 
from .words import WordsResource 

dictionary = Dictionary([
    {
        'lemma': ['part1', 'part2'],
        'homonym': 'I'
    }
])
words = WordsResource(dictionary)

api = application = falcon.API()
api.add_route('/words/{lemma}/{homonym}', words)
