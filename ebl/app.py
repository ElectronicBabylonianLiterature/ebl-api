import os
from base64 import b64decode

import falcon
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from pymongo import MongoClient
import requests

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from ebl.cors_component import CORSComponent

from ebl.dictionary.dictionary import MongoDictionary
from ebl.dictionary.words import WordsResource
from ebl.dictionary.word_search import WordSearch
from ebl.fragmentarium.fragmentarium import MongoFragmentarium
from ebl.fragmentarium.fragments import FragmentsResource
from ebl.files import FilesResource


def auth0_user_loader(token):
    return token


def create_auth0_backend():
    certificate = b64decode(os.environ['AUTH0_PEM'])
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    public_key = cert_obj.public_key()

    return JWTAuthBackend(
        auth0_user_loader,
        public_key,
        algorithm='RS256',
        auth_header_prefix='Bearer',
        audience=os.environ['AUTH0_AUDIENCE'],
        issuer=os.environ['AUTH0_ISSUER'],
        verify_claims=['signature', 'exp', 'iat'],
        required_claims=['exp', 'iat', 'openid', 'read:words']
    )


def fetch_auth0_user_profile(req):
    issuer = os.environ['AUTH0_ISSUER']
    url = f'{issuer}userinfo'
    headers = {'Authorization': req.get_header('Authorization', True)}
    return requests.get(url, headers=headers).json()


def create_app(dictionary,
               fragmenatrium, files,
               auth_backend,
               fetch_user_profile):
    auth_middleware = FalconAuthMiddleware(auth_backend)

    api = falcon.API(middleware=[CORSComponent(), auth_middleware])

    words = WordsResource(dictionary)
    word_search = WordSearch(dictionary)
    fragments = FragmentsResource(fragmenatrium, fetch_user_profile)

    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)
    api.add_route('/fragments/{number}', fragments)
    api.add_route('/images/{file_name}', files)

    return api


def get_app():
    auth0_backend = create_auth0_backend()

    client = MongoClient(os.environ['MONGODB_URI'])
    database = client.get_database()
    dictionary = MongoDictionary(database)
    fragmenatrium = MongoFragmentarium(database)
    files = FilesResource(database)

    return create_app(
        dictionary,
        fragmenatrium,
        files,
        auth0_backend,
        fetch_auth0_user_profile
    )
