from typing import Sequence, Set, Tuple, Optional

import pytest
from ebl.tests.factories.corpus import ChapterFactory
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.tests.common.ngram_test_support import ngrams_from_signs, N_VALUES


def chapter_ngrams_from_signs(
    chapter_signs: Sequence[Optional[str]], N: Sequence[int]
) -> Set[Tuple[str]]:
    return set.union(
        *(ngrams_from_signs(signs, N) for signs in chapter_signs if signs is not None)
    )


def test_create_chapter_sets_ngrams(text_repository, chapter_ngram_repository):
    chapter = ChapterFactory.build()
    text_repository.create_chapter(chapter)

    assert chapter_ngram_repository._ngrams.exists(chapter_id_query(chapter.id_))


@pytest.mark.parametrize(
    "N",
    N_VALUES,
)
@pytest.mark.parametrize(
    "N_NEW",
    N_VALUES,
)
def test_update_chapter_ngrams(text_repository, chapter_ngram_repository, N, N_NEW):
    chapter = ChapterFactory.build()
    text_repository.create_chapter(chapter, N)

    ngrams = chapter_ngrams_from_signs(chapter.signs, N)

    assert chapter_ngram_repository.get_ngrams(chapter.id_) == ngrams

    chapter_ngram_repository.set_ngrams(chapter.id_, N_NEW)
    ngrams = chapter_ngrams_from_signs(chapter.signs, N_NEW)
    assert chapter_ngram_repository.get_ngrams(chapter.id_) == ngrams
