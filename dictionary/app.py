import json

import falcon
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from .cors_component import CORSComponent
from .dictionary import Dictionary
from .words import WordsResource


def auth0_user_loader(token):
    return token

def create_app(dictionary_path, auth_backend):
    with open(dictionary_path, encoding='utf8') as dictionary_json:
        dictionary = Dictionary(json.load(dictionary_json))

    auth_middleware = FalconAuthMiddleware(auth_backend)

    api = falcon.API(middleware=[CORSComponent(), auth_middleware])

    words = WordsResource(dictionary)
    api.add_route('/words/{lemma}/{homonym}', words)

    return api

def get_app(dictionary_path, auth0_path, certificate_path):
    with open(auth0_path, encoding='utf8') as auth0_json:
        auth0_config = json.load(auth0_json)

    with open(certificate_path, 'rb') as cert:
        cert_obj = load_pem_x509_certificate(cert.read(), default_backend())
        public_key = cert_obj.public_key()

    auth0_backend = JWTAuthBackend(auth0_user_loader,
                                   public_key,
                                   algorithm='RS256',
                                   auth_header_prefix='Bearer',
                                   audience=auth0_config['audience'],
                                   issuer=auth0_config['issuer'],
                                   verify_claims=['signature', 'exp', 'iat'],
                                   required_claims=['exp', 'iat'])

    return create_app(dictionary_path, auth0_backend)
