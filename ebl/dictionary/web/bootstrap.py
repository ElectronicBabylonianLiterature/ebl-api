import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.dictionary.web.word_search import WordSearch
from ebl.dictionary.web.words import (
    WordsResource,
    WordsListResource,
    ProperNounCreationResource,
)


def create_dictionary_routes(api: falcon.App, context: Context):
    dictionary = Dictionary(context.word_repository, context.changelog)
    words = WordsResource(dictionary)
    word_search = WordSearch(dictionary)
    word_list = WordsListResource(dictionary)
    proper_noun_creation = ProperNounCreationResource(dictionary)
    api.add_route("/words/create-proper-noun", proper_noun_creation)
    api.add_route("/words", word_search)
    api.add_route("/words/{object_id}", words)
    api.add_route("/words/all", word_list)
