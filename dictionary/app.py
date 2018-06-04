import json
import falcon

from .cors_component import CORSComponent
from .dictionary import Dictionary
from .words import WordsResource

def create_app(dictionary_path):
    with open(dictionary_path, encoding='utf8') as dictionary_json:
        dictionary = Dictionary(json.load(dictionary_json))

    api = falcon.API(middleware=CORSComponent())

    words = WordsResource(dictionary)
    api.add_route('/words/{lemma}/{homonym}', words)

    return api
