import falcon

from ebl.context import Context
from ebl.dictionary.application.dictionary import Dictionary
from ebl.dictionary.web.word_search import WordSearch
from ebl.dictionary.web.words import WordsResource


def create_dictionary_routes(api: falcon.API, context: Context, spec):
    dictionary = Dictionary(context.word_repository, context.changelog)
    words = WordsResource(dictionary)
    word_search = WordSearch(dictionary)
    api.add_route("/words", word_search)
    api.add_route("/words/{object_id}", words)
    spec.path(resource=words)
    spec.path(resource=word_search)
