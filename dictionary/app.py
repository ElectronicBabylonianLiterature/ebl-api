import falcon
import json

from .dictionary import Dictionary 
from .words import WordsResource 

def create_app(dictionaryPath):
    with open(dictionaryPath, encoding='utf8') as dictionaryJson:
        dictionary = Dictionary(json.load(dictionaryJson))

    words = WordsResource(dictionary)

    api = falcon.API()
    api.add_route('/words/{lemma}/{homonym}', words)

    return api
