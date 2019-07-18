import os
from base64 import b64decode

import falcon
import sentry_sdk
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from falcon_auth import FalconAuthMiddleware
from pymongo import MongoClient

import ebl.error_handler
from ebl.auth0 import Auth0Backend
from ebl.bibliography.bibliography import MongoBibliography
from ebl.bibliography.bibliography_entries import (BibliographyEntriesResource,
                                                   BibliographyResource)
from ebl.changelog import Changelog
from ebl.corpus.corpus import Corpus
from ebl.corpus.lines import LinesResource
from ebl.corpus.manuscripts import ManuscriptsResource
from ebl.corpus.mongo_text_repository import MongoTextRepository
from ebl.corpus.texts import TextResource, TextsResource
from ebl.corpus.alignments import AlignmentResource
from ebl.cors_component import CorsComponent
from ebl.dictionary.dictionary import MongoDictionary
from ebl.dictionary.word_search import WordSearch
from ebl.dictionary.words import WordsResource
from ebl.files.file_repository import GridFsFiles
from ebl.files.files import create_files_resource
from ebl.fragment.fragment_factory import FragmentFactory
from ebl.fragmentarium.folio_pager import FolioPagerResource
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.fragment_search import FragmentSearch
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.fragmentarium.fragments import FragmentsResource
from ebl.fragmentarium.lemma_search import LemmaSearch
from ebl.fragmentarium.lemmatizations import LemmatizationResource
from ebl.fragmentarium.references import ReferencesResource
from ebl.fragmentarium.statistics import StatisticsResource
from ebl.fragmentarium.transliterations import TransliterationResource
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MongoSignRepository


def create_bibliography_routes(api, context):
    bibliography_resource = BibliographyResource(context['bibliography'])
    bibliography_entries = BibliographyEntriesResource(context['bibliography'])
    api.add_route('/bibliography', bibliography_resource)
    api.add_route('/bibliography/{id_}', bibliography_entries)


def create_dictionary_routes(api, context):
    words = WordsResource(context['dictionary'])
    word_search = WordSearch(context['dictionary'])
    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)


def create_fragmentarium_routes(api, context, sign_list):
    fragmentarium = Fragmentarium(context['fragment_repository'],
                                  context['changelog'],
                                  sign_list,
                                  context['dictionary'],
                                  context['bibliography'])

    fragments = FragmentsResource(fragmentarium)
    fragment_search = FragmentSearch(fragmentarium)
    lemmatization = LemmatizationResource(fragmentarium)
    references = ReferencesResource(fragmentarium)
    statistics = StatisticsResource(fragmentarium)
    transliteration = TransliterationResource(fragmentarium)
    folio_pager = FolioPagerResource(fragmentarium)
    lemma_search = LemmaSearch(fragmentarium)

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


def create_corpus_routes(api, context, sign_list):
    corpus = Corpus(
        context['text_repository'],
        context['bibliography'],
        context['changelog'],
        sign_list
    )
    context['text_repository'].create_indexes()

    api.add_route('/texts', TextsResource(corpus))
    api.add_route('/texts/{category}/{index}', TextResource(corpus))
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/alignment',
        AlignmentResource(corpus)
    )
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/manuscripts',
        ManuscriptsResource(corpus)
    )
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/lines',
        LinesResource(corpus)
    )


def create_app(context):
    auth_middleware = FalconAuthMiddleware(context['auth_backend'])
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)

    sign_list = SignList(context['sign_repository'])
    create_bibliography_routes(api, context)
    create_dictionary_routes(api, context)
    create_fragmentarium_routes(api, context, sign_list)
    create_corpus_routes(api, context, sign_list)

    files = create_files_resource(context['auth_backend'])(context['files'])
    api.add_route('/images/{file_name}', files)

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
    context = {
        'auth_backend': auth_backend,
        'dictionary': MongoDictionary(database),
        'sign_repository': MongoSignRepository(database),
        'files': GridFsFiles(database),
        'fragment_repository': MongoFragmentRepository(
            database,
            FragmentFactory(bibliography)
        ),
        'changelog': Changelog(database),
        'bibliography': bibliography,
        'text_repository': MongoTextRepository(database)
    }

    app = create_app(context)

    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'])
    return SentryWsgiMiddleware(app)


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()
