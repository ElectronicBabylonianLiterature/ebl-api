import falcon

from ebl.context import Context
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.alignments import AlignmentResource
from ebl.corpus.web.lines import LinesResource
from ebl.corpus.web.manuscripts import ManuscriptsResource
from ebl.corpus.web.texts import TextResource, TextsResource
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.signs.application.atf_converter import AtfConverter


def create_corpus_routes(api: falcon.API,
                         context: Context,
                         atf_converter: AtfConverter,
                         spec):
    corpus = Corpus(
        context.text_repository,
        context.bibliography,
        context.changelog,
        TransliterationUpdateFactory(atf_converter)
    )
    context.text_repository.create_indexes()

    texts = TextsResource(corpus)
    text = TextResource(corpus)
    alignment = AlignmentResource(corpus)
    manuscript = ManuscriptsResource(corpus)
    lines = LinesResource(corpus)

    api.add_route('/texts', texts)
    api.add_route('/texts/{category}/{index}', text)
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/alignment',
        alignment
    )
    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/manuscripts',
        manuscript
    )

    api.add_route(
        '/texts/{category}/{index}/chapters/{chapter_index}/lines',
        lines)

    spec.path(resource=texts)
    spec.path(resource=text)
    spec.path(resource=alignment)
    spec.path(resource=manuscript)
    spec.path(resource=lines)
