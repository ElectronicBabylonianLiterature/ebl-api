from typing import Sequence
import pytest
from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.tests.corpus.test_chapter_ngram_repository import chapter_ngrams_from_signs
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.common.ngram_test_support import ngrams_from_signs, N_VALUES
import falcon

SIGNS = ["X BA KU ABZ075", "KI DU ABZ411 BA MA TI\nX MU TA MA UD", "KU ABZ411 MA KI"]


def compute_overlap(fragment: Fragment, chapter: Chapter, N: Sequence[int]) -> float:
    F = ngrams_from_signs(fragment.signs, N)
    C = chapter_ngrams_from_signs(chapter.signs, N)

    return (len(F & C) / min(len(F), len(C))) if F and C else 0.0


@pytest.mark.parametrize(
    "N",
    N_VALUES,
)
def test_match_fragment_ngrams(
    client,
    fragment_repository,
    text_repository,
    N,
):
    fragment = TransliteratedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment, ngram_n=N)
    chapters = [ChapterFactory.build(signs=(signs,)) for signs in SIGNS]

    for chapter in chapters:
        text_repository.create_chapter(chapter, N)

    result = client.simulate_get(f"/fragments/{fragment_id}/ngrams", params={"n": N})

    assert result.status == falcon.HTTP_OK
    assert result.json == sorted(
        (
            {
                **ChapterIdSchema().dump(chapter.id_),
                "overlap": compute_overlap(fragment, chapter, N),
            }
            for chapter in chapters
        ),
        key=lambda item: item["overlap"],
        reverse=True,
    )
