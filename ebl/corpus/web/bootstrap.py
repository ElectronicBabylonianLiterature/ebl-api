import falcon

from ebl.context import Context
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.alignments import AlignmentResource
from ebl.corpus.web.chapters import ChaptersResource
from ebl.corpus.web.lemmatizations import LemmatizationResource
from ebl.corpus.web.lines import LinesImportResource, LinesResource
from ebl.corpus.web.manuscripts import ManuscriptsResource
from ebl.corpus.web.texts import TextResource, TextSearchResource, TextsResource
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


def create_corpus_routes(api: falcon.API, context: Context):
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.sign_repository,
    )
    context.text_repository.create_indexes()

    texts = TextsResource(corpus)
    text = TextResource(corpus)
    text_search = TextSearchResource(
        corpus, TransliterationQueryFactory(context.sign_repository)
    )
    chapters = ChaptersResource(corpus)
    alignment = AlignmentResource(corpus)
    manuscript_lemmatization = LemmatizationResource(corpus)
    manuscript = ManuscriptsResource(corpus)
    lines = LinesResource(corpus)
    lines_import = LinesImportResource(corpus)

    api.add_route("/texts", texts)
    api.add_route("/textsearch", text_search)
    api.add_route("/texts/{category}/{index}", text)
    api.add_route("/texts/{category}/{index}/chapters/{stage}/{name}", chapters)
    api.add_route(
        "/texts/{category}/{index}/chapters/{stage}/{name}/alignment", alignment
    )
    api.add_route(
        "/texts/{category}/{index}/chapters/{stage}/{name}/lemmatization",
        manuscript_lemmatization,
    )
    api.add_route(
        "/texts/{category}/{index}/chapters/{stage}/{name}/manuscripts", manuscript
    )

    api.add_route("/texts/{category}/{index}/chapters/{stage}/{name}/lines", lines)
    api.add_route(
        "/texts/{category}/{index}/chapters/{stage}/{name}/import", lines_import
    )
