import falcon  # pyre-ignore[21]

from ebl.context import Context
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.alignments import AlignmentResource
from ebl.corpus.web.lines import LinesResource
from ebl.corpus.web.manuscripts import ManuscriptsResource
from ebl.corpus.web.lemmatizations import (
    LemmatizationResource,
    CorpusLemmatizationsSchema,
)
from ebl.corpus.web.texts import TextResource, TextsResource
from ebl.corpus.web.text_schemas import ApiTextSchema


def create_corpus_routes(api: falcon.API, context: Context, spec):  # pyre-ignore[11]
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.get_transliteration_update_factory(),
    )
    context.text_repository.create_indexes()

    texts = TextsResource(corpus)
    text = TextResource(corpus)
    alignment = AlignmentResource(corpus)
    manuscript_lemmatization = LemmatizationResource(corpus)
    manuscript = ManuscriptsResource(corpus)
    lines = LinesResource(corpus)

    api.add_route("/texts", texts)
    api.add_route("/texts/{category}/{index}", text)
    api.add_route(
        "/texts/{category}/{index}/chapters/{chapter_index}/alignment", alignment
    )
    api.add_route(
        "/texts/{category}/{index}/chapters/{chapter_index}/lemmatization",
        manuscript_lemmatization,
    )
    api.add_route(
        "/texts/{category}/{index}/chapters/{chapter_index}/manuscripts", manuscript
    )

    api.add_route("/texts/{category}/{index}/chapters/{chapter_index}/lines", lines)

    spec.components.schema("CorpusLemmatizations", schema=CorpusLemmatizationsSchema)
    spec.components.schema("CorpusText", schema=ApiTextSchema)

    spec.path(resource=texts)
    spec.path(resource=text)
    spec.path(resource=alignment)
    spec.path(resource=manuscript)
    spec.path(resource=manuscript_lemmatization)
    spec.path(resource=lines)
