import json
import falcon
from falcon_auth import FalconAuthMiddleware, BasicAuthBackend

from .cors_component import CORSComponent
from .dictionary import Dictionary
from .words import WordsResource

def create_app(dictionary_path):
    with open(dictionary_path, encoding='utf8') as dictionary_json:
        dictionary = Dictionary(json.load(dictionary_json))

    user_loader = lambda username, password: { 'username': username }
    auth_backend = BasicAuthBackend(user_loader)
    auth_middleware = FalconAuthMiddleware(auth_backend)

    api = falcon.API(middleware=[CORSComponent(), auth_middleware])

    words = WordsResource(dictionary)
    api.add_route('/words/{lemma}/{homonym}', words)

    return api
