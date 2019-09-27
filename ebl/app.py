import os
from base64 import b64decode

import falcon
import sentry_sdk
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from falcon_auth import FalconAuthMiddleware
from pymongo import MongoClient
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

import ebl.error_handler
from ebl.auth0 import Auth0Backend
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.bibliography.web.bootstrap import create_bibliography_routes
from ebl.changelog import Changelog
from ebl.context import Context
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.bootstrap import create_corpus_routes
from ebl.cors_component import CorsComponent
from ebl.dictionary.infrastructure.dictionary import MongoWordRepository
from ebl.dictionary.web.bootstrap import create_dictionary_routes
from ebl.files.infrastructure.file_repository import GridFsFiles
from ebl.files.web.bootstrap import create_files_route
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.fragmentarium.web.bootstrap import create_fragmentarium_routes
from ebl.openapi.web.bootstrap import create_open_api_route
from ebl.openapi.web.spec import create_spec
from ebl.signs.infrastructure.mongo_sign_repository import \
    MongoSignRepository


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()


def create_context():
    client = MongoClient(os.environ['MONGODB_URI'])
    database = client.get_database()
    auth_backend = Auth0Backend(
        decode_certificate(os.environ['AUTH0_PEM']),
        os.environ['AUTH0_AUDIENCE'],
        os.environ['AUTH0_ISSUER']
    )
    context = Context(
        auth_backend=auth_backend,
        word_repository=MongoWordRepository(database),
        sign_repository=MongoSignRepository(database),
        files=GridFsFiles(database),
        fragment_repository=MongoFragmentRepository(database),
        changelog=Changelog(database),
        bibliography_repository=MongoBibliographyRepository(database),
        text_repository=MongoTextRepository(database)
    )
    return context


def create_api(context: Context) -> falcon.API:
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)
    return api


def create_app(context: Context, issuer: str = '', audience: str = ''):
    api = create_api(context)
    spec = create_spec(api, issuer, audience)

    create_bibliography_routes(api, context, spec)
    create_dictionary_routes(api, context, spec)
    create_fragmentarium_routes(api, context, spec)
    create_corpus_routes(api, context, spec)
    create_files_route(api, context, spec)
    create_open_api_route(api, spec)

    return api


def get_app():
    context = create_context()

    app = create_app(context,
                     os.environ['AUTH0_ISSUER'],
                     os.environ['AUTH0_AUDIENCE'])

    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'])
    return SentryWsgiMiddleware(app)
