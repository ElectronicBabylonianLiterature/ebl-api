import falcon  # pyre-ignore

from ebl.context import Context
from ebl.dictionary.application.dictionary import Dictionary
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.folio_pager_schema import FolioPagerInfoSchema
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragment_pager_schema import FragmentPagerInfoSchema
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.web.annotations import AnnotationResource
from ebl.fragmentarium.web.dtos import FragmentDtoSchema
from ebl.fragmentarium.web.folio_pager import FolioPagerResource
from ebl.fragmentarium.web.folios import FoliosResource
from ebl.fragmentarium.web.fragment_genre import FragmentGenreResource
from ebl.fragmentarium.web.fragment_pager import FragmentPagerResource
from ebl.fragmentarium.web.fragment_search import FragmentSearch
from ebl.fragmentarium.web.fragments import FragmentsResource
from ebl.fragmentarium.web.lemma_search import LemmaSearch
from ebl.fragmentarium.web.lemmatizations import LemmatizationResource
from ebl.fragmentarium.web.photo import PhotoResource
from ebl.fragmentarium.web.references import ReferencesResource
from ebl.fragmentarium.web.statistics import StatisticsResource
from ebl.fragmentarium.web.transliterations import TransliterationResource


def create_fragmentarium_routes(api: falcon.API, context: Context, spec):  # pyre-ignore[11]
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
        context.annotations_repository, context.changelog
    )

    statistics = StatisticsResource(fragmentarium)
    fragments = FragmentsResource(finder)
    fragment_genre = FragmentGenreResource(updater)
    fragment_search = FragmentSearch(
        fragmentarium,
        finder,
        context.get_transliteration_query_factory()
    )
    lemmatization = LemmatizationResource(updater)
    references = ReferencesResource(updater)
    transliteration = TransliterationResource(
        updater, context.get_transliteration_update_factory()
    )
    annotations = AnnotationResource(annotations_service)
    fragment_pager = FragmentPagerResource(finder)
    folio_pager = FolioPagerResource(finder)
    lemma_search = LemmaSearch(finder)
    photo = PhotoResource(finder)
    folios = FoliosResource(finder)

    api.add_route("/fragments", fragment_search)
    api.add_route("/fragments/{number}/genre", fragment_genre)
    api.add_route("/fragments/{number}", fragments)
    api.add_route("/fragments/{number}/pager", fragment_pager)
    api.add_route("/fragments/{number}/lemmatization", lemmatization)
    api.add_route("/fragments/{number}/references", references)
    api.add_route("/fragments/{number}/transliteration", transliteration)
    api.add_route("/fragments/{number}/annotations", annotations)
    api.add_route("/fragments/{number}/photo", photo)
    api.add_route("/lemmas", lemma_search)
    api.add_route("/statistics", statistics)
    api.add_route("/fragments/{number}/pager/{folio_name}/{folio_number}", folio_pager)
    api.add_route("/folios/{name}/{number}", folios)

    spec.components.schema("FragmentInfo", schema=FragmentInfoSchema)
    spec.components.schema("Fragment", schema=FragmentDtoSchema)
    spec.components.schema("FolioPagerInfo", schema=FolioPagerInfoSchema)
    spec.components.schema("FragmentPagerInfo", schema=FragmentPagerInfoSchema)
    spec.components.schema("Annotations", schema=AnnotationsSchema)

    spec.path(resource=fragment_search)
    spec.path(resource=fragments)
    spec.path(resource=fragment_genre)
    spec.path(resource=lemmatization)
    spec.path(resource=references)
    spec.path(resource=transliteration)
    spec.path(resource=annotations)
    spec.path(resource=photo)
    spec.path(resource=lemma_search)
    spec.path(resource=statistics)
    spec.path(resource=folio_pager)
    spec.path(resource=fragment_pager)
    spec.path(resource=folios)
