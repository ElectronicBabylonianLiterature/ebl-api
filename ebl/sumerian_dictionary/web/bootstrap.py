import falcon

from ebl.context import Context
from ebl.sumerian_dictionary.web.sumerian_words import (
    SumerianWordListResource,
    SumerianWordResource,
    SumerianWordSearchResource,
    SumerianWordStatisticsResource,
)


def create_sumerian_dictionary_routes(api: falcon.App, context: Context) -> None:
    repository = context.sumerian_word_repository
    repository.create_indexes()
    api.add_route(
        "/sumerian-words/all", SumerianWordListResource(repository, context.cache)
    )
    api.add_route(
        "/sumerian-words/statistics",
        SumerianWordStatisticsResource(repository, context.cache),
    )
    api.add_route("/sumerian-words/{word_id}", SumerianWordResource(repository))
    api.add_route("/sumerian-words", SumerianWordSearchResource(repository))
