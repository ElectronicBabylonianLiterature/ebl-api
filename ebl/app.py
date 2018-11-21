from base64 import b64decode
import os

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

import falcon
from falcon_auth import FalconAuthMiddleware

from pymongo import MongoClient

from ebl.auth0 import Auth0Backend
from ebl.changelog import Changelog
from ebl.cors_component import CORSComponent
import ebl.error_handler

from ebl.dictionary.dictionary import MongoDictionary
from ebl.dictionary.word_search import WordSearch
from ebl.dictionary.words import WordsResource

from ebl.fragmentarium.folio_pager import FolioPagerResource
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.fragment_search import FragmentSearch
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.fragmentarium.fragments import FragmentsResource
from ebl.fragmentarium.lemmatizations import LemmatizationResource
from ebl.fragmentarium.statistics import StatisticsResource

from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MongoSignRepository

from ebl.files.file_repository import GridFsFiles
from ebl.files.files import FilesResource


def create_app(context):
    auth_middleware = FalconAuthMiddleware(context['auth_backend'])
    api = falcon.API(middleware=[CORSComponent(), auth_middleware])
    ebl.error_handler.set_up(api)

    sign_list = SignList(context['sign_repository'])

    fragmentarium = Fragmentarium(context['fragment_repository'],
                                  context['changelog'],
                                  sign_list)

    words = WordsResource(context['dictionary'])
    word_search = WordSearch(context['dictionary'])
    fragments = FragmentsResource(fragmentarium)
    fragment_search = FragmentSearch(fragmentarium)
    lemmatization = LemmatizationResource(fragmentarium)
    statistics = StatisticsResource(fragmentarium)
    files = FilesResource(context['files'])
    folio_pager = FolioPagerResource(fragmentarium)

    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)
    api.add_route('/fragments', fragment_search)
    api.add_route('/fragments/{number}', fragments)
    api.add_route('/fragments/{number}/lemmatization', lemmatization)
    api.add_route('/images/{file_name}', files)
    api.add_route('/statistics', statistics)
    api.add_route(
        '/pager/folios/{folio_name}/{folio_number}/{number}',
        folio_pager
    )

    return api


def get_app():
    client = MongoClient(os.environ['MONGODB_URI'])
    database = client.get_database()
    auth_backend = Auth0Backend(
        decode_certificate(os.environ['AUTH0_PEM']),
        os.environ['AUTH0_AUDIENCE'],
        os.environ['AUTH0_ISSUER']
    )

    context = {
        'auth_backend': auth_backend,
        'dictionary': MongoDictionary(database),
        'sign_repository': MongoSignRepository(database),
        'files': GridFsFiles(database),
        'fragment_repository': MongoFragmentRepository(database),
        'changelog': Changelog(database)
    }

    return create_app(context)


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()
