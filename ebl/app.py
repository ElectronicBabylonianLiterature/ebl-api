import os
from base64 import b64decode

import falcon  # pyre-ignore[21]
import sentry_sdk  # pyre-ignore[21]
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from falcon_auth import FalconAuthMiddleware  # pyre-ignore[21]
from pymongo import MongoClient  # pyre-ignore[21]
from sentry_sdk import configure_scope
from sentry_sdk.integrations.falcon import FalconIntegration  # pyre-ignore[21]

import ebl.error_handler
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.bibliography.web.bootstrap import create_bibliography_routes
from ebl.cdli.web.bootstrap import create_cdli_routes
from ebl.changelog import Changelog
from ebl.context import Context
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.bootstrap import create_corpus_routes
from ebl.cors_component import CorsComponent
from ebl.dictionary.infrastructure.dictionary import MongoWordRepository
from ebl.dictionary.web.bootstrap import create_dictionary_routes
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.files.web.bootstrap import create_files_route
from ebl.fragmentarium.infrastructure.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
    MongoAnnotationsRepository,
)
from ebl.fragmentarium.web.bootstrap import create_fragmentarium_routes
from ebl.openapi.web.bootstrap import create_open_api_route
from ebl.openapi.web.spec import create_spec
from ebl.transliteration.infrastructure.mongo_sign_repository import MongoSignRepository
from ebl.users.infrastructure.auth0 import Auth0Backend


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()


def set_sentry_user(id_: str) -> None:
    with configure_scope() as scope:
        scope.user = {"id": id_}


def create_context():
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    auth_backend = Auth0Backend(
        decode_certificate(os.environ["AUTH0_PEM"]),
        os.environ["AUTH0_AUDIENCE"],
        os.environ["AUTH0_ISSUER"],
        set_sentry_user,
    )
    context = Context(
        auth_backend=auth_backend,
        word_repository=MongoWordRepository(database),
        sign_repository=MongoSignRepository(database),
        public_file_repository=GridFsFileRepository(database, "fs"),
        photo_repository=GridFsFileRepository(database, "photos"),
        folio_repository=GridFsFileRepository(database, "folios"),
        fragment_repository=MongoFragmentRepository(database),
        changelog=Changelog(database),
        bibliography_repository=MongoBibliographyRepository(database),
        text_repository=MongoTextRepository(database),
        annotations_repository=MongoAnnotationsRepository(database),
    )
    return context


def create_api(context: Context) -> falcon.API:  # pyre-ignore[11]
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)
    return api


def create_app(context: Context, issuer: str = "", audience: str = ""):
    api = create_api(context)
    spec = create_spec(api, issuer, audience)

    create_bibliography_routes(api, context, spec)
    create_cdli_routes(api, spec)
    create_corpus_routes(api, context, spec)
    create_dictionary_routes(api, context, spec)
    create_files_route(api, context, spec)
    create_fragmentarium_routes(api, context, spec)
    create_open_api_route(api, spec)

    return api


def get_app():
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], integrations=[FalconIntegration()])
    context = create_context()

    return create_app(context, os.environ["AUTH0_ISSUER"], os.environ["AUTH0_AUDIENCE"])
