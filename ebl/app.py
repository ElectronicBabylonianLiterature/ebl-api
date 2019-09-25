import os
from base64 import b64decode

import attr
import falcon
import sentry_sdk
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from falcon_apispec import FalconPlugin
from falcon_auth import FalconAuthMiddleware
from falcon_auth.backends import AuthBackend
from pymongo import MongoClient
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

import ebl.error_handler
from ebl.auth0 import Auth0Backend
from ebl.bibliography.bibliography import MongoBibliography
from ebl.bibliography.web.bibliography_entries import (
    BibliographyEntriesResource,
    BibliographyResource)
from ebl.changelog import Changelog
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.alignments import AlignmentResource
from ebl.corpus.web.lines import LinesResource
from ebl.corpus.web.manuscripts import ManuscriptsResource
from ebl.corpus.web.texts import TextResource, TextsResource
from ebl.cors_component import CorsComponent
from ebl.dictionary.dictionary import MongoDictionary
from ebl.dictionary.web.word_search import WordSearch
from ebl.dictionary.web.words import WordsResource
from ebl.files.file_repository import GridFsFiles
from ebl.files.files import create_files_resource
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_query_factory \
    import TransliterationQueryFactory
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.infrastructure.fragment_info_schema import \
    FragmentInfoSchema
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.fragmentarium.web.folio_pager import FolioPagerResource
from ebl.fragmentarium.web.fragment_search import FragmentSearch
from ebl.fragmentarium.web.fragments import FragmentsResource
from ebl.fragmentarium.web.lemma_search import LemmaSearch
from ebl.fragmentarium.web.lemmatizations import LemmatizationResource
from ebl.fragmentarium.web.references import ReferencesResource
from ebl.fragmentarium.web.statistics import StatisticsResource
from ebl.fragmentarium.web.transliterations import TransliterationResource
from ebl.signs.application.atf_converter import AtfConverter
from ebl.signs.application.sign_repository import SignRepository
from ebl.signs.infrastructure.mongo_sign_repository import \
    MongoSignRepository

API_VERSION = '0.0.1'


@attr.s(auto_attribs=True, frozen=True)
class Context:
    auth_backend: AuthBackend
    dictionary: MongoDictionary
    sign_repository: SignRepository
    files: GridFsFiles
    fragment_repository: FragmentRepository
    changelog: Changelog
    bibliography: MongoBibliography
    text_repository: MongoTextRepository


def create_bibliography_routes(api, context: Context, spec):
    bibliography_resource = BibliographyResource(context.bibliography)
    bibliography_entries = BibliographyEntriesResource(context.bibliography)
    api.add_route('/bibliography', bibliography_resource)
    api.add_route('/bibliography/{id_}', bibliography_entries)
    spec.path(resource=bibliography_resource)
    spec.path(resource=bibliography_entries)


def create_dictionary_routes(api, context: Context, spec):
    words = WordsResource(context.dictionary)
    word_search = WordSearch(context.dictionary)
    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)
    spec.path(resource=words)
    spec.path(resource=word_search)


def create_fragmentarium_routes(api,
                                context: Context,
                                transliteration_search,
                                spec):
    fragmentarium = Fragmentarium(context.fragment_repository)
    finder = FragmentFinder(context.fragment_repository,
                            context.dictionary)
    updater = FragmentUpdater(context.fragment_repository,
                              context.changelog,
                              context.bibliography)

    statistics = StatisticsResource(fragmentarium)
    fragments = FragmentsResource(finder)
    fragment_search = \
        FragmentSearch(fragmentarium,
                       finder,
                       TransliterationQueryFactory(transliteration_search))
    lemmatization = LemmatizationResource(updater)
    references = ReferencesResource(updater)
    transliteration = TransliterationResource(
        updater,
        TransliterationUpdateFactory(transliteration_search)
    )
    folio_pager = FolioPagerResource(finder)
    lemma_search = LemmaSearch(finder)

    api.add_route('/fragments', fragment_search)
    api.add_route('/fragments/{number}', fragments)
    api.add_route('/fragments/{number}/lemmatization', lemmatization)
    api.add_route('/fragments/{number}/references', references)
    api.add_route('/fragments/{number}/transliteration', transliteration)
    api.add_route('/lemmas', lemma_search)
    api.add_route('/statistics', statistics)
    api.add_route(
        '/pager/folios/{folio_name}/{folio_number}/{number}',
        folio_pager
    )

    spec.components.schema('FragmentInfo',
                           schema=FragmentInfoSchema)
    spec.path(resource=fragment_search)
    spec.path(resource=fragments)
    spec.path(resource=lemmatization)
    spec.path(resource=references)
    spec.path(resource=transliteration)
    spec.path(resource=lemma_search)
    spec.path(resource=statistics)
    spec.path(resource=folio_pager)


def create_corpus_routes(api,
                         context: Context,
                         transliteration_search,
                         spec):
    corpus = Corpus(
        context.text_repository,
        context.bibliography,
        context.changelog,
        TransliterationUpdateFactory(transliteration_search)
    )
    context.text_repository.create_indexes()

    texts = TextsResource(corpus)
    text = TextResource(corpus)
    alignment = AlignmentResource(corpus)
    manuscript = ManuscriptsResource(corpus)
    lines = LinesResource(corpus)

    api.add_route('/texts', texts)
    api.add_route('/texts/{category}/{index}', text)
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/alignment',
        alignment
    )
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/manuscripts',
        manuscript
    )

    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/lines',
        lines)

    spec.path(resource=texts)
    spec.path(resource=text)
    spec.path(resource=alignment)
    spec.path(resource=manuscript)
    spec.path(resource=lines)


def create_app(context: Context):
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)

    spec = APISpec(
        title="Electronic Babylonian Literature",
        version=API_VERSION,
        openapi_version='3.0.0',
        plugins=[FalconPlugin(api), MarshmallowPlugin()],
    )
    authorization_url = (
        f'{os.environ.get("AUTH0_ISSUER")}authorize'
        f'?audience={os.environ.get("AUTH0_AUDIENCE")}'
    )
    auth0_scheme = {
        'type': "oauth2",
        'flows': {
            'implicit': {
                'authorizationUrl': authorization_url,
                'scopes': {
                    'openid': '',
                    'profile': '',
                    'read:words': '',
                    'write:words': '',
                    'read:fragments': '',
                    'transliterate:fragments': '',
                    'read:MJG-folios': '',
                    'read:WGL-folios': '',
                    'read:FWG-folios': '',
                    'read:EL-folios': '',
                    'read:AKG-folios': '',
                    'lemmatize:fragments': '',
                    'access:beta': '',
                    'read:bibliography': '',
                    'write:bibliography': '',
                    'read:WRM-folios': '',
                    'read:texts': '',
                    'write:texts': '',
                    'create:texts': '',
                    'read:CB-folios': '',
                    'read:JS-folios': '',
                }
            }
        }
    }

    spec.components.security_scheme("auth0", auth0_scheme)

    transliteration_search = AtfConverter(context.sign_repository)
    create_bibliography_routes(api, context, spec)
    create_dictionary_routes(api, context, spec)
    create_fragmentarium_routes(api, context, transliteration_search, spec)
    create_corpus_routes(api, context, transliteration_search, spec)

    files = create_files_resource(context.auth_backend)(context.files)
    api.add_route('/images/{file_name}', files)
    spec.path(resource=files)

    class OpenApiResource:
        auth = {'auth_disabled': True}

        def on_get(self, _req, resp):
            resp.content_type = falcon.MEDIA_YAML
            resp.body = spec.to_yaml()

    open_api = OpenApiResource()
    api.add_route(
        '/ebl.yml',
        open_api
    )
    spec.path(resource=open_api)

    return api


def get_app():
    client = MongoClient(os.environ['MONGODB_URI'])
    database = client.get_database()
    auth_backend = Auth0Backend(
        decode_certificate(os.environ['AUTH0_PEM']),
        os.environ['AUTH0_AUDIENCE'],
        os.environ['AUTH0_ISSUER']
    )

    bibliography = MongoBibliography(database)
    context = Context(
        auth_backend=auth_backend,
        dictionary=MongoDictionary(database),
        sign_repository=MongoSignRepository(database),
        files=GridFsFiles(database),
        fragment_repository=MongoFragmentRepository(database),
        changelog=Changelog(database),
        bibliography=bibliography,
        text_repository=MongoTextRepository(database)
    )

    app = create_app(context)

    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'])
    return SentryWsgiMiddleware(app)


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()
