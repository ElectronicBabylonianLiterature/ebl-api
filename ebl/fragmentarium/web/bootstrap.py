import falcon

from ebl.context import Context
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_query_factory import \
    TransliterationQueryFactory
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.infrastructure.fragment_info_schema import \
    FragmentInfoSchema
from ebl.fragmentarium.web.folio_pager import FolioPagerResource
from ebl.fragmentarium.web.fragment_search import FragmentSearch
from ebl.fragmentarium.web.fragments import FragmentsResource
from ebl.fragmentarium.web.lemma_search import LemmaSearch
from ebl.fragmentarium.web.lemmatizations import LemmatizationResource
from ebl.fragmentarium.web.references import ReferencesResource
from ebl.fragmentarium.web.statistics import StatisticsResource
from ebl.fragmentarium.web.transliterations import TransliterationResource
from ebl.signs.application.atf_converter import AtfConverter


def create_fragmentarium_routes(api: falcon.API,
                                context: Context,
                                spec):
    fragmentarium = Fragmentarium(context.fragment_repository)
    finder = FragmentFinder(context.fragment_repository,
                            context.dictionary)
    updater = FragmentUpdater(context.fragment_repository,
                              context.changelog,
                              context.bibliography)

    statistics = StatisticsResource(fragmentarium)
    fragments = FragmentsResource(finder)
    atf_converter = AtfConverter(context.sign_repository)
    fragment_search = \
        FragmentSearch(fragmentarium,
                       finder,
                       TransliterationQueryFactory(atf_converter))
    lemmatization = LemmatizationResource(updater)
    references = ReferencesResource(updater)
    transliteration = TransliterationResource(
        updater,
        TransliterationUpdateFactory(atf_converter)
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
