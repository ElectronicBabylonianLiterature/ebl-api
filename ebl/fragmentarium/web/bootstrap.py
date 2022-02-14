import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary import Dictionary
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.web.annotations import AnnotationResource
from ebl.fragmentarium.web.folio_pager import FolioPagerResource
from ebl.fragmentarium.web.folios import FoliosResource
from ebl.fragmentarium.web.fragment_genre import FragmentGenreResource
from ebl.fragmentarium.web.fragment_matcher import FragmentMatcherResource
from ebl.fragmentarium.web.fragment_pager import FragmentPagerResource
from ebl.fragmentarium.web.fragment_search import FragmentSearch
from ebl.fragmentarium.web.fragments import FragmentsResource
from ebl.fragmentarium.web.genres import GenresResource
from ebl.fragmentarium.web.lemmatizations import LemmatizationResource
from ebl.fragmentarium.web.photo import PhotoResource
from ebl.fragmentarium.web.references import ReferencesResource
from ebl.fragmentarium.web.statistics import StatisticsResource
from ebl.fragmentarium.web.transliterations import TransliterationResource


def create_fragmentarium_routes(api: falcon.App, context: Context):
    context.fragment_repository.create_indexes()
    fragmentarium = Fragmentarium(context.fragment_repository)
    finder = FragmentFinder(
        context.get_bibliography(),
        context.fragment_repository,
        Dictionary(context.word_repository, context.changelog),
        context.photo_repository,
        context.folio_repository,
    )
    updater = context.get_fragment_updater()
    annotations_service = AnnotationsService(
        context.ebl_ai_client,
        context.annotations_repository,
        context.photo_repository,
        context.changelog,
    )

    statistics = StatisticsResource(fragmentarium)
    fragments = FragmentsResource(finder)
    fragment_genre = FragmentGenreResource(updater)

    fragment_matcher = FragmentMatcherResource(
        FragmentMatcher(context.fragment_repository)
    )
    fragment_search = FragmentSearch(
        fragmentarium, finder, context.get_transliteration_query_factory()
    )
    genres = GenresResource()
    lemmatization = LemmatizationResource(updater)
    references = ReferencesResource(updater)
    transliteration = TransliterationResource(
        updater, context.get_transliteration_update_factory()
    )
    annotations = AnnotationResource(annotations_service)
    fragment_pager = FragmentPagerResource(finder)
    folio_pager = FolioPagerResource(finder)
    photo = PhotoResource(finder)
    folios = FoliosResource(finder)

    api.add_route("/fragments", fragment_search)
    api.add_route("/fragments/{number}/match", fragment_matcher)
    api.add_route("/fragments/{number}/genres", fragment_genre)
    api.add_route("/fragments/{number}", fragments)
    api.add_route("/fragments/{number}/pager", fragment_pager)
    api.add_route("/fragments/{number}/lemmatization", lemmatization)
    api.add_route("/fragments/{number}/references", references)
    api.add_route("/fragments/{number}/transliteration", transliteration)
    api.add_route("/fragments/{number}/annotations", annotations)
    api.add_route("/fragments/{number}/photo", photo)
    api.add_route("/genres", genres)
    api.add_route("/statistics", statistics)
    api.add_route("/fragments/{number}/pager/{folio_name}/{folio_number}", folio_pager)
    api.add_route("/folios/{name}/{number}", folios)
