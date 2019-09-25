import falcon

from ebl.context import Context
from ebl.dictionary.web.word_search import WordSearch
from ebl.dictionary.web.words import WordsResource


def create_dictionary_routes(api: falcon.API, context: Context, spec):
    words = WordsResource(context.dictionary)
    word_search = WordSearch(context.dictionary)
    api.add_route('/words', word_search)
    api.add_route('/words/{object_id}', words)
    spec.path(resource=words)
    spec.path(resource=word_search)
