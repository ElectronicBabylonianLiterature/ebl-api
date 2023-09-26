from typing import List
from ebl.common.infrastructure.ngrams import NGRAM_N_VALUES
from ebl.corpus.application.display_schemas import ChapterNgramScoreSchema
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_display import ChapterNgramScore
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.tests.common.ngram_test_support import compute_ngram_score
from ebl.corpus.domain.text import Text
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
import falcon

from ebl.transliteration.domain.text_id import TextId

SIGNS = ["X BA KU ABZ075", "KI DU ABZ411 BA MA TI\nX MU TA MA UD", "KU ABZ411 MA KI"]
TEXT: Text = TextFactory.build()


def test_match_fragment_ngrams(
    client,
    fragment_repository: FragmentRepository,
    text_repository: TextRepository,
):
    fragment = TransliteratedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment)
    text_repository.create(TEXT)
    chapters: List[Chapter] = [
        ChapterFactory.build(
            signs=(signs,), text_id=TextId(TEXT.genre, TEXT.category, TEXT.index)
        )
        for signs in SIGNS
    ]

    for chapter in chapters:
        text_repository.create_chapter(chapter)

    result = client.simulate_get(f"/fragments/{fragment_id}/ngrams")

    assert result.status == falcon.HTTP_OK
    assert result.json == sorted(
        (
            ChapterNgramScoreSchema().dump(
                ChapterNgramScore.of(
                    chapter.id_,
                    TEXT.name,
                    compute_ngram_score(fragment, chapter, NGRAM_N_VALUES),
                )
            )
            for chapter in chapters
        ),
        key=lambda item: item["score"],
        reverse=True,
    )
