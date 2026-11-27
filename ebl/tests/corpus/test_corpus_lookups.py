from typing import Callable

import pytest

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_info import ChapterInfosPagination
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.errors import Defect
from ebl.tests.corpus.outline_support import create_outline_chapter
from ebl.tests.factories.corpus import TextFactory
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

MANUSCRIPT_MUSEUM_NUMBER = MuseumNumber.of("K.5419.C")
UNCERTAIN_MUSEUM_NUMBER = MuseumNumber.of("K.1")
UNRELATED_MUSEUM_NUMBER = MuseumNumber.of("X.404")


@pytest.fixture
def chapter(
    store_editable_chapter: Callable[[Chapter], Chapter],
    text_repository: MongoTextRepository,
) -> Chapter:
    chapter = store_editable_chapter(create_outline_chapter())
    text_repository.create(
        TextFactory.build(
            genre=chapter.text_id.genre,
            category=chapter.text_id.category,
            index=chapter.text_id.index,
        )
    )
    return chapter


def test_search_corpus_by_fragment(corpus: Corpus, chapter: Chapter) -> None:
    result = corpus.search_corpus_by_fragment(
        [MANUSCRIPT_MUSEUM_NUMBER, UNCERTAIN_MUSEUM_NUMBER, UNRELATED_MUSEUM_NUMBER]
    )

    assert [
        (attestation.chapter_id, attestation.manuscript.museum_number)
        for attestation in result["manuscripts"]
    ] == [(chapter.id_, MANUSCRIPT_MUSEUM_NUMBER)]
    assert [
        attestation.chapter_id for attestation in result["uncertain_fragments"]
    ] == [chapter.id_]


def test_search_corpus_by_unrelated_fragment(corpus: Corpus, chapter: Chapter) -> None:
    assert corpus.search_corpus_by_fragment([UNRELATED_MUSEUM_NUMBER]) == {
        "manuscripts": [],
        "uncertain_fragments": [],
    }


def test_find_manuscripts_with_unknown_reference_is_a_defect(
    corpus: Corpus, text_repository: MongoTextRepository
) -> None:
    chapter = create_outline_chapter()
    text_repository.create_chapter(chapter)

    with pytest.raises(Defect, match="not found"):
        corpus.find_manuscripts(chapter.id_)


@pytest.mark.parametrize("pagination_index", [0, 3])
def test_search_transliteration_with_empty_query(
    corpus: Corpus,
    sign_repository: SignRepository,
    chapter: Chapter,
    pagination_index: int,
) -> None:
    query = TransliterationQueryFactory(sign_repository).create("")

    assert corpus.search_transliteration(
        query, pagination_index
    ) == ChapterInfosPagination([], 0)
