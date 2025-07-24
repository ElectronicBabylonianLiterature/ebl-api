import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.web.annotations import AnnotationResource
from ebl.fragmentarium.web.edition import EditionResource
from ebl.fragmentarium.web.findspots import FindspotResource
from ebl.fragmentarium.web.folio_pager import FolioPagerResource
from ebl.fragmentarium.web.folios import FoliosResource
from ebl.fragmentarium.web.fragment_genre import FragmentGenreResource
from ebl.fragmentarium.web.fragment_script import FragmentScriptResource
from ebl.fragmentarium.web.fragment_date import (
    FragmentDateResource,
    FragmentDatesInTextResource,
)
from ebl.fragmentarium.web.fragment_matcher import FragmentMatcherResource
from ebl.fragmentarium.web.fragment_pager import make_fragment_pager_resource
from ebl.fragmentarium.web.fragment_search import FragmentSearch
from ebl.fragmentarium.web.fragments import (
    FragmentAuthorizedScopesResource,
    FragmentsQueryResource,
    FragmentsResource,
    FragmentsListResource,
    FragmentsRetrieveAllResource,
    make_latest_additions_resource,
    make_all_fragment_signs_resource,
)
from ebl.fragmentarium.web.genres import GenresResource
from ebl.fragmentarium.web.lemma_annotation import (
    LemmaAnnotationResource,
    AutofillLemmasResource,
)
from ebl.fragmentarium.web.named_entities import NamedEntityResource
from ebl.fragmentarium.web.provenances import ProvenancesResource
from ebl.fragmentarium.web.periods import PeriodsResource
from ebl.fragmentarium.web.lemmatizations import LemmatizationResource
from ebl.fragmentarium.web.photo import PhotoResource
from ebl.fragmentarium.web.references import ReferencesResource
from ebl.fragmentarium.web.statistics import make_statistics_resource
from ebl.fragmentarium.web.archaeology import ArchaeologyResource
from ebl.fragmentarium.web.fragments_afo_register import (
    AfoRegisterFragmentsQueryResource,
)
from ebl.corpus.web.chapters import ChaptersByFragmentResource
from ebl.corpus.application.corpus import Corpus
from ebl.fragmentarium.web.colophons import ColophonResource, ColophonNamesResource


def create_fragmentarium_routes(api: falcon.App, context: Context):
    context.fragment_repository.create_indexes()
    fragmentarium = Fragmentarium(context.fragment_repository)
    finder = FragmentFinder(
        context.get_bibliography(),
        context.fragment_repository,
        Dictionary(context.word_repository, context.changelog),
        context.photo_repository,
        context.folio_repository,
        context.thumbnail_repository,
        context.parallel_line_injector,
    )
    updater = context.get_fragment_updater()
    annotations_service = AnnotationsService(
        context.ebl_ai_client,
        context.annotations_repository,
        context.photo_repository,
        context.changelog,
        context.fragment_repository,
        context.photo_repository,
        context.cropped_sign_images_repository,
    )
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.sign_repository,
        context.parallel_line_injector,
    )
    statistics = make_statistics_resource(context.cache, fragmentarium)
    fragments = FragmentsResource(finder)

    fragments_retrieve_all = FragmentsRetrieveAllResource(
        context.fragment_repository, context.photo_repository
    )
    fragment_genre = FragmentGenreResource(updater)
    fragment_script = FragmentScriptResource(updater)
    fragment_date = FragmentDateResource(updater)
    fragment_dates_in_text = FragmentDatesInTextResource(updater)

    fragment_matcher = FragmentMatcherResource(
        FragmentMatcher(context.fragment_repository)
    )
    fragment_search = FragmentSearch(
        fragmentarium,
        finder,
        context.get_transliteration_query_factory(),
        context.cache,
    )
    fragment_query = FragmentsQueryResource(
        context.fragment_repository, context.get_transliteration_query_factory()
    )
    afo_register_fragments_query = AfoRegisterFragmentsQueryResource(
        context.fragment_repository, finder
    )
    latest_additions_query = make_latest_additions_resource(
        context.fragment_repository, context.cache
    )
    genres = GenresResource()
    provenances = ProvenancesResource()
    periods = PeriodsResource()
    lemmatization = LemmatizationResource(updater)
    lemma_annotation = LemmaAnnotationResource(updater)
    lemma_autofill = AutofillLemmasResource(
        context.fragment_repository, context.word_repository
    )
    references = ReferencesResource(updater)
    edition = EditionResource(updater, context.get_transliteration_update_factory())
    scopes = FragmentAuthorizedScopesResource(
        context.fragment_repository, finder, updater
    )
    archaeology = ArchaeologyResource(updater)
    colophon = ColophonResource(updater)
    annotations = AnnotationResource(annotations_service)
    fragment_pager = make_fragment_pager_resource(finder, context.cache)
    folio_pager = FolioPagerResource(finder)
    photo = PhotoResource(finder)
    folios = FoliosResource(finder)
    chapters = ChaptersByFragmentResource(corpus, finder)
    findspots = FindspotResource(context.findspot_repository)

    all_fragments = FragmentsListResource(context.fragment_repository)
    all_signs = make_all_fragment_signs_resource(
        context.fragment_repository, context.cache
    )
    colophon_names = ColophonNamesResource(context.fragment_repository)
    named_entities = NamedEntityResource(finder)

    routes = [
        ("/fragments", fragment_search),
        ("/fragments/retrieve-all", fragments_retrieve_all),
        ("/fragments/{number}/match", fragment_matcher),
        ("/fragments/{number}/genres", fragment_genre),
        ("/fragments/{number}/script", fragment_script),
        ("/fragments/{number}/date", fragment_date),
        ("/fragments/{number}/dates-in-text", fragment_dates_in_text),
        ("/fragments/{number}", fragments),
        ("/fragments/{number}/pager", fragment_pager),
        ("/fragments/{number}/lemmatization", lemmatization),
        ("/fragments/{number}/lemma-annotation", lemma_annotation),
        ("/fragments/{number}/collect-lemmas", lemma_autofill),
        ("/fragments/{number}/references", references),
        ("/fragments/{number}/edition", edition),
        ("/fragments/{number}/archaeology", archaeology),
        ("/fragments/{number}/colophon", colophon),
        ("/fragments/{number}/annotations", annotations),
        ("/fragments/{number}/thumbnail/{resolution}", photo),
        ("/fragments/{number}/photo", photo),
        ("/fragments/{number}/corpus", chapters),
        ("/genres", genres),
        ("/provenances", provenances),
        ("/periods", periods),
        ("/statistics", statistics),
        ("/fragments/{number}/pager/{folio_name}/{folio_number}", folio_pager),
        ("/folios/{name}/{number}", folios),
        ("/fragments/query", fragment_query),
        ("/fragments/query-by-traditional-references", afo_register_fragments_query),
        ("/fragments/latest", latest_additions_query),
        ("/fragments/all", all_fragments),
        ("/fragments/all-signs", all_signs),
        ("/fragments/colophon-names", colophon_names),
        ("/findspots", findspots),
        ("/fragments/{number}/scopes", scopes),
        ("/fragments/{number}/named-entities", named_entities),
    ]

    for uri, resource in routes:
        api.add_route(uri, resource)
