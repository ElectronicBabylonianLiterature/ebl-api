import falcon

from ebl.context import Context
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.alignments import AlignmentResource
from ebl.corpus.web.chapters import (
    ChaptersByLemmaResource,
    ChaptersDisplayResource,
    ChaptersResource,
)
from ebl.corpus.web.colophons import ColophonsResource
from ebl.corpus.web.extant_lines import ExtantLinesResource
from ebl.corpus.web.lemmatizations import LemmatizationResource
from ebl.corpus.web.lines import LinesImportResource, LinesResource, LineResource
from ebl.corpus.web.manuscripts import ManuscriptsResource
from ebl.corpus.web.texts import TextResource, TextsResource, make_text_search_resource
from ebl.corpus.web.unplaced_lines import UnplacedLinesResource
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


def create_corpus_routes(api: falcon.App, context: Context):
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.sign_repository,
        context.parallel_line_injector,
    )
    context.text_repository.create_indexes()

    texts = TextsResource(corpus)
    text = TextResource(corpus)
    text_search = make_text_search_resource(
        context.cache, corpus, TransliterationQueryFactory(context.sign_repository)
    )
    chapters = ChaptersResource(corpus)
    chapters_display = ChaptersDisplayResource(corpus)
    chapters_line = LineResource(corpus)
    chapters_by_lemma = ChaptersByLemmaResource(corpus)
    alignment = AlignmentResource(corpus)
    manuscript_lemmatization = LemmatizationResource(corpus)
    manuscript = ManuscriptsResource(corpus)
    lines = LinesResource(corpus)
    lines_import = LinesImportResource(corpus)
    colophons = ColophonsResource(corpus)
    unplaced_lines = UnplacedLinesResource(corpus)
    extant_lines = ExtantLinesResource(corpus)

    text_url = "/texts/{genre}/{category}/{index}"
    chapter_url = text_url + "/chapters/{stage}/{name}"

    api.add_route("/texts", texts)
    api.add_route("/textsearch", text_search)
    api.add_route(text_url, text)

    api.add_route(chapter_url, chapters)
    api.add_route(f"{chapter_url}/display", chapters_display)
    api.add_route(f"{chapter_url}/alignment", alignment)
    api.add_route(f"{chapter_url}/lemmatization", manuscript_lemmatization)
    api.add_route(f"{chapter_url}/manuscripts", manuscript)
    api.add_route(f"{chapter_url}/lines", lines)
    api.add_route(f"{chapter_url}/lines/{{number}}", chapters_line)
    api.add_route(f"{chapter_url}/import", lines_import)
    api.add_route(f"{chapter_url}/colophons", colophons)
    api.add_route(f"{chapter_url}/unplaced_lines", unplaced_lines)
    api.add_route(f"{chapter_url}/extant_lines", extant_lines)
    api.add_route("/lemmasearch", chapters_by_lemma)
