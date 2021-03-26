import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary import Dictionary
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.lemmatization.web.lemma_search import LemmaSearch


def create_lemmatization_routes(api: falcon.API, context: Context, spec):
    finder = FragmentFinder(
        context.get_bibliography(),
        context.fragment_repository,
        Dictionary(context.word_repository, context.changelog),
        context.photo_repository,
        context.folio_repository,
    )
    lemma_search = LemmaSearch(finder)

    api.add_route("/lemmas", lemma_search)

    spec.path(resource=lemma_search)
