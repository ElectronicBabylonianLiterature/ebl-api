import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary import Dictionary
from ebl.lemmatization.application.suggestion_finder import SuggestionFinder
from ebl.lemmatization.web.lemma_search import LemmaSearch


def create_lemmatization_routes(api: falcon.API, context: Context):
    dictionary = Dictionary(context.word_repository, context.changelog)
    finder = SuggestionFinder(dictionary, context.lemma_repository)
    lemma_search = LemmaSearch(finder)

    api.add_route("/lemmas", lemma_search)
