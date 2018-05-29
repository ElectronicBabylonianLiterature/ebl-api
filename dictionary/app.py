import falcon

from .dictionary import Dictionary 
from .words import WordsResource 

def create_app(words):
    dictionary = Dictionary(words)
    words = WordsResource(dictionary)

    api = falcon.API()
    api.add_route('/words/{lemma}/{homonym}', words)

    return api

def get_app():
    return create_app([
        {
            'lemma': ['part1', 'part2'],
            'homonym': 'I'
        }
    ])
