import os
from base64 import b64decode

import falcon
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from pymongo import MongoClient

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from ebl.cors_component import CORSComponent

from ebl.dictionary.dictionary import MongoDictionary
from ebl.dictionary.words import WordsResource
from ebl.dictionary.word_search import WordSearch


def auth0_user_loader(token):
    return token


def create_app(dictionary, auth_backend):
    auth_middleware = FalconAuthMiddleware(auth_backend)

    api = falcon.API(middleware=[CORSComponent(), auth_middleware])

    words = WordsResource(dictionary)
    word_search = WordSearch(dictionary)

    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)

    return api


def get_app():
    certificate = b64decode(os.environ['AUTH0_PEM'])
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    public_key = cert_obj.public_key()

    auth0_backend = JWTAuthBackend(auth0_user_loader,
                                   public_key,
                                   algorithm='RS256',
                                   auth_header_prefix='Bearer',
                                   audience=os.environ['AUTH0_AUDIENCE'],
                                   issuer=os.environ['AUTH0_ISSUER'],
                                   verify_claims=['signature', 'exp', 'iat'],
                                   required_claims=['exp', 'iat'])

    client = MongoClient(os.environ['MONGODB_URI'])
    dictionary = MongoDictionary(client[os.environ['MONGODB_DATABASE']])

    return create_app(dictionary, auth0_backend)
