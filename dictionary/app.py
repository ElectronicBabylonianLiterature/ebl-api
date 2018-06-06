import os

import falcon
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from pymongo import MongoClient

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from .cors_component import CORSComponent
from .dictionary import MongoDictionary
from .words import WordsResource


def auth0_user_loader(token):
    return token

def create_app(dictionary, auth_backend):
    auth_middleware = FalconAuthMiddleware(auth_backend)

    api = falcon.API(middleware=[CORSComponent(), auth_middleware])

    words = WordsResource(dictionary)
    api.add_route('/words/{lemma}/{homonym}', words)

    return api

def get_app(certificate_path):
    with open(certificate_path, 'rb') as cert:
        cert_obj = load_pem_x509_certificate(cert.read(), default_backend())
        public_key = cert_obj.public_key()

    auth0_backend = JWTAuthBackend(auth0_user_loader,
                                   public_key,
                                   algorithm='RS256',
                                   auth_header_prefix='Bearer',
                                   audience=os.environ['AUTH0_AUDIENCE'],
                                   issuer=os.environ['AUTH0_ISSUER'],
                                   verify_claims=['signature', 'exp', 'iat'],
                                   required_claims=['exp', 'iat'])

    dictionary = MongoDictionary(MongoClient(os.environ['MONGODB_HOST'], 27017))

    return create_app(dictionary, auth0_backend)
