import os
from base64 import b64decode

import falcon
import sentry_sdk
from Cryptodome.PublicKey import RSA
from falcon_auth import FalconAuthMiddleware, MultiAuthBackend, NoneAuthBackend
from pymongo import MongoClient
from sentry_sdk import configure_scope
from sentry_sdk.integrations.falcon import FalconIntegration
import althaia
import ebl.error_handler
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.bibliography.web.bootstrap import create_bibliography_routes
from ebl.cache.application.cache import create_cache
from ebl.cache.application.custom_cache import ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.cdli.web.bootstrap import create_cdli_routes
from ebl.changelog import Changelog
from ebl.context import Context
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.bootstrap import create_corpus_routes
from ebl.dictionary.infrastructure.word_repository import MongoWordRepository
from ebl.dictionary.web.bootstrap import create_dictionary_routes
from ebl.ebl_ai_client import EblAiClient
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.files.web.bootstrap import create_files_route
from ebl.markup.web.bootstrap import create_markup_routes
from ebl.fragmentarium.infrastructure.cropped_sign_images_repository import (
    MongoCroppedSignImagesRepository,
)
from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
    MongoAnnotationsRepository,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.fragmentarium.web.bootstrap import create_fragmentarium_routes
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)
from ebl.lemmatization.web.bootstrap import create_lemmatization_routes
from ebl.signs.infrastructure.mongo_sign_repository import MongoSignRepository
from ebl.signs.web.bootstrap import create_signs_routes
from ebl.afo_register.web.bootstrap import create_afo_register_routes
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.infrastructure.mongo_parallel_repository import (
    MongoParallelRepository,
)
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MongoAfoRegisterRepository,
)
from ebl.users.domain.user import Guest
from ebl.users.infrastructure.auth0 import Auth0Backend
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)

althaia.patch()


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate).decode()
    return RSA.import_key(certificate).exportKey("PEM")


def set_sentry_user(id_: str) -> None:
    with configure_scope() as scope:
        scope.user = {"id": id_}


def create_context():
    ebl_ai_client = EblAiClient(os.environ["EBL_AI_API"])
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    auth_backend = Auth0Backend(
        decode_certificate(os.environ["AUTH0_PEM"]),
        os.environ["AUTH0_AUDIENCE"],
        os.environ["AUTH0_ISSUER"],
        set_sentry_user,
    )
    guest_backend = NoneAuthBackend(Guest)
    cache = create_cache()
    custom_cache = ChapterCache(MongoCacheRepository(database))
    return Context(
        ebl_ai_client=ebl_ai_client,
        auth_backend=MultiAuthBackend(auth_backend, guest_backend),
        cropped_sign_images_repository=MongoCroppedSignImagesRepository(database),
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
        afo_register_repository=MongoAfoRegisterRepository(database),
        findspot_repository=MongoFindspotRepository(database),
        custom_cache=custom_cache,
        cache=cache,
        parallel_line_injector=ParallelLineInjector(MongoParallelRepository(database)),
    )


def create_api(context: Context) -> falcon.App:
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.App(
        cors_enable=True, middleware=[auth_middleware, context.cache.middleware]
    )
    ebl.error_handler.set_up(api)
    return api


def create_app(context: Context, issuer: str = "", audience: str = ""):
    api = create_api(context)

    create_signs_routes(api, context)
    create_bibliography_routes(api, context)
    create_cdli_routes(api)
    create_corpus_routes(api, context)
    create_dictionary_routes(api, context)
    create_files_route(api, context)
    create_fragmentarium_routes(api, context)
    create_lemmatization_routes(api, context)
    create_markup_routes(api, context)
    create_afo_register_routes(api, context)

    return api


def get_app():
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], integrations=[FalconIntegration()])
    context = create_context()
    return create_app(context, os.environ["AUTH0_ISSUER"], os.environ["AUTH0_AUDIENCE"])
