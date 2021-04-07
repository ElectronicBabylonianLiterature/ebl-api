import os
from base64 import b64decode

import falcon
import sentry_sdk
from falcon_auth import FalconAuthMiddleware
from pymongo import MongoClient
from sentry_sdk import configure_scope
from sentry_sdk.integrations.falcon import FalconIntegration
from Cryptodome.PublicKey import RSA

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
from ebl.lemmatization.web.bootstrap import create_lemmatization_routes
from ebl.openapi.web.bootstrap import create_open_api_route
from ebl.openapi.web.spec import create_spec
from ebl.signs.web.bootstrap import create_signs_routes
from ebl.transliteration.infrastructure.mongo_sign_repository import MongoSignRepository
from ebl.users.infrastructure.auth0 import Auth0Backend
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate).decode()
    return RSA.import_key(certificate).exportKey("PEM")


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
    return Context(
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
        lemma_repository=MongoLemmaRepository(database),
    )


def create_api(context: Context) -> falcon.API:
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)
    return api


def create_app(context: Context, issuer: str = "", audience: str = ""):
    api = create_api(context)
    spec = create_spec(api, issuer, audience)

    create_signs_routes(api, context, spec)
    create_bibliography_routes(api, context, spec)
    create_cdli_routes(api, spec)
    create_corpus_routes(api, context, spec)
    create_dictionary_routes(api, context, spec)
    create_files_route(api, context, spec)
    create_fragmentarium_routes(api, context, spec)
    create_lemmatization_routes(api, context, spec)
    create_open_api_route(api, spec)

    return api


def get_app():
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], integrations=[FalconIntegration()])
    context = create_context()

    return create_app(context, os.environ["AUTH0_ISSUER"], os.environ["AUTH0_AUDIENCE"])
